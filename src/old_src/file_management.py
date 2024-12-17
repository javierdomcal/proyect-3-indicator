import os
import logging
from cluster_connection import ClusterConnection
from logging_config import setup_logging, log_execution_time  # Assuming your custom logging module is logging_config
import pandas as pd
import paramiko

class FileManager:
    def __init__(self, connection):
        """
        Initializes the FileManager for handling file operations between local, colony, and scratch.
        """
        self.connection = connection

    def get_colony_dir(self, title):
        """
        Returns the colony directory for the given title.
        """
        return os.path.join(self.connection.colony_dir, title)

    def get_scratch_dir(self, title):
        """
        Returns the scratch directory for the given title.
        """
        return os.path.join(self.connection.scratch_dir, title)

    @log_execution_time
    def create_colony_directory(self, title):
        """
        Creates a directory in the colony for a specific job, using title as the folder name.
        """
        try:
            colony_dir = self.get_colony_dir(title)
            self.connection.execute_command(f"mkdir -p {colony_dir}")
            logging.info(f"Created colony directory: {colony_dir}")
        except Exception as e:
            logging.error(f"Error creating colony directory for job {title}: {e}")
            raise

    @log_execution_time
    def create_scratch_directory(self, title):
        """
        Creates a directory in the scratch for a specific job, using title as the folder name.
        """
        try:
            scratch_dir = self.get_scratch_dir(title)
            self.connection.execute_command(f"mkdir -p {scratch_dir}")
            logging.info(f"Created scratch directory: {scratch_dir}")
        except Exception as e:
            logging.error(f"Error creating scratch directory for job {title}: {e}")
            raise

    @log_execution_time
    def upload_file_to_colony(self, local_path, title):
        """
        Uploads a file from the local system to the colony directory with the given title.
        """
        if not os.path.exists(local_path):
            raise ValueError(f"Local file {local_path} does not exist.")

        remote_path = os.path.join(self.get_colony_dir(title), os.path.basename(local_path))
        try:
            self.connection.upload_file(local_path, remote_path)
            logging.info(f"Uploaded {local_path} to {remote_path}")
        except Exception as e:
            logging.error(f"Failed to upload {local_path} to {remote_path}: {e}")
            raise

    @log_execution_time
    def download_file_from_colony(self, filename, local_dir, title):
        """
        Downloads a file from the colony (remote cluster) to the local machine.
        
        Args:
            filename (str): The name of the file in the colony directory.
            local_dir (str): The local directory where the file should be saved.
        
        Raises:
            ValueError: If the specified local directory does not exist.
            Exception: For any connection or file transfer issues.
        """
        if not os.path.exists(local_dir):
            raise ValueError(f"Local directory {local_dir} does not exist.")

        # Construct the remote path from the filename and the colony directory
        remote_path = os.path.join(self.get_colony_dir(title), filename)

        # Construct the local path for the downloaded file
        local_file_path = os.path.join(local_dir, filename)

        try:
            # Use the connection object to download the file
            self.connection.download_file(remote_path, local_file_path)
            logging.info(f"Downloaded {remote_path} to {local_file_path}")
        except Exception as e:
            logging.error(f"Failed to download {remote_path} to {local_file_path}: {e}")
            raise

    @log_execution_time
    def move_to_scratch(self, title, filename):
        """
        Moves a file from the colony to the scratch directory for the given title.
        """
        colony_path = os.path.join(self.get_colony_dir(title), filename)
        scratch_path = os.path.join(self.get_scratch_dir(title), filename)

        try:
            self.connection.execute_command(f"cp {colony_path} {scratch_path}")
            self.connection.execute_command(f"chmod -R 777 {scratch_path}")
            logging.info(f"Copied {filename} from {colony_path} to {scratch_path}")
        except Exception as e:
            logging.error(f"Failed to copy {filename} from {colony_path} to {scratch_path}: {e}")
            raise

    @log_execution_time
    def retrieve_results_from_scratch(self, title):
        """
        Retrieves all result files from the scratch directory back to the colony for the given title.
        """
        colony_dir = self.get_colony_dir(title)
        scratch_dir = self.get_scratch_dir(title)

        try:
            self.connection.execute_command(f"mkdir -p {colony_dir}")
            self.connection.execute_command(f"cp -r {scratch_dir}/* {colony_dir}/")
            self.connection.execute_command(f"chmod -R 777 {colony_dir}/")

            logging.info(f"Retrieved results from {scratch_dir} to {colony_dir}")
        except Exception as e:
            logging.error(f"Failed to retrieve results from {scratch_dir} to {colony_dir}: {e}")
            raise

    @log_execution_time
    def clean_scratch_directory(self, title):
        """
        Deletes all contents from the scratch directory for the given title.
        """
        scratch_dir = self.get_scratch_dir(title)
        try:
            self.connection.execute_command(f"rm -rf {scratch_dir}/*")
            logging.info(f"Cleaned scratch directory: {scratch_dir}")
        except Exception as e:
            logging.error(f"Failed to clean scratch directory {scratch_dir}: {e}")
            raise

    @log_execution_time
    def change_directory(self, new_dir):
        """
        Changes the current working directory on the cluster.
        """
        try:
            self.connection.execute_command(f"cd {new_dir}")
            logging.info(f"Changed directory to {new_dir}")
        except Exception as e:
            logging.error(f"Failed to change directory to {new_dir}: {e}")
            raise


    def get_results(self, job_name, local_dir='/tmp'):
        """
        Retrieves the 'ontop.dat' file from the colony directory and loads it into a DataFrame.
        
        Args:
            job_name (str): The name of the job associated with the file.
            local_dir (str): The local directory to save the downloaded file.
            
        Returns:
            pd.DataFrame: The DataFrame containing data from the downloaded file.
        """
        try:
            logging.info(f"Retrieving results for {job_name}")
            
            # Ensure the local directory exists
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            
            # Use download_file_from_colony to download 'ontop.dat' to local_dir
            self.download_file_from_colony(filename='ontop.dat', local_dir=local_dir, title=job_name)
            
            # Load the downloaded file into a pandas DataFrame
            local_file_path = os.path.join(local_dir, 'ontop.dat')
            df = pd.read_csv(local_file_path)
            logging.info(f"Results for {job_name} retrieved and loaded into a pandas DataFrame.")
            
            return df
        except Exception as e:
            logging.error(f"Error retrieving results for {job_name}: {e}")
            raise

    def transfer_between_clusters(self, source_conn, job_name, file_name = None, extension='.log'):
        """
        Transfers a file from one cluster to another via local temporary storage.
        
        Parameters:
        - source_conn (ClusterConnection): Source cluster connection.
        - target_conn (ClusterConnection): Target cluster connection.
        - remote_source_path (str): Path of the file on the source cluster.
        - remote_target_path (str): Path to save the file on the target cluster.
        """
        temp_path = "/tmp/transfer_between_clusters.txt"

        if file_name == None:
            file_name = job_name
        target_path = self.get_colony_dir(job_name)
        source_path = os.path.join(source_conn.colony_dir, job_name)

        source_conn.download_file(source_path+'/'+file_name+extension, temp_path)
        self.connection.upload_file(temp_path, target_path+'/'+file_name+extension)
        os.remove(temp_path)
        logging.info(f"Transferred {source_path} from {source_conn.hostname} to {target_path} on {self.connection.hostname}.")


    def read_remote_file(self, file_path):
        """
        Reads a file from the remote cluster and returns its contents.
        
        Args:
            file_path (str): Absolute path to the file on the remote cluster
        
        Returns:
            str: Contents of the remote file
        """
        try:
            content = self.connection.execute_command(f"cat {file_path}")
            # Since execute_command returns a string directly, we don't need to call read()
            logging.info(f"Successfully read remote file: {file_path}")
            return content
        except Exception as e:
            logging.error(f"Failed to read remote file {file_path}: {e}")
            # Add diagnostic information
            try:
                ls_output = self.connection.execute_command(f"ls -l {file_path}")
                logging.error(f"File details: {ls_output}")
            except:
                pass
            raise


if __name__ == "__main__":
    from molecule import Molecule
    from method import Method
    from basis import BasisSet

    from input_generator import InputFileGenerator
    
    # Setup logging before starting
    setup_logging(verbose_level=1)  # Use appropriate verbose level

    # Initialize ClusterConnection and FileManager
    with ClusterConnection(config_file="utils/cluster_config.json") as connection:
        file_manager = FileManager(connection)

        # Test with the title "test_calculation"
        title = "test_calculation"
        molecule = Molecule(name="hydrogen_atom", multiplicity=2)
        method = Method("HF")
        basis = BasisSet("sto-3g")
        calc = InputFileGenerator(config="SP", molecule=molecule, method=method, basis=basis, title=title, input_type="gaussian")
        calc.generate_input_file(f"test/{title}.com")

        # Create directories in colony and scratch
        file_manager.create_colony_directory(title)
        file_manager.create_scratch_directory(title)

        # Upload a test file (ensure the file exists locally)
        local_file = "test/test_calculation.com"
        try:
            file_manager.upload_file_to_colony(local_file, title)
        except ValueError as e:
            logging.error(e)

        # Move file from colony to scratch
        try:
            file_manager.move_to_scratch(title, "test_calculation.com")
        except Exception as e:
            logging.error(e)

        # Retrieve results from scratch to colony
        file_manager.retrieve_results_from_scratch(title)

        # Clean up scratch directory
        file_manager.clean_scratch_directory(title)
