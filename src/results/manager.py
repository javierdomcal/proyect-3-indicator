"""
Main interface for managing calculation results.
"""

import os
import json
import shutil
import logging
from pathlib import Path

from results.storage import ResultsStorage
from results.formats import ResultsFormatter

class ResultsManager:
    """Manages storage and retrieval of calculation results."""

    def __init__(self, base_path="../results"):
        """Initialize with path to results directory."""
        self.base_path = Path(base_path).resolve()
        self.storage = ResultsStorage(self.base_path)
        self.formatter = ResultsFormatter()

    def store_calculation_results(self, calculation_hash, details, results, colony_path, has_optimization=False):
        """
        Store calculation results in the standard format.

        Args:
            calculation_hash: Unique identifier for the calculation
            details: Dictionary containing calculation details
            results: Dictionary containing calculation results
            colony_path: Path to colony directory containing files
            has_optimization: Whether geometry optimization was performed
        """
        try:
            # Create calculation directory
            calc_dir = self.storage.create_calculation_directory(calculation_hash)

            # Store details.json
            self.storage.store_json(calc_dir / "details.json", details)

            # Store results.json
            formatted_results = self.formatter.format_results(results)
            self.storage.store_json(calc_dir / "results.json", formatted_results)

            # Copy relevant files from colony
            if has_optimization:
                self.storage.copy_optimized_geometry(colony_path, calc_dir)

            self.storage.copy_ontop_file(colony_path, calc_dir)

            logging.info(f"Stored results for calculation {calculation_hash}")
            return calc_dir

        except Exception as e:
            logging.error(f"Error storing results for {calculation_hash}: {e}")
            raise

    def get_calculation_results(self, calculation_hash):
        """
        Retrieve results for a calculation.

        Args:
            calculation_hash: Unique identifier for the calculation

        Returns:
            Dictionary containing all result information
        """
        try:
            # Get calculation directory
            calc_dir = self.base_path / calculation_hash
            if not calc_dir.exists():
                raise FileNotFoundError(f"No results found for {calculation_hash}")

            # Load all result files
            details = self.storage.load_json(calc_dir / "details.json")
            results = self.storage.load_json(calc_dir / "results.json")

            # Check for optional files
            has_optimization = (calc_dir / "optimized_geometry.xyz").exists()
            has_ontop = (calc_dir / "ontop.dat").exists()

            output = {
                "details": details,
                "results": results,
                "has_optimization": has_optimization,
                "has_ontop": has_ontop
            }

            # Add file contents if they exist
            if has_optimization:
                output["optimized_geometry"] = self.storage.load_xyz(calc_dir / "optimized_geometry.xyz")
            if has_ontop:
                output["ontop"] = self.storage.load_ontop(calc_dir / "ontop.dat")

            return output

        except Exception as e:
            logging.error(f"Error retrieving results for {calculation_hash}: {e}")
            raise

    def check_calculation_exists(self, calculation_hash):
        """
        Check if results exist for a calculation.

        Args:
            calculation_hash: Unique identifier for the calculation

        Returns:
            bool: Whether complete results exist
        """
        try:
            calc_dir = self.base_path / calculation_hash
            if not calc_dir.exists():
                return False

            # Check for required files
            required_files = ["details.json", "results.json"]
            return all((calc_dir / file).exists() for file in required_files)

        except Exception as e:
            logging.error(f"Error checking results for {calculation_hash}: {e}")
            return False

    def clean_calculation_results(self, calculation_hash):
        """
        Remove results for a calculation.

        Args:
            calculation_hash: Unique identifier for the calculation
        """
        try:
            calc_dir = self.base_path / calculation_hash
            if calc_dir.exists():
                shutil.rmtree(calc_dir)
                logging.info(f"Cleaned results for {calculation_hash}")

        except Exception as e:
            logging.error(f"Error cleaning results for {calculation_hash}: {e}")
            raise