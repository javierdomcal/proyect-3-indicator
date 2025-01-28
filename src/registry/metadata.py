"""
Handles metadata management for flux calculations.
"""

import os
import json
import logging
from datetime import datetime


class MetadataManager:
    """Manages metadata for calculations."""

    METADATA_FILE = os.path.join("utils", "storage", "metadata.json")

    def __init__(self):
        """Initialize manager and ensure storage exists."""
        os.makedirs(os.path.dirname(self.METADATA_FILE), exist_ok=True)

    def add_metadata(self, hash_str, key, value):
        """Add or update metadata for a calculation."""
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

    def remove_metadata(self, hash_str, key=None):
        """Remove metadata for a calculation."""
        try:
            if not os.path.exists(self.METADATA_FILE):
                return

            with open(self.METADATA_FILE, "r") as f:
                metadata = json.load(f)

            if hash_str not in metadata:
                return

            if key is None:
                # Remove all metadata for this hash
                del metadata[hash_str]
            else:
                # Remove specific key
                if key in metadata[hash_str]:
                    del metadata[hash_str][key]

            # Save updated metadata
            with open(self.METADATA_FILE, "w") as f:
                json.dump(metadata, f, indent=2, sort_keys=True)

            logging.info(
                f"Removed metadata {'key ' + key if key else 'all'} for {hash_str}"
            )

        except Exception as e:
            logging.error(f"Error removing metadata for {hash_str}: {e}")
            raise

    def search_metadata(self, criteria):
        """
        Search for calculations matching metadata criteria.

        Args:
            criteria (dict): Dictionary of key-value pairs to match

        Returns:
            dict: Matching calculation hashes and their metadata
        """
        try:
            if not os.path.exists(self.METADATA_FILE):
                return {}

            with open(self.METADATA_FILE, "r") as f:
                metadata = json.load(f)

            matches = {}
            for hash_str, hash_metadata in metadata.items():
                match = all(
                    key in hash_metadata and hash_metadata[key]["value"] == value
                    for key, value in criteria.items()
                )
                if match:
                    matches[hash_str] = hash_metadata

            return matches

        except Exception as e:
            logging.error(f"Error searching metadata: {e}")
            raise


if __name__ == "__main__":
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from utils.log_config import setup_logging

    # Setup logging
    setup_logging(verbose_level=2)

    try:
        # Initialize manager
        manager = MetadataManager()

        # Test hash
        test_hash = "a1b2c3d4"

        print("\nTesting metadata operations...")
        # Add some metadata
        manager.add_metadata(test_hash, "runtime", "3600s")
        manager.add_metadata(test_hash, "energy", "-76.12345")
        manager.add_metadata(test_hash, "convergence", "achieved")

        # Get all metadata for hash
        print("\nAll metadata:")
        all_meta = manager.get_metadata(test_hash)
        print(json.dumps(all_meta, indent=2))

        # Get specific metadata
        print("\nSpecific metadata:")
        energy = manager.get_metadata(test_hash, "energy")
        print(f"Energy value: {energy['value']}")

        # Search metadata
        print("\nSearching metadata:")
        criteria = {"convergence": "achieved"}
        matches = manager.search_metadata(criteria)
        print("Matches:", json.dumps(matches, indent=2))

        # Remove specific metadata
        print("\nRemoving specific metadata...")
        manager.remove_metadata(test_hash, "runtime")
        print("After removing runtime:", manager.get_metadata(test_hash))

    except Exception as e:
        print(f"Test failed: {e}")
