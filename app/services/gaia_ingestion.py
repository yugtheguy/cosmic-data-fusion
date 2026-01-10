"""
Gaia DR3 specific ingestion service for COSMIC Data Fusion.

Handles loading and processing of Gaia DR3 catalog data.

IMPORTANT LICENSING NOTE:
Gaia data provided by ESA under the Gaia Archive terms.
See: https://gea.esac.esa.int/archive/
This excerpt is for demonstration purposes only.

ASTRONOMY NOTES:
- Gaia DR3 coordinates are already in ICRS frame
- Reference epoch is J2016.0 (not J2000.0, but the difference for
  positions without proper motion is negligible for this demo)
- For precise astrometry, proper motion correction would be needed
- phot_g_mean_mag is the Gaia G-band magnitude (broad optical band)
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

# Path to bundled Gaia sample data
GAIA_DATA_PATH = Path(__file__).parent.parent / "data" / "gaia_dr3_sample.csv"

# Gaia-specific column configuration
GAIA_REQUIRED_COLUMNS = [
    "source_id",
    "ra",
    "dec",
    "phot_g_mean_mag",
]

# Map Gaia column names to our internal names
GAIA_COLUMN_MAPPING = {
    "source_id": "source_id",
    "ra": "ra",
    "dec": "dec",
    "phot_g_mean_mag": "brightness_mag",
    "ref_epoch": "ref_epoch",
}

# Type converters for Gaia columns
GAIA_TYPE_CONVERTERS = {
    "source_id": safe_string,
    "ra": safe_float,
    "dec": safe_float,
    "phot_g_mean_mag": safe_float,
    "ref_epoch": safe_float,
}


class GaiaIngestionService:
    """
    Service for ingesting Gaia DR3 catalog data.
    
    Handles:
    - Reading the bundled Gaia CSV sample
    - Mapping Gaia columns to our schema
    - Bulk insertion via existing ingestion pipeline
    - Duplicate detection (by source_id)
    
    Astronomy Notes:
        - Gaia coordinates are ICRS (no transformation needed)
        - We still pass through standardizer for consistency
        - G-band magnitude is used as brightness measure
    """
    
    def __init__(self, db: Session):
        """
        Initialize Gaia ingestion service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.ingestion_service = IngestionService(db)
        
        # Configure CSV parser for Gaia format
        self.csv_service = CSVIngestionService(
            required_columns=GAIA_REQUIRED_COLUMNS,
            column_mapping=GAIA_COLUMN_MAPPING,
            type_converters=GAIA_TYPE_CONVERTERS,
        )
    
    def _get_existing_source_ids(self, source_name: str) -> set:
        """
        Get set of source_ids already in database for given source.
        
        Used for duplicate detection to avoid re-ingesting stars.
        
        Args:
            source_name: Original source name (e.g., "Gaia DR3")
            
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
            row: Parsed row from CSV with Gaia data
            
        Returns:
            StarIngestRequest ready for ingestion pipeline
            
        Notes:
            - Gaia coordinates are already ICRS, so frame="icrs"
            - coord1 = RA, coord2 = Dec (both in degrees)
            - G-band magnitude used as brightness
        """
        return StarIngestRequest(
            source_id=str(row["source_id"]),
            coord1=row["ra"],       # RA in degrees (ICRS)
            coord2=row["dec"],      # Dec in degrees (ICRS)
            brightness_mag=row["brightness_mag"],  # G-band magnitude
            original_source="Gaia DR3",
            frame=CoordinateFrame.ICRS,  # Gaia is already ICRS
        )
    
    def load_bundled_gaia_data(
        self,
        skip_duplicates: bool = True,
        max_rows: int | None = None
    ) -> Tuple[int, int, int]:
        """
        Load the bundled Gaia DR3 sample into the database.
        
        This method:
        1. Reads the CSV file from app/data/
        2. Filters out duplicates if requested
        3. Bulk inserts via the standard pipeline
        
        Args:
            skip_duplicates: If True, skip stars already in DB
            max_rows: Maximum rows to load (None = all)
            
        Returns:
            Tuple of (ingested_count, skipped_duplicates, error_count)
            
        Raises:
            CSVIngestionError: If CSV file cannot be read
        """
        logger.info("="*60)
        logger.info("Starting Gaia DR3 data ingestion")
        logger.info(f"Data source: {GAIA_DATA_PATH}")
        logger.info("="*60)
        
        # Check if data file exists
        if not GAIA_DATA_PATH.exists():
            raise CSVIngestionError(
                f"Gaia data file not found: {GAIA_DATA_PATH}"
            )
        
        # Parse CSV file
        rows, parse_errors = self.csv_service.read_csv(
            GAIA_DATA_PATH,
            skip_errors=True,
            max_rows=max_rows
        )
        
        logger.info(f"Parsed {len(rows)} rows from CSV ({len(parse_errors)} parse errors)")
        
        # Get existing source IDs for duplicate detection
        if skip_duplicates:
            existing_ids = self._get_existing_source_ids("Gaia DR3")
            logger.info(f"Found {len(existing_ids)} existing Gaia DR3 records")
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
        logger.info("Gaia DR3 ingestion complete")
        logger.info(f"  Ingested: {ingested_count}")
        logger.info(f"  Skipped (duplicates): {skipped_count}")
        logger.info(f"  Errors: {error_count}")
        logger.info("="*60)
        
        return ingested_count, skipped_count, error_count
    
    def get_gaia_stats(self) -> dict:
        """
        Get statistics about Gaia data in the database.
        
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
            UnifiedStarCatalog.original_source == "Gaia DR3"
        ).first()
        
        return {
            "source": "Gaia DR3",
            "count": stats.count if stats else 0,
            "min_magnitude": float(stats.min_mag) if stats and stats.min_mag else None,
            "max_magnitude": float(stats.max_mag) if stats and stats.max_mag else None,
            "avg_magnitude": float(stats.avg_mag) if stats and stats.avg_mag else None,
        }
