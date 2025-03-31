"""
Parallel handler for managing multiple flux calculations simultaneously.
"""

import logging
import concurrent.futures
import time
import re
from pathlib import Path
from datetime import datetime

from .calculation import CalculationHandler
from ..cluster.connection import ClusterConnection
from ..cluster.transfer import FileTransfer
from ..jobs.manager import JobManager
from ..database import get_database

try:
    from IPython.display import HTML, display, clear_output
    import ipywidgets as widgets
    IN_NOTEBOOK = True
except ImportError:
    IN_NOTEBOOK = False

logger = logging.getLogger(__name__)

class ParallelHandler:
    def __init__(self, connection, file_manager, job_manager, max_workers=4, db=None):
        """
        Initialize parallel handler.
        The initial connection is only used as a template for configuration.

        Args:
            connection: ClusterConnection instance (used as template)
            file_manager: FileTransfer instance (not used)
            job_manager: JobManager instance (not used)
            max_workers: Maximum number of concurrent calculations
            db: Database instance (optional, will be created if not provided)
        """
        self.config_file = connection.config_file
        self.cluster_name = connection.cluster_name
        self.max_workers = max_workers
        self.calculations = []
        self.db = db or get_database()

        # Set up notebook display if in notebook environment
        if IN_NOTEBOOK:
            self.status_output = widgets.Output()
            self.log_output = widgets.Output()
            display(widgets.VBox([self.status_output, self.log_output]))

    def _generate_status_html(self):
        """Generate HTML for status display."""
        if not IN_NOTEBOOK:
            return

        completed = sum(1 for c in self.calculations if c['status'] == 'completed')
        failed = sum(1 for c in self.calculations if c['status'] == 'failed')
        total = len(self.calculations)

        html = f"""
        <div style="margin: 10px 0; font-family: Arial, sans-serif;">
            <div style="margin-bottom: 10px;">
                <b>Progress: {completed} / {total} completed</b>
                {f' ({failed} failed)' if failed > 0 else ''}
            </div>
            <table style="width:100%; border-collapse: collapse;">
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 8px;">Job Name</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Molecule</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Method</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Basis</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">ID</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Status</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Time</th>
                </tr>
        """

        status_colors = {
            'pending': '#fff',
            'running': '#fff3cd',
            'completed': '#d4edda',
            'failed': '#f8d7da'
        }

        for calc in self.calculations:
            status_color = status_colors.get(calc['status'], '#fff')
            elapsed = calc.get('elapsed', '')
            error_msg = calc.get('error', '')

            html += f"""
                <tr style="background-color: {status_color}">
                    <td style="border: 1px solid #ddd; padding: 8px;">{calc['job_name']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{calc['molecule_name']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{calc['method_name']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{calc['basis_name']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{calc.get('calc_id', 'N/A')}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">
                        {calc['status']}
                        {f'<div style="color: red; font-size: 0.9em;">{error_msg}</div>' if error_msg else ''}
                    </td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{elapsed}</td>
                </tr>
            """

        html += "</table></div>"
        return html

    def update_status(self, params, new_status, error_msg=None, calc_id=None):
        """
        Update calculation status and refresh display.

        Args:
            params: Calculation parameters
            new_status: New status (pending/running/completed/failed)
            error_msg: Error message (optional)
            calc_id: Calculation ID if available (optional)
        """
        job_name = params.get('job_name', f"{params['molecule_name']}_{params['method_name']}_{params['basis_name']}")

        for calc in self.calculations:
            if calc['job_name'] == job_name:
                calc['status'] = new_status

                if calc_id is not None:
                    calc['calc_id'] = calc_id

                if error_msg:
                    calc['error'] = error_msg

                if new_status == 'completed':
                    end_time = datetime.now()
                    start_time = calc.get('start_time')
                    if start_time:
                        elapsed = end_time - start_time
                        calc['elapsed'] = str(elapsed).split('.')[0]

                elif new_status == 'running':
                    calc['start_time'] = datetime.now()

                break

        # Update display in notebook or log
        if IN_NOTEBOOK:
            with self.status_output:
                clear_output(wait=True)
                display(HTML(self._generate_status_html()))
            if error_msg:
                with self.log_output:
                    print(f"\nJob {job_name}: {new_status} - {error_msg}")
        else:
            log_msg = f"Job {job_name}: {new_status}"
            if error_msg:
                log_msg += f" - {error_msg}"
            logger.info(log_msg)

        # Update database if we have a calculation ID
        if calc_id is not None:
            try:
                with self.db.transaction():
                    # Check if we need to update database status
                    calc_info = self.db.calculations.get(calc_id)
                    if calc_info and calc_info['status'] != new_status:
                        self.db.calculations.update_status(calc_id, new_status, error_msg)
            except Exception as e:
                logger.warning(f"Failed to update database status for calculation {calc_id}: {e}")

    def create_new_connection(self):
        """
        Create a fresh connection for each calculation.

        Returns:
            tuple: (connection, handler)
        """
        connection = ClusterConnection(
            config_file=self.config_file,
            cluster_name=self.cluster_name
        )
        connection.connect()
        file_manager = FileTransfer(connection)
        job_manager = JobManager(connection, file_manager)

        # Pass the database instance to the calculation handler
        handler = CalculationHandler(connection, file_manager, job_manager, self.db)

        return connection, handler

    def _run_single_calculation(self, input_params):
        """
        Run a single calculation with its own connection.

        Args:
            input_params: Calculation parameters

        Returns:
            dict: Calculation results
        """
        connection = None
        try:
            # Create fresh connection for this calculation
            connection, handler = self.create_new_connection()

            # Update status to running
            self.update_status(input_params, 'running')

            # Run the calculation with this connection
            result = handler.handle_calculation(input_params)

            # Update status with the calculation ID from the result
            calc_id = result.get('calculation_id')
            self.update_status(input_params, 'completed', calc_id=calc_id)

            return result

        except Exception as e:
            logger.error(f"Error in calculation: {str(e)}")
            self.update_status(input_params, 'failed', str(e))
            raise

        finally:
            # Always clean up the connection
            if connection:
                try:
                    connection.disconnect()
                except Exception as conn_error:
                    logger.warning(f"Error disconnecting: {str(conn_error)}")

    def handle_parallel_calculations(self, input):
        """
        Handle multiple calculations in parallel.

        Args:
            input: Dictionary with calculation parameters
                molecule: String or list of molecule names
                method: String or list of method names
                basis: String or list of basis set names
                config: Calculation type ("SP" or "Opt"), default "SP"
                charge: Molecular charge, default 0
                multiplicity: Spin multiplicity, default 1
                omega: Omega parameter for harmonium/even-tempered basis
                scanning_props: Properties to scan

        Returns:
            dict or object: If multiple results, returns a dictionary organized by the
                            varied parameter (molecule, method, or basis). If only one
                            calculation, returns the single result directly.
        """
        try:
            # Extract and normalize inputs
            molecules = input['molecule'] if isinstance(input['molecule'], list) else [input['molecule']]
            methods = input['method'] if isinstance(input['method'], list) else [input['method']]
            bases = input['basis'] if isinstance(input['basis'], list) else [input['basis']]

            # Default values for optional parameters
            config = input.get('config', 'SP')
            charge = input.get('charge', 0)
            multiplicity = input.get('multiplicity', 1)
            omega = input.get('omega', None)
            scanning_props = input.get('scanning_props', [])

            # Generate all calculation combinations
            calcs = []
            self.calculations = []

            # Determine which parameter is varying (for organizing results)
            varying_param = None
            if len(molecules) > 1:
                varying_param = "molecule"
            elif len(methods) > 1:
                varying_param = "method"
            elif len(bases) > 1:
                varying_param = "basis"

            for mol in molecules:
                for meth in methods:
                    for bas in bases:
                        job_name = f"calc_{re.sub(r'[^a-zA-Z0-9]', '_', f'{mol}_{meth}_{bas}')}"

                        # Create calculation parameter dictionary
                        calc_params = {
                            'molecule': mol,
                            'method': meth,
                            'basis': bas,
                            'config': config,
                            'charge': charge,
                            'multiplicity': multiplicity,
                            'omega': omega,
                            'scanning_props': scanning_props,
                            'job_name': job_name,
                            'status': 'pending',
                            'calc_id': None
                        }

                        # Both for running and for display
                        calcs.append(calc_params)
                        self.calculations.append(calc_params.copy())

            # Display initial status
            if IN_NOTEBOOK:
                with self.log_output:
                    print(f"Launching {len(calcs)} calculations with {self.max_workers} workers")
                with self.status_output:
                    display(HTML(self._generate_status_html()))
            else:
                logger.info(f"Launching {len(calcs)} calculations with {self.max_workers} workers")

            # Run calculations in parallel with independent connections
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_params = {}
                for params in calcs:
                    future = executor.submit(self._run_single_calculation, params)
                    future_to_params[future] = params
                    time.sleep(5)  # 5-second delay between launching calculations

                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_params):
                    params = future_to_params[future]

                    try:
                        result = future.result()
                        results.append(result)
                        logger.info(f"Completed calculation for {params['molecule']}/{params['method']}/{params['basis']}")

                    except Exception as e:
                        error_msg = str(e)
                        logger.error(f"Calculation failed: {error_msg}")

                        # Create a placeholder result for failed calculations
                        results.append({
                            "calculation_id": None,
                            "molecule": params['molecule'],
                            "method": params['method'],
                            "basis": params['basis'],
                            "status": "failed",
                            "error_message": error_msg
                        })

            # Tag all calculations as part of this batch
            batch_tag = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            for result in results:
                if result.get("calculation_id"):
                    try:
                        with self.db.transaction():
                            self.db.calculations.add_tag(result["calculation_id"], batch_tag)
                    except Exception as e:
                        logger.warning(f"Could not add batch tag: {e}")

            # Organize results based on what parameter is varying
            if len(calcs) == 1:
                # If only one calculation was run, return the result directly
                return results[0] if results else None

            elif varying_param:
                # If we have a varying parameter, organize by that
                organized_results = {}

                # Key mapping based on varying parameter
                key_map = {
                    "molecule": "molecule",
                    "method": "method",
                    "basis": "basis"
                }

                # Organize results by the varying parameter
                for result in results:
                    key = result.get(key_map[varying_param])
                    if key:
                        organized_results[key] = result

                return organized_results

            else:
                # If no clear varying parameter but multiple calcs, create a dictionary
                # Using a combination key of molecule_method_basis
                organized_results = {}
                for result in results:
                    key = f"{result.get('molecule')}_{result.get('method')}_{result.get('basis')}"
                    organized_results[key] = result

                return organized_results

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in parallel calculation handling: {error_msg}")

            if IN_NOTEBOOK:
                with self.log_output:
                    print(f"Error in parallel calculation handling: {error_msg}")

            raise