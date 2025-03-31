"""
Handles preliminary optimization calculations for screening purposes.
"""

import os
import logging
from pathlib import Path
from copy import deepcopy

from ..calculations.gaussian import GaussianCalculation
from ..utils.parsers import extract_geometry_from_log
from ..input.specification import InputSpecification
from ..input.molecules import Molecule
from ..input.methods import Method
from ..input.basis import BasisSet

class ScreeningHandler:
    """Handles preliminary optimization calculations."""

    def __init__(self, connection, file_manager, job_manager):
        """Initialize with required components."""
        self.connection = connection
        self.file_manager = file_manager
        self.job_manager = job_manager
        self.gaussian = GaussianCalculation(connection, file_manager, job_manager)

    def create_screening_spec(self, original_spec, screening_dict):
        """
        Create a new InputSpecification for screening calculation.

        Args:
            original_spec: Original InputSpecification
            screening_dict: Dictionary with modifications for screening
                          Can include: 'basis', 'method'

        Returns:
            InputSpecification for screening calculation
        """
        # Prepare input dictionary based on original specification
        input_dict = {
            "molecule": original_spec.molecule.name,
            "charge": original_spec.molecule.charge,
            "multiplicity": original_spec.molecule.multiplicity,
            "omega": original_spec.molecule.omega,
            "method": screening_dict.get('method', original_spec.method.name),
            "basis": screening_dict.get('basis', original_spec.basis.name),
            "config": "Opt",  # Always optimization for screening
            "grid": original_spec.grid.to_dict() if hasattr(original_spec.grid, 'to_dict') else {},
            "properties": original_spec.properties.properties if hasattr(original_spec.properties, 'properties') else [],
            "excited_state": None  # Force ground state for optimization
        }

        # Create screening specification with the new input format
        screening_spec = InputSpecification(input_dict)

        # Update title to include screening suffix
        screening_spec.title = f"{original_spec.title}_screening"

        # Copy geometry from original spec if available
        if hasattr(original_spec.molecule, 'geometry') and original_spec.molecule.geometry:
            screening_spec.molecule.geometry = deepcopy(original_spec.molecule.geometry)

        # Use original calculation ID if available
        if hasattr(original_spec, 'calc_id') and original_spec.calc_id:
            screening_spec.calc_id = original_spec.calc_id

        return screening_spec

    def handle_screening(self, original_spec, screening_dict):
        """
        Handle complete screening calculation workflow.

        Args:
            original_spec: Original InputSpecification
            screening_dict: Dictionary with screening parameters

        Returns:
            Modified original_spec with optimized geometry
        """
        try:
            # Create screening specification
            screening_spec = self.create_screening_spec(original_spec, screening_dict)

            # Use main calculation ID with screening suffix
            calc_id = original_spec.title  # This should be the calculation ID
            screening_id = f"{calc_id}_screening"

            # Run Gaussian optimization using screening ID
            success = self.gaussian.handle_calculation(
                job_name=screening_id,
                input_spec=screening_spec
            )

            if not success:
                raise ValueError("Screening calculation failed")

            # Get log file path
            log_file = os.path.join(
                self.connection.colony_dir,
                screening_id,
                f"{screening_id}.log"
            )

            # Extract optimized geometry
            log_content = self.connection.commands.read_file_content(log_file)
            geometry_data = extract_geometry_from_log(log_content, is_content=True)

            if not geometry_data['is_optimized']:
                raise ValueError("Geometry optimization did not converge")

            # Convert geometry to XYZ format
            xyz_content = f"{len(geometry_data['geometry'])}\n"
            xyz_content += f"Optimized geometry from screening calculation\n"
            for atom in geometry_data['geometry']:
                coords = atom['coordinates']
                xyz_content += f"{atom['symbol']}  {coords[0]:.6f}  {coords[1]:.6f}  {coords[2]:.6f}\n"

            # Update original specification with optimized geometry
            original_spec.update_geometry(xyz_content)

            # Clean up screening calculation files
            self.cleanup_screening(f"{original_spec.title}_screening")

            return original_spec

        except Exception as e:
            logging.error(f"Error in screening calculation: {str(e)}")
            raise

    def cleanup_screening(self, screening_name):
        """Clean up files from screening calculation."""
        try:
            # Remove colony directory
            self.connection.commands.execute_command(
                f"rm -rf {self.connection.colony_dir}/{screening_name}"
            )

            # Remove scratch directory
            self.connection.commands.execute_command(
                f"rm -rf {self.connection.scratch_dir}/{screening_name}"
            )

        except Exception as e:
            logging.warning(f"Error cleaning up screening files: {str(e)}")


if __name__ == "__main__":
    # Test the screening handler
    from ..cluster.connection import ClusterConnection
    from ..cluster.transfer import FileTransfer
    from ..jobs.manager import JobManager

    try:
        with ClusterConnection() as connection:
            # Initialize components
            file_manager = FileTransfer(connection)
            job_manager = JobManager(connection, file_manager)

            # Create test input dictionary
            input_dict = {
                "molecule": "ethene",
                "method": "HF",
                "basis": "sto-3g",
                "config": "SP"
            }

            # Create original specification with the new input format
            original_spec = InputSpecification(input_dict)
            original_spec.title = "ethene_test"  # Set title explicitly

            # Create screening dictionary
            screening_dict = {
                'basis': '3-21g',  # Use smaller basis for optimization
                'method': 'HF'     # Use HF for optimization
            }

            # Initialize and run screening
            handler = ScreeningHandler(connection, file_manager, job_manager)
            modified_spec = handler.handle_screening(original_spec, screening_dict)

            print("\nOptimized geometry:")
            print(modified_spec.molecule.geometry)

    except Exception as e:
        print(f"Test failed: {str(e)}")