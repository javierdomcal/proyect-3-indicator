"""
Handler for individual flux calculations with standardized results processing.
No database dependencies.
"""

import json
import logging
import pandas as pd
from pathlib import Path
import time
from datetime import datetime
import random
import os

from ..input.specification import InputSpecification
from ..flux.flux_manager import Flux
from ..config.settings import RESULTS_DIR
from ..cluster.command import ClusterCommands
from ..utils.parsers import parse_gaussian_log
from ..utils.cube import read_cube_file, to_dataframe, to_unique_dataframe

logger = logging.getLogger(__name__)

class CalculationHandler:
    """Handles complete calculation workflows without database dependencies."""

    # Class-level counter for generating calculation IDs
    _calculation_counter = 0

    @classmethod
    def _generate_calc_id(cls):
        """Generate a unique calculation ID."""
        cls._calculation_counter = random.randint(100000, 999999)
        return cls._calculation_counter

    def __init__(self, connection, file_manager, job_manager):
        """
        Initialize calculation handler with component management.

        Args:
            connection: ClusterConnection instance
            file_manager: FileTransfer instance
            job_manager: JobManager instance
        """
        self.connection = connection
        self.file_manager = file_manager
        self.job_manager = job_manager
        self.flux = Flux(connection, file_manager, job_manager)
        self.commands = ClusterCommands(connection)
        self.results_dir = Path(RESULTS_DIR)
        self.logger = logger
        self.input_spec = None

        # Ensure results directory exists
        os.makedirs(self.results_dir, exist_ok=True)

        # In-memory storage of calculation metadata
        self.calculations = {}  # Dict to store calculation info
        self.properties = {}    # Dict to store properties by calc_id

    def handle_calculation(self, input_params):
        """
        Handle complete calculation workflow without database dependencies.

        Args:
            input_params: Dictionary with calculation parameters
                molecule: Molecule name
                method: Method name
                basis: Basis set name
                config: Calculation type ("SP" or "Opt"), default "SP"
                charge: Molecular charge, default 0
                multiplicity: Spin multiplicity, default 1
                omega: Omega parameter for harmonium
                properties: Properties to calculate
                force_recalculate: Force recalculation even if exists, default False

        Returns:
            dict: Processed calculation results
        """
        start_time = time.time()
        force_recalculate = input_params.get('force_recalculate', False)

        try:
            # Convert input parameters to specification object
            self.input_spec = self._prepare_input_spec(input_params)

            # Generate or find calculation ID
            calc_id, run_calculation = self._prepare_calculation_metadata(
                self.input_spec, force_recalculate)

            # Update input spec with calculation ID
            self.input_spec.get_calc_id(calc_id)

            # Run calculation if needed
            if run_calculation:
                self._run_calculation(calc_id, self.input_spec, input_params)

            # Process and return results
            result = self._get_results(calc_id)

            # Log completion
            elapsed = time.time() - start_time
            self.logger.info(f"Completed calculation workflow for {calc_id} in {elapsed:.1f}s")

            return result

        except Exception as e:
            self._handle_calculation_error(e, start_time)
            raise

    def _prepare_input_spec(self, input_params):
        """
        Convert input parameters to specification object with validation.

        Args:
            input_params: Dictionary with calculation parameters

        Returns:
            InputSpecification: Validated input specification

        Raises:
            ValueError: If input parameters are invalid
        """
        try:
            input_spec = InputSpecification(input_params)
            self.logger.info(f"Processing calculation for {input_spec.molecule.name} with {input_spec.method.name}/{input_spec.basis.name}")

            # Debug log for requested properties
            property_names = []
            if hasattr(input_spec, 'properties'):
                if hasattr(input_spec.properties, 'get_active_properties'):
                    property_names = input_spec.properties.get_active_properties()
                elif isinstance(input_spec.properties, list):
                    property_names = input_spec.properties

            if property_names:
                self.logger.debug(f"Requested properties: {', '.join(property_names)}")
            else:
                self.logger.debug("No specific properties requested")

            return input_spec
        except Exception as e:
            self.logger.error(f"Error preparing input specification: {str(e)}")
            raise ValueError(f"Invalid input parameters: {str(e)}")

    def _prepare_calculation_metadata(self, input_spec, force_recalculate):
        """
        Create or find calculation metadata without using a database.

        Args:
            input_spec: InputSpecification instance
            force_recalculate: Whether to force recalculation

        Returns:
            tuple: (calculation_id, should_run_calculation)
        """
        # Extract properties needed for lookups
        property_names = []
        if hasattr(input_spec, 'properties'):
            if hasattr(input_spec.properties, 'get_active_properties'):
                property_names = input_spec.properties.get_active_properties()
            elif isinstance(input_spec.properties, list):
                property_names = input_spec.properties

        # Create unique key for this calculation configuration
        calc_key = f"{input_spec.molecule.name}_{input_spec.method.name}_{input_spec.basis.name}_{input_spec.config}"

        # Check for existing calculation if not forcing recalculation
        if not force_recalculate:
            for calc_id, info in self.calculations.items():
                if info.get('calc_key') == calc_key and info.get('status') == "completed":
                    self.logger.debug(f"Found existing calculation {calc_id}")

                    # Check if all properties are available
                    existing_props = self.properties.get(calc_id, {}).get('completed', [])
                    self.logger.debug(f"Properties already calculated: {existing_props}")

                    # Find missing properties
                    missing_props = [p for p in property_names if p not in existing_props]

                    if missing_props:
                        self.logger.info(f"Using existing calculation {calc_id} but need to calculate missing properties: {missing_props}")
                        # Register missing properties
                        if calc_id not in self.properties:
                            self.properties[calc_id] = {'active': [], 'completed': []}
                        self.properties[calc_id]['active'].extend(missing_props)
                        return calc_id, True
                    else:
                        self.logger.info(f"Using existing calculation {calc_id} with all requested properties already calculated")
                        return calc_id, False

        # Generate new calculation ID
        calc_id = self._generate_calc_id()

        # Store calculation metadata
        self.calculations[calc_id] = {
            'calc_key': calc_key,
            'molecule_name': input_spec.molecule.name,
            'method_name': input_spec.method.name,
            'basis_name': input_spec.basis.name,
            'config': input_spec.config,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'error_message': None
        }

        # Register properties
        if property_names:
            self.properties[calc_id] = {
                'active': property_names,
                'completed': []
            }
        else:
            self.properties[calc_id] = {
                'active': [],
                'completed': []
            }

        self.logger.info(f"Created new calculation with ID: {calc_id}")
        return calc_id, True

    def _run_calculation(self, calc_id, input_spec, input_params):
        """
        Execute the calculation and store results.

        Args:
            calc_id: Calculation ID
            input_spec: InputSpecification instance
            input_params: Original input parameters
        """
        start_time = time.time()

        # Debug log before running calculation
        active_props = self.properties.get(calc_id, {}).get('active', [])
        self.logger.debug(f"Starting calculation {calc_id} for properties: {active_props}")

        # Update calculation status
        self.calculations[calc_id]['status'] = "running"
        self.calculations[calc_id]['start_time'] = datetime.now().isoformat()

        try:
            # Handle screening if requested
            if input_params.get('screening_value') is not None:
                input_spec = self._handle_screening(input_spec, input_params['screening_value'])

            # Run actual calculation
            self.flux.handle_flux(calc_id, input_spec)

            # Store and process results
            self._store_results(calc_id)

            # Update calculation status
            self.calculations[calc_id]['status'] = "completed"
            self.calculations[calc_id]['end_time'] = datetime.now().isoformat()

            # Calculate elapsed time
            elapsed = time.time() - start_time
            self.calculations[calc_id]['elapsed_time'] = elapsed

            self.logger.info(f"Calculation {calc_id} completed successfully in {elapsed:.1f}s")

        except Exception as e:
            self.calculations[calc_id]['status'] = "failed"
            self.calculations[calc_id]['error_message'] = str(e)
            self.logger.error(f"Calculation {calc_id} failed: {str(e)}")
            raise

    def _handle_screening(self, input_spec, screening_value):
        """
        Handle screening calculation workflow.

        Args:
            input_spec: InputSpecification instance
            screening_value: Screening parameters

        Returns:
            InputSpecification: Updated input specification
        """
        from ..calculations.screening import ScreeningHandler
        self.logger.info(f"Handling screening for calculation {input_spec.calc_id}")

        screening_handler = ScreeningHandler(
            self.connection,
            self.file_manager,
            self.job_manager
        )
        return screening_handler.handle_screening(input_spec, screening_value)

    def _store_results(self, calc_id):
        """
        Store calculation results with efficient file handling.

        Args:
            calc_id: Calculation ID
        """
        # Get calculation info
        calc_info = self.calculations.get(calc_id, {})
        active_props = self.properties.get(calc_id, {}).get('active', [])

        if not calc_info:
            raise ValueError(f"Invalid calculation info for calc_id {calc_id}")

        self.logger.debug(f"Storing results for calculation {calc_id}, active properties: {active_props}")

        # Create results directory
        results_path = self.results_dir / str(calc_id)
        results_path.mkdir(parents=True, exist_ok=True)

        # Download files only if they don't exist locally
        colony_path = f"{self.connection.colony_dir}/{calc_id}"
        downloaded_files = self._download_needed_files(calc_id, colony_path, results_path, active_props)

        # Process log file if it exists
        log_file = results_path / f"{calc_id}.log"
        gaussian_results = self._process_log_file(log_file) if log_file.exists() else {}

        # Create and store results summary
        self._create_results_summary(calc_id, calc_info, active_props, gaussian_results, results_path)

        # Store geometry data if available
        geometry = gaussian_results.get("geometry")
        if geometry:
            self._store_geometry_data(calc_id, geometry, calc_info, results_path)

        # Process cube files
        processed_cubes = self._process_cube_files(calc_id, results_path, active_props)

        # Update properties records
        if calc_id in self.properties:
            # Mark processed cubes as completed
            for prop in processed_cubes:
                if prop not in self.properties[calc_id]['completed']:
                    self.properties[calc_id]['completed'].append(prop)

            # Check for any missing properties
            still_missing = [p for p in active_props if p not in self.properties[calc_id]['completed']]
            if still_missing:
                self.logger.warning(f"Some properties could not be processed for calculation {calc_id}: {still_missing}")

    def _download_needed_files(self, calc_id, colony_path, results_path, active_props):
        """
        Download only the files that are needed and don't exist locally.

        Args:
            calc_id: Calculation ID
            colony_path: Path to colony directory
            results_path: Path to results directory
            active_props: List of active properties

        Returns:
            list: List of downloaded file paths
        """
        downloaded_files = []

        # Map of remote files to local files
        files_to_check = [
            (f"{colony_path}/{calc_id}.log", results_path / f"{calc_id}.log")
        ]

        # Add cube files
        for prop in active_props:
            remote_file = f"{colony_path}/{prop}.cube"
            local_file = results_path / f"{prop}.cube"
            files_to_check.append((remote_file, local_file))

        self.logger.debug(f"Checking for files to download: {[remote for remote, _ in files_to_check]}")

        # Download only if remote exists and local doesn't
        for remote_file, local_file in files_to_check:
            if not local_file.exists():
                if self.commands.check_file_exists(remote_file):
                    self.logger.info(f"Downloading {remote_file} to {local_file}")
                    self.file_manager.download_file(remote_file, str(local_file))
                    downloaded_files.append(local_file)
                else:
                    self.logger.warning(f"Remote file not found: {remote_file}")
            else:
                self.logger.debug(f"File already exists locally: {local_file}")

        if downloaded_files:
            self.logger.debug(f"Downloaded {len(downloaded_files)} files: {[str(f) for f in downloaded_files]}")
        else:
            self.logger.debug("No files needed downloading")

        return downloaded_files

    def _process_log_file(self, log_file):
        """
        Process Gaussian log file with better error handling.

        Args:
            log_file: Path to log file

        Returns:
            dict: Parsed Gaussian results
        """
        try:
            with open(log_file) as f:
                content = f.read()
            results = parse_gaussian_log(content, is_content=True)
            self.logger.debug(f"Successfully parsed log file: {log_file}")
            return results
        except Exception as e:
            self.logger.error(f"Error parsing log file {log_file}: {str(e)}")
            return {}

    def _create_results_summary(self, calc_id, calc_info, active_props, gaussian_results, results_path):
        """
        Create a JSON summary of calculation results.

        Args:
            calc_id: Calculation ID
            calc_info: Calculation info from memory
            active_props: List of active properties
            gaussian_results: Parsed Gaussian results
            results_path: Path to results directory
        """
        # Core results JSON
        results = {
            "calculation_info": {
                "id": calc_id,
                "molecule_name": calc_info.get("molecule_name"),
                "basis_name": calc_info.get("basis_name"),
                "method_name": calc_info.get("method_name"),
                "status": calc_info.get("status"),
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

        self.logger.debug(f"Created results summary for calculation {calc_id}")

    def _store_geometry_data(self, calc_id, geometry, calc_info, results_path):
        """
        Store geometry data in XYZ format.

        Args:
            calc_id: Calculation ID
            geometry: Geometry data from Gaussian results
            calc_info: Calculation info from memory
            results_path: Path to results directory
        """
        xyz_file = results_path / "optimized_geometry.xyz"

        try:
            with open(xyz_file, "w") as f:
                f.write(f"{len(geometry)}\n")
                f.write(f"{calc_info['molecule_name']} Optimized Geometry {calc_info['method_name']}/{calc_info['basis_name']}\n")
                for atom in geometry:
                    coords = atom["coordinates"]
                    f.write(f"{atom['symbol']} {coords[0]} {coords[1]} {coords[2]}\n")

            self.logger.debug(f"Stored geometry data for calculation {calc_id} with {len(geometry)} atoms")

        except Exception as e:
            self.logger.error(f"Error storing geometry data for calculation {calc_id}: {str(e)}")

    def _process_cube_files(self, calc_id, results_path, active_props):
        """
        Process cube files and store metadata locally.        if 'value' in df.columns:


        Args:
            calc_id: Calculation ID
            results_path: Path to results directory
            active_props: List of active properties

        Returns:
            list: List of successfully processed properties
        """
        processed_cubes = []
        missing_cubes = []

        for prop_name in active_props:
            cube_path = results_path / f"{prop_name}.cube"
            if cube_path.exists():
                try:
                    # Read cube file metadata only
                    cube_data = read_cube_file(cube_path)

                    # Store metadata in a JSON file
                    meta_path = results_path / f"{prop_name}_meta.json"
                    with open(meta_path, 'w') as f:
                        json.dump({
                            "format": "cube",
                            "dimensions": cube_data["shape"],
                            "origin": cube_data["header"]["origin"].tolist(),
                            "path": str(cube_path),
                            "atoms": len(cube_data["atoms"])
                        }, f, indent=2)

                    processed_cubes.append(prop_name)
                    self.logger.debug(f"Processed cube file for property {prop_name} in calculation {calc_id}")

                except Exception as e:
                    self.logger.error(f"Error processing cube file {prop_name}.cube for calculation {calc_id}: {str(e)}")
            else:
                missing_cubes.append(prop_name)
                self.logger.warning(f"Cube file not found for property {prop_name} in calculation {calc_id}")

        # Log summary of cube processing
        if processed_cubes:
            self.logger.info(f"Successfully processed {len(processed_cubes)} cube files for calculation {calc_id}: {processed_cubes}")
        if missing_cubes:
            self.logger.warning(f"Missing {len(missing_cubes)} cube files for calculation {calc_id}: {missing_cubes}")

        return processed_cubes

    def _get_results(self, calc_id):
        """
        Get processed calculation results with efficient data handling.

        Args:
            calc_id: Calculation ID

        Returns:
            dict: Processed calculation results
        """
        # Get basic calculation info
        calc_info = self.calculations.get(calc_id, {})
        if not calc_info:
            raise ValueError(f"Invalid calculation info for calc_id {calc_id}")

        results_path = self.results_dir / str(calc_id)

        # Build results dictionary
        result = {
            "calculation_id": calc_id,
            "molecule_name": calc_info.get("molecule_name"),
            "method_name": calc_info.get("method_name"),
            "basis_name": calc_info.get("basis_name"),
            "status": calc_info.get("status"),
            "error_message": calc_info.get("error_message"),
        }

        # Add energy data if available
        energy_data = self._get_energy_data(calc_id, results_path)
        if energy_data:
            result.update(energy_data)

        # Add geometry data if available
        geometry_data = self._get_geometry_data(calc_id, results_path)
        if geometry_data:
            result.update(geometry_data)

        # Get active and completed properties
        active_props = self.input_spec.properties.get_active_properties()

        self.logger.debug(f"Results for calculation {calc_id}:")
        self.logger.debug(f"  - Active properties: {active_props}")

        # Process cube files if needed
        cube_df = self._get_cube_dataframe(calc_id, results_path, active_props)
        if cube_df is not None:
            result["cube_df"] = cube_df

        return result

    def _get_energy_data(self, calc_id, results_path):
        """
        Get energy data for calculation.

        Args:
            calc_id: Calculation ID
            results_path: Path to results directory

        Returns:
            dict: Energy data
        """
        # Check results.json first
        results_json = results_path / "results.json"
        if results_json.exists():
            try:
                with open(results_json) as f:
                    data = json.load(f)
                    if "results" in data and "energy" in data["results"]:
                        return {"energy": data["results"]["energy"].get("total")}
            except Exception as e:
                self.logger.warning(f"Error reading results.json for calculation {calc_id}: {str(e)}")

        return {"energy": None}

    def _get_geometry_data(self, calc_id, results_path):
        """
        Get geometry data for calculation.

        Args:
            calc_id: Calculation ID
            results_path: Path to results directory

        Returns:
            dict: Geometry data
        """
        geometry = ""
        xyz_file = results_path / "optimized_geometry.xyz"

        if xyz_file.exists():
            try:
                with open(xyz_file) as f:
                    geometry = f.read()
            except Exception as e:
                self.logger.warning(f"Error reading geometry file for calculation {calc_id}: {str(e)}")

        return {"geometry": geometry}

    def _get_cube_dataframe(self, calc_id, results_path, completed_props):
        """
        Get a combined DataFrame of cube data.

        Args:
            calc_id: Calculation ID
            results_path: Path to results directory
            completed_props: List of completed properties

        Returns:
            DataFrame or None: Combined cube data
        """
        # Check which cube files exist
        cube_files = {}
        for prop in completed_props:
            cube_path = results_path / f"{prop}.cube"
            if cube_path.exists():
                cube_files[prop] = cube_path

        if not cube_files:
            self.logger.info(f"No cube files found for calculation {calc_id}")
            return None

        self.logger.debug(f"Found {len(cube_files)} cube files for calculation {calc_id}: {list(cube_files.keys())}")

        # Process each cube file
        cube_dfs = {}
        for prop_name, cube_path in cube_files.items():
            try:
                cube_data = read_cube_file(cube_path)
                df = to_dataframe(cube_data)
                print(df)
                # Rename value column to property name
                cube_dfs[prop_name] = df
                self.logger.debug(f"Processed cube file {prop_name} with {len(df)} grid points for calculation {calc_id}")
            except Exception as e:
                self.logger.error(f"Error processing cube file {prop_name} for calculation {calc_id}: {str(e)}")

        # Combine DataFrames if any were successfully processed
        if not cube_dfs:
            return None

        try:
            # Combine on x, y, z coordinates
            print(cube_dfs)
            combined_df = to_unique_dataframe(cube_dfs)


            self.logger.info(f"Created combined DataFrame with {len(combined_df)} grid points for calculation {calc_id}")
            return combined_df
        except Exception as e:
            self.logger.error(f"Error combining cube data for calculation {calc_id}: {str(e)}")
            return None

    def _handle_calculation_error(self, error, start_time):
        """
        Handle calculation errors with better context.

        Args:
            error: Exception that occurred
            start_time: Start time of calculation
        """
        elapsed = time.time() - start_time
        error_message = str(error)
        self.logger.error(f"Error in calculation workflow ({elapsed:.1f}s): {error_message}")