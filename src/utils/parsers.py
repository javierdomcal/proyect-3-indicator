import re


def parse_gaussian_log(log_input, is_content=False):
    """
    Parse Gaussian log file for energies, timing, and optimized geometry.

    Args:
        log_input (str): Either the file path or the content of the log file
        is_content (bool): If True, log_input is treated as file content rather than a path
    """
    data = {
        "hf_energy": None,
        "cpu_time": None,
        "elapsed_time": None,
        "normal_termination": False,
        "optimization_status": None,
        "optimized_geometry": [],
        "atomic_numbers": [],
        "atomic_symbols": [],
    }

    patterns = {
        "hf": re.compile(r"HF=(-?\d+\.\d+)"),
        "cpu": re.compile(r"Job cpu time:\s+(\d+ days\s+ \d+ hours\s+ \d+ minutes\s+ \d+\.\d+ seconds\.)"),
        "elapsed": re.compile(r"Elapsed time:\s+(\d+ days\s+ \d+ hours\s+ \d+ minutes\s+ \d+\.\d+ seconds\.)"),
        "termination": re.compile(r"Normal termination"),
        "opt_start": re.compile(r"Standard orientation:"),
        "opt_end": re.compile(r" Rotational constants "),
    }

    if is_content:
        lines = log_input.splitlines()
    else:
        with open(log_input, "r") as file:
            lines = file.readlines()

    reading_geometry = False
    geometry_lines = []
    last_geometry = []

    for i, line in enumerate(lines):
        # Extract basic info
        for key, pattern in patterns.items():
            if pattern.search(line):
                if key == "hf":
                    data["hf_energy"] = float(pattern.search(line).group(1))
                elif key in ["cpu", "elapsed"]:
                    data[f"{key}_time"] = pattern.search(line).group(1)
                elif key == "termination":
                    data["normal_termination"] = True

        # Extract geometry
        if patterns["opt_start"].search(line):
            reading_geometry = True
            geometry_lines = []
            continue

        if reading_geometry:
            if patterns["opt_end"].search(line):
                reading_geometry = False
                last_geometry = geometry_lines.copy()
                continue

            if len(line.split()) == 6 and line.split()[0].isdigit():
                atom_data = line.split()
                geometry_lines.append({
                    "atomic_number": int(atom_data[1]),
                    "symbol": get_atomic_symbol(int(atom_data[1])),
                    "coordinates": [float(x) for x in atom_data[3:]]
                })

    if last_geometry:
        data["optimized_geometry"] = last_geometry
        data["atomic_numbers"] = [atom["atomic_number"] for atom in last_geometry]
        data["atomic_symbols"] = [atom["symbol"] for atom in last_geometry]
        data["optimization_status"] = "Completed" if data["normal_termination"] else "Failed"

    return data


def get_atomic_symbol(atomic_number):
    """Convert atomic number to symbol."""
    symbols = {
        0: "X", 1: "H", 2: "He", 3: "Li", 4: "Be", 5: "B", 6: "C", 7: "N", 8: "O", 9: "F",
        10: "Ne", 11: "Na", 12: "Mg", 13: "Al", 14: "Si", 15: "P", 16: "S", 17: "Cl", 18: "Ar",
        19: "K", 20: "Ca", 21: "Sc", 22: "Ti", 23: "V", 24: "Cr", 25: "Mn", 26: "Fe", 27: "Co",
        28: "Ni", 29: "Cu", 30: "Zn", 31: "Ga", 32: "Ge", 33: "As", 34: "Se", 35: "Br", 36: "Kr",
        37: "Rb", 38: "Sr", 39: "Y", 40: "Zr", 41: "Nb", 42: "Mo", 43: "Tc", 44: "Ru", 45: "Rh",
        46: "Pd", 47: "Ag", 48: "Cd", 49: "In", 50: "Sn", 51: "Sb", 52: "Te", 53: "I", 54: "Xe",
        55: "Cs", 56: "Ba", 57: "La", 58: "Ce", 59: "Pr", 60: "Nd", 61: "Pm", 62: "Sm", 63: "Eu",
        64: "Gd", 65: "Tb", 66: "Dy", 67: "Ho", 68: "Er", 69: "Tm", 70: "Yb", 71: "Lu", 72: "Hf",
        73: "Ta", 74: "W", 75: "Re", 76: "Os", 77: "Ir", 78: "Pt", 79: "Au", 80: "Hg", 81: "Tl",
        82: "Pb", 83: "Bi", 84: "Po", 85: "At", 86: "Rn", 87: "Fr", 88: "Ra", 89: "Ac", 90: "Th",
        91: "Pa", 92: "U", 93: "Np", 94: "Pu", 95: "Am", 96: "Cm", 97: "Bk", 98: "Cf", 99: "Es",
        100: "Fm", 101: "Md", 102: "No", 103: "Lr", 104: "Rf", 105: "Db", 106: "Sg", 107: "Bh",
        108: "Hs", 109: "Mt", 110: "Ds", 111: "Rg", 112: "Cn", 113: "Nh", 114: "Fl", 115: "Mc",
        116: "Lv", 117: "Ts", 118: "Og",
    }
    return symbols.get(atomic_number, str(atomic_number))


if __name__ == "__main__":
    # Test the parser with a sample Gaussian log file
    test_log_content = """
 HF=-76.12345
 Job cpu time:     0 days  0 hours  1 minutes 30.0 seconds.
 Elapsed time:     0 days  0 hours  0 minutes 45.2 seconds.
 Standard orientation:
     1          8           0        0.000000    0.000000    0.000000
     2          1           0        0.000000    0.000000    1.000000
 Rotational constants (GHZ):
 Normal termination
    """
    
    try:
        # Test parsing from content
        print("Testing log parsing from content:")
        result = parse_gaussian_log(test_log_content, is_content=True)
        print("\nParsed data:")
        for key, value in result.items():
            print(f"{key}: {value}")
            
        # Test atomic symbol conversion
        print("\nTesting atomic symbol conversion:")
        test_numbers = [1, 8, 26, 92]
        for num in test_numbers:
            symbol = get_atomic_symbol(num)
            print(f"Atomic number {num} -> Symbol {symbol}")
            
    except Exception as e:
        print(f"Test failed: {e}")