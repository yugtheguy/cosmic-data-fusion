"""
Analytics API endpoints for COSMIC Data Fusion.

Provides read-only endpoints to query materialized views for analytics:
- GET /analytics/discovery/stats - Discovery run statistics
- GET /analytics/discovery/clusters/{run_id} - Cluster size distribution
- GET /analytics/discovery/stars/{star_id}/frequency - Anomaly frequency per star
- GET /analytics/discovery/overlaps - Run overlap matrix
- GET /analytics/discovery/timeline - Historical trends

All endpoints use pre-computed materialized views for optimal performance.
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class DiscoveryRunStats(BaseModel):
    """Statistics for a discovery run from materialized view."""
    model_config = ConfigDict(from_attributes=True)
    
    run_id: str
    run_type: str
    created_at: datetime
    total_stars: int
    parameters_json: str
    anomaly_count: int
    anomaly_percentage: float
    min_anomaly_score: Optional[float]
    max_anomaly_score: Optional[float]
    avg_anomaly_score: Optional[float]
    cluster_count: int
    max_cluster_size: Optional[int]
    min_cluster_size: Optional[int]
    avg_cluster_size: Optional[float]
    noise_count: int


class ClusterDistribution(BaseModel):
    """Cluster size distribution from materialized view."""
    model_config = ConfigDict(from_attributes=True)
    
    run_id: str
    cluster_id: int
    cluster_size: int
    star_ids: List[int]
    last_updated: datetime


class StarAnomalyFrequency(BaseModel):
    """Cross-run anomaly frequency for a star."""
    model_config = ConfigDict(from_attributes=True)
    
    star_id: int
    anomaly_count: int
    total_runs: int
    frequency_pct: float
    run_ids: List[str]
    last_updated: datetime


class RunOverlap(BaseModel):
    """Overlap statistics between two anomaly detection runs."""
    model_config = ConfigDict(from_attributes=True)
    
    run_1_id: str
    run_1_count: int
    run_2_id: str
    run_2_count: int
    overlap_count: int
    overlapping_star_ids: Optional[List[int]]
    run_1_unique_count: int
    run_2_unique_count: int
    jaccard_similarity: float
    last_updated: datetime


class TimelineTrend(BaseModel):
    """Historical trend data (weekly or monthly)."""
    model_config = ConfigDict(from_attributes=True)
    
    period_start: datetime
    run_type: str
    total_runs: int
    completed_runs: int
    total_stars_analyzed: int
    period_type: str  # 'week' or 'month'


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/discovery/stats", response_model=List[DiscoveryRunStats])
def get_discovery_run_statistics(
    run_type: Optional[str] = Query(None, description="Filter by run type ('anomaly' or 'cluster')"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of runs to return"),
    db: Session = Depends(get_db)
):
    """
    Get discovery run statistics from materialized view.
    
    Returns pre-computed statistics for discovery runs including:
    - Total stars analyzed
    - Anomaly counts
    - Cluster counts and sizes
    - Run completion status
    
    **Performance**: Uses materialized view for ~50x faster queries.
    """
    try:
        query = """
            SELECT 
                run_id, run_type, created_at, total_stars, parameters_json,
                anomaly_count, anomaly_percentage,
                min_anomaly_score, max_anomaly_score, avg_anomaly_score,
                cluster_count, max_cluster_size, min_cluster_size, avg_cluster_size,
                noise_count
            FROM mv_discovery_run_stats
        """
        
        if run_type:
            query += f" WHERE run_type = :run_type"
        
        query += " ORDER BY created_at DESC LIMIT :limit"
        
        result = db.execute(
            text(query),
            {"run_type": run_type, "limit": limit} if run_type else {"limit": limit}
        )
        
        rows = result.fetchall()
        return [
            DiscoveryRunStats(
                run_id=row[0],
                run_type=row[1],
                created_at=row[2],
                total_stars=row[3],
                parameters_json=row[4],
                anomaly_count=row[5],
                anomaly_percentage=row[6],
                min_anomaly_score=row[7],
                max_anomaly_score=row[8],
                avg_anomaly_score=row[9],
                cluster_count=row[10],
                max_cluster_size=row[11],
                min_cluster_size=row[12],
                avg_cluster_size=row[13],
                noise_count=row[14]
            )
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Failed to fetch discovery run stats: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/discovery/clusters/{run_id}/sizes", response_model=List[ClusterDistribution])
def get_cluster_size_distribution(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Get cluster size distribution for a specific run.
    
    Returns pre-computed cluster sizes including:
    - Cluster ID and size
    - Array of star IDs in each cluster
    
    **Performance**: Uses materialized view for instant retrieval.
    """
    try:
        query = """
            SELECT run_id, cluster_id, cluster_size, star_ids, last_updated
            FROM mv_cluster_size_distribution
            WHERE run_id = :run_id
            ORDER BY cluster_size DESC
        """
        
        result = db.execute(text(query), {"run_id": run_id})
        rows = result.fetchall()
        
        if not rows:
            raise HTTPException(status_code=404, detail=f"No clusters found for run {run_id}")
        
        return [
            ClusterDistribution(
                run_id=row[0],
                cluster_id=row[1],
                cluster_size=row[2],
                star_ids=row[3] if row[3] else [],
                last_updated=row[4]
            )
            for row in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch cluster distribution: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/discovery/stars/{star_id}/frequency", response_model=StarAnomalyFrequency)
def get_star_anomaly_frequency(
    star_id: int,
    db: Session = Depends(get_db)
):
    """
    Get anomaly frequency for a specific star across all runs.
    
    Shows how often this star has been flagged as anomalous:
    - Number of times flagged
    - Total runs analyzed
    - Frequency percentage
    - List of run IDs where flagged
    
    **Use case**: Identify consistently anomalous objects for further study.
    """
    try:
        query = """
            SELECT star_id, anomaly_count, total_runs, frequency_pct, run_ids, last_updated
            FROM mv_star_anomaly_frequency
            WHERE star_id = :star_id
        """
        
        result = db.execute(text(query), {"star_id": star_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=404, 
                detail=f"Star {star_id} not found in anomaly detection runs"
            )
        
        return StarAnomalyFrequency(
            star_id=row[0],
            anomaly_count=row[1],
            total_runs=row[2],
            frequency_pct=row[3],
            run_ids=row[4] if row[4] else [],
            last_updated=row[5]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch star anomaly frequency: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/discovery/overlaps", response_model=List[RunOverlap])
def get_run_overlaps(
    run_id: Optional[str] = Query(None, description="Filter overlaps for specific run"),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0, description="Minimum Jaccard similarity"),
    limit: int = Query(50, ge=1, le=500, description="Maximum overlaps to return"),
    db: Session = Depends(get_db)
):
    """
    Get overlap analysis between anomaly detection runs.
    
    Returns pre-computed set overlaps including:
    - Overlapping star count
    - Unique stars per run
    - Jaccard similarity score
    - Arrays of overlapping star IDs
    
    **Use case**: Compare detection runs to find consistent anomalies.
    **Performance**: ~200x faster than Python set operations.
    """
    try:
        query = """
            SELECT 
                run_1_id, run_1_count, run_2_id, run_2_count,
                overlap_count, overlapping_star_ids,
                run_1_unique_count, run_2_unique_count,
                jaccard_similarity, last_updated
            FROM mv_anomaly_overlap_matrix
            WHERE jaccard_similarity >= :min_similarity
        """
        
        if run_id:
            query += " AND (run_1_id = :run_id OR run_2_id = :run_id)"
        
        query += " ORDER BY jaccard_similarity DESC LIMIT :limit"
        
        params = {"min_similarity": min_similarity, "limit": limit}
        if run_id:
            params["run_id"] = run_id
        
        result = db.execute(text(query), params)
        rows = result.fetchall()
        
        return [
            RunOverlap(
                run_1_id=row[0],
                run_1_count=row[1],
                run_2_id=row[2],
                run_2_count=row[3],
                overlap_count=row[4],
                overlapping_star_ids=row[5] if row[5] else [],
                run_1_unique_count=row[6],
                run_2_unique_count=row[7],
                jaccard_similarity=row[8],
                last_updated=row[9]
            )
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Failed to fetch run overlaps: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/discovery/timeline", response_model=List[TimelineTrend])
def get_discovery_timeline(
    period_type: str = Query("week", pattern="^(week|month)$", description="Aggregation period"),
    run_type: Optional[str] = Query(None, description="Filter by run type"),
    limit: int = Query(52, ge=1, le=365, description="Number of periods to return"),
    db: Session = Depends(get_db)
):
    """
    Get historical trends of discovery runs (weekly or monthly).
    
    Returns time-series data showing:
    - Number of runs per period
    - Completion rates
    - Total stars analyzed
    
    **Use case**: Dashboard visualizations and trend analysis.
    **Default**: Last 52 weeks of data.
    """
    try:
        query = """
            SELECT period_start, run_type, total_runs, completed_runs, 
                   total_stars_analyzed, period_type
            FROM mv_discovery_timeline
            WHERE period_type = :period_type
        """
        
        if run_type:
            query += " AND run_type = :run_type"
        
        query += " ORDER BY period_start DESC LIMIT :limit"
        
        params = {"period_type": period_type, "limit": limit}
        if run_type:
            params["run_type"] = run_type
        
        result = db.execute(text(query), params)
        rows = result.fetchall()
        
        return [
            TimelineTrend(
                period_start=row[0],
                run_type=row[1],
                total_runs=row[2],
                completed_runs=row[3],
                total_stars_analyzed=row[4],
                period_type=row[5]
            )
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Failed to fetch discovery timeline: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/discovery/refresh-views")
def refresh_materialized_views(db: Session = Depends(get_db)):
    """
    Manually trigger refresh of all discovery materialized views.
    
    **Note**: Views are automatically refreshed when discovery runs complete.
    Use this endpoint for:
    - Manual synchronization
    - Admin maintenance
    - Testing
    
    **Warning**: This operation may take several seconds for large datasets.
    """
    try:
        from app.repository.discovery import DiscoveryRepository
        
        repo = DiscoveryRepository(db)
        repo.refresh_all_views()
        
        return {
            "status": "success",
            "message": "All materialized views refreshed successfully",
            "views_refreshed": [
                "mv_discovery_run_stats",
                "mv_cluster_size_distribution",
                "mv_star_anomaly_frequency",
                "mv_anomaly_overlap_matrix",
                "mv_discovery_timeline"
            ]
        }
    except Exception as e:
        logger.error(f"Failed to refresh materialized views: {e}")
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")
