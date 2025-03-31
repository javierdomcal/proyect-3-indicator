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
            handler = CalculationHandler(connection, file_manager, job_manager, db)
            return handler.handle_calculation(input)

    except Exception as e:
        logger.error(f"Error in calculation execution: {str(e)}")
        raise

# For backward compatibility
def get_database_instance():
    """Get the global database instance."""
    return db