class Properties:
    """
    Class to manage property definitions and track which properties are active for a calculation.
    This class differentiates between calculated properties (that need to be passed to INCA)
    and derived properties (which are calculated from other properties).
    """

    # Define calculated properties (need to be passed to INCA)
    CALCULATED_PROPERTIES = {
        "density": {
            "display_name": "Density",
            "latex": r"\rho(\mathbf{r})",
            "aliases": ["density"],
            "electrons": 1,
            "description": "Electronic density at a point in space",
            "option": "total"
        },
        "on_top": {
            "display_name": "On-top Pair Density",
            "latex": r"\Pi(\mathbf{r})",
            "aliases": ["on top", "ontop", "ot", "on-top", "on_top"],
            "electrons": 1,
            "description": "On-top pair density",
            "option": "all"
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
            "aliases": ["pair density c1", "c1", "pair_density_c1"],
            "electrons": 2,
            "description": "Pair density component C1"
        },
        "pair_density_c2": {
            "display_name": "Pair Density C2",
            "latex": r"\rho_{2,C2}(\mathbf{r}_1, \mathbf{r}_2)",
            "aliases": ["pair density c2", "c2", "pair_density_c2"],
            "electrons": 2,
            "description": "Pair density component C2"
        },
        "pair_density_hf": {
            "display_name": "Pair Density HF",
            "latex": r"\rho_{2,HF}(\mathbf{r}_1, \mathbf{r}_2)",
            "aliases": ["pair density hf", "pair_density_hf"],
            "electrons": 2,
            "description": "Hartree-Fock pair density"
        },

        "pair_density_nucleus": {
            "display_name": "Pair Density Nucleus",
            "latex": r"\rho_{2}(\mathbf{r}_1, \emptyset)",
            "aliases": ["pair density nucleus", "nucleus", "pair_density_nucleus"],
            "electrons": 2,
            "description": "Pair density with one electron at nucleus",
            "option": "all"
        },

        "pair_density_nucleus_c1": {
            "display_name": "Pair Density Nucleus C1",
            "latex": r"\rho_{2,C1}(\mathbf{r}_1, \emptyset)",
            "aliases": ["pair density nucleus c1", "nucleus_c1", "pair_density_nucleus_c1"],
            "electrons": 2,
            "description": "Pair density C1 with one electron at nucleus",
            "option": "all"
        },

        "pair_density_nucleus_c2": {
            "display_name": "Pair Density Nucleus C2",
            "latex": r"\rho_{2,C2}(\mathbf{r}_1, \emptyset)",
            "aliases": ["pair density nucleus c2", "nucleus_c2", "pair_density_nucleus_c2"],
            "electrons": 2,
            "description": "Pair density C2 with one electron at nucleus",
            "option": "all"
    },

        "pair_density_nucleus_hf": {
            "display_name": "Pair Density Nucleus HF",
            "latex": r"\rho_{2,HF}(\mathbf{r}_1, \emptyset)",
            "aliases": ["pair density nucleus hf", "nucleus_hf", "pair_density_nucleus_hf"],
            "electrons": 2,
            "description": "Pair density HF with one electron at nucleus",
            "option": "all"
        },

        "intracule": {
            "display_name": "Intracule",
            "latex": r"\rho_2(\mathbf{r}_1, \mathbf{r}_2)",
            "aliases": ["intracule", "intracule density", "intracule_density"],
            "electrons": 2,
            "description": "Intracule density",
            "option": "all"
        },

        "intracule_c1": {
            "display_name": "Intracule C1",
            "latex": r"\rho_{2,C1}(\mathbf{r}_1, \mathbf{r}_2)",
            "aliases": ["intracule c1", "intracule_c1"],
            "electrons": 2,
            "description": "Intracule density component C1",
            "option": "all"
        },
        "intracule_c2": {
            "display_name": "Intracule C2",
            "latex": r"\rho_{2,C2}(\mathbf{r}_1, \mathbf{r}_2)",
            "aliases": ["intracule c2", "intracule_c2"],
            "electrons": 2,
            "description": "Intracule density component C2",
            "option": "all"
        },
        "intracule_hf": {
            "display_name": "Intracule HF",
            "latex": r"\rho_{2,HF}(\mathbf{r}_1, \mathbf{r}_2)",
            "aliases": ["intracule hf", "intracule_hf"],
            "electrons": 2,
            "description": "Intracule density HF",
            "option": "all"
        },
    }
    # Define derived properties (calculated from other properties)
    DERIVED_PROPERTIES = {
        "on_top_ratio": {
            "display_name": "X(r)",
            "latex": r"X(\mathbf{r})",
            "aliases": ["xr", "x(r)", "truhlar", "on top ratio", "otr"],
            "electrons": 1,
            "description": "On-top ratio function (Truhlar)",
            "dependencies": ["on_top", "density"],
            "formula": "2 * on_top / (density ** 2)"
        }
    }

    def __init__(self, properties_list=None):
        """
        Initialize the Properties class with a list of property strings.

        Args:
            properties_list (list): List of property strings to process
        """
        self.raw_properties = properties_list or []

        # Initialize properties dictionaries
        self.calculated_properties = {}
        self.derived_properties = {}

        # Initialize all properties as False
        self._initialize_properties()

        # Process the input properties list
        self._process_properties()

        # Combined property names for compatibility with existing code
        self.properties = {**self.calculated_properties, **self.derived_properties}
        self.names = list(self.properties.keys())

    def _initialize_properties(self):
        """
        Initialize all properties (both calculated and derived) as False.
        """
        for key in self.CALCULATED_PROPERTIES.keys():
            self.calculated_properties[key] = False

        for key in self.DERIVED_PROPERTIES.keys():
            self.derived_properties[key] = False

    def _process_properties(self):
        """
        Process the raw properties list to clean and standardize property names.
        Handles both calculated and derived properties.
        """
        # Process each property in the raw list
        for raw_property in self.raw_properties:
            print (raw_property)
            if not isinstance(raw_property, str):
                continue  # Skip non-string properties

            cleaned_property = raw_property.strip().lower()

            # Check if it's a calculated property
            property_found = False
            for standard_name, property_info in self.CALCULATED_PROPERTIES.items():
                if cleaned_property in property_info["aliases"]:
                    self.calculated_properties[standard_name] = True
                    property_found = True
                    break

            # If not found in calculated properties, check derived properties
            if not property_found:
                for standard_name, property_info in self.DERIVED_PROPERTIES.items():
                    if cleaned_property in property_info["aliases"]:
                        self.derived_properties[standard_name] = True
                        property_found = True
                        break

        # Apply dependencies (ensure properties needed for derived properties are activated)
        self._apply_dependencies()

    def _apply_dependencies(self):
        """
        Activate dependencies for derived properties.
        If a derived property is active, its dependencies must be activated as well.
        """
        # Check each derived property
        for property_name, is_active in self.derived_properties.items():
            if not is_active:
                continue  # Skip inactive properties

            # Get the property info
            property_info = self.DERIVED_PROPERTIES[property_name]

            # If it has dependencies, activate them in the calculated properties
            if "dependencies" in property_info:
                for dependency in property_info["dependencies"]:
                    if dependency in self.calculated_properties:
                        self.calculated_properties[dependency] = True
                    elif dependency in self.derived_properties:
                        self.derived_properties[dependency] = True
                        # Recursive dependency resolution
                        self._apply_dependencies()

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

        # Check calculated properties
        for standard_name, property_info in self.CALCULATED_PROPERTIES.items():
            if cleaned in property_info["aliases"]:
                self.calculated_properties[standard_name] = True
                added = True
                break

        # Check derived properties if not found
        if not added:
            for standard_name, property_info in self.DERIVED_PROPERTIES.items():
                if cleaned in property_info["aliases"]:
                    self.derived_properties[standard_name] = True
                    added = True
                    break

        if added:
            self._apply_dependencies()
            # Update the properties and names
            self.properties = {**self.calculated_properties, **self.derived_properties}
            self.names = list(self.properties.keys())
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
        property_type = None

        # Check in calculated properties
        for std_name, property_info in self.CALCULATED_PROPERTIES.items():
            if cleaned == std_name.lower() or cleaned in property_info["aliases"]:
                standard_name = std_name
                property_type = "calculated"
                break

        # Check in derived properties if not found
        if not standard_name:
            for std_name, property_info in self.DERIVED_PROPERTIES.items():
                if cleaned == std_name.lower() or cleaned in property_info["aliases"]:
                    standard_name = std_name
                    property_type = "derived"
                    break

        if standard_name:
            # Mark property as inactive in the appropriate dictionary
            if property_type == "calculated":
                self.calculated_properties[standard_name] = False
            else:
                self.derived_properties[standard_name] = False

            # Try to remove from raw properties too
            for idx, raw_prop in enumerate(self.raw_properties):
                if isinstance(raw_prop, str) and raw_prop.strip().lower() == cleaned:
                    self.raw_properties.pop(idx)
                    break

            # Update the properties and names
            self.properties = {**self.calculated_properties, **self.derived_properties}
            self.names = list(self.properties.keys())
            return True

        return False

    def get_active_properties(self):
        """
        Return a list of all active property names (both calculated and derived).

        Returns:
            list: List of active property standard names
        """
        active_properties = []

        # Add active calculated properties
        for key, value in self.calculated_properties.items():
            if value:
                active_properties.append(key)


        return active_properties

    def get_active_calculated_properties(self):
        """
        Return a list of active calculated properties (to be passed to INCA).

        Returns:
            list: List of active calculated property names
        """
        return [key for key, value in self.calculated_properties.items() if value]

    def get_active_derived_properties(self):
        """
        Return a list of active derived properties.

        Returns:
            list: List of active derived property names
        """
        return [key for key, value in self.derived_properties.items() if value]

    def get_property_info(self, property_name):
        """
        Get metadata about a specific property.

        Args:
            property_name (str): Name of the property

        Returns:
            dict: Property metadata or None if not found
        """
        # Try direct lookup in calculated properties
        if property_name in self.CALCULATED_PROPERTIES:
            return self.CALCULATED_PROPERTIES[property_name]

        # Try direct lookup in derived properties
        if property_name in self.DERIVED_PROPERTIES:
            return self.DERIVED_PROPERTIES[property_name]

        # Try to find by alias
        cleaned = property_name.strip().lower()

        # Check calculated properties
        for std_name, property_info in self.CALCULATED_PROPERTIES.items():
            if cleaned in property_info["aliases"]:
                return property_info

        # Check derived properties
        for std_name, property_info in self.DERIVED_PROPERTIES.items():
            if cleaned in property_info["aliases"]:
                return property_info

        return None

    def generate_properties_string(self):
        """
        Generate a string of calculated properties for INCA input.
        Only calculated properties are included since derived ones are calculated post-processing.

        Returns:
            str: Formatted string of active calculated properties for INCA
        """
        active_properties = self.get_active_calculated_properties()

        if not active_properties:
            return "$Properties\nNone\n"

        string = "$Properties\n" + str(len(active_properties)) + "\n"
        for property_name in active_properties:
            property_info = self.CALCULATED_PROPERTIES[property_name]
            option = property_info.get("option", "")
            string += f"{property_name} {option}\n"

        return string

    def __str__(self):
        """
        String representation showing all active properties.
        """
        active_props = self.get_active_properties()
        if not active_props:
            return "No active properties"
        return ', '.join(active_props)

    def __repr__(self):
        """
        Detailed representation of the Properties object.
        """
        return f"Properties(calculated={self.get_active_calculated_properties()}, derived={self.get_active_derived_properties()})"