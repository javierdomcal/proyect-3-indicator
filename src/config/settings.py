import os
from pathlib import Path

# Project root directory (assuming we're in src/config/settings.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Utility directories
UTILS_DIR = os.path.join(PROJECT_ROOT, "utils")
MOLECULES_DIR = os.path.join(UTILS_DIR, "molecules")
BASIS_SETS_DIR = os.path.join(UTILS_DIR, "basis_sets")

# Configuration files
CLUSTER_CONFIG = os.path.join(UTILS_DIR, "cluster_config.json")

# Working directories
SLURM_DIR = os.path.join(PROJECT_ROOT, "slurm_scripts")
TEST_DIR = os.path.join(PROJECT_ROOT, "test")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

# Ensure all directories exist
for directory in [UTILS_DIR, MOLECULES_DIR, BASIS_SETS_DIR, SLURM_DIR, TEST_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

if __name__ == "__main__":
    print("Testing settings.py configuration:")
    print(f"Project Root: {PROJECT_ROOT}")
    print("\nUtility Directories:")
    print(f"Utils Directory: {UTILS_DIR}")
    print(f"Molecules Directory: {MOLECULES_DIR}")
    print(f"Basis Sets Directory: {BASIS_SETS_DIR}")
    print(f"\nConfiguration Files:")
    print(f"Cluster Config: {CLUSTER_CONFIG}")
    print(f"\nWorking Directories:")
    print(f"SLURM Directory: {SLURM_DIR}")
    print(f"Test Directory: {TEST_DIR}")
    print(f"Log Directory: {LOG_DIR}")