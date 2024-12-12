import os
from cluster_connection import ClusterConnection
from file_management import FileManager

class CalculationCleaner:
    def __init__(self, file_manager, slurm_dir="slurm_scripts", test_dir="test"):
        """
        Initializes the CalculationCleaner for deleting calculation-related files and directories.

        Parameters:
        - file_manager (FileManager): Instance of FileManager for managing file operations.
        - slurm_dir (str): Local directory where SLURM scripts are stored (default is "slurm_scripts").
        - test_dir (str): Local directory where the Gaussian .com files are stored (default is "test").
        """
        self.file_manager = file_manager
        self.slurm_dir = slurm_dir
        self.test_dir = test_dir

    def delete_scratch_folder(self, calculation_name):
        """
        Deletes the calculation's folder and contents in the scratch directory on the cluster.

        Parameters:
        - calculation_name (str): Name of the calculation folder to delete.
        """
        scratch_dir = self.file_manager.get_scratch_dir(calculation_name)
        
        # Command to delete the directory
        command = f"rm -rf {scratch_dir}"
        print(f"Executing: {command}")
        
        # Execute the command and capture output/errors
        output = self.file_manager.connection.execute_command(command)
        
        # Log the result or any errors
        if output:
            print(f"Error during deletion: {output}")
        else:
            # Check if directory still exists after attempting deletion
            check_command = f"test -d {scratch_dir} && echo 'exists' || echo 'deleted'"
            check_output = self.file_manager.connection.execute_command(check_command)
            
            if "exists" in check_output:
                print(f"Directory {scratch_dir} still exists. Check permissions or active jobs.")
            else:
                print(f"Successfully deleted {scratch_dir} from scratch.")

    def delete_colony_folder(self, calculation_name):
        """
        Deletes the calculation's folder and contents in the colony directory on the cluster.

        Parameters:
        - calculation_name (str): Name of the calculation folder to delete.
        """
        colony_dir = self.file_manager.get_colony_dir(calculation_name)
        self.file_manager.connection.execute_command(f"rm -rf {colony_dir}")
        print(f"Deleted {colony_dir} from colony.")

    def delete_local_com_file(self, calculation_name):
        """
        Deletes the .com file associated with the calculation in the local test directory.

        Parameters:
        - calculation_name (str): Name of the calculation file to delete.
        """
        com_file_path = os.path.join(self.test_dir, f"{calculation_name}.com")
        if os.path.exists(com_file_path):
            os.remove(com_file_path)
            print(f"Deleted {com_file_path} locally.")
        else:
            print(f"{com_file_path} not found.")

    def delete_slurm_script(self, calculation_name):
        """
        Deletes the SLURM script associated with the calculation in the local slurm_scripts directory.

        Parameters:
        - calculation_name (str): Name of the SLURM script file to delete.
        """
        slurm_file_path = os.path.join(self.slurm_dir, f"{calculation_name}.slurm")
        if os.path.exists(slurm_file_path):
            os.remove(slurm_file_path)
            print(f"Deleted {slurm_file_path} locally.")
        else:
            print(f"{slurm_file_path} not found.")

    def clean_calculation(self, calculation_name):
        """
        Deletes all related files and directories for a specific calculation.

        Parameters:
        - calculation_name (str): Name of the calculation to clean up.
        """
        self.delete_scratch_folder(calculation_name)
        self.delete_colony_folder(calculation_name)
        self.delete_local_com_file(calculation_name)
        self.delete_slurm_script(calculation_name)


if __name__ == "__main__":
    # Establish connection to the cluster
    connection = ClusterConnection(config_file="utils/cluster_config.json")
    connection.connect()

    try:
        # Initialize FileManager and CalculationCleaner
        file_manager = FileManager(connection)
        cleaner = CalculationCleaner(file_manager)

        # Specify the calculation name to clean up
        calculation_name = "harmonium"

        # Perform the cleanup
        cleaner.clean_calculation(calculation_name)

    finally:
        connection.disconnect()
