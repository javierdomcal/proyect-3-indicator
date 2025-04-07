"""
Handles DMN calculations.
"""

import os
import logging
import time
from ..calculations.base import Calculation


class DMNCalculation(Calculation):
    def modify_log_file(self, job_name):
        """Modify the Gaussian log file for subsequent calculations."""
        try:
            time.sleep(2)  # Adjust time as needed
            log_file = f"{self.colony_dir}/{job_name}.log"

            # Verify log file exists
            if not self.commands.check_file_exists(log_file):
                raise FileNotFoundError(f"Log file not found: {log_file}")

                        # Create modified content directly on cluster
            cmd = f"cp {log_file} {self.colony_dir}/{job_name}_copy.log"
            self.commands.execute_command(cmd)
            print('here')



            # Prepare additional content
            additional_text = """
 Thresholds for DMn (READ, WRITE)
 1d-10 1d-10
 DMs to compute
 2 1 2
 DM2HF
 DM2SD
"""
            # Create modified content directly on cluster
            cmd = f"echo '{additional_text}' >> {self.colony_dir}/{job_name}.log"
            self.commands.execute_command(cmd)


        except Exception as e:
            logging.error(f"Error modifying log file for {job_name}: {e}")
            raise

    def prepare_input_files(self, job_name, input_spec):
        """Prepare input files for DMN calculation."""
        try:
            # DMN needs the Gaussian log file
            self.modify_log_file(job_name)
            log_file = f"{job_name}.log"

            colony_log_path= f"{self.colony_dir}/{job_name}.log"


            if not self.commands.check_file_exists(colony_log_path):
                raise FileNotFoundError(f"{log_file} not found in colony directory")

            # Generate DMN SLURM script
            slurm_script = self.generate_dmn_script(job_name)

            # Upload to colony
            self.file_manager.upload_file(
                slurm_script, f"{self.colony_dir}/{job_name}_dmn.slurm"
                )
            return 'dmn'

        except Exception as e:
            logging.error(f"Error preparing DMN input files for {job_name}: {e}")
            raise

    def _move_required_files_to_scratch(self, job_name):
        """Move required files to scratch directory."""
        self.move_to_scratch( f"{job_name}_dmn.slurm")
        self.move_to_scratch( f"{job_name}.log")

    def generate_dmn_script(self, job_name):
        """Generate SLURM script for DMN calculation."""
        script_path = os.path.join('test', f"{job_name}_dmn.slurm")

        content = f"""#!/bin/bash
#SBATCH --qos=regular
#SBATCH --job-name={job_name}_dmn
#SBATCH --cpus-per-task=1
#SBATCH --mem=5gb
#SBATCH --nodes=1
#SBATCH --output={self.scratch_dir}/{job_name}_dmn.out
#SBATCH --error={self.scratch_dir}/{job_name}_dmn.err
#SBATCH --chdir={self.scratch_dir}

cd {self.scratch_dir}
source ~/.bashrc
module load intel/2020a
{self.scratch_dir}/../SOFT/DMN/DMN {self.scratch_dir}/{job_name}.log
cd {self.colony_dir}
"""
        with open(script_path, "w") as f:
            f.write(content)

        logging.info(f"Generated DMN SLURM script at {script_path}")
        return script_path
