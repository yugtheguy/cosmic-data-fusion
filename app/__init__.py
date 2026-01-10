"""
COSMIC Data Fusion - Astronomical Data Standardization Backend

A research-grade FastAPI backend for ingesting astronomical data
from various catalogs and coordinate frames, standardizing to ICRS J2000.

Architecture:
    api/        - FastAPI route handlers (no business logic)
    services/   - Business logic (astronomy, ingestion, search)
    repository/ - Database queries (SQLAlchemy ORM)
    models.py   - SQLAlchemy ORM models
    schemas.py  - Pydantic validation schemas
    database.py - Database configuration
    main.py     - Application entry point
"""

__version__ = "1.0.0"
