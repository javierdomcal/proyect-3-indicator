"""
Handler for individual flux calculations with standardized results processing.
"""

import io
import json
import logging
import pandas as pd
from pathlib import Path
import time
from datetime import datetime

from ..input.specification import InputSpecification
from ..flux.correlation import CorrelationFlux
from ..database import get_database
from ..config.settings import RESULTS_DIR
from ..cluster.command import ClusterCommands
from ..utils.parsers import parse_gaussian_log
from ..utils.cube import read_cube_file, to_dataframe

logger = logging.getLogger(__name__)

class CalculationHandler:
    def __init__(self, connection, file_manager, job_manager, db=None):
        """
        Initialize calculation handler.

        Args:
            connection: ClusterConnection instance
            file_manager: FileTransfer instance
            job_manager: JobManager instance
            db: Database instance (optional, will be created if not provided)
        """
        self.connection = connection
        self.file_manager = file_manager
        self.job_manager = job_manager
        self.correlation_flux = CorrelationFlux(connection, file_manager, job_manager)
        self.db = db or get_database()
        self.commands = ClusterCommands(connection)

    def handle_calculation(self, input):
        """
        Handle complete calculation workflow.

        Args:
            input: Dictionary with calculation parameters
                molecule: Molecule name
                method: Method name
                basis: Basis set name
                config: Calculation type ("SP" or "Opt"), default "SP"
                charge: Molecular charge, default 0
                multiplicity: Spin multiplicity, default 1
                omega: Omega parameter for harmonium
                properties: Properties to calculate

        Returns:
            dict: Processed calculation results
        """
        start_time = time.time()
        calc_id = None

        try:
            # Create input specification directly from the input dictionary
            input_spec = InputSpecification(input)

            logger.info(f"Processing calculation for {input_spec.molecule.name} with {input_spec.method.name}/{input_spec.basis.name}")

            # Process properties from input
            property_names = self.db.properties.process_properties_list(input_spec.properties)

            # Use a transaction for all database operations
            with self.db.transaction():
                # Step 1: Get or create molecule in database
                if input_spec.molecule.is_harmonium:
                    molecule_id = self.db.molecules.add(
                        name=input_spec.molecule.name,
                        charge=input_spec.molecule.charge,
                        multiplicity=input_spec.molecule.multiplicity,
                        is_harmonium=True,
                        omega=input_spec.molecule.omega,
                        formula=getattr(input_spec.molecule, 'formula', None)
                    )
                else:
                    molecule_id = self.db.molecules.add(
                        name=input_spec.molecule.name,
                        charge=input_spec.molecule.charge,
                        multiplicity=input_spec.molecule.multiplicity,
                        formula=getattr(input_spec.molecule, 'formula', None)
                    )

                # Step 2: Check if calculation exists and is completed
                calc_info = self.db.calculations.find(
                    molecule_id=molecule_id,
                    basis_set=input_spec.basis.name,
                    method=input_spec.method.name,
                    config_type=input_spec.config,
                    grid=input_spec.grid if hasattr(input_spec, 'grid') else None
                )

                if calc_info and calc_info["status"] == "completed":
                    # Check if all requested properties are available
                    missing_props = self.db.properties.get_missing_properties(
                        calc_info["id"], property_names
                    )

                    if not missing_props:
                        logger.info(f"Found completed calculation {calc_info['id']} with all requested properties")
                        return self.get_processed_results(calc_info['id'])

                    # Some properties are missing but calculation is complete
                    # We might need to run additional property calculations
                    logger.info(f"Found completed calculation {calc_info['id']} but missing properties: {missing_props}")
                    calc_id = calc_info["id"]
                    # Add missing properties to track
                    self.db.properties.add_properties(calc_id, missing_props)

                # Step 3: Create new calculation if needed
                if not calc_id:
                    # Register new calculation
                    calc_id = self.db.calculations.add(
                        molecule_id=molecule_id,
                        basis_set=input_spec.basis.name,
                        method=input_spec.method.name,
                        config_type=input_spec.config,
                        grid=input_spec.grid if hasattr(input_spec, 'grid') else None,
                        code_version=input_spec.code_version if hasattr(input_spec, 'code_version') else None
                    )
                    logger.info(f"Created new calculation with ID: {calc_id}")

                    # Add properties to track
                    self.db.properties.add_properties(calc_id, property_names)

                # Update the input_spec with the calculation ID
                input_spec.get_calc_id(calc_id)

                # Update calculation status to running
                self.db.calculations.update_status(calc_id, "running")

            # Run the calculation (outside transaction to avoid long locks)
            try:
                # Special case for screening calculations
                if hasattr(input, 'screening_value') and input.screening_value is not None:
                    from ..calculations.screening import ScreeningHandler
                    screening_handler = ScreeningHandler(
                        self.connection,
                        self.file_manager,
                        self.job_manager
                    )
                    input_spec = screening_handler.handle_screening(input_spec, input.screening_value)

                # Run the actual calculation
                flux_results = self.correlation_flux.handle_correlation_flux(
                    calc_id,
                    input_spec
                )

                # Store results
                self.store_results(calc_id)

                # Update database with success (in transaction)
                with self.db.transaction():
                    self.db.calculations.update_status(calc_id, "completed")

                    # Add a tag with calculation duration
                    elapsed = time.time() - start_time
                    self.db.calculations.add_tag(calc_id, f"duration:{int(elapsed)}")

            except Exception as e:
                # Update database with failure status (in transaction)
                with self.db.transaction():
                    self.db.calculations.update_status(calc_id, "failed", str(e))
                raise

            return self.get_processed_results(calc_id)

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error in calculation workflow ({elapsed:.1f}s): {str(e)}")

            # If we have a calc_id but haven't updated status yet
            if calc_id:
                try:
                    with self.db.transaction():
                        status_info = self.db.calculations.get(calc_id)
                        if status_info and status_info["status"] == "running":
                            self.db.calculations.update_status(calc_id, "failed", str(e))
                except:
                    pass  # Best effort update

            raise

    def store_results(self, calc_id):
        """
        Store calculation results in results directory.

        Args:
            calc_id: Calculation ID
        """
        try:
            # Create results directory locally
            results_path = Path(RESULTS_DIR) / str(calc_id)
            results_path.mkdir(parents=True, exist_ok=True)

            # Get calculation info from database
            with self.db.transaction():
                calc_info = self.db.calculations.get(calc_id)
                active_props = []

                # Get all properties for this calculation
                for prop_name in self.db.properties.get_missing_properties(calc_id, []):
                    active_props.append(prop_name)

            if not calc_info:
                raise ValueError(f"Invalid calculation info for calc_id {calc_id}")

            # Check and download files from cluster
            colony_path = f"{self.connection.colony_dir}/{calc_id}"
            files_to_check = active_props + [f"{calc_id}.log"]

            for file in files_to_check:
                remote_file = f"{colony_path}/{file}"
                if self.commands.check_file_exists(remote_file):
                    logger.info(f"Found {file} on cluster, downloading...")
                    self.file_manager.download_file(
                        remote_file,
                        str(results_path / file)
                    )
                else:
                    logger.warning(f"File {file} not found in colony directory on cluster")

            # Parse Gaussian results
            log_file = results_path / f"{calc_id}.log"
            gaussian_results = {}

            if log_file.exists():
                with open(log_file) as f:
                    gaussian_results = parse_gaussian_log(f.read(), is_content=True)

            # Core results JSON
            results = {
                "calculation_info": {
                    "id": calc_id,
                    "molecule_name": calc_info["molecule_name"],
                    "basis_name": calc_info["basis_set"],
                    "method_name": calc_info["method"],
                    "status": calc_info["status"],
                    "properties": active_props
                },
                "results": {
                    "energy": gaussian_results.get("energies", {}),
                    "calculation_time": gaussian_results.get("elapsed_time"),
                    "status": "completed"
                }
            }

            # Store JSON results locally
            with open(results_path / "results.json", "w") as f:
                json.dump(results, f, indent=2)

            # Also store in database
            with self.db.transaction():
                # Store energy result if available
                if "energies" in gaussian_results and "total" in gaussian_results["energies"]:
                    energy_data = {
                        "total": gaussian_results["energies"]["total"],
                        "type": "energy"
                    }
                    self.db.properties.store_result(calc_id, "energy", energy_data)

                # Store calculation time if available
                if "elapsed_time" in gaussian_results:
                    time_data = {
                        "elapsed_time": gaussian_results["elapsed_time"],
                        "unit": "seconds"
                    }
                    self.db.properties.store_result(calc_id, "calculation_time", time_data)

            # Store geometry if available
            geometry = gaussian_results.get("geometry")
            if geometry:
                with open(results_path / "optimized_geometry.xyz", "w") as f:
                    f.write(f"{len(geometry)}\n")
                    f.write(f"{calc_info['molecule_name']} Optimized Geometry {calc_info['method']}/{calc_info['basis_set']}\n")
                    for atom in geometry:
                        coords = atom["coordinates"]
                        f.write(f"{atom['symbol']} {coords[0]} {coords[1]} {coords[2]}\n")

                # Store geometry in database too
                with self.db.transaction():
                    self.db.properties.store_result(calc_id, "geometry", {
                        "format": "xyz",
                        "data": geometry
                    })

            # Process cube files and store in database
            for prop_name in active_props:
                cube_path = results_path / f"{prop_name}.cube"
                if cube_path.exists():
                    try:
                        # Read cube file but don't store the full data in DB (too large)
                        # Just record that it exists and store metadata
                        cube_data = read_cube_file(cube_path)
                        with self.db.transaction():
                            self.db.properties.store_result(calc_id, f"{prop_name}_meta", {
                                "format": "cube",
                                "dimensions": cube_data["dimensions"],
                                "origin": cube_data["origin"],
                                "path": str(cube_path),
                                "atoms": len(cube_data["atoms"])
                            })
                    except Exception as e:
                        logger.error(f"Error processing cube file {prop_name}.cube: {e}")

        except Exception as e:
            logger.error(f"Error storing results for {calc_id}: {str(e)}")
            raise

    def get_processed_results(self, calc_id):
        """
        Get processed calculation results in standardized format.

        Args:
            calc_id: Calculation ID

        Returns:
            dict: Processed calculation results
        """
        try:
            # Get calculation info and all properties
            with self.db.transaction():
                calc_info = self.db.calculations.get(calc_id)
                if not calc_info:
                    raise ValueError(f"Invalid calculation info for calc_id {calc_id}")

            results_path = Path(RESULTS_DIR) / str(calc_id)

            # Try to load results.json if it exists
            results = {}
            if (results_path / "results.json").exists():
                with open(results_path / "results.json") as f:
                    results = json.load(f)

            # Get geometry if available
            geometry = ""
            if (results_path / "optimized_geometry.xyz").exists():
                with open(results_path / "optimized_geometry.xyz") as f:
                    geometry = f.read()

            # Get all property names for this calculation
            with self.db.transaction():
                active_props = []
                for prop in self.db.properties.get_missing_properties(calc_id, []):
                    active_props.append(prop)

            # Process cube files into dataframes
            cube_dfs = []
            for prop_name in active_props:
                cube_path = results_path / f"{prop_name}.cube"
                if not cube_path.exists():
                    logger.warning(f"Cube file {prop_name}.cube not found for calculation {calc_id}")
                    continue

                try:
                    cube_data = read_cube_file(cube_path)
                    cube_df = to_dataframe(cube_data)
                    cube_dfs.append(cube_df)
                except Exception as e:
                    logger.error(f"Error processing cube file {prop_name}.cube: {e}")

            # Combine cube dataframes
            cube_df = None
            if cube_dfs:
                cube_df = pd.concat(cube_dfs, axis=1)
                logger.info(f"Created DataFrame with {len(cube_df)} grid points for calculation {calc_id}")

            # Get energy from results or database
            energy = None
            if "results" in results and "energy" in results["results"]:
                energy = results["results"]["energy"].get("total")

            # Get calculation time
            calculation_time = None
            if "results" in results and "calculation_time" in results["results"]:
                calculation_time = results["results"]["calculation_time"]
            elif calc_info["start_time"] and calc_info["end_time"]:
                # Calculate from database timestamps
                start = datetime.strptime(calc_info["start_time"], "%Y-%m-%d %H:%M:%S")
                end = datetime.strptime(calc_info["end_time"], "%Y-%m-%d %H:%M:%S")
                calculation_time = (end - start).total_seconds()

            # Build processed results
            processed_results = {
                "calculation_id": calc_id,
                "molecule_name": calc_info["molecule_name"],
                "method_name": calc_info["method"],
                "basis_name": calc_info["basis_set"],
                "energy": energy,
                "calculation_time": calculation_time,
                "geometry": geometry,
                "ontop_cube": cube_df,
                "status": calc_info["status"],
                "error_message": calc_info["error_message"]
            }

            return processed_results

        except Exception as e:
            logger.error(f"Error processing results for {calc_id}: {str(e)}")
            raise