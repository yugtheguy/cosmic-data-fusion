"""
Ingestion service for COSMIC Data Fusion.

Handles the pipeline for ingesting astronomical data:
1. Validate input coordinates
2. Transform to ICRS J2000
3. Persist to database

Designed to be extensible for future FITS/CSV file ingestion.
"""

import logging
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.schemas import StarIngestRequest, CoordinateFrame
from app.models import UnifiedStarCatalog
from app.repository.star_catalog import StarCatalogRepository
from app.services.standardizer import CoordinateStandardizer

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Service for ingesting star observations into the unified catalog.
    
    Responsibilities:
    - Coordinate validation and transformation
    - Data normalization
    - Database persistence via repository layer
    
    Extension Points:
    - process_fits_file(): For FITS file ingestion
    - process_csv_file(): For CSV file ingestion
    """
    
    def __init__(self, db: Session):
        """
        Initialize ingestion service.
        
        Args:
            db: SQLAlchemy session for database operations
        """
        self.repository = StarCatalogRepository(db)
        self.standardizer = CoordinateStandardizer()
    
    def _transform_and_prepare(
        self,
        star_data: StarIngestRequest
    ) -> dict:
        """
        Transform coordinates and prepare data for database insertion.
        
        Args:
            star_data: Validated star ingestion request
            
        Returns:
            Dictionary ready for UnifiedStarCatalog creation
            
        Raises:
            ValueError: If coordinate transformation fails
        """
        # Transform coordinates to ICRS J2000
        ra_deg, dec_deg = self.standardizer.transform_to_icrs(
            coord1=star_data.coord1,
            coord2=star_data.coord2,
            frame=star_data.frame
        )
        
        # Prepare data dictionary for database
        return {
            "source_id": star_data.source_id,
            "ra_deg": ra_deg,
            "dec_deg": dec_deg,
            "brightness_mag": star_data.brightness_mag,
            "original_source": star_data.original_source,
            "raw_frame": star_data.frame.value,
        }
    
    def ingest_single(self, star_data: StarIngestRequest) -> UnifiedStarCatalog:
        """
        Ingest a single star observation.
        
        Args:
            star_data: Validated star data with coordinates
            
        Returns:
            Created UnifiedStarCatalog record
            
        Raises:
            ValueError: If coordinate transformation fails
        """
        logger.info(
            f"Ingesting star: {star_data.source_id} "
            f"from {star_data.original_source} ({star_data.frame.value})"
        )
        
        # Transform and prepare data
        prepared_data = self._transform_and_prepare(star_data)
        
        # Persist via repository
        db_star = self.repository.create(prepared_data)
        
        logger.info(
            f"Successfully ingested star ID {db_star.id}: "
            f"RA={db_star.ra_deg:.6f}°, Dec={db_star.dec_deg:.6f}°"
        )
        
        return db_star
    
    def ingest_bulk(
        self,
        stars_data: List[StarIngestRequest]
    ) -> Tuple[List[UnifiedStarCatalog], List[Tuple[int, str]]]:
        """
        Ingest multiple star observations in a single transaction.
        
        Processes all valid stars and collects errors for invalid ones.
        This allows partial success - valid stars are ingested even if
        some fail validation.
        
        Args:
            stars_data: List of star data to ingest
            
        Returns:
            Tuple of:
            - List of successfully created records
            - List of (index, error_message) for failures
        """
        logger.info(f"Starting bulk ingestion of {len(stars_data)} stars")
        
        prepared_data_list: List[dict] = []
        failures: List[Tuple[int, str]] = []
        
        # Transform all coordinates (fail-fast on transform errors)
        for idx, star_data in enumerate(stars_data):
            try:
                prepared_data = self._transform_and_prepare(star_data)
                prepared_data_list.append(prepared_data)
            except ValueError as e:
                logger.warning(f"Failed to transform star at index {idx}: {e}")
                failures.append((idx, str(e)))
        
        # Bulk insert valid records
        if prepared_data_list:
            db_stars = self.repository.create_bulk(prepared_data_list)
        else:
            db_stars = []
        
        logger.info(
            f"Bulk ingestion complete: {len(db_stars)} succeeded, "
            f"{len(failures)} failed"
        )
        
        return db_stars, failures
