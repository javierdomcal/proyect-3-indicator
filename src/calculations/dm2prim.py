"""
Handles DM2PRIM calculations.
"""

import os
import logging
from calculations.base import Calculation


class DM2PRIMCalculation(Calculation):
    def prepare_input_files(self, job_name):
        """Prepare input files for DM2PRIM calculation."""
        try:
            # Check required input files from previous calculations
            colony_dir = os.path.join(self.connection.colony_dir, job_name)
            required_files = [
                f"{job_name}.dm2",
                f"{job_name}.fchk"
            ]
            
            # Verify input files exist
            for file in required_files:
                if not self.commands.check_file_exists(os.path.join(colony_dir, file)):
                    raise FileNotFoundError(f"Required input file {file} not found")
            
            # Generate DM2PRIM SLURM script
            slurm_script = self.job_manager.submitter.generate_dm2prim_script(
                job_name,
                os.path.join(self.connection.scratch_dir, job_name)
            )
            
            # Upload SLURM script to colony
            self.file_manager.upload_file(
                slurm_script,
                os.path.join(colony_dir, f"{job_name}_dm2prim.slurm")
            )
            
        except Exception as e:
            logging.error(f"Error preparing DM2PRIM input files for {job_name}: {e}")
            raise

    def collect_results(self, job_name):
        """Collect DM2PRIM calculation results."""
        try:
            # Check for required output files
            colony_dir = os.path.join(self.connection.colony_dir, job_name)
            required_files = [
                f"{job_name}.dm2p",
                f"{job_name}.wfx"
            ]
            
            # Verify output files exist
            for file in required_files:
                file_path = os.path.join(colony_dir, file)
                if not self.commands.check_file_exists(file_path):
                    raise FileNotFoundError(f"Required DM2PRIM output file {file} not found")
                
            return {
                "status": "completed",
                "output_files": required_files
            }
            
        except Exception as e:
            logging.error(f"Error collecting DM2PRIM results for {job_name}: {e}")
            raise

    def handle_calculation(self, job_name):
        """Handle complete DM2PRIM calculation workflow."""
        try:
            # Prepare directories
            self.prepare_directories(job_name)
            
            # Prepare input files
            self.prepare_input_files(job_name)
            
            # Move required files to scratch
            files_to_move = [
                f"{job_name}_dm2prim.slurm",
                f"{job_name}.dm2",
                f"{job_name}.fchk"
            ]
            
            for file in files_to_move:
                self.move_to_scratch(job_name, file)
            
            # Submit and monitor
            job_id = self.submit_and_monitor(job_name, step="dm2prim")
            
            # Retrieve results from scratch
            self.retrieve_results(job_name, ["*"])
            
            # Collect and return results
            return self.collect_results(job_name)
            
        except Exception as e:
            logging.error(f"Error in DM2PRIM calculation for {job_name}: {e}")
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
            
            # Test parameters
            test_name = "dm2prim_test"
            
            # Run prerequisite calculations
            print("\nRunning prerequisite calculations...")
            molecule = Molecule(name="hydrogen_atom", multiplicity=2)
            method = Method("CISD")
            basis = BasisSet("sto-3g")
            
            # Gaussian calculation
            print("\nRunning Gaussian calculation...")
            gaussian = GaussianCalculation(connection, file_manager, job_manager)
            gaussian.handle_calculation(test_name, molecule, method, basis)
            
            # DMN calculation
            print("\nRunning DMN calculation...")
            dmn = DMNCalculation(connection, file_manager, job_manager)
            dmn.handle_calculation(test_name)
            
            # Now run DM2PRIM calculation
            print("\nTesting DM2PRIM calculation...")
            dm2prim_calc = DM2PRIMCalculation(connection, file_manager, job_manager)
            results = dm2prim_calc.handle_calculation(test_name)
            
            # Print results
            print("\nDM2PRIM Calculation results:")
            for key, value in results.items():
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