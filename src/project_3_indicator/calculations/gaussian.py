"""
Handles Gaussian quantum chemistry calculations.
"""

import os
import logging
from ..calculations.base import Calculation
from ..utils.parsers import parse_gaussian_log


class GaussianCalculation(Calculation):
    def prepare_input_files(self, job_name, input_spec, nproc=1, wfx=True):
        """Prepare input files for Gaussian calculation."""
        try:
            # Generate Gaussian input file

            # Create local test directory and generate input file
            input_dir = "test"
            os.makedirs(input_dir, exist_ok=True)
            com_file = os.path.join(input_dir, f"{job_name}.com")
            self._generate_gaussian_input(input_spec, nproc=nproc,  wfx=wfx)

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

    def _generate_gaussian_input(self, inp, nproc,  wfx=True):
        """Generate Gaussian input file (.com)."""
        filename = "./test/" + str(inp.calc_id) + ".com"
        basis_type = (
            "gen "
            if inp.basis.is_even_tempered or inp.basis.is_imported
            else f"{inp.basis.name} "
        )

        with open(filename, "w") as f:
            # Write Gaussian header
            f.write(f"%chk={str(inp.calc_id)}.chk\n")
            f.write(f"%mem=4GB\n")
            f.write(f"%NProcShared={nproc}\n")
            f.write(f"#P {inp.config} {inp.method.name}/{basis_type}")

            wfx_text = "out=wfx" if wfx else ""
            # Gaussian options
            f.write(
                "gfinput fchk=all "
                + inp.method.method_keywords
                + wfx_text
                + "\n\n"
            )

            # Title line
            molecule_desc = inp.molecule.get_molecule_description()
            f.write(
                f"{inp.calc_id} {molecule_desc} {inp.method.name} {inp.basis.name}\n\n"
            )

            # Charge and multiplicity
            f.write(f"{inp.molecule.charge} {inp.molecule.multiplicity}\n")

            # Molecule geometry or harmonium placeholder
            if inp.molecule.is_harmonium:
                f.write("H-Bq 0.000000 0.000000 0.000000\n\n")
            else:
                f.write(inp.molecule.geometry + "\n")

            # Basis set details if custom basis is needed
            if inp.basis.is_imported:
                for atom in inp.atoms_to_import:
                    self._write_basis_coefficients(inp, f, atom)
                f.write(" ****\n\n")

            if inp.basis.is_even_tempered:
                f.write("   1 0\n")
                for i in range(inp.basis.n):
                    for orbital in inp.basis.angular_momentum:
                        f.write(f"{orbital}   1 1.0 0.0\n")
                        coefficient = inp.basis.alpha * (inp.basis.beta**i)
                        f.write(f"                 {coefficient} 1.0\n")
                f.write(" ****\n\n")



            # Special harmonium configuration
            if inp.molecule.is_harmonium:
                f.write(
                    "    0.0000000000D+00    0.0000000000D+00    0.0000000000D+00\n"
                )
                f.write(
                    f"   {-inp.molecule.omega**2 / 2:.10f}   {-inp.molecule.omega**2 / 2:.10f}   {-inp.molecule.omega**2 / 2:.10f}\n"
                )
                for _ in range(9):
                    f.write(
                        "    0.0000000000D+00    0.0000000000D+00    0.0000000000D+00\n"
                    )

            if wfx:
                f.write(f"{str(inp.calc_id)}.wfx\n\n")



        print(f"Gaussian input file '{filename}' generated successfully.")

    def _write_basis_coefficients(self, inp, file_handle, atom):
        """Write basis coefficients for an atom from .gbs file."""
        basis_file_path = f"./utils/basis_sets/{inp.basis.name}.gbs"

        if not os.path.exists(basis_file_path):
            raise FileNotFoundError(f"Basis file {basis_file_path} not found.")

        with open(basis_file_path, "r") as basis_file:
            lines = basis_file.readlines()
            writing = False

            for line in lines:
                if line.strip().lower().startswith(atom.lower()):
                    writing = True
                elif writing and line.strip() == "****":
                    break

                if writing:
                    file_handle.write(line)

        print(
            f"Basis coefficients for {atom} from {basis_file_path} written successfully."
        )
