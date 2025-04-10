"""
Handles INCA calculations.
"""

import os
import logging
from ..calculations.base import Calculation


class INCACalculation(Calculation):
    def prepare_input_files(self, job_name, input_spec):
        """Prepare input files for INCA calculation."""
        try:
            # Define cluster paths

            # Generate INCA input file

            # Generate and upload input file
            input_dir = "test"
            os.makedirs(input_dir, exist_ok=True)
            inp_file = os.path.join(input_dir, f"{job_name}.inp")
            self._generate_inca_input(job_name, input_spec)

            # Upload to colony
            self.file_manager.upload_file(inp_file, f"{self.colony_dir}/{job_name}.inp")

            # Generate and upload SLURM script
            scratch_dir = f"{self.scratch_dir}/{job_name}"
            slurm_script = self.generate_inca_script(job_name)
            self.file_manager.upload_file(
                slurm_script, f"{self.colony_dir}/{job_name}_inca.slurm"
            )

            # Check required input files from previous calculations
            required_files = [f"{job_name}.wfx"]
            if input_spec.method.name.upper() != "HF":
                required_files.append(f"{job_name}.dm2p")

            for file in required_files:
                if not self.commands.check_file_exists(f"{self.colony_dir}/{file}"):
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

        if self.folder_name == job_name:
            files_to_move.append(f"{job_name}_hf.dm2")
            files_to_move.append(f"{job_name}_hfl.dm2")
        # Check if dm2p file exists (needed for non-HF calculations)
        colony_dir = f"{self.connection.colony_dir}/{job_name}"
        if self.commands.check_file_exists(f"{colony_dir}/{job_name}.dm2p"):
            files_to_move.append(f"{job_name}.dm2p")

        for file in files_to_move:
            self.move_to_scratch(file)

    def _generate_inca_input(self, job_name, inp):
        """Generate INCA input file (.inp)."""
        filename = "./test/" + job_name + ".inp"
        dm2p_hf = job_name + "_hf.dm2p" if 'pair_density_nucleus' in inp.properties.get_active_properties() else "no"
        dm2p_hfl = job_name + "_hfl.dm2p" if 'pair_density_nucleus' in inp.properties.get_active_properties() else "no"
        with open(filename, "w") as f:
            f.write("test_input\n")
            f.write("$wfxfile\n")
            f.write(f"{job_name}.wfx\n")
            f.write("$logfile\n")
            f.write("no\n")
            f.write(f"{inp.grid.to_string()}")
            f.write("$Grid_2\n")
            f.write(".false.\n")
            f.write(f"{inp.properties.generate_properties_string()}")
            f.write("$DM2files\n")
            f.write(f"{job_name}.dm2p {dm2p_hf} {dm2p_hfl}\n")






        print(f"INCA input file '{filename}' generated successfully.")

    def generate_inca_script(self, job_name):
        """Generate SLURM script for INCA calculation."""
        script_path = os.path.join('test', f"{job_name}_inca.slurm")

        content = f"""#!/bin/bash
#SBATCH --qos=regular
#SBATCH --job-name={job_name}_inca
#SBATCH --cpus-per-task=1
#SBATCH --mem=5gb
#SBATCH --nodes=1
#SBATCH --output={self.scratch_dir}/{job_name}_inca.out
#SBATCH --error={self.scratch_dir}/{job_name}_inca.err
#SBATCH --chdir={self.scratch_dir}

cd {self.scratch_dir}
source ~/.bashrc
module load intel
{self.scratch_dir}/../SOFT/INCA_mod/roda.x {job_name}.inp
cd {self.colony_dir}
"""
        with open(script_path, "w") as f:
            f.write(content)

        logging.info(f"Generated INCA SLURM script at {script_path}")
        return script_path
