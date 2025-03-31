# src/input/basis.py

import os
from ..config.settings import UTILS_DIR
import re
import pandas as pd


class BasisSet:
    def __init__(self, name):
        """
        Initializes a BasisSet instance.

        Parameters:
        - name (str): Name of the basis set. If it follows the pattern "8SPDF", it's an even-tempered basis.
        - omega (float, optional): Omega parameter required for even-tempered bases associated with harmonium.
        - molecule (Molecule, optional): Molecule instance needed for helium-like atom case
        """
        self.name = name
        self.n = None
        self.angular_momentum = None
        self.is_even_tempered = self.check_if_even_tempered()
        self.is_imported = False
        self.alpha = None
        self.beta = None
        self.coefficients = None

        # Load coefficients if the basis is even-tempered


    def check_if_even_tempered(self):
        """
        Checks if the basis name follows the format for even-tempered bases (e.g., "8SPDF").
        """
        match = re.match(r"(\d+)([A-Z]+)$", self.name)
        if match:
            self.n = int(match.group(1))
            self.angular_momentum = match.group(
                2
            )  # Extracts angular momentum part (SPDF, SPD, etc.)
            return True
        return False

    def load_even_tempered_coefficients(self, molecule):
        """
        Load coefficients for even-tempered basis.

        Supports both harmonium and helium-like atom cases.
        """
        try:
            # Determine which CSV to use
            if molecule.omega is not None:
                # Harmonium case
                csv_path = os.path.join(UTILS_DIR, "even-tempered-coefficients.csv")
                df = pd.read_csv(csv_path)
                row = df[(df["n"] == self.n) &
                         (abs(df["omega"].astype(float) - molecule.omega) < 0.00001)]
            elif molecule is not None:
                # Helium-like atom case
                csv_path = os.path.join(UTILS_DIR, "even-tempered-coefficients-helium.csv")

                # Check if file exists
                if not os.path.exists(csv_path):
                    raise FileNotFoundError(f"Required CSV file {csv_path} not found.")

                # Import here to avoid circular imports
                from ..utils.parsers import get_atomic_number

                # Get atomic number for the atom
                atomic_symbol = molecule.unique_atoms()[0] if molecule.unique_atoms() else "He"
                atomic_number = get_atomic_number(atomic_symbol)

                df = pd.read_csv(csv_path)
                row = df[(df["n"] == self.n) & (df["Z"] == atomic_number)]
            else:
                raise ValueError("Either omega or molecule must be provided for even-tempered basis sets")

            if row.empty:
                raise ValueError(f"Coefficients not found for specified parameters in {csv_path}")

            self.alpha = row.iloc[0]["alpha"]
            self.beta = row.iloc[0]["beta"]

            print(f"Even-tempered coefficients loaded: alpha={self.alpha}, beta={self.beta}")

        except FileNotFoundError as e:
            raise FileNotFoundError(f"CSV file error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error loading even-tempered coefficients: {str(e)}")

    def __str__(self):
        """
        Returns a string representation of the basis set.
        """
        return f"{self.name}"


if __name__ == "__main__":
    print("Testing BasisSet class...")

    # Test 1: Standard basis example
    print("\nStandard basis test:")
    standard_basis = BasisSet("6-31G")
    print(standard_basis)

    # Test 2: Even-tempered basis example with omega specified
    print("\nEven-tempered basis test (with omega):")
    even_tempered_basis = BasisSet("8SPDF", omega=0.5)
    print(even_tempered_basis)

    # Test 3: Invalid even-tempered basis configuration
    print("\nInvalid even-tempered basis test:")
    try:
        invalid_basis = BasisSet("8SPDF")
    except ValueError as e:
        print(f"Error: {e}")

    # Test 4: Non-existent coefficients
    print("\nNon-existent coefficients test:")
    try:
        nonexistent_basis = BasisSet("10SPDFGH", omega=0.3)
    except ValueError as e:
        print(f"Error: {e}")
