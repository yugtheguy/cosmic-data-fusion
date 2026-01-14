"""
Search service for COSMIC Data Fusion.

Provides astronomical search capabilities:
- Bounding box search (rectangular region)
- Cone search (circular region with proper spherical geometry)
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import UnifiedStarCatalog
from app.repository.star_catalog import StarCatalogRepository
from app.services.standardizer import CoordinateStandardizer

logger = logging.getLogger(__name__)


class SearchService:
    """
    Service for searching the unified star catalog.
    
    Provides both simple rectangular searches and proper cone searches
    with spherical geometry handled by Astropy.
    """
    
    def __init__(self, db: Session):
        """
        Initialize search service.
        
        Args:
            db: SQLAlchemy session for database operations
        """
        self.repository = StarCatalogRepository(db)
        self.standardizer = CoordinateStandardizer()
    
    def get_star_by_id(self, star_id: int) -> Optional[UnifiedStarCatalog]:
        """
        Get a single star by its database ID.
        
        Args:
            star_id: The database ID of the star
            
        Returns:
            UnifiedStarCatalog instance or None if not found
        """
        logger.info(f"Fetching star with ID: {star_id}")
        return self.repository.get_by_id(star_id)
    
    def search_bounding_box(
        self,
        ra_min: float,
        ra_max: float,
        dec_min: float,
        dec_max: float,
        limit: int = 1000
    ) -> List[UnifiedStarCatalog]:
        """
        Search stars within a rectangular bounding box.
        
        Simple filter on RA/Dec ranges. Efficient for regions
        away from RA=0° boundary and poles.
        
        Args:
            ra_min: Minimum RA in degrees (ICRS)
            ra_max: Maximum RA in degrees (ICRS)
            dec_min: Minimum Dec in degrees (ICRS)
            dec_max: Maximum Dec in degrees (ICRS)
            limit: Maximum results
            
        Returns:
            List of matching UnifiedStarCatalog records
        """
        logger.info(
            f"Bounding box search: RA[{ra_min:.2f}°, {ra_max:.2f}°], "
            f"Dec[{dec_min:.2f}°, {dec_max:.2f}°], limit={limit}"
        )
        
        results = self.repository.search_bounding_box(
            ra_min=ra_min,
            ra_max=ra_max,
            dec_min=dec_min,
            dec_max=dec_max,
            limit=limit
        )
        
        logger.info(f"Bounding box search returned {len(results)} stars")
        return results
    
    def search_cone(
        self,
        ra: float,
        dec: float,
        radius: float,
        limit: int = 1000
    ) -> List[UnifiedStarCatalog]:
        """
        Search stars within a circular region (cone search).
        
        Implementation:
        1. Calculate bounding box for the cone (pre-filter)
        2. Query database for candidates using indexed columns
        3. Filter candidates by exact angular separation using Astropy
        
        This two-stage approach leverages the database index while
        ensuring correct spherical geometry for the final filter.
        
        Args:
            ra: Center RA in degrees (ICRS)
            dec: Center Dec in degrees (ICRS)
            radius: Search radius in degrees
            limit: Maximum results
            
        Returns:
            List of matching UnifiedStarCatalog records, sorted by
            distance from search center
            
        Astronomy Note:
            The angular separation calculation uses Astropy's SkyCoord
            which properly handles the cos(dec) factor and pole regions.
        """
        logger.info(
            f"Cone search: center=({ra:.4f}°, {dec:.4f}°), "
            f"radius={radius:.4f}°, limit={limit}"
        )
        
        # Step 1: Calculate bounding box for pre-filtering
        # This is a conservative bound to catch all possible matches
        ra_min, ra_max, dec_min, dec_max = \
            self.standardizer.calculate_bounding_box_for_cone(ra, dec, radius)
        
        logger.debug(
            f"Cone bounding box: RA[{ra_min:.2f}°, {ra_max:.2f}°], "
            f"Dec[{dec_min:.2f}°, {dec_max:.2f}°]"
        )
        
        # Step 2: Get candidates from database (uses index)
        # Request more candidates than limit since some will be filtered out
        candidates = self.repository.search_bounding_box_for_cone(
            ra_min=ra_min,
            ra_max=ra_max,
            dec_min=dec_min,
            dec_max=dec_max,
            limit=limit * 2  # Over-fetch to account for filtering
        )
        
        logger.debug(f"Retrieved {len(candidates)} candidates for cone filtering")
        
        # Step 3: Filter by exact angular separation
        # This uses Astropy's spherical geometry calculations
        results_with_distance: List[tuple] = []
        
        for star in candidates:
            separation = self.standardizer.calculate_angular_separation(
                ra1=ra,
                dec1=dec,
                ra2=star.ra_deg,
                dec2=star.dec_deg
            )
            
            if separation <= radius:
                results_with_distance.append((star, separation))
        
        # Sort by distance from center
        results_with_distance.sort(key=lambda x: x[1])
        
        # Apply limit and extract stars
        results = [star for star, _ in results_with_distance[:limit]]
        
        logger.info(
            f"Cone search returned {len(results)} stars "
            f"(from {len(candidates)} candidates)"
        )
        
        return results
