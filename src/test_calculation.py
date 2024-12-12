import os
from gaussian_input_generator import GaussianInputGenerator
from molecule import Molecule
from method import Method
from basis import BasisSet

def create_test_calculations():
    # Define test directory paths
    local_test_dir = "test"

    # Ensure local test directory exists
    os.makedirs(local_test_dir, exist_ok=True)

    # Test Case 1: Single-point energy calculation
    hydrogen_atom = Molecule(name="hydrogen_atom", charge=0, multiplicity=2)
    hf_method = Method("HF")
    sto3g_basis = BasisSet("sto-3g")

    sp_generator = GaussianInputGenerator(
        config="SP", molecule=hydrogen_atom, method=hf_method, basis=sto3g_basis, title="Hydrogen Atom Calculation"
    )
    sp_file = os.path.join(local_test_dir, "hydrogen_sp.com")
    sp_generator.generate_input_file(sp_file)


    print(f"Generated test file:\n- {sp_file}")


if __name__ == "__main__":
    create_test_calculations()
