"""
Database adapter for the computational chemistry project.
This is the main interface to the database for the application.
"""

import sqlite3
import json
import logging
import time
import hashlib
import datetime
import threading
from contextlib import contextmanager
from .connection import get_db_connection
from .schema import init_db

logger = logging.getLogger(__name__)

class DatabaseAdapter:
    """
    Main adapter class for database operations.
    Provides a clean API for the application to interact with the database.
    """

    def __init__(self):
        """Initialize the database adapter"""
        # Ensure database is initialized
        init_db()
        # Thread-local storage for transaction state
        self._local = threading.local()

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        Supports nested transactions using SQLite savepoints.

        Usage:
            with db_adapter.transaction():
                db_adapter.add_molecule(...)
                db_adapter.add_calculation(...)
        """
        # Initialize transaction depth counter
        self._local.in_transaction = getattr(self._local, 'in_transaction', 0) + 1
        transaction_depth = self._local.in_transaction

        # Get a connection for this transaction
        with get_db_connection() as conn:
            # If this is the outermost transaction, store the connection
            if transaction_depth == 1:
                self._local.conn = conn

            try:
                # For outermost transaction, use BEGIN
                # For nested transactions, use savepoints
                if transaction_depth == 1:
                    conn.execute("BEGIN")
                    logger.debug("Starting transaction")
                else:
                    savepoint_name = f"sp_{transaction_depth}"
                    conn.execute(f"SAVEPOINT {savepoint_name}")
                    logger.debug(f"Creating savepoint {savepoint_name}")

                # Yield control back to the with block
                yield

                # For outermost transaction, commit
                # For nested transactions, release savepoint
                if transaction_depth == 1:
                    conn.commit()
                    logger.debug("Transaction committed")
                else:
                    savepoint_name = f"sp_{transaction_depth}"
                    conn.execute(f"RELEASE {savepoint_name}")
                    logger.debug(f"Released savepoint {savepoint_name}")

            except Exception as e:
                # On error, rollback the transaction or savepoint
                if transaction_depth == 1:
                    try:
                        conn.rollback()
                        logger.debug(f"Transaction rolled back due to error: {str(e)}")
                    except:
                        pass
                else:
                    try:
                        savepoint_name = f"sp_{transaction_depth}"
                        conn.execute(f"ROLLBACK TO {savepoint_name}")
                        logger.debug(f"Rolled back to savepoint {savepoint_name} due to error: {str(e)}")
                    except:
                        pass
                raise
            finally:
                # Clean up transaction state
                self._local.in_transaction -= 1
                if self._local.in_transaction == 0:
                    if hasattr(self._local, 'conn'):
                        delattr(self._local, 'conn')

    def get_connection(self):
        """Get the current transaction connection or a new one"""
        if getattr(self._local, 'in_transaction', 0) > 0 and hasattr(self._local, 'conn'):
            return self._local.conn
        else:
            raise ValueError("Not in a transaction - use 'with db_adapter.transaction():' to start one")

    def _get_current_timestamp(self):
        """Get current timestamp in SQLite format"""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _calculate_grid_hash(self, grid):
        """Calculate a hash for grid parameters"""
        if not grid:
            return None

        # Convert grid parameters to string and hash them
        try:
            grid_str = f"{grid.x[0]}:{grid.x[1]}:{grid.y[0]}:{grid.y[1]}:{grid.z[0]}:{grid.z[1]}"
            return hashlib.md5(grid_str.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"Could not calculate grid hash: {str(e)}")
            return None

    # ========== Molecule Operations ==========

    def add_molecule(self, name, charge=0, multiplicity=1, is_harmonium=False, omega=None, formula=None):
        """
        Add a molecule to the database or get its ID if it exists.

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
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # First check if molecule exists
            cursor.execute(
                """SELECT id FROM molecules
                WHERE name=? AND charge=? AND multiplicity=? AND is_harmonium=? AND
                  (omega IS NULL AND ? IS NULL OR omega=?)""",
                (name, charge, multiplicity, int(is_harmonium), omega, omega)
            )
            existing = cursor.fetchone()

            if existing:
                molecule_id = existing[0]
                logger.debug(f"Found existing molecule: {name} (id: {molecule_id})")
                return molecule_id

            # Add new molecule
            cursor.execute(
                """INSERT INTO molecules
                (name, charge, multiplicity, is_harmonium, omega, formula)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (name, charge, multiplicity, int(is_harmonium), omega, formula)
            )

            molecule_id = cursor.lastrowid
            logger.info(f"Added new molecule: {name} (id: {molecule_id})")
            return molecule_id

        except Exception as e:
            logger.error(f"Error adding molecule {name}: {str(e)}")
            raise

    def get_molecule(self, molecule_id):
        """
        Get molecule details by ID.

        Args:
            molecule_id (int): Molecule ID

        Returns:
            dict: Molecule details or None if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT id, name, charge, multiplicity, is_harmonium, omega, formula FROM molecules WHERE id=?",
                (molecule_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "id": row[0],
                "name": row[1],
                "charge": row[2],
                "multiplicity": row[3],
                "is_harmonium": bool(row[4]),
                "omega": row[5],
                "formula": row[6]
            }

        except Exception as e:
            logger.error(f"Error getting molecule {molecule_id}: {str(e)}")
            raise

    def get_molecule_by_details(self, name, charge=0, multiplicity=1, is_harmonium=False, omega=None):
        """
        Get molecule ID by details.

        Args:
            name (str): Molecule name
            charge (int): Molecular charge
            multiplicity (int): Spin multiplicity
            is_harmonium (bool): Whether this is a harmonium molecule
            omega (float): Omega parameter for harmonium

        Returns:
            int: Molecule ID or None if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """SELECT id FROM molecules
                WHERE name=? AND charge=? AND multiplicity=? AND is_harmonium=? AND
                  (omega IS NULL AND ? IS NULL OR omega=?)""",
                (name, charge, multiplicity, int(is_harmonium), omega, omega)
            )
            row = cursor.fetchone()

            return row[0] if row else None

        except Exception as e:
            logger.error(f"Error finding molecule {name}: {str(e)}")
            raise

    # ========== Calculation Operations ==========

    def add_calculation(self, molecule_id, basis_set, method, config_type='SP', grid=None, code_version=None):
        """
        Add a calculation to the database.

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
        conn = self.get_connection()
        cursor = conn.cursor()

        grid_hash = self._calculate_grid_hash(grid)

        try:
            # Check if calculation already exists
            cursor.execute(
                """SELECT id FROM calculations
                WHERE molecule_id=? AND basis_set=? AND method=? AND config_type=? AND
                  (grid_hash IS NULL AND ? IS NULL OR grid_hash=?)""",
                (molecule_id, basis_set, method, config_type, grid_hash, grid_hash)
            )
            existing = cursor.fetchone()

            if existing:
                calc_id = existing[0]
                logger.debug(f"Found existing calculation (id: {calc_id})")
                return calc_id

            # Add new calculation
            cursor.execute(
                """INSERT INTO calculations
                (molecule_id, basis_set, method, config_type, grid_hash, code_version,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
                (molecule_id, basis_set, method, config_type, grid_hash, code_version,
                 self._get_current_timestamp())
            )

            calc_id = cursor.lastrowid
            logger.info(f"Added new calculation (id: {calc_id})")
            return calc_id

        except Exception as e:
            logger.error(f"Error adding calculation: {str(e)}")
            raise

    def update_calculation_status(self, calc_id, status, error_message=None):
        """
        Update the status of a calculation.

        Args:
            calc_id (int): Calculation ID
            status (str): New status (pending/running/completed/failed)
            error_message (str): Error message (if status is failed)

        Returns:
            bool: Success
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Update timestamps based on status
            timestamp_updates = {}
            if status == 'running':
                timestamp_updates['start_time'] = self._get_current_timestamp()
            elif status in ('completed', 'failed'):
                timestamp_updates['end_time'] = self._get_current_timestamp()

            # Build update query dynamically based on fields to update
            update_fields = ['status = ?']
            params = [status]

            if error_message is not None:
                update_fields.append('error_message = ?')
                params.append(error_message)

            for field, value in timestamp_updates.items():
                update_fields.append(f'{field} = ?')
                params.append(value)

            # Add calculation ID to params
            params.append(calc_id)

            # Execute update
            cursor.execute(
                f"UPDATE calculations SET {', '.join(update_fields)} WHERE id = ?",
                params
            )

            conn.commit()
            logger.info(f"Updated calculation {calc_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating calculation {calc_id}: {str(e)}")
            raise

    def get_calculation(self, calc_id):
        """
        Get calculation details by ID.

        Args:
            calc_id (int): Calculation ID

        Returns:
            dict: Calculation details or None if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """SELECT c.id, c.molecule_id, c.basis_set, c.method, c.config_type,
                   c.grid_hash, c.status, c.error_message, c.start_time, c.end_time,
                   c.code_version, m.name, m.charge, m.multiplicity, m.is_harmonium, m.omega
                FROM calculations c
                JOIN molecules m ON c.molecule_id = m.id
                WHERE c.id = ?""",
                (calc_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            result = {
                "id": row[0],
                "molecule_id": row[1],
                "basis_set": row[2],
                "method": row[3],
                "config_type": row[4],
                "grid_hash": row[5],
                "status": row[6],
                "error_message": row[7],
                "start_time": row[8],
                "end_time": row[9],
                "code_version": row[10],
                "molecule_name": row[11],
                "molecule_charge": row[12],
                "molecule_multiplicity": row[13],
                "is_harmonium": bool(row[14]),
                "omega": row[15],
                "elapsed_time": None
            }

            # Calculate elapsed time if we have both start and end time
            if row[8] and row[9]:
                start = datetime.datetime.strptime(row[8], "%Y-%m-%d %H:%M:%S")
                end = datetime.datetime.strptime(row[9], "%Y-%m-%d %H:%M:%S")
                result["elapsed_time"] = str(end - start)

            return result

        except Exception as e:
            logger.error(f"Error getting calculation {calc_id}: {str(e)}")
            raise

    def find_calculation(self, molecule_id, basis_set, method, config_type='SP', grid=None):
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
        conn = self.get_connection()
        cursor = conn.cursor()

        grid_hash = self._calculate_grid_hash(grid)

        try:
            cursor.execute(
                """SELECT id FROM calculations
                WHERE molecule_id=? AND basis_set=? AND method=? AND config_type=? AND
                  (grid_hash IS NULL AND ? IS NULL OR grid_hash=?)""",
                (molecule_id, basis_set, method, config_type, grid_hash, grid_hash)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self.get_calculation(row[0])

        except Exception as e:
            logger.error(f"Error finding calculation: {str(e)}")
            raise

    # ========== Property Operations ==========

    def add_properties(self, calc_id, property_names):
        """
        Add properties to track for a calculation.

        Args:
            calc_id (int): Calculation ID
            property_names (list): List of property names to add

        Returns:
            bool: Success
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        timestamp = self._get_current_timestamp()

        try:
            for prop_name in property_names:
                cursor.execute(
                    """INSERT OR IGNORE INTO properties
                    (calculation_id, property_name, completed, created_at, updated_at)
                    VALUES (?, ?, 0, ?, ?)""",
                    (calc_id, prop_name, timestamp, timestamp)
                )

            logger.info(f"Added {len(property_names)} properties to calculation {calc_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding properties to calculation {calc_id}: {str(e)}")
            raise

    def get_property(self, calc_id, property_name):
        """
        Get a property for a calculation.

        Args:
            calc_id (int): Calculation ID
            property_name (str): Property name

        Returns:
            dict: Property details or None if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """SELECT id, property_name, completed, property_data, updated_at
                FROM properties
                WHERE calculation_id=? AND property_name=?""",
                (calc_id, property_name)
            )
            row = cursor.fetchone()

            if not row:
                return None

            result = {
                "id": row[0],
                "property_name": row[1],
                "completed": bool(row[2]),
                "updated_at": row[4]
            }

            # Parse property data if it exists
            if row[3]:
                try:
                    result["data"] = json.loads(row[3])
                except json.JSONDecodeError:
                    result["data"] = row[3]
            else:
                result["data"] = None

            return result

        except Exception as e:
            logger.error(f"Error getting property {property_name} for calculation {calc_id}: {str(e)}")
            raise

    def store_property_result(self, calc_id, property_name, property_data):
        """
        Store a property result.

        Args:
            calc_id (int): Calculation ID
            property_name (str): Property name
            property_data: Property data (will be serialized to JSON if not a string)

        Returns:
            bool: Success
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Serialize data if needed
        if not isinstance(property_data, str):
            property_data = json.dumps(property_data)

        try:
            # Check if property exists
            cursor.execute(
                "SELECT id FROM properties WHERE calculation_id=? AND property_name=?",
                (calc_id, property_name)
            )
            existing = cursor.fetchone()

            timestamp = self._get_current_timestamp()

            if existing:
                # Update existing property
                cursor.execute(
                    """UPDATE properties
                    SET completed=1, property_data=?, updated_at=?
                    WHERE calculation_id=? AND property_name=?""",
                    (property_data, timestamp, calc_id, property_name)
                )
            else:
                # Insert new property
                cursor.execute(
                    """INSERT INTO properties
                    (calculation_id, property_name, completed, property_data, created_at, updated_at)
                    VALUES (?, ?, 1, ?, ?, ?)""",
                    (calc_id, property_name, property_data, timestamp, timestamp)
                )

            logger.info(f"Stored result for property {property_name} of calculation {calc_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing property {property_name} for calculation {calc_id}: {str(e)}")
            raise

    def get_missing_properties(self, calc_id, requested_props):
        """
        Get a list of properties that need to be calculated.

        Args:
            calc_id (int): Calculation ID
            requested_props (list): List of requested property names

        Returns:
            list: List of property names that need to be calculated
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        missing = []
        try:
            for prop in requested_props:
                cursor.execute(
                    """SELECT completed FROM properties
                    WHERE calculation_id=? AND property_name=?""",
                    (calc_id, prop)
                )
                row = cursor.fetchone()

                if not row or not row[0]:
                    missing.append(prop)

            return missing

        except Exception as e:
            logger.error(f"Error checking missing properties for calculation {calc_id}: {str(e)}")
            raise

    # ========== Tag Operations ==========

    def add_tag(self, calc_id, tag):
        """
        Add a tag to a calculation.

        Args:
            calc_id (int): Calculation ID
            tag (str): Tag to add

        Returns:
            bool: Success
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """INSERT OR IGNORE INTO tags
                (calculation_id, tag)
                VALUES (?, ?)""",
                (calc_id, tag)
            )

            logger.debug(f"Added tag '{tag}' to calculation {calc_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding tag '{tag}' to calculation {calc_id}: {str(e)}")
            raise

    def get_tags(self, calc_id):
        """
        Get all tags for a calculation.

        Args:
            calc_id (int): Calculation ID

        Returns:
            list: List of tags
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT tag FROM tags WHERE calculation_id=?",
                (calc_id,)
            )

            return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error getting tags for calculation {calc_id}: {str(e)}")
            raise

    def find_calculations_by_tag(self, tag):
        """
        Find calculations with a specific tag.

        Args:
            tag (str): Tag to search for

        Returns:
            list: List of calculation IDs
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """SELECT c.id
                FROM calculations c
                JOIN tags t ON c.id = t.calculation_id
                WHERE t.tag=?""",
                (tag,)
            )

            return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error finding calculations with tag '{tag}': {str(e)}")
            raise