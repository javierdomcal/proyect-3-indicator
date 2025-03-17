"""
Handler for individual flux calculations with standardized results processing.
"""

import io
import json
import logging
import re
import pandas as pd
from pathlib import Path
import numpy as np

from ..input.specification import InputSpecification
from ..input.molecules import Molecule
from ..input.methods import Method
from ..input.basis import BasisSet
from ..input.scanning import ScanningProperties
from ..flux.correlation import CorrelationFlux
from ..database.operations import DatabaseOperations
from ..config.settings import RESULTS_DIR
from ..cluster.command import ClusterCommands
from ..utils.parsers import parse_gaussian_log

class CalculationHandler:
    def __init__(self, connection, file_manager, job_manager):
        """
        Initialize calculation handler.

        Args:
            connection: ClusterConnection instance
            file_manager: FileTransfer instance
            job_manager: JobManager instance
        """
        self.connection = connection
        self.file_manager = file_manager
        self.job_manager = job_manager
        self.correlation_flux = CorrelationFlux(connection, file_manager, job_manager)
        self.db = DatabaseOperations()
        self.commands = ClusterCommands(connection)


    def handle_calculation(self, molecule_name, method_name, basis_name,
                         config="SP", charge=0, multiplicity=1,
                         omega=None, scanning_props=None, excited_state=None):
        """
        Handle complete calculation workflow.
        """
        try:
            # Create input specification
            molecule = Molecule(name=molecule_name, charge=charge,
                              multiplicity=multiplicity, omega=omega)
            method = Method(method_name,excited_state=excited_state)
            basis = BasisSet(basis_name=basis_name, omega=omega)
            scanning = ScanningProperties(molecule=molecule, scan_props=scanning_props)

            if excited_state is not None:
                config = {
                    'basis': basis_name,
                    'method': method_name
                }

            input_spec = InputSpecification(
                molecule=molecule,
                method=method,
                basis=basis,
                title=f"{molecule_name}_{method_name}_{basis_name}",
                config=config,
                scanning_props=scanning
            )

            # Check if calculation exists in database
            calc_info = self.db.get_calculation_info_by_input_spec(
                input_spec
            )

            if calc_info and calc_info["status"] == "completed":
                logging.info(f"Found completed calculation {calc_info['id']}")
                return self.get_processed_results(calc_info['id'])

            # Register new calculation
            calc_id = self.db.register_calculation(
                input_spec
            )

            input_spec.calc_id = calc_id

            try:
                if isinstance(config, dict):
                    from ..calculations.screening import ScreeningHandler
                    screening_handler = ScreeningHandler(
                        self.connection,
                        self.file_manager,
                        self.job_manager
                    )
                    input_spec = screening_handler.handle_screening(input_spec, config)


                flux_results = self.correlation_flux.handle_correlation_flux(
                    calc_id,
                    input_spec
                )

                # Store results
                self.store_results(calc_id)

                # Update database with success
                self.db.update_calculation_status(calc_id, "completed")

            except Exception as e:
                self.db.update_calculation_status(calc_id, "failed", str(e))
                raise

            return self.get_processed_results(calc_id)

        except Exception as e:
            logging.error(f"Error in calculation workflow: {str(e)}")
            raise

    def store_results(self, calc_id):
        """Store calculation results in results directory."""
        try:
            # Create results directory locally
            results_path = Path(RESULTS_DIR) / calc_id
            results_path.mkdir(parents=True, exist_ok=True)

            # Get calculation info from database
            calc_info = self.db.get_calculation_info(calc_id)

            # Check and download files from cluster
            colony_path = f"{self.connection.colony_dir}/{calc_id}"
            files_to_check = [f"{calc_id}.log", "ontop.dat", "ontop.cube", "density.cube", "ID.cube"]

            for file in files_to_check:
                remote_file = f"{colony_path}/{file}"
                if self.commands.check_file_exists(remote_file):
                    logging.info(f"Found {file} on cluster, downloading...")
                    self.file_manager.download_file(
                        remote_file,
                        str(results_path / file)
                    )
                else:
                    logging.warning(f"File {file} not found in colony directory on cluster")

            # Parse Gaussian results
            log_file = results_path / f"{calc_id}.log"
            if log_file.exists():
                with open(log_file) as f:
                    gaussian_results = parse_gaussian_log(f.read(), is_content=True)
            else:
                gaussian_results = {}

            # Core results JSON
            results = {
                "calculation_info": calc_info,
                "results": {
                    "energy": gaussian_results.get("energies", {}),
                    "calculation_time": gaussian_results.get("elapsed_time"),
                    "status": "completed"
                }
            }

            # Store JSON results locally
            with open(results_path / "results.json", "w") as f:
                json.dump(results, f, indent=2)

            # Store geometry if available
            geometry = gaussian_results.get("geometry")
            if geometry:
                with open(results_path / "optimized_geometry.xyz", "w") as f:
                    f.write(f"{len(geometry)}\n")
                    f.write(f"{calc_info['molecule_name']} Optimized Geometry {calc_info['method_name']}/{calc_info['basis_name']}\n")
                    for atom in geometry:
                        coords = atom["coordinates"]
                        f.write(f"{atom['symbol']} {coords[0]} {coords[1]} {coords[2]}\n")

        except Exception as e:
            logging.error(f"Error storing results for {calc_id}: {str(e)}")
            raise

    def read_cube_file(cube_path):
        """Read a cube file and return the grid data and values."""
        with open(cube_path, 'r') as f:
            # Skip the first two comment lines
            next(f)
            next(f)

            # Read grid specs
            parts = next(f).split()
            natoms = int(parts[0])
            origin = np.array([float(parts[1]), float(parts[2]), float(parts[3])])

            # Read grid dimensions and step sizes
            nx_line = next(f).split()
            ny_line = next(f).split()
            nz_line = next(f).split()

            nx = int(nx_line[0])
            ny = int(ny_line[0])
            nz = int(nz_line[0])

            dx = float(nx_line[1])
            dy = float(ny_line[2])
            dz = float(nz_line[3])

            # Skip atom coordinates
            for _ in range(natoms):
                next(f)

            # Read the volumetric data
            values = []
            for line in f:
                values.extend([float(val) for val in line.split()])

            values = np.array(values)

            # Create the grid
            x = np.linspace(origin[0], origin[0] + (nx-1)*dx, nx)
            y = np.linspace(origin[1], origin[1] + (ny-1)*dy, ny)
            z = np.linspace(origin[2], origin[2] + (nz-1)*dz, nz)

            # Create meshgrid
            X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

            # Reshape values to match grid shape
            values = values.reshape((nx, ny, nz))

            return X, Y, Z, values, (nx, ny, nz)

    def get_processed_results(self, calc_id):
        """Get processed calculation results in standardized format."""
        try:
            calc_info = self.db.get_calculation_info(calc_id)
            results_path = Path(RESULTS_DIR) / calc_id

            with open(results_path / "results.json") as f:
                results = json.load(f)

            geometry = ""
            if (results_path / "optimized_geometry.xyz").exists():
                with open(results_path / "optimized_geometry.xyz") as f:
                    geometry = f.read()

            ontop_df = None
            if (results_path / "ontop.dat").exists():
                ontop_df = pd.read_csv(
                    results_path / "ontop.dat",
                    skipinitialspace=True
                )

            # Paths to cube files
            ontop_path = results_path / "ontop.cube"
            density_path = results_path / "density.cube"
            id_path = results_path / "ID.cube"

            cube_df = None
            if ontop_path.exists() and density_path.exists() and id_path.exists():
                # Read the cube files
                X, Y, Z, ontop_values, dims = read_cube_file(ontop_path)
                _, _, _, density_values, _ = read_cube_file(density_path)
                _, _, _, id_values, _ = read_cube_file(id_path)

                # Flatten the arrays for DataFrame creation
                x_flat = X.flatten()
                y_flat = Y.flatten()
                z_flat = Z.flatten()
                ontop_flat = ontop_values.flatten()
                density_flat = density_values.flatten()
                id_flat = id_values.flatten()

                # Create DataFrame
                cube_df = pd.DataFrame({
                    'x': x_flat,
                    'y': y_flat,
                    'z': z_flat,
                    'ontop': ontop_flat,
                    'density': density_flat,
                    'indicator': id_flat
                })

                print(f"Created DataFrame with {len(cube_df)} grid points")
            else:
                print("One or more cube files not found")


            processed_results = {
                "calculation_id": calc_id,
                "molecule_name": calc_info["molecule_name"],
                "method_name": calc_info["method_name"],
                "basis_name": calc_info["basis_name"],
                "energy": results.get("energy", {}).get("total"),
                "calculation_time": results.get("calculation", {}).get("elapsed_time"),
                "geometry": geometry,
                "ontop_data": ontop_df,
                "ontop_cube": cube_df,
                "status": calc_info["status"]
            }

            return processed_results

        except Exception as e:
            logging.error(f"Error processing results for {calc_id}: {str(e)}")
            raise


if __name__ == "__main__":
    import sys
    import os
    from utils.log_config import setup_logging
    from cluster.connection import ClusterConnection
    from cluster.transfer import FileTransfer
    from jobs.manager import JobManager

    setup_logging(verbose_level=2)

    try:
        with ClusterConnection() as connection:
            file_manager = FileTransfer(connection)
            job_manager = JobManager(connection, file_manager)

            handler = CalculationHandler(connection, file_manager, job_manager)

            results = handler.handle_calculation(
                molecule_name="helium",
                method_name="CASSCF(2,2)",
                basis_name="sto-3g",
                charge=0,
                multiplicity=1
            )

            print("\nCalculation Results:")
            for key, value in results.items():
                if key != "ontop_data":
                    print(f"{key}: {value}")

    except Exception as e:
        print(f"Test failed: {str(e)}")