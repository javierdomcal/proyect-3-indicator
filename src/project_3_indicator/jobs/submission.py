"""
Job submission and SLURM script generation functionality.
"""

import os
import logging
from ..cluster.command import ClusterCommands


class JobSubmitter:
    def __init__(self, connection, slurm_dir="slurm_scripts"):
        """Initialize with cluster connection."""
        self.connection = connection
        self.commands = ClusterCommands(connection)
        self.slurm_dir = slurm_dir
        os.makedirs(slurm_dir, exist_ok=True)











if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from utils.log_config import setup_logging
    from cluster.connection import ClusterConnection
    from cluster.command import ClusterCommands
    from cluster.cleanup import ClusterCleanup

    # Setup logging
    setup_logging(verbose_level=2)

    try:
        with ClusterConnection() as connection:
            submitter = JobSubmitter(connection)
            commands = ClusterCommands(connection)
            cleanup = ClusterCleanup(connection)
            test_name = "submit_test"

            print("\nTesting script generation...")
            # Test generating all types of scripts
            scratch_dir = os.path.join(connection.scratch_dir, test_name)
            scripts = {
                "gaussian": submitter.generate_gaussian_script(test_name, scratch_dir),
                "dmn": submitter.generate_dmn_script(test_name, scratch_dir),
                "dm2prim": submitter.generate_dm2prim_script(test_name, scratch_dir),
                "inca": submitter.generate_inca_script(test_name, scratch_dir),
            }

            print("\nGenerated scripts:")
            for script_type, script_path in scripts.items():
                print(f"{script_type}: {script_path}")
                with open(script_path, "r") as f:
                    print(f"\nContent of {script_type} script:")
                    print(f.read())

            # Create test directory on cluster
            print("\nCreating test directory on cluster...")
            commands.create_directory(scratch_dir)

            # Test submitting a simple job
            test_script = scripts["gaussian"]
            if os.path.exists(test_script):
                print("\nTesting job submission...")
                test_submit_cmd = f"sbatch --wrap='sleep 5' --job-name={test_name}"
                output = commands.execute_command(test_submit_cmd)
                if "Submitted batch job" in output:
                    print("Job submission test successful")

            # Clean up
            print("\nCleaning up...")
            cleanup.clean_calculation(test_name)
            for script in scripts.values():
                if os.path.exists(script):
                    os.remove(script)
                    print(f"Removed {script}")

    except Exception as e:
        print(f"Test failed: {e}")
        # Try to cleanup even if test failed
        try:
            cleanup.clean_calculation(test_name)
            for script in scripts.values():
                if os.path.exists(script):
                    os.remove(script)
        except:
            pass
