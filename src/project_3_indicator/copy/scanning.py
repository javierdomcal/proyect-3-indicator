class ScanningProperties:
    def __init__(self, molecule, scan_props=None):
        self.molecule = molecule
        self.atom_indices = None
        self.directions = None
        self.end_distance = 3.0
        self.step_size = 0.05

        self.set_default_values()
        if scan_props is not None:
            self.update_values_from_dict(scan_props)

    def set_default_values(self):
        if self.molecule.molecule_type == "atom":
            self.atom_indices = "1"
            self.directions = "z"
        else:
            non_hydrogen_indices = self.get_non_hydrogen_indices()

            if self.molecule.molecule_type == "diatomic":
                self.atom_indices = non_hydrogen_indices[0]
                self.directions = "y,z"
            elif self.molecule.molecule_type == "planar":
                self.atom_indices = ",".join(non_hydrogen_indices[:len(non_hydrogen_indices)//2])
                self.directions = "y,z"
            else:
                self.atom_indices = ",".join(non_hydrogen_indices)
                self.directions = "x,y,z"

    def update_values_from_dict(self, scan_props):
        if "atom_indices" in scan_props:
            self.atom_indices = scan_props["atom_indices"]
        if "directions" in scan_props:
            self.directions = scan_props["directions"]
        if "end_distance" in scan_props:
            self.end_distance = scan_props["end_distance"]
        if "step_size" in scan_props:
            self.step_size = scan_props["step_size"]

    def get_non_hydrogen_indices(self):
        if not self.molecule.geometry:
            return []

        non_hydrogen_indices = []
        lines = self.molecule.geometry.strip().split("\n")
        for i, line in enumerate(lines, 1):
            if line.strip() and not line.strip().startswith("H "):
                non_hydrogen_indices.append(str(i))

        if not non_hydrogen_indices:
            # If only hydrogens, consider the first half
            non_hydrogen_indices = [str(i) for i in range(1, len(lines)//2 + 1)]

        return non_hydrogen_indices

    def __str__(self):
        return f"{self.atom_indices} {self.directions} {self.end_distance} {self.step_size}"