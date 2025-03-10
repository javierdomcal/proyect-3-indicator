# src/input/methods.py

import re


class Method:
    def __init__(self, method_name):
        """
        Initializes a Method instance.

        Parameters:
        - method_name (str): Name of the calculation method, which can be standard (e.g., HF, MP2)
          or CASSCF with parameters in the format "CASSCF[n,m]".
        """
        self.method_name = method_name
        self.is_casscf = method_name.lower().startswith("casscf")
        self.is_fullci = method_name.lower().startswith("fullci")
        self.method_keywords = ""

        # Extract n and m if method is CASSCF with parameters
        if self.is_casscf:
            match = re.match(r"CASSCF\((\d+),(\d+)\)", method_name, re.IGNORECASE)
            if not match:
                raise ValueError(
                    "CASSCF method requires parameters in the format 'CASSCF[n,m]'."
                )
            self.n = int(match.group(1))
            self.m = int(match.group(2))
            self.method_keywords = "density=current iop(5/33=1) "  # iop(4/21=100) '
            if self.m >= 10:
                self.method_keywords += "iop(4/21=100) "
        else:
            self.n = None
            self.m = None
            self.method_keywords = "density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 "

    def __str__(self):
        """
        Returns a string representation of the method.
        """
        return f"{self.method_name}"


if __name__ == "__main__":
    print("Testing Method class...")

    # Test 1: HF method
    print("\nHF method test:")
    hf_method = Method("HF")
    print(hf_method)

    # Test 2: MP2 method
    print("\nMP2 method test:")
    mp2_method = Method("MP2")
    print(mp2_method)

    # Test 3: CASSCF method with parameters
    print("\nCASSCF method test (with parameters):")
    casscf_method = Method("CASSCF(4,2)")
    print(casscf_method)

    # Test 4: Invalid CASSCF format
    print("\nInvalid CASSCF format test:")
    try:
        invalid_casscf = Method("CASSCF(4)")
    except ValueError as e:
        print(f"Error: {e}")

    # Test 5: CASSCF method with m >= 10
    print("\nCASSCF method test (m >= 10):")
    casscf_large_m = Method("CASSCF(10,12)")
    print(casscf_large_m)
