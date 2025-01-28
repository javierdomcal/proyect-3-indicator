"""
Handles Gaussian quantum chemistry calculations.
"""

import os
import logging
from calculations.base import Calculation
from utils.generator import InputFileGenerator
from utils.parsers import parse_gaussian_log


class GaussianCalculation(Calculation):
    def prepare_input_files(self, job_name, input_spec, nproc=1, wfx=True):
        """Prepare input files for Gaussian calculation."""
        try:
            # Generate Gaussian input file
            generator = InputFileGenerator(
                config=input_spec.config,
                molecule=input_spec.molecule,
                method=input_spec.method,
                basis=input_spec.basis,
                title=job_name,
                input_type="gaussian",
            )

            # Create local test directory and generate input file
            input_dir = "test"
            os.makedirs(input_dir, exist_ok=True)
            com_file = os.path.join(input_dir, f"{job_name}.com")
            generator.generate_input_file(nproc=nproc, wfx=wfx)

            # Define cluster paths
            colony_dir = f"{self.connection.colony_dir}/{job_name}"
            colony_com = f"{colony_dir}/{job_name}.com"

            # Upload .com file to colony
            self.file_manager.upload_file(com_file, colony_com)

            # Generate SLURM script and upload
            slurm_script = self.job_manager.submitter.generate_gaussian_script(
                job_name, f"{self.connection.scratch_dir}/{job_name}"
            )
            self.file_manager.upload_file(
                slurm_script, f"{colony_dir}/{job_name}.slurm"
            )

            logging.info(f"Input files prepared for {job_name}")

        except Exception as e:
            logging.error(f"Error preparing Gaussian input files for {job_name}: {e}")
            raise

    def collect_results(self, job_name):
        """Collect and process Gaussian calculation results."""
        try:
            # Define paths
            colony_dir = f"{self.connection.colony_dir}/{job_name}"
            log_file = f"{colony_dir}/{job_name}.log"

            # Verify log file exists
            if not self.commands.check_file_exists(log_file):
                raise FileNotFoundError(f"Log file not found: {log_file}")

            # Read and parse log file
            content = self.commands.read_file_content(log_file)
            results = parse_gaussian_log(content, is_content=True)

            logging.info(f"Results collected for {job_name}")
            return results

        except Exception as e:
            logging.error(f"Error collecting results for {job_name}: {e}")
            raise

    def handle_calculation(self, job_name, input_spec, nproc=1, wfx=True):
        """Handle complete Gaussian calculation workflow."""
        try:
            # Prepare directories
            self.prepare_directories(job_name)

            # Prepare input files
            self.prepare_input_files(job_name, input_spec, nproc, wfx)

            # Move files to scratch
            self.move_to_scratch(job_name, f"{job_name}.com")
            self.move_to_scratch(job_name, f"{job_name}.slurm")

            # Submit and monitor
            job_id = self.submit_and_monitor(job_name)

            # Retrieve results
            self.move_all_files_to_colony(job_name)

            # Process outputs

            # Collect and return results
            return self.collect_results(job_name)

        except Exception as e:
            logging.error(f"Error in Gaussian calculation for {job_name}: {e}")
            raise


if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Setup imports
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
        # Initialize test inputs
        job_name = "helium_testing_gaussian"
        molecule = Molecule(name="helium")
        method = Method("CISD")
        basis = BasisSet("sto-3g")

        # Create input specification
        input_spec = InputSpecification(
            molecule=molecule,
            method=method,
            basis=basis,
            title=job_name,
            config="SP",
            input_type="gaussian",
        )

        # Establish connection and initialize components
        with ClusterConnection(config_file="utils/cluster_config.json") as connection:
            # Initialize managers
            file_manager = FileTransfer(connection)
            job_manager = JobManager(connection, file_manager)
            cleanup = ClusterCleanup(connection)

            # Create calculation instance
            gaussian_calc = GaussianCalculation(
                connection=connection,
                file_manager=file_manager,
                job_manager=job_manager,
            )

            # Run calculation
            print("\nRunning Gaussian calculation...")
            results = gaussian_calc.handle_calculation(
                job_name=job_name, input_spec=input_spec, nproc=4, wfx=True
            )

            # Print results
            print("\nCalculation Results:")
            for key, value in results.items():
                print(f"{key}: {value}")

            # Clean up
            print("\nCleaning up...")
            cleanup.clean_calculation(job_name)

    except Exception as e:
        print(f"Test failed: {e}")
        # Try to cleanup even if test failed
        try:
            cleanup.clean_calculation(job_name)
        except:
            pass
