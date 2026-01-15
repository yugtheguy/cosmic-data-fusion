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
from app.services.gaia import GaiaService
from app.repository.star_catalog import StarCatalogRepository
from app.models import UnifiedStarCatalog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


@router.get(
    "/box",
    summary="Bounding box search",
    description="Search stars within a rectangular RA/Dec region. Returns standardized response format."
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
):
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
    # Validate dec ranges (RA wraparound is allowed for ra_min > ra_max)
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
        
        # Convert to StarRecord format
        from app.api.query import StarRecord
        records = []
        for star in stars:
            records.append(StarRecord(
                id=star.id,
                source_id=star.source_id,
                ra_deg=star.ra_deg,
                dec_deg=star.dec_deg,
                brightness_mag=star.brightness_mag,
                parallax_mas=star.parallax_mas,
                distance_pc=star.distance_pc,
                original_source=star.original_source
            ))
        
        # Return standardized format
        return {
            "success": True,
            "total_count": len(records),
            "records": records
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during bounding box search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/cone",
    summary="Cone search",
    description="Search stars within a circular region using proper spherical geometry. Returns standardized response format."
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
):
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
        
        # Convert to StarResponse format
        from app.api.query import StarRecord
        records = []
        for star in stars:
            records.append(StarRecord(
                id=star.id,
                source_id=star.source_id,
                ra_deg=star.ra_deg,
                dec_deg=star.dec_deg,
                brightness_mag=star.brightness_mag,
                parallax_mas=star.parallax_mas,
                distance_pc=star.distance_pc,
                original_source=star.original_source
            ))
        
        # Return standardized format
        return {
            "success": True,
            "total_count": len(records),
            "records": records
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during cone search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/star/{star_id}",
    response_model=StarResponse,
    summary="Get single star by ID",
    description="Retrieve detailed information about a specific star."
)
def get_star_by_id(
    star_id: int,
    db: Session = Depends(get_db)
) -> StarResponse:
    """
    Get a single star by its database ID.
    
    Args:
        star_id: The database ID of the star
        db: Database session (injected)
        
    Returns:
        StarResponse with full star details
        
    Raises:
        HTTPException 404: Star not found
        HTTPException 500: Database error
    """
    try:
        service = SearchService(db)
        star = service.get_star_by_id(star_id)
        
        if star is None:
            raise HTTPException(
                status_code=404,
                detail=f"Star with ID {star_id} not found"
            )
        
        return StarResponse.model_validate(star)
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching star {star_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/star/{star_id}/nearby",
    response_model=SearchResponse,
    summary="Find nearby stars",
    description="Find stars near a specific star within a given radius."
)
def get_nearby_stars(
    star_id: int,
    radius: float = Query(
        default=0.5, gt=0.0, le=10.0,
        description="Search radius in degrees"
    ),
    limit: int = Query(
        default=50, ge=1, le=500,
        description="Maximum results to return"
    ),
    db: Session = Depends(get_db)
) -> SearchResponse:
    """
    Find stars near a specific star.
    
    First retrieves the target star's coordinates, then performs
    a cone search around that position.
    
    Args:
        star_id: The database ID of the reference star
        radius: Search radius in degrees (default 0.5)
        limit: Maximum number of nearby stars to return
        db: Database session (injected)
        
    Returns:
        SearchResponse with nearby stars (excluding the target star itself)
        
    Raises:
        HTTPException 404: Target star not found
        HTTPException 500: Database error
    """
    try:
        service = SearchService(db)
        
        # First get the target star
        target_star = service.get_star_by_id(star_id)
        if target_star is None:
            raise HTTPException(
                status_code=404,
                detail=f"Star with ID {star_id} not found"
            )
        
        # Perform cone search around the target star
        nearby_stars = service.search_cone(
            ra=target_star.ra_deg,
            dec=target_star.dec_deg,
            radius=radius,
            limit=limit + 1  # +1 to account for the target star itself
        )
        
        # Filter out the target star from results
        nearby_stars = [s for s in nearby_stars if s.id != star_id][:limit]
        
        star_responses = [
            StarResponse.model_validate(star) for star in nearby_stars
        ]
        
        return SearchResponse(
            count=len(star_responses),
            stars=star_responses
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error finding nearby stars for {star_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
@router.post(
    "/star/{star_id}/refresh-gaia",
    response_model=StarResponse,
    summary="Fetch real-time data from Gaia",
    description="Query ESA Gaia Archive for this star and update the database with real scientific values."
)
def refresh_star_from_gaia(
    star_id: int,
    db: Session = Depends(get_db)
) -> StarResponse:
    """
    Fetch and update star data from Gaia Archive.
    """
    try:
        # 1. Get local star to find its source_id
        service = SearchService(db)
        local_star = service.get_star_by_id(star_id)
        
        if not local_star:
            raise HTTPException(status_code=404, detail="Star not found")
            
        # 2. Query Gaia Archive with Fallback
        gaia_data = GaiaService.fetch_star_data(
            source_id=local_star.source_id, 
            ra=local_star.ra_deg, 
            dec=local_star.dec_deg
        )
        
        if not gaia_data:
            raise HTTPException(
                status_code=502, 
                detail="Could not fetch data from Gaia Archive. Star might not exist in DR3 or service is down."
            )
            
        # 3. Update local database
        # We access the repository directly or via service to update
        # For simplicity, we'll do a direct update here since we have the DB session
        
        local_star.parallax_mas = gaia_data.get("parallax")
        
        # Use GSP-Phot distance if available, else calculate from parallax
        dist = gaia_data.get("distance")
        if dist is None and local_star.parallax_mas and local_star.parallax_mas > 0:
            dist = 1000.0 / local_star.parallax_mas
            
        local_star.distance_pc = dist
        
        # Update metadata to indicate this is real data
        meta = local_star.raw_metadata or {}
        if isinstance(meta, str):
            import json
            try: meta = json.loads(meta)
            except: meta = {}
            
        meta["data_source"] = "Gaia DR3 (Live Fetch)"
        meta["fetched_at"] = "Just now"
        meta["radial_velocity"] = gaia_data.get("radial_velocity")
        meta["effective_temperature"] = gaia_data.get("teff")
        
        local_star.raw_metadata = meta
        
        db.commit()
        db.refresh(local_star)
        
        return StarResponse.model_validate(local_star)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating star from Gaia: {e}")
        raise HTTPException(status_code=500, detail=str(e))
