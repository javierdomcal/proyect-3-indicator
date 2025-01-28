import os
from input_specification import InputSpecification


class InputFileGenerator:
    def __init__(self, config, molecule, method, basis, title, input_type="gaussian"):
        """
        Initializes the InputFileGenerator instance.

        Parameters:
        - config (str): Type of calculation, either "Opt" (optimization) or "SP" (single-point).
        - molecule: Molecule information passed as parameters for InputSpecification.
        - method: Method information passed as parameters for InputSpecification.
        - basis: BasisSet information passed as parameters for InputSpecification.
        - title (str): Title for the calculation.
        - input_type (str): Type of input file to generate, either "gaussian" or "inca".
        """
        # Initialize InputSpecification with provided molecule, method, and basis information
        self.inp = InputSpecification(
            molecule=molecule,
            basis=basis,
            method=method,
            title=title,
            config=config,
            input_type=input_type,
        )
        self.title = title
        self.input_type = input_type.lower()  # Either "gaussian" or "inca"

    def generate_input_file(self, nproc=1, wfx=True):
        """
        Generates the input file based on the selected input type (Gaussian or INCA).

        Parameters:
        - nproc (int): Number of processors to use (applicable for Gaussian files).
        """
        if self.input_type == "gaussian":
            self._generate_gaussian_input(nproc, wfx)
        elif self.input_type == "inca":
            self._generate_inca_input()
        else:
            raise ValueError(f"Unsupported input type: {self.input_type}")

    def _generate_gaussian_input(self, nproc, wfx=True):
        """
        Private method to generate Gaussian input file (.com).
        Allows switching between different input combinations (original or modified).
        """

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
                        coefficient = self.inp.basis.alfa * (self.inp.basis.beta**i)
                        f.write(f"                 {coefficient} 1.0\n")
                f.write(" ****\n\n")

            # 7. Special harmonium configuration (optional)
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
                f.write(f"{self.title}.wfx\n\n")

        print(f"Gaussian input file '{filename}' generated successfully.")

    def _write_basis_coefficients(self, file_handle, atom):
        """
        Reads basis coefficients for a specific atom from a .gbs file and writes them to the Gaussian input file.

        Parameters:
        - file_handle: The file handle of the Gaussian input file to write into.
        - atom (str): The atom symbol for which to load and write basis coefficients.
        """
        basis_file_path = f"./utils/basis_sets/{self.inp.basis.basis_name}.gbs"

        if not os.path.exists(basis_file_path):
            raise FileNotFoundError(f"Basis file {basis_file_path} not found.")

        with open(basis_file_path, "r") as basis_file:
            lines = basis_file.readlines()
            writing = False

            for line in lines:
                if line.strip().lower().startswith(atom.lower()):
                    writing = True  # Start writing after finding the atom block
                elif writing and line.strip() == "****":
                    break  # Stop writing at the end of the atom block

                if writing:
                    file_handle.write(line)

        print(
            f"Basis coefficients for {atom} from {basis_file_path} written successfully."
        )

    def _generate_inca_input(self):
        """
        Private method to generate INCA input file (.inp).
        """
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
            f.write(f"{self.title}.dm2p\n")

        print(f"INCA input file '{filename}' generated successfully.")
