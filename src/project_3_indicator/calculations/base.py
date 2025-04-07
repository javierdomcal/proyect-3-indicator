"""
Base class for all calculation types.
"""

import os
import logging
from ..cluster.command import ClusterCommands
from ..cluster.cleanup import ClusterCleanup


class Calculation:
    """Base class for all calculation types."""

    def __init__(self, connection, file_manager, job_manager):
        """Initialize calculation with necessary components."""
        self.connection = connection
        self.file_manager = file_manager
        self.job_manager = job_manager
        self.commands = ClusterCommands(connection)
        self.cleanup = ClusterCleanup(connection)
        self.folder_name = None
        self.colony_dir = None
        self.scratch_dir = None

    def create_scratch_directory(self):
        """Create or clean scratch directory for calculation."""
        try:
            scratch_dir = f"{self.connection.scratch_dir}/{self.folder_name}"



            # Create fresh scratch directory
            self.commands.create_directory(scratch_dir)
            logging.info(f"Created fresh scratch directory: {scratch_dir}")
            return scratch_dir

        except Exception as e:
            logging.error(f"Error managing scratch directory for {self.folder_name}: {e}")
            raise

    def create_colony_directory(self):
        """Create or verify colony directory for calculation."""
        try:
            colony_dir = f"{self.connection.colony_dir}/{self.folder_name}"

            if self.commands.check_directory_exists(colony_dir):
                pass
            else:
                # Create new directory if it doesn't exist
                self.commands.create_directory(colony_dir)
                logging.info(f"Created new colony directory: {colony_dir}")

            return colony_dir

        except Exception as e:
            logging.error(f"Error managing colony directory for {self.folder_name}: {e}")
            raise

    def prepare_input_files(self, job_name, input_spec):
        """
        Prepare input files for calculation.
        Must be implemented by specific calculation class.
        """
        raise NotImplementedError("Must be implemented by specific calculation class")

    def submit_and_monitor(self, job_name, step=None):
        """Submit job and monitor until completion."""
        try:
            job_id = self.job_manager.submit_and_monitor(job_name, self.scratch_dir, step)
            logging.info(f"Job {job_id} completed successfully for {job_name}")
            return job_id
        except Exception as e:
            logging.error(f"Error in job submission/monitoring for {job_name}: {e}")
            raise



    def move_all_files_to_colony(self):
        """Move all files from scratch to colony."""
        try:


            # Move all files from scratch to colony
            move_cmd = f"cp -rf {self.scratch_dir}/* {self.colony_dir}/"
            self.commands.execute_command(move_cmd)


        except Exception as e:
            logging.error(f"Error moving files to colony for {self.folder_name}: {e}")
            raise

    def move_to_scratch(self, filename):
        """Move a file from colony to scratch."""
        try:


            # Copy file from colony to scratch
            cmd = f"cp {self.colony_dir}/{filename} {self.scratch_dir}/"
            self.commands.execute_command(cmd)

            # Verify the file was copied successfully
            check_cmd = f"ls {self.scratch_dir}/{filename}"
            result = self.commands.execute_command(check_cmd)
            if result:
                logging.info(f"Moved {filename} from colony to scratch for {self.folder_name}")
            else:
                raise FileNotFoundError(f"Failed to copy {filename} to scratch directory")

        except Exception as e:
            logging.error(f"Error moving {filename} to scratch for {self.folder_name}: {e}")
            raise

    def _move_required_files_to_scratch(self, job_name):
        """
        Move required files to scratch directory.
        Must be implemented by specific calculation class.
        """
        raise NotImplementedError("Must be implemented by specific calculation class")

    def create_folders(self, folder_name):
        """
        Create folders for colony and scratch directories.
        Args:
            folder_name (str): Name of the folder to create
        """
        self.folder_name = folder_name
        self.colony_dir = self.create_colony_directory()
        self.scratch_dir = self.create_scratch_directory()

    def handle_calculation(self, job_name, input_spec):
        """
        Template method that defines the calculation workflow.

        Args:
            job_name (str): Name of the calculation
            input_spec: Input specification object for the calculation
            **kwargs: Additional keyword arguments
        """
        try:

            if self.folder_name is None:
                self.create_folders(job_name)
            # 2. Prepare input files (implemented by subclass)
            # Pass input_spec and any additional kwargs to prepare_input_files
            step = self.prepare_input_files(job_name, input_spec)

            # 3. Move required files to scratch (implemented by subclass)
            self._move_required_files_to_scratch(job_name)

            # 4. Submit and monitor job
            job_id = self.submit_and_monitor(job_name, step)

            # 5. Retrieve results from scratch
            self.move_all_files_to_colony()


            # 7. Clean up scratch directory
            #self.cleanup.delete_scratch_folder(job_name)
            #logging.info(f"Deleted scratch directory for {job_name}")



        except Exception as e:
            # Ensure scratch cleanup happens even if calculation fails
            try:
                pass
                #self.cleanup.delete_scratch_folder(job_name)
                #logging.info(f"Cleaned up scratch directory after error for {job_name}")
            except Exception as cleanup_error:
                pass
                #logging.error(f"Error during cleanup for {job_name}: {cleanup_error}")

            #logging.error(f"Error in calculation for {job_name}: {e}")
            raise

