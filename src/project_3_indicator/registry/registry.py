"""
Registry for managing calculations using the new database structure.
"""
from pathlib import Path
from datetime import datetime
from ..database.operations import DatabaseOperations
from ..input.specification import InputSpecification

class Registry:
    """
    Registry class that uses the new database structure.
    Acts as an adapter between the old registry interface and the new database.
    """
    def __init__(self):
        """Initialize registry with database operations."""
        self.db = DatabaseOperations()
        self.results_dir = Path("results")

    def register_calculation(self, input_spec: InputSpecification) -> str:
        """
        Register a new calculation or return existing ID if found.

        Args:
            input_spec: InputSpecification instance

        Returns:
            str: Calculation ID
        """
        try:
            return self.db.register_calculation(
                molecule=input_spec.molecule,
                method=input_spec.method,
                basis=input_spec.basis,
                scanning_props=input_spec.scanning_props,
                config=input_spec.config,
                excited_state=input_spec.method.excited_state
            )
        except Exception as e:
            raise ValueError(f"Failed to register calculation: {str(e)}")

    def get_status(self, calc_id: str) -> str:
        """Get calculation status."""
        calc_info = self.db.get_calculation_info(calc_id)
        return calc_info["status"] if calc_info else None

    def update_status(self, calc_id: str, status: str, message: str = None):
        """Update calculation status."""
        try:
            self.db.update_calculation_status(calc_id, status, message)
        except Exception as e:
            raise ValueError(f"Failed to update status: {str(e)}")

    def get_calc_info(self, calc_id: str) -> dict:
        """
        Get all information for a calculation.

        Returns a dictionary containing both the calculation info
        and its related objects (molecule, method, basis).
        """
        try:
            calc_info = self.db.get_calculation_info(calc_id)
            if not calc_info:
                return None

            # Convert to the expected format for backward compatibility
            return {
                "id": calc_info["id"],
                "status": calc_info["status"],
                "created": calc_info["created_at"],
                "last_updated": calc_info["last_updated"],
                "message": calc_info["message"],
                "results_path": calc_info["results_path"],
                "input": {
                    "molecule": {
                        "name": calc_info["molecule_name"],
                        "omega": calc_info["molecule_omega"],
                        "charge": calc_info["charge"],
                        "multiplicity": calc_info["multiplicity"],
                        "geometry": calc_info["geometry"]
                    },
                    "method": {
                        "name": calc_info["method_name"],
                        "n": calc_info["n_electrons"],
                        "m": calc_info["m_orbitals"],
                        "excited_state": calc_info["excited_state"],
                        "keywords": calc_info["keywords"]
                    },
                    "basis": {
                        "name": calc_info["basis_name"],
                        "omega": calc_info["basis_omega"],
                        "is_even_tempered": calc_info["is_even_tempered"],
                        "is_imported": calc_info["is_imported"]
                    },
                    "scanning_props": {
                        "atom_indices": calc_info["atom_indices"],
                        "directions": calc_info["directions"],
                        "end_distance": calc_info["end_distance"],
                        "step_size": calc_info["step_size"]
                    } if calc_info.get("atom_indices") else None,
                    "config": calc_info["config"]
                }
            }
        except Exception as e:
            raise ValueError(f"Failed to get calculation info: {str(e)}")

    def get_results_path(self, calc_id: str) -> Path:
        """Get path where results should be stored."""
        calc_info = self.db.get_calculation_info(calc_id)
        if calc_info:
            return Path(calc_info["results_path"])
        return None

    def calculation_complete(self, calc_id: str) -> bool:
        """Check if calculation has completed successfully."""
        calc_info = self.db.get_calculation_info(calc_id)
        if not calc_info:
            return False
        return (calc_info["status"] == "completed" and
                Path(calc_info["results_path"]).exists())