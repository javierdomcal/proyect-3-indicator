import logging
from molecule import Molecule
from method import Method
from basis import BasisSet


class InputSpecification:
    # Hardcoded dictionary for imported basis sets and their specific atoms
    imported_basis = {
        "aug-pc-4": ["He", "Ne", "Ar"],
        "dec-pc-4": ["He", "Ne", "Ar"],
        "aug-pc-3": ["Ne"],
        "dec-cc-pv6z": ["Ne"],
    }

    def __init__(
        self, molecule, basis, method, title, config="Opt", input_type="gaussian"
    ):
        """
        Initializes the InputSpecification instance.

        Parameters:
        - molecule (Molecule): An instance of Molecule.
        - basis (BasisSet): An instance of BasisSet.
        - method (Method): An instance of Method.
        - title (str): Title for the calculation.
        - config (str): Type of calculation, either "Opt" (optimization) or "SP" (single-point).
        - input_type (str): Type of input file to generate ("gaussian" or "inca").
        """
        self.molecule = molecule
        self.basis = basis
        self.method = method
        self.title = title
        self.config = "SP" if self.molecule.count_atoms() <= 1 else config
        self.input_type = input_type.lower()
        self.atoms_to_import = []

        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Validate and initialize parameters
        self.validate_dependencies()
        self.atoms_to_import = self.handle_imported_basis()

    def validate_dependencies(self):
        """
        Validates compatibility across molecule, basis, and method, especially with shared parameters like omega.
        Raises errors for inconsistencies.
        """
        # Check omega consistency if harmonium molecule and even-tempered basis are used
        if self.molecule.is_harmonium and self.basis.is_even_tempered:
            if self.molecule.omega != self.basis.omega:
                raise ValueError(
                    "Inconsistent omega values for harmonium molecule and even-tempered basis set."
                )

        # Additional compatibility checks can be added here if needed
        self.logger.info("Dependencies validated successfully.")

    def handle_imported_basis(self):
        """
        Checks if the basis set is in the hardcoded imported_basis dictionary and prepares the basis set for input generation.
        """
        atoms_to_import = []
        if self.basis.basis_name in self.imported_basis:
            for atom in self.molecule.unique_atoms():
                if atom in self.imported_basis[self.basis.basis_name]:
                    self.basis.is_imported = True
                    atoms_to_import.append(atom)
                    self.logger.info(
                        f"Imported custom basis set '{self.basis.basis_name}' for atoms: {atoms_to_import}"
                    )
        else:
            self.logger.info(f"Using default basis set '{self.basis.basis_name}'.")
        return atoms_to_import

    def __str__(self):
        """
        Returns a summary string of the input specification details.
        """
        summary = (
            f"InputSpecification for {self.title}:\n"
            f"  Molecule: {self.molecule.get_molecule_description()}\n"
            f"  Basis Set: {self.basis.basis_name} ({'imported' if self.basis.basis_name in self.imported_basis else 'default'})\n"
            f"  Method: {self.method.method_name}\n"
            f"  Config: {self.config}\n"
            f"  Input Type: {self.input_type}"
        )
        return summary


# Example usage (assuming molecule, basis, method classes and instances are defined):
if __name__ == "__main__":
    # Define the molecule, method, and basis as per requirements
    water_molecule = Molecule(name="water", charge=0, multiplicity=1)
    hf_method = Method("HF")
    custom_basis = BasisSet("aug-pc-4")

    # Create the InputSpecification instance
    input_spec = InputSpecification(
        molecule=water_molecule,
        basis=custom_basis,
        method=hf_method,
        title="Water Calculation",
        config="SP",
        input_type="gaussian",
    )

    # Generate input files with specified configuration
    print(input_spec)
