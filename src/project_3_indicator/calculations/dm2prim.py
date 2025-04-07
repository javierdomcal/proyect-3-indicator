"""
Handles DM2PRIM calculations.
"""

import os
import logging
from ..calculations.base import Calculation


class DM2PRIMCalculation(Calculation):
    def rename_output_files(self, job_name):
        """Rename output files after calculation."""
        try:
            fchk_file = f"{self.colony_dir}/Test.FChk"
            new_fchk = f"{self.colony_dir}/{job_name}.fchk"

            old_sd_dm2 = f"{self.colony_dir}/{job_name}_sd.dm2"
            new_sd_dm2 = f"{self.colony_dir}/{job_name}_hfl.dm2"

            # Check if source file exists
            if not self.commands.check_file_exists(fchk_file):
                raise FileNotFoundError(f"Test.FChk not found in {self.colony_dir}")

            if self.commands.check_file_exists(old_sd_dm2):
                # Rename DM2 file
                self.commands.execute_command(f"cp {old_sd_dm2} {new_sd_dm2}")
                logging.info(f"Renamed {old_sd_dm2} to {new_sd_dm2}")
            else:
                logging.warning(f"{old_sd_dm2} not found, skipping rename")

            # Rename file
            self.commands.execute_command(f"mv {fchk_file} {new_fchk}")
            logging.info(f"Renamed Test.FChk to {job_name}.fchk")

        except Exception as e:
            logging.error(f"Error renaming output files for {job_name}: {e}")
            raise

    def prepare_input_files(self, job_name, input_spec):
        """Prepare input files for DM2PRIM calculation."""
        try:
            # Check required input files from previous calculations
            self.rename_output_files(job_name)

            required_files = [f"{job_name}.dm2", f"{job_name}.fchk"]

            # Verify input files exist
            for file in required_files:
                if not self.commands.check_file_exists(f"{self.colony_dir}/{file}"):
                    raise FileNotFoundError(f"Required input file {file} not found")

            # Generate DM2PRIM SLURM script
            slurm_script = self.generate_dm2prim_script(job_name)

            self.file_manager.upload_file(
                slurm_script,f"{self.colony_dir}/{job_name}_dm2prim.slurm"
            )
            return 'dm2prim'

        except Exception as e:
            logging.error(f"Error preparing DM2PRIM input files for {job_name}: {e}")
            raise

    def _move_required_files_to_scratch(self, job_name):
        """Move required files to scratch directory."""
        files_to_move = [
            f"{job_name}_dm2prim.slurm",
            f"{job_name}.dm2",
            f"{job_name}.fchk",
        ]




        for file in files_to_move:
            self.move_to_scratch(file)


    def generate_dm2prim_script(self, job_name):
        """Generate SLURM script for DM2PRIM calculation."""
        script_path = os.path.join('test', f"{job_name}_dm2prim.slurm")

        content = f"""#!/bin/bash
#SBATCH --qos=regular
#SBATCH --job-name={job_name}_dm2prim
#SBATCH --cpus-per-task=1
#SBATCH --mem=64gb
#SBATCH --nodes=1
#SBATCH --output={self.scratch_dir}/{job_name}_dm2prim.out
#SBATCH --error={self.scratch_dir}/{job_name}_dm2prim.err
#SBATCH --chdir={self.scratch_dir}

cd {self.scratch_dir}
source ~/.bashrc
module load intel
{self.scratch_dir}/../SOFT/DM2PRIM/DM2PRIM.x {job_name} 10 10 no no no yes
cd {self.colony_dir}
"""
        with open(script_path, "w") as f:
            f.write(content)

        logging.info(f"Generated DM2PRIM SLURM script at {script_path}")
        return script_path
