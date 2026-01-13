"""
Query Builder Service for COSMIC Data Fusion.

Provides dynamic query construction for filtering star catalog data.
This module is READ-ONLY and does not modify any database records.

The QueryBuilder class constructs SQLAlchemy queries based on optional
filter parameters, allowing flexible searches across the unified catalog.

Phase: 3 - Query & Export Engine
"""

import logging
from typing import Optional
from dataclasses import dataclass

from sqlalchemy.orm import Session, Query

from app.models import UnifiedStarCatalog

logger = logging.getLogger(__name__)


@dataclass
class QueryFilters:
    """
    Filter parameters for querying the star catalog.
    
    All fields are optional - only non-None values will be applied as filters.
    This allows flexible queries from simple (e.g., just magnitude range)
    to complex (combining spatial, photometric, and source filters).
    
    Attributes:
        min_mag: Minimum magnitude (brightest limit, lower values = brighter)
        max_mag: Maximum magnitude (faintest limit)
        min_parallax: Minimum parallax in milliarcseconds (closest stars)
        max_parallax: Maximum parallax in milliarcseconds (farthest stars)
        ra_min: Minimum Right Ascension in degrees [0, 360)
        ra_max: Maximum Right Ascension in degrees [0, 360)
        dec_min: Minimum Declination in degrees [-90, +90]
        dec_max: Maximum Declination in degrees [-90, +90]
        original_source: Filter by source catalog (e.g., "Gaia DR3")
        limit: Maximum number of results (default 1000)
        offset: Number of results to skip (for pagination)
    """
    min_mag: Optional[float] = None
    max_mag: Optional[float] = None
    min_parallax: Optional[float] = None
    max_parallax: Optional[float] = None
    ra_min: Optional[float] = None
    ra_max: Optional[float] = None
    dec_min: Optional[float] = None
    dec_max: Optional[float] = None
    original_source: Optional[str] = None
    limit: int = 1000
    offset: int = 0


class QueryBuilder:
    """
    Dynamic query builder for the UnifiedStarCatalog.
    
    This class constructs SQLAlchemy Query objects based on optional filters.
    It follows the builder pattern, adding filters only when values are provided.
    
    Key Design Decisions:
    ---------------------
    1. READ-ONLY: This class only builds SELECT queries, never modifies data.
    2. Lazy Execution: Returns Query object without calling .all(), allowing
       the caller to add pagination or further modifications.
    3. Optional Filters: All filters are optional, enabling flexible queries.
    4. Logging: All filter applications are logged for debugging.
    
    Usage:
        builder = QueryBuilder(db_session)
        filters = QueryFilters(min_mag=5.0, max_mag=10.0, original_source="Gaia DR3")
        query = builder.build_query(filters)
        results = query.all()  # Execute when ready
    """
    
    def __init__(self, db: Session):
        """
        Initialize the QueryBuilder.
        
        Args:
            db: SQLAlchemy database session (read-only operations)
        """
        self.db = db
    
    def build_query(self, filters: QueryFilters) -> Query:
        """
        Build a SQLAlchemy query with dynamic filters.
        
        This method constructs a query by:
        1. Starting with a base query on UnifiedStarCatalog
        2. Adding each filter only if its value is not None
        3. Returning the Query object (not executed yet)
        
        Args:
            filters: QueryFilters dataclass with optional filter values
            
        Returns:
            SQLAlchemy Query object (call .all() to execute)
            
        Note:
            The returned Query can be further modified (e.g., .limit(), .offset())
            before execution.
        """
        logger.info("Building query with filters...")
        
        # Start with base query
        query = self.db.query(UnifiedStarCatalog)
        filters_applied = []
        
        # =====================================================================
        # MAGNITUDE FILTERS (Brightness)
        # Note: Lower magnitude = brighter star (astronomical convention)
        # =====================================================================
        if filters.min_mag is not None:
            query = query.filter(UnifiedStarCatalog.brightness_mag >= filters.min_mag)
            filters_applied.append(f"mag >= {filters.min_mag}")
        
        if filters.max_mag is not None:
            query = query.filter(UnifiedStarCatalog.brightness_mag <= filters.max_mag)
            filters_applied.append(f"mag <= {filters.max_mag}")
        
        # =====================================================================
        # PARALLAX FILTERS (Distance proxy)
        # Higher parallax = closer star (parallax is inverse of distance)
        # =====================================================================
        if filters.min_parallax is not None:
            query = query.filter(UnifiedStarCatalog.parallax_mas >= filters.min_parallax)
            filters_applied.append(f"parallax >= {filters.min_parallax} mas")
        
        if filters.max_parallax is not None:
            query = query.filter(UnifiedStarCatalog.parallax_mas <= filters.max_parallax)
            filters_applied.append(f"parallax <= {filters.max_parallax} mas")
        
        # =====================================================================
        # SPATIAL FILTERS (Bounding Box)
        # RA: Right Ascension [0, 360) degrees
        # Dec: Declination [-90, +90] degrees
        # =====================================================================
        if filters.ra_min is not None:
            query = query.filter(UnifiedStarCatalog.ra_deg >= filters.ra_min)
            filters_applied.append(f"RA >= {filters.ra_min}°")
        
        if filters.ra_max is not None:
            query = query.filter(UnifiedStarCatalog.ra_deg <= filters.ra_max)
            filters_applied.append(f"RA <= {filters.ra_max}°")
        
        if filters.dec_min is not None:
            query = query.filter(UnifiedStarCatalog.dec_deg >= filters.dec_min)
            filters_applied.append(f"Dec >= {filters.dec_min}°")
        
        if filters.dec_max is not None:
            query = query.filter(UnifiedStarCatalog.dec_deg <= filters.dec_max)
            filters_applied.append(f"Dec <= {filters.dec_max}°")
        
        # =====================================================================
        # SOURCE FILTER
        # Filter by original catalog (e.g., "Gaia DR3", "SDSS", etc.)
        # =====================================================================
        if filters.original_source is not None:
            query = query.filter(
                UnifiedStarCatalog.original_source == filters.original_source
            )
            filters_applied.append(f"source = '{filters.original_source}'")
        
        # =====================================================================
        # PAGINATION
        # Apply limit and offset for paginated results
        # =====================================================================
        if filters.offset > 0:
            query = query.offset(filters.offset)
            filters_applied.append(f"offset = {filters.offset}")
        
        if filters.limit > 0:
            query = query.limit(filters.limit)
            filters_applied.append(f"limit = {filters.limit}")
        
        # Log applied filters
        if filters_applied:
            logger.info(f"Filters applied: {', '.join(filters_applied)}")
        else:
            logger.info("No filters applied (returning all records up to limit)")
        
        return query
    
    def count_results(self, filters: QueryFilters) -> int:
        """
        Count the number of results matching the filters (without pagination).
        
        Useful for displaying "Showing 1-100 of 5,432 results".
        
        Args:
            filters: QueryFilters dataclass (limit/offset ignored for count)
            
        Returns:
            Total count of matching records
        """
        # Create a copy of filters without pagination
        count_filters = QueryFilters(
            min_mag=filters.min_mag,
            max_mag=filters.max_mag,
            min_parallax=filters.min_parallax,
            max_parallax=filters.max_parallax,
            ra_min=filters.ra_min,
            ra_max=filters.ra_max,
            dec_min=filters.dec_min,
            dec_max=filters.dec_max,
            original_source=filters.original_source,
            limit=0,  # No limit for count
            offset=0
        )
        
        # Build query without limit/offset and count
        query = self.db.query(UnifiedStarCatalog)
        
        # Apply same filters (copy the filter logic, excluding limit/offset)
        if count_filters.min_mag is not None:
            query = query.filter(UnifiedStarCatalog.brightness_mag >= count_filters.min_mag)
        if count_filters.max_mag is not None:
            query = query.filter(UnifiedStarCatalog.brightness_mag <= count_filters.max_mag)
        if count_filters.min_parallax is not None:
            query = query.filter(UnifiedStarCatalog.parallax_mas >= count_filters.min_parallax)
        if count_filters.max_parallax is not None:
            query = query.filter(UnifiedStarCatalog.parallax_mas <= count_filters.max_parallax)
        if count_filters.ra_min is not None:
            query = query.filter(UnifiedStarCatalog.ra_deg >= count_filters.ra_min)
        if count_filters.ra_max is not None:
            query = query.filter(UnifiedStarCatalog.ra_deg <= count_filters.ra_max)
        if count_filters.dec_min is not None:
            query = query.filter(UnifiedStarCatalog.dec_deg >= count_filters.dec_min)
        if count_filters.dec_max is not None:
            query = query.filter(UnifiedStarCatalog.dec_deg <= count_filters.dec_max)
        if count_filters.original_source is not None:
            query = query.filter(UnifiedStarCatalog.original_source == count_filters.original_source)
        
        return query.count()
