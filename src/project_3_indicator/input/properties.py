class Properties:
    """
    Class to manage property definitions and track which properties are active for a calculation.
    This class is independent of the database and manages properties in memory.
    """

    # Define standard property definitions as a class constant with metadata
    PROPERTY_MAPPING = {
        "density": {
            "display_name": "Density",
            "latex": r"\rho(\mathbf{r})",
            "aliases": ["density"],
            "electrons": 1,
            "description": "Electronic density at a point in space"
        },
        "on_top": {
            "display_name": "On-top Pair Density",
            "latex": r"\Pi(\mathbf{r})",
            "aliases": ["on top", "ontop", "ot", "on-top", "on_top"],
            "electrons": 1,
            "description": "On-top pair density"
        },
        "pair_density": {
            "display_name": "Pair Density",
            "latex": r"\rho_2(\mathbf{r}_1, \mathbf{r}_2)",
            "aliases": ["pair density", "pairdensity", "pd", "pair-density", "pair_density"],
            "electrons": 2,
            "description": "Electron pair density"
        },
        "I_D": {
            "display_name": "Indicator Dynamic",
            "latex": r"I_D(\mathbf{r})",
            "aliases": ["indicator dynamic", "ID", "dynamic", "id", "i_d"],
            "electrons": 1,
            "description": "Indicator dynamic property"
        },
        "pair_density_c1": {
            "display_name": "Pair Density C1",
            "latex": r"\rho_{2,C1}(\mathbf{r}_1, \mathbf{r}_2)",
            "aliases": ["pair density c1", "c1"],
            "electrons": 2,
            "description": "Pair density component C1"
        },
        "pair_density_c2": {
            "display_name": "Pair Density C2",
            "latex": r"\rho_{2,C2}(\mathbf{r}_1, \mathbf{r}_2)",
            "aliases": ["pair density c2", "c2"],
            "electrons": 2,
            "description": "Pair density component C2"
        },
        "pair_density_hf": {
            "display_name": "Pair Density HF",
            "latex": r"\rho_{2,HF}(\mathbf{r}_1, \mathbf{r}_2)",
            "aliases": ["pair density hf", "hf"],
            "electrons": 2,
            "description": "Hartree-Fock pair density"
        },
        "X(r)": {
            "display_name": "X(r)",
            "latex": r"X(\mathbf{r})",
            "aliases": ["xr", "x(r)", "truhlar", "on top ratio", "otr"],
            "electrons": 1,
            "description": "On-top ratio function (Truhlar)",
            "dependencies": ["on_top", "density"]
        }
    }

    def __init__(self, properties_list=None):
        """
        Initialize the Properties class with a list of property strings.

        Args:
            properties_list (list): List of property strings to process
        """
        self.raw_properties = properties_list or []
        self.cleaned_properties = {}
        self._initialize_properties()
        self._process_properties()
        self.names = list(self.cleaned_properties.keys())

    def _initialize_properties(self):
        """
        Initialize all standard properties as False.
        """
        for key in self.PROPERTY_MAPPING.keys():
            self.cleaned_properties[key] = False

    def _process_properties(self):
        """
        Process the raw properties list to clean and standardize property names.
        """
        # Match raw properties to standardized names
        for raw_property in self.raw_properties:
            if not isinstance(raw_property, str):
                continue  # Skip non-string properties

            cleaned_property = raw_property.strip().lower()
            for standard_name, property_info in self.PROPERTY_MAPPING.items():
                if cleaned_property in property_info["aliases"]:
                    self.cleaned_properties[standard_name] = True
                    break

        # Apply property dependencies
        self._apply_dependencies()

    def _apply_dependencies(self):
        """
        Apply interdependencies between properties.
        """
        # Check dependencies for all active properties
        for property_name, property_info in self.PROPERTY_MAPPING.items():
            # Skip if this property isn't active
            if not self.cleaned_properties.get(property_name, False):
                continue

            # If property has dependencies, activate them
            if "dependencies" in property_info:
                for dependency in property_info["dependencies"]:
                    self.cleaned_properties[dependency] = True

    def add_property(self, property_name):
        """
        Add a new property to the existing properties.

        Args:
            property_name (str): The property to add

        Returns:
            bool: True if property was added, False otherwise
        """
        if not isinstance(property_name, str):
            return False

        self.raw_properties.append(property_name)

        # Process this property
        cleaned = property_name.strip().lower()
        added = False

        for standard_name, property_info in self.PROPERTY_MAPPING.items():
            if cleaned in property_info["aliases"]:
                self.cleaned_properties[standard_name] = True
                added = True
                break

        if added:
            self._apply_dependencies()
            self.names = list(self.cleaned_properties.keys())
            return True

        return False  # Property not recognized

    def remove_property(self, property_name):
        """
        Remove a property if it exists.

        Args:
            property_name (str): The property to remove

        Returns:
            bool: True if property was removed, False otherwise
        """
        # Find the standard name for this property
        standard_name = None
        cleaned = property_name.strip().lower()

        for std_name, property_info in self.PROPERTY_MAPPING.items():
            if cleaned == std_name.lower() or cleaned in property_info["aliases"]:
                standard_name = std_name
                break

        if standard_name and standard_name in self.cleaned_properties:
            # Mark property as inactive
            self.cleaned_properties[standard_name] = False

            # Try to remove from raw properties too
            for idx, raw_prop in enumerate(self.raw_properties):
                if raw_prop.strip().lower() == cleaned:
                    self.raw_properties.pop(idx)
                    break

            # Update names list
            self.names = list(self.cleaned_properties.keys())
            return True

        return False

    def get_active_properties(self):
        """
        Return a list of active property names.

        Returns:
            list: List of active property standard names
        """
        return [key for key, value in self.cleaned_properties.items() if value]

    def get_property_info(self, property_name):
        """
        Get metadata about a specific property.

        Args:
            property_name (str): Name of the property

        Returns:
            dict: Property metadata or None if not found
        """
        # Try direct lookup first
        if property_name in self.PROPERTY_MAPPING:
            return self.PROPERTY_MAPPING[property_name]

        # Try to find by alias
        cleaned = property_name.strip().lower()
        for std_name, property_info in self.PROPERTY_MAPPING.items():
            if cleaned in property_info["aliases"]:
                return property_info

        return None

    def generate_properties_string(self, format_type="default"):
        """
        Generate a string of properties that are set to True.

        Args:
            format_type (str): The format style ("default" or "title_case")

        Returns:
            str: Formatted string of active properties
        """
        active_properties = self.get_active_properties()

        if not active_properties:
            return "$Properties\nNone"

        if format_type == "title_case":
            formatted_props = [name.replace("_", " ").title() for name in active_properties]
        else:
            formatted_props = active_properties

        return "$Properties\n" + "\n".join(formatted_props)

    def __str__(self):
        """
        String representation showing active properties.
        """
        active_props = self.get_active_properties()
        if not active_props:
            return "No active properties"
        return ', '.join(active_props)

    def __repr__(self):
        """
        Detailed representation of the Properties object.
        """
        return f"Properties(active={self.get_active_properties()})"


# Example usage
if __name__ == "__main__":
    properties_list = [
        "density", "on top", "pair density", "indicator dynamic",
        "c1", "c2", "hf"
    ]

    # Create Properties object
    props = Properties(properties_list)
    print("Active properties:", props)
    print("\nFormatted properties string:")
    print(props.generate_properties_string(format_type="title_case"))

    # Test adding a property
    print("\nAdding 'X(r)':")
    props.add_property("X(r)")
    print("Updated properties:", props)

    # Test removing a property
    print("\nRemoving 'pair_density':")
    props.remove_property("pair density")
    print("Updated properties:", props)