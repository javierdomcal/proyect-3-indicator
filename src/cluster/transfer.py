"""
Handles file transfers between local system and clusters.
"""

import os
import logging
from cluster.connection import ClusterConnection
from cluster.command import ClusterCommands


class FileTransfer:
    def __init__(self, connection):
        """Initialize with a cluster connection."""
        self.connection = connection
        self.commands = ClusterCommands(connection)  # Create an instance of ClusterCommands

    def upload_file(self, local_path, remote_path):
        """Uploads a file from local system to cluster."""
        if not self.connection.scp_client:
            raise ConnectionError("Not connected to cluster.")

        self.connection.scp_client.put(local_path, remote_path)
        print(f"Uploaded {local_path} to {remote_path} on the cluster.")

    def download_file(self, remote_path, local_path):
        """Downloads a file from cluster to local system."""
        if not self.connection.scp_client:
            raise ConnectionError("Not connected to cluster.")

        self.connection.scp_client.get(remote_path, local_path)
        print(f"Downloaded {remote_path} to {local_path} locally.")

    def move_to_scratch(self, job_name, filename):
        """Move a file from colony to scratch directory."""
        colony_path = os.path.join(self.connection.colony_dir, job_name, filename)
        scratch_path = os.path.join(self.connection.scratch_dir, job_name, filename)
        
        # Create scratch directory if it doesn't exist
        scratch_dir = os.path.dirname(scratch_path)
        if not self.commands.check_directory_exists(scratch_dir):
            self.commands.create_directory(scratch_dir)
        
        # Move file from colony to scratch
        command = f"mv {colony_path} {scratch_path}"
        self.commands.execute_command(command)
        logging.info(f"Moved {filename} from colony to scratch for {job_name}")

    def move_to_colony(self, job_name, filename):
        """Move a file from scratch to colony directory."""
        scratch_path = os.path.join(self.connection.scratch_dir, job_name, filename)
        colony_path = os.path.join(self.connection.colony_dir, job_name, filename)
        
        # Create colony directory if it doesn't exist
        colony_dir = os.path.dirname(colony_path)
        if not self.commands.check_directory_exists(colony_dir):
            self.commands.create_directory(colony_dir)
        
        # Move file from scratch to colony
        command = f"mv {scratch_path} {colony_path}"
        self.commands.execute_command(command)
        logging.info(f"Moved {filename} from scratch to colony for {job_name}")

    def transfer_between_clusters(self, source_conn, job_name, file_name=None, extension=".log"):
        """Transfers files between clusters via local temporary storage."""
        temp_path = "/tmp/transfer_between_clusters.txt"

        if file_name is None:
            file_name = job_name
        target_path = os.path.join(self.connection.colony_dir, job_name)
        source_path = os.path.join(source_conn.colony_dir, job_name)

        try:
            source_conn.scp_client.get(
                source_path + "/" + file_name + extension,
                temp_path
            )
            self.connection.scp_client.put(
                temp_path,
                target_path + "/" + file_name + extension
            )
            logging.info(
                f"Transferred {source_path} from {source_conn.hostname} "
                f"to {target_path} on {self.connection.hostname}."
            )
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    import sys
    import os
    
    # Add the parent directory to sys.path for imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from cluster.connection import ClusterConnection
    from cluster.command import ClusterCommands
    from cluster.cleanup import ClusterCleanup
    
    # Test file transfer operations
    try:
        with ClusterConnection() as connection:
            transfer = FileTransfer(connection)
            commands = ClusterCommands(connection)
            cleanup = ClusterCleanup(connection)
            test_name = "transfer_test"
            
            # Create test directory structure
            print("\nCreating directories...")
            os.makedirs("test", exist_ok=True)
            test_file = os.path.join("test", f"{test_name}.txt")
            
            # Create remote directory
            remote_dir = f"{connection.colony_dir}/{test_name}"
            commands.create_directory(remote_dir)
            
            print("\nTesting file transfers...")
            # Create and upload test file
            with open(test_file, "w") as f:
                f.write("Test content")
            
            remote_path = f"{remote_dir}/{test_name}.txt"
            transfer.upload_file(test_file, remote_path)
            print("Upload test successful")
            
            # Test download
            download_path = os.path.join("test", f"{test_name}_downloaded.txt")
            transfer.download_file(remote_path, download_path)
            print("Download test successful")
            
            # Clean up everything
            print("\nCleaning up...")
            #cleanup.clean_calculation(test_name)
            for path in [test_file, download_path]:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Removed local file: {path}")
                
    except Exception as e:
        print(f"Transfer test failed: {e}")
        # Try to cleanup even if test failed
        try:
            cleanup.clean_calculation(test_name)
            for path in [test_file, download_path]:
                if os.path.exists(path):
                    os.remove(path)
        except:
            pass