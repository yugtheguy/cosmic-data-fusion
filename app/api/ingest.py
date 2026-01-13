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
    AutoIngestResponse,
    CoordinateFrame,
)
from app.services.ingestion import IngestionService
from app.services.adapter_registry import registry, AdapterDetectionError

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
    
    This endpoint uses the Gaia adapter to parse, validate,
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
    from app.services.adapters.gaia_adapter import GaiaAdapter
    from app.models import UnifiedStarCatalog
    from io import BytesIO
    
    logger.info(f"Received Gaia ingestion request: file={file.filename}")
    
    try:
        # Read uploaded file content
        content = await file.read()
        file_obj = BytesIO(content)
        
        # Initialize Gaia adapter
        adapter = GaiaAdapter(dataset_id=dataset_id)
        
        # Process the data
        valid_records, validation_results = adapter.process_batch(
            file_obj,
            skip_invalid=skip_invalid
        )
        
        if not valid_records:
            return {
                "success": False,
                "message": "No valid records found in uploaded file",
                "ingested_count": 0,
                "failed_count": len(validation_results),
                "dataset_id": adapter.dataset_id
            }
        
        # Insert records into database
        db_records = []
        for record in valid_records:
            db_record = UnifiedStarCatalog(**record)
            db_records.append(db_record)
        
        # Bulk insert
        db.bulk_save_objects(db_records)
        db.commit()
        
        logger.info(f"Successfully ingested {len(db_records)} Gaia records")
        
        # Collect validation warnings
        warnings = []
        for result in validation_results:
            if result.warnings:
                warnings.extend(result.warnings[:2])  # Limit to avoid huge response
        
        warning_summary = ""
        if warnings:
            warning_summary = f" Warnings: {warnings[0]}"
            if len(warnings) > 1:
                warning_summary += f" (+{len(warnings)-1} more)"
        
        return {
            "success": True,
            "message": f"Successfully ingested {len(db_records)} records from {file.filename}.{warning_summary}",
            "ingested_count": len(db_records),
            "failed_count": len(validation_results) - len(valid_records),
            "dataset_id": adapter.dataset_id,
            "file_name": file.filename
        }
        
    except ValueError as e:
        logger.error(f"Data validation/parsing error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data: {str(e)}"
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during Gaia ingestion: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during Gaia ingestion: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post(
    "/sdss",
    summary="Ingest SDSS DR17 data",
    description="Ingest SDSS (Sloan Digital Sky Survey) DR17 catalog data. Accepts CSV or FITS files."
)
async def ingest_sdss(
    file: UploadFile = File(...),
    dataset_id: str = None,
    skip_invalid: bool = False,
    db: Session = Depends(get_db)
):
    """
    Ingest SDSS DR17 catalog data.
    
    This endpoint uses the SDSS adapter to parse, validate,
    and transform SDSS data to the unified schema.
    
    Args:
        file: Uploaded SDSS data file (CSV or FITS)
        dataset_id: Optional dataset identifier
        skip_invalid: Whether to skip invalid records
        db: Database session (injected)
        
    Returns:
        Ingestion summary with counts and validation results
        
    Raises:
        HTTPException 400: Invalid file format or data
        HTTPException 500: Database or processing error
    """
    from app.services.adapters.sdss_adapter import SDSSAdapter
    from app.models import UnifiedStarCatalog
    from io import BytesIO
    
    logger.info(f"Received SDSS ingestion request: file={file.filename}")
    
    try:
        # Read uploaded file content
        content = await file.read()
        file_obj = BytesIO(content)
        
        # Initialize SDSS adapter
        adapter = SDSSAdapter(dataset_id=dataset_id)
        
        # Process the data
        valid_records, validation_results = adapter.process_batch(
            file_obj,
            skip_invalid=skip_invalid
        )
        
        if not valid_records:
            return {
                "success": False,
                "message": "No valid records found in uploaded file",
                "ingested_count": 0,
                "failed_count": len(validation_results),
                "dataset_id": adapter.dataset_id
            }
        
        # Insert records into database
        db_records = []
        for record in valid_records:
            db_record = UnifiedStarCatalog(**record)
            db_records.append(db_record)
        
        # Bulk insert
        db.bulk_save_objects(db_records)
        db.commit()
        
        logger.info(f"Successfully ingested {len(db_records)} SDSS records")
        
        # Collect validation warnings
        warnings = []
        for result in validation_results:
            if result.warnings:
                warnings.extend(result.warnings[:2])  # Limit to avoid huge response
        
        warning_summary = ""
        if warnings:
            warning_summary = f" Warnings: {warnings[0]}"
            if len(warnings) > 1:
                warning_summary += f" (+{len(warnings)-1} more)"
        
        return {
            "success": True,
            "message": f"Successfully ingested {len(db_records)} SDSS records from {file.filename}.{warning_summary}",
            "ingested_count": len(db_records),
            "failed_count": len(validation_results) - len(valid_records),
            "dataset_id": adapter.dataset_id,
            "file_name": file.filename
        }
        
    except ValueError as e:
        logger.error(f"Data validation/parsing error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data: {str(e)}"
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during SDSS ingestion: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during SDSS ingestion: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post(
    "/fits",
    summary="Ingest FITS catalog file",
    description="""
Ingest astronomical data from FITS (Flexible Image Transport System) binary tables.

Supports various catalogs including:
- Hipparcos (ESA) - High precision parallax catalog
- 2MASS (NASA/IPAC) - Near-infrared sky survey
- Tycho-2 - Astrometric catalog
- Sloan FITS exports
- Pan-STARRS FITS tables
- Gaia FITS exports
- Custom catalogs with standard columns

**Auto-Detection**: The adapter automatically detects RA, Dec, magnitude, and parallax columns
from common naming conventions.

**Multi-Extension Support**: For FITS files with multiple HDUs, specify which extension to read.
    """
)
def ingest_fits_file(
    file: UploadFile = File(..., description="FITS file to upload"),
    dataset_id: str = None,
    extension: int = None,
    skip_invalid: bool = True,
    db: Session = Depends(get_db)
):
    """
    Ingest FITS catalog file.
    
    Args:
        file: FITS file upload
        dataset_id: Optional dataset identifier for tracking
        extension: Optional HDU extension index (default: first data table)
        skip_invalid: Skip invalid records (default: True)
        db: Database session (injected)
        
    Returns:
        Ingestion statistics with success/failure counts
        
    Raises:
        HTTPException 400: Invalid FITS format or data
        HTTPException 500: Database error
    """
    try:
        logger.info(f"Received FITS file: {file.filename}")
        
        # Import here to avoid circular dependencies
        from app.services.adapters.fits_adapter import FITSAdapter
        from app.models import UnifiedStarCatalog
        import tempfile
        import os
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.fits') as tmp_file:
            content = file.file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Initialize adapter
            adapter = FITSAdapter(dataset_id=dataset_id)
            
            # Process file with optional extension parameter
            kwargs = {'skip_invalid': skip_invalid}
            if extension is not None:
                kwargs['extension'] = extension
            
            valid_records, validation_results = adapter.process_batch(
                input_data=tmp_file_path,
                **kwargs
            )
            
            logger.info(
                f"FITS processing complete: {len(valid_records)} valid, "
                f"{len(validation_results) - len(valid_records)} failed"
            )
            
            if not valid_records:
                # Clean up temp file
                os.unlink(tmp_file_path)
                return {
                    "success": False,
                    "message": "No valid records found in FITS file",
                    "ingested_count": 0,
                    "failed_count": len(validation_results),
                    "dataset_id": adapter.dataset_id,
                    "file_name": file.filename
                }
            
            # Insert records into database
            db_records = []
            for record in valid_records:
                db_record = UnifiedStarCatalog(**record)
                db_records.append(db_record)
            
            # Bulk insert
            db.bulk_save_objects(db_records)
            db.commit()
            
            logger.info(f"Successfully ingested {len(db_records)} FITS records")
            
            # Collect validation warnings (limit to avoid huge response)
            warnings = []
            for result in validation_results:
                if result.warnings:
                    warnings.extend(result.warnings[:2])
            
            warning_summary = ""
            if warnings:
                warning_summary = f" Warnings: {warnings[0]}"
                if len(warnings) > 1:
                    warning_summary += f" (+{len(warnings)-1} more)"
            
            return {
                "success": True,
                "message": f"Successfully ingested {len(db_records)} records from FITS file {file.filename}.{warning_summary}",
                "ingested_count": len(db_records),
                "failed_count": len(validation_results) - len(valid_records),
                "dataset_id": adapter.dataset_id,
                "file_name": file.filename,
                "catalog_info": getattr(adapter, 'header_metadata', {})
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
        
    except ValueError as e:
        logger.error(f"FITS validation/parsing error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid FITS data: {str(e)}"
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during FITS ingestion: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during FITS ingestion: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post(
    "/csv",
    summary="Ingest CSV catalog file",
    description="""
Ingest astronomical data from generic CSV files with flexible column mapping.

Supports:
- Auto-detection of common astronomical column names (RA, Dec, magnitude, parallax)
- Custom column mapping for non-standard formats
- Multiple delimiters (comma, tab, semicolon, pipe)
- Header auto-detection
- Data validation and type conversion

**Auto-Detection Mode**: If columns use standard names (ra, dec, magnitude, parallax, etc.),
the adapter will automatically detect them.

**Custom Mapping Mode**: For non-standard column names, provide a column_mapping JSON:
```json
{
  "ra": "RIGHT_ASCENSION",
  "dec": "DECLINATION",
  "magnitude": "MAG_V",
  "parallax": "PLX"
}
```
    """
)
def ingest_csv_file(
    file: UploadFile = File(..., description="CSV file to upload"),
    dataset_id: str = None,
    column_mapping: str = None,
    skip_invalid: bool = True,
    db: Session = Depends(get_db)
):
    """
    Ingest generic CSV catalog file.
    
    Args:
        file: CSV file upload
        dataset_id: Optional dataset identifier for tracking
        column_mapping: Optional JSON string mapping standard names to custom column names
        skip_invalid: Skip invalid records (default: True)
        db: Database session (injected)
        
    Returns:
        Ingestion statistics with success/failure counts
        
    Raises:
        HTTPException 400: Invalid CSV format or data
        HTTPException 500: Database error
    """
    try:
        logger.info(f"Received CSV file: {file.filename}")
        
        # Import here to avoid circular dependencies
        from app.services.adapters.csv_adapter import CSVAdapter
        from app.models import UnifiedStarCatalog
        import json
        from io import StringIO
        
        # Parse column mapping if provided
        mapping_dict = None
        if column_mapping:
            try:
                mapping_dict = json.loads(column_mapping)
                logger.info(f"Using custom column mapping: {mapping_dict}")
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid column_mapping JSON: {str(e)}"
                )
        
        # Read file content
        content = file.file.read().decode('utf-8')
        csv_io = StringIO(content)
        
        # Initialize adapter
        adapter = CSVAdapter(
            dataset_id=dataset_id,
            column_mapping=mapping_dict
        )
        
        # Process file
        valid_records, validation_results = adapter.process_batch(
            input_data=csv_io,
            skip_invalid=skip_invalid
        )
        
        logger.info(
            f"CSV processing complete: {len(valid_records)} valid, "
            f"{len(validation_results) - len(valid_records)} failed"
        )
        
        if not valid_records:
            return {
                "success": False,
                "message": "No valid records found in CSV file",
                "ingested_count": 0,
                "failed_count": len(validation_results),
                "dataset_id": adapter.dataset_id,
                "file_name": file.filename
            }
        
        # Insert records into database
        db_records = []
        for record in valid_records:
            db_record = UnifiedStarCatalog(**record)
            db_records.append(db_record)
        
        # Bulk insert
        db.bulk_save_objects(db_records)
        db.commit()
        
        logger.info(f"Successfully ingested {len(db_records)} CSV records")
        
        # Collect validation warnings (limit to avoid huge response)
        warnings = []
        for result in validation_results:
            if result.warnings:
                warnings.extend(result.warnings[:2])
        
        warning_summary = ""
        if warnings:
            warning_summary = f" Warnings: {warnings[0]}"
            if len(warnings) > 1:
                warning_summary += f" (+{len(warnings)-1} more)"
        
        return {
            "success": True,
            "message": f"Successfully ingested {len(db_records)} records from CSV file {file.filename}.{warning_summary}",
            "ingested_count": len(db_records),
            "failed_count": len(validation_results) - len(valid_records),
            "dataset_id": adapter.dataset_id,
            "file_name": file.filename
        }
        
    except ValueError as e:
        logger.error(f"CSV validation/parsing error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid CSV data: {str(e)}"
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during CSV ingestion: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during CSV ingestion: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post(
    "/auto",
    response_model=AutoIngestResponse,
    summary="Auto-detect and ingest file",
    description=(
        "Automatically detect the file type and use the appropriate adapter for ingestion. "
        "Supports FITS, CSV, Gaia DR3, and SDSS DR17 formats. "
        "Detection uses magic bytes, file extensions, and content analysis."
    )
)
async def ingest_auto(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> AutoIngestResponse:
    """
    Auto-detect file type and ingest using the appropriate adapter.
    
    The system will:
    1. Analyze the uploaded file using multiple detection strategies
    2. Select the best matching adapter based on confidence score
    3. Parse and ingest the data using the detected adapter
    4. Return ingestion results with detection information
    
    Detection Methods (in priority order):
    - Magic bytes (binary file headers) - highest confidence (0.99)
    - File extension matching - high confidence (0.90-0.95)
    - Content analysis (column names) - medium confidence (0.75-0.80)
    
    Args:
        file: Uploaded file (any supported format)
        db: Database session
        
    Returns:
        AutoIngestResponse with adapter information and ingestion results
        
    Raises:
        HTTPException 400: If file type cannot be detected or parsing fails
        HTTPException 500: If database error occurs
    """
    import tempfile
    import os
    
    temp_path = None
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(file.filename or '')[1]
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        logger.info(f"Processing auto-ingestion for file: {file.filename}")
        
        # Auto-detect adapter
        try:
            adapter_name, confidence, method = registry.detect_adapter(
                temp_path,
                confidence_threshold=0.60
            )
            logger.info(
                f"Detected adapter: {adapter_name} "
                f"(confidence: {confidence:.2f}, method: {method})"
            )
        except AdapterDetectionError as e:
            logger.warning(f"Adapter detection failed: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Could not detect file type: {e.message}"
            )
        
        # Get adapter class and instantiate
        adapter_class = registry.get_adapter(adapter_name)
        adapter = adapter_class()
        
        # Process file using adapter (parse, validate, map)
        try:
            unified_records, validation_results = adapter.process_batch(
                temp_path,
                skip_invalid=False
            )
        except Exception as e:
            logger.error(f"Processing failed with {adapter_name} adapter: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to process file with {adapter_name} adapter: {str(e)}"
            )
        
        # Ingest into database
        try:
            ingestion_service = IngestionService(db)
            records_ingested = 0
            
            # Convert unified records (dicts) to StarIngestRequest objects
            for record in unified_records:
                star_request = StarIngestRequest(
                    source_id=record.get('source_id', ''),
                    coord1=record.get('ra_deg', 0.0),
                    coord2=record.get('dec_deg', 0.0),
                    brightness_mag=record.get('brightness_mag'),
                    original_source=record.get('original_source', adapter_name),
                    frame=CoordinateFrame.ICRS  # Adapters already return ICRS
                )
                ingestion_service.ingest_single(star_request)
                records_ingested += 1
            
            db.commit()
            logger.info(
                f"Successfully ingested {records_ingested} records "
                f"using {adapter_name} adapter"
            )
            
            return AutoIngestResponse(
                message=f"Successfully ingested {records_ingested} records",
                adapter_used=adapter_name,
                adapter_confidence=confidence,
                detection_method=method,
                records_ingested=records_ingested
            )
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Database ingestion failed: {str(e)}"
            )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error during auto-ingestion: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_path}: {e}")
