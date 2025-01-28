"""
Handles hash generation and management for flux calculations.
"""

import hashlib
import json
import logging
import os


class FluxHasher:
    """Handles creation and validation of flux calculation hashes."""

    STORAGE_DIR = os.path.join("utils", "storage")
    REGISTRY_FILE = os.path.join("utils", "storage", "registry.json")

    @staticmethod
    def generate_flux_hash(input_spec, flux_type="correlation"):
        """
        Generate a unique hash for a flux calculation.

        Args:
            input_spec: InputSpecification instance
            flux_type: Type of flux calculation

        Returns:
            str: 8-character hash identifier
        """
        try:
            params = {
                "molecule": {
                    "name": input_spec.molecule.name,
                    "charge": input_spec.molecule.charge,
                    "multiplicity": input_spec.molecule.multiplicity,
                    "omega": input_spec.molecule.omega,
                },
                "method": {
                    "name": input_spec.method.method_name,
                    "is_casscf": input_spec.method.is_casscf,
                    "n": input_spec.method.n,
                    "m": input_spec.method.m,
                },
                "basis": {
                    "name": input_spec.basis.basis_name,
                    "omega": input_spec.basis.omega,
                    "is_even_tempered": input_spec.basis.is_even_tempered,
                },
                "config": input_spec.config,
                "flux_type": flux_type,
            }

            param_str = json.dumps(params, sort_keys=True)
            hash_obj = hashlib.sha256(param_str.encode())
            hash_str = hash_obj.hexdigest()[:8]  # Just 8 characters

            logging.info(f"Generated hash {hash_str} for {input_spec.title}")
            return hash_str

        except Exception as e:
            logging.error(f"Error generating flux hash: {e}")
            raise

    @staticmethod
    def store_hash_info(hash_str, input_spec, flux_type="correlation"):
        """Store hash mapping information in registry."""
        try:
            # Create storage directory if it doesn't exist
            os.makedirs(os.path.dirname(FluxHasher.REGISTRY_FILE), exist_ok=True)

            # Load existing registry
            registry = {}
            if os.path.exists(FluxHasher.REGISTRY_FILE):
                with open(FluxHasher.REGISTRY_FILE, "r") as f:
                    registry = json.load(f)

            # Create readable description
            description = {
                "molecule": input_spec.molecule.name,
                "method": input_spec.method.method_name,
                "basis": input_spec.basis.basis_name,
                "flux_type": flux_type,
                "details": {
                    "charge": input_spec.molecule.charge,
                    "multiplicity": input_spec.molecule.multiplicity,
                    "configuration": input_spec.config,
                    "is_even_tempered": input_spec.basis.is_even_tempered,
                },
            }

            if input_spec.method.is_casscf:
                description[
                    "method"
                ] = f"CASSCF({input_spec.method.n},{input_spec.method.m})"

            if input_spec.basis.omega is not None:
                description["details"]["basis_omega"] = input_spec.basis.omega

            if input_spec.molecule.omega is not None:
                description["details"]["molecule_omega"] = input_spec.molecule.omega

            # Store in registry
            registry[hash_str] = description

            # Save updated registry
            with open(FluxHasher.REGISTRY_FILE, "w") as f:
                json.dump(registry, f, indent=2, sort_keys=True)

            logging.info(f"Stored info for hash {hash_str} in registry")

        except Exception as e:
            logging.error(f"Error storing hash info: {e}")
            raise

    @staticmethod
    def get_hash_info(hash_str):
        """Get information about a calculation from its hash."""
        try:
            if not os.path.exists(FluxHasher.REGISTRY_FILE):
                raise FileNotFoundError("Registry file not found")

            with open(FluxHasher.REGISTRY_FILE, "r") as f:
                registry = json.load(f)

            if hash_str not in registry:
                raise KeyError(f"Hash {hash_str} not found in registry")

            return registry[hash_str]

        except Exception as e:
            logging.error(f"Error retrieving hash info: {e}")
            raise

    @staticmethod
    def get_storage_path(hash_str):
        """Get the storage path for a job."""
        return os.path.join(FluxHasher.STORAGE_DIR, hash_str)
