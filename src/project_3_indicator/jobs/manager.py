"""
Main job management functionality.
"""

import os
import logging
from ..jobs.monitoring import JobMonitor
from ..jobs.submission import JobSubmitter
from ..cluster.command import ClusterCommands


class JobManager:
    def __init__(self, connection, file_manager):
        """Initialize job manager with necessary components."""
        self.connection = connection
        self.commands = ClusterCommands(connection)
        self.file_manager = file_manager
        self.monitor = JobMonitor(connection)
        self.submitter = JobSubmitter(connection)


    def submit_and_monitor(self, job_name, step=None):
        """Submit a job and monitor it until completion."""
        try:
            job_id = self.submitter.submit_job(job_name, step)
            logging.info(f"Submitted job {job_id} for {job_name}_{step}")

            self.monitor.monitor_job(job_id, job_name, step)
            logging.info(f"Job {job_id} completed successfully")

            return job_id
        except Exception as e:
            logging.error(f"Error in job submission/monitoring for {job_name}: {e}")
            raise


if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from utils.log_config import setup_logging
    from cluster.connection import ClusterConnection
    from cluster.transfer import FileTransfer
    from cluster.command import ClusterCommands
    from cluster.cleanup import ClusterCleanup

    # Setup logging
    setup_logging(verbose_level=2)

    try:
        with ClusterConnection() as connection:
            # Initialize components
            file_manager = FileTransfer(connection)
            commands = ClusterCommands(connection)
            job_manager = JobManager(connection, file_manager)
            cleanup = ClusterCleanup(connection)

            # Test parameters
            test_name = "job_test"

            # Create test directories and files
            print("\nSetting up test environment...")
            os.makedirs("test", exist_ok=True)
            test_file = os.path.join("test", f"{test_name}.com")
            with open(test_file, "w") as f:
                f.write(
                    "%chk=test.chk\n%mem=1GB\n#P HF/STO-3G\n\nTest Job\n\n0 1\nH 0 0 0\n\n"
                )

            # Create cluster directories
            scratch_dir = os.path.join(connection.scratch_dir, test_name)
            colony_dir = os.path.join(connection.colony_dir, test_name)
            commands.create_directory(scratch_dir)
            commands.create_directory(colony_dir)

            print("\nTesting job handling...")
            job_manager.handle_job(test_name, test_file)

            # Cleanup
            print("\nCleaning up...")
            cleanup.clean_calculation(test_name)
            if os.path.exists(test_file):
                os.remove(test_file)
                print(f"Removed local file: {test_file}")

    except Exception as e:
        print(f"Test failed: {e}")
        # Try to cleanup even if test failed
        try:
            cleanup.clean_calculation(test_name)
            if os.path.exists(test_file):
                os.remove(test_file)
        except:
            pass
