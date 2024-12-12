import pytest
from unittest import mock
from molecule import Molecule

# 1. Pruebas para el constructor (inicialización)
def test_molecule_default_initialization():
    molecule = Molecule()
    assert molecule.name == "harmonium"
    assert molecule.omega == None
    assert molecule.charge == -2
    assert molecule.multiplicity == 1
    assert molecule.is_harmonium == True

def test_molecule_with_custom_name():
    molecule = Molecule(name="water")
    assert molecule.name == "water"
    assert molecule.omega == None
    assert molecule.charge == 0
    assert molecule.multiplicity == 1
    assert molecule.is_harmonium == False

def test_harmonium_molecule_initialization():
    molecule = Molecule(omega=0.5)
    assert molecule.name == "harmonium"
    assert molecule.omega == 0.5
    assert molecule.charge == -2
    assert molecule.multiplicity == 1
    assert molecule.is_harmonium == True

# 2. Mockeo del sistema de archivos para load_geometry
@mock.patch('os.path.exists', return_value=True)
@mock.patch('builtins.open', new_callable=mock.mock_open, read_data="3\nH2O H2O\nH 0 0 0\nO 1 1 1\nH 2 2 2\n")
def test_load_geometry(mock_open, mock_exists):
    molecule = Molecule(name="water")
    molecule.load_geometry()
    assert molecule.geometry == "H 0 0 0\nO 1 1 1\nH 2 2 2\n"
    assert molecule.formula == "H2O"

@mock.patch('os.path.exists', return_value=False)
def test_load_geometry_file_not_found(mock_exists):
    molecule = Molecule(name="water")
    molecule.load_geometry()
    assert molecule.geometry == None

# 3. Prueba para get_molecule_description
def test_get_molecule_description_harmonium():
    molecule = Molecule(omega=0.5)
    description = molecule.get_molecule_description()
    assert description == "harmonium_omega_0.5"

def test_get_molecule_description_non_harmonium():
    molecule = Molecule(name="water")
    description = molecule.get_molecule_description()
    assert description == "water"

# 4. Pruebas para convert_formula_to_latex
def test_convert_formula_to_latex():
    molecule = Molecule(name="water")
    molecule.formula = "H2O"
    latex_formula = molecule.convert_formula_to_latex()
    assert latex_formula == "H_\\{2\\}O"

def test_convert_formula_to_latex_complex():
    molecule = Molecule(name="ethanol")
    molecule.formula = "C2H5OH"
    latex_formula = molecule.convert_formula_to_latex()
    assert latex_formula == "C_\\{2\\}H_\\{5\\}OH"

# 5. Prueba para __str__
def test_str_representation_harmonium():
    molecule = Molecule(omega=0.5)
    assert str(molecule) == "Harmonium, Omega=0.5"

def test_str_representation_non_harmonium():
    molecule = Molecule(name="water")
    molecule.formula = "H2O"
    molecule.geometry = "H 0 0 0\nO 1 1 1\nH 2 2 2"
    expected_str = "Molecule: water (H2O), Charge=0, Multiplicity=1\nGeometry:\nH 0 0 0\nO 1 1 1\nH 2 2 2"
    assert str(molecule) == expected_str
