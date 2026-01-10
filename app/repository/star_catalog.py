"""
Repository layer for UnifiedStarCatalog database operations.

Contains all database queries using SQLAlchemy ORM.
NO raw SQL. NO business logic.
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import UnifiedStarCatalog

logger = logging.getLogger(__name__)


class StarCatalogRepository:
    """
    Repository for star catalog database operations.
    
    Provides clean interface for CRUD operations and queries.
    All methods use SQLAlchemy ORM, no raw SQL.
    """
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy session from FastAPI dependency injection
        """
        self.db = db
    
    def create(self, star_data: dict) -> UnifiedStarCatalog:
        """
        Create a single star record.
        
        Args:
            star_data: Dictionary with star attributes
            
        Returns:
            Created UnifiedStarCatalog instance
        """
        db_star = UnifiedStarCatalog(**star_data)
        self.db.add(db_star)
        self.db.commit()
        self.db.refresh(db_star)
        
        logger.debug(f"Created star record: {db_star.source_id}")
        return db_star
    
    def create_bulk(self, stars_data: List[dict]) -> List[UnifiedStarCatalog]:
        """
        Create multiple star records in a single transaction.
        
        Uses bulk insert for efficiency with thousands of records.
        
        Args:
            stars_data: List of dictionaries with star attributes
            
        Returns:
            List of created UnifiedStarCatalog instances
        """
        db_stars = [UnifiedStarCatalog(**data) for data in stars_data]
        
        self.db.add_all(db_stars)
        self.db.commit()
        
        # Refresh all to get generated IDs
        for star in db_stars:
            self.db.refresh(star)
        
        logger.info(f"Bulk created {len(db_stars)} star records")
        return db_stars
    
    def get_by_id(self, star_id: int) -> Optional[UnifiedStarCatalog]:
        """
        Retrieve a star by its database ID.
        
        Args:
            star_id: Primary key
            
        Returns:
            UnifiedStarCatalog or None if not found
        """
        return self.db.query(UnifiedStarCatalog).filter(
            UnifiedStarCatalog.id == star_id
        ).first()
    
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
        
        Uses the composite (ra_deg, dec_deg) index for efficiency.
        
        Args:
            ra_min: Minimum RA in degrees
            ra_max: Maximum RA in degrees
            dec_min: Minimum Dec in degrees
            dec_max: Maximum Dec in degrees
            limit: Maximum results to return
            
        Returns:
            List of matching stars
            
        Note:
            Does NOT handle RA wrap-around at 0°/360° boundary.
            For queries crossing RA=0°, split into two queries.
        """
        query = self.db.query(UnifiedStarCatalog).filter(
            UnifiedStarCatalog.ra_deg >= ra_min,
            UnifiedStarCatalog.ra_deg <= ra_max,
            UnifiedStarCatalog.dec_deg >= dec_min,
            UnifiedStarCatalog.dec_deg <= dec_max
        ).limit(limit)
        
        results = query.all()
        logger.debug(
            f"Bounding box search: RA[{ra_min:.2f}, {ra_max:.2f}], "
            f"Dec[{dec_min:.2f}, {dec_max:.2f}] -> {len(results)} results"
        )
        return results
    
    def search_bounding_box_for_cone(
        self,
        ra_min: float,
        ra_max: float,
        dec_min: float,
        dec_max: float,
        limit: int = 10000
    ) -> List[UnifiedStarCatalog]:
        """
        Pre-filter stars for cone search using bounding box.
        
        This is the first stage of cone search optimization:
        1. Use DB index to get candidates in bounding box
        2. Then filter by angular separation in Python
        
        Args:
            ra_min: Min RA (may be negative for wrap handling)
            ra_max: Max RA (may exceed 360 for wrap handling)
            dec_min: Min Dec clamped to -90
            dec_max: Max Dec clamped to +90
            limit: Max candidates to retrieve
            
        Returns:
            List of candidate stars for further filtering
        """
        # Handle RA wrap-around at 0°/360° boundary
        if ra_min < 0:
            # Query wraps around: (ra >= ra_min+360) OR (ra <= ra_max)
            query = self.db.query(UnifiedStarCatalog).filter(
                UnifiedStarCatalog.dec_deg >= dec_min,
                UnifiedStarCatalog.dec_deg <= dec_max
            ).filter(
                (UnifiedStarCatalog.ra_deg >= (ra_min + 360)) |
                (UnifiedStarCatalog.ra_deg <= ra_max)
            ).limit(limit)
        elif ra_max > 360:
            # Query wraps around: (ra >= ra_min) OR (ra <= ra_max-360)
            query = self.db.query(UnifiedStarCatalog).filter(
                UnifiedStarCatalog.dec_deg >= dec_min,
                UnifiedStarCatalog.dec_deg <= dec_max
            ).filter(
                (UnifiedStarCatalog.ra_deg >= ra_min) |
                (UnifiedStarCatalog.ra_deg <= (ra_max - 360))
            ).limit(limit)
        else:
            # Normal case: no wrap-around
            query = self.db.query(UnifiedStarCatalog).filter(
                UnifiedStarCatalog.ra_deg >= ra_min,
                UnifiedStarCatalog.ra_deg <= ra_max,
                UnifiedStarCatalog.dec_deg >= dec_min,
                UnifiedStarCatalog.dec_deg <= dec_max
            ).limit(limit)
        
        return query.all()
    
    def get_total_count(self) -> int:
        """
        Get total number of stars in catalog.
        
        Returns:
            Total count of records
        """
        return self.db.query(UnifiedStarCatalog).count()
