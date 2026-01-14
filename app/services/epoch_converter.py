"""
Epoch and Coordinate Harmonization Service for COSMIC Data Fusion.

This module provides validation and standardization of astronomical coordinates,
ensuring data quality across the unified catalog.

Phase: 2 - Data Harmonization
"""

import logging
from typing import Dict, Any, List

from sqlalchemy.orm import Session

from app.models import UnifiedStarCatalog

logger = logging.getLogger(__name__)


class EpochHarmonizer:
    """
    Service for validating and harmonizing astronomical coordinates.
    
    Coordinate Validation:
        - Right Ascension (RA): Must be in [0, 360) degrees
        - Declination (Dec): Must be in [-90, +90] degrees
        
    Why Validation Matters:
        - Invalid coordinates can cause calculation errors
        - May indicate data corruption or parsing errors
        - Essential for cross-matching and visualization
        
    Future Extensions:
        - Epoch propagation (proper motion correction)
        - Coordinate frame transformations
        - Systematic offset corrections
    """
    
    def __init__(self, db: Session):
        """
        Initialize the EpochHarmonizer.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def validate_coordinates(self, ra: float = None, dec: float = None) -> tuple[bool, Dict[str, Any]]:
        """
        Validate coordinates - can be called for a single coordinate pair or all stars.
        
        Args:
            ra: Optional RA in degrees. If None, validates all stars in database.
            dec: Optional Dec in degrees. If None, validates all stars in database.
        
        Returns:
            If ra/dec provided: Tuple of (is_valid: bool, error_details: dict)
            If not provided: Dict with validation report for all stars
        """
        # Single coordinate validation
        if ra is not None and dec is not None:
            issues = []
            
            if ra < 0 or ra >= 360:
                issues.append(f"RA out of range: {ra} (expected [0, 360))")
            
            if dec < -90 or dec > 90:
                issues.append(f"Dec out of range: {dec} (expected [-90, +90])")
            
            is_valid = len(issues) == 0
            return is_valid, {"issues": issues}
        
        # Validate all stars in database
        logger.info("Starting coordinate validation...")
        
        stars = self.db.query(UnifiedStarCatalog).all()
        
        if not stars:
            return {
                "valid_stars": 0,
                "invalid_stars": 0,
                "total_stars": 0,
                "invalid_details": [],
                "message": "No stars found in database"
            }
        
        valid_count = 0
        invalid_count = 0
        invalid_details: List[Dict[str, Any]] = []
        
        for star in stars:
            is_valid = True
            issues: List[str] = []
            
            # Validate RA: should be [0, 360)
            if star.ra_deg is None:
                is_valid = False
                issues.append("RA is NULL")
            elif star.ra_deg < 0 or star.ra_deg >= 360:
                is_valid = False
                issues.append(f"RA out of range: {star.ra_deg} (expected [0, 360))")
            
            # Validate Dec: should be [-90, +90]
            if star.dec_deg is None:
                is_valid = False
                issues.append("Dec is NULL")
            elif star.dec_deg < -90 or star.dec_deg > 90:
                is_valid = False
                issues.append(f"Dec out of range: {star.dec_deg} (expected [-90, +90])")
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                # Log and collect invalid entries (limit to first 100)
                if len(invalid_details) < 100:
                    invalid_details.append({
                        "id": star.id,
                        "source_id": star.source_id,
                        "original_source": star.original_source,
                        "ra_deg": star.ra_deg,
                        "dec_deg": star.dec_deg,
                        "issues": issues
                    })
                logger.warning(
                    f"Invalid coordinates for star {star.id} "
                    f"({star.source_id}): {', '.join(issues)}"
                )
        
        total_stars = valid_count + invalid_count
        
        result = {
            "valid_stars": valid_count,
            "invalid_stars": invalid_count,
            "total_stars": total_stars,
            "validation_rate": round(valid_count / total_stars * 100, 2) if total_stars > 0 else 0,
            "invalid_details": invalid_details,
            "message": (
                f"Validation complete. {valid_count}/{total_stars} stars have valid coordinates."
                if invalid_count == 0
                else f"Found {invalid_count} stars with invalid coordinates."
            )
        }
        
        logger.info(
            f"Coordinate validation complete: {valid_count} valid, "
            f"{invalid_count} invalid out of {total_stars} total"
        )
        
        return result
    
    def validate_magnitude(self) -> Dict[str, Any]:
        """
        Validate magnitude values in the database.
        
        Typical apparent magnitude ranges:
        - Brightest stars: -1 to 1 mag
        - Naked eye limit: ~6 mag
        - Telescope surveys: up to 25-30 mag
        
        Returns:
            Dict with magnitude validation report
        """
        logger.info("Starting magnitude validation...")
        
        stars = self.db.query(UnifiedStarCatalog).all()
        
        if not stars:
            return {
                "valid_stars": 0,
                "suspicious_stars": 0,
                "total_stars": 0,
                "message": "No stars found in database"
            }
        
        valid_count = 0
        suspicious_count = 0
        suspicious_details: List[Dict[str, Any]] = []
        
        # Reasonable magnitude range for astronomical surveys
        MIN_MAG = -30  # Theoretical minimum (nothing is this bright)
        MAX_MAG = 35   # Faintest detectable by any telescope
        
        # Warning thresholds
        UNUSUALLY_BRIGHT = -2  # Brighter than Sirius is rare
        UNUSUALLY_FAINT = 25   # Fainter than typical surveys
        
        for star in stars:
            is_suspicious = False
            issues: List[str] = []
            
            if star.brightness_mag is None:
                is_suspicious = True
                issues.append("Magnitude is NULL")
            elif star.brightness_mag < MIN_MAG or star.brightness_mag > MAX_MAG:
                is_suspicious = True
                issues.append(f"Magnitude out of physical range: {star.brightness_mag}")
            elif star.brightness_mag < UNUSUALLY_BRIGHT:
                is_suspicious = True
                issues.append(f"Unusually bright: {star.brightness_mag} mag")
            elif star.brightness_mag > UNUSUALLY_FAINT:
                is_suspicious = True
                issues.append(f"Unusually faint: {star.brightness_mag} mag")
            
            if is_suspicious:
                suspicious_count += 1
                if len(suspicious_details) < 100:
                    suspicious_details.append({
                        "id": star.id,
                        "source_id": star.source_id,
                        "brightness_mag": star.brightness_mag,
                        "issues": issues
                    })
            else:
                valid_count += 1
        
        total_stars = valid_count + suspicious_count
        
        return {
            "valid_stars": valid_count,
            "suspicious_stars": suspicious_count,
            "total_stars": total_stars,
            "suspicious_details": suspicious_details,
            "message": f"Magnitude validation complete. {suspicious_count} suspicious values found."
        }
    
    def get_coordinate_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about coordinate distribution in the catalog.
        
        Returns:
            Dict with RA/Dec distribution statistics
        """
        from sqlalchemy import func
        
        stats = self.db.query(
            func.count(UnifiedStarCatalog.id).label("count"),
            func.min(UnifiedStarCatalog.ra_deg).label("ra_min"),
            func.max(UnifiedStarCatalog.ra_deg).label("ra_max"),
            func.avg(UnifiedStarCatalog.ra_deg).label("ra_avg"),
            func.min(UnifiedStarCatalog.dec_deg).label("dec_min"),
            func.max(UnifiedStarCatalog.dec_deg).label("dec_max"),
            func.avg(UnifiedStarCatalog.dec_deg).label("dec_avg"),
            func.min(UnifiedStarCatalog.brightness_mag).label("mag_min"),
            func.max(UnifiedStarCatalog.brightness_mag).label("mag_max"),
            func.avg(UnifiedStarCatalog.brightness_mag).label("mag_avg"),
        ).first()
        
        return {
            "total_stars": stats.count or 0,
            "ra_range": {
                "min": round(stats.ra_min, 4) if stats.ra_min else None,
                "max": round(stats.ra_max, 4) if stats.ra_max else None,
                "avg": round(stats.ra_avg, 4) if stats.ra_avg else None
            },
            "dec_range": {
                "min": round(stats.dec_min, 4) if stats.dec_min else None,
                "max": round(stats.dec_max, 4) if stats.dec_max else None,
                "avg": round(stats.dec_avg, 4) if stats.dec_avg else None
            },
            "magnitude_range": {
                "min": round(stats.mag_min, 2) if stats.mag_min else None,
                "max": round(stats.mag_max, 2) if stats.mag_max else None,
                "avg": round(stats.mag_avg, 2) if stats.mag_avg else None
            }
        }
