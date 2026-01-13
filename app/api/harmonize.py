"""
Harmonization API endpoints for COSMIC Data Fusion.

Provides endpoints for data harmonization operations:
- POST /harmonize/cross-match - Cross-match stars across catalogs
- POST /harmonize/validate   - Validate coordinate integrity
- GET  /harmonize/stats      - Get harmonization statistics

Phase: 2 - Data Harmonization
"""

import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.harmonizer import CrossMatchService
from app.services.epoch_converter import EpochHarmonizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/harmonize", tags=["Harmonization"])


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class CrossMatchRequest(BaseModel):
    """Request parameters for cross-matching."""
    
    radius_arcsec: float = Field(
        default=1.0,
        gt=0.0,
        le=60.0,
        description=(
            "Maximum angular separation in arcseconds for considering "
            "two observations as the same star. "
            "Typical values: 1.0\" (high precision), 2.0\" (ground-based), "
            "5.0\" (older catalogs)."
        ),
        examples=[1.0, 2.0, 5.0]
    )
    
    reset_existing: bool = Field(
        default=False,
        description=(
            "If True, clear all existing fusion_group_ids before running. "
            "Use when re-running cross-match with different parameters."
        )
    )


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class CrossMatchResponse(BaseModel):
    """Response for cross-match operation."""
    success: bool
    message: str
    total_stars: int
    groups_created: int
    stars_in_groups: int
    isolated_stars: int
    radius_arcsec: float


class ValidationResponse(BaseModel):
    """Response for coordinate validation."""
    success: bool
    message: str
    valid_stars: int
    invalid_stars: int
    total_stars: int
    validation_rate: float
    invalid_details: List[Dict[str, Any]] = Field(
        default=[],
        description="Details of first 100 invalid entries"
    )


class HarmonizationStats(BaseModel):
    """Statistics about harmonization state."""
    total_stars: int
    stars_in_fusion_groups: int
    isolated_stars: int
    unique_fusion_groups: int
    coordinate_stats: Dict[str, Any]


# ============================================================
# API ENDPOINTS
# ============================================================

@router.post(
    "/cross-match",
    response_model=CrossMatchResponse,
    summary="Cross-match stars across catalogs",
    description="""
Perform positional cross-matching to identify the same physical star
observed by different catalogs.

**How it works:**
1. Loads all stars from the unified catalog
2. Uses Astropy's spherical geometry to find coordinate matches
3. Groups matched stars using Union-Find algorithm (handles A↔B↔C chains)
4. Assigns shared UUID (fusion_group_id) to each group

**Radius Guidelines:**
- **1.0 arcsec**: For high-precision catalogs (Gaia, HST)
- **2.0 arcsec**: For typical ground-based optical surveys (SDSS)
- **5.0 arcsec**: For older or lower-resolution catalogs (2MASS)

**Use Cases:**
- Combine photometry from multiple surveys
- Identify duplicate observations
- Enable multi-wavelength analysis
    """
)
async def cross_match_catalogs(
    request: CrossMatchRequest = CrossMatchRequest(),
    db: Session = Depends(get_db)
) -> CrossMatchResponse:
    """
    Run cross-matching algorithm on the star catalog.
    
    Groups observations of the same physical star across different
    source catalogs based on positional proximity.
    """
    try:
        logger.info(
            f"Cross-match requested: radius={request.radius_arcsec}\", "
            f"reset={request.reset_existing}"
        )
        
        service = CrossMatchService(db)
        result = service.perform_cross_match(
            radius_arcsec=request.radius_arcsec,
            reset_existing=request.reset_existing
        )
        
        return CrossMatchResponse(
            success=True,
            message=result.get("message", "Cross-match complete"),
            total_stars=result["total_stars"],
            groups_created=result["groups_created"],
            stars_in_groups=result["stars_in_groups"],
            isolated_stars=result["isolated_stars"],
            radius_arcsec=result["radius_arcsec"]
        )
        
    except Exception as e:
        logger.error(f"Cross-match failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Cross-match operation failed: {str(e)}"
        )


@router.post(
    "/validate",
    response_model=ValidationResponse,
    summary="Validate star coordinates",
    description="""
Validate all star coordinates in the database for data quality.

**Checks performed:**
- Right Ascension (RA) in valid range [0, 360)
- Declination (Dec) in valid range [-90, +90]
- NULL value detection

**Why this matters:**
- Invalid coordinates cause calculation errors
- May indicate data corruption during ingestion
- Essential before running cross-match or visualization
    """
)
async def validate_coordinates(
    db: Session = Depends(get_db)
) -> ValidationResponse:
    """
    Run coordinate validation on all stars in the catalog.
    
    Returns a report of valid vs invalid entries with details.
    """
    try:
        logger.info("Coordinate validation requested")
        
        harmonizer = EpochHarmonizer(db)
        result = harmonizer.validate_coordinates()
        
        return ValidationResponse(
            success=True,
            message=result.get("message", "Validation complete"),
            valid_stars=result["valid_stars"],
            invalid_stars=result["invalid_stars"],
            total_stars=result["total_stars"],
            validation_rate=result.get("validation_rate", 0),
            invalid_details=result.get("invalid_details", [])
        )
        
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Validation operation failed: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=HarmonizationStats,
    summary="Get harmonization statistics",
    description="""
Get current state of data harmonization including:
- Fusion group counts
- Coordinate range statistics
- Data quality metrics
    """
)
async def get_harmonization_stats(
    db: Session = Depends(get_db)
) -> HarmonizationStats:
    """
    Get statistics about the current harmonization state.
    """
    try:
        cross_match_service = CrossMatchService(db)
        epoch_harmonizer = EpochHarmonizer(db)
        
        cross_match_stats = cross_match_service.get_cross_match_statistics()
        coord_stats = epoch_harmonizer.get_coordinate_statistics()
        
        return HarmonizationStats(
            total_stars=cross_match_stats["total_stars"],
            stars_in_fusion_groups=cross_match_stats["stars_in_fusion_groups"],
            isolated_stars=cross_match_stats["isolated_stars"],
            unique_fusion_groups=cross_match_stats["unique_fusion_groups"],
            coordinate_stats=coord_stats
        )
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve harmonization statistics: {str(e)}"
        )


@router.get(
    "/fusion-group/{group_id}",
    summary="Get stars in a fusion group",
    description="Retrieve all stars that belong to a specific fusion group."
)
async def get_fusion_group(
    group_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all stars belonging to a specific fusion group.
    
    Args:
        group_id: UUID of the fusion group
        
    Returns:
        List of stars in the group with their details
    """
    try:
        service = CrossMatchService(db)
        stars = service.get_fusion_group(group_id)
        
        if not stars:
            raise HTTPException(
                status_code=404,
                detail=f"Fusion group '{group_id}' not found"
            )
        
        return {
            "fusion_group_id": group_id,
            "star_count": len(stars),
            "stars": stars
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get fusion group: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve fusion group: {str(e)}"
        )
