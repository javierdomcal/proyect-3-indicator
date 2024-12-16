import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def read_dat_file(filepath):
    """
    Read .dat file with proper error handling
    """
    try:
        # Read all lines first
        with open(filepath, "r") as f:
            lines = f.readlines()

        # Process first line to determine format
        first_line = [x.strip() for x in lines[2].strip().split(",")]
        is_4_column = len(first_line) == 4

        # Process lines and convert to DataFrame
        data = []
        for line in lines:
            # Remove extra whitespace and split by comma
            values = [x.strip() for x in line.strip().split(",")]
            if len(values) < 4 or len(values) > 5:  # Skip malformed lines
                continue

            try:
                # Convert scientific notation and floats
                row = [float(x.replace("E", "e")) for x in values]
                if is_4_column:
                    # Insert 0 for z coordinate
                    row.insert(2, 0.0)
                data.append(row)
            except ValueError:
                continue

        # Create DataFrame
        df = pd.DataFrame(data, columns=["x", "y", "z", "ontop", "density"])

        # Filter out rows where columns 1 and 2 are zero
        df = df[(abs(df["y"]) < 1e-10) & (abs(df["z"]) < 1e-10)]
        df["x"] = df["x"] * 0.529177

        # Check if we have any data left after filtering
        if df.empty:
            print(f"Warning: No valid data in {filepath} after filtering")
            return None

        return df
    except Exception as e:
        print(f"Error reading {filepath}: {str(e)}")
        return None


def plot_basis_results(folder_path="./basis-results-temporal"):
    # Create figure
    plt.figure(figsize=(10, 6))

    # Ensure folder exists
    if not os.path.exists(folder_path):
        print(f"Error: Folder {folder_path} does not exist")
        return

    # Track if we successfully plotted any data
    plotted_any = False

    # Read all .dat files
    for filepath in Path(folder_path).glob("*.dat"):
        try:
            # Read file
            df = read_dat_file(filepath)
            if df is None:
                continue

            # Calculate indicator
            df["indicator"] = (2 * df["ontop"]) / (df["density"] ** 2)

            # Plot with filename (without .dat) as label
            label = filepath.stem  # Gets filename without extension
            plt.plot(df["x"], df["indicator"], label=label)  # Using column 2 for x-axis
            plotted_any = True

            print(f"Successfully processed {filepath.name}")

        except Exception as e:
            print(f"Error processing {filepath.name}: {str(e)}")
            continue

    if not plotted_any:
        print("No valid data files were processed")
        return

    # Customize plot
    plt.xlabel("x")
    plt.ylabel("Indicator")
    plt.title("Basis Results Comparison")
    plt.legend()
    plt.grid(True)

    # Show plot
    plt.show()


if __name__ == "__main__":
    plot_basis_results()
