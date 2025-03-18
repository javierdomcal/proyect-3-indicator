"""
Configuration settings for file and directory locations.

This module defines the file structure for the project, including locations of
input files, where results should be stored, and configuration files.
"""

import os
from pathlib import Path

# Allow overriding the project root with an environment variable
PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", "/home/javi/Desktop/Doctorado/proyect-3-indicator"))

# Main directories
UTILS_DIR = PROJECT_ROOT / "utils"
SRC_DIR = PROJECT_ROOT / "src"
RESULTS_DIR = PROJECT_ROOT / "results"
LOG_DIR = PROJECT_ROOT / "logs"
TEST_DIR = PROJECT_ROOT / "test"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# Utility subdirectories
MOLECULES_DIR = UTILS_DIR / "molecules"
BASIS_SETS_DIR = UTILS_DIR / "basis_sets"

# Working directories
SLURM_DIR = PROJECT_ROOT / "slurm_scripts"

# Storage directories
STORAGE_DIR = UTILS_DIR / "storage"
METADATA_DIR = STORAGE_DIR
REGISTRY_DIR = UTILS_DIR
STATUS_DIR = STORAGE_DIR

# Configuration files
CLUSTER_CONFIG = UTILS_DIR / "cluster_config.json"

# Important files
REGISTRY_FILE = REGISTRY_DIR / "registry.db"
METADATA_FILE = METADATA_DIR / "metadata.json"
STATUS_FILE = STATUS_DIR / "status.json"

# Dictionary with all directories for easy access
DIRECTORIES = {
    "project_root": PROJECT_ROOT,
    "utils": UTILS_DIR,
    "src": SRC_DIR,
    "results": RESULTS_DIR,
    "logs": LOG_DIR,
    "tests": TEST_DIR,
    "notebooks": NOTEBOOKS_DIR,
    "molecules": MOLECULES_DIR,
    "basis_sets": BASIS_SETS_DIR,
    "slurm": SLURM_DIR,
    "storage": STORAGE_DIR,
    "metadata": METADATA_DIR,
    "registry": REGISTRY_DIR,
    "status": STATUS_DIR,
}

def ensure_directories_exist():
    """Create all required directories if they don't exist yet."""
    for directory in DIRECTORIES.values():
        directory.mkdir(parents=True, exist_ok=True)

    # Log successful directory creation
    print(f"Created project directory structure in {PROJECT_ROOT}")
    return True

# Only create directories when explicitly requested or when module is run directly
if __name__ == "__main__":
    ensure_directories_exist()
    print("Testing settings.py configuration:")
    print(f"Project Root: {PROJECT_ROOT}")

    for name, path in DIRECTORIES.items():
        print(f"{name}: {path}")
        print(f"  - Exists: {path.exists()}")