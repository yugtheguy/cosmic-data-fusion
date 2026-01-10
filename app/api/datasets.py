"""
Dataset ingestion API endpoints for COSMIC Data Fusion.

Provides endpoints for loading bundled astronomical datasets.

LICENSING NOTE:
Gaia data provided by ESA under the Gaia Archive terms.
See: https://gea.esac.esa.int/archive/
This excerpt is for demonstration purposes only.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.schemas import (
    GaiaLoadResponse,
    DatasetStatsResponse,
)
from app.services.gaia_ingestion import GaiaIngestionService
from app.services.csv_ingestion import CSVIngestionError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post(
    "/gaia/load",
    response_model=GaiaLoadResponse,
    summary="Load Gaia DR3 sample data",
    description="""
Load the bundled Gaia DR3 sample dataset into the database.

This endpoint reads a pre-bundled CSV excerpt from the Gaia DR3 catalog
and ingests it into the unified star catalog.

**Data Source**: Gaia DR3 (ESA)  
**License**: Data provided under Gaia Archive terms  
**Coordinates**: ICRS (no transformation needed)

**Behavior**:
- Skips stars already in the database (by source_id)
- Uses bulk insert for performance
- Returns ingestion statistics
    """
)
def load_gaia_dataset(
    skip_duplicates: bool = True,
    max_rows: int | None = None,
    db: Session = Depends(get_db)
) -> GaiaLoadResponse:
    """
    Load bundled Gaia DR3 sample data into the database.
    
    Args:
        skip_duplicates: Skip stars already in DB (default: True)
        max_rows: Maximum rows to load (None = all)
        db: Database session (injected)
        
    Returns:
        GaiaLoadResponse with ingestion statistics
        
    Raises:
        HTTPException 500: If ingestion fails
    """
    try:
        logger.info(
            f"Gaia load request: skip_duplicates={skip_duplicates}, "
            f"max_rows={max_rows}"
        )
        
        service = GaiaIngestionService(db)
        ingested, skipped, errors = service.load_bundled_gaia_data(
            skip_duplicates=skip_duplicates,
            max_rows=max_rows
        )
        
        # Determine success status
        success = ingested > 0 or (ingested == 0 and skipped > 0)
        
        if ingested > 0:
            message = f"Successfully loaded {ingested} Gaia DR3 stars"
        elif skipped > 0:
            message = f"No new stars to load ({skipped} already in database)"
        else:
            message = "No stars were loaded"
        
        return GaiaLoadResponse(
            success=success,
            message=message,
            ingested_count=ingested,
            skipped_count=skipped,
            error_count=errors,
            source="Gaia DR3",
            license_note="Data provided by ESA under the Gaia Archive terms"
        )
        
    except CSVIngestionError as e:
        logger.error(f"CSV ingestion error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read Gaia data file: {str(e)}"
        )
    
    except SQLAlchemyError as e:
        logger.error(f"Database error during Gaia ingestion: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/gaia/stats",
    response_model=DatasetStatsResponse,
    summary="Get Gaia dataset statistics",
    description="Get statistics about Gaia DR3 data currently in the database."
)
def get_gaia_stats(
    db: Session = Depends(get_db)
) -> DatasetStatsResponse:
    """
    Get statistics about Gaia data in the database.
    
    Args:
        db: Database session (injected)
        
    Returns:
        DatasetStatsResponse with count and magnitude statistics
    """
    try:
        service = GaiaIngestionService(db)
        stats = service.get_gaia_stats()
        
        return DatasetStatsResponse(
            source=stats["source"],
            record_count=stats["count"],
            min_magnitude=stats["min_magnitude"],
            max_magnitude=stats["max_magnitude"],
            avg_magnitude=stats["avg_magnitude"],
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error getting Gaia stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
