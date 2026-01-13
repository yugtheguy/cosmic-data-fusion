"""
AI Discovery API endpoints for COSMIC Data Fusion.

Provides endpoints for machine learning analysis of astronomical data:
- POST /ai/anomalies - Detect anomalous stellar objects
- POST /ai/clusters  - Find star clusters
- POST /ai/insights  - Get summary AI insights

All endpoints read from the existing UnifiedStarCatalog table
without modifying any ingestion logic.

Phase: 5 - AI-Assisted Discovery
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.ai_discovery import (
    AIDiscoveryService,
    AIDiscoveryError,
    InsufficientDataError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Discovery"])


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class AnomalyDetectionRequest(BaseModel):
    """Request parameters for anomaly detection."""
    
    contamination: float = Field(
        default=0.05,
        ge=0.001,
        le=0.5,
        description=(
            "Expected proportion of anomalies in the dataset. "
            "Range: 0.001 to 0.5. Default 0.05 (5%)."
        ),
        examples=[0.05, 0.1, 0.01]
    )


class ClusteringRequest(BaseModel):
    """Request parameters for DBSCAN clustering."""
    
    eps: float = Field(
        default=0.5,
        gt=0.0,
        le=10.0,
        description=(
            "Maximum distance between two samples to be considered neighbors. "
            "In scaled feature space. Smaller values = tighter clusters."
        ),
        examples=[0.3, 0.5, 1.0]
    )
    
    min_samples: int = Field(
        default=10,
        ge=2,
        le=100,
        description=(
            "Minimum number of samples in a neighborhood to form a core point. "
            "Higher values = more robust clusters."
        ),
        examples=[5, 10, 20]
    )


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class AnomalyItem(BaseModel):
    """Single anomaly detection result."""
    id: int
    source_id: str
    original_source: str
    ra_deg: float
    dec_deg: float
    brightness_mag: float
    parallax_mas: float
    anomaly_score: float = Field(
        description="Anomaly score. More negative = more anomalous."
    )


class AnomalyDetectionResponse(BaseModel):
    """Response for anomaly detection endpoint."""
    success: bool
    message: str
    total_stars_analyzed: int
    anomaly_count: int
    contamination_used: float
    anomalies: list[AnomalyItem]


class ClusterStats(BaseModel):
    """Statistics for a single cluster."""
    count: int
    mean_ra: float
    mean_dec: float
    mean_magnitude: float
    mean_parallax: float
    ra_range: list[float]
    dec_range: list[float]
    mag_range: list[float]


class ClusteringResponse(BaseModel):
    """Response for clustering endpoint."""
    success: bool
    message: str
    n_clusters: int
    n_noise: int
    total_stars: int
    parameters: dict
    clusters: dict[str, list[int]]
    cluster_stats: dict[str, ClusterStats]


class InsightsSummary(BaseModel):
    """Response for AI insights endpoint."""
    success: bool
    summary: str
    total_stars: int
    anomaly_count: int
    cluster_count: int
    noise_count: int
    most_anomalous_star: Optional[dict]
    largest_cluster: Optional[dict]
    recommendations: list[str]


# ============================================================
# API ENDPOINTS
# ============================================================

@router.post(
    "/anomalies",
    response_model=AnomalyDetectionResponse,
    summary="Detect anomalous stars",
    description="""
Detect anomalous stellar objects using the Isolation Forest algorithm.

**How it works:**
- Loads all stars from the unified catalog
- Scales features (RA, Dec, magnitude, parallax) to normalize ranges
- Trains an Isolation Forest model to identify outliers
- Returns stars flagged as anomalies with their anomaly scores

**Parameters:**
- `contamination`: Expected fraction of anomalies (default: 5%)

**Use cases:**
- Find measurement errors or data quality issues
- Discover rare or unusual stellar objects
- Identify candidates for follow-up observation

**Score interpretation:**
- More negative scores = more anomalous
- Scores near 0 = normal behavior
    """
)
async def detect_anomalies(
    request: AnomalyDetectionRequest = AnomalyDetectionRequest(),
    db: Session = Depends(get_db)
) -> AnomalyDetectionResponse:
    """
    Run anomaly detection on the star catalog.
    
    Uses Isolation Forest algorithm with configurable contamination level.
    Returns list of stars identified as anomalies, sorted by anomaly score.
    """
    try:
        logger.info(f"AI anomaly detection requested with contamination={request.contamination}")
        
        service = AIDiscoveryService(db)
        service.load_data()
        anomalies = service.detect_anomalies(contamination=request.contamination)
        
        # Convert to response format
        anomaly_items = [AnomalyItem(**a) for a in anomalies]
        
        return AnomalyDetectionResponse(
            success=True,
            message=f"Successfully analyzed catalog. Found {len(anomalies)} anomalous stars.",
            total_stars_analyzed=len(service._df),
            anomaly_count=len(anomalies),
            contamination_used=request.contamination,
            anomalies=anomaly_items,
        )
        
    except InsufficientDataError as e:
        logger.warning(f"Insufficient data for anomaly detection: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "insufficient_data",
                "message": str(e),
                "suggestion": "Load more data using POST /datasets/gaia/load"
            }
        )
        
    except AIDiscoveryError as e:
        logger.error(f"AI discovery error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ai_discovery_error",
                "message": str(e)
            }
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error in anomaly detection: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": f"An unexpected error occurred: {str(e)}"
            }
        )


@router.post(
    "/clusters",
    response_model=ClusteringResponse,
    summary="Find star clusters",
    description="""
Group stars into clusters using the DBSCAN algorithm.

**How it works:**
- Loads all stars from the unified catalog
- Scales features for proper distance calculation
- Clusters based on position (RA, Dec) AND brightness (magnitude)
- Finds groups of stars that are spatially close AND have similar brightness

**Parameters:**
- `eps`: Maximum neighborhood distance (default: 0.5)
- `min_samples`: Minimum stars to form a cluster (default: 10)

**Why DBSCAN?**
- Finds clusters of arbitrary shape (not just spherical)
- Automatically determines number of clusters
- Identifies noise points (stars not in any cluster)

**Use cases:**
- Discover stellar associations or moving groups
- Find open clusters or globular cluster candidates
- Identify regions of similar stellar populations
    """
)
async def detect_clusters(
    request: ClusteringRequest = ClusteringRequest(),
    db: Session = Depends(get_db)
) -> ClusteringResponse:
    """
    Run DBSCAN clustering on the star catalog.
    
    Clusters stars based on position and brightness.
    Returns cluster assignments and statistics for each cluster.
    """
    try:
        logger.info(
            f"AI clustering requested with eps={request.eps}, "
            f"min_samples={request.min_samples}"
        )
        
        service = AIDiscoveryService(db)
        service.load_data()
        result = service.detect_clusters(
            eps=request.eps,
            min_samples=request.min_samples
        )
        
        # Convert cluster_stats to proper format
        cluster_stats_formatted = {}
        for name, stats in result["cluster_stats"].items():
            cluster_stats_formatted[name] = ClusterStats(**stats)
        
        return ClusteringResponse(
            success=True,
            message=f"Successfully clustered catalog. Found {result['n_clusters']} clusters.",
            n_clusters=result["n_clusters"],
            n_noise=result["n_noise"],
            total_stars=result["total_stars"],
            parameters=result["parameters"],
            clusters=result["clusters"],
            cluster_stats=cluster_stats_formatted,
        )
        
    except InsufficientDataError as e:
        logger.warning(f"Insufficient data for clustering: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "insufficient_data",
                "message": str(e),
                "suggestion": "Load more data using POST /datasets/gaia/load"
            }
        )
        
    except AIDiscoveryError as e:
        logger.error(f"AI discovery error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ai_discovery_error",
                "message": str(e)
            }
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error in clustering: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": f"An unexpected error occurred: {str(e)}"
            }
        )


@router.post(
    "/insights",
    response_model=InsightsSummary,
    summary="Get AI insights summary",
    description="""
Generate a comprehensive AI analysis summary of the star catalog.

Runs both anomaly detection and clustering with default parameters
and returns a human-readable summary with recommendations.

**Returns:**
- Summary text describing findings
- Count of anomalies and clusters
- Details on most anomalous star
- Details on largest cluster
- Recommendations for further analysis
    """
)
async def get_insights(
    db: Session = Depends(get_db)
) -> InsightsSummary:
    """
    Generate comprehensive AI insights for the star catalog.
    
    Combines anomaly detection and clustering results into
    a single summary with actionable recommendations.
    """
    try:
        logger.info("AI insights summary requested")
        
        service = AIDiscoveryService(db)
        insights = service.get_summary_insights()
        
        return InsightsSummary(
            success=True,
            **insights
        )
        
    except InsufficientDataError as e:
        logger.warning(f"Insufficient data for insights: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "insufficient_data",
                "message": str(e),
                "suggestion": "Load more data using POST /datasets/gaia/load"
            }
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error in insights generation: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": f"An unexpected error occurred: {str(e)}"
            }
        )
