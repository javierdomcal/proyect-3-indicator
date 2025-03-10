"""
Manages SSH connections to computational clusters.
"""

import json
import logging
import paramiko
from scp import SCPClient
from ..config.settings import CLUSTER_CONFIG

class ClusterConnection:
    def __init__(self, config_file=str(CLUSTER_CONFIG), cluster_name="atlas"):
        self.config_file = config_file
        self.cluster_name = cluster_name
        self.ssh_client = None
        self.scp_client = None
        self._load_config()

    def _load_config(self):
        """Loads configuration for the specified cluster from the JSON file."""
        with open(self.config_file, "r") as f:
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
        """Establishes SSH connection to the cluster."""
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.load_system_host_keys()
        self.ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())

        try:
            self.ssh_client.connect(self.hostname, username=self.username)
            self.scp_client = SCPClient(self.ssh_client.get_transport())
            print(f"Connected to {self.cluster_name}.")
        except paramiko.ssh_exception.SSHException as e:
            print(f"Error: {e}")
            raise

    def disconnect(self):
        """Closes the SSH and SCP connections."""
        if self.scp_client:
            self.scp_client.close()
        if self.ssh_client:
            self.ssh_client.close()
        print("Disconnected from cluster.")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit."""
        self.disconnect()
        if exc_type:
            print(f"Exception occurred: {exc_type}, {exc_value}")
        return False

if __name__ == "__main__":

    # Test cluster connection
    try:
        with ClusterConnection() as connection:
            print(f"Connected to {connection.hostname} as {connection.username}")
            print(f"Colony directory: {connection.colony_dir}")
            print(f"Scratch directory: {connection.scratch_dir}")

            # Create a test directory to verify cleanup
            test_name = "connection_test"


    except Exception as e:
        print(f"Connection test failed: {e}")