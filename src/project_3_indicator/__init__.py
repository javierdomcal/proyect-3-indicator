"""
Main package interface for running quantum chemistry calculations.
"""
import logging
from pathlib import Path
import atexit

from .cluster.connection import ClusterConnection
from .cluster.transfer import FileTransfer
from .jobs.manager import JobManager
from .handler.calculation import CalculationHandler
from .handler.parallel import ParallelHandler
from .database import get_database, close_database

logger = logging.getLogger(__name__)

# Initialize database once and register cleanup
db = get_database()
atexit.register(close_database)

def run_calculation(input):
    """
    Run a quantum chemistry calculation with the provided input parameters.

    This is the main entry point for the package.

    Args:
        input (dict): Dictionary containing calculation parameters:
            - molecule: Molecule name
            - method: Method name
            - basis: Basis set name
            - config: Calculation type (SP/Opt), default "SP"
            - charge: Molecular charge, default 0
            - multiplicity: Spin multiplicity, default 1
            - omega: Omega parameter for harmonium
            - properties: Properties to calculate

    Returns:
        dict: The calculation results

    Examples:
        # Single calculation
        result = run_calculation({
            'molecule': 'water',
            'method': 'B3LYP',
            'basis': '6-31G'
        })
    """
    try:
        # Create cluster connection and required components
        with ClusterConnection() as connection:
            file_manager = FileTransfer(connection)
            job_manager = JobManager(connection, file_manager)

            # Create handler and run calculation
            handler = CalculationHandler(connection, file_manager, job_manager)
            return handler.handle_calculation(input)

    except Exception as e:
        logger.error(f"Error in calculation execution: {str(e)}")
        raise

# For backward compatibility
def get_database_instance():
    """Get the global database instance."""
    return db

def get_calculation_cube_data(calc_id):
    """
    Retrieve the cube data from a completed calculation without rerunning.

    Args:
        calc_id: ID of the previously run calculation

    Returns:
        DataFrame containing the combined cube data, or None if not found
    """
    from .utils.cube import read_cube_file, to_dataframe, to_unique_dataframe
    from pathlib import Path
    import os
    import logging
    from .config.settings import RESULTS_DIR

    logger = logging.getLogger(__name__)
    results_path = Path(RESULTS_DIR) / str(calc_id)

    if not results_path.exists():
        logger.error(f"No results found for calculation ID {calc_id}")
        return None

# Find all cube files
    cube_files = {}
    for prop in ['density', 'on_top']:
        cube_path = results_path / f"{prop}.cube"
        if cube_path.exists():
            cube_files[prop] = cube_path

    if not cube_files:
        logger.info(f"No cube files found for calculation {calc_id}")
        return None

    logger.debug(f"Found {len(cube_files)} cube files for calculation {calc_id}: {list(cube_files.keys())}")

    # Process each cube file
    cube_dfs = {}
    for prop_name, cube_path in cube_files.items():
        try:
            cube_data = read_cube_file(cube_path)
            df = to_dataframe(cube_data)
            print(df)
            # Rename value column to property name
            cube_dfs[prop_name] = df
            logger.debug(f"Processed cube file {prop_name} with {len(df)} grid points for calculation {calc_id}")
        except Exception as e:
            logger.error(f"Error processing cube file {prop_name} for calculation {calc_id}: {str(e)}")

    # Combine DataFrames if any were successfully processed
    if not cube_dfs:
        return None

    try:
        # Combine on x, y, z coordinates
        print(cube_dfs)
        combined_df = to_unique_dataframe(cube_dfs)


        logger.info(f"Created combined DataFrame with {len(combined_df)} grid points for calculation {calc_id}")
        return combined_df
    except Exception as e:
        logger.error(f"Error combining cube data for calculation {calc_id}: {str(e)}")
        return None