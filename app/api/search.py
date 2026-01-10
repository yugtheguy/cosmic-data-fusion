"""
Search API endpoints for COSMIC Data Fusion.

Provides endpoints for querying the star catalog:
- Bounding box search (rectangular region)
- Cone search (circular region with proper spherical geometry)

All search logic is delegated to the service layer.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.schemas import (
    StarResponse,
    SearchResponse,
)
from app.services.search import SearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


@router.get(
    "/box",
    response_model=SearchResponse,
    summary="Bounding box search",
    description="Search stars within a rectangular RA/Dec region."
)
def search_bounding_box(
    ra_min: float = Query(
        ..., ge=0.0, lt=360.0,
        description="Minimum RA in degrees (ICRS)"
    ),
    ra_max: float = Query(
        ..., ge=0.0, lt=360.0,
        description="Maximum RA in degrees (ICRS)"
    ),
    dec_min: float = Query(
        ..., ge=-90.0, le=90.0,
        description="Minimum Dec in degrees (ICRS)"
    ),
    dec_max: float = Query(
        ..., ge=-90.0, le=90.0,
        description="Maximum Dec in degrees (ICRS)"
    ),
    limit: int = Query(
        default=1000, ge=1, le=10000,
        description="Maximum results to return"
    ),
    db: Session = Depends(get_db)
) -> SearchResponse:
    """
    Search stars within a bounding box.
    
    Returns all stars where:
    - ra_min <= RA <= ra_max
    - dec_min <= Dec <= dec_max
    
    Note: This simple filter does NOT handle RA wrap-around at 0°/360°.
    For searches crossing RA=0°, make two separate queries.
    
    Args:
        ra_min: Minimum Right Ascension (degrees)
        ra_max: Maximum Right Ascension (degrees)
        dec_min: Minimum Declination (degrees)
        dec_max: Maximum Declination (degrees)
        limit: Maximum number of results
        db: Database session (injected)
        
    Returns:
        SearchResponse with count and matching stars
        
    Raises:
        HTTPException 400: Invalid parameter ranges
        HTTPException 500: Database error
    """
    # Validate ranges
    if ra_min > ra_max:
        raise HTTPException(
            status_code=400,
            detail="ra_min must be less than or equal to ra_max"
        )
    if dec_min > dec_max:
        raise HTTPException(
            status_code=400,
            detail="dec_min must be less than or equal to dec_max"
        )
    
    try:
        service = SearchService(db)
        stars = service.search_bounding_box(
            ra_min=ra_min,
            ra_max=ra_max,
            dec_min=dec_min,
            dec_max=dec_max,
            limit=limit
        )
        
        star_responses = [
            StarResponse.model_validate(star) for star in stars
        ]
        
        return SearchResponse(
            count=len(star_responses),
            stars=star_responses
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during bounding box search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/cone",
    response_model=SearchResponse,
    summary="Cone search",
    description="Search stars within a circular region using proper spherical geometry."
)
def search_cone(
    ra: float = Query(
        ..., ge=0.0, lt=360.0,
        description="Center RA in degrees (ICRS)"
    ),
    dec: float = Query(
        ..., ge=-90.0, le=90.0,
        description="Center Dec in degrees (ICRS)"
    ),
    radius: float = Query(
        ..., gt=0.0, le=180.0,
        description="Search radius in degrees"
    ),
    limit: int = Query(
        default=1000, ge=1, le=10000,
        description="Maximum results to return"
    ),
    db: Session = Depends(get_db)
) -> SearchResponse:
    """
    Search stars within a cone (circular region).
    
    Uses Astropy for proper spherical geometry - correctly handles:
    - cos(dec) factor for RA
    - Regions near the poles
    - Large search radii
    
    Results are sorted by angular distance from the search center.
    
    Args:
        ra: Center Right Ascension (degrees, ICRS)
        dec: Center Declination (degrees, ICRS)
        radius: Search radius (degrees)
        limit: Maximum number of results
        db: Database session (injected)
        
    Returns:
        SearchResponse with count and matching stars (sorted by distance)
        
    Raises:
        HTTPException 500: Database error
        
    Astronomy Note:
        Angular separation is computed using Astropy's SkyCoord.separation()
        which uses the Vincenty formula for geodesic accuracy.
    """
    try:
        service = SearchService(db)
        stars = service.search_cone(
            ra=ra,
            dec=dec,
            radius=radius,
            limit=limit
        )
        
        star_responses = [
            StarResponse.model_validate(star) for star in stars
        ]
        
        return SearchResponse(
            count=len(star_responses),
            stars=star_responses
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during cone search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
