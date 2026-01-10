"""
Visualization Service for COSMIC Data Fusion.

Provides data transformations and aggregations optimized for
frontend visualization libraries (scatter plots, heatmaps, charts).

All coordinates are already standardized to ICRS J2000 - no conversions needed.
"""

from typing import Optional
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models import UnifiedStarCatalog


class VisualizationService:
    """
    Service for generating visualization-ready astronomical data.
    
    Handles:
    - Sky map point extraction (scatter plots)
    - Spatial density binning (heatmaps)
    - Statistical aggregations (charts)
    """

    def __init__(self, db: Session):
        self.db = db

    def get_sky_points(
        self,
        limit: int = 10000,
        min_brightness: Optional[float] = None,
        max_brightness: Optional[float] = None
    ) -> list[dict]:
        """
        Retrieve RA/Dec points optimized for sky scatter plots.
        
        Returns lightweight point data suitable for rendering thousands
        of stars on a 2D projection (e.g., Mollweide, Aitoff).
        
        Args:
            limit: Maximum points to return (default 10000 for performance)
            min_brightness: Optional minimum magnitude filter
            max_brightness: Optional maximum magnitude filter
            
        Returns:
            List of dicts with ra, dec, brightness_mag, source_id
        """
        query = self.db.query(
            UnifiedStarCatalog.source_id,
            UnifiedStarCatalog.ra_deg,
            UnifiedStarCatalog.dec_deg,
            UnifiedStarCatalog.brightness_mag
        )

        if min_brightness is not None:
            query = query.filter(UnifiedStarCatalog.brightness_mag >= min_brightness)
        if max_brightness is not None:
            query = query.filter(UnifiedStarCatalog.brightness_mag <= max_brightness)

        # Order by brightness (brightest first) for visual priority
        query = query.order_by(UnifiedStarCatalog.brightness_mag.asc())
        query = query.limit(limit)

        results = query.all()

        return [
            {
                "source_id": row.source_id,
                "ra": row.ra_deg,
                "dec": row.dec_deg,
                "mag": row.brightness_mag
            }
            for row in results
        ]

    def get_density_grid(
        self,
        ra_bin_size: float = 10.0,
        dec_bin_size: float = 10.0
    ) -> list[dict]:
        """
        Generate binned star counts for density heatmap visualization.
        
        Divides the sky into rectangular bins and counts stars per bin.
        Output is optimized for 2D heatmap rendering.
        
        Args:
            ra_bin_size: Width of RA bins in degrees (default 10°)
            dec_bin_size: Height of Dec bins in degrees (default 10°)
            
        Returns:
            List of dicts with ra_bin, dec_bin, count for each non-empty bin
        """
        # Validate bin sizes
        ra_bin_size = max(1.0, min(ra_bin_size, 90.0))
        dec_bin_size = max(1.0, min(dec_bin_size, 45.0))

        # SQL floor division to compute bin indices
        # RA bins: 0-360 degrees
        # Dec bins: -90 to +90 degrees (shifted to 0-180 for binning)
        ra_bin_expr = func.floor(UnifiedStarCatalog.ra_deg / ra_bin_size) * ra_bin_size
        dec_bin_expr = func.floor((UnifiedStarCatalog.dec_deg + 90) / dec_bin_size) * dec_bin_size - 90

        query = self.db.query(
            ra_bin_expr.label("ra_bin"),
            dec_bin_expr.label("dec_bin"),
            func.count().label("count")
        ).group_by(
            ra_bin_expr,
            dec_bin_expr
        ).order_by(
            ra_bin_expr,
            dec_bin_expr
        )

        results = query.all()

        return [
            {
                "ra_bin": float(row.ra_bin),
                "dec_bin": float(row.dec_bin),
                "count": row.count
            }
            for row in results
        ]

    def get_catalog_stats(self) -> dict:
        """
        Compute comprehensive statistics for dashboard visualization.
        
        Returns aggregated metrics suitable for summary cards,
        histograms, and range indicators.
        
        Returns:
            Dict with total_stars, brightness stats, coordinate ranges,
            and source distribution
        """
        # Basic counts and ranges
        stats_query = self.db.query(
            func.count(UnifiedStarCatalog.id).label("total_stars"),
            func.min(UnifiedStarCatalog.ra_deg).label("ra_min"),
            func.max(UnifiedStarCatalog.ra_deg).label("ra_max"),
            func.min(UnifiedStarCatalog.dec_deg).label("dec_min"),
            func.max(UnifiedStarCatalog.dec_deg).label("dec_max"),
            func.min(UnifiedStarCatalog.brightness_mag).label("mag_min"),
            func.max(UnifiedStarCatalog.brightness_mag).label("mag_max"),
            func.avg(UnifiedStarCatalog.brightness_mag).label("mag_mean")
        ).first()

        # Brightness distribution (magnitude bins for histogram)
        mag_bins = self._compute_magnitude_histogram()

        # Source catalog distribution
        source_dist = self._compute_source_distribution()

        return {
            "total_stars": stats_query.total_stars or 0,
            "coordinate_ranges": {
                "ra": {
                    "min": float(stats_query.ra_min) if stats_query.ra_min else 0.0,
                    "max": float(stats_query.ra_max) if stats_query.ra_max else 360.0
                },
                "dec": {
                    "min": float(stats_query.dec_min) if stats_query.dec_min else -90.0,
                    "max": float(stats_query.dec_max) if stats_query.dec_max else 90.0
                }
            },
            "brightness": {
                "min_mag": float(stats_query.mag_min) if stats_query.mag_min else None,
                "max_mag": float(stats_query.mag_max) if stats_query.mag_max else None,
                "mean_mag": round(float(stats_query.mag_mean), 4) if stats_query.mag_mean else None,
                "histogram": mag_bins
            },
            "sources": source_dist
        }

    def _compute_magnitude_histogram(self) -> list[dict]:
        """
        Compute magnitude distribution in 1-mag bins for histogram display.
        
        Bins: <0, 0-1, 1-2, ..., 9-10, >10
        """
        # Use CASE expressions for magnitude binning
        mag_bin_expr = case(
            (UnifiedStarCatalog.brightness_mag < 0, -1),
            (UnifiedStarCatalog.brightness_mag < 1, 0),
            (UnifiedStarCatalog.brightness_mag < 2, 1),
            (UnifiedStarCatalog.brightness_mag < 3, 2),
            (UnifiedStarCatalog.brightness_mag < 4, 3),
            (UnifiedStarCatalog.brightness_mag < 5, 4),
            (UnifiedStarCatalog.brightness_mag < 6, 5),
            (UnifiedStarCatalog.brightness_mag < 7, 6),
            (UnifiedStarCatalog.brightness_mag < 8, 7),
            (UnifiedStarCatalog.brightness_mag < 9, 8),
            (UnifiedStarCatalog.brightness_mag < 10, 9),
            else_=10
        )

        query = self.db.query(
            mag_bin_expr.label("bin"),
            func.count().label("count")
        ).filter(
            UnifiedStarCatalog.brightness_mag.isnot(None)
        ).group_by(
            mag_bin_expr
        ).order_by(
            mag_bin_expr
        )

        results = query.all()

        # Format bin labels for display
        bin_labels = {
            -1: "<0",
            0: "0-1",
            1: "1-2",
            2: "2-3",
            3: "3-4",
            4: "4-5",
            5: "5-6",
            6: "6-7",
            7: "7-8",
            8: "8-9",
            9: "9-10",
            10: ">10"
        }

        return [
            {
                "bin_label": bin_labels.get(row.bin, f"{row.bin}"),
                "bin_start": row.bin if row.bin >= 0 else None,
                "count": row.count
            }
            for row in results
        ]

    def _compute_source_distribution(self) -> list[dict]:
        """
        Count stars by original source catalog.
        """
        query = self.db.query(
            UnifiedStarCatalog.original_source,
            func.count().label("count")
        ).group_by(
            UnifiedStarCatalog.original_source
        ).order_by(
            func.count().desc()
        )

        results = query.all()

        return [
            {
                "source": row.original_source or "unknown",
                "count": row.count
            }
            for row in results
        ]
