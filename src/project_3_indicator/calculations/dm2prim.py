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
            colony_dir = f"{self.connection.colony_dir}/{job_name}"
            fchk_file = f"{colony_dir}/Test.FChk"
            new_fchk = f"{colony_dir}/{job_name}.fchk"

            # Check if source file exists
            if not self.commands.check_file_exists(fchk_file):
                raise FileNotFoundError(f"Test.FChk not found in {colony_dir}")

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

            colony_dir = os.path.join(self.connection.colony_dir, job_name)
            required_files = [f"{job_name}.dm2", f"{job_name}.fchk"]

            # Verify input files exist
            for file in required_files:
                if not self.commands.check_file_exists(os.path.join(colony_dir, file)):
                    raise FileNotFoundError(f"Required input file {file} not found")

            # Generate DM2PRIM SLURM script
            slurm_script = self.job_manager.submitter.generate_dm2prim_script(
                job_name, os.path.join(self.connection.scratch_dir, job_name)
            )

            # Upload SLURM script to colony
            self.file_manager.upload_file(
                slurm_script, os.path.join(colony_dir, f"{job_name}_dm2prim.slurm")
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
            self.move_to_scratch(job_name, file)

