"""
Database schema definition for the computational chemistry project.
This module handles the creation and maintenance of the database structure.
"""

import sqlite3
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Default database location in user's home directory
DEFAULT_DB_PATH = os.path.join(str(Path.home()), ".chem_calculations", "calculations.db")

def get_db_path():
    """Get the database path from environment or use default"""
    return os.environ.get("CHEM_DB_PATH", DEFAULT_DB_PATH)

def ensure_db_directory():
    """Ensure the database directory exists"""
    db_path = get_db_path()
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        logger.info(f"Created database directory: {db_dir}")
    return db_path

def create_schema(conn):
    """
    Create the database schema if it doesn't exist.

    Args:
        conn: SQLite connection
    """
    cursor = conn.cursor()

    # Create molecules table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS molecules (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        charge INTEGER DEFAULT 0,
        multiplicity INTEGER DEFAULT 1,
        is_harmonium INTEGER DEFAULT 0,
        omega REAL DEFAULT NULL,
        formula TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(name, charge, multiplicity, is_harmonium, omega)
    )
    ''')

    # Create calculations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS calculations (
        id INTEGER PRIMARY KEY,
        molecule_id INTEGER,
        basis_set TEXT,
        method TEXT,
        config_type TEXT DEFAULT 'SP',
        grid_hash TEXT DEFAULT NULL,
        status TEXT DEFAULT 'pending',
        error_message TEXT DEFAULT NULL,
        start_time DATETIME DEFAULT NULL,
        end_time DATETIME DEFAULT NULL,
        code_version TEXT DEFAULT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (molecule_id) REFERENCES molecules (id)
    )
    ''')

    # Create properties table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS properties (
        id INTEGER PRIMARY KEY,
        calculation_id INTEGER,
        property_name TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        property_data TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (calculation_id) REFERENCES calculations (id),
        UNIQUE(calculation_id, property_name)
    )
    ''')

    # Create tags table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY,
        calculation_id INTEGER,
        tag TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (calculation_id) REFERENCES calculations (id),
        UNIQUE(calculation_id, tag)
    )
    ''')

    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_calculations_molecule ON calculations(molecule_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_properties_calculation ON properties(calculation_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_calculation ON tags(calculation_id)')

    conn.commit()
    logger.info("Database schema created or verified")

def init_db():
    """Initialize the database schema"""
    db_path = ensure_db_directory()

    try:
        conn = sqlite3.connect(db_path)
        create_schema(conn)
        logger.info(f"Database initialized at {db_path}")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Set up logging when run directly
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Initialize the database
    success = init_db()
    print(f"Database initialization {'successful' if success else 'failed'}")