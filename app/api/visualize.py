"""
Visualization API Routes for COSMIC Data Fusion.

Endpoints optimized for frontend chart and map libraries.
Returns pre-formatted data for scatter plots, heatmaps, and dashboards.

All data is in ICRS J2000 coordinates (already standardized).
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.visualization import VisualizationService
from app.schemas import (
    SkyPointsResponse,
    DensityGridResponse,
    CatalogStatsResponse
)


router = APIRouter(prefix="/visualize", tags=["visualization"])


@router.get("/sky", response_model=SkyPointsResponse)
def get_sky_map_points(
    limit: int = Query(
        default=10000,
        ge=1,
        le=100000,
        description="Maximum number of points to return"
    ),
    min_mag: Optional[float] = Query(
        default=None,
        description="Minimum magnitude (brightest)"
    ),
    max_mag: Optional[float] = Query(
        default=None,
        description="Maximum magnitude (faintest)"
    ),
    db: Session = Depends(get_db)
) -> SkyPointsResponse:
    """
    Get star positions for sky map scatter plot visualization.
    
    Returns RA/Dec coordinates with brightness values, optimized for
    rendering on 2D sky projections (Mollweide, Aitoff, equirectangular).
    
    Points are sorted by brightness (brightest first) to prioritize
    visually significant stars when rendering limits apply.
    
    **Visualization Use Cases:**
    - Interactive sky maps
    - All-sky scatter plots
    - Constellation overlays
    
    **Frontend Libraries:**
    - D3.js geo projections
    - Plotly scatter_geo
    - Matplotlib/Astropy sky plots
    """
    service = VisualizationService(db)
    points = service.get_sky_points(
        limit=limit,
        min_brightness=min_mag,
        max_brightness=max_mag
    )

    return SkyPointsResponse(
        count=len(points),
        points=points
    )


@router.get("/density", response_model=DensityGridResponse)
def get_density_heatmap(
    ra_bin: float = Query(
        default=10.0,
        ge=1.0,
        le=90.0,
        description="RA bin width in degrees"
    ),
    dec_bin: float = Query(
        default=10.0,
        ge=1.0,
        le=45.0,
        description="Dec bin height in degrees"
    ),
    db: Session = Depends(get_db)
) -> DensityGridResponse:
    """
    Get binned star density for heatmap visualization.
    
    Divides the celestial sphere into rectangular bins and returns
    star counts per bin. Suitable for density heatmap rendering.
    
    **Coordinate System:**
    - RA: 0° to 360° (bin edges align to multiples of bin size)
    - Dec: -90° to +90° (bin edges align to multiples of bin size)
    
    **Visualization Use Cases:**
    - Star density heatmaps
    - Survey coverage maps
    - Galactic structure visualization
    
    **Frontend Libraries:**
    - Plotly heatmap
    - D3.js contour/density
    - Seaborn heatmap (via API)
    
    **Performance Note:**
    Smaller bins = more cells = slower rendering.
    Recommended: 5-15° bins for overview, 1-5° for detailed regions.
    """
    service = VisualizationService(db)
    grid = service.get_density_grid(
        ra_bin_size=ra_bin,
        dec_bin_size=dec_bin
    )

    # Calculate grid dimensions
    ra_bins = int(360 / ra_bin)
    dec_bins = int(180 / dec_bin)

    return DensityGridResponse(
        ra_bin_size=ra_bin,
        dec_bin_size=dec_bin,
        ra_bins=ra_bins,
        dec_bins=dec_bins,
        total_cells=len(grid),
        cells=grid
    )


@router.get("/stats", response_model=CatalogStatsResponse)
def get_catalog_statistics(
    db: Session = Depends(get_db)
) -> CatalogStatsResponse:
    """
    Get comprehensive catalog statistics for dashboard visualization.
    
    Returns aggregated metrics including totals, ranges, distributions,
    and breakdowns suitable for summary cards and charts.
    
    **Visualization Use Cases:**
    - Dashboard summary cards
    - Magnitude histogram
    - Source pie chart
    - Coordinate range indicators
    
    **Included Statistics:**
    - Total star count
    - RA/Dec coordinate ranges
    - Brightness min/max/mean
    - Magnitude distribution histogram
    - Source catalog breakdown
    """
    service = VisualizationService(db)
    stats = service.get_catalog_stats()

    return CatalogStatsResponse(**stats)
