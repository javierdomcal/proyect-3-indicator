import sqlite3
from pathlib import Path
from contextlib import contextmanager
from ..config.settings import REGISTRY_FILE

class DatabaseConnection:
    def __init__(self, db_path=REGISTRY_FILE):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS molecules (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    omega REAL,
                    charge INTEGER DEFAULT 0,
                    multiplicity INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS methods (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    n_electrons INTEGER,
                    m_orbitals INTEGER,
                    excited_state INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS basis_sets (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS scanning_properties (
                    id INTEGER PRIMARY KEY,
                    atom_indices TEXT,
                    directions TEXT,
                    end_distance REAL DEFAULT 1.0,
                    step_size REAL DEFAULT 0.05
                );

                CREATE TABLE IF NOT EXISTS calculations (
                    id TEXT PRIMARY KEY,
                    molecule_id INTEGER NOT NULL,
                    method_id INTEGER NOT NULL,
                    basis_id INTEGER NOT NULL,
                    scanning_props_id INTEGER,
                    status TEXT NOT NULL,
                    config TEXT DEFAULT 'SP',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP,
                    message TEXT,
                    results_path TEXT,
                    FOREIGN KEY (molecule_id) REFERENCES molecules(id),
                    FOREIGN KEY (method_id) REFERENCES methods(id),
                    FOREIGN KEY (basis_id) REFERENCES basis_sets(id),
                    FOREIGN KEY (scanning_props_id) REFERENCES scanning_properties(id)
                );

                CREATE TABLE IF NOT EXISTS calculation_results (
                    id INTEGER PRIMARY KEY,
                    calculation_id TEXT NOT NULL,
                    energy REAL,
                    calculation_time TEXT,
                    geometry TEXT,
                    ontop_data TEXT,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (calculation_id) REFERENCES calculations(id)
                );

            """)

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()