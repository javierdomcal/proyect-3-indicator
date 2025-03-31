"""
Database package for the computational chemistry project.
Provides a clean API for interacting with the database.
"""

import logging
from .adapter import DatabaseAdapter
from .models.molecule import MoleculeModel
from .models.calculation import CalculationModel
from .models.property import PropertyModel
from .schema import init_db
from .connection import close_connections

logger = logging.getLogger(__name__)

class ChemistryDatabase:
    """
    Main database interface for the application.
    Provides access to all database models.
    """

    def __init__(self):
        """Initialize the database interface."""
        # Ensure database is initialized
        init_db()

        # Create the database adapter
        self.adapter = DatabaseAdapter()

        # Create models
        self.molecules = MoleculeModel(self.adapter)
        self.calculations = CalculationModel(self.adapter)
        self.properties = PropertyModel(self.adapter)

        logger.debug("ChemistryDatabase initialized")

    @property
    def transaction(self):
        """Get the transaction context manager from the adapter."""
        return self.adapter.transaction

    def close(self):
        """Close all database connections."""
        close_connections()
        logger.debug("Database connections closed")

# Create a singleton instance
_db_instance = None

def get_database():
    """Get the global database instance, creating it if necessary."""
    global _db_instance
    if _db_instance is None:
        _db_instance = ChemistryDatabase()
    return _db_instance

def close_database():
    """Close the global database instance."""
    global _db_instance
    if _db_instance is not None:
        _db_instance.close()
        _db_instance = None