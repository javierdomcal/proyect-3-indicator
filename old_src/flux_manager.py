import logging
from job_manager import JobManager
from file_management import FileManager


class FluxManager:
    def __init__(self, connection, file_manager, job_manager):
        """
        Initializes the FluxManager for managing and coordinating multiple jobs in a flux.
        """
        self.connection = connection
        self.file_manager = file_manager
        self.job_manager = job_manager
        # Use an in-memory dictionary to track completed fluxes for now
        self.completed_fluxes = {}

    def log_flux(self, job_name, molecule, method, base, status, runtime, errors=""):
        """
        Logs a completed flux into an in-memory dictionary instead of a CSV.
        """
        self.completed_fluxes[job_name] = {
            "molecule": molecule,
            "method": method,
            "base": base,
            "status": status,
            "runtime": runtime,
            "errors": errors,
        }
        logging.info(f"Flux {job_name} logged with status: {status}")

    def check_if_flux_completed(self, job_name):
        """
        Checks if the given flux has already been completed successfully.
        """
        return (
            job_name in self.completed_fluxes
            and self.completed_fluxes[job_name]["status"] == "completed"
        )

    def handle_flux(self, jobs):
        """
        Handles the execution of a flux, including launching and monitoring jobs sequentially.

        Parameters:
        - jobs: List of job configurations (each job being a dictionary with molecule, method, base, etc.)
        """
        try:
            # Execute jobs in sequence
            for job in jobs:
                job_name = job["job_name"]

                if self.check_if_flux_completed(job_name):
                    logging.info(
                        f"Flux {job_name} already completed. Skipping execution."
                    )
                    continue

                com_file_path = job["com_file_path"]
                self.file_manager.create_calculation_directory(job_name)
                self.job_manager.handle_job(job_name, com_file_path)

                # Once the job is complete, log the flux as completed
                self.log_flux(
                    job_name,
                    job["molecule"],
                    job["method"],
                    job["base"],
                    "completed",
                    "runtime_placeholder",
                )

        except Exception as e:
            logging.error(f"Error during flux execution: {e}")
            raise


if __name__ == "__main__":
    # Set up connection, file management, and job management systems
    from cluster_connection import ClusterConnection
    from file_management import FileManager
    from job_manager import JobManager
    from slurm_manager import SlurmManager
    from molecule import Molecule
    from method import Method
    from basis import BasisSet
    from input_generator import InputFileGenerator

    with ClusterConnection(config_file="utils/cluster_config.json") as connection:
        file_manager = FileManager(connection)
        job_manager = JobManager(connection, file_manager, SlurmManager())

        flux_manager = FluxManager(connection, file_manager, job_manager)

        # Example molecule, method, and basis for job generation
        helium = Molecule(name="helium")
        hf_method = Method("HF")
        sto3g_basis = BasisSet("sto-3g")

        # Create Gaussian input file (.com) for the job
        job_name = "helium"
        generator = InputFileGenerator(
            config="SP",
            molecule=helium,
            method=hf_method,
            basis=sto3g_basis,
            title="Helium SP Calculation",
            input_type="gaussian",
        )
        com_file_path = f"test/{job_name}.com"
        generator.generate_input_file(com_file_path)

        # Example list of jobs in a flux
        jobs = [
            {
                "job_name": job_name,
                "com_file_path": com_file_path,
                "molecule": "helium",
                "method": "HF",
                "base": "sto-3g",
            }
        ]

        # Handle the flux (jobs are executed sequentially)
        flux_manager.handle_flux(jobs)
