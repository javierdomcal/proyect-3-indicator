"""
Main package interface for running quantum chemistry calculations.
"""

import logging
from pathlib import Path

from .cluster.connection import ClusterConnection
from .cluster.transfer import FileTransfer
from .jobs.manager import JobManager
from .handler.calculation import CalculationHandler
from .handler.parallel import ParallelHandler
from .database.operations import DatabaseOperations

def run_calculation(molecule_name, method_name, basis_name,
                   config="SP", charge=0, multiplicity=1,
                   omega=None, scanning_props=None, max_workers=4):
    """
    Main interface for running calculations.

    Automatically detects if parallel execution is needed based on inputs.
    At least one input must be provided.

    Args:
        molecule_name: String or list of molecule names
        method_name: String or list of method names (e.g., "HF", "CASSCF(2,2)")
        basis_name: String or list of basis set names
        config: Calculation type ("SP" or "Opt"), default "SP"
        charge: Molecular charge, default 0
        multiplicity: Spin multiplicity, default 1
        omega: Omega parameter for harmonium/even-tempered basis, default None
        scanning_props: Properties to scan, default None
        max_workers: Maximum number of parallel calculations, default 4

    Returns:
        If all inputs are single strings:
            dict: Results dictionary for single calculation
        If any input is a list:
            list: List of result dictionaries for each calculation
    """
    try:
        # Check if any input is a list
        is_parallel = any(
            isinstance(x, list)
            for x in [molecule_name, method_name, basis_name]
        )

        # Create cluster connection and required components
        with ClusterConnection() as connection:
            file_manager = FileTransfer(connection)
            job_manager = JobManager(connection, file_manager)
            db_operations = DatabaseOperations()

            if is_parallel:
                handler = ParallelHandler(
                    connection,
                    file_manager,
                    job_manager,
                    max_workers=max_workers
                )
                results = handler.handle_parallel_calculations(
                    molecule_name=molecule_name,
                    method_name=method_name,
                    basis_name=basis_name,
                    config=config,
                    charge=charge,
                    multiplicity=multiplicity,
                    omega=omega,
                    scanning_props=scanning_props
                )
            else:
                handler = CalculationHandler(
                    connection,
                    file_manager,
                    job_manager
                        )
                results = handler.handle_calculation(
                    molecule_name=molecule_name,
                    method_name=method_name,
                    basis_name=basis_name,
                    config=config,
                    charge=charge,
                    multiplicity=multiplicity,
                    omega=omega,
                    scanning_props=scanning_props
                )

            return results

    except Exception as e:
        logging.error(f"Error in calculation execution: {str(e)}")
        raise