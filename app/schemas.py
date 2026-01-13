"""
Pydantic schemas for COSMIC Data Fusion API.

Handles input validation, coordinate frame specification, and response serialization.
All schemas use Pydantic v2 syntax.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class CoordinateFrame(str, Enum):
    """
    Supported input coordinate frames for astronomical data.
    
    ICRS: International Celestial Reference System
        - Modern standard, defined by distant quasars
        - Input: RA (0-360°), Dec (-90° to +90°)
    
    FK5: Fifth Fundamental Catalog (J2000 epoch)
        - Historical standard, nearly identical to ICRS
        - Input: RA (0-360°), Dec (-90° to +90°)
    
    GALACTIC: Galactic Coordinate System
        - Centered on Sun, aligned with Milky Way plane
        - Galactic center at l=0°, b=0°
        - Input: l (0-360°), b (-90° to +90°)
    """
    ICRS = "icrs"
    FK5 = "fk5"
    GALACTIC = "galactic"


# ============================================================
# INGESTION SCHEMAS
# ============================================================

class StarIngestRequest(BaseModel):
    """
    Schema for ingesting a single star observation.
    
    Coordinate interpretation depends on 'frame':
        - ICRS/FK5: coord1=RA, coord2=Dec (degrees)
        - GALACTIC: coord1=l, coord2=b (degrees)
    """
    
    source_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original catalog identifier"
    )
    coord1: float = Field(
        ...,
        description="RA (ICRS/FK5) or Galactic l, in degrees"
    )
    coord2: float = Field(
        ...,
        description="Dec (ICRS/FK5) or Galactic b, in degrees"
    )
    brightness_mag: float = Field(
        ...,
        ge=-30.0,
        le=40.0,
        description="Apparent magnitude"
    )
    original_source: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Source catalog name"
    )
    frame: CoordinateFrame = Field(
        default=CoordinateFrame.ICRS,
        description="Input coordinate frame"
    )
    
    @field_validator("coord1")
    @classmethod
    def normalize_coord1(cls, v: float) -> float:
        """Normalize longitude to [0, 360) range."""
        return v % 360.0
    
    @field_validator("coord2")
    @classmethod
    def validate_coord2(cls, v: float) -> float:
        """Validate latitude is within [-90, +90]."""
        if v < -90.0 or v > 90.0:
            raise ValueError("Latitude must be between -90 and +90 degrees")
        return v


class BulkIngestRequest(BaseModel):
    """Schema for bulk star ingestion."""
    
    stars: List[StarIngestRequest] = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="List of stars to ingest"
    )


# ============================================================
# SEARCH SCHEMAS
# ============================================================

class BoundingBoxParams(BaseModel):
    """
    Parameters for bounding-box coordinate search.
    
    Defines a rectangular region in ICRS coordinates.
    Note: Does not handle RA wrap-around at 0°/360°.
    """
    
    ra_min: float = Field(..., ge=0.0, lt=360.0, description="Min RA (degrees)")
    ra_max: float = Field(..., ge=0.0, lt=360.0, description="Max RA (degrees)")
    dec_min: float = Field(..., ge=-90.0, le=90.0, description="Min Dec (degrees)")
    dec_max: float = Field(..., ge=-90.0, le=90.0, description="Max Dec (degrees)")
    limit: int = Field(default=1000, ge=1, le=10000, description="Max results")
    
    @field_validator("ra_max")
    @classmethod
    def validate_ra_range(cls, v: float, info) -> float:
        ra_min = info.data.get("ra_min")
        if ra_min is not None and v < ra_min:
            raise ValueError("ra_max must be >= ra_min")
        return v
    
    @field_validator("dec_max")
    @classmethod
    def validate_dec_range(cls, v: float, info) -> float:
        dec_min = info.data.get("dec_min")
        if dec_min is not None and v < dec_min:
            raise ValueError("dec_max must be >= dec_min")
        return v


class ConeSearchParams(BaseModel):
    """
    Parameters for cone search (circular region).
    
    Uses astropy for proper angular separation calculation
    on the celestial sphere.
    """
    
    ra: float = Field(..., ge=0.0, lt=360.0, description="Center RA (degrees, ICRS)")
    dec: float = Field(..., ge=-90.0, le=90.0, description="Center Dec (degrees, ICRS)")
    radius: float = Field(
        ...,
        gt=0.0,
        le=180.0,
        description="Search radius in degrees"
    )
    limit: int = Field(default=1000, ge=1, le=10000, description="Max results")


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class StarResponse(BaseModel):
    """Response schema for star data."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    source_id: str
    ra_deg: float
    dec_deg: float
    brightness_mag: float
    original_source: str
    raw_frame: str
    created_at: datetime


class IngestResponse(BaseModel):
    """Response for single star ingestion."""
    
    success: bool
    message: str
    star: Optional[StarResponse] = None


class BulkIngestResponse(BaseModel):
    """Response for bulk ingestion."""
    
    success: bool
    message: str
    ingested_count: int
    failed_count: int
    stars: List[StarResponse]


class SearchResponse(BaseModel):
    """Response for search queries."""
    
    count: int
    stars: List[StarResponse]


class HealthResponse(BaseModel):
    """Response for health check."""
    
    status: str
    service: str
    database: str


# ============================================================
# DATASET INGESTION SCHEMAS
# ============================================================

class GaiaLoadResponse(BaseModel):
    """
    Response for Gaia dataset loading.
    
    Gaia data provided by ESA under the Gaia Archive terms.
    """
    
    success: bool
    message: str
    ingested_count: int
    skipped_count: int
    error_count: int
    source: str
    license_note: str


class DatasetStatsResponse(BaseModel):
    """Response for dataset statistics."""
    
    source: str
    record_count: int
    min_magnitude: Optional[float] = None
    max_magnitude: Optional[float] = None
    avg_magnitude: Optional[float] = None


# ============================================================
# VISUALIZATION SCHEMAS
# ============================================================

class SkyPoint(BaseModel):
    """
    Single point for sky map visualization.
    
    Coordinates are ICRS J2000 (already standardized).
    """
    
    source_id: str = Field(description="Original catalog identifier")
    ra: float = Field(description="Right Ascension in degrees (0-360)")
    dec: float = Field(description="Declination in degrees (-90 to +90)")
    mag: Optional[float] = Field(description="Apparent magnitude (brightness)")


class SkyPointsResponse(BaseModel):
    """
    Response for sky map scatter plot visualization.
    
    Points are sorted by brightness (brightest first) for
    visual priority when rendering limited datasets.
    
    Suitable for: D3.js, Plotly scatter_geo, Matplotlib
    """
    
    count: int = Field(description="Number of points returned")
    points: List[SkyPoint] = Field(description="Star positions for plotting")


class DensityCell(BaseModel):
    """
    Single cell in density grid for heatmap visualization.
    
    Represents star count in a rectangular sky region.
    """
    
    ra_bin: float = Field(description="RA bin left edge in degrees")
    dec_bin: float = Field(description="Dec bin bottom edge in degrees")
    count: int = Field(description="Number of stars in this bin")


class DensityGridResponse(BaseModel):
    """
    Response for density heatmap visualization.
    
    Provides binned star counts for 2D heatmap rendering.
    Empty bins are omitted for efficiency.
    
    Suitable for: Plotly heatmap, D3.js contour, Seaborn
    """
    
    ra_bin_size: float = Field(description="RA bin width in degrees")
    dec_bin_size: float = Field(description="Dec bin height in degrees")
    ra_bins: int = Field(description="Number of RA bins (360 / bin_size)")
    dec_bins: int = Field(description="Number of Dec bins (180 / bin_size)")
    total_cells: int = Field(description="Number of non-empty cells")
    cells: List[DensityCell] = Field(description="Density grid cells")


class CoordinateRange(BaseModel):
    """Min/max range for a coordinate axis."""
    
    min: float
    max: float


class CoordinateRanges(BaseModel):
    """RA and Dec ranges in the catalog."""
    
    ra: CoordinateRange = Field(description="RA range (0-360 degrees)")
    dec: CoordinateRange = Field(description="Dec range (-90 to +90 degrees)")


class MagnitudeBin(BaseModel):
    """Single bin in magnitude histogram."""
    
    bin_label: str = Field(description="Human-readable bin label (e.g., '3-4')")
    bin_start: Optional[int] = Field(description="Bin start magnitude (None for <0)")
    count: int = Field(description="Number of stars in this bin")


class BrightnessStats(BaseModel):
    """Brightness/magnitude statistics."""
    
    min_mag: Optional[float] = Field(description="Brightest star magnitude")
    max_mag: Optional[float] = Field(description="Faintest star magnitude")
    mean_mag: Optional[float] = Field(description="Mean magnitude")
    histogram: List[MagnitudeBin] = Field(description="Magnitude distribution")


class SourceCount(BaseModel):
    """Star count by source catalog."""
    
    source: str = Field(description="Source catalog name")
    count: int = Field(description="Number of stars from this source")


class CatalogStatsResponse(BaseModel):
    """
    Comprehensive catalog statistics for dashboard visualization.
    
    Provides all metrics needed for summary cards, histograms,
    pie charts, and range indicators.
    """
    
    total_stars: int = Field(description="Total stars in catalog")
    coordinate_ranges: CoordinateRanges = Field(description="RA/Dec coverage")
    brightness: BrightnessStats = Field(description="Magnitude statistics")
    sources: List[SourceCount] = Field(description="Stars per source catalog")