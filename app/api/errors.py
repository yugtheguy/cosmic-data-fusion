"""
Error Reporting API endpoints for COSMIC Data Fusion.

Provides endpoints to retrieve and export ingestion errors for debugging
and user feedback.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.error_reporter import ErrorReporter
from app.models import IngestionError
from pydantic import BaseModel, Field, ConfigDict


router = APIRouter(prefix="/errors", tags=["errors"])


class ErrorResponse(BaseModel):
    """Response model for error records."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Error ID")
    dataset_id: Optional[str] = Field(None, description="Associated dataset ID")
    error_type: str = Field(..., description="Error category")
    severity: str = Field(..., description="Error severity")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Structured error details")
    source_row: Optional[int] = Field(None, description="Source row number")
    timestamp: str = Field(..., description="ISO timestamp when error occurred")


class ErrorSummary(BaseModel):
    """Summary statistics for errors."""
    
    total_errors: int = Field(..., description="Total number of errors")
    error_count: int = Field(..., description="Count of ERROR severity")
    warning_count: int = Field(..., description="Count of WARNING severity")
    info_count: int = Field(..., description="Count of INFO severity")
    by_type: dict = Field(..., description="Error counts by type")


@router.get("/dataset/{dataset_id}", response_model=List[ErrorResponse])
async def get_dataset_errors(
    dataset_id: str,
    error_type: Optional[str] = Query(None, description="Filter by error type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum errors to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all errors for a specific dataset.
    
    This endpoint returns a list of all errors encountered during ingestion
    for the specified dataset. Errors can be filtered by type and severity.
    
    **Error Types:**
    - VALIDATION: File validation failures
    - PARSING: Data parsing errors
    - MAPPING: Schema mapping failures
    - COORDINATE: Coordinate transformation errors
    - DATABASE: Database insertion errors
    - NETWORK: Remote fetch failures
    
    **Severity Levels:**
    - ERROR: Critical error preventing ingestion
    - WARNING: Non-critical issue
    - INFO: Informational message
    
    **Example:**
    ```
    GET /errors/dataset/abc-123?error_type=VALIDATION&severity=ERROR
    ```
    """
    reporter = ErrorReporter(db)
    errors = reporter.get_errors_by_dataset(
        dataset_id=dataset_id,
        error_type=error_type,
        severity=severity,
        limit=limit
    )
    
    if not errors:
        raise HTTPException(
            status_code=404,
            detail=f"No errors found for dataset {dataset_id}"
        )
    
    # Convert to response model
    return [
        ErrorResponse(
            id=error.id,
            dataset_id=error.dataset_id,
            error_type=error.error_type,
            severity=error.severity,
            message=error.message,
            details=error.details,
            source_row=error.source_row,
            timestamp=error.timestamp.isoformat()
        )
        for error in errors
    ]


@router.get("/dataset/{dataset_id}/summary", response_model=ErrorSummary)
async def get_error_summary(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for errors in a dataset.
    
    Returns counts of errors by severity and type for quick overview.
    
    **Example:**
    ```json
    {
      "total_errors": 42,
      "error_count": 35,
      "warning_count": 5,
      "info_count": 2,
      "by_type": {
        "VALIDATION": 10,
        "PARSING": 20,
        "MAPPING": 12
      }
    }
    ```
    """
    reporter = ErrorReporter(db)
    
    # Get counts by severity
    total = reporter.get_error_count(dataset_id)
    errors = reporter.get_error_count(dataset_id, severity="ERROR")
    warnings = reporter.get_error_count(dataset_id, severity="WARNING")
    info = reporter.get_error_count(dataset_id, severity="INFO")
    
    if total == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No errors found for dataset {dataset_id}"
        )
    
    # Get counts by type
    by_type = {}
    for error_type in ["VALIDATION", "PARSING", "MAPPING", "COORDINATE", "DATABASE", "NETWORK"]:
        count = reporter.get_error_count(dataset_id, error_type=error_type)
        if count > 0:
            by_type[error_type] = count
    
    return ErrorSummary(
        total_errors=total,
        error_count=errors,
        warning_count=warnings,
        info_count=info,
        by_type=by_type
    )


@router.get("/dataset/{dataset_id}/export")
async def export_errors_csv(
    dataset_id: str,
    error_type: Optional[str] = Query(None, description="Filter by error type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db: Session = Depends(get_db)
):
    """
    Export errors to CSV format.
    
    Downloads all errors for a dataset as a CSV file for offline analysis.
    
    **Example:**
    ```
    GET /errors/dataset/abc-123/export?error_type=VALIDATION
    ```
    
    Returns a CSV file with columns:
    - error_id
    - timestamp
    - error_type
    - severity
    - message
    - source_row
    - details
    """
    reporter = ErrorReporter(db)
    
    # Check if errors exist
    count = reporter.get_error_count(
        dataset_id=dataset_id,
        error_type=error_type,
        severity=severity
    )
    
    if count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No errors found for dataset {dataset_id}"
        )
    
    # Generate CSV
    csv_content = reporter.export_errors_to_csv(
        dataset_id=dataset_id,
        error_type=error_type,
        severity=severity
    )
    
    # Return as downloadable file
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=errors_{dataset_id}.csv"
        }
    )


@router.delete("/dataset/{dataset_id}")
async def clear_dataset_errors(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete all errors for a specific dataset.
    
    Use with caution - this permanently removes error records.
    
    **Example:**
    ```
    DELETE /errors/dataset/abc-123
    ```
    """
    reporter = ErrorReporter(db)
    deleted_count = reporter.clear_errors_by_dataset(dataset_id)
    
    if deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No errors found for dataset {dataset_id}"
        )
    
    return {
        "message": f"Deleted {deleted_count} errors for dataset {dataset_id}",
        "deleted_count": deleted_count
    }
