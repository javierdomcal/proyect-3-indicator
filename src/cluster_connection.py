import paramiko
import os
import json
from scp import SCPClient
import getpass

class ClusterConnection:
    def __init__(self, config_file="utils/cluster_config.json", cluster_name='atlas'):
        """
        Initializes the ClusterConnection instance using a configuration JSON file.
        
        Parameters:
        - config_file (str): Path to the JSON file with connection details.
        """
        self.config_file = config_file
        self.cluster_name = cluster_name
        self.load_config()
        self.ssh_client = None
        self.scp_client = None

    def load_config(self):
        """
        Loads configuration for the specified cluster from the JSON file.
        """
        with open(self.config_file, 'r') as f:
            all_configs = json.load(f)
            config = all_configs.get(self.cluster_name)
            
            if not config:
                raise ValueError(f"Cluster '{self.cluster_name}' configuration not found.")
            
            self.hostname = config.get("hostname")
            self.username = config.get("username")
            self.password = config.get("password")
            self.key_path = config.get("key_path")
            self.colony_dir = config.get("colony_dir")
            self.scratch_dir = config.get("scratch_dir")
            
            if not self.hostname or not self.username:
                raise ValueError("Hostname and username must be provided for the selected cluster.")


    def connect(self):
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.load_system_host_keys()
        self.ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())
        
        try:
            # Connect using SSH agent, which holds the decrypted private key
            self.ssh_client.connect(self.hostname, username=self.username)
            
        except paramiko.ssh_exception.SSHException as e:
            print(f"Error: {e}")

        self.scp_client = SCPClient(self.ssh_client.get_transport())
        print(f"Connected to {self.cluster_name}.")


    def disconnect(self):
        """
        Closes the SSH and SCP connections.
        """
        if self.scp_client:
            self.scp_client.close()
        if self.ssh_client:
            self.ssh_client.close()
        print("Disconnected from cluster.")

    def upload_file(self, local_path, remote_path):
        """
        Uploads a file from the local system to the cluster.
        
        Parameters:
        - local_path (str): Path to the local file.
        - remote_path (str): Path on the cluster to upload the file to.
        """
        if not self.scp_client:
            raise ConnectionError("Not connected to cluster.")
        
        self.scp_client.put(local_path, remote_path)
        print(f"Uploaded {local_path} to {remote_path} on the cluster.")

    def download_file(self, remote_path, local_path):
        """
        Downloads a file from the cluster to the local system.
        
        Parameters:
        - remote_path (str): Path on the cluster to download the file from.
        - local_path (str): Path to save the file locally.
        """
        if not self.scp_client:
            raise ConnectionError("Not connected to cluster.")
        
        self.scp_client.get(remote_path, local_path)
        print(f"Downloaded {remote_path} to {local_path} locally.")

    def execute_command(self, command, wait=False):
        """
        Executes a command on the cluster over SSH.
        
        Parameters:
        - command (str): The command to execute on the cluster.
        - wait (bool): If True, waits until the command completes before returning.
        
        Returns:
        - str: The command output.
        """
        if not self.ssh_client:
            raise ConnectionError("Not connected to cluster.")
        
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        
        if wait:
            stdout.channel.recv_exit_status()  # Waits for the command to complete

        output = stdout.read().decode()
        error = stderr.read().decode()

        if error:
            print(f"Error executing command: {error}")
        else:
            print(f"Command output: {output}")
        
        return output if output else error


    def check_file_exists(self, path):
        """
        Checks if a file exists in the specified path on the cluster.
        """
        command = f"ls {path}"
        output = self.execute_command(command)
        return "No such file or directory" not in output

    def check_directory_exists(self, path):
        """
        Checks if a directory exists on the cluster.
        """
        command = f"ls -ld {path}"
        output = self.execute_command(command)
        return "No such file or directory" not in output

    def __enter__(self):
        """
        This method is called when the context is entered.
        It ensures the connection is established.
        """
        self.connect()
        return self  # Return the instance for use in the 'with' block

    def __exit__(self, exc_type, exc_value, traceback):
        """
        This method is called when the context is exited.
        It ensures the connection is closed.
        """
        self.disconnect()
        # Optionally handle exceptions here if necessary
        if exc_type:
            print(f"Exception occurred: {exc_type}, {exc_value}")
        return False  # Re-raise exceptions if they occurred

    def transfer_between_clusters(source_conn, target_conn, remote_source_path, remote_target_path):
        """
        Transfers a file from one cluster to another via local temporary storage.
        
        Parameters:
        - source_conn (ClusterConnection): Source cluster connection.
        - target_conn (ClusterConnection): Target cluster connection.
        - remote_source_path (str): Path of the file on the source cluster.
        - remote_target_path (str): Path to save the file on the target cluster.
        """
        temp_path = "/temp/temp.txt"
        source_conn.download_file(remote_source_path, temp_path)
        target_conn.upload_file(temp_path, remote_target_path)
        os.remove(temp_path)
        print(f"Transferred {remote_source_path} from {source_conn.hostname} to {remote_target_path} on {target_conn.hostname}.")



if __name__ == "__main__":
    # Load configurations for different clusters
    atlas_connection = ClusterConnection(config_file="utils/cluster_config.json", cluster_name="atlas")
    llum_connection = ClusterConnection(config_file="utils/cluster_config.json", cluster_name="llum")

    try:
        # Connect to the first cluster, execute tasks, and transfer files
        atlas_connection.connect()
        atlas_connection.upload_file("local_path/file1.txt", "remote_path/file1.txt")
        atlas_connection.execute_command("some_command")
        atlas_connection.download_file("remote_path/result1.txt", "local_path/result1.txt")
        
        # Connect to the second cluster for further tasks
        llum_connection.connect()
        llum_connection.upload_file("local_path/result1.txt", "another_remote_path/result1.txt")
        llum_connection.execute_command("another_command")
        
    finally:
        # Ensure connections are closed
        atlas_connection.disconnect()
        llum_connection.disconnect()

