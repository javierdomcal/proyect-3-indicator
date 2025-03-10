"""
Handler for individual flux calculations with standardized results processing.
"""

import io
import json
import logging
import re
import pandas as pd
from pathlib import Path

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
            files_to_check = [f"{calc_id}.log", "ontop.dat"]

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


            processed_results = {
                "calculation_id": calc_id,
                "molecule_name": calc_info["molecule_name"],
                "method_name": calc_info["method_name"],
                "basis_name": calc_info["basis_name"],
                "energy": results.get("energy", {}).get("total"),
                "calculation_time": results.get("calculation", {}).get("elapsed_time"),
                "geometry": geometry,
                "ontop_data": ontop_df,
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