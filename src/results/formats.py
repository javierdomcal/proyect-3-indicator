"""
Defines standard formats for result files.
"""

import json
import logging
from datetime import datetime


class ResultsFormatter:
    """Handles formatting of calculation results."""

    def format_results(self, results):
        """
        Format calculation results into standard structure.

        Args:
            results: Raw calculation results

        Returns:
            Dictionary with standardized format
        """
        try:
            formatted = {
                "timestamp": datetime.now().isoformat(),
                "energy": {"total": results.get("hf_energy"), "units": "hartree"},
                "calculation": {
                    "success": results.get("normal_termination", False),
                    "optimization_status": results.get("optimization_status"),
                    "cpu_time": results.get("cpu_time"),
                    "elapsed_time": results.get("elapsed_time"),
                },
            }

            # Add geometry information if available
            if "optimized_geometry" in results:
                formatted["geometry"] = {
                    "atomic_numbers": results["atomic_numbers"],
                    "atomic_symbols": results["atomic_symbols"],
                    "coordinates": [
                        atom["coordinates"] for atom in results["optimized_geometry"]
                    ],
                }

            return formatted

        except Exception as e:
            logging.error(f"Error formatting results: {e}")
            raise

    def validate_details(self, details):
        """
        Validate details.json format.

        Args:
            details: Dictionary of calculation details

        Returns:
            bool: Whether format is valid
        """
        required_fields = {
            "molecule": ["name", "charge", "multiplicity"],
            "method": ["name"],
            "basis": ["name"],
            "config": None,
        }

        try:
            # Check all required sections exist
            for section, fields in required_fields.items():
                if section not in details:
                    return False

                # Check required fields in section
                if fields:
                    section_data = details[section]
                    if not all(field in section_data for field in fields):
                        return False

            return True

        except Exception as e:
            logging.error(f"Error validating details: {e}")
            return False

    def validate_results(self, results):
        """
        Validate results.json format.

        Args:
            results: Dictionary of calculation results

        Returns:
            bool: Whether format is valid
        """
        try:
            # Check required top-level fields
            required_fields = ["timestamp", "energy", "calculation"]
            if not all(field in results for field in required_fields):
                return False

            # Check energy section
            if not all(field in results["energy"] for field in ["total", "units"]):
                return False

            # Check calculation section
            calc_fields = ["success", "optimization_status", "cpu_time", "elapsed_time"]
            if not all(field in results["calculation"] for field in calc_fields):
                return False

            return True

        except Exception as e:
            logging.error(f"Error validating results: {e}")
            return False

    def validate_xyz(self, content):
        """
        Validate XYZ file format.

        Args:
            content: String content of XYZ file

        Returns:
            bool: Whether format is valid
        """
        try:
            lines = content.strip().split("\n")

            # Check minimum length (number of atoms + 2 header lines)
            if len(lines) < 3:
                return False

            # Check first line is number of atoms
            try:
                n_atoms = int(lines[0])
            except ValueError:
                return False

            # Check we have correct number of coordinate lines
            if len(lines) != n_atoms + 2:
                return False

            # Check each coordinate line has 4 fields (symbol + 3 coordinates)
            for line in lines[2:]:
                fields = line.split()
                if len(fields) != 4:
                    return False

                # Check coordinates are float-parseable
                try:
                    [float(x) for x in fields[1:]]
                except ValueError:
                    return False

            return True

        except Exception as e:
            logging.error(f"Error validating XYZ format: {e}")
            return False

    def validate_ontop(self, content):
        """
        Validate ontop.dat format.

        Args:
            content: String content of ontop.dat file

        Returns:
            bool: Whether format is valid
        """
        try:
            lines = content.strip().split("\n")

            # Check we have content
            if not lines:
                return False

            # Check all lines have same number of fields
            fields_per_line = len(lines[0].split())
            if not all(len(line.split()) == fields_per_line for line in lines):
                return False

            # Check all fields are float-parseable
            try:
                for line in lines:
                    [float(x) for x in line.split()]
                return True
            except ValueError:
                return False

        except Exception as e:
            logging.error(f"Error validating ontop format: {e}")
            return False


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    # Setup test data
    test_details_valid = {
        "molecule": {"name": "water", "charge": 0, "multiplicity": 1},
        "method": {"name": "HF"},
        "basis": {"name": "sto-3g"},
        "config": "Opt",
    }

    test_details_invalid = {
        "molecule": {"name": "water"},
        "method": {},
        "basis": {"name": "sto-3g"},
    }

    test_results_valid = {
        "hf_energy": -74.9659012345,
        "normal_termination": True,
        "optimization_status": "Optimized",
        "cpu_time": "0 days 0 hours 1 minutes 3.0 seconds",
        "elapsed_time": "0 days 0 hours 0 minutes 57.6 seconds",
        "optimized_geometry": [
            {"atomic_number": 8, "coordinates": [0.0, 0.0, 0.0]},
            {"atomic_number": 1, "coordinates": [0.0, -0.757, 0.587]},
            {"atomic_number": 1, "coordinates": [0.0, 0.757, 0.587]},
        ],
        "atomic_numbers": [8, 1, 1],
        "atomic_symbols": ["O", "H", "H"],
    }

    test_results_invalid = {
        "hf_energy": -74.9659012345,
        "normal_termination": True,
    }

    test_xyz_valid = """3
    water
    O        0.000000    0.000000    0.000000
    H        0.000000   -0.757000    0.587000
    H        0.000000    0.757000    0.587000
    """

    test_xyz_invalid = """3
    water
    O        0.000000    0.000000
    H        0.000000   -0.757000    0.587000
    H        0.000000    0.757000    0.587000
    """

    test_ontop_valid = """0.123 0.456 0.789
    0.234 0.567 0.890
    0.345 0.678 0.901
    """

    test_ontop_invalid = """0.123 0.456 0.789
    0.234 0.567
    0.345 0.678 0.901
    """

    # Initialize formatter
    formatter = ResultsFormatter()

    print("Testing details validation...")
    print("Valid details:", formatter.validate_details(test_details_valid))
    print("Invalid details:", formatter.validate_details(test_details_invalid))

    print("\nTesting results validation...")
    print("Valid results:", formatter.validate_results(test_results_valid))
    print("Invalid results:", formatter.validate_results(test_results_invalid))

    print("\nTesting XYZ validation...")
    print("Valid XYZ:", formatter.validate_xyz(test_xyz_valid))
    print("Invalid XYZ:", formatter.validate_xyz(test_xyz_invalid))

    print("\nTesting ontop validation...")
    print("Valid ontop:", formatter.validate_ontop(test_ontop_valid))
    print("Invalid ontop:", formatter.validate_ontop(test_ontop_invalid))

    print("\nTesting results formatting...")
    try:
        formatted = formatter.format_results(test_results_valid)
        print(json.dumps(formatted, indent=2))
    except Exception as e:
        logging.exception("Error in format_results")
