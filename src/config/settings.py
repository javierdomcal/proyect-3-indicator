import os
from pathlib import Path

# Project root directory (assuming we're in src/config/settings.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Only the paths needed for molecules.py
UTILS_DIR = os.path.join(PROJECT_ROOT, "utils")
MOLECULES_DIR = os.path.join(UTILS_DIR, "molecules")

# Ensure directories exist
os.makedirs(MOLECULES_DIR, exist_ok=True)

if __name__ == "__main__":
    print("Testing settings.py configuration:")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Utils Directory: {UTILS_DIR}")
    print(f"Molecules Directory: {MOLECULES_DIR}")