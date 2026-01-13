"""
Data source adapters for COSMIC Data Fusion.

Provides adapters for ingesting data from various astronomical catalogs.
"""

from .base_adapter import BaseAdapter, ValidationResult

__all__ = ["BaseAdapter", "ValidationResult"]
