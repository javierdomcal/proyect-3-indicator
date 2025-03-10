import re
import logging

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

def parse_gaussian_log(log_input, is_content=False):
    """Parse Gaussian log file for energies, timing, geometry and completion status."""
    data = {
        "energies": {},
        "cpu_time": None,
        "elapsed_time": None,
        "normal_termination": False,
        "geometry": []
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
        "opt_found": re.compile(r"Stationary point found"),
        "geometry_start": re.compile(r"Input orientation:|Standard orientation:"),
        "geometry_end": re.compile(r" ----------------|Rotational constants"),
        "geometry_header": re.compile(r" Center     Atomic      Atomic")
    }

    lines = log_input.splitlines() if is_content else open(log_input, "r").readlines()
    reading_geometry = False
    header_found = False
    geometry_lines = []
    final_geometry = []

    try:
        for line in lines:
            # Energy and timing patterns
            for key, pattern in patterns.items():
                if key not in ["geometry_start", "geometry_end", "geometry_header"]:
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
                        elif key == "opt_found":
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
        logging.error(f"Error parsing log file: {str(e)}")
        return data

    if final_geometry:
        data["geometry"] = final_geometry
    elif geometry_lines:
        data["geometry"] = geometry_lines

    # Add atomic numbers and symbols lists
    if data["geometry"]:
        data["atomic_numbers"] = [atom["atomic_number"] for atom in data["geometry"]]
        data["atomic_symbols"] = [atom["symbol"] for atom in data["geometry"]]

    # Add optimization status
    data["optimization_status"] = "Optimized" if final_geometry else "Not optimized"

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

    result = parse_gaussian_log(test_log, is_content=True)
    print("\nParsed data:")
    for key, value in result.items():
        print(f"{key}: {value}")