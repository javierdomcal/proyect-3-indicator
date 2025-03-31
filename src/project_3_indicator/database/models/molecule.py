"""
Molecule data model and operations.
Provides a clean API for working with molecule data in the database.
"""

import logging
from ..cache import cached, invalidate_cache

logger = logging.getLogger(__name__)

class MoleculeModel:
    """
    Model for working with molecule data.
    Provides a higher-level API than the raw database adapter.
    """

    def __init__(self, db_adapter):
        """
        Initialize the molecule model.

        Args:
            db_adapter: DatabaseAdapter instance
        """
        self.db = db_adapter

    @cached("molecule:id", ttl=3600)  # Cache for 1 hour
    def get(self, molecule_id):
        """
        Get a molecule by ID.

        Args:
            molecule_id (int): Molecule ID

        Returns:
            dict: Molecule data or None if not found
        """
        with self.db.transaction():
            return self.db.get_molecule(molecule_id)

    @cached("molecule:details", ttl=3600)
    def get_by_details(self, name, charge=0, multiplicity=1, is_harmonium=False, omega=None):
        """
        Get a molecule by its details.

        Args:
            name (str): Molecule name
            charge (int): Molecular charge
            multiplicity (int): Spin multiplicity
            is_harmonium (bool): Whether this is a harmonium molecule
            omega (float): Omega parameter for harmonium

        Returns:
            int: Molecule ID or None if not found
        """
        with self.db.transaction():
            return self.db.get_molecule_by_details(name, charge, multiplicity, is_harmonium, omega)

    def add(self, name, charge=0, multiplicity=1, is_harmonium=False, omega=None, formula=None):
        """
        Add a molecule or get existing ID.

        Args:
            name (str): Molecule name
            charge (int): Molecular charge
            multiplicity (int): Spin multiplicity
            is_harmonium (bool): Whether this is a harmonium molecule
            omega (float): Omega parameter for harmonium
            formula (str): Molecular formula

        Returns:
            int: Molecule ID
        """
        with self.db.transaction():
            molecule_id = self.db.add_molecule(name, charge, multiplicity, is_harmonium, omega, formula)

            # Invalidate cache for this molecule
            invalidate_cache("molecule:details", name, charge, multiplicity, int(is_harmonium), omega)

            return molecule_id

    def add_from_object(self, molecule):
        """
        Add a molecule from a Molecule object.

        Args:
            molecule: Molecule object with appropriate attributes

        Returns:
            int: Molecule ID
        """
        # Extract properties from the molecule object
        name = getattr(molecule, 'name', '').lower()
        charge = getattr(molecule, 'charge', 0)
        multiplicity = getattr(molecule, 'multiplicity', 1)
        is_harmonium = getattr(molecule, 'is_harmonium', False)
        omega = getattr(molecule, 'omega', None) if is_harmonium else None
        formula = getattr(molecule, 'formula', None)

        return self.add(name, charge, multiplicity, is_harmonium, omega, formula)

    def find_or_create(self, name, charge=0, multiplicity=1, is_harmonium=False, omega=None, formula=None):
        """
        Find a molecule by details or create it if not found.

        Args:
            name (str): Molecule name
            charge (int): Molecular charge
            multiplicity (int): Spin multiplicity
            is_harmonium (bool): Whether this is a harmonium molecule
            omega (float): Omega parameter for harmonium
            formula (str): Molecular formula

        Returns:
            tuple: (molecule_id, created) where created is a boolean
        """
        molecule_id = self.get_by_details(name, charge, multiplicity, is_harmonium, omega)

        if molecule_id:
            return molecule_id, False

        # Molecule doesn't exist, create it
        molecule_id = self.add(name, charge, multiplicity, is_harmonium, omega, formula)
        return molecule_id, True