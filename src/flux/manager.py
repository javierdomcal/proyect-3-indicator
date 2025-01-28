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
        self.completed_fluxes = {}

    def log_flux_completion(
        self, job_name, flux_type, start_time, end_time, status="completed", error=None
    ):
        """Log completion of a flux calculation."""
        try:
            runtime = end_time - start_time
            self.completed_fluxes[job_name] = {
                "flux_type": flux_type,
                "start_time": start_time,
                "end_time": end_time,
                "runtime": runtime,
                "status": status,
                "error": error,
            }
            logging.info(f"Flux {job_name} completed with status: {status}")

        except Exception as e:
            logging.error(f"Error logging flux completion for {job_name}: {e}")
            raise

    def check_flux_completed(self, job_name):
        """Check if a flux has already been completed."""
        if job_name in self.completed_fluxes:
            status = self.completed_fluxes[job_name]["status"]
            logging.info(f"Flux {job_name} previous status: {status}")
            return status == "completed"
        return False

    def handle_flux(self, job_name, input_spec, flux_type, calculations):
        """
        Handle a sequence of calculations in a flux.

        Args:
            job_name: Base name for the job
            input_spec: InputSpecification instance
            flux_type: Type of flux (e.g., 'correlation', 'energy')
            calculations: List of calculation instances to run in sequence
        """
        try:
            if self.check_flux_completed(job_name):
                logging.info(f"Flux {job_name} already completed, skipping.")
                return self.completed_fluxes[job_name]

            start_time = datetime.now()
            results = {}

            for calc in calculations:
                calc_name = calc.__class__.__name__
                logging.info(f"Running {calc_name} for {job_name}")

                if hasattr(calc, "handle_calculation"):
                    if "input_spec" in calc.handle_calculation.__code__.co_varnames:
                        results[calc_name] = calc.handle_calculation(
                            job_name, input_spec
                        )
                    else:
                        results[calc_name] = calc.handle_calculation(job_name)
                else:
                    raise ValueError(
                        f"Calculation {calc_name} missing handle_calculation method"
                    )

            end_time = datetime.now()
            self.log_flux_completion(job_name, flux_type, start_time, end_time)

            return results

        except Exception as e:
            logging.error(f"Error in flux {job_name}: {e}")
            end_time = datetime.now()
            self.log_flux_completion(
                job_name, flux_type, start_time, end_time, status="failed", error=str(e)
            )
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
