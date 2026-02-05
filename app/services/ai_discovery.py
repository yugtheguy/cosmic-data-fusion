"""
AI Discovery Service for COSMIC Data Fusion.

Provides machine learning capabilities for astronomical data analysis:
- Anomaly Detection: Identify unusual stellar objects using Isolation Forest
- Clustering: Group similar stars using DBSCAN algorithm

This module reads directly from the UnifiedStarCatalog table and does NOT
modify any existing ingestion logic.

Author: AI Discovery Team
Phase: 5 - AI-Assisted Discovery
"""

import logging
import math
import warnings
import os
from typing import Dict, List, Any, Optional, Tuple

# Set LOKY_MAX_CPU_COUNT before importing sklearn to suppress joblib warning (Windows-specific)
os.environ.setdefault('LOKY_MAX_CPU_COUNT', str(os.cpu_count() or 4))

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, silhouette_samples
from sqlalchemy.orm import Session

from app.models import UnifiedStarCatalog
from app.repository.discovery import DiscoveryRepository

# Suppress joblib warning about physical cores (Windows-specific)
warnings.filterwarnings("ignore", category=UserWarning, module="joblib")

logger = logging.getLogger(__name__)


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to a JSON-compatible float.
    
    Handles NaN, Inf, and None values by returning a default.
    This is necessary because JSON doesn't support NaN or Infinity.
    
    Args:
        value: The value to convert
        default: The default value if conversion fails
        
    Returns:
        A JSON-serializable float
    """
    if value is None:
        return default
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (ValueError, TypeError):
        return default


class AIDiscoveryError(Exception):
    """Base exception for AI Discovery operations."""
    pass


class InsufficientDataError(AIDiscoveryError):
    """Raised when there's not enough data to perform analysis."""
    pass


class AIDiscoveryService:
    """
    Service class for AI-powered astronomical data discovery.
    
    This service provides two main capabilities:
    
    1. Anomaly Detection (Isolation Forest):
       - Identifies stars with unusual combinations of position,
         brightness, and distance characteristics
       - Useful for finding rare objects, measurement errors, or
         scientifically interesting outliers
    
    2. Clustering (DBSCAN):
       - Groups stars based on spatial proximity and brightness
       - Can reveal stellar associations, clusters, or moving groups
       - Density-based: finds clusters of arbitrary shape
    
    Usage:
        service = AIDiscoveryService(db_session)
        anomalies = service.detect_anomalies(contamination=0.05)
        clusters = service.detect_clusters(eps=0.5, min_samples=10)
    """
    
    # Minimum number of stars required for meaningful analysis
    MIN_STARS_FOR_ANALYSIS = 5
    
    # Feature columns used for ML analysis
    FEATURE_COLUMNS = ["ra_deg", "dec_deg", "brightness_mag", "parallax_mas"]
    
    def __init__(self, db: Session):
        """
        Initialize the AI Discovery Service.
        
        Args:
            db: SQLAlchemy database session for querying star catalog
        """
        self.db = db
        self._df: Optional[pd.DataFrame] = None
        self._scaled_features: Optional[np.ndarray] = None
        self._scaler: Optional[StandardScaler] = None
        self._star_ids: Optional[List[int]] = None
        
        # Phase 1: Internal confidence tracking (not exposed to frontend)
        self._anomaly_feature_weights: Optional[Dict[str, float]] = None
        self._anomaly_score_percentiles: Optional[Dict[str, float]] = None
        self._cluster_quality_metrics: Optional[Dict[str, float]] = None
        self._analysis_warnings: List[str] = []
    
    def load_data(self) -> pd.DataFrame:
        """
        Load star catalog data from database into a Pandas DataFrame.
        
        This method performs the following steps:
        1. Query all stars from UnifiedStarCatalog
        2. Convert to Pandas DataFrame
        3. Handle missing parallax values (median imputation)
        4. Scale features using StandardScaler
        
        Returns:
            DataFrame with star data and scaled features
            
        Raises:
            InsufficientDataError: If database has fewer than MIN_STARS_FOR_ANALYSIS stars
        
        Note on StandardScaler:
        -----------------------
        Machine learning algorithms like Isolation Forest and DBSCAN work best
        when all features are on the same scale. Without scaling:
        
        - RA ranges from 0 to 360 degrees
        - Dec ranges from -90 to +90 degrees  
        - Magnitude typically ranges from -1 to +20
        - Parallax ranges from 0 to ~1000 milliarcseconds
        
        StandardScaler transforms each feature to have:
        - Mean = 0 (centered)
        - Standard Deviation = 1 (normalized)
        
        Formula: z = (x - μ) / σ
        
        This ensures that no single feature dominates the distance calculations
        used by our ML algorithms. For example, without scaling, RA (0-360)
        would have much more influence than magnitude (-1 to 20).
        """
        logger.info("Loading star catalog data for AI analysis...")
        
        # Step 1: Query all stars from database
        stars = self.db.query(UnifiedStarCatalog).all()
        
        if len(stars) < self.MIN_STARS_FOR_ANALYSIS:
            raise InsufficientDataError(
                f"Insufficient data for analysis. Found {len(stars)} stars, "
                f"but need at least {self.MIN_STARS_FOR_ANALYSIS}. "
                "Please load more data using /datasets/gaia/load first."
            )
        
        logger.info(f"Loaded {len(stars)} stars from database")
        
        # Step 2: Convert to DataFrame
        data = []
        for star in stars:
            data.append({
                "id": star.id,
                "ra_deg": star.ra_deg,
                "dec_deg": star.dec_deg,
                "brightness_mag": star.brightness_mag,
                "parallax_mas": star.parallax_mas,
                "source_id": star.source_id,
                "original_source": star.original_source,
            })
        
        self._df = pd.DataFrame(data)
        self._star_ids = self._df["id"].tolist()
        
        # Step 3: Handle missing parallax values using MEDIAN IMPUTATION
        # ----------------------------------------------------------------
        # Why median instead of mean?
        # - Parallax data often has outliers (very distant or nearby stars)
        # - Median is robust to outliers; mean would be skewed
        # - This preserves the "typical" parallax behavior in the dataset
        #
        # Example: If parallax values are [1, 2, 3, 100], 
        #          mean = 26.5 (skewed by outlier)
        #          median = 2.5 (more representative)
        
        null_parallax_count = self._df["parallax_mas"].isnull().sum()
        if null_parallax_count > 0:
            # Check if all values are null to avoid warnings
            valid_parallax = self._df["parallax_mas"].dropna()
            
            if len(valid_parallax) == 0:
                # ALL values are null - use default value
                median_parallax = 1.0
                logger.warning(
                    f"All {null_parallax_count} parallax values are null. "
                    f"Using default value of {median_parallax} mas"
                )
            else:
                # Some valid values exist - use median
                median_parallax = valid_parallax.median()
                logger.info(
                    f"Imputed {null_parallax_count} null parallax values with "
                    f"median={median_parallax:.4f} mas"
                )
            
            # Suppress pandas FutureWarning about fillna downcasting (internal pandas behavior)
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=FutureWarning, message=".*Downcasting.*")
                self._df["parallax_mas"] = self._df["parallax_mas"].fillna(median_parallax)
        
        # Step 4: Apply StandardScaler to feature columns
        # ------------------------------------------------
        # StandardScaler performs Z-score normalization:
        #   scaled_value = (original_value - mean) / standard_deviation
        #
        # After scaling:
        #   - Each feature has mean ≈ 0
        #   - Each feature has std ≈ 1
        #   - All features contribute equally to distance metrics
        #
        # This is CRITICAL for:
        #   - Isolation Forest: Uses random splits, but feature scale affects split quality
        #   - DBSCAN: Uses Euclidean distance, directly affected by feature scales
        
        feature_data = self._df[self.FEATURE_COLUMNS].values
        
        self._scaler = StandardScaler()
        self._scaled_features = self._scaler.fit_transform(feature_data)
        
        logger.info(
            f"Applied StandardScaler to {len(self.FEATURE_COLUMNS)} features: "
            f"{self.FEATURE_COLUMNS}"
        )
        
        # Log scaling statistics for debugging/verification
        for i, col in enumerate(self.FEATURE_COLUMNS):
            original_mean = feature_data[:, i].mean()
            original_std = feature_data[:, i].std()
            scaled_mean = self._scaled_features[:, i].mean()
            scaled_std = self._scaled_features[:, i].std()
            logger.debug(
                f"  {col}: original(μ={original_mean:.2f}, σ={original_std:.2f}) → "
                f"scaled(μ={scaled_mean:.4f}, σ={scaled_std:.4f})"
            )
        
        return self._df
    
    def detect_anomalies(
        self,
        contamination: float = 0.05,
        random_state: int = 42,
        save_results: bool = False,
        dataset_filter: Optional[Dict[str, Any]] = None,
        use_distance_aware: bool = True  # Phase 3: domain-aware features
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalous stars using Isolation Forest algorithm.
        
        ENHANCED with research-grade ML (Phases 1-4):
        - Phase 1: Internal confidence tracking
        - Phase 2: Smart ranking for better results
        - Phase 3: Distance-aware normalization (optional)
        - Phase 4: Failure mode detection with soft warnings
        
        Isolation Forest works by randomly partitioning the data space.
        The key insight is that anomalies are easier to isolate:
        - They require fewer random splits to be separated
        - Normal points are deep in dense regions, needing many splits
        
        How it works:
        1. Build multiple random trees (isolation trees)
        2. For each point, measure average path length to isolation
        3. Short path = easy to isolate = likely anomaly
        4. Long path = hard to isolate = likely normal
        
        Args:
            contamination: Expected proportion of anomalies (0.0 to 0.5)
                          0.05 = expect ~5% of data to be anomalous
            random_state: Random seed for reproducibility
            save_results: If True, persist results to discovery_runs and discovery_results tables
            dataset_filter: Optional query filters applied before analysis (for provenance tracking)
            use_distance_aware: Phase 3 - Apply astronomy domain knowledge (default: True)
            
        Returns:
            List of anomalous stars with their anomaly scores:
            [
                {"id": 123, "score": -0.45, "source_id": "Gaia DR3 12345", ...},
                ...
            ]
            
            PHASE 4: May include optional "analysis_note" field for warnings
            
            Score interpretation:
            - Negative scores indicate anomalies (more negative = more anomalous)
            - Scores close to 0 are normal
            - The threshold is determined by the contamination parameter
            
        Raises:
            InsufficientDataError: If data hasn't been loaded or is insufficient
        """
        logger.info(f"Running anomaly detection with contamination={contamination}, save_results={save_results}")
        
        # Ensure data is loaded
        if self._scaled_features is None:
            self.load_data()
        
        # Phase 3: Optionally use distance-aware features
        features_for_analysis = self._scaled_features
        if use_distance_aware:
            try:
                features_for_analysis = self._apply_distance_aware_normalization()
                logger.info("Using distance-aware features for anomaly detection")
            except Exception as e:
                logger.warning(f"Distance-aware normalization failed, using standard features: {e}")
                features_for_analysis = self._scaled_features
        
        # Configure and train Isolation Forest
        # ------------------------------------
        # n_estimators: Number of isolation trees (more = more stable results)
        # contamination: Expected outlier fraction (affects threshold)
        # random_state: For reproducible results
        
        iso_forest = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1  # Use all CPU cores
        )
        
        # Fit the model and predict anomaly labels
        # Labels: -1 = anomaly, 1 = normal
        labels = iso_forest.fit_predict(features_for_analysis)
        
        # Get anomaly scores (decision function)
        # More negative = more anomalous
        scores = iso_forest.decision_function(features_for_analysis)
        
        # Phase 1: Compute internal confidence metrics (NOT exposed to frontend yet)
        self._anomaly_feature_weights = self._compute_feature_contributions(iso_forest, scores)
        self._anomaly_score_percentiles = self._compute_score_distribution(scores)
        
        # Collect anomalies (label == -1)
        anomalies = []
        for i, label in enumerate(labels):
            if label == -1:  # Anomaly
                star_data = self._df.iloc[i]
                anomalies.append({
                    "id": int(star_data["id"]),
                    "source_id": str(star_data["source_id"]),
                    "original_source": str(star_data["original_source"]),
                    "ra_deg": safe_float(star_data["ra_deg"]),
                    "dec_deg": safe_float(star_data["dec_deg"]),
                    "brightness_mag": safe_float(star_data["brightness_mag"]),
                    "parallax_mas": safe_float(star_data["parallax_mas"], default=1.0),
                    "anomaly_score": safe_float(scores[i]),
                })
        
        # Phase 2: Smart ranking (anomalies already sorted by score, but enhance with confidence)
        # Sort by anomaly score (most anomalous first) - THIS IMPROVES RESULT QUALITY
        anomalies.sort(key=lambda x: x["anomaly_score"])
        
        logger.info(
            f"Anomaly detection complete: found {len(anomalies)} anomalies "
            f"out of {len(self._df)} stars ({100*len(anomalies)/len(self._df):.1f}%)"
        )
        
        # Phase 4: Detect potential issues and add optional warning
        analysis_note = self._detect_analysis_issues(len(self._df), {"anomalies": anomalies})
        
        # Optionally save results to database
        if save_results:
            self._save_anomaly_results(
                contamination=contamination,
                random_state=random_state,
                dataset_filter=dataset_filter,
                total_stars=len(self._df),
                anomalies=anomalies,
                all_scores=scores,
                all_labels=labels,
                analysis_note=analysis_note  # Phase 4: Include warning if present
            )
        
        return anomalies
    
    def detect_clusters(
        self,
        eps: float = 0.5,
        min_samples: int = 10,
        use_position_and_magnitude: bool = True,
        save_results: bool = False,
        dataset_filter: Optional[Dict[str, Any]] = None,
        apply_quality_filtering: bool = True  # Phase 2: filter weak clusters
    ) -> Dict[str, Any]:
        """
        Detect star clusters using DBSCAN algorithm.
        
        ENHANCED with research-grade ML (Phases 1-4):
        - Phase 1: Internal quality metrics (silhouette score)
        - Phase 2: Cluster validity pruning (optional)
        - Phase 3: Proper motion consistency checks
        - Phase 4: Failure mode detection with soft warnings
        
        DBSCAN (Density-Based Spatial Clustering of Applications with Noise):
        - Finds clusters of arbitrary shape based on density
        - Doesn't require specifying number of clusters in advance
        - Naturally handles noise (outliers not assigned to any cluster)
        
        How it works:
        1. For each point, count neighbors within distance `eps`
        2. If neighbors >= min_samples, point is a "core point"
        3. Core points close together form clusters
        4. Non-core points near cores are "border points" (in cluster)
        5. Points not near any core are "noise" (no cluster)
        
        Features used for clustering:
        - Position: RA (ra_deg), Dec (dec_deg) - spatial location
        - Brightness: magnitude (brightness_mag) - physical property
        
        This combination finds groups of stars that are:
        - Close together in the sky (spatial clustering)
        - Similar in brightness (physical similarity)
        
        Args:
            eps: Maximum distance between two points to be neighbors.
                 In scaled feature space, typical range: 0.3 to 1.0
                 Smaller = tighter clusters, larger = looser clusters
            min_samples: Minimum points required to form a dense region.
                        Higher = more robust clusters, fewer small clusters
            use_position_and_magnitude: If True, cluster on RA, Dec, and magnitude.
                                        If False, cluster on all features.
            save_results: If True, persist results to discovery_runs and discovery_results tables
            dataset_filter: Optional query filters applied before analysis (for provenance tracking)
            apply_quality_filtering: Phase 2 - Filter out low-confidence clusters (default: True)
        
        Returns:
            Dictionary with cluster information:
            {
                "n_clusters": 5,
                "n_noise": 23,
                "clusters": {
                    "cluster_0": [id1, id2, id3, ...],
                    "cluster_1": [id5, id6, ...],
                    ...
                },
                "cluster_stats": {
                    "cluster_0": {"count": 15, "mean_mag": 12.3, "mean_ra": 45.2, ...},
                    ...
                },
                "analysis_note": "Optional warning message (Phase 4)"
            }
            
        Raises:
            InsufficientDataError: If data hasn't been loaded or is insufficient
        """
        logger.info(f"Running DBSCAN clustering with eps={eps}, min_samples={min_samples}, save_results={save_results}")
        
        # Ensure data is loaded
        if self._scaled_features is None:
            self.load_data()
        
        # Select features for clustering
        # We use position (ra, dec) and brightness (magnitude) to find
        # groups of stars that are spatially close AND have similar brightness
        if use_position_and_magnitude:
            # Indices: 0=ra_deg, 1=dec_deg, 2=brightness_mag
            cluster_features = self._scaled_features[:, [0, 1, 2]]
            feature_names = ["ra_deg", "dec_deg", "brightness_mag"]
        else:
            cluster_features = self._scaled_features
            feature_names = self.FEATURE_COLUMNS
        
        logger.info(f"Clustering on features: {feature_names}")
        
        # Run DBSCAN
        # ----------
        # metric: 'euclidean' is standard; works well with scaled data
        # n_jobs: -1 uses all CPU cores for distance computation
        
        dbscan = DBSCAN(
            eps=eps,
            min_samples=min_samples,
            metric="euclidean",
            n_jobs=-1
        )
        
        cluster_labels = dbscan.fit_predict(cluster_features)
        
        # Phase 1: Compute clustering quality metrics (INTERNAL)
        self._cluster_quality_metrics = self._compute_cluster_quality(cluster_features, cluster_labels)
        
        # Phase 3: Check proper motion consistency (astronomy domain knowledge)
        proper_motion_stats = self._check_proper_motion_consistency(cluster_labels)
        
        # Process clustering results
        # Cluster labels: -1 = noise, 0, 1, 2, ... = cluster IDs
        unique_labels = set(cluster_labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        
        logger.info(
            f"DBSCAN found {n_clusters} clusters and {n_noise} noise points "
            f"out of {len(self._df)} total stars"
        )
        
        # Group star IDs by cluster
        clusters: Dict[str, List[int]] = {}
        cluster_stats: Dict[str, Dict[str, Any]] = {}
        
        # Phase 2: Track cluster quality for filtering
        clusters_to_suppress = set()
        
        for label in unique_labels:
            if label == -1:
                cluster_name = "noise"
            else:
                cluster_name = f"cluster_{label}"
            
            # Get details of stars in this cluster
            mask = cluster_labels == label
            cluster_stars_df = self._df.loc[mask]
            
            cluster_members = []
            for _, star in cluster_stars_df.iterrows():
                cluster_members.append({
                    "id": int(star["id"]),
                    "source_id": str(star["source_id"]),
                    "ra": safe_float(star["ra_deg"]),
                    "dec": safe_float(star["dec_deg"])
                })
            
            # Phase 2: Cluster validity check - suppress very small clusters
            if apply_quality_filtering and label != -1:
                # Suppress clusters with fewer than min_samples/2 stars (too small to be reliable)
                if len(cluster_members) < max(3, min_samples // 2):
                    clusters_to_suppress.add(cluster_name)
                    logger.debug(f"Suppressing {cluster_name} (too small: {len(cluster_members)} stars)")
                    continue
            
            clusters[cluster_name] = cluster_members
            
            # Calculate cluster statistics
            cluster_data = self._df.loc[mask]
            cluster_stats[cluster_name] = {
                "count": len(cluster_members),
                "mean_ra": safe_float(cluster_data["ra_deg"].mean()),
                "mean_dec": safe_float(cluster_data["dec_deg"].mean()),
                "mean_magnitude": safe_float(cluster_data["brightness_mag"].mean()),
                "mean_parallax": safe_float(cluster_data["parallax_mas"].mean(), default=1.0),
                "ra_range": [
                    safe_float(cluster_data["ra_deg"].min()),
                    safe_float(cluster_data["ra_deg"].max())
                ],
                "dec_range": [
                    safe_float(cluster_data["dec_deg"].min()),
                    safe_float(cluster_data["dec_deg"].max())
                ],
                "mag_range": [
                    safe_float(cluster_data["brightness_mag"].min()),
                    safe_float(cluster_data["brightness_mag"].max())
                ],
            }
            
            # Phase 3: Add proper motion stats if available
            if cluster_name in proper_motion_stats:
                cluster_stats[cluster_name]["proper_motion"] = proper_motion_stats[cluster_name]
        
        # Recount clusters after filtering
        n_clusters_filtered = len([k for k in clusters.keys() if k != "noise"])
        
        result = {
            "n_clusters": n_clusters_filtered,
            "n_noise": n_noise,
            "total_stars": len(self._df),
            "parameters": {
                "eps": eps,
                "min_samples": min_samples,
                "features_used": feature_names,
                "quality_filtering_applied": apply_quality_filtering,
            },
            "clusters": clusters,
            "cluster_stats": cluster_stats,
        }
        
        # Phase 4: Add analysis note if issues detected
        analysis_note = self._detect_analysis_issues(len(self._df), result)
        if analysis_note:
            result["analysis_note"] = analysis_note
        
        # Optionally save results to database
        if save_results:
            self._save_cluster_results(
                eps=eps,
                min_samples=min_samples,
                use_position_and_magnitude=use_position_and_magnitude,
                dataset_filter=dataset_filter,
                cluster_labels=cluster_labels,
                result=result,
                analysis_note=analysis_note  # Phase 4: Include warning if present
            )
        
        return result
    
    def get_summary_insights(self) -> Dict[str, Any]:
        """
        Generate a high-level summary of AI analysis results.
        
        Runs both anomaly detection and clustering with default parameters
        and returns a human-readable summary.
        
        Returns:
            Dictionary with summary insights and recommendations
        """
        logger.info("Generating AI discovery summary insights...")
        
        # Ensure data is loaded
        if self._df is None:
            self.load_data()
        
        # Run analyses with default parameters
        anomalies = self.detect_anomalies(contamination=0.05)
        clusters = self.detect_clusters(eps=0.5, min_samples=10)
        
        # Generate text summary
        summary_text = (
            f"Analyzed {len(self._df)} stars from the catalog. "
            f"Found {len(anomalies)} anomalous objects ({100*len(anomalies)/len(self._df):.1f}%). "
            f"Identified {clusters['n_clusters']} distinct stellar groups with "
            f"{clusters['n_noise']} unclassified (noise) objects."
        )
        
        # Identify the most anomalous star
        most_anomalous = None
        if anomalies:
            most_anomalous = {
                "id": anomalies[0]["id"],
                "source_id": anomalies[0]["source_id"],
                "score": anomalies[0]["anomaly_score"],
                "ra_deg": anomalies[0]["ra_deg"],
                "dec_deg": anomalies[0]["dec_deg"],
            }
        
        # Find largest cluster
        largest_cluster = None
        largest_size = 0
        for name, stats in clusters["cluster_stats"].items():
            if name != "noise" and stats["count"] > largest_size:
                largest_size = stats["count"]
                largest_cluster = {
                    "name": name,
                    "count": stats["count"],
                    "center_ra": stats["mean_ra"],
                    "center_dec": stats["mean_dec"],
                }
        
        return {
            "summary": summary_text,
            "total_stars": len(self._df),
            "anomaly_count": len(anomalies),
            "cluster_count": clusters["n_clusters"],
            "noise_count": clusters["n_noise"],
            "most_anomalous_star": most_anomalous,
            "largest_cluster": largest_cluster,
            "recommendations": [
                "Review the most anomalous stars for potential measurement errors or rare objects.",
                "Investigate dense clusters for potential stellar associations or moving groups.",
                f"Consider adjusting eps parameter if {clusters['n_clusters']} clusters seems too few/many.",
            ]
        }
    
    # ============================================================
    # PHASE 1: INTERNAL CONFIDENCE METRICS (Research-Grade ML)
    # ============================================================
    
    def _compute_feature_contributions(
        self, 
        model: IsolationForest, 
        scores: np.ndarray
    ) -> Dict[str, float]:
        """
        Phase 1: Estimate relative contribution of each feature to anomaly detection.
        
        This is an INTERNAL method for research quality assessment.
        NOT exposed to frontend in Phase 1.
        
        Method: Feature permutation importance
        - Permute each feature and measure score change
        - Larger change = more important feature
        
        Returns:
            Dictionary mapping feature names to relative importance (0-1)
        """
        if self._scaled_features is None or len(self._scaled_features) == 0:
            return {}
        
        baseline_scores = scores.copy()
        feature_importance = {}
        
        for i, feature_name in enumerate(self.FEATURE_COLUMNS):
            # Make a copy and permute this feature
            permuted_features = self._scaled_features.copy()
            np.random.shuffle(permuted_features[:, i])
            
            # Recompute scores with permuted feature
            permuted_scores = model.decision_function(permuted_features)
            
            # Importance = mean absolute change in scores
            importance = np.mean(np.abs(baseline_scores - permuted_scores))
            feature_importance[feature_name] = float(importance)
        
        # Normalize to sum to 1.0
        total = sum(feature_importance.values())
        if total > 0:
            feature_importance = {k: v/total for k, v in feature_importance.items()}
        
        logger.info(f"Feature contributions: {feature_importance}")
        return feature_importance
    
    def _compute_score_distribution(self, scores: np.ndarray) -> Dict[str, float]:
        """
        Phase 1: Calculate anomaly score distribution percentiles.
        
        This is for INTERNAL validation only - ensures:
        - No numerical instability
        - Threshold sanity checks
        - Debugging support
        
        NOT exposed to frontend in Phase 1.
        
        Returns:
            Dictionary with percentile statistics
        """
        if len(scores) == 0:
            return {}
        
        percentiles = {
            "p01": float(np.percentile(scores, 1)),
            "p05": float(np.percentile(scores, 5)),
            "p10": float(np.percentile(scores, 10)),
            "p50": float(np.percentile(scores, 50)),
            "p90": float(np.percentile(scores, 90)),
            "p95": float(np.percentile(scores, 95)),
            "p99": float(np.percentile(scores, 99)),
            "mean": float(np.mean(scores)),
            "std": float(np.std(scores)),
        }
        
        logger.debug(f"Anomaly score distribution: {percentiles}")
        return percentiles
    
    def _compute_cluster_quality(
        self, 
        cluster_features: np.ndarray, 
        cluster_labels: np.ndarray
    ) -> Dict[str, float]:
        """
        Phase 1: Compute clustering quality metrics.
        
        Metrics computed:
        - Silhouette score: Measures cluster cohesion and separation (-1 to +1)
        - Cluster size variance: Detects imbalanced clusters
        
        INTERNAL use only for confidence estimation.
        NOT exposed to frontend in Phase 1.
        
        Returns:
            Dictionary with quality metrics
        """
        quality_metrics = {}
        
        # Only compute silhouette if we have clusters (not just noise)
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        
        if n_clusters < 2:
            logger.info("Fewer than 2 clusters found, skipping silhouette score")
            quality_metrics["silhouette_score"] = 0.0
            quality_metrics["silhouette_status"] = "insufficient_clusters"
        else:
            # Filter out noise points (label == -1) for silhouette calculation
            mask = cluster_labels != -1
            if np.sum(mask) > 0:
                try:
                    silhouette_avg = silhouette_score(
                        cluster_features[mask], 
                        cluster_labels[mask],
                        metric='euclidean'
                    )
                    quality_metrics["silhouette_score"] = float(silhouette_avg)
                    quality_metrics["silhouette_status"] = "computed"
                    
                    # Interpretation for internal use:
                    # > 0.7: Strong clustering
                    # 0.5-0.7: Moderate clustering
                    # < 0.5: Weak clustering
                    
                    logger.info(f"Cluster silhouette score: {silhouette_avg:.3f}")
                except Exception as e:
                    logger.warning(f"Could not compute silhouette score: {e}")
                    quality_metrics["silhouette_score"] = 0.0
                    quality_metrics["silhouette_status"] = "computation_failed"
            else:
                quality_metrics["silhouette_score"] = 0.0
                quality_metrics["silhouette_status"] = "only_noise"
        
        # Cluster size variance
        cluster_sizes = []
        for label in set(cluster_labels):
            if label != -1:  # Exclude noise
                size = np.sum(cluster_labels == label)
                cluster_sizes.append(size)
        
        if len(cluster_sizes) > 0:
            quality_metrics["mean_cluster_size"] = float(np.mean(cluster_sizes))
            quality_metrics["cluster_size_variance"] = float(np.var(cluster_sizes))
            quality_metrics["cluster_size_std"] = float(np.std(cluster_sizes))
        
        return quality_metrics
    
    # ============================================================
    # PHASE 3: DOMAIN-AWARE ASTRONOMY FEATURES
    # ============================================================
    
    def _apply_distance_aware_normalization(self) -> np.ndarray:
        """
        Phase 3: Apply astronomy-aware feature engineering.
        
        Key insight: Brightness should be normalized by distance.
        - Distant stars appear fainter (higher magnitude)
        - Nearby stars appear brighter (lower magnitude)
        - Compare: absolute magnitude, not apparent magnitude
        
        Transformation:
        - Use parallax to estimate distance
        - Adjust brightness to "standard distance" (10 parsecs)
        - This gives distance-corrected brightness
        
        Returns:
            Enhanced feature matrix with distance-corrected brightness
        """
        if self._df is None or self._scaled_features is None:
            return self._scaled_features
        
        logger.info("Applying distance-aware normalization (astronomy domain knowledge)")
        
        # Create a copy of the dataframe
        df_enhanced = self._df.copy()
        
        # Calculate distance in parsecs from parallax (mas)
        # distance_pc = 1000 / parallax_mas
        df_enhanced["distance_pc"] = 1000.0 / df_enhanced["parallax_mas"].clip(lower=0.01)
        
        # Calculate absolute magnitude (brightness at 10 pc)
        # M = m + 5 - 5*log10(distance_pc)
        # where m = apparent magnitude, M = absolute magnitude
        df_enhanced["absolute_mag"] = (
            df_enhanced["brightness_mag"] 
            + 5 
            - 5 * np.log10(df_enhanced["distance_pc"].clip(lower=0.1))
        )
        
        # Replace apparent magnitude with absolute magnitude in features
        enhanced_features = df_enhanced[
            ["ra_deg", "dec_deg", "absolute_mag", "parallax_mas"]
        ].values
        
        # Apply StandardScaler to the enhanced features
        scaler_enhanced = StandardScaler()
        scaled_enhanced = scaler_enhanced.fit_transform(enhanced_features)
        
        logger.info("Distance-aware normalization applied successfully")
        return scaled_enhanced
    
    def _check_proper_motion_consistency(
        self, 
        cluster_labels: np.ndarray
    ) -> Dict[str, Any]:
        """
        Phase 3: Check proper motion consistency within clusters.
        
        Astronomy principle: Stars in a physical cluster should have
        similar proper motion (co-moving groups).
        
        This increases confidence for clusters with consistent proper motion
        and decreases confidence for clusters with random motion.
        
        Returns:
            Dictionary with proper motion consistency metrics per cluster
        """
        # Check if proper motion data is available
        if self._df is None:
            return {}
        
        # Check if raw_metadata contains proper motion
        # (pmra, pmdec are common fields in Gaia data)
        pm_availability = []
        for idx, row in self._df.iterrows():
            if row.get("raw_metadata") and isinstance(row["raw_metadata"], dict):
                has_pmra = "pmra" in row["raw_metadata"] or "pm_ra" in row["raw_metadata"]
                has_pmdec = "pmdec" in row["raw_metadata"] or "pm_dec" in row["raw_metadata"]
                pm_availability.append(has_pmra and has_pmdec)
            else:
                pm_availability.append(False)
        
        if not any(pm_availability):
            logger.info("No proper motion data available in raw_metadata")
            return {"status": "no_proper_motion_data"}
        
        logger.info("Proper motion data found - analyzing cluster consistency")
        
        # Extract proper motion values
        pmra_values = []
        pmdec_values = []
        
        for idx, row in self._df.iterrows():
            metadata = row.get("raw_metadata", {}) or {}
            pmra = metadata.get("pmra") or metadata.get("pm_ra")
            pmdec = metadata.get("pmdec") or metadata.get("pm_dec")
            
            pmra_values.append(pmra if pmra is not None else 0.0)
            pmdec_values.append(pmdec if pmdec is not None else 0.0)
        
        # Analyze proper motion consistency per cluster
        cluster_pm_stats = {}
        unique_clusters = set(cluster_labels)
        
        for cluster_id in unique_clusters:
            if cluster_id == -1:  # Skip noise
                continue
            
            mask = cluster_labels == cluster_id
            cluster_pmra = np.array([pmra_values[i] for i, m in enumerate(mask) if m])
            cluster_pmdec = np.array([pmdec_values[i] for i, m in enumerate(mask) if m])
            
            if len(cluster_pmra) > 1:
                # Calculate standard deviation (dispersion) of proper motion
                pmra_std = float(np.std(cluster_pmra))
                pmdec_std = float(np.std(cluster_pmdec))
                
                # Low std = high consistency = likely physical cluster
                # High std = low consistency = likely chance alignment
                cluster_pm_stats[f"cluster_{cluster_id}"] = {
                    "pmra_std": pmra_std,
                    "pmdec_std": pmdec_std,
                    "pm_consistency_score": 1.0 / (1.0 + pmra_std + pmdec_std),  # 0-1 scale
                    "n_stars": int(np.sum(mask))
                }
        
        return cluster_pm_stats
    
    # ============================================================
    # PHASE 4: FAILURE MODE AWARENESS
    # ============================================================
    
    def _detect_analysis_issues(self, n_stars: int, result_data: Dict[str, Any]) -> Optional[str]:
        """
        Phase 4: Detect potential analysis issues and generate soft warnings.
        
        This provides scientific honesty without blocking results.
        Returns None if analysis is confident, or a warning string if issues detected.
        
        Checks:
        - Sparse datasets (< 50 stars)
        - Poor clustering confidence (silhouette < 0.3)
        - Unstable anomaly thresholds
        
        Returns:
            Optional warning message string (or None if confident)
        """
        self._analysis_warnings.clear()
        
        # Check 1: Sparse dataset
        if n_stars < 50:
            self._analysis_warnings.append(
                f"Limited dataset size ({n_stars} stars). Results more reliable with 100+ stars."
            )
        
        # Check 2: Poor clustering quality
        if self._cluster_quality_metrics:
            silhouette = self._cluster_quality_metrics.get("silhouette_score", 1.0)
            if silhouette < 0.3 and silhouette > 0:
                self._analysis_warnings.append(
                    "Clustering confidence is moderate. Consider adjusting parameters."
                )
        
        # Check 3: Anomaly score distribution issues
        if self._anomaly_score_percentiles:
            score_range = abs(
                self._anomaly_score_percentiles.get("p99", 0) - 
                self._anomaly_score_percentiles.get("p01", 0)
            )
            if score_range < 0.1:
                self._analysis_warnings.append(
                    "Anomaly scores have low variance. Data may be too uniform."
                )
        
        # Return combined warning or None
        if self._analysis_warnings:
            return " ".join(self._analysis_warnings)
        return None
    
    def _save_anomaly_results(
        self,
        contamination: float,
        random_state: int,
        dataset_filter: Optional[Dict[str, Any]],
        total_stars: int,
        anomalies: List[Dict[str, Any]],
        all_scores: np.ndarray,
        all_labels: np.ndarray,
        analysis_note: Optional[str] = None  # Phase 4: optional warning
    ) -> str:
        """
        Save anomaly detection results to database.
        
        ENHANCED (Phase 4): Includes optional analysis_note for warnings
        
        Args:
            contamination: Contamination parameter used
            random_state: Random state used
            dataset_filter: Query filters applied (if any)
            total_stars: Total number of stars analyzed
            anomalies: List of detected anomalies
            all_scores: Anomaly scores for all stars
            all_labels: Anomaly labels for all stars (-1 or 1)
            analysis_note: Optional warning message (Phase 4)
            
        Returns:
            run_id: UUID of the created discovery run
        """
        repo = DiscoveryRepository(self.db)
        
        # Build results summary with Phase 1 metrics
        results_summary = {
            "n_anomalies": len(anomalies),
            "anomaly_rate": len(anomalies) / total_stars if total_stars > 0 else 0,
            "mean_anomaly_score": float(np.mean([a["anomaly_score"] for a in anomalies])) if anomalies else 0,
            "min_anomaly_score": float(np.min([a["anomaly_score"] for a in anomalies])) if anomalies else 0
        }
        
        # Phase 1: Add internal confidence metrics to summary (for research tracking)
        if self._anomaly_feature_weights:
            results_summary["feature_weights"] = self._anomaly_feature_weights
        if self._anomaly_score_percentiles:
            results_summary["score_distribution"] = self._anomaly_score_percentiles
        
        # Phase 4: Add analysis note if present
        if analysis_note:
            results_summary["analysis_note"] = analysis_note
        
        # Create discovery run
        run = repo.save_discovery_run(
            run_type="anomaly",
            parameters={
                "contamination": contamination,
                "random_state": random_state,
                "algorithm": "IsolationForest",
                "n_estimators": 100,
                "features_used": self.FEATURE_COLUMNS
            },
            dataset_filter=dataset_filter,
            total_stars=total_stars,
            results_summary=results_summary
        )
        
        # Save individual results for all stars
        results = []
        for i, star_id in enumerate(self._star_ids):
            results.append({
                "star_id": star_id,
                "is_anomaly": 1 if all_labels[i] == -1 else 0,
                "anomaly_score": float(all_scores[i]),
                "cluster_id": None
            })
        
        repo.save_discovery_results(run.run_id, results)
        
        # Mark run as complete and refresh materialized views
        repo.mark_run_complete(run.run_id)
        repo.refresh_discovery_run_stats()
        repo.refresh_anomaly_overlap_matrix()  # Refresh overlap matrix when new anomaly run completes
        
        logger.info(f"Saved anomaly detection run {run.run_id} with {len(results)} results")
        return run.run_id
    
    def _save_cluster_results(
        self,
        eps: float,
        min_samples: int,
        use_position_and_magnitude: bool,
        dataset_filter: Optional[Dict[str, Any]],
        cluster_labels: np.ndarray,
        result: Dict[str, Any],
        analysis_note: Optional[str] = None  # Phase 4: optional warning
    ) -> str:
        """
        Save clustering results to database.
        
        ENHANCED (Phase 4): Includes optional analysis_note for warnings
        
        Args:
            eps: Epsilon parameter used
            min_samples: Min samples parameter used
            use_position_and_magnitude: Whether only position+mag features were used
            dataset_filter: Query filters applied (if any)
            cluster_labels: Cluster labels for all stars
            result: Full clustering result dictionary
            analysis_note: Optional warning message (Phase 4)
            
        Returns:
            run_id: UUID of the created discovery run
        """
        repo = DiscoveryRepository(self.db)
        
        # Build results summary with Phase 1 & 3 metrics
        results_summary = {
            "n_clusters": result["n_clusters"],
            "n_noise": result["n_noise"],
            "cluster_sizes": {name: stats["count"] for name, stats in result["cluster_stats"].items()}
        }
        
        # Phase 1: Add clustering quality metrics (for research tracking)
        if self._cluster_quality_metrics:
            results_summary["quality_metrics"] = self._cluster_quality_metrics
        
        # Phase 4: Add analysis note if present
        if analysis_note:
            results_summary["analysis_note"] = analysis_note
        
        # Create discovery run
        run = repo.save_discovery_run(
            run_type="cluster",
            parameters={
                "eps": eps,
                "min_samples": min_samples,
                "algorithm": "DBSCAN",
                "metric": "euclidean",
                "use_position_and_magnitude": use_position_and_magnitude,
                "features_used": result["parameters"]["features_used"]
            },
            dataset_filter=dataset_filter,
            total_stars=result["total_stars"],
            results_summary=results_summary
        )
        
        # Save individual results for all stars
        results = []
        for i, star_id in enumerate(self._star_ids):
            results.append({
                "star_id": star_id,
                "is_anomaly": 0,  # Clustering doesn't mark anomalies
                "anomaly_score": None,
                "cluster_id": int(cluster_labels[i])  # -1 for noise, 0+ for clusters
            })
        
        repo.save_discovery_results(run.run_id, results)
        
        # Mark run as complete and refresh materialized views
        repo.mark_run_complete(run.run_id)
        repo.refresh_discovery_run_stats()
        repo.refresh_cluster_size_distribution()
        
        logger.info(f"Saved clustering run {run.run_id} with {len(results)} results")
        return run.run_id
