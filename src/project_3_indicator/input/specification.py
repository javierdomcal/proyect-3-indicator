# src/input/specification.py

import logging
from ..input.molecules import Molecule
from ..input.methods import Method
from ..input.basis import BasisSet
from ..input.scanning import ScanningProperties


class InputSpecification:
    # Hardcoded dictionary for imported basis sets and their specific atoms
    imported_basis = {
        "aug-pc-4": ["He", "Ne", "Ar"],
        "dec-pc-4": ["He", "Ne", "Ar"],
        "aug-pc-3": ["Ne"],
        "dec-cc-pv6z": ["Ne"],
    }

    def __init__(
        self, molecule, basis, method, title, config="Opt", scanning_props=None
    ):
        """
        Initializes the InputSpecification instance.

        Parameters:
        - molecule (Molecule): An instance of Molecule.
        - basis (BasisSet): An instance of BasisSet.
        - method (Method): An instance of Method.
        - title (str): Title for the calculation.
        - config (str): Type of calculation, either "Opt" (optimization) or "SP" (single-point).
        - scanning_props (ScanningProperties, optional): Properties for scanning calculations
        """
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Validate input instances
        if not isinstance(molecule, Molecule):
            raise TypeError("Invalid molecule instance provided.")
        if not isinstance(basis, BasisSet):
            raise TypeError("Invalid basis set instance provided.")
        if not isinstance(method, Method):
            raise TypeError("Invalid method instance provided.")

        self.molecule = molecule
        self.basis = basis
        self.method = method
        self.title = title
        if self.molecule == "harmonium":
            self.method.method_keywords + "gfinput "

        if method.excited_state is not None:
            self.config = "SP"
        else:
            self.config = "SP" if self.molecule.count_atoms() <= 1 else config


        self.atoms_to_import = []
        self.scanning_props = scanning_props if scanning_props else ScanningProperties(self.molecule)
        self.calc_id = None

        self.logger.info(f"Creating input specification for {title}")

        # Validate and initialize parameters
        self.validate_dependencies()
        self.atoms_to_import = self.handle_imported_basis()

    def validate_dependencies(self):
        """
        Validate compatibility of basis set with molecule.
        """
        # Harmonium case (existing check)
        if self.molecule.is_harmonium and self.basis.is_even_tempered:
            if self.molecule.omega != self.basis.omega:
                raise ValueError(
                    "Inconsistent omega values for harmonium molecule and even-tempered basis set."
                )

        # Even-tempered basis validation
        if self.basis.is_even_tempered:
            # Check for helium-like atom case
            if (self.molecule.count_atoms() == 1 and
                self.molecule.count_electrons() == 2):

                # Additional check: ensure atomic number is within supported range
                from ..utils.parsers import get_atomic_number
                atomic_number = get_atomic_number(self.molecule.unique_atoms()[0])

                # Supported atomic numbers for 2-electron systems (He to N)
                if atomic_number < 2 or atomic_number > 7:
                    raise ValueError(
                        f"Even-tempered basis for 2-electron systems is only supported for atomic numbers 2-7 (He to N). "
                        f"Provided atomic number: {atomic_number}"
                    )

                return

            # Harmonium case remains the same
            if self.molecule.is_harmonium:
                return

            # If neither condition is met, raise an error
            raise ValueError(
                "Even-tempered basis is only supported for single-atom systems with 2 electrons or harmonium"
            )

    def get_registry_label(self):
        return(f"{self.molecule}_{self.method}_{self.basis}")

    def get_registry(self):
        return {
            "molecule": self.molecule,
            "basis" : self.basis,
            "method" : self.method,
            "scanning" : self.scanning_props,
            "config" : self.config
        }

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
            f"    Number of atoms: {self.molecule.count_atoms()}\n"
            f"    Charge: {self.molecule.charge}\n"
            f"    Multiplicity: {self.molecule.multiplicity}\n"
            f"  Basis Set: {self.basis.basis_name}\n"
            f"    Type: {'Imported' if self.basis.is_imported else 'Standard'}\n"
            f"    Even-tempered: {self.basis.is_even_tempered}\n"
            f"  Method: {self.method.method_name}\n"
            f"    CASSCF: {self.method.is_casscf}\n"
            f"    FullCI: {self.method.is_fullci}\n"
            f"  Configuration: {self.config}\n"
        )
        if self.atoms_to_import:
            summary += f"  Imported Atoms: {', '.join(self.atoms_to_import)}\n"
        return summary

    def update_geometry(self, new_geometry):
        """Update molecule geometry."""
        self.molecule.geometry = new_geometry


if __name__ == "__main__":
    # Test the InputSpecification class
    try:
        # Test with a standard molecule and method
        print("\nTesting standard molecule setup:")
        molecule = Molecule(name="water")
        method = Method("HF")
        basis = BasisSet("sto-3g")
        spec = InputSpecification(
            molecule=molecule,
            method=method,
            basis=basis,
            title="Water_Test",
            config="SP",
        )
        print(spec)

        # Test with harmonium
        print("\nTesting harmonium setup:")
        harmonium = Molecule(name="harmonium", omega=0.5)
        even_basis = BasisSet("8SPDF", omega=0.5)
        spec_harmonium = InputSpecification(
            molecule=harmonium, method=method, basis=even_basis, title="Harmonium_Test"
        )
        print(spec_harmonium)

        # Test with imported basis
        print("\nTesting imported basis setup:")
        helium = Molecule(name="helium")
        imported_basis = BasisSet("aug-pc-4")
        spec_imported = InputSpecification(
            molecule=helium, method=method, basis=imported_basis, title="Helium_Test"
        )
        print(spec_imported)

        # Test error cases
        print("\nTesting error cases:")
        try:
            # Test omega mismatch
            wrong_harmonium = Molecule(name="harmonium", omega=0.5)
            wrong_basis = BasisSet("8SPDF", omega=0.6)
            spec_wrong = InputSpecification(
                molecule=wrong_harmonium,
                method=method,
                basis=wrong_basis,
                title="Wrong_Test",
            )
        except ValueError as e:
            print(f"Caught expected error: {e}")

    except Exception as e:
        print(f"Test failed: {e}")
