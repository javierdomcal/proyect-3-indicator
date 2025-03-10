"""
Handles correlation indicator flux calculations.
"""

import logging
from ..flux.flux_manager import FluxManager
from ..calculations.gaussian import GaussianCalculation
from ..calculations.dmn import DMNCalculation
from ..calculations.dm2prim import DM2PRIMCalculation
from ..calculations.inca import INCACalculation


class CorrelationFlux(FluxManager):
    def __init__(self, connection, file_manager, job_manager):
        """Initialize correlation flux manager."""
        super().__init__(connection, file_manager, job_manager)
        self.gaussian = GaussianCalculation(connection, file_manager, job_manager)
        self.dmn = DMNCalculation(connection, file_manager, job_manager)
        self.dm2prim = DM2PRIMCalculation(connection, file_manager, job_manager)
        self.inca = INCACalculation(connection, file_manager, job_manager)

    def handle_correlation_flux(self, job_name, input_spec):
        """
        Handle complete correlation flux calculation.

        This includes:
        1. Gaussian calculation
        2. DMN calculation
        3. DM2PRIM calculation
        4. INCA calculation
        """
        try:

            if input_spec.method.is_hf:
                return self.handle_hf_flux(job_name, input_spec)

            calculations = [self.gaussian, self.dmn, self.dm2prim, self.inca]

            self.handle_flux(
                job_name, input_spec,  calculations
            )
            logging.info(f"Correlation flux completed for {job_name}")


        except Exception as e:
            logging.error(f"Error in correlation flux for {job_name}: {e}")
            raise

    def handle_hf_flux(self, job_name, input_spec):
        """Handle HF-only flux calculation."""
        try:
            calculations = [self.gaussian, self.inca]
            results = self.handle_flux(
                job_name, input_spec,  calculations
            )
            logging.info(f"HF flux completed for {job_name}")
            return results

        except Exception as e:
            logging.error(f"Error in HF flux for {job_name}: {e}")
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

            # Initialize correlation flux manager
            flux_manager = CorrelationFlux(connection, file_manager, job_manager)

            # Test setup
            test_name = "correlation_test"
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

            # Run correlation flux
            print("\nTesting correlation flux...")
            results = flux_manager.handle_correlation_flux(test_name, input_spec)

            # Print results
            print("\nCorrelation Flux Results:")
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
