"""
Handles physical storage and retrieval of result files.
"""

import os
import json
import shutil
import logging
from pathlib import Path


class ResultsStorage:
    """Handles physical storage operations for calculation results."""

    def __init__(self, base_path):
        """Initialize with base path for results storage."""
        self.base_path = Path(base_path)
        self._ensure_base_directory()

    def _ensure_base_directory(self):
        """Ensure base results directory exists."""
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_calculation_directory(self, calculation_hash):
        """
        Create and return directory for a calculation's results.

        Args:
            calculation_hash: Unique identifier for the calculation

        Returns:
            Path: Directory path
        """
        calc_dir = self.base_path / calculation_hash
        calc_dir.mkdir(exist_ok=True)
        return calc_dir

    def store_json(self, filepath, data):
        """
        Store data as JSON file.

        Args:
            filepath: Path for JSON file
            data: Data to store
        """
        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Error storing JSON at {filepath}: {e}")
            raise

    def load_json(self, filepath):
        """
        Load data from JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            Loaded data
        """
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading JSON from {filepath}: {e}")
            raise

    def copy_optimized_geometry(self, colony_path, calc_dir):
        """
        Copy optimized geometry file from colony to results.

        Args:
            colony_path: Path to colony directory
            calc_dir: Path to calculation results directory
        """
        try:
            source = Path(colony_path) / "optimized_geometry.xyz"
            if source.exists():
                shutil.copy2(source, calc_dir / "optimized_geometry.xyz")
        except Exception as e:
            logging.error(f"Error copying optimized geometry: {e}")
            raise

    def copy_ontop_file(self, colony_path, calc_dir):
        """
        Copy ontop.dat file from colony to results.

        Args:
            colony_path: Path to colony directory
            calc_dir: Path to calculation results directory
        """
        try:
            source = Path(colony_path) / "ontop.dat"
            if source.exists():
                shutil.copy2(source, calc_dir / "ontop.dat")
        except Exception as e:
            logging.error(f"Error copying ontop file: {e}")
            raise

    def load_xyz(self, filepath):
        """
        Load XYZ file content.

        Args:
            filepath: Path to XYZ file

        Returns:
            str: File content
        """
        try:
            with open(filepath, "r") as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error loading XYZ file {filepath}: {e}")
            raise

    def load_ontop(self, filepath):
        """
        Load ontop.dat file content.

        Args:
            filepath: Path to ontop.dat file

        Returns:
            str: File content
        """
        try:
            with open(filepath, "r") as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error loading ontop file {filepath}: {e}")
            raise
