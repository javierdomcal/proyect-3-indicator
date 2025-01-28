"""
Handles checking for existing calculations in the cache.
"""

import logging
from pathlib import Path

from results import ResultsManager
from registry.status import StatusTracker
from registry.metadata import MetadataManager

class CacheChecker:
    """Checks for existing calculations in the cache."""

    def __init__(self, results_path="../results"):
        """Initialize checker with results path."""
        self.results = ResultsManager(results_path)
        self.status_tracker = StatusTracker()
        self.metadata = MetadataManager()

    def check_calculation(self, calculation_hash):
        """
        Full check for existing valid calculation.

        Args:
            calculation_hash: Unique identifier for calculation

        Returns:
            tuple: (exists, status, message)
        """
        try:
            # Check if results exist locally
            results_exist = self.results.check_calculation_exists(calculation_hash)

            # Get calculation status
            status_info = self.status_tracker.get_status(calculation_hash)
            current_status = status_info.get("status") if status_info else None

            # If no results or status, calculation doesn't exist
            if not results_exist and not current_status:
                return False, None, "Calculation not found"

            # If results exist but no status, something's wrong
            if results_exist and not current_status:
                return False, None, "Inconsistent state: results exist but no status"

            # If status exists but no results, calculation failed or is incomplete
            if not results_exist and current_status:
                return False, current_status, f"Calculation {current_status} but no results found"

            # Both exist - check status is completed
            if current_status != "completed":
                return False, current_status, f"Calculation exists but status is {current_status}"

            # All checks passed
            return True, "completed", "Calculation exists and is valid"

        except Exception as e:
            logging.error(f"Error checking calculation {calculation_hash}: {e}")
            return False, None, f"Error checking calculation: {str(e)}"

    def validate_calculation(self, calculation_hash):
        """
        Validate integrity of existing calculation.

        Args:
            calculation_hash: Unique identifier for calculation

        Returns:
            tuple: (is_valid, message)
        """
        try:
            # Get calculation results
            results = self.results.get_calculation_results(calculation_hash)
            if not results:
                return False, "No results found"

            # Check required files exist and are valid
            required_files = ["details", "results"]
            if not all(key in results for key in required_files):
                return False, "Missing required result files"

            # Check calculation was successful
            if not results["results"].get("calculation", {}).get("success", False):
                return False, "Calculation did not complete successfully"

            # Check if optimization was requested and completed
            details = results["details"]
            if details.get("config") == "Opt":
                if not results.get("has_optimization", False):
                    return False, "Optimization requested but not completed"

            return True, "Calculation is valid"

        except Exception as e:
            logging.error(f"Error validating calculation {calculation_hash}: {e}")
            return False, f"Error validating calculation: {str(e)}"

    def check_dependencies(self, calculation_hash):
        """
        Check if any required prerequisite calculations exist.

        Args:
            calculation_hash: Unique identifier for calculation

        Returns:
            tuple: (dependencies_met, missing_dependencies)
        """
        try:
            # Get calculation details
            results = self.results.get_calculation_results(calculation_hash)
            if not results:
                return False, []

            details = results["details"]

            # List of prerequisites based on calculation type
            prerequisites = []

            # Add required calculations based on type
            if details.get("calculation_type") == "dmn":
                prerequisites.append("gaussian")
            elif details.get("calculation_type") == "dm2prim":
                prerequisites.extend(["gaussian", "dmn"])
            elif details.get("calculation_type") == "inca":
                prerequisites.extend(["gaussian", "dmn", "dm2prim"])

            # Check each prerequisite
            missing = []
            for prereq in prerequisites:
                prereq_hash = details.get(f"{prereq}_calculation_hash")
                if not prereq_hash or not self.check_calculation(prereq_hash)[0]:
                    missing.append(prereq)

            return len(missing) == 0, missing

        except Exception as e:
            logging.error(f"Error checking dependencies for {calculation_hash}: {e}")
            return False, []