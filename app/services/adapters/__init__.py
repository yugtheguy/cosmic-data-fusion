"""
Data source adapters for COSMIC Data Fusion.

Provides adapters for ingesting data from various astronomical catalogs.
"""

from .base_adapter import BaseAdapter, ValidationResult
from .gaia_adapter import GaiaAdapter
from .sdss_adapter import SDSSAdapter
from .fits_adapter import FITSAdapter
from .csv_adapter import CSVAdapter

__all__ = [
    "BaseAdapter",
    "ValidationResult",
    "GaiaAdapter",
    "SDSSAdapter",
    "FITSAdapter",
    "CSVAdapter"
]
