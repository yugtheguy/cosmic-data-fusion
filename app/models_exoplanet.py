"""
Exoplanet candidate database model.

Stores results from BLS transit detection on TESS light curves.
Each candidate represents a potential exoplanet detection.
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class ExoplanetCandidate(Base):
    """
    Exoplanet candidate detected via BLS transit analysis.
    
    Attributes:
        id: Primary key
        source_id: TESS Input Catalog (TIC) ID
        period: Orbital period in days
        transit_time: Time of first transit (BTJD - TESS Barycentric Julian Date)
        duration: Transit duration in hours
        depth: Transit depth (fractional flux loss, 0-1)
        power: BLS signal detection power (higher = more significant)
        snr: Signal-to-noise ratio of detection
        num_transits: Number of transits observed
        visualization_json: JSON with folded light curve (phase, flux arrays)
        analysis_timestamp: When the analysis was performed
        mission: Mission name (TESS, Kepler)
        sector: TESS sector number
        status: Validation status (candidate, confirmed, false_positive)
    """
    
    __tablename__ = "exoplanet_candidates"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Target identification
    source_id = Column(String(50), nullable=False, index=True, 
                      comment="TIC ID (e.g., '261136679')")
    
    # Orbital parameters
    period = Column(Float, nullable=False, 
                   comment="Orbital period in days")
    transit_time = Column(Float, nullable=False,
                         comment="Time of first transit (BTJD)")
    duration = Column(Float, nullable=False,
                     comment="Transit duration in hours")
    
    # Transit characteristics
    depth = Column(Float, nullable=False,
                  comment="Transit depth (fractional flux loss)")
    power = Column(Float, nullable=False,
                  comment="BLS signal detection power")
    snr = Column(Float, nullable=True,
                comment="Signal-to-noise ratio")
    num_transits = Column(Integer, nullable=True,
                         comment="Number of transits observed")
    
    # Visualization data
    visualization_json = Column(Text, nullable=False,
                               comment="JSON: {phase: [...], flux: [...], binned_phase: [...], binned_flux: [...]}")
    
    # Metadata
    analysis_timestamp = Column(DateTime, nullable=False, 
                               server_default=func.now(),
                               comment="When analysis was performed")
    mission = Column(String(20), nullable=False, default="TESS",
                    comment="Mission name (TESS, Kepler)")
    sector = Column(Integer, nullable=True,
                   comment="TESS sector number")
    status = Column(String(20), nullable=False, default="candidate",
                   comment="candidate, confirmed, false_positive, under_review")
    
    # Additional notes
    notes = Column(Text, nullable=True,
                  comment="Additional analysis notes")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_source_period', 'source_id', 'period'),
        Index('idx_status', 'status'),
        Index('idx_analysis_time', 'analysis_timestamp'),
    )
    
    def __repr__(self):
        return (f"<ExoplanetCandidate(id={self.id}, "
                f"TIC={self.source_id}, "
                f"period={self.period:.3f}d, "
                f"depth={self.depth*100:.2f}%, "
                f"status={self.status})>")
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "period_days": round(self.period, 6),
            "transit_time_btjd": round(self.transit_time, 6),
            "duration_hours": round(self.duration, 3),
            "depth_ppm": round(self.depth * 1e6, 1),  # Parts per million
            "depth_percent": round(self.depth * 100, 3),
            "power": round(self.power, 3),
            "snr": round(self.snr, 2) if self.snr else None,
            "num_transits": self.num_transits,
            "mission": self.mission,
            "sector": self.sector,
            "status": self.status,
            "analysis_timestamp": self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
            "notes": self.notes
        }
