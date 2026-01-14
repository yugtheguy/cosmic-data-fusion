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
    DatasetRegisterRequest,
    DatasetMetadataResponse,
    DatasetListResponse,
    DatasetRegistryStats,
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


# ============================================================
# DATASET REGISTRY ENDPOINTS
# ============================================================

@router.post(
    "/register",
    response_model=DatasetMetadataResponse,
    status_code=201,
    summary="Register a new dataset",
    description="""
Register a new dataset in the system.

This endpoint creates a metadata entry for a dataset that will be ingested.
Returns the generated dataset_id which should be used when ingesting records.

**Use Cases**:
- Pre-register a dataset before ingestion starts
- Track file uploads and their metadata
- Enable dataset attribution and provenance
    """
)
def register_dataset(
    dataset: DatasetRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new dataset in the metadata registry."""
    from app.repository.dataset_repository import DatasetRepository
    
    try:
        repo = DatasetRepository(db)
        
        # Check for duplicate filename
        if dataset.original_filename:
            existing = repo.get_by_filename(dataset.original_filename)
            if existing:
                logger.warning(f"Dataset with filename '{dataset.original_filename}' already exists")
                raise HTTPException(
                    status_code=409,
                    detail=f"Dataset with filename '{dataset.original_filename}' already registered"
                )
        
        # Create dataset metadata
        dataset_data = dataset.model_dump()
        db_dataset = repo.create(dataset_data)
        
        logger.info(f"Registered new dataset: {db_dataset.dataset_id}")
        return db_dataset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering dataset: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register dataset: {str(e)}"
        )


@router.get(
    "",
    response_model=DatasetListResponse,
    summary="List all datasets",
    description="""
List all registered datasets with pagination.

**Query Parameters**:
- `catalog_type`: Filter by catalog type (gaia, sdss, fits, csv)
- `limit`: Number of results per page (default: 100, max: 1000)
- `offset`: Pagination offset (default: 0)

Returns datasets sorted by ingestion time (newest first).
    """
)
def list_datasets(
    catalog_type: str = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all datasets with optional filtering and pagination."""
    from app.repository.dataset_repository import DatasetRepository
    
    try:
        # Validate pagination params
        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be non-negative")
        
        repo = DatasetRepository(db)
        
        datasets = repo.list_all(catalog_type=catalog_type, limit=limit, offset=offset)
        total = repo.count_all(catalog_type=catalog_type)
        
        return DatasetListResponse(
            datasets=datasets,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing datasets: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list datasets: {str(e)}"
        )


@router.get(
    "/statistics",
    response_model=DatasetRegistryStats,
    summary="Get dataset statistics",
    description="""
Get comprehensive statistics about all registered datasets.

Returns:
- Total number of datasets
- Total records across all datasets  
- Breakdown by catalog type (gaia, sdss, fits, csv)

Useful for dashboard overview and system health monitoring.
    """
)
def get_dataset_statistics(db: Session = Depends(get_db)):
    """Get statistics about all datasets."""
    from app.repository.dataset_repository import DatasetRepository
    
    try:
        repo = DatasetRepository(db)
        stats = repo.get_statistics()
        
        return DatasetRegistryStats(**stats)
        
    except Exception as e:
        logger.error(f"Error getting dataset statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get(
    "/{dataset_id}",
    response_model=DatasetMetadataResponse,
    summary="Get dataset by ID",
    description="""
Retrieve metadata for a specific dataset by its UUID.

Returns complete metadata including:
- Source information
- Record counts
- Column mappings
- Configuration
- Timestamps

Returns 404 if dataset not found.
    """
)
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific dataset by its UUID."""
    from app.repository.dataset_repository import DatasetRepository
    
    try:
        repo = DatasetRepository(db)
        dataset = repo.get_by_id(dataset_id)
        
        if not dataset:
            raise HTTPException(
                status_code=404,
                detail=f"Dataset '{dataset_id}' not found"
            )
        
        return dataset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve dataset: {str(e)}"
        )


@router.delete(
    "/{dataset_id}",
    status_code=204,
    summary="Delete dataset",
    description="""
Delete a dataset metadata record.

**WARNING**: This only deletes the metadata entry, NOT the associated
star records. Star records will remain in the database with their
dataset_id field set to the deleted ID.

Consider implementing soft delete or cascade deletion based on your needs.

Returns 404 if dataset not found.
    """
)
def delete_dataset(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """Delete a dataset metadata record."""
    from app.repository.dataset_repository import DatasetRepository
    
    try:
        repo = DatasetRepository(db)
        deleted = repo.delete(dataset_id)
        
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Dataset '{dataset_id}' not found"
            )
        
        logger.info(f"Deleted dataset: {dataset_id}")
        # 204 No Content - don't return anything
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete dataset: {str(e)}"
        )
