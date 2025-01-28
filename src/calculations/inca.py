"""
Handles INCA calculations.
"""

import os
import logging
from calculations.base import Calculation
from utils.generator import InputFileGenerator


class INCACalculation(Calculation):
    def prepare_input_files(self, job_name, input_spec):
        """Prepare input files for INCA calculation."""
        try:
            # Define cluster paths
            colony_dir = f"{self.connection.colony_dir}/{job_name}"

            # Generate INCA input file
            generator = InputFileGenerator(
                config="SP",
                molecule=input_spec.molecule,
                method=input_spec.method,
                basis=input_spec.basis,
                title=job_name,
                input_type="inca",
            )

            # Generate and upload input file
            input_dir = "test"
            os.makedirs(input_dir, exist_ok=True)
            inp_file = os.path.join(input_dir, f"{job_name}.inp")
            generator.generate_input_file()

            # Upload to colony
            self.file_manager.upload_file(inp_file, f"{colony_dir}/{job_name}.inp")

            # Generate and upload SLURM script
            scratch_dir = f"{self.connection.scratch_dir}/{job_name}"
            slurm_script = self.job_manager.submitter.generate_inca_script(
                job_name, scratch_dir
            )
            self.file_manager.upload_file(
                slurm_script, f"{colony_dir}/{job_name}_inca.slurm"
            )

            # Check required input files from previous calculations
            required_files = [f"{job_name}.wfx", f"{job_name}.dm2p"]

            for file in required_files:
                if not self.commands.check_file_exists(f"{colony_dir}/{file}"):
                    raise FileNotFoundError(f"Required input file {file} not found")

            logging.info(f"Input files prepared for INCA calculation of {job_name}")

        except Exception as e:
            logging.error(f"Error preparing INCA input files for {job_name}: {e}")
            raise

    def collect_results(self, job_name):
        """Collect INCA calculation results."""
        try:
            # Check output files in colony
            colony_dir = f"{self.connection.colony_dir}/{job_name}"
            result_file = "ontop.dat"
            result_path = f"{colony_dir}/{result_file}"

            if not self.commands.check_file_exists(result_path):
                raise FileNotFoundError(f"INCA output file {result_file} not found")

            # Get file content
            content = self.commands.read_file_content(result_path)

            # List files in colony directory
            ls_cmd = f"ls -l {colony_dir}"
            file_list = self.commands.execute_command(ls_cmd)
            logging.info(f"Files in colony directory:\n{file_list}")

            return {
                "status": "completed",
                "output_file": result_file,
                "content": content,
            }

        except Exception as e:
            logging.error(f"Error collecting INCA results for {job_name}: {e}")
            raise

    def handle_calculation(self, job_name, input_spec):
        """Handle complete INCA calculation workflow."""
        try:
            # Prepare directories
            self.prepare_directories(job_name)

            # Prepare input files
            self.prepare_input_files(job_name, input_spec)

            # Move required files to scratch
            files_to_move = [
                f"{job_name}_inca.slurm",
                f"{job_name}.inp",
                f"{job_name}.wfx",
                f"{job_name}.dm2p",
            ]

            for file in files_to_move:
                self.move_to_scratch(job_name, file)

            # Submit and monitor
            job_id = self.submit_and_monitor(job_name, step="inca")

            # Retrieve results from scratch
            self.move_all_files_to_colony(job_name)

            # Collect and return results
            return self.collect_results(job_name)

        except Exception as e:
            logging.error(f"Error in INCA calculation for {job_name}: {e}")
            raise


if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from utils.log_config import setup_logging
    from cluster.connection import ClusterConnection
    from cluster.transfer import FileTransfer
    from jobs.manager import JobManager
    from cluster.cleanup import ClusterCleanup
    from calculations.gaussian import GaussianCalculation
    from calculations.dmn import DMNCalculation
    from calculations.dm2prim import DM2PRIMCalculation
    from input.molecules import Molecule
    from input.methods import Method
    from input.basis import BasisSet
    from input.specification import InputSpecification

    # Setup logging
    setup_logging(verbose_level=2)

    try:
        with ClusterConnection() as connection:
            # Initialize components
            file_manager = FileTransfer(connection)
            job_manager = JobManager(connection, file_manager)
            cleanup = ClusterCleanup(connection)

            # Test parameters
            test_name = "inca_test"

            # First run prerequisite calculations
            print("\nRunning prerequisite calculations...")
            molecule = Molecule(name="hydrogen_atom", multiplicity=2)
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

            # Run chain of calculations
            print("\nRunning Gaussian calculation...")
            gaussian = GaussianCalculation(connection, file_manager, job_manager)
            gaussian.handle_calculation(test_name, input_spec)

            print("\nRunning DMN calculation...")
            dmn = DMNCalculation(connection, file_manager, job_manager)
            dmn.handle_calculation(test_name)

            print("\nRunning DM2PRIM calculation...")
            dm2prim = DM2PRIMCalculation(connection, file_manager, job_manager)
            dm2prim.handle_calculation(test_name)

            # Now run INCA calculation
            print("\nTesting INCA calculation...")
            inca_calc = INCACalculation(connection, file_manager, job_manager)
            results = inca_calc.handle_calculation(test_name, input_spec)

            # Print results
            print("\nINCA Calculation results:")
            for key, value in results.items():
                if key != "content":  # Skip printing full content
                    print(f"{key}: {value}")

            # Clean up
            print("\nCleaning up...")
            cleanup.clean_calculation(test_name)

    except Exception as e:
        print(f"Test failed: {e}")
        try:
            cleanup.clean_calculation(test_name)
        except:
            pass
