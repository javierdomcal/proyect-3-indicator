import os
from ..input.specification import InputSpecification


class InputFileGenerator:
    def __init__(self, job_name, input_spec, type='gaussian'):
        """
        Initialize with InputSpecification instance and input type.

        Args:
            input_spec: Complete InputSpecification instance
            type: Type of input to generate ("gaussian" or "inca")
        """
        self.inp = input_spec
        self.title = job_name
        self.type = type.lower()

    def generate_input_file(self, nproc=1, wfx=True):
        """
        Generate input file based on the selected type.

        Args:
            nproc: Number of processors to use (for Gaussian)
            wfx: Whether to generate wfx file (for Gaussian)
        """
        if self.type == "gaussian":
            self._generate_gaussian_input(nproc, wfx)
        elif self.type == "inca":
            self._generate_inca_input()
        else:
            raise ValueError(f"Unsupported input type: {self.type}")

    def _generate_gaussian_input(self, nproc, wfx=True):
        """Generate Gaussian input file (.com)."""
        filename = "./test/" + self.title + ".com"
        basis_type = (
            "gen "
            if self.inp.basis.is_even_tempered or self.inp.basis.is_imported
            else f"{self.inp.basis.basis_name} "
        )

        with open(filename, "w") as f:
            # Write Gaussian header
            f.write(f"%chk={self.title}.chk\n")
            f.write(f"%mem=4GB\n")
            f.write(f"%NProcShared={nproc}\n")
            f.write(f"#P {self.inp.config} {self.inp.method.method_name}/{basis_type}")

            wfx_text = "out=wfx" if wfx else ""
            # Gaussian options
            f.write(
                "gfinput fchk=all "
                + self.inp.method.method_keywords
                + wfx_text
                + "\n\n"
            )

            # Title line
            molecule_desc = self.inp.molecule.get_molecule_description()
            f.write(
                f"{self.title} {molecule_desc} {self.inp.method.method_name} {self.inp.basis.basis_name}\n\n"
            )

            # Charge and multiplicity
            f.write(f"{self.inp.molecule.charge} {self.inp.molecule.multiplicity}\n")

            # Molecule geometry or harmonium placeholder
            if self.inp.molecule.is_harmonium:
                f.write("H-Bq 0.000000 0.000000 0.000000\n\n")
            else:
                f.write(self.inp.molecule.geometry + "\n")

            # Basis set details if custom basis is needed
            if self.inp.basis.is_imported:
                for atom in self.inp.atoms_to_import:
                    self._write_basis_coefficients(f, atom)
                f.write(" ****\n\n")

            if self.inp.basis.is_even_tempered:
                f.write("   1 0\n")
                for i in range(self.inp.basis.n):
                    for orbital in self.inp.basis.angular_momentum:
                        f.write(f"{orbital}   1 1.0 0.0\n")
                        coefficient = self.inp.basis.alpha * (self.inp.basis.beta**i)
                        f.write(f"                 {coefficient} 1.0\n")
                f.write(" ****\n\n")



            # Special harmonium configuration
            if self.inp.molecule.is_harmonium:
                f.write(
                    "    0.0000000000D+00    0.0000000000D+00    0.0000000000D+00\n"
                )
                f.write(
                    f"   {-self.inp.molecule.omega**2 / 2:.10f}   {-self.inp.molecule.omega**2 / 2:.10f}   {-self.inp.molecule.omega**2 / 2:.10f}\n"
                )
                for _ in range(9):
                    f.write(
                        "    0.0000000000D+00    0.0000000000D+00    0.0000000000D+00\n"
                    )

            if wfx:
                f.write(f"\n{self.title}.wfx\n\n")



        print(f"Gaussian input file '{filename}' generated successfully.")

    def _write_basis_coefficients(self, file_handle, atom):
        """Write basis coefficients for an atom from .gbs file."""
        basis_file_path = f"./utils/basis_sets/{self.inp.basis.basis_name}.gbs"

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

    def _generate_inca_input(self):
        """Generate INCA input file (.inp)."""
        filename = "./test/" + self.title + ".inp"
        with open(filename, "w") as f:
            f.write("test_input\n")
            f.write("$wfxfile\n")
            f.write(f"{self.title}.wfx\n")
            f.write("$logfile\n")
            f.write("no\n")
            f.write("$cubefile\n")
            f.write(".false.\n")
            f.write("$Coulomb Hole !select an option\n")
            f.write("ontop          !C1, all, c1approx,intra\n")
            f.write("$On top\n")
            if self.inp.method.method_name.upper() != "HF":
                f.write(f"{self.title}.dm2p\n")
            else:
                f.write("no\n")

            if self.inp.scanning_props:
                f.write("$scanning_props\n")
                atom_indices = self.inp.scanning_props.atom_indices.split(',')
                directions = self.inp.scanning_props.directions.split(',')

                # Write number of atoms and indices
                f.write(f"{len(atom_indices)}\n")
                f.write(f"{self.inp.scanning_props.atom_indices}\n")

                # Write number of directions and directions
                f.write(f"{len(directions)}\n")
                f.write(f"{self.inp.scanning_props.directions}\n")

                # Write distances
                f.write(f"{self.inp.scanning_props.end_distance}\n")
                f.write(f"{self.inp.scanning_props.step_size}\n")

            f.write("$ID\n")
            f.write(".true.\n")

        print(f"INCA input file '{filename}' generated successfully.")


if __name__ == "__main__":
    # Test the input generator
    from ..input.molecules import Molecule
    from ..input.methods import Method
    from ..input.basis import BasisSet

    try:
        # Test with basic molecule
        molecule = Molecule(name="water")
        method = Method("HF")
        basis = BasisSet("sto-3g")

        # Create input specification
        spec = InputSpecification(
            molecule=molecule,
            method=method,
            basis=basis,
            title="test_calc",
            config="SP"
        )

        # Test Gaussian input generation
        print("\nTesting Gaussian input generation:")
        gaussian_gen = InputFileGenerator(spec, type="gaussian")
        gaussian_gen.generate_input_file()

        # Test INCA input generation
        print("\nTesting INCA input generation:")
        inca_gen = InputFileGenerator(spec, type="inca")
        inca_gen.generate_input_file()

    except Exception as e:
        print(f"Test failed: {e}")

    # Clean up test files
    test_files = ["test_gaussian.com", "test_inca.inp"]
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"Cleaned up {file}")