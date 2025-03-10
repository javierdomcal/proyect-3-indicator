"""
Handles INCA calculations.
"""

import os
import logging
from ..calculations.base import Calculation
from ..utils.generator import InputFileGenerator


class INCACalculation(Calculation):
    def prepare_input_files(self, job_name, input_spec):
        """Prepare input files for INCA calculation."""
        try:
            # Define cluster paths
            colony_dir = f"{self.connection.colony_dir}/{job_name}"

            # Generate INCA input file
            generator = InputFileGenerator(job_name, input_spec, type="inca")

            # Generate and upload input file
            input_dir = "test"
            os.makedirs(input_dir, exist_ok=True)
            inp_file = os.path.join(input_dir, f"{job_name}.inp")
            generator.generate_input_file()

            # Upload to colony
            self.file_manager.upload_file(inp_file, f"{colony_dir}/{job_name}.inp")

            # Generate and upload SLURM script
            scratch_dir = f"{self.connection.scratch_dir}/{job_name}"
            slurm_script = self.job_manager.submitter.generate_inca_script(
                job_name, scratch_dir
            )
            self.file_manager.upload_file(
                slurm_script, f"{colony_dir}/{job_name}_inca.slurm"
            )

            # Check required input files from previous calculations
            required_files = [f"{job_name}.wfx"]
            if input_spec.method.method_name.upper() != "HF":
                required_files.append(f"{job_name}.dm2p")

            for file in required_files:
                if not self.commands.check_file_exists(f"{colony_dir}/{file}"):
                    raise FileNotFoundError(f"Required input file {file} not found")

            logging.info(f"Input files prepared for INCA calculation of {job_name}")

            return 'inca'

        except Exception as e:
            logging.error(f"Error preparing INCA input files for {job_name}: {e}")
            raise

    def _move_required_files_to_scratch(self, job_name):
        """Move required files to scratch directory."""
        files_to_move = [
            f"{job_name}_inca.slurm",
            f"{job_name}.inp",
            f"{job_name}.wfx"
        ]

        # Check if dm2p file exists (needed for non-HF calculations)
        colony_dir = f"{self.connection.colony_dir}/{job_name}"
        if self.commands.check_file_exists(f"{colony_dir}/{job_name}.dm2p"):
            files_to_move.append(f"{job_name}.dm2p")

        for file in files_to_move:
            self.move_to_scratch(job_name, file)

