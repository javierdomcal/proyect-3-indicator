from ..config.settings import MOLECULES_DIR
import os
import re
from collections import Counter


class Molecule:
    def __init__(self, name="harmonium",  charge=0, multiplicity=1, omega=None,):
        """
        Initialize a Molecule instance.

        Args:
            name (str): Name of the molecule (default: "harmonium")
            omega (float, optional): Omega parameter for harmonium
            charge (int): Molecular charge (default: 0)
            multiplicity (int): Spin multiplicity (default: 1)
        """
        self.name = name.lower()
        self.omega = omega
        self.charge = charge
        self.multiplicity = multiplicity
        self.is_harmonium = omega is not None
        self.geometry = None
        self.formula = None

        if not self.is_harmonium:
            self.load_geometry()

        if self.is_harmonium:
            self.name = "harmonium"
            self.charge = -2
            self.multiplicity = 1


    def classify_molecule(self):
        """Classify the molecule type based on its geometry.

        Classifications:
        - atom: 1 or 0 atoms
        - linear: 2 or more atoms, all coordinates aligned on z-axis
        - planar: 3 or more atoms, all coordinates in xy plane (z=0)
        - other: non-planar molecules
        """
        # Use the internal get_geometry function
        geometry_data = self.get_geometry()

        # Check if geometry is loaded
        if isinstance(geometry_data, str):
            return "atom"

        # Number of atoms
        num_atoms = len(geometry_data)
        print(f"Number of atoms: {num_atoms}")
        print(f"Geometry data: {geometry_data}")

        # Atom case
        if num_atoms <= 1:
            return "atom"

        # Extract coordinates from geometry data
        coords = [(atom[1], atom[2], atom[3]) for atom in geometry_data]

        # Linear case: 2 or more atoms, all aligned on z-axis (y and x coordinates are 0)
        if all(abs(coord[0]) < 1e-6 and abs(coord[1]) < 1e-6 for coord in coords) and num_atoms >= 2:
            return "linear"
        # Planar case: 3 or more atoms, all in xy plane (z=0)
        elif all(abs(coord[2]) < 1e-6 for coord in coords) and num_atoms >= 3:
            return "planar"
        # Other case: non-planar molecules
        else:
            return "other"

    def load_geometry(self):
        """Load molecular geometry from XYZ file."""
        file_path = os.path.join(MOLECULES_DIR, f"{self.name}.xyz")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                lines = f.readlines()
                formula = lines[1].split(" ")[1]
                self.formula = formula if formula else self.name
                if len(lines) > 1:
                    lines[1] = f"{self.name} {self.formula}\n"
                self.geometry = "".join(lines[2:])
                print(f"Geometry for {self.name} successfully loaded.")
        else:
            print(f".xyz file for molecule {self.name} not found in {file_path}.")

    def get_molecule_description(self):
        """Get a descriptive string of the molecule."""
        description = f"{self.name}"
        if self.is_harmonium:
            description += f"_omega_{self.omega}"
        return description

    def convert_formula_to_latex(self):
        """Convert molecular formula to LaTeX format."""
        if not self.formula:
            return self.name

        formula_latex = re.sub(r"([A-Z][a-z]*)(\d+)", r"\1_\{\2\}", self.formula)
        formula_latex = re.sub(r"\((.*?)\)(\d+)", r"(\1)_\{\2\}", formula_latex)
        formula_latex = re.sub(
            r"\^([+-]?\d*)", lambda m: f"^{{{m.group(1)}}}", formula_latex
        )
        return formula_latex



    def unique_atoms(self):
        """
        Get list of unique elements in the molecule.

        Returns:
            list: List of unique element symbols.
        """
        if not self.formula:
            return []

        elements = re.findall(r"[A-Z][a-z]*", self.formula)
        return sorted(set(elements))

    def molecular_weight(self, atomic_weights):
        """
        Calculate molecular weight based on formula and atomic weights.

        Args:
            atomic_weights (dict): Dictionary of atomic weights (e.g., {'H': 1.008})

        Returns:
            float: Molecular weight
        """
        if not self.formula:
            return 0.0

        atom_counts = re.findall(r"([A-Z][a-z]*)(\d*)", self.formula)
        weight = sum(
            atomic_weights[atom] * (int(count) if count else 1)
            for atom, count in atom_counts
        )
        return weight

    def geometry_summary(self):
        """
        Summarize atoms in the loaded geometry.

        Returns:
            dict: Elements as keys and their counts as values.
        """
        if not self.geometry:
            return "Geometry not loaded"

        atoms = [line.split()[0] for line in self.geometry.strip().splitlines()]
        atom_counts = Counter(atoms)
        return dict(atom_counts)

    def count_atoms(self):
        """
        Count total number of atoms in the molecule based on geometry.

        Returns:
            int: Total number of atoms.
        """
        if not self.geometry:
            return 1  # Default to 1 for atoms or when geometry is not loaded

        # Count atoms from geometry if available
        lines = self.geometry.strip().split("\n")
        return len(lines)

    def count_electrons(self):
        """
        Calculate total number of electrons in the molecule.

        Returns:
            int: Total number of electrons.
        """
        # Base calculation: atomic number minus charge
        base_electrons = 0

        if self.geometry:
            # Count electrons from geometry
            lines = self.geometry.strip().split("\n")
            base_electrons = sum(self.get_atomic_number(line.split()[0]) for line in lines)
        elif self.name:
            # Fallback to predefined electronic configurations
            electron_map = {
                "harmonium": 2,  # Special case for harmonium
                # Add more predefined atoms as needed
            }
            base_electrons = electron_map.get(self.name.lower(), 0)

        # Subtract electrons based on charge
        electrons = base_electrons - self.charge

        return electrons

    def __str__(self):
        if self.is_harmonium:
            return f"Harmonium(w={self.omega})"
        else:
            charge_str = '' if self.charge == 0 else f"( charge = {self.charge})"
            multiplicity_str = '' if self.multiplicity == 1 else f"( mult = {self.multiplicity})"
            return f"{self.name.replace('_',' ')}{charge_str}{multiplicity_str}"

    def get_geometry(self):
        """
        Get the molecular geometry as a list of lists.

        Returns:
            list or str: The molecular geometry as a list of lists where each inner list
                        contains [atom_symbol, x, y, z] with coordinates as floats,
                        or a string message if geometry is not loaded.
        """
        if not self.geometry:
            return "Geometry not loaded"

        try:
            geometry_list = []
            lines = self.geometry.strip().split('\n')

            for line in lines:
                # Skip empty lines
                if not line.strip():
                    continue

                # Split the line and handle potential issues
                parts = line.strip().split()
                if len(parts) < 4:
                    continue  # Skip lines that don't have enough data

                atom = parts[0]
                # Convert coordinates to float, with error handling
                try:
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3])
                    geometry_list.append([atom, x, y, z])
                except ValueError:
                    # Handle case where coordinates can't be converted to float
                    continue

            return geometry_list
        except Exception as e:
            return f"Error parsing geometry: {str(e)}"

    def get_xyz_geometry(self):
        """
        Get the molecular geometry as a list of XYZ coordinates.

        Returns:
            list: List of atomic coordinates in XYZ format.
        """
        if self.geometry:
            return self.geometry
        return "Geometry not loaded"

    def get_atomic_number(self,symbol):
        """
        Convert atomic symbol to atomic number.

        Args:
            symbol (str): Atomic symbol (e.g., 'H', 'He', 'C')

        Returns:
            int: Atomic number corresponding to the symbol
        """
        # Dictionary mapping atomic symbols to atomic numbers
        atomic_numbers = {
            'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10,
            'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20,
            'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30,
            'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40,
            'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50,
            'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60,
            'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70,
            'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80,
            'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90,
            'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100,
            'Md': 101, 'No': 102, 'Lr': 103, 'Rf': 104, 'Db': 105, 'Sg': 106, 'Bh': 107, 'Hs': 108, 'Mt': 109,
            'Ds': 110, 'Rg': 111, 'Cn': 112, 'Nh': 113, 'Fl': 114, 'Mc': 115, 'Lv': 116, 'Ts': 117, 'Og': 118
        }

        # Handle case sensitivity by converting the first letter to uppercase and rest to lowercase
        if symbol and len(symbol) > 0:
            formatted_symbol = symbol[0].upper() + symbol[1:].lower() if len(symbol) > 1 else symbol.upper()

            if formatted_symbol in atomic_numbers:
                return atomic_numbers[formatted_symbol]

        # Return 0 for unrecognized symbols (could alternatively raise an exception)
        return 0


if __name__ == "__main__":
    # Test the Molecule class
    print("Testing Molecule class...")

    # Test 1: Water molecule
    h2o = Molecule(name="water")
    print("\nWater molecule test:")
    print(h2o)
    print("Formula in LaTeX:", h2o.convert_formula_to_latex())
    print("Total atoms:", h2o.count_atoms())
    print("Unique elements:", h2o.unique_atoms())
    print("Geometry summary:", h2o.geometry_summary())

    # Test 2: Harmonium
    print("\nHarmonium test:")
    harmonium = Molecule(omega=0.5)
    print(harmonium)
    print("Description:", harmonium.get_molecule_description())

    # Test 3: Non-existent molecule
    print("\nNon-existent molecule test:")
    fake = Molecule(name="nonexistent")
    print(fake)
