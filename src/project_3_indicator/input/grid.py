class Grid:
    def __init__(self, grid_input=None, molecule=None):
        """
        Initialize the Grid object based on the input dictionary.
        If no input is provided, default to max_size=1.0 and step_size=0.05 for all dimensions.
        """
        self.default_step = 0.05
        self.default_max = 1.0
        self.calculate_default_from_geometry(molecule)
        self.from_molecule(molecule)
        self.grid_input = grid_input or {}
        self.x = self._parse_dimension('x')
        self.y = self._parse_dimension('y')
        self.z = self._parse_dimension('z')

    def _parse_dimension(self, dim):
        """
        Parse a single dimension from the input dictionary.
        If the dimension is not provided, default to [0, 0] (no calculation).
        """
        if dim in self.grid_input:
            values = self.grid_input[dim]
            if len(values) == 1:
                return [values[0], self.default_step]
            return values
        elif not self.grid_input:
            return [self.default_max, self.default_step]
        return [0, 0]

    def to_string(self):
        """
        Build the string representation of the grid in the format:
        $Grid max_x step_x max_y step_y max_z step_z
        """
        return f"$Grid\n{self.x[0]} {self.x[1]}\n{self.y[0]} {self.y[1]}\n{self.z[0]} {self.z[1]}\n"

    def from_molecule(self, molecule):
        """
        Create a Grid object based on the molecule's geometry.
        If the molecule is atomic, only calculate in the z direction.
        If the molecule is linear, calculate in x and z directions.
        Otherwise, calculate in all three directions.
        """
        label = molecule.classify_molecule()
        if label == 'atom':
            self.x = [0.0, 0.0]
            self.y = [0.0, 0.0]
        elif label == 'linear':
            self.y = [0.0, 0.0]



    def calculate_default_from_geometry(self,molecule):
        """
        Calculate the default max size for each dimension based on the molecule's geometry.
        The max size is the maximum between (max_distance + 0.5) / 2 and 1.0.
        """
        geometry = molecule.get_geometry()
        max_x = max(atom[1] for atom in geometry)
        max_y = max(atom[2] for atom in geometry)
        max_z = max(atom[3] for atom in geometry)

        def calculate_max(value):
            return max((value + 0.5), self.default_max)


        self.x = [calculate_max(max_x), self.default_step]
        self.y = [calculate_max(max_y), self.default_step]
        self.z = [calculate_max(max_z), self.default_step]

