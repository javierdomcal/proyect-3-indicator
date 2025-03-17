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

    def create_scratch_directory(self, job_name):
        """Create or clean scratch directory for calculation."""
        try:
            scratch_dir = f"{self.connection.scratch_dir}/{job_name}"



            # Create fresh scratch directory
            self.commands.create_directory(scratch_dir)
            logging.info(f"Created fresh scratch directory: {scratch_dir}")
            return scratch_dir

        except Exception as e:
            logging.error(f"Error managing scratch directory for {job_name}: {e}")
            raise

    def create_colony_directory(self, job_name):
        """Create or verify colony directory for calculation."""
        try:
            colony_dir = f"{self.connection.colony_dir}/{job_name}"

            if self.commands.check_directory_exists(colony_dir):
                pass
            else:
                # Create new directory if it doesn't exist
                self.commands.create_directory(colony_dir)
                logging.info(f"Created new colony directory: {colony_dir}")

            return colony_dir

        except Exception as e:
            logging.error(f"Error managing colony directory for {job_name}: {e}")
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
            job_id = self.job_manager.submit_and_monitor(job_name, step)
            logging.info(f"Job {job_id} completed successfully for {job_name}")
            return job_id
        except Exception as e:
            logging.error(f"Error in job submission/monitoring for {job_name}: {e}")
            raise

    def move_all_files_to_colony(self, job_name):
        """Move all files from scratch to colony."""
        try:
            scratch_dir = f"{self.connection.scratch_dir}/{job_name}"
            colony_dir = f"{self.connection.colony_dir}/{job_name}"

            # Move all files from scratch to colony
            move_cmd = f"cp -rf {scratch_dir}/* {colony_dir}/"
            self.commands.execute_command(move_cmd)


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
                raise FileNotFoundError(f"Failed to copy {filename} to scratch directory")

        except Exception as e:
            logging.error(f"Error moving {filename} to scratch for {job_name}: {e}")
            raise

    def _move_required_files_to_scratch(self, job_name):
        """
        Move required files to scratch directory.
        Must be implemented by specific calculation class.
        """
        raise NotImplementedError("Must be implemented by specific calculation class")



    def handle_calculation(self, job_name, input_spec):
        """
        Template method that defines the calculation workflow.

        Args:
            job_name (str): Name of the calculation
            input_spec: Input specification object for the calculation
            **kwargs: Additional keyword arguments
        """
        try:
            # 1. Create/verify directories
            colony_dir = self.create_colony_directory(job_name)
            scratch_dir = self.create_scratch_directory(job_name)

            # 2. Prepare input files (implemented by subclass)
            # Pass input_spec and any additional kwargs to prepare_input_files
            step = self.prepare_input_files(job_name, input_spec)

            # 3. Move required files to scratch (implemented by subclass)
            self._move_required_files_to_scratch(job_name)

            # 4. Submit and monitor job
            job_id = self.submit_and_monitor(job_name, step)

            # 5. Retrieve results from scratch
            self.move_all_files_to_colony(job_name)


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


if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from utils.log_config import setup_logging
    from cluster.connection import ClusterConnection
    from cluster.transfer import FileTransfer
    from jobs.manager import JobManager
    from cluster.cleanup import ClusterCleanup
    from input.specification import InputSpecification
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

            # Create test calculation class
            class TestCalculation(Calculation):
                def prepare_input_files(self, job_name, input_spec=None, **kwargs):
                    print(f"Preparing input files for {job_name}")
                    # Create a test file in colony
                    test_file = f"{self.connection.colony_dir}/{job_name}/test.txt"
                    self.commands.execute_command(f"echo 'test content' > {test_file}")

                def _move_required_files_to_scratch(self, job_name):
                    print(f"Moving files to scratch for {job_name}")
                    self.move_to_scratch(job_name, "test.txt")


            # Test calculations
            test_name = "calc_test"

            # Create test input specification
            molecule = Molecule(name="helium")
            method = Method("HF")
            basis = BasisSet("sto-3g")
            input_spec = InputSpecification(
                molecule=molecule,
                method=method,
                basis=basis,
                title=test_name,
                config="SP"
            )

            calc = TestCalculation(connection, file_manager, job_manager)

            # Test with new directories
            print("\nTesting calculation with new directories...")
            results = calc.handle_calculation(test_name, input_spec=input_spec)
            print(f"Calculation results: {results}")

            # Test with existing colony directory
            print("\nTesting calculation with existing colony directory...")
            results = calc.handle_calculation(test_name, input_spec=input_spec)
            print(f"Calculation results: {results}")

            # Clean up
            print("\nCleaning up...")
            cleanup.clean_calculation(test_name)

    except Exception as e:
        print(f"Test failed: {e}")
        try:
            pass
            #cleanup.clean_calculation(test_name)
        except:
            pass