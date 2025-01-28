"""
Job monitoring functionality.
"""

import os
import time
import logging
from datetime import datetime
from cluster.command import ClusterCommands


class JobMonitor:
    def __init__(self, connection):
        """Initialize with cluster connection."""
        self.connection = connection
        self.commands = ClusterCommands(connection)
        self.delay = 1  # Initial delay in seconds
        self.max_delay = 60  # Maximum delay in seconds

    def monitor_job(self, job_id, job_name=None, step=None):
        """Monitor a SLURM job until completion."""
        start_time = datetime.now()

        # Log monitoring start
        full_name = job_name if step is None else f"{job_name}_{step}"
        logging.info(f"Monitoring job {job_id} for {full_name}...")

        delay = self.delay
        while True:
            try:
                # Check job status
                output = self.commands.execute_command(f"squeue -j {job_id}")

                # If job not in queue, it's completed
                if job_id not in output:
                    end_time = datetime.now()
                    runtime = end_time - start_time
                    self._log_completion(job_id, start_time, end_time, runtime)
                    logging.info(
                        f"Job {job_id} for {full_name} completed after {runtime}"
                    )
                    return "COMPLETED"

                # Job still running
                logging.info(
                    f"Job {job_id} for {full_name} still running, checking again in {delay} seconds"
                )
                time.sleep(delay)

                # Exponential backoff for delay
                if delay < self.max_delay:
                    delay = min(delay * 2, self.max_delay)

            except Exception as e:
                logging.error(f"Error monitoring job {job_id}: {e}")
                raise

    def check_job_status(self, job_id):
        """Get current status of a job."""
        try:
            output = self.commands.execute_command(f"squeue -j {job_id}")

            if job_id not in output:
                return "COMPLETED"

            # Parse status from squeue output
            lines = output.strip().split("\n")
            if len(lines) > 1:  # Skip header
                status = lines[1].split()[4]  # Status column
                return status
            return "UNKNOWN"

        except Exception as e:
            logging.error(f"Error checking status for job {job_id}: {e}")
            raise

    def _log_completion(self, job_id, start_time, end_time, runtime):
        """Log job completion details."""
        try:
            log_file = f"logs/job_{job_id}.log"
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            with open(log_file, "a") as f:
                f.write(f"Job ID: {job_id}\n")
                f.write(f"Start Time: {start_time}\n")
                f.write(f"End Time: {end_time}\n")
                f.write(f"Runtime: {runtime}\n\n")

        except Exception as e:
            logging.error(f"Error logging completion for job {job_id}: {e}")


if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from utils.log_config import setup_logging
    from cluster.connection import ClusterConnection
    from cluster.command import ClusterCommands
    from cluster.cleanup import ClusterCleanup

    # Setup logging
    setup_logging(verbose_level=2)

    try:
        with ClusterConnection() as connection:
            commands = ClusterCommands(connection)
            monitor = JobMonitor(connection)
            cleanup = ClusterCleanup(connection)

            # Test job submission and monitoring
            test_name = "monitor_test"

            # Submit a simple test job
            output = commands.execute_command(
                f"sbatch --wrap='sleep 10' --job-name={test_name}"
            )

            if "Submitted batch job" in output:
                job_id = output.strip().split()[-1]
                print(f"\nSubmitted test job: {job_id}")

                # Monitor the job
                print("\nMonitoring job...")
                status = monitor.monitor_job(job_id, test_name)
                print(f"Final status: {status}")

            # Cleanup
            print("\nCleaning up...")
            cleanup.clean_calculation(test_name)

    except Exception as e:
        print(f"Test failed: {e}")
