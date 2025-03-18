"""
Utilities for handling cube files.

This module provides functions for reading, writing, analyzing, and visualizing
Gaussian cube files used in quantum chemistry calculations.
"""

import numpy as np
import logging
import os
import pandas as pd
from pathlib import Path

def read_cube_file(cube_path):
    """
    Read a cube file and return the header information, grid data, and values.

    Args:
        cube_path (str or Path): Path to the cube file

    Returns:
        dict: Dictionary containing:
            - header (dict): Metadata about the cube file
            - atoms (list): List of atom information
            - grid (tuple): Tuple of (X, Y, Z) meshgrid arrays
            - values (ndarray): 3D array of values
            - shape (tuple): Shape of the grid as (nx, ny, nz)
    """
    try:
        with open(cube_path, 'r') as f:
            # Read the first two comment lines
            comment1 = f.readline().strip()
            comment2 = f.readline().strip()

            # Read grid specs
            parts = f.readline().split()
            natoms = int(parts[0])
            origin = np.array([float(parts[1]), float(parts[2]), float(parts[3])])

            # Read grid dimensions and step sizes
            nx_line = f.readline().split()
            ny_line = f.readline().split()
            nz_line = f.readline().split()

            nx = int(nx_line[0])
            ny = int(ny_line[0])
            nz = int(nz_line[0])

            dx = np.array([float(nx_line[1]), float(nx_line[2]), float(nx_line[3])])
            dy = np.array([float(ny_line[1]), float(ny_line[2]), float(ny_line[3])])
            dz = np.array([float(nz_line[1]), float(nz_line[2]), float(nz_line[3])])

            # Read atom coordinates
            atoms = []
            for i in range(natoms):
                atom_line = f.readline().split()
                atom = {
                    'atomic_number': int(atom_line[0]),
                    'charge': float(atom_line[1]),
                    'coordinates': [float(atom_line[2]), float(atom_line[3]), float(atom_line[4])]
                }
                atoms.append(atom)

            # Read the volumetric data
            values = []
            for line in f:
                values.extend([float(val) for val in line.split()])

            values = np.array(values)

            # Reshape values to match grid shape
            try:
                values = values.reshape((nx, ny, nz))
            except ValueError:
                # If reshape fails, try flattening and reshaping
                logging.warning(f"Reshaping failed for {cube_path}, trying alternative approach")
                values = np.array(values).flatten()
                if len(values) >= nx * ny * nz:
                    values = values[:nx * ny * nz].reshape((nx, ny, nz))
                else:
                    raise ValueError(f"Insufficient data points in cube file: {len(values)} < {nx * ny * nz}")

            # Create the grid
            x = np.linspace(origin[0], origin[0] + (nx-1)*dx[0], nx)
            y = np.linspace(origin[1], origin[1] + (ny-1)*dy[1], ny)
            z = np.linspace(origin[2], origin[2] + (nz-1)*dz[2], nz)

            # Create meshgrid
            X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

            header = {
                'comment1': comment1,
                'comment2': comment2,
                'natoms': natoms,
                'origin': origin,
                'nx': nx,
                'ny': ny,
                'nz': nz,
                'dx': dx,
                'dy': dy,
                'dz': dz
            }

            return {
                'header': header,
                'atoms': atoms,
                'grid': (X, Y, Z),
                'values': values,
                'shape': (nx, ny, nz)
            }

    except Exception as e:
        logging.error(f"Error reading cube file {cube_path}: {str(e)}")
        raise

def to_dataframe(cube_data):
    """
    Convert cube data to a pandas DataFrame.

    Args:
        cube_data (dict): Dictionary with cube data from read_cube_file

    Returns:
        pd.DataFrame: DataFrame with columns x, y, z, value
    """
    X, Y, Z = cube_data['grid']
    values = cube_data['values']

    # Flatten the arrays for DataFrame creation
    x_flat = X.flatten()
    y_flat = Y.flatten()
    z_flat = Z.flatten()
    values_flat = values.flatten()

    # Create DataFrame
    df = pd.DataFrame({
        'x': x_flat,
        'y': y_flat,
        'z': z_flat,
        'value': values_flat
    })

    return df

def get_value_at_point(cube_data, point):
    """
    Get the value at a specific point by interpolation.

    Args:
        cube_data (dict): Dictionary with cube data from read_cube_file
        point (tuple): (x, y, z) coordinates

    Returns:
        float: Interpolated value at the specified point
    """
    from scipy.interpolate import RegularGridInterpolator

    X, Y, Z = cube_data['grid']
    values = cube_data['values']

    # Get unique coordinate values
    x_unique = np.unique(X[:, 0, 0])
    y_unique = np.unique(Y[0, :, 0])
    z_unique = np.unique(Z[0, 0, :])

    # Create interpolator
    interpolator = RegularGridInterpolator((x_unique, y_unique, z_unique), values)

    # Return interpolated value
    return float(interpolator(point))

def combine_cube_files(files_dict, output_path=None):
    """
    Combine multiple cube files into a pandas DataFrame.
    Useful for creating datasets with multiple properties.

    Args:
        files_dict (dict): Dictionary mapping column names to cube file paths
        output_path (str, optional): Path to save the combined DataFrame

    Returns:
        pd.DataFrame: Combined DataFrame with values from all cube files
    """
    first_file = list(files_dict.values())[0]
    base_data = read_cube_file(first_file)
    df = to_dataframe(base_data)

    # Rename value column to match first file key
    first_key = list(files_dict.keys())[0]
    df.rename(columns={'value': first_key}, inplace=True)

    # Add data from other files
    for name, path in list(files_dict.items())[1:]:
        if os.path.exists(path):
            try:
                cube_data = read_cube_file(path)
                tmp_df = to_dataframe(cube_data)
                df[name] = tmp_df['value']
            except Exception as e:
                logging.error(f"Error processing {path}: {str(e)}")
                df[name] = np.nan
        else:
            logging.warning(f"File not found: {path}")
            df[name] = np.nan

    # Save to CSV if output path provided
    if output_path:
        df.to_csv(output_path, index=False)

    return df

def calculate_statistics(cube_data):
    """
    Calculate basic statistics for cube data.

    Args:
        cube_data (dict): Dictionary with cube data from read_cube_file

    Returns:
        dict: Dictionary with statistics
    """
    values = cube_data['values']
    stats = {
        'min': float(np.min(values)),
        'max': float(np.max(values)),
        'mean': float(np.mean(values)),
        'median': float(np.median(values)),
        'std': float(np.std(values)),
        'abs_max': float(np.max(np.abs(values))),
        'nonzero_count': int(np.count_nonzero(values)),
        'total_points': int(values.size)
    }
    return stats

def write_cube_file(output_path, header, atoms, values):
    """
    Write data to a cube file.

    Args:
        output_path (str): Path to output cube file
        header (dict): Header information
        atoms (list): List of atom information
        values (ndarray): 3D array of values
    """
    try:
        with open(output_path, 'w') as f:
            # Write comment lines
            f.write(f"{header.get('comment1', 'Cube file generated by project_3_indicator')}\n")
            f.write(f"{header.get('comment2', 'Values represent electronic properties')}\n")

            # Write grid specs
            origin = header['origin']
            f.write(f"{len(atoms)} {origin[0]:.6f} {origin[1]:.6f} {origin[2]:.6f}\n")

            # Write grid dimensions and step sizes
            f.write(f"{header['nx']} {header['dx'][0]:.6f} {header['dx'][1]:.6f} {header['dx'][2]:.6f}\n")
            f.write(f"{header['ny']} {header['dy'][0]:.6f} {header['dy'][1]:.6f} {header['dy'][2]:.6f}\n")
            f.write(f"{header['nz']} {header['dz'][0]:.6f} {header['dz'][1]:.6f} {header['dz'][2]:.6f}\n")

            # Write atom coordinates
            for atom in atoms:
                coords = atom['coordinates']
                f.write(f"{atom['atomic_number']} {atom['charge']:.6f} {coords[0]:.6f} {coords[1]:.6f} {coords[2]:.6f}\n")

            # Write volumetric data
            values_flat = values.flatten()
            count = 0
            for val in values_flat:
                f.write(f"{val:.5E} ")
                count += 1
                if count % 6 == 0:
                    f.write("\n")

            if count % 6 != 0:
                f.write("\n")

    except Exception as e:
        logging.error(f"Error writing cube file {output_path}: {str(e)}")
        raise

def get_atom_locations(cube_data):
    """
    Extract atom locations from cube data.

    Args:
        cube_data (dict): Dictionary with cube data from read_cube_file

    Returns:
        pd.DataFrame: DataFrame with atom information
    """
    atoms = []
    for i, atom in enumerate(cube_data['atoms']):
        atoms.append({
            'atom_index': i + 1,
            'atomic_number': atom['atomic_number'],
            'x': atom['coordinates'][0],
            'y': atom['coordinates'][1],
            'z': atom['coordinates'][2],
            'charge': atom['charge']
        })

    return pd.DataFrame(atoms)

def apply_function_to_cube(cube_data, func):
    """
    Apply a function to the cube data values.

    Args:
        cube_data (dict): Dictionary with cube data from read_cube_file
        func (callable): Function to apply to values

    Returns:
        dict: New cube data with transformed values
    """
    # Create a copy of the input data
    new_cube_data = cube_data.copy()

    # Apply function to values
    new_cube_data['values'] = func(cube_data['values'])

    return new_cube_data

def save_plot(cube_data, output_path, plane='xy', index=None, cmap='viridis',
              include_atoms=True, contour=True):
    """
    Create and save a 2D slice plot from cube data.

    Args:
        cube_data (dict): Dictionary with cube data from read_cube_file
        output_path (str): Path to save the plot
        plane (str): Plane to plot ('xy', 'xz', or 'yz')
        index (int, optional): Index for the slice (if None, uses the middle)
        cmap (str): Colormap for the plot
        include_atoms (bool): Whether to include atom markers
        contour (bool): Whether to include contour lines
    """
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize

    # Get data
    values = cube_data['values']
    X, Y, Z = cube_data['grid']
    shape = values.shape

    # Determine slice
    if index is None:
        if plane == 'xy':
            index = shape[2] // 2
        elif plane == 'xz':
            index = shape[1] // 2
        elif plane == 'yz':
            index = shape[0] // 2

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot slice
    if plane == 'xy':
        data = values[:, :, index]
        x_coords = X[:, :, 0]
        y_coords = Y[:, :, 0]
        plt_x, plt_y = x_coords, y_coords
        title = f'XY Plane (Z={Z[0, 0, index]:.2f})'
        xlabel, ylabel = 'X', 'Y'
    elif plane == 'xz':
        data = values[:, index, :]
        x_coords = X[:, 0, :]
        z_coords = Z[:, 0, :]
        plt_x, plt_y = x_coords, z_coords
        title = f'XZ Plane (Y={Y[0, index, 0]:.2f})'
        xlabel, ylabel = 'X', 'Z'
    elif plane == 'yz':
        data = values[index, :, :]
        y_coords = Y[0, :, :]
        z_coords = Z[0, :, :]
        plt_x, plt_y = y_coords, z_coords
        title = f'YZ Plane (X={X[index, 0, 0]:.2f})'
        xlabel, ylabel = 'Y', 'Z'

    # Plot the data
    im = ax.pcolormesh(plt_x, plt_y, data, cmap=cmap,
                       norm=Normalize(vmin=data.min(), vmax=data.max()))

    # Add contour lines if requested
    if contour:
        levels = np.linspace(data.min(), data.max(), 10)
        cs = ax.contour(plt_x, plt_y, data, levels=levels, colors='k', alpha=0.5)
        ax.clabel(cs, inline=1, fontsize=8)

    # Add atom markers if requested
    if include_atoms and len(cube_data['atoms']) > 0:
        atom_df = get_atom_locations(cube_data)

        if plane == 'xy':
            # Filter atoms close to the z-plane
            z_val = Z[0, 0, index]
            close_atoms = atom_df[np.abs(atom_df['z'] - z_val) < 1.0]
            ax.scatter(close_atoms['x'], close_atoms['y'], c='r', s=50, marker='o')
            for _, atom in close_atoms.iterrows():
                ax.text(atom['x'], atom['y'], f"{int(atom['atomic_number'])}",
                        fontsize=8, ha='center', va='center')

        elif plane == 'xz':
            # Filter atoms close to the y-plane
            y_val = Y[0, index, 0]
            close_atoms = atom_df[np.abs(atom_df['y'] - y_val) < 1.0]
            ax.scatter(close_atoms['x'], close_atoms['z'], c='r', s=50, marker='o')
            for _, atom in close_atoms.iterrows():
                ax.text(atom['x'], atom['z'], f"{int(atom['atomic_number'])}",
                        fontsize=8, ha='center', va='center')

        elif plane == 'yz':
            # Filter atoms close to the x-plane
            x_val = X[index, 0, 0]
            close_atoms = atom_df[np.abs(atom_df['x'] - x_val) < 1.0]
            ax.scatter(close_atoms['y'], close_atoms['z'], c='r', s=50, marker='o')
            for _, atom in close_atoms.iterrows():
                ax.text(atom['y'], atom['z'], f"{int(atom['atomic_number'])}",
                        fontsize=8, ha='center', va='center')

    # Finalize plot
    plt.colorbar(im, ax=ax, label='Value')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_aspect('equal')

    # Save the plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

if __name__ == "__main__":
    # Test the cube file handling functions
    import sys
    from pathlib import Path

    # Setup logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Get test cube file path from command line or use default
    test_file = sys.argv[1] if len(sys.argv) > 1 else None

    if test_file and Path(test_file).exists():
        logging.info(f"Processing test cube file: {test_file}")

        # Read the cube file
        cube_data = read_cube_file(test_file)

        # Print basic information
        header = cube_data['header']
        logging.info(f"Cube file: {Path(test_file).name}")
        logging.info(f"Grid dimensions: {header['nx']} x {header['ny']} x {header['nz']}")
        logging.info(f"Number of atoms: {header['natoms']}")

        # Calculate and print statistics
        stats = calculate_statistics(cube_data)
        logging.info("Statistics:")
        for key, value in stats.items():
            logging.info(f"  {key}: {value}")

        # Convert to DataFrame
        df = to_dataframe(cube_data)
        logging.info(f"DataFrame shape: {df.shape}")

        # Create a test plot
        output_dir = Path("cube_test_output")
        output_dir.mkdir(exist_ok=True)

        # Create plots for different planes
        for plane in ['xy', 'xz', 'yz']:
            plot_file = output_dir / f"{Path(test_file).stem}_{plane}_plot.png"
            save_plot(cube_data, plot_file, plane=plane)
            logging.info(f"Saved plot: {plot_file}")

        # Test writing a modified cube file
        modified_cube = apply_function_to_cube(cube_data, lambda x: x * 2.0)
        write_file = output_dir / f"{Path(test_file).stem}_modified.cube"
        write_cube_file(write_file,
                       modified_cube['header'],
                       modified_cube['atoms'],
                       modified_cube['values'])
        logging.info(f"Saved modified cube file: {write_file}")

    else:
        logging.warning("No test file provided or file does not exist")
        logging.info("Usage: python cube.py <path_to_cube_file>")