"""
Handles DMN calculations.
"""

import os
import logging
import time
from calculations.base import Calculation


class DMNCalculation(Calculation):
    def modify_log_file(self, job_name):
        """Modify the Gaussian log file for subsequent calculations."""
        try:
            # Define cluster paths
            colony_dir = f"{self.connection.colony_dir}/{job_name}"
            log_file = f"{colony_dir}/{job_name}.log"

            # Verify log file exists
            if not self.commands.check_file_exists(log_file):
                raise FileNotFoundError(f"Log file not found: {log_file}")

            # Read current content
            content = self.commands.read_file_content(log_file)

            # Prepare additional content
            additional_text = """
             Thresholds for DMn (READ, WRITE)
             1d-10 1d-10
             DMs to compute
             2 1 2
             DM2HF
             DM2SD

            """
            # Create modified content directly on cluster
            cmd = f"echo '{content}{additional_text}' > {colony_dir}/temp.log"
            self.commands.execute_command(cmd)

            # Replace original with modified version
            self.commands.execute_command(f"mv {colony_dir}/temp.log {log_file}")

            logging.info(f"Log file modified for {job_name}")

        except Exception as e:
            logging.error(f"Error modifying log file for {job_name}: {e}")
            raise

    def prepare_input_files(self, job_name):
        """Prepare input files for DMN calculation."""
        try:
            # DMN needs the Gaussian log file

            self.modify_log_file(job_name)
            log_file = f"{job_name}.log"

            colony_log_path = os.path.join(
                self.connection.colony_dir, job_name, log_file
            )

            if not self.commands.check_file_exists(colony_log_path):
                raise FileNotFoundError(f"{log_file} not found in colony directory")

            # Generate DMN SLURM script
            slurm_script = self.job_manager.submitter.generate_dmn_script(
                job_name, os.path.join(self.connection.scratch_dir, job_name)
            )

            # Upload to colony
            self.file_manager.upload_file(
                slurm_script,
                os.path.join(
                    self.connection.colony_dir, job_name, f"{job_name}_dmn.slurm"
                ),
            )

        except Exception as e:
            logging.error(f"Error preparing DMN input files for {job_name}: {e}")
            raise

    def collect_results(self, job_name):
        """Collect DMN calculation results."""
        try:
            # DMN outputs several files needed for subsequent calculations
            colony_dir = os.path.join(self.connection.colony_dir, job_name)
            required_files = [f"{job_name}.dm2"]

            # Verify all required output files exist
            for file in required_files:
                file_path = os.path.join(colony_dir, file)
                if not self.commands.check_file_exists(file_path):
                    raise FileNotFoundError(
                        f"Required DMN output file {file} not found"
                    )

            return {"status": "completed", "output_files": required_files}

        except Exception as e:
            logging.error(f"Error collecting DMN results for {job_name}: {e}")
            raise

    def handle_calculation(self, job_name):
        """Handle complete DMN calculation workflow."""
        try:
            # Prepare directories
            self.prepare_directories(job_name)

            # Prepare input files
            self.prepare_input_files(job_name)

            # Move required files to scratch
            files_to_move = [f"{job_name}_dmn.slurm", f"{job_name}.log"]

            for file in files_to_move:
                self.move_to_scratch(job_name, file)

            # Submit and monitor
            job_id = self.submit_and_monitor(job_name, step="dmn")

            # Wait a bit to ensure file system sync
            time.sleep(1)

            # Retrieve results from scratch
            self.move_all_files_to_colony(job_name)

            # Collect and return results
            return self.collect_results(job_name)

        except Exception as e:
            logging.error(f"Error in DMN calculation for {job_name}: {e}")
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
    from input.molecules import Molecule
    from input.methods import Method
    from input.basis import BasisSet

    # Setup logging
    setup_logging(verbose_level=2)

    try:
        with ClusterConnection() as connection:
            # Initialize components
            file_manager = FileTransfer(connection)
            job_manager = JobManager(connection, file_manager)
            cleanup = ClusterCleanup(connection)

            # Test parameters
            test_name = "dmn_test"

            # First run Gaussian calculation to get required input
            print("\nRunning prerequisite Gaussian calculation...")
            molecule = Molecule(name="hydrogen_atom", multiplicity=2)
            method = Method("CISD")
            basis = BasisSet("sto-3g")

            gaussian = GaussianCalculation(connection, file_manager, job_manager)
            gaussian.handle_calculation(test_name, molecule, method, basis)

            # Now run DMN calculation
            print("\nTesting DMN calculation...")
            dmn_calc = DMNCalculation(connection, file_manager, job_manager)
            results = dmn_calc.handle_calculation(test_name)

            # Print results
            print("\nDMN Calculation results:")
            for key, value in results.items():
                print(f"{key}: {value}")

            # Clean up
            print("\nCleaning up...")
            cleanup.clean_calculation(test_name)

    except Exception as e:
        print(f"Test failed: {e}")
        try:
            cleanup.clean_calculation(test_name)
        except:
            pass
