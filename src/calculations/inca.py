"""
Handles INCA calculations.
"""

import os
import logging
from calculations.base import Calculation
from utils.generator import InputFileGenerator


class INCACalculation(Calculation):
    def prepare_input_files(self, job_name, molecule, method, basis):
        """Prepare input files for INCA calculation."""
        try:
            # Generate INCA input file
            generator = InputFileGenerator(
                config="SP",
                molecule=molecule,
                method=method,
                basis=basis,
                title=job_name,
                input_type="inca"
            )
            
            inp_file = os.path.join("test", f"{job_name}.inp")
            generator.generate_input_file()
            
            # Upload to colony
            colony_file = os.path.join(self.connection.colony_dir, job_name, f"{job_name}.inp")
            self.file_manager.upload_file(inp_file, colony_file)
            
            # Generate INCA SLURM script
            slurm_script = self.job_manager.submitter.generate_inca_script(
                job_name,
                os.path.join(self.connection.scratch_dir, job_name)
            )
            
            # Upload SLURM script
            self.file_manager.upload_file(
                slurm_script,
                os.path.join(self.connection.colony_dir, job_name, f"{job_name}_inca.slurm")
            )
            
            # Check required input files from previous calculations
            required_files = [
                f"{job_name}.wfx",
                f"{job_name}.dm2p"
            ]
            
            colony_dir = os.path.join(self.connection.colony_dir, job_name)
            for file in required_files:
                if not self.commands.check_file_exists(os.path.join(colony_dir, file)):
                    raise FileNotFoundError(f"Required input file {file} not found")
            
        except Exception as e:
            logging.error(f"Error preparing INCA input files for {job_name}: {e}")
            raise

    def collect_results(self, job_name):
        """Collect INCA calculation results."""
        try:
            # INCA outputs ontop.dat file
            colony_dir = os.path.join(self.connection.colony_dir, job_name)
            result_file = "ontop.dat"
            
            if not self.commands.check_file_exists(os.path.join(colony_dir, result_file)):
                raise FileNotFoundError(f"INCA output file {result_file} not found")
            
            # Get results
            content = self.commands.read_file_content(os.path.join(colony_dir, result_file))
            
            return {
                "status": "completed",
                "output_file": result_file,
                "content": content
            }
            
        except Exception as e:
            logging.error(f"Error collecting INCA results for {job_name}: {e}")
            raise

    def handle_calculation(self, job_name, molecule, method, basis):
        """Handle complete INCA calculation workflow."""
        try:
            # Prepare directories
            self.prepare_directories(job_name)
            
            # Prepare input files
            self.prepare_input_files(job_name, molecule, method, basis)
            
            # Move required files to scratch
            files_to_move = [
                f"{job_name}_inca.slurm",
                f"{job_name}.inp",
                f"{job_name}.wfx",
                f"{job_name}.dm2p"
            ]
            
            for file in files_to_move:
                self._move_to_scratch(job_name, file)
            
            # Submit and monitor
            job_id = self.submit_and_monitor(job_name, step="inca")
            
            # Retrieve results
            self._retrieve_from_scratch(job_name)
            
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
    
    # Setup logging
    setup_logging(verbose_level=2)
    
    try:
        with ClusterConnection() as connection:
            # Initialize components
            file_manager = FileTransfer(connection)
            job_manager = JobManager(connection, file_manager)
            cleanup = ClusterCleanup(connection)
            
            # Test calculation
            test_name = "inca_test"
            
            # First run prerequisite calculations
            print("\nRunning prerequisite calculations...")
            molecule = Molecule(name="hydrogen_atom", multiplicity=2)
            method = Method("CISD")
            basis = BasisSet("sto-3g")
            
            # Run chain of calculations
            print("\nRunning Gaussian calculation...")
            gaussian = GaussianCalculation(connection, file_manager, job_manager)
            gaussian.handle_calculation(test_name, molecule, method, basis)
            
            print("\nRunning DMN calculation...")
            dmn = DMNCalculation(connection, file_manager, job_manager)
            dmn.handle_calculation(test_name)
            
            print("\nRunning DM2PRIM calculation...")
            dm2prim = DM2PRIMCalculation(connection, file_manager, job_manager)
            dm2prim.handle_calculation(test_name)
            
            # Now run INCA calculation
            print("\nTesting INCA calculation...")
            calc = INCACalculation(connection, file_manager, job_manager)
            results = calc.handle_calculation(test_name, molecule, method, basis)
            
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