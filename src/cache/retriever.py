"""
Handles retrieval of cached calculation results.
"""

import logging
from pathlib import Path

from results import ResultsManager
from registry.metadata import MetadataManager
from cache.checker import CacheChecker


class CacheRetriever:
    """Retrieves cached calculation results."""

    def __init__(self, results_path="../results"):
        """Initialize retriever with results path."""
        self.results = ResultsManager(results_path)
        self.checker = CacheChecker(results_path)
        self.metadata = MetadataManager()

    def get_calculation_result(self, calculation_hash, validate=True):
        """
        Retrieve results for a cached calculation.

        Args:
            calculation_hash: Unique identifier for calculation
            validate: Whether to validate results before returning

        Returns:
            tuple: (results, status_message)
        """
        try:
            # First check calculation exists and is valid
            if validate:
                exists, status, message = self.checker.check_calculation(
                    calculation_hash
                )
                if not exists:
                    return None, message

                is_valid, validation_message = self.checker.validate_calculation(
                    calculation_hash
                )
                if not is_valid:
                    return None, validation_message

            # Get the results
            results = self.results.get_calculation_results(calculation_hash)
            if not results:
                return None, "Failed to retrieve results"

            return results, "Results retrieved successfully"

        except Exception as e:
            logging.error(f"Error retrieving results for {calculation_hash}: {e}")
            return None, f"Error retrieving results: {str(e)}"

    def get_calculation_files(self, calculation_hash, file_list=None):
        """
        Retrieve specific result files for a calculation.

        Args:
            calculation_hash: Unique identifier for calculation
            file_list: List of files to retrieve (None for all)

        Returns:
            dict: Dictionary of filename: content pairs
        """
        try:
            # Default file list if none provided
            if file_list is None:
                file_list = [
                    "details.json",
                    "results.json",
                    "optimized_geometry.xyz",
                    "ontop.dat",
                ]

            # Get calculation directory
            calc_dir = Path(self.results.base_path) / calculation_hash
            if not calc_dir.exists():
                return {}

            # Collect requested files
            files = {}
            for filename in file_list:
                filepath = calc_dir / filename
                if filepath.exists():
                    with open(filepath, "r") as f:
                        files[filename] = f.read()

            return files

        except Exception as e:
            logging.error(f"Error retrieving files for {calculation_hash}: {e}")
            return {}

    def get_calculation_chain(self, calculation_hash):
        """
        Retrieve full chain of calculations leading to this one.

        Args:
            calculation_hash: Unique identifier for final calculation

        Returns:
            dict: Dictionary of all related calculation results
        """
        try:
            # Get the target calculation first
            results = self.results.get_calculation_results(calculation_hash)
            if not results:
                return {}

            chain = {calculation_hash: results}

            # Get details to find prerequisites
            details = results["details"]

            # Recursively get prerequisites based on type
            if details.get("calculation_type") == "inca":
                dm2prim_hash = details.get("dm2prim_calculation_hash")
                if dm2prim_hash:
                    chain.update(self.get_calculation_chain(dm2prim_hash))

            elif details.get("calculation_type") == "dm2prim":
                dmn_hash = details.get("dmn_calculation_hash")
                if dmn_hash:
                    chain.update(self.get_calculation_chain(dmn_hash))

            elif details.get("calculation_type") == "dmn":
                gaussian_hash = details.get("gaussian_calculation_hash")
                if gaussian_hash:
                    chain.update(self.get_calculation_chain(gaussian_hash))

            return chain

        except Exception as e:
            logging.error(
                f"Error retrieving calculation chain for {calculation_hash}: {e}"
            )
            return {}

    def get_calculations_by_criteria(self, criteria):
        """
        Find calculations matching given criteria.

        Args:
            criteria: Dictionary of criteria to match

        Returns:
            list: List of matching calculation hashes
        """
        try:
            # Search metadata for matching calculations
            matches = self.metadata.search_metadata(criteria)

            # Filter to only valid calculations
            valid_matches = []
            for calc_hash in matches:
                exists, status, _ = self.checker.check_calculation(calc_hash)
                if exists and status == "completed":
                    valid_matches.append(calc_hash)

            return valid_matches

        except Exception as e:
            logging.error(f"Error searching calculations: {e}")
            return []
