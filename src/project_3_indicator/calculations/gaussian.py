"""
Handles Gaussian quantum chemistry calculations.
"""

import os
import logging
from ..calculations.base import Calculation
from ..utils.generator import InputFileGenerator
from ..utils.parsers import parse_gaussian_log


class GaussianCalculation(Calculation):
    def prepare_input_files(self, job_name, input_spec, nproc=1, wfx=True):
        """Prepare input files for Gaussian calculation."""
        try:
            # Generate Gaussian input file
            generator = InputFileGenerator(job_name, input_spec, type="gaussian")

            # Create local test directory and generate input file
            input_dir = "test"
            os.makedirs(input_dir, exist_ok=True)
            com_file = os.path.join(input_dir, f"{job_name}.com")
            generator.generate_input_file(nproc=nproc, wfx=wfx)

            # Define cluster paths
            colony_dir = f"{self.connection.colony_dir}/{job_name}"
            colony_com = f"{colony_dir}/{job_name}.com"

            # Upload .com file to colony
            self.file_manager.upload_file(com_file, colony_com)

            # Generate SLURM script and upload
            slurm_script = self.job_manager.submitter.generate_gaussian_script(
                job_name, f"{self.connection.scratch_dir}/{job_name}"
            )
            self.file_manager.upload_file(
                slurm_script, f"{colony_dir}/{job_name}_gaussian.slurm"
            )

            logging.info(f"Input files prepared for {job_name}")

            return 'gaussian'

        except Exception as e:
            logging.error(f"Error preparing Gaussian input files for {job_name}: {e}")
            raise

    def _move_required_files_to_scratch(self, job_name):
        """Move required files to scratch directory."""
        self.move_to_scratch(job_name, f"{job_name}.com")
        self.move_to_scratch(job_name, f"{job_name}_gaussian.slurm")

