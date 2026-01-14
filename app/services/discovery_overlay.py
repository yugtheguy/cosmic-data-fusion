"""
Discovery Overlay Service

Enriches query results with AI discovery information (anomalies, clusters).
Combines QueryBuilder with Discovery Repository to provide unified results.
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models import UnifiedStarCatalog, DiscoveryResult
from app.services.query_builder import QueryBuilder
from app.repository.discovery import DiscoveryRepository


class DiscoveryOverlayService:
    """
    Service for overlaying AI discovery results onto query results.
    
    This service combines:
    - Standard query filtering (from QueryBuilder)
    - AI discovery metadata (from DiscoveryRepository)
    
    Use cases:
    - "Show me all anomalous stars in this region"
    - "Find stars in cluster 3 with magnitude > 12"
    - "Get query results and highlight which ones are anomalies"
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.query_builder = QueryBuilder(db)
        self.discovery_repo = DiscoveryRepository(db)
    
    def query_with_discovery(
        self,
        run_id: str,
        filters: Optional[Dict[str, Any]] = None,
        anomalies_only: bool = False,
        cluster_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Query stars with discovery overlay from a specific run.
        
        This method:
        1. Retrieves discovery results for the specified run
        2. Applies optional filters (anomalies_only, cluster_id)
        3. Joins with star catalog data
        4. Returns enriched results
        
        Args:
            run_id: UUID of the discovery run to overlay
            filters: Optional query filters (magnitude, parallax, spatial, etc.)
            anomalies_only: If True, return only stars marked as anomalies
            cluster_id: If specified, return only stars in this cluster
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            Dictionary with:
            - run_info: Discovery run metadata
            - results: List of enriched star records with discovery metadata
            - total_count: Total matching results (before pagination)
            - returned_count: Number of results in this response
            
        Example:
            {
                "run_info": {
                    "run_id": "...",
                    "run_type": "anomaly",
                    "parameters": {...}
                },
                "results": [
                    {
                        "star": {...},  # Star catalog data
                        "discovery": {
                            "is_anomaly": true,
                            "anomaly_score": -0.75,
                            "cluster_id": null
                        }
                    },
                    ...
                ],
                "total_count": 250,
                "returned_count": 100
            }
        """
        # Get discovery run metadata
        run = self.discovery_repo.get_discovery_run(run_id)
        if not run:
            return {
                "error": f"Discovery run {run_id} not found",
                "results": [],
                "total_count": 0,
                "returned_count": 0
            }
        
        # Build base query joining DiscoveryResult with UnifiedStarCatalog
        query = self.db.query(DiscoveryResult, UnifiedStarCatalog).join(
            UnifiedStarCatalog,
            DiscoveryResult.star_id == UnifiedStarCatalog.id
        ).filter(DiscoveryResult.run_id == run_id)
        
        # Apply discovery filters
        if anomalies_only:
            query = query.filter(DiscoveryResult.is_anomaly == 1)
        
        if cluster_id is not None:
            query = query.filter(DiscoveryResult.cluster_id == cluster_id)
        
        # Apply catalog filters if provided
        if filters:
            query = self._apply_catalog_filters(query, filters)
        
        # Count total before pagination
        total_count = query.count()
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute query and format results
        results = []
        for discovery_result, star in query.all():
            results.append({
                "star": {
                    "id": star.id,
                    "object_id": star.object_id,
                    "source_id": star.source_id,
                    "ra_deg": star.ra_deg,
                    "dec_deg": star.dec_deg,
                    "brightness_mag": star.brightness_mag,
                    "parallax_mas": star.parallax_mas,
                    "distance_pc": star.distance_pc,
                    "original_source": star.original_source,
                    "fusion_group_id": star.fusion_group_id
                },
                "discovery": {
                    "is_anomaly": bool(discovery_result.is_anomaly),
                    "anomaly_score": discovery_result.anomaly_score,
                    "cluster_id": discovery_result.cluster_id
                }
            })
        
        return {
            "run_info": {
                "run_id": run.run_id,
                "run_type": run.run_type,
                "parameters": run.parameters,
                "total_stars": run.total_stars,
                "results_summary": run.results_summary,
                "created_at": run.created_at.isoformat() if run.created_at else None
            },
            "results": results,
            "total_count": total_count,
            "returned_count": len(results)
        }
    
    def find_anomalies(
        self,
        filters: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Find all anomalous stars, optionally from a specific run.
        
        Args:
            filters: Optional query filters
            run_id: If specified, use this run; otherwise use most recent anomaly run
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Dictionary with anomalous stars and discovery metadata
        """
        # If no run_id specified, use most recent anomaly run
        if not run_id:
            runs = self.discovery_repo.list_discovery_runs(run_type="anomaly", limit=1)
            if not runs:
                return {
                    "error": "No anomaly detection runs found",
                    "results": [],
                    "total_count": 0,
                    "returned_count": 0
                }
            run_id = runs[0].run_id
        
        # Use query_with_discovery with anomalies_only=True
        return self.query_with_discovery(
            run_id=run_id,
            filters=filters,
            anomalies_only=True,
            limit=limit,
            offset=offset
        )
    
    def find_cluster_members(
        self,
        cluster_id: int,
        filters: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Find all stars in a specific cluster.
        
        Args:
            cluster_id: Cluster identifier (0, 1, 2, ... or -1 for noise)
            filters: Optional query filters
            run_id: If specified, use this run; otherwise use most recent cluster run
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Dictionary with cluster members and discovery metadata
        """
        # If no run_id specified, use most recent clustering run
        if not run_id:
            runs = self.discovery_repo.list_discovery_runs(run_type="cluster", limit=1)
            if not runs:
                return {
                    "error": "No clustering runs found",
                    "results": [],
                    "total_count": 0,
                    "returned_count": 0
                }
            run_id = runs[0].run_id
        
        # Use query_with_discovery with cluster_id filter
        return self.query_with_discovery(
            run_id=run_id,
            filters=filters,
            cluster_id=cluster_id,
            limit=limit,
            offset=offset
        )
    
    def compare_runs(
        self,
        run_id_1: str,
        run_id_2: str,
        filters: Optional[Dict[str, Any]] = None,
        comparison_type: str = "anomaly_overlap"
    ) -> Dict[str, Any]:
        """
        Compare two discovery runs to find overlaps or differences.
        
        Args:
            run_id_1: First discovery run UUID
            run_id_2: Second discovery run UUID
            filters: Optional query filters
            comparison_type: Type of comparison:
                - "anomaly_overlap": Stars marked as anomalies in both runs
                - "anomaly_difference": Stars marked as anomaly in run1 but not run2
                - "cluster_stability": Stars in same cluster across runs
                
        Returns:
            Dictionary with comparison results and statistics
        """
        # Get run metadata
        run1 = self.discovery_repo.get_discovery_run(run_id_1)
        run2 = self.discovery_repo.get_discovery_run(run_id_2)
        
        if not run1 or not run2:
            return {
                "error": "One or both runs not found",
                "results": [],
                "stats": {}
            }
        
        # Build queries for both runs
        query1 = self.db.query(DiscoveryResult).filter(
            DiscoveryResult.run_id == run_id_1
        )
        query2 = self.db.query(DiscoveryResult).filter(
            DiscoveryResult.run_id == run_id_2
        )
        
        if comparison_type == "anomaly_overlap":
            # Find stars marked as anomalies in both runs
            query1 = query1.filter(DiscoveryResult.is_anomaly == 1)
            query2 = query2.filter(DiscoveryResult.is_anomaly == 1)
            
            results1 = {r.star_id: r for r in query1.all()}
            results2 = {r.star_id: r for r in query2.all()}
            
            overlap_star_ids = set(results1.keys()) & set(results2.keys())
            
            # Get star details for overlapping anomalies
            stars = self.db.query(UnifiedStarCatalog).filter(
                UnifiedStarCatalog.id.in_(overlap_star_ids)
            ).all()
            
            results = [
                {
                    "star": {
                        "id": star.id,
                        "source_id": star.source_id,
                        "ra_deg": star.ra_deg,
                        "dec_deg": star.dec_deg,
                        "brightness_mag": star.brightness_mag
                    },
                    "run1_score": results1[star.id].anomaly_score,
                    "run2_score": results2[star.id].anomaly_score
                }
                for star in stars
            ]
            
            return {
                "comparison_type": "anomaly_overlap",
                "run1": {"run_id": run_id_1, "parameters": run1.parameters},
                "run2": {"run_id": run_id_2, "parameters": run2.parameters},
                "results": results,
                "stats": {
                    "run1_anomalies": len(results1),
                    "run2_anomalies": len(results2),
                    "overlap_count": len(overlap_star_ids),
                    "overlap_percentage": len(overlap_star_ids) / max(len(results1), 1) * 100
                }
            }
        
        elif comparison_type == "anomaly_difference":
            # Find stars marked as anomaly in run1 but not run2
            query1 = query1.filter(DiscoveryResult.is_anomaly == 1)
            
            results1 = {r.star_id: r for r in query1.all()}
            results2_all = query2.all()
            results2 = {r.star_id: r for r in results2_all}
            results2_anomalies = {r.star_id for r in results2_all if r.is_anomaly == 1}
            
            diff_star_ids = set(results1.keys()) - results2_anomalies
            
            stars = self.db.query(UnifiedStarCatalog).filter(
                UnifiedStarCatalog.id.in_(diff_star_ids)
            ).all()
            
            results = [
                {
                    "star": {
                        "id": star.id,
                        "source_id": star.source_id,
                        "ra_deg": star.ra_deg,
                        "dec_deg": star.dec_deg,
                        "brightness_mag": star.brightness_mag
                    },
                    "run1_score": results1[star.id].anomaly_score,
                    "run2_score": results2.get(star.id).anomaly_score if star.id in results2 else None
                }
                for star in stars
            ]
            
            return {
                "comparison_type": "anomaly_difference",
                "run1": {"run_id": run_id_1, "parameters": run1.parameters},
                "run2": {"run_id": run_id_2, "parameters": run2.parameters},
                "results": results,
                "stats": {
                    "run1_only_count": len(diff_star_ids)
                }
            }
        
        return {
            "error": f"Unknown comparison_type: {comparison_type}",
            "results": [],
            "stats": {}
        }
    
    def _apply_catalog_filters(self, query, filters: Dict[str, Any]):
        """
        Apply catalog filters to a query.
        
        Args:
            query: SQLAlchemy query object
            filters: Dictionary of filter parameters
            
        Returns:
            Modified query with filters applied
        """
        # Magnitude filters
        if "magnitude_min" in filters:
            query = query.filter(UnifiedStarCatalog.brightness_mag >= filters["magnitude_min"])
        if "magnitude_max" in filters:
            query = query.filter(UnifiedStarCatalog.brightness_mag <= filters["magnitude_max"])
        
        # Parallax filters
        if "parallax_min" in filters:
            query = query.filter(UnifiedStarCatalog.parallax_mas >= filters["parallax_min"])
        if "parallax_max" in filters:
            query = query.filter(UnifiedStarCatalog.parallax_mas <= filters["parallax_max"])
        
        # Distance filters
        if "distance_min" in filters:
            query = query.filter(UnifiedStarCatalog.distance_pc >= filters["distance_min"])
        if "distance_max" in filters:
            query = query.filter(UnifiedStarCatalog.distance_pc <= filters["distance_max"])
        
        # Spatial filters (bounding box)
        if "ra_min" in filters:
            query = query.filter(UnifiedStarCatalog.ra_deg >= filters["ra_min"])
        if "ra_max" in filters:
            query = query.filter(UnifiedStarCatalog.ra_deg <= filters["ra_max"])
        if "dec_min" in filters:
            query = query.filter(UnifiedStarCatalog.dec_deg >= filters["dec_min"])
        if "dec_max" in filters:
            query = query.filter(UnifiedStarCatalog.dec_deg <= filters["dec_max"])
        
        # Source filter
        if "source" in filters:
            query = query.filter(UnifiedStarCatalog.original_source.ilike(f"%{filters['source']}%"))
        
        return query
