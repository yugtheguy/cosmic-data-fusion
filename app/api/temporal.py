"""
Temporal Query API - Time Machine Feature

Provides REST endpoints for querying star positions at arbitrary epochs.
Enables the Time Machine frontend to:
1. Query stars at specific time points
2. Get star trails (animated paths)
3. Identify fast movers
4. Calculate position uncertainty

Author: COSMIC Data Fusion Team
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
import json

from app.database import get_db
from app.services.temporal_calculator import (
    TemporalCalculator,
    batch_calculate_positions,
    format_epoch_display
)

router = APIRouter(prefix="/temporal", tags=["temporal"])

# Initialize calculator (shared instance)
temporal_calc = TemporalCalculator()


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class TemporalQueryRequest(BaseModel):
    """Request model for temporal queries."""
    target_epoch: float = Field(
        ...,
        description="Target epoch as decimal year (e.g., 2026.5, -3000, 12000)",
        example=2026.0
    )
    ra_min: Optional[float] = Field(
        None,
        ge=0,
        lt=360,
        description="Minimum RA for spatial filter (degrees)"
    )
    ra_max: Optional[float] = Field(
        None,
        ge=0,
        lt=360,
        description="Maximum RA for spatial filter (degrees)"
    )
    dec_min: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="Minimum Dec for spatial filter (degrees)"
    )
    dec_max: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="Maximum Dec for spatial filter (degrees)"
    )
    max_magnitude: Optional[float] = Field(
        None,
        description="Maximum magnitude (fainter limit)"
    )
    min_proper_motion: Optional[float] = Field(
        None,
        ge=0,
        description="Minimum total proper motion (mas/yr) - for fast movers"
    )
    limit: int = Field(
        1000,
        ge=1,
        le=10000,
        description="Maximum number of stars to return"
    )


class StarTemporalPosition(BaseModel):
    """Star position at a specific epoch."""
    id: int
    source_id: str
    original_source: str
    
    # Current (reference) position
    ra_deg: float
    dec_deg: float
    
    # Position at target epoch
    ra_at_epoch: float
    dec_at_epoch: float
    
    # Metadata
    brightness_mag: float
    pmra: Optional[float] = None
    pmdec: Optional[float] = None
    total_pm: Optional[float] = None  # Total PM magnitude
    pm_angle: Optional[float] = None  # PM direction (deg East of North)
    
    # Temporal info
    epoch: float
    delta_years: float
    uncertainty_arcsec: float
    uncertainty_deg: float  # NEW: Uncertainty in degrees for visualization
    uncertainty_class: str
    confidence_score: float  # NEW: 0-1 score (inverse of uncertainty)


class TemporalQueryResponse(BaseModel):
    """Response model for temporal queries."""
    epoch: float
    epoch_display: str  # Human-readable epoch (e.g., "2026 AD", "3000 BC")
    count: int
    stars: List[StarTemporalPosition]


class StarTrailRequest(BaseModel):
    """Request for star trail visualization."""
    star_id: int
    start_epoch: float
    end_epoch: float
    num_points: int = Field(
        50,
        ge=2,
        le=500,
        description="Number of points along trail"
    )


class StarTrailResponse(BaseModel):
    """Star trail path data."""
    star_id: int
    source_id: str
    trail_points: List[dict]  # List of {epoch, ra, dec, uncertainty}
    start_epoch: float
    end_epoch: float


# ============================================================
# API ENDPOINTS
# ============================================================

@router.post("/query", response_model=TemporalQueryResponse)
async def query_stars_at_epoch(
    request: TemporalQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query star positions at a specific epoch.
    
    This is the core endpoint for the Time Machine feature. It:
    1. Fetches stars from the database (with optional spatial filters)
    2. Calculates their positions at the target epoch using proper motion
    3. Returns positions with uncertainty estimates
    
    **Example Usage:**
    ```python
    # Get Pleiades positions in year 1000 BC
    {
        "target_epoch": -1000,
        "ra_min": 50,
        "ra_max": 65,
        "dec_min": 20,
        "dec_max": 30,
        "limit": 500
    }
    ```
    """
    # Use raw SQL for better control (SQLite doesn't support all ORM features)
    sql_parts = ["SELECT * FROM unified_star_catalog WHERE 1=1"]
    params = {}
    
    # Spatial filters
    if request.ra_min is not None and request.ra_max is not None:
        # Handle RA wraparound (e.g., 350° to 10°)
        if request.ra_max < request.ra_min:
            sql_parts.append("AND (ra_deg >= :ra_min OR ra_deg <= :ra_max)")
        else:
            sql_parts.append("AND ra_deg BETWEEN :ra_min AND :ra_max")
        params['ra_min'] = request.ra_min
        params['ra_max'] = request.ra_max
    
    if request.dec_min is not None:
        sql_parts.append("AND dec_deg >= :dec_min")
        params['dec_min'] = request.dec_min
    
    if request.dec_max is not None:
        sql_parts.append("AND dec_deg <= :dec_max")
        params['dec_max'] = request.dec_max
    
    if request.max_magnitude is not None:
        sql_parts.append("AND brightness_mag <= :max_mag")
        params['max_mag'] = request.max_magnitude
    
    # Order by brightness (brightest first)
    sql_parts.append("ORDER BY brightness_mag ASC")
    sql_parts.append(f"LIMIT {request.limit}")
    
    # Execute query
    from sqlalchemy import text
    sql = " ".join(sql_parts)
    result = db.execute(text(sql), params)
    
    # Convert to list of dicts
    stars = []
    for row in result:
        # Parse metadata (column 12 = raw_metadata)
        metadata = {}
        if row[12]:  # raw_metadata column
            try:
                if isinstance(row[12], str):
                    metadata = json.loads(row[12])
                elif isinstance(row[12], dict):
                    metadata = row[12]
            except:
                pass
        
        pmra = metadata.get('pmra') if isinstance(metadata, dict) else None
        pmdec = metadata.get('pmdec') if isinstance(metadata, dict) else None
        
        # Apply PM filter if requested
        if request.min_proper_motion is not None:
            if pmra is None or pmdec is None:
                continue
            import math
            total_pm = math.sqrt(pmra**2 + pmdec**2)
            if total_pm < request.min_proper_motion:
                continue
        
        star = {
            'id': row[0],
            'source_id': row[2],
            'original_source': row[8],  # source_catalog column
            'ra_deg': row[3],
            'dec_deg': row[4],
            'brightness_mag': row[5],  # brightness_mag column
            'pmra': pmra,
            'pmdec': pmdec,
        }
        stars.append(star)
    
    # Calculate positions at target epoch
    stars_at_epoch = batch_calculate_positions(
        stars,
        target_epoch=request.target_epoch,
        calculator=temporal_calc
    )
    
    # Format response
    formatted_stars = []
    for star in stars_at_epoch:
        # Calculate total PM and angle
        total_pm = None
        pm_angle = None
        if star.get('pmra') is not None and star.get('pmdec') is not None:
            import math
            total_pm, pm_angle = temporal_calc.calculate_motion_vector(
                star['pmra'],
                star['pmdec']
            )
        
        # Calculate uncertainty in degrees and confidence score
        uncertainty_arcsec = star.get('uncertainty_arcsec', 0)
        uncertainty_deg = uncertainty_arcsec / 3600.0  # Convert arcsec to degrees
        
        # Calculate confidence score (0-1, where 1 = perfect confidence)
        # Use exponential decay based on uncertainty
        # Max uncertainty for EXTREME_RANGE is ~10° = 36000 arcsec
        # Formula: confidence = e^(-uncertainty/scale)
        import math
        scale_factor = 10000  # arcsec (tuned for good 0-1 range)
        confidence_score = math.exp(-uncertainty_arcsec / scale_factor)
        confidence_score = max(0.0, min(1.0, confidence_score))  # Clamp to [0, 1]
        
        formatted_stars.append(StarTemporalPosition(
            id=star['id'],
            source_id=star['source_id'],
            original_source=star['original_source'],
            ra_deg=star['ra_deg'],
            dec_deg=star['dec_deg'],
            ra_at_epoch=star.get('ra_at_epoch', star['ra_deg']),
            dec_at_epoch=star.get('dec_at_epoch', star['dec_deg']),
            brightness_mag=star['brightness_mag'],
            pmra=star.get('pmra'),
            pmdec=star.get('pmdec'),
            total_pm=total_pm,
            pm_angle=pm_angle,
            epoch=request.target_epoch,
            delta_years=request.target_epoch - temporal_calc.reference_epoch,
            uncertainty_arcsec=uncertainty_arcsec,
            uncertainty_deg=uncertainty_deg,
            uncertainty_class=star.get('uncertainty_class', 'unknown'),
            confidence_score=confidence_score
        ))
    
    return TemporalQueryResponse(
        epoch=request.target_epoch,
        epoch_display=format_epoch_display(request.target_epoch),
        count=len(formatted_stars),
        stars=formatted_stars
    )


@router.get("/star/{star_id}/trail", response_model=StarTrailResponse)
async def get_star_trail(
    star_id: int,
    start_epoch: float = Query(..., description="Start epoch"),
    end_epoch: float = Query(..., description="End epoch"),
    num_points: int = Query(50, ge=2, le=500, description="Number of points"),
    db: Session = Depends(get_db)
):
    """
    Get star's motion trail between two epochs.
    
    This generates a series of positions showing how a star moves across
    the sky over time. Useful for visualizing proper motion.
    
    **Example:** Star trail from 2000 BC to 4000 AD
    ```
    GET /temporal/star/397/trail?start_epoch=-2000&end_epoch=4000&num_points=100
    ```
    """
    # Fetch star
    from sqlalchemy import text
    result = db.execute(
        text("SELECT * FROM unified_star_catalog WHERE id = :star_id"),
        {"star_id": star_id}
    )
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Star {star_id} not found")
    
    # Parse star data
    metadata = {}
    if row[12]:  # raw_metadata column
        try:
            if isinstance(row[12], str):
                metadata = json.loads(row[12])
            elif isinstance(row[12], dict):
                metadata = row[12]
        except:
            pass
    
    ra = row[3]
    dec = row[4]
    pmra = metadata.get('pmra') if isinstance(metadata, dict) else None
    pmdec = metadata.get('pmdec') if isinstance(metadata, dict) else None
    
    if pmra is None or pmdec is None:
        raise HTTPException(
            status_code=400,
            detail="Star has no proper motion data"
        )
    
    # Generate trail points
    trail_points = []
    epoch_step = (end_epoch - start_epoch) / (num_points - 1)
    
    for i in range(num_points):
        epoch = start_epoch + i * epoch_step
        
        result = temporal_calc.calculate_position_at_epoch(
            ra_deg=ra,
            dec_deg=dec,
            pmra_mas_yr=pmra,
            pmdec_mas_yr=pmdec,
            target_epoch=epoch
        )
        
        trail_points.append({
            "epoch": epoch,
            "epoch_display": format_epoch_display(epoch),
            "ra": result.ra_deg,
            "dec": result.dec_deg,
            "uncertainty_arcsec": result.uncertainty_arcsec,
            "uncertainty_class": result.uncertainty_class.value
        })
    
    return StarTrailResponse(
        star_id=star_id,
        source_id=row[2],
        trail_points=trail_points,
        start_epoch=start_epoch,
        end_epoch=end_epoch
    )


@router.get("/fast-movers")
async def get_fast_movers(
    min_pm: float = Query(50, description="Minimum PM (mas/yr)"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get stars with high proper motion (fast movers).
    
    These stars show the most dramatic movement over time and make
    for impressive Time Machine demonstrations.
    
    **Default:** Returns top 20 stars with PM > 50 mas/yr
    """
    from sqlalchemy import text
    import math
    
    # Get all stars with PM data
    result = db.execute(text("""
        SELECT id, source_id, ra_deg, dec_deg, brightness_mag, raw_metadata
        FROM unified_star_catalog
        WHERE raw_metadata IS NOT NULL
    """))
    
    fast_movers = []
    
    for row in result:
        try:
            if isinstance(row[5], str):
                metadata = json.loads(row[5])
            else:
                metadata = row[5] or {}
            
            pmra = metadata.get('pmra')
            pmdec = metadata.get('pmdec')
            
            if pmra and pmdec:
                total_pm = math.sqrt(pmra**2 + pmdec**2)
                
                if total_pm >= min_pm:
                    fast_movers.append({
                        "id": row[0],
                        "source_id": row[1],
                        "ra_deg": row[2],
                        "dec_deg": row[3],
                        "magnitude": row[4],
                        "pmra": pmra,
                        "pmdec": pmdec,
                        "total_pm": total_pm
                    })
        except:
            continue
    
    # Sort by total PM (descending)
    fast_movers.sort(key=lambda x: x['total_pm'], reverse=True)
    
    return {
        "count": len(fast_movers[:limit]),
        "min_pm_threshold": min_pm,
        "stars": fast_movers[:limit]
    }


# ============================================================
# ANIMATION ENDPOINT
# ============================================================

@router.get("/animation")
async def generate_animation_frames(
    start_epoch: float = Query(..., description="Start epoch (decimal year)"),
    end_epoch: float = Query(..., description="End epoch (decimal year)"),
    frame_count: int = Query(50, ge=10, le=200, description="Number of frames to generate"),
    ra_min: Optional[float] = Query(None, ge=0, lt=360),
    ra_max: Optional[float] = Query(None, ge=0, lt=360),
    dec_min: Optional[float] = Query(None, ge=-90, le=90),
    dec_max: Optional[float] = Query(None, ge=-90, le=90),
    max_magnitude: Optional[float] = Query(None, description="Max magnitude filter"),
    limit: int = Query(500, ge=1, le=2000, description="Max stars per frame"),
    delta_encoding: bool = Query(True, description="Use delta encoding to reduce payload"),
    db: Session = Depends(get_db)
):
    """
    Generate animation keyframes for smooth star position playback.
    
    Returns precomputed frames with star positions at each epoch,
    enabling fluid animations in the Time Machine.
    
    **Delta Encoding:**
    - When enabled, first frame has full positions
    - Subsequent frames only contain position deltas (dra, ddec)
    - Reduces payload size by ~60%
    
    **Example:**
    ```
    GET /temporal/animation?start_epoch=-3000&end_epoch=2000&frame_count=100
    ```
    """
    from sqlalchemy import text
    import sys
    
    # Validate epoch order
    if start_epoch >= end_epoch:
        raise HTTPException(status_code=400, detail="start_epoch must be less than end_epoch")
    
    # Build SQL query for stars
    sql_parts = ["SELECT id, source_id, ra_deg, dec_deg, brightness_mag, raw_metadata FROM unified_star_catalog WHERE 1=1"]
    params = {}
    
    if ra_min is not None and ra_max is not None:
        if ra_min <= ra_max:
            sql_parts.append("AND ra_deg BETWEEN :ra_min AND :ra_max")
        else:
            sql_parts.append("AND (ra_deg >= :ra_min OR ra_deg <= :ra_max)")
        params['ra_min'] = ra_min
        params['ra_max'] = ra_max
    
    if dec_min is not None and dec_max is not None:
        sql_parts.append("AND dec_deg BETWEEN :dec_min AND :dec_max")
        params['dec_min'] = dec_min
        params['dec_max'] = dec_max
    
    if max_magnitude is not None:
        sql_parts.append("AND brightness_mag <= :max_mag")
        params['max_mag'] = max_magnitude
    
    sql_parts.append(f"LIMIT {limit}")
    
    sql_query = " ".join(sql_parts)
    stars_data = db.execute(text(sql_query), params).fetchall()
    
    if not stars_data:
        return {
            "start_epoch": start_epoch,
            "end_epoch": end_epoch,
            "frame_count": 0,
            "stars_per_frame": 0,
            "frames": [],
            "metadata": {"error": "No stars found matching criteria"}
        }
    
    # Calculate epoch step
    time_span = end_epoch - start_epoch
    epoch_step = time_span / (frame_count - 1) if frame_count > 1 else 0
    
    # Preprocess star data with proper motion
    star_info = []
    for row in stars_data:
        try:
            metadata = json.loads(row[5]) if isinstance(row[5], str) else (row[5] or {})
            star_info.append({
                "id": row[0],
                "source_id": row[1],
                "ra_deg": row[2],
                "dec_deg": row[3],
                "mag": row[4],
                "pmra": metadata.get('pmra', 0) or 0,
                "pmdec": metadata.get('pmdec', 0) or 0
            })
        except:
            continue
    
    # Generate frames
    frames = []
    prev_positions = {}  # For delta encoding
    
    for frame_idx in range(frame_count):
        epoch = start_epoch + (frame_idx * epoch_step)
        positions = []
        
        for star in star_info:
            try:
                pos_result = temporal_calc.calculate_position_at_epoch(
                    ra_deg=star["ra_deg"],
                    dec_deg=star["dec_deg"],
                    pmra_mas_yr=star["pmra"] if star["pmra"] else None,
                    pmdec_mas_yr=star["pmdec"] if star["pmdec"] else None,
                    target_epoch=epoch
                )
                
                current_ra = round(pos_result.ra_deg, 6)
                current_dec = round(pos_result.dec_deg, 6)
                
                if delta_encoding and frame_idx > 0 and star["id"] in prev_positions:
                    # Delta encoding: send difference from previous frame
                    prev = prev_positions[star["id"]]
                    dra = round(current_ra - prev["ra"], 6)
                    ddec = round(current_dec - prev["dec"], 6)
                    
                    # Only include if there's meaningful change
                    if abs(dra) > 0.000001 or abs(ddec) > 0.000001:
                        positions.append({
                            "id": star["id"],
                            "dra": dra,
                            "ddec": ddec
                        })
                else:
                    # Full position (first frame or no delta encoding)
                    positions.append({
                        "id": star["id"],
                        "ra": current_ra,
                        "dec": current_dec,
                        "mag": star["mag"]
                    })
                
                # Store for next frame's delta calculation
                prev_positions[star["id"]] = {"ra": current_ra, "dec": current_dec}
                
            except Exception:
                continue
        
        frames.append({
            "frame_index": frame_idx,
            "epoch": round(epoch, 2),
            "epoch_display": format_epoch_display(epoch),
            "positions": positions
        })
    
    # Calculate payload size estimate
    payload_estimate = sys.getsizeof(str(frames))
    
    return {
        "start_epoch": start_epoch,
        "end_epoch": end_epoch,
        "frame_count": len(frames),
        "stars_per_frame": len(star_info),
        "frames": frames,
        "metadata": {
            "total_time_span": time_span,
            "time_per_frame": round(epoch_step, 2),
            "payload_bytes_estimate": payload_estimate,
            "encoding": "delta" if delta_encoding else "absolute",
            "star_ids": [s["id"] for s in star_info]  # For frontend to track stars
        }
    }


# ============================================================
# EXPORT ENDPOINT
# ============================================================

@router.get("/export")
async def export_temporal_data(
    target_epoch: float = Query(..., description="Epoch to export (decimal year)"),
    format: str = Query("csv", description="Export format: csv or json"),
    ra_min: Optional[float] = Query(None, ge=0, lt=360),
    ra_max: Optional[float] = Query(None, ge=0, lt=360),
    dec_min: Optional[float] = Query(None, ge=-90, le=90),
    dec_max: Optional[float] = Query(None, ge=-90, le=90),
    max_magnitude: Optional[float] = Query(None, description="Max magnitude filter"),
    limit: int = Query(1000, ge=1, le=50000, description="Max stars to export"),
    db: Session = Depends(get_db)
):
    """
    Export temporal star data in CSV or JSON format.
    
    Returns star positions at the specified epoch with:
    - Original positions (J2000)
    - Calculated positions at target epoch
    - Proper motion data
    - Position uncertainty
    - Metadata
    
    **Formats:**
    - CSV: id, source_id, ra_orig, dec_orig, ra_epoch, dec_epoch, epoch, pmra, pmdec, uncertainty_arcsec, magnitude
    - JSON: Full response with all metadata
    """
    from fastapi.responses import StreamingResponse
    from sqlalchemy import text
    import io
    import csv
    
    # Build SQL query with filters
    sql_parts = ["SELECT id, source_id, ra_deg, dec_deg, brightness_mag, raw_metadata FROM unified_star_catalog WHERE 1=1"]
    params = {}
    
    if ra_min is not None and ra_max is not None:
        if ra_min <= ra_max:
            sql_parts.append("AND ra_deg BETWEEN :ra_min AND :ra_max")
            params['ra_min'] = ra_min
            params['ra_max'] = ra_max
        else:
            sql_parts.append("AND (ra_deg >= :ra_min OR ra_deg <= :ra_max)")
            params['ra_min'] = ra_min
            params['ra_max'] = ra_max
    
    if dec_min is not None and dec_max is not None:
        sql_parts.append("AND dec_deg BETWEEN :dec_min AND :dec_max")
        params['dec_min'] = dec_min
        params['dec_max'] = dec_max
    
    if max_magnitude is not None:
        sql_parts.append("AND brightness_mag <= :max_mag")
        params['max_mag'] = max_magnitude
    
    sql_parts.append(f"LIMIT {limit}")
    
    sql_query = " ".join(sql_parts)
    result = db.execute(text(sql_query), params).fetchall()
    
    # Calculate temporal positions
    export_data = []
    for row in result:
        try:
            metadata = json.loads(row[5]) if isinstance(row[5], str) else (row[5] or {})
            pmra = metadata.get('pmra', 0)
            pmdec = metadata.get('pmdec', 0)
            parallax = metadata.get('parallax_mas', 0)
            
            # Calculate position at target epoch
            pos_result = temporal_calc.calculate_position_at_epoch(
                ra_deg=row[2],
                dec_deg=row[3],
                pmra_mas_yr=pmra if pmra else None,
                pmdec_mas_yr=pmdec if pmdec else None,
                target_epoch=target_epoch
            )
            
            export_data.append({
                "id": row[0],
                "source_id": row[1],
                "ra_j2000": row[2],
                "dec_j2000": row[3],
                "ra_epoch": pos_result.ra_deg,
                "dec_epoch": pos_result.dec_deg,
                "epoch": target_epoch,
                "pmra": pmra,
                "pmdec": pmdec,
                "parallax_mas": parallax,
                "uncertainty_arcsec": pos_result.uncertainty_arcsec,
                "magnitude": row[4],
                "delta_years": target_epoch - 2016.0
            })
        except Exception as e:
            continue
    
    # Return based on format
    if format.lower() == "json":
        return {
            "epoch": target_epoch,
            "epoch_display": format_epoch_display(target_epoch),
            "count": len(export_data),
            "filters": {
                "ra_range": [ra_min, ra_max] if ra_min is not None else None,
                "dec_range": [dec_min, dec_max] if dec_min is not None else None,
                "max_magnitude": max_magnitude
            },
            "stars": export_data,
            "export_timestamp": str(db.execute(text("SELECT datetime('now')")).scalar())
        }
    
    elif format.lower() == "csv":
        # Generate CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'id', 'source_id', 'ra_j2000', 'dec_j2000', 'ra_epoch', 'dec_epoch',
            'epoch', 'pmra', 'pmdec', 'parallax_mas', 'uncertainty_arcsec', 
            'magnitude', 'delta_years'
        ])
        writer.writeheader()
        writer.writerows(export_data)
        
        # Return as downloadable file
        output.seek(0)
        epoch_str = format_epoch_display(target_epoch).replace(" ", "_")
        filename = f"temporal_export_epoch_{epoch_str}.csv"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}. Use 'csv' or 'json'")
