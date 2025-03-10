"""
Project configuration settings.
"""
import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Utility directories
UTILS_DIR = PROJECT_ROOT / "utils"
MOLECULES_DIR = UTILS_DIR / "molecules"
BASIS_SETS_DIR = UTILS_DIR / "basis_sets"

# Registry files and directories
REGISTRY_FILE = UTILS_DIR / "registry.db"
RESULTS_DIR = PROJECT_ROOT / "results"

# Configuration files
CLUSTER_CONFIG = str(UTILS_DIR / "cluster_config.json")

# Working directories
SLURM_DIR = PROJECT_ROOT / "slurm_scripts"
TEST_DIR = PROJECT_ROOT / "test"
LOG_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
for directory in [UTILS_DIR, MOLECULES_DIR, BASIS_SETS_DIR, SLURM_DIR, TEST_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

if __name__ == "__main__":
    print(f"MOLECULES_DIR: {MOLECULES_DIR}")
    print(f"CLUSTER_CONFIG: {CLUSTER_CONFIG}")