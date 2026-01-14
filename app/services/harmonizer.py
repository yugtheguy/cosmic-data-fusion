"""
Cross-Match Harmonization Service for COSMIC Data Fusion.

This module provides positional cross-matching to identify the same physical star
across multiple astronomical catalogs. Uses Astropy's SkyCoord for proper
spherical geometry and handles the union-find problem for transitive matching.

Phase: 2 - Data Harmonization
"""

import logging
import uuid
from typing import Dict, Any, List, Set, Optional

import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units as u
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import UnifiedStarCatalog

logger = logging.getLogger(__name__)


class CrossMatchService:
    """
    Service for cross-matching stars across different catalogs.
    
    Cross-matching identifies observations of the same physical star from
    different surveys (e.g., Gaia, SDSS) based on positional proximity.
    
    Algorithm Overview:
        1. Load all stars with their celestial coordinates
        2. Use Astropy's search_around_sky for efficient spherical matching
        3. Build equivalence groups using union-find (connected components)
        4. Assign shared UUIDs (fusion_group_id) to matched observations
    
    Why Cross-Matching Matters:
        - Different surveys observe the same sky with different instruments
        - Each catalog may have slightly different positions (measurement error)
        - Cross-matching enables multi-wavelength analysis
        - Helps identify and merge duplicate entries
    """
    
    def __init__(self, db: Session):
        """
        Initialize the CrossMatchService.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def perform_cross_match(
        self,
        radius_arcsec: float = 1.0,
        reset_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Perform positional cross-matching on all stars in the catalog.
        
        Uses Astropy's search_around_sky to find all pairs of stars within
        the specified angular separation. Then groups matched stars using
        a union-find algorithm to handle transitive relationships
        (if A matches B and B matches C, then A, B, C are all the same star).
        
        Args:
            radius_arcsec: Maximum angular separation in arcseconds for a match.
                          Typical values:
                          - 1.0": For high-precision catalogs (Gaia, HST)
                          - 2.0": For ground-based optical surveys
                          - 5.0": For older or lower-resolution catalogs
            reset_existing: If True, clear all existing fusion_group_ids first
            
        Returns:
            Dict with cross-match statistics:
            {
                "total_stars": int,
                "groups_created": int,
                "stars_in_groups": int,
                "isolated_stars": int,
                "radius_arcsec": float
            }
        """
        logger.info(f"Starting cross-match with radius={radius_arcsec} arcsec")
        
        # Step A: Load all stars from database
        stars = self.db.query(UnifiedStarCatalog).all()
        
        if not stars:
            logger.warning("No stars in database to cross-match")
            return {
                "total_stars": 0,
                "groups_created": 0,
                "stars_in_groups": 0,
                "isolated_stars": 0,
                "radius_arcsec": radius_arcsec,
                "message": "No stars found in database"
            }
        
        total_stars = len(stars)
        logger.info(f"Loaded {total_stars} stars from database")
        
        # Reset existing fusion_group_ids if requested
        if reset_existing:
            logger.info("Resetting existing fusion_group_ids")
            for star in stars:
                star.fusion_group_id = None
        
        # Build lookup structures
        star_by_id: Dict[int, UnifiedStarCatalog] = {star.id: star for star in stars}
        ids = [star.id for star in stars]
        ra_list = [star.ra_deg for star in stars]
        dec_list = [star.dec_deg for star in stars]
        
        # Step B: Create SkyCoord array for all stars
        coords = SkyCoord(ra=ra_list * u.degree, dec=dec_list * u.degree, frame='icrs')
        
        # Find all pairs within radius using search_around_sky
        # This returns indices of matching pairs
        # idx1[i] and idx2[i] are indices of a matching pair
        logger.info(f"Running search_around_sky with radius={radius_arcsec} arcsec")
        idx1, idx2, sep2d, _ = coords.search_around_sky(coords, radius_arcsec * u.arcsec)
        
        logger.info(f"Found {len(idx1)} coordinate pairs within radius")
        
        # Step C: Build groups using Union-Find algorithm
        # parent[id] -> id of the group representative
        parent: Dict[int, int] = {star_id: star_id for star_id in ids}
        
        def find(x: int) -> int:
            """Find the root/representative of x's group with path compression."""
            if parent[x] != x:
                parent[x] = find(parent[x])  # Path compression
            return parent[x]
        
        def union(x: int, y: int) -> None:
            """Merge the groups containing x and y."""
            root_x = find(x)
            root_y = find(y)
            if root_x != root_y:
                parent[root_x] = root_y
        
        # Process all matching pairs (skip self-matches where idx1 == idx2)
        for i in range(len(idx1)):
            if idx1[i] != idx2[i]:  # Skip self-matches
                star_id_1 = ids[idx1[i]]
                star_id_2 = ids[idx2[i]]
                union(star_id_1, star_id_2)
        
        # Step D: Collect groups and assign UUIDs
        # Group stars by their root representative
        groups: Dict[int, List[int]] = {}
        for star_id in ids:
            root = find(star_id)
            if root not in groups:
                groups[root] = []
            groups[root].append(star_id)
        
        # Filter to only groups with more than one star
        multi_star_groups = {k: v for k, v in groups.items() if len(v) > 1}
        
        # Assign fusion_group_id to each group
        groups_created = 0
        stars_in_groups = 0
        
        for root, member_ids in multi_star_groups.items():
            # Check if any member already has a fusion_group_id
            existing_group_id: Optional[str] = None
            for member_id in member_ids:
                star = star_by_id[member_id]
                if star.fusion_group_id:
                    existing_group_id = star.fusion_group_id
                    break
            
            # Use existing ID or generate new UUID
            group_uuid = existing_group_id or str(uuid.uuid4())
            
            # Assign to all members
            for member_id in member_ids:
                star = star_by_id[member_id]
                star.fusion_group_id = group_uuid
                stars_in_groups += 1
            
            if not existing_group_id:
                groups_created += 1
        
        # Commit changes to database
        self.db.commit()
        
        isolated_stars = total_stars - stars_in_groups
        
        total_groups = len(multi_star_groups)
        
        result = {
            "total_stars": total_stars,
            "groups_created": groups_created,
            "total_groups": total_groups,
            "stars_in_groups": stars_in_groups,
            "isolated_stars": isolated_stars,
            "radius_arcsec": radius_arcsec,
            "message": f"Cross-match complete. Found {total_groups} fusion groups ({groups_created} new)."
        }
        
        logger.info(
            f"Cross-match complete: {total_groups} groups total, {groups_created} new, "
            f"{stars_in_groups} stars grouped, {isolated_stars} isolated"
        )
        
        return result
    
    def get_fusion_group(self, fusion_group_id: str) -> List[Dict[str, Any]]:
        """
        Get all stars in a specific fusion group.
        
        Args:
            fusion_group_id: UUID of the fusion group
            
        Returns:
            List of star dictionaries in the group
        """
        stars = self.db.query(UnifiedStarCatalog).filter(
            UnifiedStarCatalog.fusion_group_id == fusion_group_id
        ).all()
        
        return [
            {
                "id": star.id,
                "source_id": star.source_id,
                "original_source": star.original_source,
                "ra_deg": star.ra_deg,
                "dec_deg": star.dec_deg,
                "brightness_mag": star.brightness_mag,
                "parallax_mas": star.parallax_mas
            }
            for star in stars
        ]
    
    def get_cross_match_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about current cross-match state.
        
        Returns:
            Dict with statistics about fusion groups
        """
        total_stars = self.db.query(UnifiedStarCatalog).count()
        
        stars_with_groups = self.db.query(UnifiedStarCatalog).filter(
            UnifiedStarCatalog.fusion_group_id.isnot(None)
        ).count()
        
        # Count unique groups
        from sqlalchemy import func
        unique_groups = self.db.query(
            func.count(func.distinct(UnifiedStarCatalog.fusion_group_id))
        ).filter(
            UnifiedStarCatalog.fusion_group_id.isnot(None)
        ).scalar()
        
        return {
            "total_stars": total_stars,
            "stars_in_fusion_groups": stars_with_groups,
            "isolated_stars": total_stars - stars_with_groups,
            "unique_fusion_groups": unique_groups or 0
        }
    def list_fusion_groups(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List fusion groups with metadata for visualization.
        """
        groups = self.db.query(
            UnifiedStarCatalog.fusion_group_id,
            func.count(UnifiedStarCatalog.id).label('star_count'),
            func.avg(UnifiedStarCatalog.ra_deg).label('avg_ra'),
            func.avg(UnifiedStarCatalog.dec_deg).label('avg_dec')
        ).filter(
            UnifiedStarCatalog.fusion_group_id.isnot(None)
        ).group_by(
            UnifiedStarCatalog.fusion_group_id
        ).limit(limit).all()
        
        return [
            {
                "id": g.fusion_group_id,
                "label": f"Group {i+1}",
                "star_count": g.star_count,
                "ra": float(g.avg_ra) if g.avg_ra else 0,
                "dec": float(g.avg_dec) if g.avg_dec else 0,
                # Simulate sources for visualization variety if strict mapping not needed yet
                # ideally we count source types from DB but that's expensive
            }
            for i, g in enumerate(groups)
        ]
