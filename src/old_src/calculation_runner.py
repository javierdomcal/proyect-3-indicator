from pathlib import Path
from input_specification import InputSpecification
from molecule import Molecule
from method import Method
from basis import BasisSet
from cluster_connection import ClusterConnection
from file_management import FileManager
from job_manager import JobManager
from slurm_manager import SlurmManager
from flux_correlation_indicator import FluxCorrelationIndicator
from registry.calculation_registry import CalculationRegistry


class CalculationRunner:
    def __init__(self, config_file="utils/cluster_config.json"):
        self.config_file = config_file
        self.registry = CalculationRegistry()

    def run_ontop_calculation_analysis(self, molecule_name, method_name, basis_sets):
        results = []

        with ClusterConnection(config_file=self.config_file) as connection:
            file_manager = FileManager(connection)
            job_manager = JobManager(connection, file_manager, SlurmManager())
            flux_manager = FluxCorrelationIndicator(
                connection, file_manager, job_manager
            )

            for basis_name in basis_sets:
                # Create input specification
                input_spec = InputSpecification(
                    molecule=Molecule(name=molecule_name),
                    method=Method(method_name),
                    basis=BasisSet(basis_name),
                    title=molecule_name,
                    config="SP",
                )

                # Check if calculation exists
                calc_id, colony_dir = self.registry.check_calculation_exists(input_spec)

                if colony_dir:
                    # Calculation exists, get results
                    df = file_manager.get_results(colony_dir)
                    results.append(df)
                    continue

                # Need to run new calculation
                job_name = f"{molecule_name[:2]}{method_name.split('(')[1].split(',')[0]}{method_name.split(',')[1].strip(')').strip()}{basis_name.replace('-','')}"

                # Run calculation
                flux_manager.handle_flux(
                    job_name, input_spec.molecule, input_spec.method, input_spec.basis
                )

                # Register the calculation
                colony_dir = f"/dipc/javidom/proyect-3-indicator/{job_name}"
                self.registry.register_calculation(input_spec, colony_dir)

                # Get results
                df = file_manager.get_results(job_name)
                results.append(df)

        return results


# ... (previous code remains the same)

if __name__ == "__main__":
    # Simple test of calculation runner
    runner = CalculationRunner()

    # Test parameters
    test_params = {
        "molecule_name": "helium",
        "method_name": "HF",
        "basis_sets": ["sto-3g"],
    }

    print("Running test calculation...")
    try:
        results = runner.run_ontop_calculation_analysis(**test_params)
        print("Calculation successful!")
        print(f"Number of results: {len(results)}")
        if results:
            print("First result head:")
            print(results[0].head())
    except Exception as e:
        print(f"Error in calculation: {e}")
