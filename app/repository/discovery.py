"""
Discovery Repository Layer

Provides database access layer for AI discovery operations.
Handles CRUD operations for DiscoveryRun and DiscoveryResult models.
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.models import DiscoveryRun, DiscoveryResult, UnifiedStarCatalog


class DiscoveryRepository:
    """
    Repository for managing discovery runs and results.
    
    Provides methods to:
    - Save and retrieve discovery runs
    - Store per-star discovery results
    - Query results by various criteria
    - Retrieve historical discovery data
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_discovery_run(
        self,
        run_type: str,
        parameters: Dict[str, Any],
        dataset_filter: Optional[Dict[str, Any]],
        total_stars: int,
        results_summary: Dict[str, Any]
    ) -> DiscoveryRun:
        """
        Create and save a new discovery run.
        
        Args:
            run_type: Type of discovery ('anomaly' or 'cluster')
            parameters: Algorithm parameters (contamination, eps, etc.)
            dataset_filter: Query filters used to select stars
            total_stars: Number of stars analyzed
            results_summary: Statistics summary (n_anomalies, n_clusters, etc.)
            
        Returns:
            DiscoveryRun: The created run with auto-generated run_id
        """
        run = DiscoveryRun(
            run_id=str(uuid4()),
            run_type=run_type,
            parameters=parameters,
            dataset_filter=dataset_filter,
            total_stars=total_stars,
            results_summary=results_summary
        )
        
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        
        return run
    
    def get_discovery_run(self, run_id: str) -> Optional[DiscoveryRun]:
        """
        Retrieve a discovery run by its ID.
        
        Args:
            run_id: UUID of the discovery run
            
        Returns:
            DiscoveryRun or None if not found
        """
        return self.db.query(DiscoveryRun).filter(
            DiscoveryRun.run_id == run_id
        ).first()
    
    def list_discovery_runs(
        self,
        run_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DiscoveryRun]:
        """
        List discovery runs with optional filtering and pagination.
        
        Args:
            run_type: Filter by run type ('anomaly' or 'cluster')
            limit: Maximum number of runs to return
            offset: Number of runs to skip
            
        Returns:
            List of DiscoveryRun objects, ordered by created_at descending
        """
        query = self.db.query(DiscoveryRun)
        
        if run_type:
            query = query.filter(DiscoveryRun.run_type == run_type)
        
        query = query.order_by(desc(DiscoveryRun.created_at))
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def save_discovery_results(
        self,
        run_id: str,
        results: List[Dict[str, Any]]
    ) -> int:
        """
        Batch save discovery results for a run.
        
        Args:
            run_id: UUID of the discovery run
            results: List of result dictionaries with keys:
                - star_id: int
                - is_anomaly: int (0 or 1)
                - anomaly_score: Optional[float]
                - cluster_id: Optional[int]
                
        Returns:
            Number of results saved
        """
        result_objects = [
            DiscoveryResult(
                run_id=run_id,
                star_id=r["star_id"],
                is_anomaly=r.get("is_anomaly", 0),
                anomaly_score=r.get("anomaly_score"),
                cluster_id=r.get("cluster_id")
            )
            for r in results
        ]
        
        self.db.bulk_save_objects(result_objects)
        self.db.commit()
        
        return len(result_objects)
    
    def mark_run_complete(self, run_id: str) -> bool:
        """
        Mark a discovery run as complete after all results are saved.
        
        Args:
            run_id: UUID of the discovery run
            
        Returns:
            True if run was marked complete, False if not found
        """
        run = self.get_discovery_run(run_id)
        if not run:
            return False
        
        run.is_complete = True
        self.db.commit()
        return True
    
    def get_results_by_run_id(
        self,
        run_id: str,
        limit: int = 1000,
        offset: int = 0
    ) -> List[DiscoveryResult]:
        """
        Retrieve all results for a specific discovery run.
        
        Args:
            run_id: UUID of the discovery run
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of DiscoveryResult objects
        """
        return self.db.query(DiscoveryResult).filter(
            DiscoveryResult.run_id == run_id
        ).limit(limit).offset(offset).all()
    
    def get_anomalies_by_run_id(
        self,
        run_id: str,
        limit: int = 1000,
        offset: int = 0
    ) -> List[DiscoveryResult]:
        """
        Retrieve only anomalies for a specific discovery run.
        
        Args:
            run_id: UUID of the discovery run
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of DiscoveryResult objects where is_anomaly=1
        """
        return self.db.query(DiscoveryResult).filter(
            and_(
                DiscoveryResult.run_id == run_id,
                DiscoveryResult.is_anomaly == 1
            )
        ).limit(limit).offset(offset).all()
    
    def get_cluster_members(
        self,
        run_id: str,
        cluster_id: int,
        limit: int = 1000,
        offset: int = 0
    ) -> List[DiscoveryResult]:
        """
        Retrieve all stars in a specific cluster.
        
        Args:
            run_id: UUID of the discovery run
            cluster_id: Cluster identifier (0, 1, 2, ...)
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of DiscoveryResult objects in the cluster
        """
        return self.db.query(DiscoveryResult).filter(
            and_(
                DiscoveryResult.run_id == run_id,
                DiscoveryResult.cluster_id == cluster_id
            )
        ).limit(limit).offset(offset).all()
    
    def get_results_with_star_data(
        self,
        run_id: str,
        anomalies_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve discovery results joined with star catalog data.
        
        Args:
            run_id: UUID of the discovery run
            anomalies_only: If True, return only anomalies
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of dictionaries with combined result + star data
        """
        query = self.db.query(DiscoveryResult, UnifiedStarCatalog).join(
            UnifiedStarCatalog,
            DiscoveryResult.star_id == UnifiedStarCatalog.id
        ).filter(DiscoveryResult.run_id == run_id)
        
        if anomalies_only:
            query = query.filter(DiscoveryResult.is_anomaly == 1)
        
        query = query.limit(limit).offset(offset)
        
        results = []
        for result, star in query.all():
            results.append({
                "result_id": result.id,
                "run_id": result.run_id,
                "star_id": result.star_id,
                "is_anomaly": bool(result.is_anomaly),
                "anomaly_score": result.anomaly_score,
                "cluster_id": result.cluster_id,
                "star": {
                    "object_id": star.object_id,
                    "source_id": star.source_id,
                    "ra_deg": star.ra_deg,
                    "dec_deg": star.dec_deg,
                    "brightness_mag": star.brightness_mag,
                    "parallax_mas": star.parallax_mas,
                    "distance_pc": star.distance_pc,
                    "original_source": star.original_source
                }
            })
        
        return results
    
    def count_results_by_run_id(self, run_id: str) -> int:
        """
        Count total results for a discovery run.
        
        Args:
            run_id: UUID of the discovery run
            
        Returns:
            Number of results
        """
        return self.db.query(DiscoveryResult).filter(
            DiscoveryResult.run_id == run_id
        ).count()
    
    # ==================== Materialized View Management ====================
    
    def refresh_discovery_run_stats(self, run_id: Optional[str] = None) -> None:
        """
        Refresh the mv_discovery_run_stats materialized view.
        
        Args:
            run_id: If specified, only refresh for this run (not supported by PostgreSQL MV)
                   If None, refreshes entire view
        """
        from sqlalchemy import text
        self.db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_discovery_run_stats"))
        self.db.commit()
    
    def refresh_cluster_size_distribution(self) -> None:
        """Refresh the mv_cluster_size_distribution materialized view."""
        from sqlalchemy import text
        self.db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_cluster_size_distribution"))
        self.db.commit()
    
    def refresh_star_anomaly_frequency(self) -> None:
        """Refresh the mv_star_anomaly_frequency materialized view."""
        from sqlalchemy import text
        self.db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_star_anomaly_frequency"))
        self.db.commit()
    
    def refresh_anomaly_overlap_matrix(self) -> None:
        """Refresh the mv_anomaly_overlap_matrix materialized view."""
        from sqlalchemy import text
        self.db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_anomaly_overlap_matrix"))
        self.db.commit()
    
    def refresh_discovery_timeline(self) -> None:
        """Refresh the mv_discovery_timeline materialized view."""
        from sqlalchemy import text
        self.db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_discovery_timeline"))
        self.db.commit()
    
    def refresh_all_views(self) -> None:
        """Refresh all materialized views. Use for nightly batch jobs."""
        self.refresh_discovery_run_stats()
        self.refresh_cluster_size_distribution()
        self.refresh_star_anomaly_frequency()
        self.refresh_anomaly_overlap_matrix()
        self.refresh_discovery_timeline()
    
    def count_anomalies_by_run_id(self, run_id: str) -> int:
        """
        Count anomalies for a discovery run.
        
        Args:
            run_id: UUID of the discovery run
            
        Returns:
            Number of anomalies (is_anomaly=1)
        """
        return self.db.query(DiscoveryResult).filter(
            and_(
                DiscoveryResult.run_id == run_id,
                DiscoveryResult.is_anomaly == 1
            )
        ).count()
