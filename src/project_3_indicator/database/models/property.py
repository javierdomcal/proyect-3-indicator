"""
Property data model and operations.
Provides a clean API for working with property data in the database.
"""

import logging
import json
from ..cache import cached, invalidate_cache

logger = logging.getLogger(__name__)

class PropertyModel:
    """
    Model for working with property data.
    Provides a higher-level API than the raw database adapter.
    """

    def __init__(self, db_adapter):
        """
        Initialize the property model.

        Args:
            db_adapter: DatabaseAdapter instance
        """
        self.db = db_adapter

    @cached("property", ttl=300)  # Cache for 5 minutes
    def get(self, calculation_id, property_name):
        """
        Get a property for a calculation.

        Args:
            calculation_id (int): Calculation ID
            property_name (str): Property name

        Returns:
            dict: Property details or None if not found
        """
        with self.db.transaction():
            return self.db.get_property(calculation_id, property_name)

    def add_properties(self, calculation_id, property_names):
        """
        Add properties to track for a calculation.

        Args:
            calculation_id (int): Calculation ID
            property_names (list): List of property names to add

        Returns:
            bool: Success
        """
        with self.db.transaction():
            return self.db.add_properties(calculation_id, property_names)

    def store_result(self, calculation_id, property_name, property_data):
        """
        Store a property result.

        Args:
            calculation_id (int): Calculation ID
            property_name (str): Property name
            property_data: Property data (will be serialized to JSON if not a string)

        Returns:
            bool: Success
        """
        with self.db.transaction():
            result = self.db.store_property_result(calculation_id, property_name, property_data)
            # Invalidate cache for this property
            invalidate_cache("property", calculation_id, property_name)
            return result

    def get_missing_properties(self, calculation_id, requested_props):
        """
        Get a list of properties that need to be calculated.

        Args:
            calculation_id (int): Calculation ID
            requested_props (list): List of requested property names

        Returns:
            list: List of property names that need to be calculated
        """
        with self.db.transaction():
            return self.db.get_missing_properties(calculation_id, requested_props)

    def process_properties_list(self, properties_obj):
        """
        Process a Properties object or list into a standardized list of property names.

        Args:
            properties_obj: Properties object or list of property names

        Returns:
            list: Standardized list of property names
        """
        if properties_obj is None:
            return []

        # If it's a Properties object with get_active_properties method
        if hasattr(properties_obj, 'get_active_properties'):
            return properties_obj.get_active_properties()

        # If it's already a list
        if isinstance(properties_obj, list):
            return properties_obj

        # If it's a string (single property)
        if isinstance(properties_obj, str):
            return [properties_obj]

        # Default empty list
        return []

    def get_active_properties(self, calculation_id):
        """
        Get all active properties for a calculation.

        Args:
            calculation_id (int): Calculation ID

        Returns:
            list: List of active property names
        """
        with self.db.transaction():
            conn = self.db.get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """SELECT property_name FROM properties
                    WHERE calculation_id=?""",
                    (calculation_id,)
                )

                return [row[0] for row in cursor.fetchall()]

            except Exception as e:
                logger.error(f"Error getting active properties for calculation {calculation_id}: {str(e)}")
                return []

    def get_completed_properties(self, calculation_id):
        """
        Get a list of properties that have been successfully calculated.

        Args:
            calculation_id (int): Calculation ID

        Returns:
            list: List of property names that have been completed
        """
        with self.db.transaction():
            conn = self.db.get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """SELECT property_name FROM properties
                    WHERE calculation_id=? AND completed=1""",
                    (calculation_id,)
                )

                return [row[0] for row in cursor.fetchall()]

            except Exception as e:
                logger.error(f"Error getting completed properties for calculation {calculation_id}: {str(e)}")
                return []