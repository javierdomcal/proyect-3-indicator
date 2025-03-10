from ..config.settings import MOLECULES_DIR
import os
import re
from collections import Counter


class Molecule:
    def __init__(self, name="harmonium", omega=None, charge=0, multiplicity=1):
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
        self.molecule_type = None

        if not self.is_harmonium:
            self.load_geometry()
            self.classify_molecule()

        if self.is_harmonium:
            self.name = "harmonium"
            self.charge = -2
            self.multiplicity = 1
            self.molecule_type = 'atom'

    def classify_molecule(self):
        """Classify the molecule type based on its geometry."""
        if not self.geometry:
            self.molecule_type = "atom"
        else:
            lines = self.geometry.strip().split("\n")
            num_atoms = len(lines)

            if num_atoms == 1:
                self.molecule_type = "atom"
            elif num_atoms == 2:
                self.molecule_type = "diatomic"
            else:
                # Check if all atoms lie on the same plane (z-coordinate)
                z_coords = [float(line.split()[3]) for line in lines]
                if all(abs(z - z_coords[0]) < 1e-6 for z in z_coords):
                    self.molecule_type = "planar"
                else:
                    self.molecule_type = "other"

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

    def count_atoms(self):
        """
        Count total number of atoms in the molecule based on formula.

        Returns:
            int: Total number of atoms.
        """
        if not self.formula:
            return 0

        atom_counts = re.findall(r"([A-Z][a-z]*)(\d*)", self.formula)
        total_atoms = sum(int(count) if count else 1 for _, count in atom_counts)
        return total_atoms

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

    def __str__(self):
        if self.is_harmonium:
            return f"Harmonium(w={self.omega})"
        else:
            charge_str = '' if self.charge == 0 else f"( charge = {self.charge})"
            multiplicity_str = '' if self.multiplicity == 1 else f"( mult = {self.multiplicity})"
            return f"{self.name.replace('_',' ')}{charge_str}{multiplicity_str}"


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
