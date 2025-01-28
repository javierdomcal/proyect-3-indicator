"""
Base class for all calculation types.
"""

import os
import logging
from cluster.command import ClusterCommands


class Calculation:
    """Base class for all calculation types."""

    def __init__(self, connection, file_manager, job_manager):
        """Initialize calculation with necessary components."""
        self.connection = connection
        self.file_manager = file_manager
        self.job_manager = job_manager
        self.commands = ClusterCommands(connection)

    def prepare_directories(self, job_name):
        """Create and prepare necessary directories."""
        try:
            # Use forward slashes for cluster paths
            colony_dir = f"{self.connection.colony_dir}/{job_name}"
            scratch_dir = f"{self.connection.scratch_dir}/{job_name}"

            # Create directories
            self.commands.create_directory(colony_dir)
            self.commands.create_directory(scratch_dir)

            return colony_dir, scratch_dir
        except Exception as e:
            logging.error(f"Error preparing directories for {job_name}: {e}")
            raise

    def prepare_input_files(self, job_name, **kwargs):
        """Prepare input files for calculation."""
        raise NotImplementedError("Must be implemented by specific calculation class")

    def submit_and_monitor(self, job_name, step=None):
        """Submit job and monitor until completion."""
        try:
            job_id = self.job_manager.submit_and_monitor(job_name, step)
            return job_id
        except Exception as e:
            logging.error(f"Error in job submission/monitoring for {job_name}: {e}")
            raise

    def collect_results(self, job_name):
        """Collect calculation results."""
        raise NotImplementedError("Must be implemented by specific calculation class")

    def handle_calculation(self, job_name, **kwargs):
        """Main method to handle full calculation lifecycle."""
        raise NotImplementedError("Must be implemented by specific calculation class")

    def move_all_files_to_colony(self, job_name):
        """Move all files from scratch to colony."""
        try:
            scratch_dir = f"{self.connection.scratch_dir}/{job_name}"
            colony_dir = f"{self.connection.colony_dir}/{job_name}"

            # Ensure colony directory exists
            if not self.commands.check_directory_exists(colony_dir):
                self.commands.create_directory(colony_dir)

            # Move all files from scratch to colony
            move_cmd = f"cp -rf {scratch_dir}/* {colony_dir}/"
            self.commands.execute_command(move_cmd)

            logging.info(f"Moved all files from {scratch_dir} to {colony_dir}")

        except Exception as e:
            logging.error(f"Error moving files to colony for {job_name}: {e}")
            raise

    def move_to_scratch(self, job_name, filename):
        """Move a file from colony to scratch."""
        try:
            colony_dir = f"{self.connection.colony_dir}/{job_name}"
            scratch_dir = f"{self.connection.scratch_dir}/{job_name}"

            # Copy file from colony to scratch
            cmd = f"cp {colony_dir}/{filename} {scratch_dir}/"
            self.commands.execute_command(cmd)

            # Verify the file was copied successfully
            check_cmd = f"ls {scratch_dir}/{filename}"
            result = self.commands.execute_command(check_cmd)
            if result:
                logging.info(f"Moved {filename} from colony to scratch for {job_name}")
            else:
                raise FileNotFoundError(
                    f"Failed to copy {filename} to scratch directory"
                )

        except Exception as e:
            logging.error(f"Error moving {filename} to scratch for {job_name}: {e}")
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

    # Setup logging
    setup_logging(verbose_level=2)

    try:
        with ClusterConnection() as connection:
            # Initialize components
            file_manager = FileTransfer(connection)
            job_manager = JobManager(connection, file_manager)
            cleanup = ClusterCleanup(connection)

            # Create test calculation class
            class TestCalculation(Calculation):
                def prepare_input_files(self, job_name):
                    print(f"Preparing input files for {job_name}")

                def collect_results(self, job_name):
                    print(f"Collecting results for {job_name}")

                def handle_calculation(self, job_name):
                    print(f"Handling calculation for {job_name}")

            # Test calculations
            test_name = "calc_test"
            calc = TestCalculation(connection, file_manager, job_manager)

            print("\nTesting directory preparation...")
            colony_dir, scratch_dir = calc.prepare_directories(test_name)
            print(
                f"Created directories:\n  Colony: {colony_dir}\n  Scratch: {scratch_dir}"
            )

            # Clean up
            print("\nCleaning up...")
            cleanup.clean_calculation(test_name)

    except Exception as e:
        print(f"Test failed: {e}")
