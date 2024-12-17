# src/__init__.py
"""
Main package initialization.
Import core functionality here to provide a clean API.
"""
from .molecule import *
from .basis import *
from .method import *
from .job_manager import *
from .flux_manager import *

# Define package version
__version__ = '0.1.0'

# src/utils/__init__.py
"""
Utility functions and helper modules.
"""
from .logging_config import setup_logging
from .file_management import *

# tests/__init__.py
"""
Test package initialization.
Enable test discovery and shared test utilities.
"""