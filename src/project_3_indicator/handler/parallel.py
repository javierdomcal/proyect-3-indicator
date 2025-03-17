"""
Parallel handler for managing multiple flux calculations simultaneously.
"""

import logging
import concurrent.futures
import time
from pathlib import Path
import re
from datetime import datetime
from .calculation import CalculationHandler
from ..cluster.connection import ClusterConnection
from ..cluster.transfer import FileTransfer
from ..jobs.manager import JobManager

try:
    from IPython.display import HTML, display, clear_output
    import ipywidgets as widgets
    IN_NOTEBOOK = True
except ImportError:
    IN_NOTEBOOK = False

class ParallelHandler:
    def __init__(self, connection, file_manager, job_manager, max_workers=4):
        """
        Initialize parallel handler.
        The initial connection is only used as a template for configuration.

        Args:
            connection: ClusterConnection instance (used as template)
            file_manager: FileTransfer instance (not used)
            job_manager: JobManager instance (not used)
            max_workers: Maximum number of concurrent calculations
        """
        self.config_file = connection.config_file
        self.cluster_name = connection.cluster_name
        self.max_workers = max_workers
        self.calculations = []
        self.logger = logging.getLogger('ParallelHandler')

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
                    <td style="border: 1px solid #ddd; padding: 8px;">
                        {calc['status']}
                        {f'<div style="color: red; font-size: 0.9em;">{error_msg}</div>' if error_msg else ''}
                    </td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{elapsed}</td>
                </tr>
            """

        html += "</table></div>"
        return html

    def update_status(self, params, new_status, error_msg=None):
        """Update calculation status and refresh display."""
        job_name = params.get('job_name', f"{params['molecule_name']}_{params['method_name']}_{params['basis_name']}")

        for calc in self.calculations:
            if calc['job_name'] == job_name:
                calc['status'] = new_status
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
            self.logger.info(log_msg)

    def create_new_connection(self):
        """Create a fresh connection for each calculation."""
        connection = ClusterConnection(
            config_file=self.config_file,
            cluster_name=self.cluster_name
        )
        connection.connect()
        file_manager = FileTransfer(connection)
        job_manager = JobManager(connection, file_manager)
        handler = CalculationHandler(connection, file_manager, job_manager)

        return connection, handler

    def _run_single_calculation(self, params):
        """Run a single calculation with its own connection."""
        connection = None
        try:
            # Create fresh connection for this calculation
            connection, handler = self.create_new_connection()
            self.update_status(params, 'running')

            # Run the calculation with this connection
            result = handler.handle_calculation(
                molecule_name=params['molecule_name'],
                method_name=params['method_name'],
                basis_name=params['basis_name'],
                config=params['config'],
                charge=params['charge'],
                multiplicity=params['multiplicity'],
                omega=params['omega'],
                scanning_props=params['scanning_props']
            )

            self.update_status(params, 'completed')
            return result

        except Exception as e:
            self.update_status(params, 'failed', str(e))
            raise
        finally:
            # Always clean up the connection
            if connection:
                try:
                    connection.disconnect()
                except:
                    pass

    def handle_parallel_calculations(self, molecule_name, method_name, basis_name,
                                  config="SP", charge=0, multiplicity=1,
                                  omega=None, scanning_props=None, excited_state=None):
        """
        Handle multiple calculations in parallel.

        Args:
            molecule_name: String or list of molecule names
            method_name: String or list of method names
            basis_name: String or list of basis set names
            config: Calculation type ("SP" or "Opt"), default "SP"
            charge: Molecular charge, default 0
            multiplicity: Spin multiplicity, default 1
            omega: Omega parameter for harmonium/even-tempered basis
            scanning_props: Properties to scan
        """
        try:
            # Convert inputs to lists if not already
            molecules = molecule_name if isinstance(molecule_name, list) else [molecule_name]
            methods = method_name if isinstance(method_name, list) else [method_name]
            bases = basis_name if isinstance(basis_name, list) else [basis_name]

            # Generate all calculation combinations
            calcs = []
            self.calculations = []
            for mol in molecules:
                for meth in methods:
                    for bas in bases:
                        job_name = f"calc_{re.sub(r'[^a-zA-Z0-9]', '_', f'{mol}_{meth}_{bas}')}"
                        calc_params = {
                            'molecule_name': mol,
                            'method_name': meth,
                            'basis_name': bas,
                            'config': config,
                            'charge': charge,
                            'multiplicity': multiplicity,
                            'omega': omega,
                            'scanning_props': scanning_props,
                            'job_name': job_name,
                            'excited_state': excited_state,
                            'status': 'pending'
                        }
                        calcs.append(calc_params)
                        self.calculations.append(calc_params.copy())

            if IN_NOTEBOOK:
                with self.log_output:
                    print(f"Launching {len(calcs)} calculations with {self.max_workers} workers")
                with self.status_output:
                    display(HTML(self._generate_status_html()))
            else:
                self.logger.info(f"Launching {len(calcs)} calculations with {self.max_workers} workers")

            # Run calculations in parallel with independent connections
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_params = {}
                for params in calcs:
                    future = executor.submit(self._run_single_calculation, params)
                    future_to_params[future] = params
                    time.sleep(5)  # 5-second delay between launching calculations

                for future in concurrent.futures.as_completed(future_to_params):
                    params = future_to_params[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        results.append({
                            "calculation_id": None,
                            "molecule_name": params['molecule_name'],
                            "method_name": params['method_name'],
                            "basis_name": params['basis_name'],
                            "status": "failed",
                            "error": str(e)
                        })

            # Sort results to match input order
            ordered_results = []
            for params in calcs:
                for result in results:
                    if (result["molecule_name"] == params['molecule_name'] and
                        result["method_name"] == params['method_name'] and
                        result["basis_name"] == params['basis_name']):
                        ordered_results.append(result)
                        break

            return ordered_results

        except Exception as e:
            error_msg = str(e)
            if IN_NOTEBOOK:
                with self.log_output:
                    print(f"Error in parallel calculation handling: {error_msg}")
            else:
                self.logger.error(f"Error in parallel calculation handling: {error_msg}")
            raise