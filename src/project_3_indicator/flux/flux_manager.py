"""
Base flux manager for handling sequences of calculations.
"""

import logging
from datetime import datetime


class FluxManager:
    def __init__(self, connection, file_manager, job_manager):
        """Initialize flux manager with necessary components."""
        self.connection = connection
        self.file_manager = file_manager
        self.job_manager = job_manager



    def handle_flux(self, job_name, input_spec, calculations):
        try:
            for calc in calculations:
                calc_name = calc.__class__.__name__
                logging.info(f"Running {calc_name} for {job_name}")

                if hasattr(calc, "handle_calculation"):
                    calc.handle_calculation(job_name, input_spec)



            return True
        except Exception as e:
            logging.error(f"Error in flux {job_name}: {e}")
            raise


if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from utils.log_config import setup_logging
    from cluster.connection import ClusterConnection
    from cluster.transfer import FileTransfer
    from jobs.manager import JobManager
    from cluster.cleanup import ClusterCleanup
    from calculations.gaussian import GaussianCalculation
    from calculations.dmn import DMNCalculation
    from calculations.dm2prim import DM2PRIMCalculation
    from calculations.inca import INCACalculation
    from input.molecules import Molecule
    from input.methods import Method
    from input.basis import BasisSet
    from input.specification import InputSpecification

    # Setup logging
    setup_logging(verbose_level=2)

    try:
        with ClusterConnection() as connection:
            # Initialize components
            file_manager = FileTransfer(connection)
            job_manager = JobManager(connection, file_manager)
            cleanup = ClusterCleanup(connection)

            # Initialize flux manager
            flux_manager = FluxManager(connection, file_manager, job_manager)

            # Test setup
            test_name = "flux_test"
            molecule = Molecule(name="hydrogen_atom", multiplicity=2)
            method = Method("CISD")
            basis = BasisSet("sto-3g")

            # Create input specification
            input_spec = InputSpecification(
                molecule=molecule,
                method=method,
                basis=basis,
                title=test_name,
                config="SP",
                input_type="gaussian",
            )

            # Create calculation instances
            calculations = [
                GaussianCalculation(connection, file_manager, job_manager),
                DMNCalculation(connection, file_manager, job_manager),
                DM2PRIMCalculation(connection, file_manager, job_manager),
                INCACalculation(connection, file_manager, job_manager),
            ]

            # Run flux
            print("\nTesting flux execution...")
            results = flux_manager.handle_flux(
                test_name, input_spec, "correlation", calculations
            )

            # Print results
            print("\nFlux Results:")
            for calc_name, result in results.items():
                print(f"\n{calc_name}:")
                print(result)

            # Clean up
            print("\nCleaning up...")
            cleanup.clean_calculation(test_name)

    except Exception as e:
        print(f"Test failed: {e}")
        try:
            cleanup.clean_calculation(test_name)
        except:
            pass
