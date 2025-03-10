# src/input/basis.py

import os
from ..config.settings import UTILS_DIR
import re
import pandas as pd


class BasisSet:
    def __init__(self, basis_name, omega=None):
        """
        Initializes a BasisSet instance.

        Parameters:
        - basis_name (str): Name of the basis set. If it follows the pattern "8SPDF", it's an even-tempered basis.
        - omega (float, optional): Omega parameter required for even-tempered bases associated with harmonium.
        """
        self.basis_name = basis_name
        self.omega = omega
        self.n = None
        self.angular_momentum = None
        self.is_even_tempered = self.check_if_even_tempered()
        self.is_imported = False
        self.alpha = None
        self.beta = None
        self.coefficients = None

        # Load coefficients if the basis is even-tempered
        if self.is_even_tempered:
            if omega is None:
                raise ValueError("Even-tempered basis requires the omega parameter.")
            self.load_even_tempered_coefficients()

    def check_if_even_tempered(self):
        """
        Checks if the basis name follows the format for even-tempered bases (e.g., "8SPDF").
        """
        match = re.match(r"(\d+)([A-Z]+)$", self.basis_name)
        if match:
            self.n = int(match.group(1))
            self.angular_momentum = match.group(
                2
            )  # Extracts angular momentum part (SPDF, SPD, etc.)
            return True
        return False

    def load_even_tempered_coefficients(self):
        """
        Loads coefficients for an even-tempered basis from the CSV file using omega, n, and angular momentum.
        """
        csv_path = os.path.join(UTILS_DIR, "even-tempered-coefficients.csv")
        try:
            df = pd.read_csv(csv_path)
            # Filter row based on n, omega, and angular_momentum
            row = df[
                (df["n"] == self.n)
                & (abs(df["omega"].astype(float) - self.omega) < 0.00001)
            ]
            if row.empty:
                raise ValueError("Coefficients not found for the specified parameters.")
            self.alpha = row.iloc[0]["alpha"]
            self.beta = row.iloc[0]["beta"]
            print(
                f"Even-tempered coefficients loaded: alpha={self.alpha}, beta={self.beta}"
            )
        except FileNotFoundError:
            print(f"CSV file {csv_path} not found.")
        except Exception as e:
            print("Error loading even-tempered coefficients:", e)

    def __str__(self):
        """
        Returns a string representation of the basis set.
        """
        return f"{self.basis_name}"


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
