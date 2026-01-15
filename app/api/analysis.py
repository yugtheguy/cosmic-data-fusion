"""
Exoplanet Analysis API endpoints.

Provides endpoints for:
- Running BLS transit detection on TESS targets
- Retrieving exoplanet candidates
- Updating candidate validation status
"""

import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models_exoplanet import ExoplanetCandidate
from app.services.planet_hunter import PlanetHunterService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/analysis",
    tags=["Exoplanet Analysis"]
)


# ==================== Request/Response Models ====================

class PlanetHuntRequest(BaseModel):
    """Optional parameters for planet hunting."""
    min_period: float = Field(0.5, ge=0.1, le=100, description="Minimum period (days)")
    max_period: float = Field(20.0, ge=0.1, le=100, description="Maximum period (days)")
    num_periods: int = Field(10000, ge=1000, le=50000, description="Number of trial periods")


class PlanetHuntResponse(BaseModel):
    """Response from planet hunt analysis."""
    success: bool
    message: str
    candidate: Optional[dict] = None
    plot_data: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Planet candidate detected!",
                "candidate": {
                    "id": 1,
                    "source_id": "261136679",
                    "period_days": 3.852826,
                    "depth_percent": 0.453,
                    "power": 15.2
                },
                "plot_data": {
                    "phase_binned": [-0.5, -0.4, 0.0, 0.4, 0.5],
                    "flux_binned": [1.0, 1.0, 0.995, 1.0, 1.0]
                }
            }
        }


class CandidateListResponse(BaseModel):
    """List of exoplanet candidates."""
    total: int
    candidates: List[dict]


class UpdateStatusRequest(BaseModel):
    """Request to update candidate validation status."""
    status: str = Field(..., pattern="^(candidate|confirmed|false_positive|under_review)$")
    notes: Optional[str] = None


# ==================== API Endpoints ====================

@router.post(
    "/planet-hunt/{tic_id}",
    response_model=PlanetHuntResponse,
    summary="Hunt for exoplanets in TESS light curve",
    description="""
Analyze a TESS target star for exoplanet transits using Box Least Squares (BLS).

**Algorithm:**
1. Download TESS light curve from MAST archive
2. Preprocess: normalize, remove outliers, flatten stellar variability
3. Run BLS periodogram to detect periodic transit signals
4. Extract orbital parameters (period, depth, duration)
5. Fold light curve at detected period for visualization

**Example TIC IDs:**
- `261136679` - TOI 270 (known multi-planet system, Neptune-sized planets)
- `307210830` - TOI 700 (Earth-sized planet in habitable zone)
- `38846515` - Pi Mensae (super-Earth + Jupiter companion)

**Notes:**
- TESS has 30-minute cadence (~50,000 stars per sector)
- Not all stars have TESS data (only observed sectors)
- Analysis takes 30-60 seconds per target
"""
)
async def hunt_for_planets(
    tic_id: str = Path(..., description="TESS Input Catalog ID (e.g., '261136679')"),
    params: PlanetHuntRequest = PlanetHuntRequest(),
    db: Session = Depends(get_db)
):
    """
    Run exoplanet transit detection on a TESS target.
    
    Returns candidate parameters and visualization data for frontend plotting.
    """
    logger.info(f"Planet hunt requested for TIC {tic_id}")
    
    try:
        # Initialize service
        service = PlanetHunterService(db)
        
        # Run analysis
        candidate = service.analyze_tic_target(
            tic_id=tic_id,
            min_period=params.min_period,
            max_period=params.max_period,
            num_periods=params.num_periods,
            save_to_db=True
        )
        
        if not candidate:
            return PlanetHuntResponse(
                success=False,
                message=f"No TESS data available for TIC {tic_id}. "
                       "This star may not have been observed by TESS yet.",
                candidate=None,
                plot_data=None
            )
        
        # Parse visualization JSON
        viz_data = json.loads(candidate.visualization_json)
        
        # Prepare response
        return PlanetHuntResponse(
            success=True,
            message=f"Planet candidate detected! Period: {candidate.period:.4f} days, "
                   f"Depth: {candidate.depth*100:.3f}%, Power: {candidate.power:.2f}",
            candidate=candidate.to_dict(),
            plot_data={
                "phase_binned": viz_data["phase_binned"],
                "flux_binned": viz_data["flux_binned"],
                "phase_full": viz_data.get("phase_full", []),
                "flux_full": viz_data.get("flux_full", []),
                "period": viz_data["period"],
                "depth": viz_data["depth"],
                "duration_hours": viz_data["duration_hours"]
            }
        )
        
    except Exception as e:
        logger.error(f"Error during planet hunt for TIC {tic_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get(
    "/candidates",
    response_model=CandidateListResponse,
    summary="List all exoplanet candidates",
    description="""
Retrieve all detected exoplanet candidates from the database.

**Filters:**
- `status` - Filter by validation status (candidate, confirmed, false_positive)
- `min_power` - Minimum BLS detection power (higher = more significant)
- `limit` - Maximum number of results

**Status Definitions:**
- `candidate` - Initial detection, not yet validated
- `confirmed` - Validated as real exoplanet
- `false_positive` - Identified as stellar activity or systematic error
- `under_review` - Being analyzed by researchers
"""
)
async def get_candidates(
    status: Optional[str] = Query(None, description="Filter by status"),
    min_power: Optional[float] = Query(None, ge=0, description="Minimum BLS power"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    db: Session = Depends(get_db)
):
    """
    List exoplanet candidates with optional filters.
    """
    try:
        service = PlanetHunterService(db)
        
        candidates = service.get_all_candidates(
            status=status,
            min_power=min_power,
            limit=limit
        )
        
        return CandidateListResponse(
            total=len(candidates),
            candidates=[c.to_dict() for c in candidates]
        )
        
    except Exception as e:
        logger.error(f"Error retrieving candidates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve candidates: {str(e)}"
        )


@router.get(
    "/candidates/{tic_id}",
    response_model=CandidateListResponse,
    summary="Get candidates for specific TIC ID",
    description="Retrieve all exoplanet candidates detected for a given TESS target."
)
async def get_candidates_by_tic(
    tic_id: str = Path(..., description="TESS Input Catalog ID"),
    db: Session = Depends(get_db)
):
    """
    Get all candidates for a specific TIC ID.
    """
    try:
        service = PlanetHunterService(db)
        candidates = service.get_candidates_by_tic(tic_id)
        
        if not candidates:
            raise HTTPException(
                status_code=404,
                detail=f"No candidates found for TIC {tic_id}"
            )
        
        return CandidateListResponse(
            total=len(candidates),
            candidates=[c.to_dict() for c in candidates]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving candidates for TIC {tic_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve candidates: {str(e)}"
        )


@router.get(
    "/candidate/{candidate_id}",
    summary="Get candidate details with plot data",
    description="Retrieve full details and visualization data for a specific candidate."
)
async def get_candidate_detail(
    candidate_id: int = Path(..., description="Candidate database ID"),
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific candidate including plot data.
    """
    try:
        candidate = db.query(ExoplanetCandidate).get(candidate_id)
        
        if not candidate:
            raise HTTPException(
                status_code=404,
                detail=f"Candidate {candidate_id} not found"
            )
        
        # Parse visualization data
        viz_data = json.loads(candidate.visualization_json)
        
        return {
            "candidate": candidate.to_dict(),
            "plot_data": {
                "phase_binned": viz_data["phase_binned"],
                "flux_binned": viz_data["flux_binned"],
                "phase_full": viz_data.get("phase_full", []),
                "flux_full": viz_data.get("flux_full", [])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving candidate {candidate_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve candidate: {str(e)}"
        )


@router.patch(
    "/candidate/{candidate_id}/status",
    summary="Update candidate validation status",
    description="""
Update the validation status of an exoplanet candidate.

**Valid statuses:**
- `candidate` - Initial detection
- `confirmed` - Validated as real exoplanet
- `false_positive` - Not a real planet
- `under_review` - Being analyzed
"""
)
async def update_candidate_status(
    candidate_id: int = Path(..., description="Candidate database ID"),
    request: UpdateStatusRequest = ...,
    db: Session = Depends(get_db)
):
    """
    Update the validation status of a candidate.
    """
    try:
        service = PlanetHunterService(db)
        
        candidate = service.update_candidate_status(
            candidate_id=candidate_id,
            status=request.status,
            notes=request.notes
        )
        
        if not candidate:
            raise HTTPException(
                status_code=404,
                detail=f"Candidate {candidate_id} not found"
            )
        
        return {
            "success": True,
            "message": f"Candidate status updated to {request.status}",
            "candidate": candidate.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating candidate {candidate_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update candidate: {str(e)}"
        )


@router.delete(
    "/candidate/{candidate_id}",
    summary="Delete a candidate",
    description="Remove an exoplanet candidate from the database."
)
async def delete_candidate(
    candidate_id: int = Path(..., description="Candidate database ID"),
    db: Session = Depends(get_db)
):
    """
    Delete an exoplanet candidate.
    """
    try:
        candidate = db.query(ExoplanetCandidate).get(candidate_id)
        
        if not candidate:
            raise HTTPException(
                status_code=404,
                detail=f"Candidate {candidate_id} not found"
            )
        
        db.delete(candidate)
        db.commit()
        
        return {
            "success": True,
            "message": f"Candidate {candidate_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting candidate {candidate_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete candidate: {str(e)}"
        )
