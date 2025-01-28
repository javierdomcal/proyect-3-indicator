import os
import logging
from flux_manager import FluxManager
import pdb
import pandas as pd
import time
from cluster_connection import ClusterConnection
from file_management import FileManager
from gaussian_log_parser import parse_gaussian_log


class FluxCorrelationIndicator(FluxManager):
    def __init__(self, connection, file_manager, job_manager):
        """
        Initializes the FluxCorrelationIndicator for handling specific fluxes related to correlation indicators.
        Inherits from FluxManager and adds specific processes for this type of flux.
        """
        super().__init__(connection, file_manager, job_manager)

    def modify_log_file(self, job_name):
        """
        Modifies the Gaussian log file after the calculation to include important information and additional data.
        The log file exists on the remote system, so file operations must be done via remote commands.
        """
        # Use the colony directory to form the path for the log file
        colony_dir = self.file_manager.get_colony_dir(job_name)
        log_file = os.path.join(colony_dir, f"{job_name}.log")

        # Debug: Print the exact file path being used
        logging.debug(f"Looking for log file at: {log_file}")

        # Verify permisions
        permissions = self.connection.execute_command(f"stat -c '%A' {log_file}")
        logging.debug(f"Current permissions for {log_file}: {permissions}")

        # Use a remote command to check if the log file exists on the remote system
        file_exists = self.connection.execute_command(
            f"test -f {log_file} && echo 'exists' || echo 'not found'"
        ).strip()

        if file_exists == "not found":
            raise FileNotFoundError(
                f"{job_name}.log not found in colony directory on the remote system."
            )

        # Use a remote command to read the log file from the remote system
        log_file_content = self.connection.execute_command(f"cat {log_file}")

        # Split the content into lines for further processing
        lines = log_file_content.splitlines()

        # Save the original file name and create a new one
        original_file = f'{log_file.replace(".log", "")}.original.log'
        modified_file = log_file  # The modified file will overwrite the original

        # Copy the original content to the original file (remote copy)
        self.connection.execute_command(f"cp {log_file} {original_file}")

        # Modify the content (same logic as before)
        index_basis = None
        for i, line in enumerate(lines):
            if "basis functions" in line and "primitive gaussians" in line:
                index_basis = i
                break

        if index_basis is None or index_basis + 1 >= len(lines):
            raise ValueError(
                "Could not find 'basis functions' and 'electrons' lines in the file."
            )

        important_lines = lines[index_basis : index_basis + 2]
        index_symmetry = None
        for i, line in enumerate(lines):
            if (
                "Two-electron integral symmetry is turned on" in line
                or "Two-electron integral symmetry is turned off" in line
            ):
                index_symmetry = i
                break

        if index_symmetry is None:
            raise ValueError(
                "Could not find the 'Two-electron integral symmetry' line in the file."
            )

        # lines.insert(index_symmetry + 1, important_lines[1])  # Second important line (electrons)
        # lines.insert(index_symmetry + 1, important_lines[0])  # First important line (basis functions)

        additional_text = [
            " ",
            " Thresholds for DMn (READ, WRITE)",
            " 1d-10 1d-10",
            " DMs to compute",
            " 2 1 2",
            " DM2HF",
            " DM2SD",
            " ",
        ]

        if "Normal termination" not in lines[-1]:
            raise ValueError(
                "The file does not appear to have terminated correctly ('Normal termination' not found)."
            )

        lines.extend(additional_text)

        # Save the modified file remotely (using echo and redirection)
        modified_content = "\n".join(lines)
        # Define the full path in /tmp for the file
        temp_file_path = f"/tmp/{job_name}.log"

        # Write the modified content to the file in /tmp
        try:
            with open(temp_file_path, "w") as temp_file:
                temp_file.write(modified_content)
            logging.info(f"Temporary file created at {temp_file_path}")

            # Use upload_file_to_colony to transfer the temporary file to the remote directory
            self.file_manager.upload_file_to_colony(temp_file_path, job_name)
            logging.info(
                f"Successfully uploaded {temp_file_path} to remote directory with title '{job_name}'"
            )
        except Exception as e:
            logging.error(f"Failed to upload {temp_file_path}: {e}")
            raise
        finally:
            # Clean up the file from /tmp after upload
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logging.info(f"Temporary file {temp_file_path} deleted after upload")

        logging.info(f"Modified log file for job {job_name} on remote system")

    def rename_output_files(self, job_name):
        """
        Renames the output files after the Gaussian calculation.
        - Renames Test.FChk to {job_name}.fchk
        """
        colony_dir = self.file_manager.get_colony_dir(job_name)
        fchk_file = os.path.join(colony_dir, "Test.FChk")

        if (
            self.connection.execute_command(
                f"test -f {fchk_file} && echo 'exists' || echo 'not found'"
            ).strip()
            == "exists"
        ):
            new_fchk_file = os.path.join(colony_dir, f"{job_name}.fchk")
            self.connection.execute_command(f"mv {fchk_file} {new_fchk_file}")
            logging.info(f"Renamed {fchk_file} to {new_fchk_file}")
        else:
            raise FileNotFoundError(f"Test.FChk not found in {colony_dir}")

    def handle_gaussian_atlas(self, job_name, molecule, method, basis):
        """
        Handles the Gaussian job execution for correlation indicator calculations.
        """
        try:
            logging.info(f"Handling Gaussian job {job_name}")

            # Step 1: Generate the .com file for Gaussian
            from input_generator import InputFileGenerator

            generator = InputFileGenerator(
                config="Opt",
                molecule=molecule,
                method=method,
                basis=basis,
                title=job_name,
                input_type="gaussian",
            )
            com_file_path = f"test/{job_name}.com"
            generator.generate_input_file(wfx=True)
            logging.info(f"Generated Gaussian .com file at {com_file_path}")

            self.file_manager.create_colony_directory(job_name)
            # Step 2: Upload .com to Colony
            self.file_manager.upload_file_to_colony(com_file_path, job_name)

            # Step 3: Generate the SLURM script
            slurm_script_path = self.job_manager.slurm_manager.generate_gaussian_slurm(
                job_name, self.file_manager.get_scratch_dir(job_name)
            )
            logging.info(f"Generated SLURM script at {slurm_script_path}")

            # Step 4: Upload SLURM script to Colony
            self.file_manager.upload_file_to_colony(slurm_script_path, job_name)

            # Step 5: Create folder in Scratch and move files
            self.file_manager.create_scratch_directory(job_name)
            self.file_manager.move_to_scratch(f"{job_name}", f"{job_name}.slurm")
            self.file_manager.move_to_scratch(f"{job_name}", f"{job_name}.com")
            logging.info(
                f"Moved Gaussian input and SLURM script to Scratch for job {job_name}"
            )

            # Step 6: Submit the job with sbatch
            job_id = self.job_manager.submit_job(job_name)
            logging.info(f"Gaussian job {job_name} submitted with ID {job_id}")

            # Step 7: Monitor the job until completion
            self.job_manager.monitor_job(job_id)

            # Step 8: Copy exit files from Scratch to Colony
            self.file_manager.change_directory(
                f"/dipc/javidom/proyect-3-indicator/{job_name}"
            )
            self.file_manager.retrieve_results_from_scratch(job_name)
            logging.info(f"Results for Gaussian job {job_name} copied back to Colony")

            # Step 10: Other log information to retrieve
            log_file_path = f"/dipc/javidom/proyect-3-indicator/{job_name}.log"
            logging.info(f"Reading log file from: {log_file_path}")

            try:
                log_content = self.file_manager.read_remote_file(log_file_path)
                results = parse_gaussian_log(log_content, is_content=True)
                logging.info("Successfully parsed Gaussian log file")
            except Exception as e:
                logging.error(f"Error reading or parsing log file: {e}")
                # Add diagnostic information
                self.file_manager.connection.execute_command(f"ls -l {log_file_path}")
                raise

            # Step 9: Clean Scratch directory
            self.file_manager.clean_scratch_directory(job_name)
            logging.info(f"Scratch directory for {job_name} cleaned.")

            return results

        except Exception as e:
            logging.error(f"Error handling Gaussian job {job_name}: {e}")
            raise

    def handle_gaussian_llum(self, job_name, molecule, method, basis):
        """
        Handles the Gaussian job execution for correlation indicator calculations.
        """
        try:
            logging.info(f"Handling Gaussian job {job_name} in Llum")

            # Llum connection
            with ClusterConnection(
                config_file="utils/cluster_config.json", cluster_name="llum"
            ) as llum_connection:
                # Step 1: Generate the .com file for Gaussian
                from input_generator import InputFileGenerator

                generator = InputFileGenerator(
                    config="Opt",
                    molecule=molecule,
                    method=method,
                    basis=basis,
                    title=job_name,
                    input_type="gaussian",
                )
                com_file_path = f"test/{job_name}.com"
                generator.generate_input_file(wfx=False)
                logging.info(f"Generated Gaussian .com file at {com_file_path}")

                llum_file_manager = FileManager(llum_connection)

                llum_file_manager.create_colony_directory(job_name)
                # Step 2: Upload .com to Colony
                llum_file_manager.upload_file_to_colony(com_file_path, job_name)

                keyword = "cas" if method.is_casscf else "c02"

                llum_connection.execute_command(
                    "source /soft/compilers/intel/oneapi/setvars.sh"
                )

                # Step 4: Launch Gaussian calculation
                # Construct the Gaussian command based on the keyword
                input_file = (
                    f"{llum_file_manager.get_colony_dir(job_name)}/{job_name}.com"
                )
                output_file = (
                    f"{llum_file_manager.get_colony_dir(job_name)}/{job_name}.log"
                )
                command = f"""
                    export g03root="/soft/quantum/g03cas"
                    source $g03root/g03/bsd/g03.profile
                    export GAUSS_SCRDIR=/scratch/g03/$USER/$$
                    mkdir -p $GAUSS_SCRDIR
                    g03 < {input_file} > {output_file}
                    rm -rf $GAUSS_SCRDIR
                """
                # Execute the command on Llum
                llum_connection.execute_command(command, wait=True)
                logging.info(
                    f"Launched Gaussian job '{job_name}' on Llum with command: {command}"
                )

                self.file_manager.create_colony_directory(job_name)
                # Step 5: Transfer results to the primary cluster's colony directory
                self.file_manager.transfer_between_clusters(
                    source_conn=llum_connection, job_name=job_name, extension=".com"
                )
                self.file_manager.transfer_between_clusters(
                    source_conn=llum_connection, job_name=job_name, extension=".log"
                )
                self.file_manager.transfer_between_clusters(
                    source_conn=llum_connection,
                    job_name=job_name,
                    file_name="Test",
                    extension=".FChk",
                )

                logging.info(
                    f"Transferred results for {job_name} from Llum to Atlas colony folder"
                )

        except Exception as e:
            logging.error(f"Error handling Gaussian job {job_name}: {e}")
            raise

    def handle_dmn(self, job_name):
        """
        Handles the DMN step after the Gaussian job, but keeps all operations within the 'job_name' directory.
        """
        try:
            logging.info(f"Handling DMN job for {job_name}")

            # Ensure the directory for the main job exists (if necessary, though it should already exist)
            self.file_manager.create_scratch_directory(
                f"{job_name}"
            )  # No step suffix here

            # Generate the DMN SLURM script (but still use the base job_name for directories)
            scratch_dir = self.file_manager.get_scratch_dir(job_name)
            dmn_slurm = self.job_manager.slurm_manager.generate_dmn_slurm(
                job_name, scratch_dir
            )
            logging.info(f"Generated DMN SLURM script at {dmn_slurm}")

            # Upload DMN SLURM script to Colony
            self.file_manager.upload_file_to_colony(dmn_slurm, job_name)

            self.file_manager.change_directory(
                f"/dipc/javidom/proyect-3-indicator/{job_name}"
            )

            # Modify the log file
            self.modify_log_file(job_name)
            time.sleep(1)

            # Move the SLURM script to Scratch and submit the job
            self.file_manager.move_to_scratch(f"{job_name}", f"{job_name}_dmn.slurm")
            self.file_manager.move_to_scratch(f"{job_name}", f"{job_name}.log")

            job_id = self.job_manager.submit_job(
                job_name, step="dmn"
            )  # No step suffix, using base job_name
            logging.info(f"DMN job submitted for {job_id}")

            # Monitor and handle results
            self.job_manager.monitor_job(job_id, step="dmn")  # No step suffix
            self.file_manager.change_directory(
                f"/dipc/javidom/proyect-3-indicator/{job_name}"
            )

            self.file_manager.retrieve_results_from_scratch(job_name)
            self.file_manager.clean_scratch_directory(job_name)
            logging.info(f"DMN job for {job_name} completed and results handled.")

        except Exception as e:
            logging.error(f"Error handling DMN flux for job {job_name}: {e}")
            raise

    def handle_dm2prim(self, job_name):
        """
        Handles the DM2PRIM step after the DMN job.
        """
        try:
            logging.info(f"Handling DM2PRIM job for {job_name}")

            # Generate and submit DM2PRIM SLURM script
            scratch_dir = self.file_manager.get_scratch_dir(job_name)
            dm2prim_slurm = self.job_manager.slurm_manager.generate_dm2prim_slurm(
                job_name, scratch_dir
            )
            self.file_manager.upload_file_to_colony(dm2prim_slurm, job_name)

            # Modify filename
            self.rename_output_files(job_name)

            time.sleep(1)

            self.file_manager.move_to_scratch(
                f"{job_name}", f"{job_name}_dm2prim.slurm"
            )
            self.file_manager.move_to_scratch(f"{job_name}", f"{job_name}.dm2")
            self.file_manager.move_to_scratch(f"{job_name}", f"{job_name}.fchk")

            job_id = self.job_manager.submit_job(job_name, step="dm2prim")
            logging.info(f"DM2PRIM job submitted for {job_id}")

            # Monitor and handle results
            self.job_manager.monitor_job(job_id, step="dm2prim")
            self.file_manager.change_directory(
                f"/dipc/javidom/proyect-3-indicator/{job_name}"
            )

            self.file_manager.retrieve_results_from_scratch(job_name)
            self.file_manager.clean_scratch_directory(job_name)
            logging.info(f"DM2PRIM job for {job_name} completed and results handled.")

        except Exception as e:
            logging.error(f"Error handling DM2PRIM flux for job {job_name}: {e}")
            raise

    def handle_inca(self, job_name, molecule, method, basis):
        """
        Handles the INCA step after the DM2PRIM job.
        """
        try:
            logging.info(f"Handling INCA job for {job_name}")

            from input_generator import InputFileGenerator

            generator = InputFileGenerator(
                config="SP",
                molecule=molecule,
                method=method,
                basis=basis,
                title=job_name,
                input_type="inca",
            )
            inp_file_path = f"test/{job_name}.inp"
            generator.generate_input_file()
            logging.info(f"Generated Input .inp file at {inp_file_path}")
            self.file_manager.upload_file_to_colony(inp_file_path, job_name)

            # Generate and submit INCA SLURM script
            scratch_dir = self.file_manager.get_scratch_dir(job_name)
            inca_slurm = self.job_manager.slurm_manager.generate_inca_slurm(
                job_name, scratch_dir
            )
            self.file_manager.upload_file_to_colony(inca_slurm, job_name)

            self.file_manager.move_to_scratch(f"{job_name}", f"{job_name}_inca.slurm")
            self.file_manager.move_to_scratch(f"{job_name}", f"{job_name}.inp")
            self.file_manager.move_to_scratch(f"{job_name}", f"{job_name}.wfx")
            self.file_manager.move_to_scratch(f"{job_name}", f"{job_name}.dm2p")

            job_id = self.job_manager.submit_job(job_name, step="inca")
            logging.info(f"INCA job submitted for {job_id}")

            # Monitor and handle results
            self.job_manager.monitor_job(job_id, step="inca")
            self.file_manager.change_directory(
                f"/dipc/javidom/proyect-3-indicator/{job_name}"
            )

            self.file_manager.retrieve_results_from_scratch(job_name)
            self.file_manager.clean_scratch_directory(job_name)
            logging.info(f"INCA job for {job_name} completed and results handled.")

        except Exception as e:
            logging.error(f"Error handling INCA flux for job {job_name}: {e}")
            raise

    def retrieve_results(self, job_name):
        """
        Retrieves results from Colony or Scratch to the local machine.
        """
        try:
            logging.info(f"Retrieving results for {job_name}")
            self.file_manager.download_file_from_colony("ontop.dat", "./test", job_name)
            logging.info(f"Results for {job_name} retrieved to local machine.")
        except Exception as e:
            logging.error(f"Error retrieving results for {job_name}: {e}")
            raise

    def handle_flux(self, job_name, molecule, method, basis):
        """
        Manages the entire execution of the flux, including Gaussian, DMN, DM2PRIM, and INCA steps.
        Executes everything sequentially.
        """
        try:
            logging.info(f"Starting flux handling for {job_name}")

            # Step 1: Gaussian job

            calculation_data = self.handle_gaussian_atlas(
                job_name, molecule, method, basis
            )

            # Step 2: DMN step
            self.handle_dmn(job_name)

            # Step 3: DM2PRIM step
            self.handle_dm2prim(job_name)

            # Step 4: INCA step
            self.handle_inca(job_name, molecule, method, basis)

        except Exception as e:
            logging.error(f"Error during flux {job_name}: {e}")
            raise

        return calculation_data


if __name__ == "__main__":
    # Set up connection, file management, and job management systems
    from cluster_connection import ClusterConnection
    from file_management import FileManager
    from job_manager import JobManager
    from slurm_manager import SlurmManager
    from molecule import Molecule
    from method import Method
    from basis import BasisSet

    # Establish the connection and initialize the necessary components
    logging.basicConfig(level=logging.INFO)

    # Initialize test inputs
    job_name = "helium_test_casscf"
    molecule = Molecule(name="helium")
    method = Method("CASSCF(2,2)")
    basis = BasisSet("6-31G")

    # Establish the primary connection and file manager for Atlas cluster
    with ClusterConnection(
        config_file="utils/cluster_config.json", cluster_name="atlas"
    ) as connection:
        file_manager = FileManager(connection)

        # Instantiate and execute Gaussian on Llum cluster
        flux_manager = FluxCorrelationIndicator(
            connection, file_manager, job_manager=None
        )  # assuming job_manager is optional for this test
        flux_manager.handle_gaussian_llum(job_name, molecule, method, basis)

        # Read and print the log file to confirm execution
        log_file_path = f"{file_manager.get_colony.dir(job_name)}/{job_name}.log"
        with open(log_file_path, "r") as log_file:
            print(log_file.read())
