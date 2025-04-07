"""
Calculation data model and operations.
Provides a clean API for working with calculation data in the database.
"""

import logging
import time
from ..cache import cached, invalidate_cache

logger = logging.getLogger(__name__)

class CalculationModel:
    """
    Model for working with calculation data.
    Provides a higher-level API than the raw database adapter.
    """

    def __init__(self, db_adapter):
        """
        Initialize the calculation model.

        Args:
            db_adapter: DatabaseAdapter instance
        """
        self.db = db_adapter

    @cached("calculation:id", ttl=300)  # Cache for 5 minutes
    def get(self, calculation_id):
        """
        Get a calculation by ID.

        Args:
            calculation_id (int): Calculation ID

        Returns:
            dict: Calculation data or None if not found
        """
        with self.db.transaction():
            return self.db.get_calculation(calculation_id)

    def find(self, molecule_id, basis_set, method, config_type='SP', grid=None):
        """
        Find a calculation by its parameters.

        Args:
            molecule_id (int): Molecule ID
            basis_set (str): Basis set name
            method (str): Calculation method
            config_type (str): Configuration type (SP/Opt)
            grid: Grid object (optional)

        Returns:
            dict: Calculation details or None if not found
        """
        with self.db.transaction():
            return self.db.find_calculation(molecule_id, basis_set, method, config_type, grid)

    def add(self, molecule_id, basis_set, method, config_type='SP', grid=None, code_version=None):
        """
        Add a new calculation.

        Args:
            molecule_id (int): Molecule ID
            basis_set (str): Basis set name
            method (str): Calculation method
            config_type (str): Configuration type (SP/Opt)
            grid: Grid object (optional)
            code_version (str): Version of the code (optional)

        Returns:
            int: Calculation ID
        """
        with self.db.transaction():
            calc_id = self.db.add_calculation(molecule_id, basis_set, method,
                                            config_type, grid, code_version)
            return calc_id

    def update_status(self, calculation_id, status, error_message=None):
        """
        Update the status of a calculation.

        Args:
            calculation_id (int): Calculation ID
            status (str): New status (pending/running/completed/failed)
            error_message (str): Error message (if status is failed)

        Returns:
            bool: Success
        """
        with self.db.transaction():
            result = self.db.update_calculation_status(calculation_id, status, error_message)
            # Invalidate cache for this calculation
            invalidate_cache("calculation:id", calculation_id)
            return result

    def find_or_create(self, molecule_id, basis_set, method, config_type='SP', grid=None, code_version=None):
        """
        Find a calculation by parameters or create it if not found.

        Args:
            molecule_id (int): Molecule ID
            basis_set (str): Basis set name
            method (str): Calculation method
            config_type (str): Configuration type (SP/Opt)
            grid: Grid object (optional)
            code_version (str): Version of the code (optional)

        Returns:
            tuple: (calculation_id, created, calculation_info)
        """
        # First try to find existing
        calc_info = self.find(molecule_id, basis_set, method, config_type, grid)

        if calc_info:
            return calc_info["id"], False, calc_info

        # Not found, create new
        with self.db.transaction():
            calc_id = self.db.add_calculation(molecule_id, basis_set, method,
                                            config_type, grid, code_version)

            # Get the newly created calculation
            calc_info = self.get(calc_id)
            return calc_id, True, calc_info

    def add_tag(self, calculation_id, tag):
        """
        Add a tag to a calculation.

        Args:
            calculation_id (int): Calculation ID
            tag (str): Tag to add

        Returns:
            bool: Success
        """
        with self.db.transaction():
            return self.db.add_tag(calculation_id, tag)

    def get_tags(self, calculation_id):
        """
        Get all tags for a calculation.

        Args:
            calculation_id (int): Calculation ID

        Returns:
            list: List of tags
        """
        with self.db.transaction():
            return self.db.get_tags(calculation_id)

    def find_by_tag(self, tag):
        """
        Find calculations with a specific tag.

        Args:
            tag (str): Tag to search for

        Returns:
            list: List of calculation IDs
        """
        with self.db.transaction():
            return self.db.find_calculations_by_tag(tag)

