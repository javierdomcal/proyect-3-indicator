class Dimension:
    def __init__(self, origin=None, max=None, step_size=None):
        """
        Initialize the Dimension object with origin, max and step_size.
        If no input is provided, defaults will be set by the Grid class.
        """
        self.origin = origin
        self.max = max
        self.step_size = step_size

class Grid:
    def __init__(self, grid_input=None, molecule=None):
        """
        Initialize the Grid object based on the input dictionary.
        If no input is provided, default to max=2.0 and step_size=0.05 for all dimensions.
        """
        default_step = 0.05
        default_max = 2.0
        default_origin = -default_max

        self.x = Dimension(default_origin, default_max, default_step)
        self.y = Dimension(default_origin, default_max, default_step)
        self.z = Dimension(default_origin, default_max, default_step)

        print(f"Molecule: {molecule}")
        if molecule:
            self.from_molecule(molecule)

        self.grid_input = grid_input or {}

        if grid_input:
            self._parse_dimension('x')
            self._parse_dimension('y')
            self._parse_dimension('z')

    def _parse_dimension(self, dim):
        """
        Parse a single dimension from the input dictionary.
        Updates the corresponding dimension object.
        """
        # Get the dimension object
        dimension = getattr(self, dim)

        if dim in self.grid_input:
            values = self.grid_input[dim]
            print(values)
            len_values = len(values) if (isinstance(values, list) or isinstance(values, tuple)) else 1

            if len_values == 0:
                pass  # Keep default values
            elif len_values == 1:
                                # Set max to the provided value
                dimension.max = values
                # Set origin to -max unless a molecule has set it to 0
                if abs(dimension.origin) < 0.00001:  # If origin was already explicitly set to 0
                    pass  # Keep it at 0
                else:
                    dimension.origin = - dimension.max

            elif len_values == 2:
                dimension.max = values[0]

                # Set origin to -max unless a molecule has set it to 0
                if abs(dimension.origin) < 0.00001:  # If origin was already explicitly set to 0
                    pass  # Keep it at 0
                else:
                    dimension.origin = -dimension.max
                dimension.step_size = values[1]
            elif len_values == 3:
                dimension.origin = values[0]
                dimension.max = values[1]
                dimension.step_size = values[2]
            else:
                raise ValueError(f"Invalid number of values for dimension '{dim}': {len_values}. Expected 1, 2, or 3.")
        elif not self.grid_input:
            pass  # Keep default values


    def to_string(self):
        """
        Build the string representation of the grid in the format:
        $Grid
        origin_x max_x step_x
        origin_y max_y step_y
        origin_z max_z step_z
        """
        return f"$Grid\n{self.x.origin} {self.x.max} {self.x.step_size}\n{self.y.origin} {self.y.max} {self.y.step_size}\n{self.z.origin} {self.z.max} {self.z.step_size}\n"

    def from_molecule(self, molecule):
        """
        Create a Grid object based on the molecule's geometry.
        If the molecule is atomic, only calculate in the z direction.
        If the molecule is linear, calculate in x and z directions.
        Otherwise, calculate in all three directions.
        """
        label = molecule.classify_molecule()
        print(f"Grid: {label} molecule")
        if label == 'atom':
            self.x.origin = 0.0
            self.x.max = 0.0
            self.x.step_size = 0.0
            self.y.origin = 0.0
            self.y.max = 0.0
            self.y.step_size = 0.0
            self.z.origin = 0.0
        elif label == 'linear':
            self.x.origin = 0.0
            self.y.origin = 0.0
            self.y.max = 0.0
            self.y.step_size = 0.0
        elif label == 'planar':
            self.x.origin = 0.0

    def calculate_default_from_geometry(self, molecule):
        """
        Calculate the default max size for each dimension based on the molecule's geometry.
        The max size is the maximum between (max_coordinate + 0.5) and the current max value.
        """
        geometry = molecule.get_geometry()
        max_x = max(atom[1] for atom in geometry)
        max_y = max(atom[2] for atom in geometry)
        max_z = max(atom[3] for atom in geometry)

        def calculate_max(value, label):
            return max((value + 0.5), label.max)

        self.x.max = calculate_max(max_x, self.x)
        self.y.max = calculate_max(max_y, self.y)
        self.z.max = calculate_max(max_z, self.z)