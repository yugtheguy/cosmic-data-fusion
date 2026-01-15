"""
SQLAlchemy ORM models for COSMIC Data Fusion.

All coordinates are stored in ICRS (International Celestial Reference System)
frame at J2000 epoch - the modern standard for astronomical catalogs.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, Integer, String, Float, DateTime, Index, JSON, Text, Boolean

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


class DatasetMetadata(Base):
    """
    Registry of ingested astronomical datasets with their metadata.
    
    This model tracks all datasets loaded into the system, storing information
    about their source, schema, record counts, and configuration. Each dataset
    represents a logical grouping of astronomical observations (e.g., a specific
    FITS file, a CSV upload, or a bulk Gaia query).
    
    Key Features:
        - Unique dataset_id (UUID) for referencing in UnifiedStarCatalog
        - Source tracking (catalog name, version, ingestion method)
        - Schema information (column mappings, detected fields)
        - Record counting for data integrity validation
        - Configuration storage (adapter settings, filters applied)
        - License and attribution tracking
    
    Use Cases:
        - Frontend dataset browser (list all ingested datasets)
        - Data provenance (which records came from which file/query)
        - Re-ingestion detection (avoid duplicate imports)
        - Export attribution (maintain proper data citations)
        - Schema mapping UI (show detected vs mapped fields)
    
    Attributes:
        id: Auto-incrementing primary key
        dataset_id: Unique UUID identifier for this dataset
        source_name: Human-readable source name (e.g., "Gaia DR3 Query", "NGC2244_SDSS.fits")
        catalog_type: Type of catalog (gaia, sdss, fits, csv, etc.)
        ingestion_time: UTC timestamp when dataset was first ingested
        adapter_used: Which adapter processed this data (e.g., "GaiaAdapter")
        schema_version: Version of the adapter schema used
        record_count: Number of records ingested from this dataset
        original_filename: Original filename if uploaded (null for API queries)
        file_size_bytes: Size of original file in bytes (null for API queries)
        column_mappings: JSON storing detected→unified field mappings
        raw_config: JSON storing adapter configuration and parameters
        license_info: License/attribution string (e.g., "ESA/Gaia DPAC", "SDSS DR17")
        notes: Optional user notes about this dataset
        created_at: UTC timestamp when record was created
        updated_at: UTC timestamp when record was last modified
    """
    
    __tablename__ = "dataset_metadata"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Unique dataset identifier (UUID)
    dataset_id = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid4()))
    
    # Source identification
    source_name = Column(String(500), nullable=False)
    catalog_type = Column(String(50), nullable=False, index=True)  # gaia, sdss, fits, csv
    
    # Ingestion metadata
    ingestion_time = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    adapter_used = Column(String(100), nullable=False)
    schema_version = Column(String(20), nullable=True)
    
    # Data statistics
    record_count = Column(Integer, nullable=False, default=0)
    
    # File information (if applicable)
    original_filename = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA256 hash of original file
    storage_key = Column(String(500), nullable=True)  # MinIO object key for file retrieval
    
    # Schema and configuration
    column_mappings = Column(JSON, nullable=True)  # {"original_ra": "ra_deg", "original_dec": "dec_deg", ...}
    raw_config = Column(JSON, nullable=True)       # Adapter-specific configuration
    
    # Attribution
    license_info = Column(String(500), nullable=True)
    notes = Column(String(2000), nullable=True)
    
    # Audit timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self) -> str:
        return (
            f"<DatasetMetadata(id={self.id}, dataset_id='{self.dataset_id}', "
            f"source_name='{self.source_name}', catalog_type='{self.catalog_type}', "
            f"records={self.record_count})>"
        )


class IngestionError(Base):
    """
    Tracks all errors encountered during file validation and data ingestion.
    
    This model provides comprehensive error logging for the ingestion pipeline,
    enabling debugging, user feedback, and data quality monitoring. Errors are
    associated with dataset_id to allow tracking which errors occurred for which
    datasets.
    
    Error Categories:
        - VALIDATION: File validation failures (size, MIME, encoding)
        - PARSING: Data parsing errors (malformed CSV, invalid FITS)
        - MAPPING: Schema mapping failures (missing columns, wrong types)
        - COORDINATE: Coordinate transformation errors (invalid coordinates)
        - DATABASE: Database insertion errors (duplicates, constraints)
        - NETWORK: Remote fetch failures (API timeouts, auth errors)
    
    Use Cases:
        - Display errors to users during upload/ingestion
        - Export error reports as CSV for debugging
        - Monitor data quality across datasets
        - Track error trends over time
        - Filter out problematic records during batch processing
    
    Attributes:
        id: Auto-incrementing primary key
        dataset_id: Foreign key to DatasetMetadata (null if dataset not created yet)
        error_type: Category of error (VALIDATION, PARSING, MAPPING, etc.)
        severity: Error severity (ERROR, WARNING, INFO)
        message: Human-readable error message
        details: JSON field for structured error details (file path, line number, etc.)
        source_row: Row number in source file where error occurred (if applicable)
        timestamp: UTC timestamp when error was logged
    """
    
    __tablename__ = "ingestion_errors"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to dataset
    dataset_id = Column(String(36), nullable=True, index=True)
    
    # Error classification
    error_type = Column(
        String(50),
        nullable=False,
        index=True
    )  # VALIDATION, PARSING, MAPPING, COORDINATE, DATABASE, NETWORK
    
    severity = Column(
        String(20),
        nullable=False,
        default="ERROR"
    )  # ERROR, WARNING, INFO
    
    # Error details
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)  # Structured error context
    
    # Source reference
    source_row = Column(Integer, nullable=True)  # Row number in source file
    
    # Audit timestamp
    timestamp = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    
    def __repr__(self) -> str:
        return (
            f"<IngestionError(id={self.id}, dataset_id='{self.dataset_id}', "
            f"type='{self.error_type}', severity='{self.severity}', "
            f"message='{self.message[:50]}...')>"
        )


class DiscoveryRun(Base):
    """
    Store AI discovery computation results and metadata.
    
    Tracks individual discovery runs (anomaly detection or clustering)
    with parameters, filters, and summary statistics. Enables:
    - Comparison of results over time
    - Tracking different parameter configurations
    - Reusing expensive computations
    - Historical trend analysis
    
    Attributes:
        id: Auto-incrementing primary key
        run_id: Unique UUID identifier for this discovery run
        run_type: Type of discovery ('anomaly' or 'cluster')
        parameters: JSON with algorithm parameters (contamination, eps, etc.)
        dataset_filter: JSON with query filters used to select stars
        total_stars: Number of stars analyzed in this run
        results_summary: JSON with statistics (n_anomalies, n_clusters, etc.)
        created_at: Timestamp when run was created
    """
    __tablename__ = "discovery_runs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid4()))
    run_type = Column(String(20), nullable=False, index=True)  # 'anomaly' or 'cluster'
    parameters = Column(JSON, nullable=False)  # Algorithm parameters
    dataset_filter = Column(JSON, nullable=True)  # Query filters used
    total_stars = Column(Integer, nullable=False)
    results_summary = Column(JSON, nullable=False)  # Stats summary
    is_complete = Column(Boolean, default=False, nullable=False)  # True when all results are saved
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    def __repr__(self) -> str:
        return (
            f"<DiscoveryRun(run_id='{self.run_id}', type='{self.run_type}', "
            f"stars={self.total_stars})>"
        )


class DiscoveryResult(Base):
    """
    Individual star discovery results linked to a discovery run.
    
    Stores per-star results from AI discovery algorithms:
    - Anomaly scores and classifications
    - Cluster assignments
    - Links back to parent DiscoveryRun
    
    Attributes:
        id: Auto-incrementing primary key
        run_id: Foreign key to DiscoveryRun.run_id
        star_id: Foreign key to UnifiedStarCatalog.id
        is_anomaly: Boolean flag if star is classified as anomaly
        anomaly_score: Anomaly score from IsolationForest (-1 to +1)
        cluster_id: Cluster assignment from DBSCAN (-1 for noise)
        created_at: Timestamp when result was stored
    """
    __tablename__ = "discovery_results"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(String(36), nullable=False, index=True)  # FK to discovery_runs.run_id
    star_id = Column(Integer, nullable=False, index=True)  # FK to unified_star_catalog.id
    is_anomaly = Column(Integer, default=0, nullable=False, index=True)  # 0/1 for boolean
    anomaly_score = Column(Float, nullable=True)  # -1 to +1 range
    cluster_id = Column(Integer, nullable=True, index=True)  # -1 for noise, 0+ for clusters
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self) -> str:
        return (
            f"<DiscoveryResult(run_id='{self.run_id}', star={self.star_id}, "
            f"anomaly={bool(self.is_anomaly)})>"
        )
