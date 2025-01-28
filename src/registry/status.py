"""
Handles status tracking for flux calculations.
"""

import os
import json
import logging
from datetime import datetime


class StatusTracker:
    """Manages status tracking of calculations."""

    STATUS_FILE = os.path.join("utils", "storage", "status.json")

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

    def get_status_history(self, hash_str):
        """Get status history of a calculation."""
        status_data = self.get_status(hash_str)
        return status_data.get("history", []) if status_data else []

    def get_all_with_status(self, status):
        """Get all calculations with a specific status."""
        try:
            if status not in self.VALID_STATUSES:
                raise ValueError(f"Invalid status: {status}")

            if not os.path.exists(self.STATUS_FILE):
                return {}

            with open(self.STATUS_FILE, "r") as f:
                status_data = json.load(f)

            return {
                hash_str: data
                for hash_str, data in status_data.items()
                if data.get("status") == status
            }

        except Exception as e:
            logging.error(f"Error getting calculations with status {status}: {e}")
            raise


if __name__ == "__main__":
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from utils.log_config import setup_logging

    # Setup logging
    setup_logging(verbose_level=2)

    try:
        # Initialize tracker
        tracker = StatusTracker()

        # Test hash
        test_hash = "a1b2c3d4"

        print("\nTesting status updates...")
        # Test status progression
        tracker.update_status(test_hash, "pending", "Preparing calculation")
        print("Status after pending:", tracker.get_status(test_hash))

        tracker.update_status(test_hash, "running", "Executing calculation")
        print("Status after running:", tracker.get_status(test_hash))

        tracker.update_status(
            test_hash, "completed", "Calculation finished successfully"
        )
        print("Status after completed:", tracker.get_status(test_hash))

        # Get status history
        print("\nStatus history:")
        history = tracker.get_status_history(test_hash)
        for entry in history:
            print(f"  {entry['timestamp']}: {entry['status']} - {entry['message']}")

        # Test getting all completed calculations
        print("\nAll completed calculations:")
        completed = tracker.get_all_with_status("completed")
        print(json.dumps(completed, indent=2))

    except Exception as e:
        print(f"Test failed: {e}")
