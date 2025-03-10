from datetime import datetime
from pathlib import Path
from .connection import DatabaseConnection
from .models import (
    DBMolecule, DBMethod, DBBasisSet, DBScanningProperties,
    DBCalculation, DBCalculationResults
)
from ..input.molecules import Molecule
from ..input.methods import Method
from ..input.basis import BasisSet
from ..input.scanning import ScanningProperties

class DatabaseOperations:
    def __init__(self):
        self.db = DatabaseConnection()

    def get_or_insert_molecule(self, molecule):
        with self.db.get_connection() as conn:
            # First try to find existing molecule
            cursor = conn.execute("""
                SELECT id FROM molecules
                WHERE name = ? AND (omega IS NULL AND ? IS NULL OR omega = ?) AND charge = ? AND multiplicity = ?
            """, (
                molecule.name,
                molecule.omega, molecule.omega,
                molecule.charge,
                molecule.multiplicity
            ))
            existing = cursor.fetchone()
            if existing:
                return existing[0]

            # If not found, insert new one
            cursor.execute("""
                INSERT INTO molecules (name, omega, charge, multiplicity)
                VALUES (?, ?, ?, ?)
                """, (
                    molecule.name,
                    molecule.omega,
                    molecule.charge,
                    molecule.multiplicity
                )
            )
            conn.commit()
            return cursor.lastrowid

    def get_or_insert_method(self, method):
        with self.db.get_connection() as conn:
            # First try to find existing method
            cursor = conn.execute("""
                SELECT id FROM methods
                WHERE name = ? AND (n_electrons IS NULL AND ? IS NULL OR n_electrons = ?) AND (m_orbitals IS NULL AND ? IS NULL OR m_orbitals = ?)AND (excited_state IS NULL AND ? IS NULL OR excited_state = ?)
            """, (
                method.method_name,
                getattr(method, 'n', None),getattr(method, 'n', None),
                getattr(method, 'm', None),getattr(method, 'm', None),
                getattr(method, 'excited_state', None),getattr(method, 'excited_state', None)

            ))
            existing = cursor.fetchone()
            if existing:
                return existing[0]

            # If not found, insert new one
            cursor.execute("""
                INSERT INTO methods (name, n_electrons, m_orbitals, excited_state)
                VALUES (?, ?, ?, ?)
                """, (
                    method.method_name,
                    getattr(method, 'n', None),
                    getattr(method, 'm', None),
                    getattr(method, 'excited_state', None)
                )
            )
            conn.commit()
            return cursor.lastrowid

    def get_or_insert_basis(self, basis):
        with self.db.get_connection() as conn:
            # First try to find existing basis
            cursor = conn.execute("""
                SELECT id FROM basis_sets
                WHERE name = ?
            """, (
                basis.basis_name,
            ))
            existing = cursor.fetchone()
            if existing:
                return existing[0]

            # If not found, insert new one
            cursor.execute("""
                INSERT INTO basis_sets (name)
                VALUES (?)
                """, (
                    basis.basis_name,
                )
            )
            conn.commit()
            return cursor.lastrowid


    def get_or_insert_scanning_props(self, scanning_props):
        """Get existing or insert new scanning properties."""


        with self.db.get_connection() as conn:
            # First try to find existing scanning properties for this molecule
            cursor = conn.execute("""
                SELECT id FROM scanning_properties
                WHERE atom_indices = ?
                AND directions = ?
                AND end_distance = ?
                AND step_size = ?
            """, (
                scanning_props.atom_indices,  # Default to empty string if None
                scanning_props.directions,
                scanning_props.end_distance,
                scanning_props.step_size
            ))
            existing = cursor.fetchone()
            if existing:
                return existing[0]

            # If not found, insert new one
            cursor.execute("""
                INSERT INTO scanning_properties
                (atom_indices, directions, end_distance, step_size)
                VALUES (?, ?, ?, ?)
                """, (
                    scanning_props.atom_indices,
                    scanning_props.directions,
                    scanning_props.end_distance,
                    scanning_props.step_size
                )
            )
            conn.commit()
            return cursor.lastrowid


    def register_calculation(self, input_spec):
        with self.db.get_connection() as conn:
            # Get next calculation ID
            cursor = conn.execute("SELECT COUNT(*) FROM calculations")
            count = cursor.fetchone()[0]
            calc_id = f"CALC_{count+1:06d}"

            # Insert components
            molecule_id = self.get_or_insert_molecule(input_spec.molecule)
            method_id = self.get_or_insert_method(input_spec.method)
            basis_id = self.get_or_insert_basis(input_spec.basis)
            scanning_props_id = self.get_or_insert_scanning_props(input_spec.scanning_props)



            # Insert calculation
            conn.execute("""
                INSERT INTO calculations
                (id, molecule_id, method_id, basis_id, scanning_props_id, status, config)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    calc_id,
                    molecule_id,
                    method_id,
                    basis_id,
                    scanning_props_id,
                    "registered",
                    input_spec.config
                )
            )
            conn.commit()
            return calc_id

    def update_calculation_status(self, calc_id, status, message=None):
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE calculations
                SET status = ?, message = ?, last_updated = ?
                WHERE id = ?
                """, (status, message, datetime.now().isoformat(), calc_id)
            )
            conn.commit()

    def get_calculation_info(self, calc_id):
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT c.*, m.name as molecule_name, mt.name as method_name,
                    b.name as basis_name, m.omega,
                    m.charge, m.multiplicity,
                    mt.n_electrons, mt.m_orbitals, mt.excited_state,
                    sp.atom_indices, sp.directions, sp.end_distance, sp.step_size
                FROM calculations c
                JOIN molecules m ON c.molecule_id = m.id
                JOIN methods mt ON c.method_id = mt.id
                JOIN basis_sets b ON c.basis_id = b.id
                LEFT JOIN scanning_properties sp ON c.scanning_props_id = sp.id
                WHERE c.id = ?
            """, (calc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_calculation_info_by_input_spec(self, input_spec):
        """
        Get calculation info from database based on InputSpecification.
        Args:
            input_spec (InputSpecification): Complete input specification for the calculation
        Returns:
            dict: Calculation info if found, None otherwise
        """
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT c.*, m.name as molecule_name, mt.name as method_name,
                    b.name as basis_name, m.omega,
                    m.charge, m.multiplicity,
                    mt.n_electrons, mt.m_orbitals,  mt.excited_state,
                    sp.atom_indices, sp.directions, sp.end_distance, sp.step_size
                FROM calculations c
                JOIN molecules m ON c.molecule_id = m.id
                JOIN methods mt ON c.method_id = mt.id
                JOIN basis_sets b ON c.basis_id = b.id
                LEFT JOIN scanning_properties sp ON c.scanning_props_id = sp.id
                WHERE m.name = ?
                AND mt.name = ?
                AND b.name = ?
                AND c.config = ?
                AND m.charge = ?
                AND m.multiplicity = ?
                AND (m.omega IS NULL AND ? IS NULL OR m.omega = ?)
                AND (mt.n_electrons IS NULL AND ? IS NULL OR mt.n_electrons = ?)
                AND (mt.m_orbitals IS NULL AND ? IS NULL OR mt.m_orbitals = ?)
                AND (mt.excited_state IS NULL AND ? IS NULL OR mt.excited_state = ?)
                AND c.status = 'completed'
                ORDER BY c.created_at DESC
                LIMIT 1
            """, (
                input_spec.molecule.name,
                input_spec.method.method_name,
                input_spec.basis.basis_name,
                input_spec.config,
                input_spec.molecule.charge,
                input_spec.molecule.multiplicity,
                getattr(input_spec.molecule, 'omega', None), getattr(input_spec.molecule, 'omega', None),
                getattr(input_spec.method, 'n', None), getattr(input_spec.method, 'n', None),
                getattr(input_spec.method, 'm', None), getattr(input_spec.method, 'm', None),
                getattr(input_spec.method, 'excited_state', None), getattr(input_spec.method, 'excited_state', None)
            ))
            row = cursor.fetchone()
            return dict(row) if row else None