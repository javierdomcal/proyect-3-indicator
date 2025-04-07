"""
Base flux manager for handling sequences of calculations.
"""

import logging
import copy
from datetime import datetime
from ..calculations.gaussian import GaussianCalculation
from ..calculations.dmn import DMNCalculation
from ..calculations.dm2prim import DM2PRIMCalculation
from ..calculations.inca import INCACalculation
from ..input.methods import Method


class Flux:
    def __init__(self, connection, file_manager, job_manager):
        """Initialize flux manager with necessary components."""
        self.connection = connection
        self.file_manager = file_manager
        self.job_manager = job_manager
        self.gaussian = GaussianCalculation(connection, file_manager, job_manager)
        self.dmn = DMNCalculation(connection, file_manager, job_manager)
        self.dm2prim = DM2PRIMCalculation(connection, file_manager, job_manager)
        self.inca = INCACalculation(connection, file_manager, job_manager)



    def handle_flux(self, job_name, input_spec):
        try:
            print(input_spec.properties.get_active_properties())
            job_name = str(job_name)
            if 'pair_density_nucleus' in input_spec.properties.get_active_properties():
                logging.info(f"Pair density nucleus property detected for {job_name}. Needs more calculations")
                self.handle_pair_density_flux(job_name, input_spec)
            else:
                if input_spec.method.is_hf:
                    self.handle_hf_correlation_flux(job_name, input_spec)
                else:
                    self.handle_correlation_flux(job_name, input_spec)

            logging.info(f"Correlation flux completed for {job_name}")

        except Exception as e:
            logging.error(f"Error in flux {job_name}: {e}")
            raise

    def handle_correlation_flux(self, job_name, input_spec):
        """
        Handle complete correlation flux calculation.

        This includes:
        1. Gaussian calculation
        2. DMN calculation
        3. DM2PRIM calculation
        4. INCA calculation
        """
        job_name = str(job_name)


        try:

            self.gaussian.handle_calculation(job_name, input_spec)
            self.dmn.handle_calculation(job_name, input_spec)
            self.dm2prim.handle_calculation(job_name, input_spec)
            self.inca.handle_calculation(job_name, input_spec)






        except Exception as e:
            logging.error(f"Error in correlation flux for {job_name}: {e}")
            raise

    def handle_hf_correlation_flux(self, job_name, input_spec):
        """Handle HF-only flux calculation."""
        try:
            self.gaussian.handle_calculation(job_name, input_spec)
            self.dmn.handle_calculation(job_name, input_spec)
            self.dm2prim.handle_calculation(job_name, input_spec)
            self.inca.handle_calculation(job_name, input_spec)


        except Exception as e:
            logging.error(f"Error in HF flux for {job_name}: {e}")
            raise

    def handle_pair_density_flux(self, job_name, input_spec):
        """
        Handle complete correlation flux calculation.

        This includes:
        1. Gaussian calculation
        2. Gaussian HF Calculation
        3. DMN calculation
        4. DM2PRIM calculation
        5. DM2PRIM HF calculation
        6. DM2PRIM HFL calculation
        7. INCA calculation
        """

        job_name = str(job_name)
        job_name_hf = job_name + "_hf"
        job_name_hfl = job_name + "_hfl"
        try:

            self.gaussian.handle_calculation(job_name, input_spec)
            input_spec_hf = copy.deepcopy(input_spec)
            input_spec_hf.method = Method(name="HF", excited_state=input_spec.method.excited_state)
            self.gaussian.handle_calculation(job_name_hf, input_spec_hf)
            self.gaussian.handle_calculation(job_name_hfl, input_spec) ##Very bad implementation but bor debugging
            self.dmn.handle_calculation(job_name, input_spec)
            self.dm2prim.handle_calculation(job_name, input_spec)
            self.dm2prim.handle_calculation(job_name_hf, input_spec_hf)
            self.dm2prim.handle_calculation(job_name_hfl, input_spec)
            self.inca.handle_calculation(job_name, input_spec)




        except Exception as e:
            logging.error(f"Error in correlation flux for {job_name}: {e}")
            raise

