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
from sqlalchemy.orm import Session

from app.models import UnifiedStarCatalog

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
        random_state: int = 42
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalous stars using Isolation Forest algorithm.
        
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
            
        Returns:
            List of anomalous stars with their anomaly scores:
            [
                {"id": 123, "score": -0.45, "source_id": "Gaia DR3 12345", ...},
                ...
            ]
            
            Score interpretation:
            - Negative scores indicate anomalies (more negative = more anomalous)
            - Scores close to 0 are normal
            - The threshold is determined by the contamination parameter
            
        Raises:
            InsufficientDataError: If data hasn't been loaded or is insufficient
        """
        logger.info(f"Running anomaly detection with contamination={contamination}")
        
        # Ensure data is loaded
        if self._scaled_features is None:
            self.load_data()
        
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
        labels = iso_forest.fit_predict(self._scaled_features)
        
        # Get anomaly scores (decision function)
        # More negative = more anomalous
        scores = iso_forest.decision_function(self._scaled_features)
        
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
        
        # Sort by anomaly score (most anomalous first)
        anomalies.sort(key=lambda x: x["anomaly_score"])
        
        logger.info(
            f"Anomaly detection complete: found {len(anomalies)} anomalies "
            f"out of {len(self._df)} stars ({100*len(anomalies)/len(self._df):.1f}%)"
        )
        
        return anomalies
    
    def detect_clusters(
        self,
        eps: float = 0.5,
        min_samples: int = 10,
        use_position_and_magnitude: bool = True
    ) -> Dict[str, Any]:
        """
        Detect star clusters using DBSCAN algorithm.
        
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
                }
            }
            
        Raises:
            InsufficientDataError: If data hasn't been loaded or is insufficient
        """
        logger.info(f"Running DBSCAN clustering with eps={eps}, min_samples={min_samples}")
        
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
        
        return {
            "n_clusters": n_clusters,
            "n_noise": n_noise,
            "total_stars": len(self._df),
            "parameters": {
                "eps": eps,
                "min_samples": min_samples,
                "features_used": feature_names,
            },
            "clusters": clusters,
            "cluster_stats": cluster_stats,
        }
    
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
