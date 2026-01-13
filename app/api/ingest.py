"""
Ingestion API endpoints for COSMIC Data Fusion.

Provides endpoints for ingesting astronomical data:
- Single star ingestion
- Bulk ingestion

All business logic is delegated to the service layer.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.schemas import (
    StarIngestRequest,
    BulkIngestRequest,
    StarResponse,
    IngestResponse,
    BulkIngestResponse,
)
from app.services.ingestion import IngestionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post(
    "/star",
    response_model=IngestResponse,
    summary="Ingest a single star",
    description="Ingest one star observation. Coordinates are transformed to ICRS J2000."
)
def ingest_star(
    star_data: StarIngestRequest,
    db: Session = Depends(get_db)
) -> IngestResponse:
    """
    Ingest a single star observation.
    
    Accepts coordinates in ICRS, FK5, or Galactic frames.
    Automatically transforms to ICRS J2000 before storage.
    
    Args:
        star_data: Star observation with coordinates and metadata
        db: Database session (injected)
        
    Returns:
        IngestResponse with success status and created record
        
    Raises:
        HTTPException 400: Invalid coordinates or transformation error
        HTTPException 500: Database error
    """
    try:
        service = IngestionService(db)
        db_star = service.ingest_single(star_data)
        
        return IngestResponse(
            success=True,
            message=(
                f"Star '{star_data.source_id}' ingested successfully. "
                f"Transformed from {star_data.frame.value.upper()} to ICRS."
            ),
            star=StarResponse.model_validate(db_star)
        )
        
    except ValueError as e:
        logger.error(f"Coordinate transformation failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Coordinate transformation failed: {str(e)}"
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during ingestion: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.post(
    "/bulk",
    response_model=BulkIngestResponse,
    summary="Bulk ingest stars",
    description="Ingest multiple stars in a single request. Partial success allowed."
)
def ingest_bulk(
    request: BulkIngestRequest,
    db: Session = Depends(get_db)
) -> BulkIngestResponse:
    """
    Bulk ingest multiple star observations.
    
    Processes all valid stars even if some fail validation.
    Returns details on both successful and failed ingestions.
    
    Args:
        request: List of star observations
        db: Database session (injected)
        
    Returns:
        BulkIngestResponse with counts and created records
        
    Raises:
        HTTPException 500: Database error during bulk insert
    """
    try:
        service = IngestionService(db)
        db_stars, failures = service.ingest_bulk(request.stars)
        
        # Build response
        star_responses = [
            StarResponse.model_validate(star) for star in db_stars
        ]
        
        # Construct message with failure details if any
        if failures:
            failure_summary = "; ".join(
                f"index {idx}: {msg}" for idx, msg in failures[:5]
            )
            if len(failures) > 5:
                failure_summary += f" (and {len(failures) - 5} more)"
            message = (
                f"Ingested {len(db_stars)} stars. "
                f"{len(failures)} failed: {failure_summary}"
            )
        else:
            message = f"Successfully ingested all {len(db_stars)} stars."
        
        return BulkIngestResponse(
            success=len(db_stars) > 0,
            message=message,
            ingested_count=len(db_stars),
            failed_count=len(failures),
            stars=star_responses
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk ingestion: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.post(
    "/gaia",
    summary="Ingest Gaia DR3 data",
    description="Ingest Gaia DR3 catalog data. Accepts CSV or FITS files."
)
async def ingest_gaia(
    file: UploadFile = File(...),
    dataset_id: str = None,
    skip_invalid: bool = False,
    db: Session = Depends(get_db)
):
    """
    Ingest Gaia DR3 catalog data.
    
    This endpoint will use the Gaia adapter to parse, validate,
    and transform Gaia data to the unified schema.
    
    Args:
        file: Uploaded Gaia data file (CSV or FITS)
        dataset_id: Optional dataset identifier
        skip_invalid: Whether to skip invalid records
        db: Database session (injected)
        
    Returns:
        Ingestion summary with counts and validation results
        
    Raises:
        HTTPException 400: Invalid file format or data
        HTTPException 500: Database or processing error
    """
    # TODO: Implement Gaia adapter logic
    # This is a skeleton endpoint to be implemented in the gaia-adapter branch
    
    logger.info(f"Received Gaia ingestion request: file={file.filename}")
    
    return {
        "success": False,
        "message": "Gaia adapter not yet implemented. This endpoint is a placeholder.",
        "file_received": file.filename,
        "note": "Implementation will be done in the gaia-adapter branch"
    }
