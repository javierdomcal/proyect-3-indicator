"""
Tracks status and progress of flux calculations.
"""

import os
import json
import logging
from datetime import datetime


class RegistryTracker:
    """Manages tracking of calculation status and progress."""

    STATUS_FILE = os.path.join("utils", "storage", "status.json")
    METADATA_FILE = os.path.join("utils", "storage", "metadata.json")

    VALID_STATUSES = [
        "pending",  # Not yet started
        "running",  # Currently executing
        "completed",  # Successfully completed
        "failed",  # Failed to complete
        "interrupted",  # Stopped mid-execution
    ]

    def __init__(self):
        """Initialize tracker and ensure storage exists."""
        os.makedirs(os.path.dirname(self.STATUS_FILE), exist_ok=True)
        os.makedirs(os.path.dirname(self.METADATA_FILE), exist_ok=True)

    def update_status(self, hash_str, status, message=None):
        """Update status of a calculation."""
        try:
            if status not in self.VALID_STATUSES:
                raise ValueError(f"Invalid status: {status}")

            # Load current status file
            current_status = {}
            if os.path.exists(self.STATUS_FILE):
                with open(self.STATUS_FILE, "r") as f:
                    current_status = json.load(f)

            # Update status
            current_status[hash_str] = {
                "status": status,
                "message": message,
                "last_updated": datetime.now().isoformat(),
                "history": current_status.get(hash_str, {}).get("history", [])
                + [
                    {
                        "status": status,
                        "message": message,
                        "timestamp": datetime.now().isoformat(),
                    }
                ],
            }

            # Save updated status
            with open(self.STATUS_FILE, "w") as f:
                json.dump(current_status, f, indent=2, sort_keys=True)

            logging.info(f"Updated status for {hash_str} to {status}")

        except Exception as e:
            logging.error(f"Error updating status for {hash_str}: {e}")
            raise

    def get_status(self, hash_str):
        """Get current status of a calculation."""
        try:
            if not os.path.exists(self.STATUS_FILE):
                return None

            with open(self.STATUS_FILE, "r") as f:
                status_data = json.load(f)

            return status_data.get(hash_str)

        except Exception as e:
            logging.error(f"Error getting status for {hash_str}: {e}")
            raise

    def add_metadata(self, hash_str, key, value):
        """Add metadata for a calculation."""
        try:
            # Load current metadata
            metadata = {}
            if os.path.exists(self.METADATA_FILE):
                with open(self.METADATA_FILE, "r") as f:
                    metadata = json.load(f)

            # Initialize if new hash
            if hash_str not in metadata:
                metadata[hash_str] = {}

            # Update metadata
            metadata[hash_str][key] = {
                "value": value,
                "timestamp": datetime.now().isoformat(),
            }

            # Save updated metadata
            with open(self.METADATA_FILE, "w") as f:
                json.dump(metadata, f, indent=2, sort_keys=True)

            logging.info(f"Added metadata '{key}' for {hash_str}")

        except Exception as e:
            logging.error(f"Error adding metadata for {hash_str}: {e}")
            raise

    def get_metadata(self, hash_str, key=None):
        """Get metadata for a calculation."""
        try:
            if not os.path.exists(self.METADATA_FILE):
                return None

            with open(self.METADATA_FILE, "r") as f:
                metadata = json.load(f)

            if hash_str not in metadata:
                return None

            if key is None:
                return metadata[hash_str]

            return metadata[hash_str].get(key)

        except Exception as e:
            logging.error(f"Error getting metadata for {hash_str}: {e}")
            raise


if __name__ == "__main__":
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from utils.log_config import setup_logging
    from input.molecules import Molecule
    from input.methods import Method
    from input.basis import BasisSet
    from input.specification import InputSpecification
    from registry.hash import FluxHasher

    # Setup logging
    setup_logging(verbose_level=2)

    try:
        # Create test input specification
        molecule = Molecule(name="helium")
        method = Method("CASSCF(2,2)")
        basis = BasisSet("sto-3g")

        input_spec = InputSpecification(
            molecule=molecule, method=method, basis=basis, title="test", config="SP"
        )

        # Generate hash
        hash_str = FluxHasher.generate_flux_hash(input_spec)
        print(f"\nGenerated hash: {hash_str}")

        # Test status tracking
        tracker = RegistryTracker()

        print("\nTesting status updates...")
        tracker.update_status(hash_str, "pending", "Preparing calculation")
        print("Status after pending:", tracker.get_status(hash_str))

        tracker.update_status(hash_str, "running", "Executing calculation")
        print("Status after running:", tracker.get_status(hash_str))

        tracker.update_status(
            hash_str, "completed", "Calculation finished successfully"
        )
        print("Status after completed:", tracker.get_status(hash_str))

        print("\nTesting metadata...")
        tracker.add_metadata(hash_str, "runtime", "3600s")
        tracker.add_metadata(hash_str, "energy", "-76.12345")

        print("Metadata for calculation:")
        print(json.dumps(tracker.get_metadata(hash_str), indent=2))

    except Exception as e:
        print(f"Test failed: {e}")
