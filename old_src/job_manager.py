import os
import logging
import time
from datetime import datetime
from logging_config import setup_logging, log_execution_time, create_log_for_calculation
from cluster_connection import ClusterConnection
from file_management import FileManager
from slurm_manager import SlurmManager
import pdb


class JobManager:
    def __init__(self, connection, file_manager, slurm_manager, log_dir="logs"):
        """
        Initializes the JobManager for handling SLURM jobs and other job-related tasks.
        """
        self.connection = connection
        self.file_manager = file_manager
        self.slurm_manager = slurm_manager
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    @log_execution_time
    def submit_job(self, job_name, step=None):
        """
        Submits a SLURM job using the generated script.

        Parameters:
        - job_name: The base name of the job (e.g., 'helium')
        - step: An optional step name (e.g., 'dmn', 'dm2prim', etc.) to append to job name
        """
        # If there's a step, modify the job_name accordingly
        full_job_name = job_name if step is None else f"{job_name}_{step}"

        # Submit the SLURM job using the script in the scratch directory
        command = (
            f"sbatch {self.connection.scratch_dir}/{job_name}/{full_job_name}.slurm"
        )
        output = self.connection.execute_command(command)

        if "Submitted batch job" in output:
            job_id = output.strip().split()[-1]
            logging.info(f"Submitted job with ID {job_id} for job {full_job_name}")
            return job_id
        else:
            raise RuntimeError(f"Failed to submit job. Command output: {output}")

    @log_execution_time
    def monitor_job(self, job_id, job_name=None, step=None):
        """
        Monitors the status of a SLURM job until it completes.
        Polls job status at exponentially increasing intervals (1, 2, 4, ... up to 60 seconds).

        Parameters:
        - job_id: The SLURM job ID to monitor.
        - job_name: The base name of the job (e.g., 'helium'). Optional, but useful for logging.
        - step: An optional step name (e.g., 'dmn', 'dm2prim', etc.) for clarity in logging.
        """
        start_time = datetime.now()

        # Combine job name and step for logging purposes
        full_job_name = job_name if step is None else f"{job_name}_{step}"
        logging.info(f"Monitoring job {job_id} for {full_job_name}...")

        delay = 1  # Start with 1 second delay
        max_delay = 60  # Maximum delay of 60 seconds

        # Chequeo inmediato tras la sumisión
        try:
            output = self.connection.execute_command(f"squeue -j {job_id}")
            if job_id not in output:
                end_time = datetime.now()
                runtime = end_time - start_time
                self.log_job_completion(job_id, start_time, end_time, runtime)
                logging.info(f"Job {job_id} for {full_job_name} completed immediately.")
                return "COMPLETED"
        except Exception as e:
            logging.error(f"Error in immediate check for job {job_id}: {e}")
            raise RuntimeError(f"Failed to monitor job {job_id}. Error: {e}")

        # If job didn't complete immediately, continue with exponential backoff
        while True:
            try:
                # Check the job status
                output = self.connection.execute_command(f"squeue -j {job_id}")

                # If the job ID is not in the output, the job has completed
                if job_id not in output:
                    end_time = datetime.now()
                    runtime = end_time - start_time

                    # Log job completion and runtime details
                    self.log_job_completion(job_id, start_time, end_time, runtime)
                    logging.info(
                        f"Job {job_id} for {full_job_name} completed after {runtime}."
                    )
                    return "COMPLETED"

                # Job is still running, log the status and wait
                logging.info(
                    f"Job {job_id} for {full_job_name} not completed yet, checking again in {delay} seconds."
                )
                time.sleep(delay)

                # Exponentially increase the delay, but cap it at max_delay (60 seconds)
                if delay < max_delay:
                    delay = min(delay * 2, max_delay)

            except Exception as e:
                # Log any errors encountered during monitoring
                logging.error(
                    f"Error while monitoring job {job_id} for {full_job_name}: {e}"
                )
                raise RuntimeError(f"Failed to monitor job {job_id}. Error: {e}")

    def log_job_completion(self, job_id, start_time, end_time, runtime):
        """
        Logs job completion details.
        """
        log_path = os.path.join(self.log_dir, "job_logs.txt")
        with open(log_path, "a") as f:
            f.write(
                f"Job ID: {job_id}\nStart Time: {start_time}\nEnd Time: {end_time}\nRuntime: {runtime}\n\n"
            )
        logging.info(f"Logged completion for job {job_id}.")

    @log_execution_time
    def handle_job(self, job_name, com_file_path):
        """
        Full job handling: Generates SLURM script, uploads files, submits the job, monitors, and retrieves results.
        """
        try:
            # Create the necessary directory in the colony for the job
            self.file_manager.create_calculation_directory(job_name)

            # Upload the Gaussian input (.com) file to the colony
            self.file_manager.upload_file_to_colony(com_file_path, job_name)

            # Generate the SLURM script
            slurm_script_path = self.slurm_manager.generate_gaussian_slurm(
                job_name, self.file_manager.get_scratch_dir(job_name)
            )

            self.file_manager.upload_file_to_colony(slurm_script_path, job_name)

            # Move the Gaussian input and SLURM script to scratch
            self.file_manager.move_to_scratch(job_name, os.path.basename(com_file_path))
            self.file_manager.move_to_scratch(
                job_name, os.path.basename(slurm_script_path)
            )

            # Submit the job
            job_id = self.submit_job(job_name)

            # Monitor the job until completion
            self.monitor_job(job_id)

            # Retrieve the results from scratch to colony
            self.file_manager.retrieve_results_from_scratch(job_name)

        except Exception as e:
            logging.error(f"Error handling job {job_name}: {e}")
            raise


if __name__ == "__main__":
    from src.molecule import Molecule
    from src.method import Method
    from src.basis import BasisSet
    from src.input_generator import InputFileGenerator

    # Set up logging
    job_name = "hydrogen_sp"
    log_file = create_log_for_calculation(job_name)
    setup_logging(verbose_level=2, log_file_name=log_file)

    # Initialize ClusterConnection and other components
    with ClusterConnection(config_file="utils/cluster_config.json") as connection:
        file_manager = FileManager(connection)
        slurm_manager = SlurmManager()
        job_manager = JobManager(connection, file_manager, slurm_manager)

        # Set up the job parameters
        hydrogen_atom = Molecule(name="hydrogen_atom", multiplicity=2)
        hf_method = Method("HF")
        sto3g_basis = BasisSet("sto-3g")

        # Generate the Gaussian input file
        generator = InputFileGenerator(
            config="SP",
            molecule=hydrogen_atom,
            method=hf_method,
            basis=sto3g_basis,
            title="Hydrogen SP Calculation",
            input_type="gaussian",
        )
        com_file_path = "test/hydrogen_sp.com"
        generator.generate_input_file(com_file_path)

        # Handle the job
        job_manager.handle_job(job_name, com_file_path)
