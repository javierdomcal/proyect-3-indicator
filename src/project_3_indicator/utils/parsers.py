import re
import logging
def get_atomic_number(symbol):
    """
    Convert atomic symbol to atomic number.

    Args:
        symbol (str): Atomic symbol (e.g., 'H', 'He', 'C')

    Returns:
        int: Atomic number corresponding to the symbol
    """
    # Dictionary mapping atomic symbols to atomic numbers
    atomic_numbers = {
        'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10,
        'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20,
        'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30,
        'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40,
        'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50,
        'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60,
        'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70,
        'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80,
        'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90,
        'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100,
        'Md': 101, 'No': 102, 'Lr': 103, 'Rf': 104, 'Db': 105, 'Sg': 106, 'Bh': 107, 'Hs': 108, 'Mt': 109,
        'Ds': 110, 'Rg': 111, 'Cn': 112, 'Nh': 113, 'Fl': 114, 'Mc': 115, 'Lv': 116, 'Ts': 117, 'Og': 118
    }

    # Handle case sensitivity by converting the first letter to uppercase and rest to lowercase
    if symbol and len(symbol) > 0:
        formatted_symbol = symbol[0].upper() + symbol[1:].lower() if len(symbol) > 1 else symbol.upper()

        if formatted_symbol in atomic_numbers:
            return atomic_numbers[formatted_symbol]

    # Return 0 for unrecognized symbols (could alternatively raise an exception)
    return 0

def get_atomic_symbol(atomic_number):
    """Convert atomic number to symbol."""
    symbols = {
        0: "X", 1: "H", 2: "He", 3: "Li", 4: "Be", 5: "B", 6: "C", 7: "N", 8: "O", 9: "F",
        10: "Ne", 11: "Na", 12: "Mg", 13: "Al", 14: "Si", 15: "P", 16: "S", 17: "Cl", 18: "Ar",
        # ... [rest of symbols remain the same]
    }
    return symbols.get(atomic_number, str(atomic_number))

def extract_geometry_from_log(log_content, is_content=False):
    """
    Extract geometry from Gaussian log file content.

    Args:
        log_content: Either file path or content string
        is_content: Boolean indicating if log_content is actual content (True) or file path (False)

    Returns:
        dict containing:
            geometry: List of dictionaries with atomic info and coordinates
            atomic_numbers: List of atomic numbers
            atomic_symbols: List of atomic symbols
            is_optimized: Boolean indicating if geometry is from optimization
    """
    patterns = {
        "geometry_start": re.compile(r"\s*(?:Input|Standard)\s+orientation:\s*"),
        "geometry_end": re.compile(r"\s*-{3,}\s*$"),
        "geometry_header": re.compile(r" Center     Atomic      Atomic"),
        "opt_found": re.compile(r"Stationary point found")
    }

    lines = log_content.splitlines() if is_content else open(log_content, "r").readlines()
    reading_geometry = False
    header_found = False
    geometry_lines = []
    final_geometry = []
    is_optimized = False

    try:
        for line in lines:
            # Check for optimization completion
            if patterns["opt_found"].search(line):
                is_optimized = True
                final_geometry = geometry_lines.copy()

            # Geometry parsing
            if patterns["geometry_start"].search(line):
                reading_geometry = True
                header_found = False
                geometry_lines = []
                continue

            if reading_geometry:
                if patterns["geometry_header"].search(line):
                    header_found = True
                    continue

                if patterns["geometry_end"].search(line):
                    reading_geometry = False
                    continue

                if header_found and line.strip():
                    try:
                        fields = line.strip().split()
                        if len(fields) >= 6 and fields[0].isdigit():
                            atomic_num = int(fields[1])
                            coords = [float(x) for x in fields[3:6]]
                            geometry_lines.append({
                                "atomic_number": atomic_num,
                                "symbol": get_atomic_symbol(atomic_num),
                                "coordinates": coords
                            })
                    except (ValueError, IndexError) as e:
                        logging.warning(f"Error parsing geometry line: {line} - {str(e)}")
                        continue

    except Exception as e:
        logging.error(f"Error extracting geometry: {str(e)}")
        return {
            "geometry": [],
            "atomic_numbers": [],
            "atomic_symbols": [],
            "is_optimized": False
        }

    # Use final geometry from optimization if available, otherwise use last geometry found
    geometry = final_geometry if final_geometry else geometry_lines

    if not geometry:
        return {
            "geometry": [],
            "atomic_numbers": [],
            "atomic_symbols": [],
            "is_optimized": False
        }

    # Extract atomic numbers and symbols lists
    atomic_numbers = [atom["atomic_number"] for atom in geometry]
    atomic_symbols = [atom["symbol"] for atom in geometry]

    return {
        "geometry": geometry,
        "atomic_numbers": atomic_numbers,
        "atomic_symbols": atomic_symbols,
        "is_optimized": is_optimized
    }

def parse_gaussian_log(log_input, is_content=False):
    """Parse Gaussian log file for energies, timing, geometry and completion status."""
    data = {
        "energies": {},
        "cpu_time": None,
        "elapsed_time": None,
        "normal_termination": False,
    }

    if not log_input or not log_input.strip():
        logging.warning("Empty log file content")
        return data

    patterns = {
        "scf": re.compile(r"SCF Done:.+?=\s+(-?\d+\.\d+)"),
        "hf": re.compile(r"HF=(-?\d+\.\d+)"),
        "mp2": re.compile(r"EUMP2.+?=\s+(-?\d+\.\d+)"),
        "casscf": re.compile(r"ECASSCF.+?=\s+(-?\d+\.\d+)"),
        "cpu": re.compile(r"Job cpu time:\s+(\d+ days\s+\d+ hours\s+\d+ minutes\s+\d+\.\d+ seconds\.)"),
        "elapsed": re.compile(r"Elapsed time:\s+(\d+ days\s+\d+ hours\s+\d+ minutes\s+\d+\.\d+ seconds\.)"),
        "termination": re.compile(r"Normal termination"),
    }

    lines = log_input.splitlines() if is_content else open(log_input, "r").readlines()

    try:
        for line in lines:
            # Energy and timing patterns
            for key, pattern in patterns.items():
                match = pattern.search(line)
                if match:
                    if key in ["scf", "hf", "mp2", "casscf"]:
                        data["energies"][key] = float(match.group(1))
                    elif key == "cpu":
                        data["cpu_time"] = match.group(1)
                    elif key == "elapsed":
                        data["elapsed_time"] = match.group(1)
                    elif key == "termination":
                        data["normal_termination"] = True

    except Exception as e:
        logging.error(f"Error parsing log file: {str(e)}")
        return data

    # Get geometry information
    geometry_data = extract_geometry_from_log(log_input, is_content)
    data.update(geometry_data)

    return data

if __name__ == "__main__":
    # Test the parsing functions
    test_log = """
     SCF Done:  E(RHF) =  -7.86144688888     A.U.
     Job cpu time:  0 days  0 hours  1 minutes 30.0 seconds.
     Elapsed time:  0 days  0 hours  0 minutes 45.2 seconds.
     Standard orientation:
     Center     Atomic      Atomic             Coordinates (Angstroms)
        Number    Number     Type             X           Y           Z
     ---------------------------------------------------------------------
          1          2          0        0.000000    0.000000    0.000000
     ---------------------------------------------------------------------
     Normal termination
    """

    # Test geometry extraction
    print("\nTesting geometry extraction:")
    geometry_result = extract_geometry_from_log(test_log, is_content=True)
    print("Geometry data:", geometry_result)

    # Test full parsing
    print("\nTesting full log parsing:")
    result = parse_gaussian_log(test_log, is_content=True)
    print("\nParsed data:")
    for key, value in result.items():
        print(f"{key}: {value}")