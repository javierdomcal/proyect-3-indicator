"""
Handles analysis of flux calculation results.
"""

import logging
import numpy as np
from datetime import datetime


class FluxAnalyzer:
    def __init__(self):
        """Initialize flux analyzer."""
        self.analyses = {}

    def analyze_ontop_data(self, job_name, data):
        """
        Analyze ontop.dat file data from INCA calculation.

        Args:
            job_name: Name of the job
            data: Content of ontop.dat file

        Returns:
            dict: Analysis results including statistical measures
        """
        try:
            # Convert content to numpy array
            rows = [line.split() for line in data.strip().split("\n")]
            values = np.array(rows, dtype=float)

            # Calculate basic statistics
            analysis = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "median": float(np.median(values)),
                "shape": values.shape,
                "non_zero": int(np.count_nonzero(values)),
                "timestamp": datetime.now().isoformat(),
            }

            # Add additional correlation metrics
            analysis.update(
                {
                    "correlation_strength": self._evaluate_correlation_strength(values),
                    "spatial_distribution": self._analyze_spatial_distribution(values),
                    "significant_regions": self._find_significant_regions(values),
                }
            )

            # Store analysis
            self.analyses[job_name] = analysis

            return analysis

        except Exception as e:
            logging.error(f"Error analyzing ontop data for {job_name}: {e}")
            raise

    def _evaluate_correlation_strength(self, values):
        """Evaluate overall correlation strength from values."""
        try:
            # Calculate relative to some threshold
            threshold = np.mean(values) + np.std(values)
            strong_correlations = np.sum(values > threshold)

            return {
                "strong_count": int(strong_correlations),
                "strong_percentage": float(strong_correlations / values.size * 100),
                "threshold": float(threshold),
            }
        except Exception as e:
            logging.error(f"Error evaluating correlation strength: {e}")
            return {}

    def _analyze_spatial_distribution(self, values):
        """Analyze spatial distribution of correlation values."""
        try:
            # Analyze value distribution in different regions
            quartiles = np.percentile(values, [25, 50, 75])

            return {
                "quartiles": quartiles.tolist(),
                "skewness": float(
                    np.mean(((values - np.mean(values)) / np.std(values)) ** 3)
                ),
                "kurtosis": float(
                    np.mean(((values - np.mean(values)) / np.std(values)) ** 4)
                ),
            }
        except Exception as e:
            logging.error(f"Error analyzing spatial distribution: {e}")
            return {}

    def _find_significant_regions(self, values):
        """Find regions with significant correlation values."""
        try:
            # Identify regions with high correlation
            threshold = np.mean(values) + 2 * np.std(values)
            significant_mask = values > threshold

            return {
                "count": int(np.sum(significant_mask)),
                "threshold": float(threshold),
                "percentage": float(np.sum(significant_mask) / values.size * 100),
            }
        except Exception as e:
            logging.error(f"Error finding significant regions: {e}")
            return {}

    def analyze_correlation_flux(self, job_name, flux_results):
        """
        Analyze complete correlation flux results.

        Args:
            job_name: Name of the job
            flux_results: Dictionary containing results from each calculation

        Returns:
            dict: Complete analysis of the correlation flux
        """
        try:
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "job_name": job_name,
                "calculations": {},
            }

            # Analyze Gaussian results
            if "GaussianCalculation" in flux_results:
                gaussian_results = flux_results["GaussianCalculation"]
                analysis["calculations"]["gaussian"] = {
                    "hf_energy": gaussian_results.get("hf_energy"),
                    "normal_termination": gaussian_results.get("normal_termination"),
                    "elapsed_time": gaussian_results.get("elapsed_time"),
                    "optimization_status": gaussian_results.get("optimization_status"),
                }

            # Record DMN completion
            if "DMNCalculation" in flux_results:
                dmn_results = flux_results["DMNCalculation"]
                analysis["calculations"]["dmn"] = {
                    "status": dmn_results.get("status"),
                    "output_files": dmn_results.get("output_files", []),
                }

            # Record DM2PRIM completion
            if "DM2PRIMCalculation" in flux_results:
                dm2prim_results = flux_results["DM2PRIMCalculation"]
                analysis["calculations"]["dm2prim"] = {
                    "status": dm2prim_results.get("status"),
                    "output_files": dm2prim_results.get("output_files", []),
                }

            # Analyze INCA results
            if "INCACalculation" in flux_results:
                inca_results = flux_results["INCACalculation"]
                if "content" in inca_results:
                    ontop_analysis = self.analyze_ontop_data(
                        job_name, inca_results["content"]
                    )
                    analysis["calculations"]["inca"] = {
                        "status": inca_results.get("status"),
                        "ontop_analysis": ontop_analysis,
                    }

            # Calculate overall success
            analysis["overall_success"] = all(
                calc.get("status") == "completed"
                for calc in analysis["calculations"].values()
                if "status" in calc
            )

            # Store complete analysis
            self.analyses[job_name] = analysis

            return analysis

        except Exception as e:
            logging.error(f"Error analyzing correlation flux for {job_name}: {e}")
            raise

    def get_analysis(self, job_name):
        """Retrieve stored analysis for a job."""
        if job_name not in self.analyses:
            logging.warning(f"No analysis found for job {job_name}")
            return None
        return self.analyses[job_name]

    def get_all_analyses(self):
        """Get all stored analyses."""
        return self.analyses

    def clear_analyses(self):
        """Clear all stored analyses."""
        self.analyses = {}
        logging.info("Cleared all stored analyses")


if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from utils.log_config import setup_logging
    from cluster.connection import ClusterConnection
    from cluster.transfer import FileTransfer
    from jobs.manager import JobManager
    from cluster.cleanup import ClusterCleanup
    from input.molecules import Molecule
    from input.methods import Method
    from input.basis import BasisSet
    from input.specification import InputSpecification
    from flux.correlation import CorrelationFlux

    # Setup logging
    setup_logging(verbose_level=2)

    try:
        with ClusterConnection() as connection:
            # Initialize components
            file_manager = FileTransfer(connection)
            job_manager = JobManager(connection, file_manager)
            cleanup = ClusterCleanup(connection)

            # Initialize flux manager and analyzer
            flux_manager = CorrelationFlux(connection, file_manager, job_manager)
            analyzer = FluxAnalyzer()

            # Test setup
            test_name = "analyzer_test"
            molecule = Molecule(name="helium", multiplicity=1)
            method = Method("CISD")
            basis = BasisSet("sto-3g")

            # Create input specification
            input_spec = InputSpecification(
                molecule=molecule,
                method=method,
                basis=basis,
                title=test_name,
                config="SP",
                input_type="gaussian",
            )

            # Run correlation flux
            print("\nRunning correlation flux...")
            flux_results = flux_manager.handle_correlation_flux(test_name, input_spec)

            # Analyze results
            print("\nAnalyzing flux results...")
            analysis = analyzer.analyze_correlation_flux(test_name, flux_results)

            # Print analysis
            print("\nFlux Analysis:")
            for key, value in analysis.items():
                if key != "calculations":
                    print(f"\n{key}: {value}")
                else:
                    print("\nCalculations:")
                    for calc_name, calc_results in value.items():
                        print(f"\n  {calc_name}:")
                        for k, v in calc_results.items():
                            print(f"    {k}: {v}")

            # Clean up
            print("\nCleaning up...")
            cleanup.clean_calculation(test_name)

    except Exception as e:
        print(f"Test failed: {e}")
        try:
            cleanup.clean_calculation(test_name)
        except:
            pass
