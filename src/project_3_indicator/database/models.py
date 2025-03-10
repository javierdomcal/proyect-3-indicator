from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class DBMolecule:
    id: Optional[int]
    name: str
    omega: Optional[float]
    charge: int
    multiplicity: int
    geometry: Optional[str]
    created_at: datetime

@dataclass
class DBMethod:
    id: Optional[int]
    name: str
    n_electrons: Optional[int]
    m_orbitals: Optional[int]
    excited_state: Optional[int]  # Added field
    keywords: Optional[str]
    created_at: datetime

@dataclass
class DBBasisSet:
    id: Optional[int]
    name: str
    omega: Optional[float]
    is_even_tempered: bool
    is_imported: bool
    created_at: datetime

@dataclass
class DBScanningProperties:
    id: Optional[int]
    molecule_id: int
    atom_indices: Optional[str]
    directions: Optional[str]
    end_distance: float
    step_size: float

@dataclass
class DBCalculation:
    id: str
    molecule_id: int
    method_id: int
    basis_id: int
    scanning_props_id: Optional[int]
    status: str
    config: str
    created_at: datetime
    last_updated: Optional[datetime]
    message: Optional[str]
    results_path: Optional[str]

@dataclass
class DBCalculationResults:
    id: Optional[int]
    calculation_id: str
    energy: Optional[float]
    calculation_time: Optional[str]
    geometry: Optional[str]
    ontop_data: Optional[str]
    completed_at: Optional[datetime]