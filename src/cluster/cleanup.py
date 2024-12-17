"""
Handles cleanup operations for testing and debugging.
"""

import os
import logging
from command import ClusterCommands
from connection import ClusterConnection


class ClusterCleanup:
    def __init__(self, connection):
        """Initialize with a cluster connection."""
        self.connection = connection
        self.commands = ClusterCommands(connection)

    def delete_scratch_folder(self, calculation_name):
        """Delete a folder and its contents from scratch directory."""
        scratch_dir = os.path.join(self.connection.scratch_dir, calculation_name)
        command = f"rm -rf {scratch_dir}"
        output = self.commands.execute_command(command)
        
        # Verify deletion
        if self.commands.check_directory_exists(scratch_dir):
            print(f"Directory {scratch_dir} still exists. Check permissions or active jobs.")
        else:
            print(f"Successfully deleted {scratch_dir} from scratch.")

    def delete_colony_folder(self, calculation_name):
        """Delete a folder and its contents from colony directory."""
        colony_dir = os.path.join(self.connection.colony_dir, calculation_name)
        self.commands.execute_command(f"rm -rf {colony_dir}")
        print(f"Deleted {colony_dir} from colony.")

    def delete_local_files(self, calculation_name, directories):
        """Delete local files associated with the calculation."""
        for directory in directories:
            for ext in ['.com', '.slurm', '.log', '.tmp']:
                filepath = os.path.join(directory, f"{calculation_name}{ext}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"Deleted local file: {filepath}")

    def clean_calculation(self, calculation_name, local_dirs=None):
        """Clean all files related to a calculation."""
        if local_dirs is None:
            local_dirs = ['test', 'slurm_scripts', 'logs']
            
        self.delete_scratch_folder(calculation_name)
        self.delete_colony_folder(calculation_name)
        self.delete_local_files(calculation_name, local_dirs)


if __name__ == "__main__":
    # Test cleanup operations
    calculation_name = "test_calcccion"
    
    # Create some test files and directories first
    os.makedirs("testing", exist_ok=True)
    os.makedirs("slurm_scripts", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Create test files
    for dir_name in ["testing", "slurm_scripts", "logs"]:
        test_file = os.path.join(dir_name, f"{calculation_name}.txt")
        with open(test_file, "w") as f:
            f.write("test content")
    
    try:
        with ClusterConnection() as connection:
            cleanup = ClusterCleanup(connection)
            
            # Create test directories on cluster
            commands = ClusterCommands(connection)
            test_scratch = os.path.join(connection.scratch_dir, calculation_name)
            test_colony = os.path.join(connection.colony_dir, calculation_name)
            commands.create_directory(test_scratch)
            commands.create_directory(test_colony)
            
            print("\nCreated test directories and files")
            print(f"Scratch dir exists: {commands.check_directory_exists(test_scratch)}")
            print(f"Colony dir exists: {commands.check_directory_exists(test_colony)}")
            
            # Test cleanup
            print("\nTesting cleanup...")
            cleanup.clean_calculation(calculation_name)
            
            # Verify cleanup
            print("\nVerifying cleanup...")
            print(f"Scratch dir exists: {commands.check_directory_exists(test_scratch)}")
            print(f"Colony dir exists: {commands.check_directory_exists(test_colony)}")
            for dir_name in ["test", "slurm_scripts", "logs"]:
                test_file = os.path.join(dir_name, f"{calculation_name}.txt")
                print(f"Local file exists ({test_file}): {os.path.exists(test_file)}")
                
    except Exception as e:
        print(f"Cleanup test failed: {e}")