import os
import re
from collections import Counter


class Molecule:
    def __init__(self, name="harmonium", omega=None, charge=0, multiplicity=1):
        self.name = name.lower()
        self.omega = omega
        self.charge = charge
        self.multiplicity = multiplicity
        self.is_harmonium = omega is not None
        self.geometry = None

        if not self.is_harmonium:
            self.load_geometry()

        if self.is_harmonium:
            self.name = "harmonium"
            self.charge = -2
            self.multiplicity = 1

    def load_geometry(self):
        file_path = f"utils/molecules/{self.name}.xyz"
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
        description = f"{self.name}"
        if self.is_harmonium:
            description += f"_omega_{self.omega}"
        return description

    def convert_formula_to_latex(self):
        formula_latex = re.sub(r"([A-Z][a-z]*)(\d+)", r"\1_\{\2\}", self.formula)
        formula_latex = re.sub(r"\((.*?)\)(\d+)", r"(\1)_\{\2\}", formula_latex)
        formula_latex = re.sub(
            r"\^([+-]?\d*)", lambda m: f"^{{{m.group(1)}}}", formula_latex
        )
        return formula_latex

    def count_atoms(self):
        """
        Counts the total number of atoms in the molecule based on the formula.

        Returns:
            int: Total number of atoms.
        """
        atom_counts = re.findall(r"([A-Z][a-z]*)(\d*)", self.formula)
        total_atoms = sum(int(count) if count else 1 for _, count in atom_counts)
        return total_atoms

    def unique_atoms(self):
        """
        Returns a list of unique elements present in the molecule.

        Returns:
            list: List of unique element symbols.
        """
        elements = re.findall(r"[A-Z][a-z]*", self.formula)
        return sorted(set(elements))

    def molecular_weight(self, atomic_weights):
        """
        Calculates the molecular weight based on the formula and provided atomic weights.

        Parameters:
            atomic_weights (dict): A dictionary of atomic weights (e.g., {'H': 1.008, 'O': 16.00})

        Returns:
            float: The molecular weight of the molecule.
        """
        atom_counts = re.findall(r"([A-Z][a-z]*)(\d*)", self.formula)
        weight = sum(
            atomic_weights[atom] * (int(count) if count else 1)
            for atom, count in atom_counts
        )
        return weight

    def geometry_summary(self):
        """
        Provides a summary of atoms in the loaded geometry, including counts by type.

        Returns:
            dict: A dictionary with elements as keys and their counts in the geometry as values.
        """
        if not self.geometry:
            return "Geometry not loaded"

        atoms = [line.split()[0] for line in self.geometry.strip().splitlines()]
        atom_counts = Counter(atoms)
        return dict(atom_counts)

    def __str__(self):
        if self.is_harmonium:
            return f"Harmonium, Omega={self.omega}"
        else:
            geometry_str = self.geometry if self.geometry else "Geometry not loaded"
            formula_str = "(" + self.formula + ")" if self.formula != self.name else ""
            return f"Molecule: {self.name.replace('_',' ')} {formula_str}, Charge={self.charge}, Multiplicity={self.multiplicity}\nGeometry:\n{geometry_str}"


# Example usage
if __name__ == "__main__":
    # Creating a water molecule (H2O) with geometry from an .xyz file
    h2o = Molecule(name="water")
    print(h2o)
    print("Formula in LaTeX:", h2o.convert_formula_to_latex())
    print("Total atoms:", h2o.count_atoms())
    print("Unique elements:", h2o.unique_elements())

    # Sample atomic weights for H and O
    atomic_weights = {"H": 1.008, "O": 16.00}
    print("Molecular weight:", h2o.molecular_weight(atomic_weights))

    # Summarize geometry if loaded
    print("Geometry summary:", h2o.geometry_summary())
