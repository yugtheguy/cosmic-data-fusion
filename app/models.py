"""
SQLAlchemy ORM models for COSMIC Data Fusion.

All coordinates are stored in ICRS (International Celestial Reference System)
frame at J2000 epoch - the modern standard for astronomical catalogs.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime, Index, JSON

from app.database import Base


class UnifiedStarCatalog(Base):
    """
    Unified star catalog with standardized ICRS J2000 coordinates.
    
    This model stores astronomical objects from various source catalogs,
    with all coordinates transformed to ICRS J2000 for consistency.
    
    Coordinate System Notes:
        - ICRS is defined by distant quasars (extragalactic sources)
        - Essentially equivalent to FK5 J2000 for most purposes
        - Float64 provides sub-microarcsecond precision
    
    Cross-Matching & Fusion:
        The `fusion_group_id` column links different observations of the same
        physical star across multiple catalogs. For example, if Gaia DR3 Object A
        and SDSS DR17 Object B are determined to be the same physical star
        (via positional cross-matching within a tolerance radius), they will
        share the same UUID in `fusion_group_id`.
        
        This enables:
        - Multi-wavelength analysis (combining photometry from different surveys)
        - Cross-validation of measurements across catalogs
        - Tracking observation history of individual stars
        - Resolving duplicate entries from overlapping surveys
    
    Attributes:
        id: Auto-incrementing primary key
        object_id: Unique identifier for the object
        source_id: Original identifier from source catalog
        ra_deg: Right Ascension in degrees [0, 360) ICRS J2000
        dec_deg: Declination in degrees [-90, +90] ICRS J2000
        brightness_mag: Apparent magnitude (lower = brighter)
        parallax_mas: Parallax in milliarcseconds
        distance_pc: Distance in parsecs (calculated from parallax)
        original_source: Name of source catalog (e.g., "Gaia DR3")
        raw_frame: Original coordinate frame before transformation
        observation_time: ISO datetime of observation
        dataset_id: Foreign key to dataset registry
        raw_metadata: JSON field for dataset-specific fields
        fusion_group_id: UUID linking observations of the same physical star
        created_at: UTC timestamp when record was created
    """
    
    __tablename__ = "unified_star_catalog"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Unique object identifier
    object_id = Column(String(255), unique=True, index=True, nullable=True)
    
    # Source identification
    source_id = Column(String(255), nullable=False, index=True)
    
    # ICRS J2000 coordinates (degrees)
    ra_deg = Column(Float, nullable=False)
    dec_deg = Column(Float, nullable=False)
    
    # Photometric data
    brightness_mag = Column(Float, nullable=False)
    
    # Distance measurements
    parallax_mas = Column(Float, nullable=True)  # Parallax in milliarcseconds
    distance_pc = Column(Float, nullable=True)   # Distance in parsecs
    
    # Provenance tracking
    original_source = Column(String(255), nullable=False, index=True)
    raw_frame = Column(String(50), nullable=False)
    observation_time = Column(DateTime, nullable=True)
    dataset_id = Column(String(255), nullable=True, index=True)
    
    # Raw metadata storage (JSON)
    raw_metadata = Column(JSON, nullable=True)
    
    # Cross-match fusion group
    # UUID linking different observations of the same physical star across catalogs
    # e.g., Gaia DR3 source and SDSS DR17 source that are the same star share this ID
    fusion_group_id = Column(String(36), nullable=True, index=True)
    
    # Audit timestamp
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Composite index for spatial queries
    # Significantly speeds up bounding-box searches
    __table_args__ = (
        Index("idx_ra_dec_spatial", "ra_deg", "dec_deg"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<UnifiedStarCatalog(id={self.id}, object_id='{self.object_id}', "
            f"source_id='{self.source_id}', "
            f"ra={self.ra_deg:.6f}°, dec={self.dec_deg:.6f}°, "
            f"mag={self.brightness_mag:.2f}, "
            f"distance={self.distance_pc:.2f}pc)>"
        )
