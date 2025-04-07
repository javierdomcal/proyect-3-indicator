# src/input/specification.py

import logging
from ..input.molecules import Molecule
from ..input.methods import Method
from ..input.basis import BasisSet
from ..input.grid import Grid
from ..input.properties import Properties
from ..utils.parsers import get_atomic_number

class InputSpecification:
    # Hardcoded dictionary for imported basis sets and their specific atoms
    imported_basis = {
        "aug-pc-4": ["He", "Ne", "Ar"],
        "dec-pc-4": ["He", "Ne", "Ar"],
        "aug-pc-3": ["Ne"],
        "dec-cc-pv6z": ["Ne"],
    }

    def __init__(self, input):
        """
        Initializes the InputSpecification instance from an input dictionary.

        Parameters:
        - input: Dictionary with calculation parameters
            molecule: String with molecule name
            method: String with method name
            basis: String with basis set name
            charge: Molecular charge (default: 0)
            multiplicity: Spin multiplicity (default: 1)
            omega: Omega parameter for harmonium (default: None)
            config: Type of calculation, either "Opt" or "SP" (default: "SP")
            grid: Grid specification (default: {})
            properties: List of properties to calculate (default: [])
            excited_state: Excited state specification (default: None)
        """
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Extract required parameters with validation
        if "molecule" not in input:
            raise ValueError("Molecule specification is required")
        if "method" not in input:
            raise ValueError("Method specification is required")
        if "basis" not in input:
            raise ValueError("Basis set specification is required")

        # Log what we're creating
        self.logger.info(f"Creating input specification for {input['molecule']} with {input['method']}/{input['basis']}")

        # Create component objects with defaults for optional parameters
        self.molecule = Molecule(
            name=input["molecule"],
            charge=input.get("charge", 0),
            multiplicity=input.get("multiplicity", 1),
            omega=input.get("omega", None)
        )

        self.method = Method(
            name=input["method"],
            excited_state=input.get("excited_state", None)
        )

        self.basis = BasisSet(
            name=input["basis"]
        )

        # Set title for the calculation
        self.title = f"{self.molecule}_{self.method}_{self.basis}"

        # Determine configuration type based on molecule and method
        if self.molecule.name == "harmonium":
            self.method.method_keywords += "gfinput "

        if hasattr(self.method, 'excited_state') and self.method.excited_state is not None:
            self.config = "SP"
        elif self.molecule.count_atoms() <= 1:
            self.config = "SP"
        else:
            self.config = input.get("config", "SP")

        # Set up grid
        self.grid = Grid(input.get("grid", {}), self.molecule)


        # Set properties
        self.properties = Properties(input.get("properties", []))

        # Initialize calculation ID (will be set later by handler)
        self.calc_id = None
        self.calc_id_str = None


        # Validate and initialize additional parameters
        self.validate_dependencies()

        # Handle even-tempered basis if needed
        if hasattr(self.basis, 'is_even_tempered') and self.basis.is_even_tempered:
            if hasattr(self.basis, 'load_even_tempered_coefficients'):
                self.basis.load_even_tempered_coefficients(self.molecule)

        # Handle imported basis sets
        self.atoms_to_import = self.handle_imported_basis()

    def validate_dependencies(self):
        """
        Validate compatibility of basis set with molecule.
        """
        # Harmonium case (existing check)
        if hasattr(self.molecule, 'is_harmonium') and self.molecule.is_harmonium:
            if hasattr(self.basis, 'is_even_tempered') and self.basis.is_even_tempered:
                if self.molecule.omega != self.basis.omega:
                    raise ValueError(
                        "Inconsistent omega values for harmonium molecule and even-tempered basis set."
                    )

        # Even-tempered basis validation
        if hasattr(self.basis, 'is_even_tempered') and self.basis.is_even_tempered:
            # Check for helium-like atom case (single atom with 2 electrons)
            if (self.molecule.count_atoms() == 1 and self.molecule.count_electrons() == 2):
                if self.basis.is_even_tempered and self.basis.molecule is None:
                    self.basis.molecule = self.molecule

                # Check atomic number is within supported range
                symbol = self.molecule.unique_atoms()[0] if self.molecule.unique_atoms() else "He"
                atomic_number = get_atomic_number(symbol)

                # Only He to N (atomic numbers 2-7) are supported
                if atomic_number < 2 or atomic_number > 7:
                    raise ValueError(
                        f"Even-tempered basis for 2-electron systems is only supported for atomic numbers 2-7 (He to N). "
                        f"Provided atomic number: {atomic_number}"
                    )

                # Set the molecule reference in the basis if not already set
                if self.basis.molecule is None:
                    self.basis.molecule = self.molecule

                if self.basis.alpha is None or self.basis.beta is None:
                    self.basis.load_even_tempered_coefficients()

                return

            # Harmonium case is allowed
            if hasattr(self.molecule, 'is_harmonium') and self.molecule.is_harmonium:
                return

            # If neither condition is met, raise an error
            raise ValueError(
                "Even-tempered basis is only supported for single-atom systems with 2 electrons or harmonium"
            )

    def get_registry_label(self):
        """Returns a string label for registry lookup."""
        return f"{self.molecule}_{self.method}_{self.basis}"

    def get_registry(self):
        """Returns a dictionary with the complete specification for registry."""
        return {
            "molecule": self.molecule,
            "basis": self.basis,
            "method": self.method,
            "grid": self.grid.to_string(),
            "properties": str(self.properties),
            "config": self.config
        }

    def handle_imported_basis(self):
        """
        Checks if the basis set is in the hardcoded imported_basis dictionary and
        prepares the basis set for input generation.
        """
        atoms_to_import = []
        if self.basis.name in self.imported_basis:
            for atom in self.molecule.unique_atoms():
                if atom in self.imported_basis[self.basis.name]:
                    self.basis.is_imported = True
                    atoms_to_import.append(atom)
            self.logger.info(
                f"Imported custom basis set '{self.basis.name}' for atoms: {atoms_to_import}"
            )
        else:
            self.logger.info(f"Using default basis set '{self.basis.name}'.")
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
            f"  Basis Set: {self.basis.name}\n"
            f"    Type: {'Imported' if hasattr(self.basis, 'is_imported') and self.basis.is_imported else 'Standard'}\n"
            f"    Even-tempered: {hasattr(self.basis, 'is_even_tempered') and self.basis.is_even_tempered}\n"
            f"  Method: {self.method.name}\n"
            f"    CASSCF: {hasattr(self.method, 'is_casscf') and self.method.is_casscf}\n"
            f"    FullCI: {hasattr(self.method, 'is_fullci') and self.method.is_fullci}\n"
            f"  Configuration: {self.config}\n"
            f"  Grid: {self.grid.to_string()}\n"
            f"  Properties: {str(self.properties)}\n"
        )
        if self.atoms_to_import:
            summary += f"  Imported Atoms: {', '.join(self.atoms_to_import)}\n"
        return summary

    def get_calc_id(self, id):
        self.calc_id = id
        self.calc_id_str = f'CALC_{self.calc_id:06d}'

    def update_geometry(self, new_geometry):
        """Update molecule geometry."""
        self.molecule.geometry = new_geometry