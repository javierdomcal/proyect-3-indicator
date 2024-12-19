"""
Job submission and SLURM script generation functionality.
"""

import os
import logging
from cluster.command import ClusterCommands


class JobSubmitter:
    def __init__(self, connection, slurm_dir="slurm_scripts"):
        """Initialize with cluster connection."""
        self.connection = connection
        self.commands = ClusterCommands(connection)
        self.slurm_dir = slurm_dir
        os.makedirs(slurm_dir, exist_ok=True)

    def submit_job(self, job_name, step=None):
        """Submit a SLURM job using the generated script."""
        full_name = job_name if step is None else f"{job_name}_{step}"
        command = f"sbatch {self.connection.scratch_dir}/{job_name}/{full_name}.slurm"
        
        output = self.commands.execute_command(command)
        if "Submitted batch job" in output:
            job_id = output.strip().split()[-1]
            logging.info(f"Submitted job with ID {job_id} for {full_name}")
            return job_id
        else:
            raise RuntimeError(f"Failed to submit job. Output: {output}")

    def generate_gaussian_script(self, job_name, scratch_dir):
        """Generate SLURM script for Gaussian calculation."""
        script_path = os.path.join(self.slurm_dir, f"{job_name}.slurm")
        
        content = f"""#!/bin/bash
#SBATCH --qos=regular
#SBATCH --job-name={job_name}
#SBATCH --cpus-per-task=1
#SBATCH --mem=6gb
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --error={scratch_dir}/{job_name}.err
#SBATCH --chdir={scratch_dir}

cd {scratch_dir}
source ~/.bashrc
module load Gaussian/16
g16 < {scratch_dir}/{job_name}.com > {scratch_dir}/{job_name}.log
cd /dipc/javidom/proyect-3-indicator/{job_name}
pwd
"""
        with open(script_path, "w") as f:
            f.write(content)

        logging.info(f"Generated Gaussian SLURM script at {script_path}")
        return script_path

    def generate_dmn_script(self, job_name, scratch_dir):
        """Generate SLURM script for DMN calculation."""
        script_path = os.path.join(self.slurm_dir, f"{job_name}_dmn.slurm")
        
        content = f"""#!/bin/bash
#SBATCH --qos=regular
#SBATCH --job-name={job_name}_dmn
#SBATCH --cpus-per-task=1
#SBATCH --mem=5gb
#SBATCH --nodes=1
#SBATCH --output={scratch_dir}/{job_name}_dmn.out
#SBATCH --error={scratch_dir}/{job_name}_dmn.err
#SBATCH --chdir={scratch_dir}

cd {scratch_dir}
source ~/.bashrc
module load intel/2020a
{scratch_dir}/../SOFT/DMN/DMN {scratch_dir}/{job_name}.log
cd /dipc/javidom/proyect-3-indicator/{job_name}
"""
        with open(script_path, "w") as f:
            f.write(content)
            
        logging.info(f"Generated DMN SLURM script at {script_path}")
        return script_path

    def generate_dm2prim_script(self, job_name, scratch_dir):
        """Generate SLURM script for DM2PRIM calculation."""
        script_path = os.path.join(self.slurm_dir, f"{job_name}_dm2prim.slurm")
        
        content = f"""#!/bin/bash
#SBATCH --qos=regular
#SBATCH --job-name={job_name}_dm2prim
#SBATCH --cpus-per-task=1
#SBATCH --mem=200gb
#SBATCH --nodes=1
#SBATCH --output={scratch_dir}/{job_name}_dm2prim.out
#SBATCH --error={scratch_dir}/{job_name}_dm2prim.err
#SBATCH --chdir={scratch_dir}

cd {scratch_dir}
source ~/.bashrc
module load intel
{scratch_dir}/../SOFT/DM2PRIM/DM2PRIM.x {job_name} 10 10 no no no yes
cd /dipc/javidom/proyect-3-indicator/{job_name}
"""
        with open(script_path, "w") as f:
            f.write(content)
            
        logging.info(f"Generated DM2PRIM SLURM script at {script_path}")
        return script_path

    def generate_inca_script(self, job_name, scratch_dir):
        """Generate SLURM script for INCA calculation."""
        script_path = os.path.join(self.slurm_dir, f"{job_name}_inca.slurm")
        
        content = f"""#!/bin/bash
#SBATCH --qos=regular
#SBATCH --job-name={job_name}_inca
#SBATCH --cpus-per-task=1
#SBATCH --mem=5gb
#SBATCH --nodes=1
#SBATCH --output={scratch_dir}/{job_name}_inca.out
#SBATCH --error={scratch_dir}/{job_name}_inca.err
#SBATCH --chdir={scratch_dir}

cd {scratch_dir}
source ~/.bashrc
module load intel
{scratch_dir}/../SOFT/INCA6_llum/roda.x {job_name}.inp
cd /dipc/javidom/proyect-3-indicator/{job_name}
"""
        with open(script_path, "w") as f:
            f.write(content)
            
        logging.info(f"Generated INCA SLURM script at {script_path}")
        return script_path


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
                'gaussian': submitter.generate_gaussian_script(test_name, scratch_dir),
                'dmn': submitter.generate_dmn_script(test_name, scratch_dir),
                'dm2prim': submitter.generate_dm2prim_script(test_name, scratch_dir),
                'inca': submitter.generate_inca_script(test_name, scratch_dir)
            }
            
            print("\nGenerated scripts:")
            for script_type, script_path in scripts.items():
                print(f"{script_type}: {script_path}")
                with open(script_path, 'r') as f:
                    print(f"\nContent of {script_type} script:")
                    print(f.read())
                    
            # Create test directory on cluster
            print("\nCreating test directory on cluster...")
            commands.create_directory(scratch_dir)
            
            # Test submitting a simple job
            test_script = scripts['gaussian']
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