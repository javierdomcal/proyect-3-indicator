import hashlib
import json
from pathlib import Path
from datetime import datetime
import sys
import os

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.input_specification import InputSpecification
from src.molecule import Molecule
from src.method import Method
from src.basis import BasisSet


class CalculationRegistry:
    def __init__(self):
        self.registry_path = Path("utils/registry")
        self.registry_file = self.registry_path / "calculations.json"
        self.registry_path.mkdir(parents=True, exist_ok=True)
        if not self.registry_file.exists():
            self._save_registry({})

    def _load_registry(self):
        try:
            with open(self.registry_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save_registry(self, data):
        with open(self.registry_file, "w") as f:
            json.dump(data, f, indent=2)

    def generate_calculation_id(self, input_spec):
        """Generate unique ID from InputSpecification object."""
        calc_string = (
            (
                f"{input_spec.molecule.name}"
                f"{input_spec.method.method_name}"
                f"{input_spec.basis.basis_name}"
            )
            .lower()
            .replace(" ", "")
        )
        return hashlib.sha256(calc_string.encode()).hexdigest()[:12]

    def check_calculation_exists(self, input_spec):
        """Check if calculation exists using InputSpecification."""
        calc_id = self.generate_calculation_id(input_spec)
        registry = self._load_registry()
        if calc_id in registry:
            return calc_id, registry[calc_id].get("colony_dir")
        return None, None

    def register_calculation(self, input_spec, colony_dir):
        """Register calculation using InputSpecification."""
        calc_id = self.generate_calculation_id(input_spec)
        registry = self._load_registry()
        registry[calc_id] = {
            "molecule": input_spec.molecule.name,
            "method": input_spec.method.method_name,
            "basis": input_spec.basis.basis_name,
            "colony_dir": colony_dir,
            "created_at": datetime.now().isoformat(),
        }
        self._save_registry(registry)
        return calc_id


if __name__ == "__main__":
    # Simple test of registry functionality
    registry = CalculationRegistry()

    # Create a test input specification
    test_spec = InputSpecification(
        molecule=Molecule(name="water"),
        method=Method("HF"),
        basis=BasisSet("sto-3g"),
        title="test",
        config="SP",
    )

    # Test registration
    colony_dir = "/path/to/test"
    calc_id = registry.register_calculation(test_spec, colony_dir)
    print(f"Registered calculation with ID: {calc_id}")

    # Test lookup
    found_id, found_dir = registry.check_calculation_exists(test_spec)
    print(f"Found calculation: {found_id}")
    print(f"Colony directory: {found_dir}")
