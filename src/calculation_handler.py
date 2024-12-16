# src/calculation_handler.py
import re
from pathlib import Path

from .registry.calculation_registry import CalculationRegistry
from .molecule import Molecule
from .method import Method
from .basis import BasisSet
from .cluster_connection import ClusterConnection
from .file_management import FileManager
from .job_manager import JobManager
from .slurm_manager import SlurmManager
from .flux_correlation_indicator import FluxCorrelationIndicator


class CalculationHandler:
    def __init__(self, config_file="utils/cluster_config.json"):
        """Initialize calculation handler with registry."""
        self.config_file = config_file
        self.registry = CalculationRegistry()

    def _generate_job_name(
        self, molecule_name: str, method_name: str, basis_name: str
    ) -> str:
        """Generate standardized job name."""
        match = re.search(r"\(([^,]+),\s*([^)]+)\)", method_name)
        if not match:
            raise ValueError(f"Invalid method name format: {method_name}")

        part1, part2 = match.group(1).strip(), match.group(2).strip()
        return f"{molecule_name[:2]}{part1}{part2}{basis_name.replace('-','')}"

    def _handle_single_calculation(
        self,
        molecule_name: str,
        method_name: str,
        basis_name: str,
        connection: ClusterConnection,
    ) -> pd.DataFrame:
        """Handle a single calculation with registry check."""
        # Check if calculation exists
        calc_id, result_path, status = self.registry.check_calculation_exists(
            molecule_name, method_name, basis_name
        )

        # If completed calculation exists, retrieve results
        if status == "completed" and result_path:
            file_manager = FileManager(connection)
            try:
                return file_manager.get_results(result_path)
            except Exception as e:
                print(f"Warning: Could not retrieve existing results: {e}")
                # Continue to new calculation

        # Set up new calculation
        molecule = Molecule(name=molecule_name)
        method = Method(method_name)
        basis = BasisSet(basis_name)

        # Register new calculation if needed
        if not calc_id:
            calc_id = self.registry.register_calculation(
                molecule_name, method_name, basis_name
            )

        # Set up managers
        file_manager = FileManager(connection)
        job_manager = JobManager(connection, file_manager, SlurmManager())
        flux_manager = FluxCorrelationIndicator(connection, file_manager, job_manager)

        # Generate job name and execute
        job_name = self._generate_job_name(molecule_name, method_name, basis_name)

        try:
            # Update status to running
            self.registry.update_calculation_status(calc_id, "running")

            # Execute calculation
            flux_manager.handle_flux(job_name, molecule, method, basis)

            # Get results
            result_df = file_manager.get_results(job_name)

            # Update registry with success
            self.registry.update_calculation_status(
                calc_id,
                "completed",
                job_name,  # result path
                f"/dipc/javidom/proyect-3-indicator/{job_name}",  # colony dir
            )

            return result_df

        except Exception as e:
            # Update registry with failure
            self.registry.update_calculation_status(calc_id, "failed")
            raise RuntimeError(f"Calculation failed: {e}")

    def run_calculations(
        self, molecule_name: str, method_name: str, basis_list: List[str]
    ) -> List[pd.DataFrame]:
        """
        Run calculations for a molecule with different basis sets.

        Args:
            molecule_name: Name of the molecule
            method_name: Calculation method
            basis_list: List of basis sets to use

        Returns:
            List of DataFrames containing results
        """
        results = []

        with ClusterConnection(config_file=self.config_file) as connection:
            for basis_name in basis_list:
                try:
                    result = self._handle_single_calculation(
                        molecule_name, method_name, basis_name, connection
                    )
                    results.append(result)
                except Exception as e:
                    print(f"Error calculating {basis_name}: {e}")
                    continue

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
