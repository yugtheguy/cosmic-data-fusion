"""
Discovery Overlay API Endpoints

Provides REST API endpoints for querying the catalog with AI discovery metadata enrichment.
Supports filtering by anomalies, clusters, and comparing discovery runs.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.discovery_overlay import DiscoveryOverlayService


router = APIRouter(prefix="/discovery", tags=["Discovery Overlay"])


# ==================== Request/Response Schemas ====================

class DiscoveryQueryRequest(BaseModel):
    """Request schema for querying with discovery overlay"""
    run_id: str = Field(..., description="Discovery run ID (UUID) to overlay")
    ra_min: Optional[float] = Field(None, description="Minimum Right Ascension")
    ra_max: Optional[float] = Field(None, description="Maximum Right Ascension")
    dec_min: Optional[float] = Field(None, description="Minimum Declination")
    dec_max: Optional[float] = Field(None, description="Maximum Declination")
    original_source: Optional[str] = Field(None, description="Filter by catalog source")
    limit: int = Field(100, ge=1, le=10000, description="Maximum results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class AnomalyQueryRequest(BaseModel):
    """Request schema for finding anomalies"""
    run_id: str = Field(..., description="Discovery run ID (UUID)")
    ra_min: Optional[float] = None
    ra_max: Optional[float] = None
    dec_min: Optional[float] = None
    dec_max: Optional[float] = None
    original_source: Optional[str] = None
    limit: int = Field(100, ge=1, le=10000)
    offset: int = Field(0, ge=0)


class ClusterMembersRequest(BaseModel):
    """Request schema for finding cluster members"""
    run_id: str = Field(..., description="Discovery run ID (UUID)")
    cluster_id: int = Field(..., description="Cluster ID to retrieve")
    ra_min: Optional[float] = None
    ra_max: Optional[float] = None
    dec_min: Optional[float] = None
    dec_max: Optional[float] = None
    original_source: Optional[str] = None
    limit: int = Field(100, ge=1, le=10000)
    offset: int = Field(0, ge=0)


class CompareRunsRequest(BaseModel):
    """Request schema for comparing two discovery runs"""
    run_id_1: str = Field(..., description="First discovery run ID (UUID)")
    run_id_2: str = Field(..., description="Second discovery run ID (UUID)")
    ra_min: Optional[float] = None
    ra_max: Optional[float] = None
    dec_min: Optional[float] = None
    dec_max: Optional[float] = None
    original_source: Optional[str] = None


class StarWithDiscovery(BaseModel):
    """Star catalog entry with discovery metadata"""
    star_id: int
    ra: float
    dec: float
    parallax: Optional[float]
    pm_ra: Optional[float]
    pm_dec: Optional[float]
    radial_velocity: Optional[float]
    magnitude: Optional[float]
    original_source: str
    is_anomaly: Optional[bool]
    anomaly_score: Optional[float]
    cluster_id: Optional[int]


class DiscoveryRunSummary(BaseModel):
    """Summary of a discovery run"""
    run_id: str  # UUID as string
    run_type: str
    parameters: dict
    total_stars: int
    timestamp: str


class DiscoveryQueryResponse(BaseModel):
    """Response for discovery query"""
    results: List[StarWithDiscovery]
    total_count: int
    run_info: DiscoveryRunSummary


class ComparisonRunInfo(BaseModel):
    """Metadata for a run in comparison"""
    run_id: str
    parameters: dict


class ComparisonResult(BaseModel):
    """Result of comparing two discovery runs"""
    comparison_type: str
    run1: ComparisonRunInfo
    run2: ComparisonRunInfo
    results: List[dict]  # Flexible to support different comparison types
    stats: dict


# ==================== API Endpoints ====================

def _flatten_discovery_response(service_response: dict) -> dict:
    """
    Transform service response from nested to flat structure for API response.
    Service returns: {star: {...}, discovery: {...}}
    API expects: flat dict with all fields
    """
    flattened_results = []
    for item in service_response.get("results", []):
        star = item.get("star", {})
        discovery = item.get("discovery", {})
        flattened_results.append({
            "star_id": star.get("id"),
            "ra": star.get("ra_deg"),
            "dec": star.get("dec_deg"),
            "parallax": star.get("parallax_mas"),
            "pm_ra": None,  # Not in UnifiedStarCatalog
            "pm_dec": None,  # Not in UnifiedStarCatalog
            "radial_velocity": None,  # Not in UnifiedStarCatalog
            "magnitude": star.get("brightness_mag"),
            "original_source": star.get("original_source"),
            "is_anomaly": discovery.get("is_anomaly"),
            "anomaly_score": discovery.get("anomaly_score"),
            "cluster_id": discovery.get("cluster_id")
        })
    
    run_info = service_response.get("run_info", {})
    return {
        "results": flattened_results,
        "total_count": service_response.get("total_count", 0),
        "run_info": {
            "run_id": run_info.get("run_id"),
            "run_type": run_info.get("run_type"),
            "parameters": run_info.get("parameters", {}),
            "total_stars": run_info.get("total_stars", 0),
            "timestamp": run_info.get("created_at")  # Service uses created_at
        }
    }

@router.post("/query", response_model=DiscoveryQueryResponse)
async def query_with_discovery(
    request: DiscoveryQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query the catalog with discovery overlay metadata.
    Returns stars enriched with anomaly/cluster information from the specified discovery run.
    """
    service = DiscoveryOverlayService(db)
    
    catalog_filters = {}
    if request.ra_min is not None:
        catalog_filters['ra_min'] = request.ra_min
    if request.ra_max is not None:
        catalog_filters['ra_max'] = request.ra_max
    if request.dec_min is not None:
        catalog_filters['dec_min'] = request.dec_min
    if request.dec_max is not None:
        catalog_filters['dec_max'] = request.dec_max
    if request.original_source is not None:
        catalog_filters['original_source'] = request.original_source
    
    result = service.query_with_discovery(
        run_id=request.run_id,
        filters=catalog_filters,
        limit=request.limit,
        offset=request.offset
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return _flatten_discovery_response(result)


@router.post("/anomalies", response_model=DiscoveryQueryResponse)
async def find_anomalies(
    request: AnomalyQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Find anomalies from a discovery run with optional spatial/catalog filters.
    Returns only stars marked as anomalies.
    """
    service = DiscoveryOverlayService(db)
    
    catalog_filters = {}
    if request.ra_min is not None:
        catalog_filters['ra_min'] = request.ra_min
    if request.ra_max is not None:
        catalog_filters['ra_max'] = request.ra_max
    if request.dec_min is not None:
        catalog_filters['dec_min'] = request.dec_min
    if request.dec_max is not None:
        catalog_filters['dec_max'] = request.dec_max
    if request.original_source is not None:
        catalog_filters['original_source'] = request.original_source
    
    result = service.find_anomalies(
        filters=catalog_filters,
        run_id=request.run_id,
        limit=request.limit,
        offset=request.offset
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return _flatten_discovery_response(result)


@router.post("/clusters/members", response_model=DiscoveryQueryResponse)
async def find_cluster_members(
    request: ClusterMembersRequest,
    db: Session = Depends(get_db)
):
    """
    Find all members of a specific cluster from a discovery run.
    Returns stars belonging to the specified cluster.
    """
    service = DiscoveryOverlayService(db)
    
    catalog_filters = {}
    if request.ra_min is not None:
        catalog_filters['ra_min'] = request.ra_min
    if request.ra_max is not None:
        catalog_filters['ra_max'] = request.ra_max
    if request.dec_min is not None:
        catalog_filters['dec_min'] = request.dec_min
    if request.dec_max is not None:
        catalog_filters['dec_max'] = request.dec_max
    if request.original_source is not None:
        catalog_filters['original_source'] = request.original_source
    
    result = service.find_cluster_members(
        cluster_id=request.cluster_id,
        filters=catalog_filters,
        run_id=request.run_id,
        limit=request.limit,
        offset=request.offset
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return _flatten_discovery_response(result)


@router.post("/compare", response_model=ComparisonResult)
async def compare_runs(
    request: CompareRunsRequest,
    db: Session = Depends(get_db)
):
    """
    Compare two discovery runs to find differences.
    Returns star IDs that appear in only one run or both runs.
    """
    service = DiscoveryOverlayService(db)
    
    catalog_filters = {}
    if request.ra_min is not None:
        catalog_filters['ra_min'] = request.ra_min
    if request.ra_max is not None:
        catalog_filters['ra_max'] = request.ra_max
    if request.dec_min is not None:
        catalog_filters['dec_min'] = request.dec_min
    if request.dec_max is not None:
        catalog_filters['dec_max'] = request.dec_max
    if request.original_source is not None:
        catalog_filters['original_source'] = request.original_source
    
    result = service.compare_runs(
        run_id_1=request.run_id_1,
        run_id_2=request.run_id_2,
        filters=catalog_filters
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/runs", response_model=List[DiscoveryRunSummary])
async def list_discovery_runs(
    run_type: Optional[str] = Query(None, description="Filter by run type"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List all discovery runs with optional filtering.
    Returns summary information for each run.
    """
    service = DiscoveryOverlayService(db)
    runs = service.discovery_repo.list_discovery_runs(
        run_type=run_type,
        limit=limit,
        offset=offset
    )
    
    return [
        DiscoveryRunSummary(
            run_id=run.run_id,
            run_type=run.run_type,
            parameters=run.parameters,
            total_stars=run.total_stars,
            timestamp=run.created_at.isoformat()
        )
        for run in runs
    ]


@router.get("/runs/{run_id}", response_model=DiscoveryRunSummary)
async def get_discovery_run(
    run_id: str,  # UUID as string
    db: Session = Depends(get_db)
):
    """
    Get details of a specific discovery run.
    """
    service = DiscoveryOverlayService(db)
    run = service.discovery_repo.get_discovery_run(run_id)
    
    if not run:
        raise HTTPException(status_code=404, detail=f"Discovery run {run_id} not found")
    
    return DiscoveryRunSummary(
        run_id=run.run_id,
        run_type=run.run_type,
        parameters=run.parameters,
        total_stars=run.total_stars,
        timestamp=run.created_at.isoformat()
    )
