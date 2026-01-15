"""
SDSS DR17/18 specific ingestion service for COSMIC Data Fusion.

Handles loading and processing of SDSS (Sloan Digital Sky Survey) catalog data.

IMPORTANT LICENSING NOTE:
SDSS data is provided under the SDSS Data Release terms.
See: https://www.sdss.org/collaboration/citing-sdss/
This excerpt is for demonstration purposes only.

ASTRONOMY NOTES:
- SDSS coordinates are in ICRS frame
- We use the 'r' band magnitude as the primary brightness measure
  (commonly used reference band for optical photometry)
- The 'r' band is centered around 6166 Å (orange-red light)
- SDSS object classes: STAR, GALAXY, QSO (quasar)
- For this stellar catalog, we filter to STAR class only
"""

import logging
from pathlib import Path
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.schemas import StarIngestRequest, CoordinateFrame
from app.services.csv_ingestion import (
    CSVIngestionService,
    CSVIngestionError,
    safe_float,
    safe_string,
)
from app.services.ingestion import IngestionService
from app.models import UnifiedStarCatalog

logger = logging.getLogger(__name__)

# Path to bundled SDSS sample data
SDSS_DATA_PATH = Path(__file__).parent.parent / "data" / "SDSS_DR18.csv"

# SDSS-specific column configuration
SDSS_REQUIRED_COLUMNS = [
    "objid",
    "ra",
    "dec",
    "r",  # r-band magnitude
]

# Map SDSS column names to our internal names
SDSS_COLUMN_MAPPING = {
    "objid": "source_id",
    "specobjid": "spec_id",
    "ra": "ra",
    "dec": "dec",
    "u": "mag_u",
    "g": "mag_g",
    "r": "brightness_mag",  # Use r-band as primary brightness
    "i": "mag_i",
    "z": "mag_z",
    "redshift": "redshift",
    "class": "object_class",
}

# Type converters for SDSS columns
SDSS_TYPE_CONVERTERS = {
    "objid": safe_string,
    "specobjid": safe_string,
    "ra": safe_float,
    "dec": safe_float,
    "u": safe_float,
    "g": safe_float,
    "r": safe_float,
    "i": safe_float,
    "z": safe_float,
    "redshift": safe_float,
    "class": safe_string,
}


class SDSSIngestionService:
    """
    Service for ingesting SDSS DR17/18 catalog data.
    
    Handles:
    - Reading the bundled SDSS CSV sample
    - Filtering to stellar objects only (class = 'STAR')
    - Mapping SDSS columns to our schema
    - Bulk insertion via existing ingestion pipeline
    - Duplicate detection (by source_id)
    
    Astronomy Notes:
        - SDSS coordinates are ICRS (no transformation needed)
        - We use r-band magnitude as brightness measure
        - Only STAR class objects are ingested (not galaxies or QSOs)
    """
    
    def __init__(self, db: Session):
        """
        Initialize SDSS ingestion service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.ingestion_service = IngestionService(db)
        
        # Configure CSV parser for SDSS format
        self.csv_service = CSVIngestionService(
            required_columns=SDSS_REQUIRED_COLUMNS,
            column_mapping=SDSS_COLUMN_MAPPING,
            type_converters=SDSS_TYPE_CONVERTERS,
        )
    
    def _get_existing_source_ids(self, source_name: str) -> set:
        """
        Get set of source_ids already in database for given source.
        
        Used for duplicate detection to avoid re-ingesting stars.
        
        Args:
            source_name: Original source name (e.g., "SDSS DR18")
            
        Returns:
            Set of existing source_id strings
        """
        existing = self.db.query(UnifiedStarCatalog.source_id).filter(
            UnifiedStarCatalog.original_source == source_name
        ).all()
        
        return {row[0] for row in existing}
    
    def _row_to_ingest_request(self, row: dict) -> StarIngestRequest:
        """
        Convert a parsed CSV row to StarIngestRequest.
        
        Args:
            row: Parsed row from CSV with SDSS data
            
        Returns:
            StarIngestRequest ready for ingestion pipeline
            
        Notes:
            - SDSS coordinates are already ICRS, so frame="icrs"
            - coord1 = RA, coord2 = Dec (both in degrees)
            - r-band magnitude used as brightness
        """
        return StarIngestRequest(
            source_id=str(row["source_id"]),
            coord1=row["ra"],       # RA in degrees (ICRS)
            coord2=row["dec"],      # Dec in degrees (ICRS)
            brightness_mag=row["brightness_mag"],  # r-band magnitude
            original_source="SDSS DR18",
            frame=CoordinateFrame.ICRS,  # SDSS is already ICRS
        )
    
    def load_bundled_sdss_data(
        self,
        skip_duplicates: bool = True,
        max_rows: int | None = None,
        stars_only: bool = True
    ) -> Tuple[int, int, int]:
        """
        Load the bundled SDSS DR18 sample into the database.
        
        This method:
        1. Reads the CSV file from app/data/
        2. Filters to STAR class objects if requested
        3. Filters out duplicates if requested
        4. Bulk inserts via the standard pipeline
        
        Args:
            skip_duplicates: If True, skip stars already in DB
            max_rows: Maximum rows to load (None = all)
            stars_only: If True, only load objects with class='STAR'
            
        Returns:
            Tuple of (ingested_count, skipped_duplicates, error_count)
            
        Raises:
            CSVIngestionError: If CSV file cannot be read
        """
        logger.info("="*60)
        logger.info("Starting SDSS DR18 data ingestion")
        logger.info(f"Data source: {SDSS_DATA_PATH}")
        logger.info(f"Stars only: {stars_only}")
        logger.info("="*60)
        
        # Check if data file exists
        if not SDSS_DATA_PATH.exists():
            raise CSVIngestionError(
                f"SDSS data file not found: {SDSS_DATA_PATH}"
            )
        
        # Parse CSV file
        rows, parse_errors = self.csv_service.read_csv(
            SDSS_DATA_PATH,
            skip_errors=True,
            max_rows=max_rows
        )
        
        logger.info(f"Parsed {len(rows)} rows from CSV ({len(parse_errors)} parse errors)")
        
        # Filter to stars only if requested
        if stars_only:
            original_count = len(rows)
            rows = [r for r in rows if r.get("object_class", "").upper() == "STAR"]
            logger.info(f"Filtered to {len(rows)} STAR objects (from {original_count} total)")
        
        # Get existing source IDs for duplicate detection
        if skip_duplicates:
            existing_ids = self._get_existing_source_ids("SDSS DR18")
            logger.info(f"Found {len(existing_ids)} existing SDSS DR18 records")
        else:
            existing_ids = set()
        
        # Convert rows to ingest requests, filtering duplicates
        ingest_requests: List[StarIngestRequest] = []
        skipped_count = 0
        
        for row in rows:
            source_id = str(row["source_id"])
            
            if source_id in existing_ids:
                skipped_count += 1
                continue
            
            try:
                request = self._row_to_ingest_request(row)
                ingest_requests.append(request)
            except Exception as e:
                logger.warning(f"Failed to convert row {source_id}: {e}")
                parse_errors.append((0, str(e)))
        
        logger.info(
            f"Prepared {len(ingest_requests)} stars for ingestion "
            f"({skipped_count} duplicates skipped)"
        )
        
        # Bulk ingest via existing pipeline
        if ingest_requests:
            db_stars, ingest_errors = self.ingestion_service.ingest_bulk(
                ingest_requests
            )
            ingested_count = len(db_stars)
            error_count = len(parse_errors) + len(ingest_errors)
        else:
            ingested_count = 0
            error_count = len(parse_errors)
        
        logger.info("="*60)
        logger.info("SDSS DR18 ingestion complete")
        logger.info(f"  Ingested: {ingested_count}")
        logger.info(f"  Skipped (duplicates): {skipped_count}")
        logger.info(f"  Errors: {error_count}")
        logger.info("="*60)
        
        return ingested_count, skipped_count, error_count
    
    def get_sdss_stats(self) -> dict:
        """
        Get statistics about SDSS data in the database.
        
        Returns:
            Dictionary with count and magnitude range
        """
        from sqlalchemy import func
        
        stats = self.db.query(
            func.count(UnifiedStarCatalog.id).label("count"),
            func.min(UnifiedStarCatalog.brightness_mag).label("min_mag"),
            func.max(UnifiedStarCatalog.brightness_mag).label("max_mag"),
            func.avg(UnifiedStarCatalog.brightness_mag).label("avg_mag"),
        ).filter(
            UnifiedStarCatalog.original_source == "SDSS DR18"
        ).first()
        
        return {
            "source": "SDSS DR18",
            "count": stats.count if stats else 0,
            "min_magnitude": float(stats.min_mag) if stats and stats.min_mag else None,
            "max_magnitude": float(stats.max_mag) if stats and stats.max_mag else None,
            "avg_magnitude": float(stats.avg_mag) if stats and stats.avg_mag else None,
        }
