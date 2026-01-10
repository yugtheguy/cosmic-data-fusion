"""
SQLAlchemy ORM models for COSMIC Data Fusion.

All coordinates are stored in ICRS (International Celestial Reference System)
frame at J2000 epoch - the modern standard for astronomical catalogs.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime, Index

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
    
    Attributes:
        id: Auto-incrementing primary key
        source_id: Original identifier from source catalog
        ra_deg: Right Ascension in degrees [0, 360) ICRS J2000
        dec_deg: Declination in degrees [-90, +90] ICRS J2000
        brightness_mag: Apparent magnitude (lower = brighter)
        original_source: Name of source catalog (e.g., "Gaia DR3")
        raw_frame: Original coordinate frame before transformation
        created_at: UTC timestamp when record was created
    """
    
    __tablename__ = "unified_star_catalog"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Source identification
    source_id = Column(String(255), nullable=False, index=True)
    
    # ICRS J2000 coordinates (degrees)
    ra_deg = Column(Float, nullable=False)
    dec_deg = Column(Float, nullable=False)
    
    # Photometric data
    brightness_mag = Column(Float, nullable=False)
    
    # Provenance tracking
    original_source = Column(String(255), nullable=False, index=True)
    raw_frame = Column(String(50), nullable=False)
    
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
            f"<UnifiedStarCatalog(id={self.id}, source_id='{self.source_id}', "
            f"ra={self.ra_deg:.6f}°, dec={self.dec_deg:.6f}°, "
            f"mag={self.brightness_mag:.2f})>"
        )
