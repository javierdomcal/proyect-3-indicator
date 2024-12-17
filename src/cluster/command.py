"""
Handles command execution and file operations on clusters.
"""

import os
import logging
from connection import ClusterConnection


class ClusterCommands:
    def __init__(self, connection):
        """Initialize with a cluster connection."""
        self.connection = connection

    def execute_command(self, command, wait=False):
        """
        Executes a command on the cluster.
        
        Args:
            command (str): Command to execute
            wait (bool): Whether to wait for command completion
        """
        if not self.connection.ssh_client:
            raise ConnectionError("Not connected to cluster.")

        stdin, stdout, stderr = self.connection.ssh_client.exec_command(command)

        if wait:
            stdout.channel.recv_exit_status()

        output = stdout.read().decode()
        error = stderr.read().decode()

        if error:
            logging.error(f"Error executing command: {error}")
        else:
            logging.info(f"Command output: {output}")

        return output if output else error

    def check_file_exists(self, path):
        """Checks if a file exists on the cluster."""
        command = f"ls {path}"
        output = self.execute_command(command)
        return "No such file or directory" not in output

    def check_directory_exists(self, path):
        """Checks if a directory exists on the cluster."""
        command = f"ls -ld {path}"
        output = self.execute_command(command)
        return "No such file or directory" not in output

    def create_directory(self, path):
        """Creates a directory on the cluster."""
        command = f"mkdir -p {path}"
        self.execute_command(command)
        logging.info(f"Created directory: {path}")

    def change_directory(self, path):
        """Changes working directory on the cluster."""
        command = f"cd {path}"
        self.execute_command(command)
        logging.info(f"Changed directory to: {path}")

    def read_file_content(self, file_path):
        """Reads content of a file from the cluster."""
        command = f"cat {file_path}"
        return self.execute_command(command)



if __name__ == "__main__":
    from cleanup import ClusterCleanup
    
    # Test cluster commands
    try:
        with ClusterConnection() as connection:
            commands = ClusterCommands(connection)
            cleanup = ClusterCleanup(connection)
            test_name = "command_test"
            
            print("\nTesting directory operations...")
            # Test colony directory
            colony_dir = f"{connection.colony_dir}/{test_name}"
            commands.create_directory(colony_dir)
            print(f"Colony directory exists: {commands.check_directory_exists(colony_dir)}")
            
            # Test scratch directory
            scratch_dir = f"{connection.scratch_dir}/{test_name}"
            commands.create_directory(scratch_dir)
            print(f"Scratch directory exists: {commands.check_directory_exists(scratch_dir)}")
            
            # Test file operations
            print("\nTesting file operations...")
            test_file = f"{colony_dir}/test.txt"
            commands.execute_command(f"echo 'test content' > {test_file}")
            print(f"File exists: {commands.check_file_exists(test_file)}")
            
            # Test file content reading
            content = commands.read_file_content(test_file)
            print(f"File content: {content}")
            
            # Clean up using cleanup class
            print("\nCleaning up...")
            #cleanup.clean_calculation(test_name)
            
            # Verify cleanup
            print("\nVerifying cleanup...")
            print(f"Colony directory exists: {commands.check_directory_exists(colony_dir)}")
            print(f"Scratch directory exists: {commands.check_directory_exists(scratch_dir)}")
            
    except Exception as e:
        print(f"Command test failed: {e}")