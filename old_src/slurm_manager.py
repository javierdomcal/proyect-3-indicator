import os
import logging


class SlurmManager:
    def __init__(self, slurm_dir="slurm_scripts"):
        self.slurm_dir = slurm_dir
        os.makedirs(self.slurm_dir, exist_ok=True)

    def generate_gaussian_slurm(self, job_name, scratch_dir):
        slurm_script_path = os.path.join(self.slurm_dir, f"{job_name}.slurm")
        slurm_content = f"""#!/bin/bash
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
        with open(slurm_script_path, "w") as f:
            f.write(slurm_content)

        logging.info(f"Generated Gaussian SLURM script at {slurm_script_path}")
        return slurm_script_path

    def generate_dmn_slurm(self, job_name, scratch_dir):
        slurm_script_path = os.path.join(self.slurm_dir, f"{job_name}_dmn.slurm")
        slurm_content = f"""#!/bin/bash
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
        with open(slurm_script_path, "w") as f:
            f.write(slurm_content)

        logging.info(f"Generated DMN SLURM script at {slurm_script_path}")
        return slurm_script_path

    def generate_dm2prim_slurm(self, job_name, scratch_dir):
        slurm_script_path = os.path.join(self.slurm_dir, f"{job_name}_dm2prim.slurm")
        slurm_content = f"""#!/bin/bash
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
        with open(slurm_script_path, "w") as f:
            f.write(slurm_content)

        logging.info(f"Generated DM2PRIM SLURM script at {slurm_script_path}")
        return slurm_script_path

    def generate_inca_slurm(self, job_name, scratch_dir):
        slurm_script_path = os.path.join(self.slurm_dir, f"{job_name}_inca.slurm")
        slurm_content = f"""#!/bin/bash
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
        with open(slurm_script_path, "w") as f:
            f.write(slurm_content)

        logging.info(f"Generated INCA SLURM script at {slurm_script_path}")
        return slurm_script_path
