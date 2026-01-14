"""
Error Reporting Service for COSMIC Data Fusion.

This module provides centralized error logging and reporting functionality
for the ingestion pipeline. All validation, parsing, mapping, and database
errors are tracked in a structured way for debugging and user feedback.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from io import StringIO
import csv

from sqlalchemy.orm import Session

from app.models import IngestionError


logger = logging.getLogger(__name__)


class ErrorReporter:
    """
    Centralized error reporting service for the ingestion pipeline.
    
    This class provides methods to log errors to the database with structured
    metadata, retrieve errors by dataset, and export error reports as CSV.
    
    Error Types:
        - VALIDATION: File validation failures (size, MIME, encoding)
        - PARSING: Data parsing errors (malformed CSV, invalid FITS)
        - MAPPING: Schema mapping failures (missing columns, wrong types)
        - COORDINATE: Coordinate transformation errors (invalid coordinates)
        - DATABASE: Database insertion errors (duplicates, constraints)
        - NETWORK: Remote fetch failures (API timeouts, auth errors)
    
    Severity Levels:
        - ERROR: Critical error preventing ingestion
        - WARNING: Non-critical issue that may affect data quality
        - INFO: Informational message for tracking purposes
    
    Example Usage:
        >>> reporter = ErrorReporter(db)
        >>> reporter.log_validation_error(
        ...     dataset_id="abc-123",
        ...     message="File size exceeds maximum limit",
        ...     details={"file_size": 600000000, "max_size": 500000000}
        ... )
        >>> errors = reporter.get_errors_by_dataset("abc-123")
        >>> csv_content = reporter.export_errors_to_csv("abc-123")
    """
    
    def __init__(self, db: Session):
        """
        Initialize the ErrorReporter with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def log_error(
        self,
        error_type: str,
        message: str,
        dataset_id: Optional[str] = None,
        severity: str = "ERROR",
        details: Optional[Dict[str, Any]] = None,
        source_row: Optional[int] = None
    ) -> IngestionError:
        """
        Log an error to the database.
        
        Args:
            error_type: Error category (VALIDATION, PARSING, MAPPING, etc.)
            message: Human-readable error message
            dataset_id: Optional dataset ID to associate with this error
            severity: Error severity (ERROR, WARNING, INFO)
            details: Optional structured error context (dict)
            source_row: Optional row number in source file where error occurred
            
        Returns:
            IngestionError: The created error record
        """
        error = IngestionError(
            dataset_id=dataset_id,
            error_type=error_type,
            severity=severity,
            message=message,
            details=details,
            source_row=source_row,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.db.add(error)
        self.db.commit()
        self.db.refresh(error)
        
        logger.info(
            f"Logged {severity} error: {error_type} - {message} "
            f"(dataset_id={dataset_id}, error_id={error.id})"
        )
        
        return error
    
    def log_validation_error(
        self,
        message: str,
        dataset_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "ERROR"
    ) -> IngestionError:
        """
        Log a file validation error.
        
        Args:
            message: Error message
            dataset_id: Optional dataset ID
            details: Optional error context
            severity: Error severity
            
        Returns:
            IngestionError: The created error record
        """
        return self.log_error(
            error_type="VALIDATION",
            message=message,
            dataset_id=dataset_id,
            severity=severity,
            details=details
        )
    
    def log_parsing_error(
        self,
        message: str,
        dataset_id: str,
        details: Optional[Dict[str, Any]] = None,
        source_row: Optional[int] = None,
        severity: str = "ERROR"
    ) -> IngestionError:
        """
        Log a data parsing error.
        
        Args:
            message: Error message
            dataset_id: Dataset ID
            details: Optional error context
            source_row: Row number where error occurred
            severity: Error severity
            
        Returns:
            IngestionError: The created error record
        """
        return self.log_error(
            error_type="PARSING",
            message=message,
            dataset_id=dataset_id,
            severity=severity,
            details=details,
            source_row=source_row
        )
    
    def log_mapping_error(
        self,
        message: str,
        dataset_id: str,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "ERROR"
    ) -> IngestionError:
        """
        Log a schema mapping error.
        
        Args:
            message: Error message
            dataset_id: Dataset ID
            details: Optional error context
            severity: Error severity
            
        Returns:
            IngestionError: The created error record
        """
        return self.log_error(
            error_type="MAPPING",
            message=message,
            dataset_id=dataset_id,
            severity=severity,
            details=details
        )
    
    def log_coordinate_error(
        self,
        message: str,
        dataset_id: str,
        details: Optional[Dict[str, Any]] = None,
        source_row: Optional[int] = None,
        severity: str = "ERROR"
    ) -> IngestionError:
        """
        Log a coordinate transformation error.
        
        Args:
            message: Error message
            dataset_id: Dataset ID
            details: Optional error context
            source_row: Row number where error occurred
            severity: Error severity
            
        Returns:
            IngestionError: The created error record
        """
        return self.log_error(
            error_type="COORDINATE",
            message=message,
            dataset_id=dataset_id,
            severity=severity,
            details=details,
            source_row=source_row
        )
    
    def log_database_error(
        self,
        message: str,
        dataset_id: str,
        details: Optional[Dict[str, Any]] = None,
        source_row: Optional[int] = None,
        severity: str = "ERROR"
    ) -> IngestionError:
        """
        Log a database insertion error.
        
        Args:
            message: Error message
            dataset_id: Dataset ID
            details: Optional error context
            source_row: Row number where error occurred
            severity: Error severity
            
        Returns:
            IngestionError: The created error record
        """
        return self.log_error(
            error_type="DATABASE",
            message=message,
            dataset_id=dataset_id,
            severity=severity,
            details=details,
            source_row=source_row
        )
    
    def log_network_error(
        self,
        message: str,
        dataset_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "ERROR"
    ) -> IngestionError:
        """
        Log a network/API error.
        
        Args:
            message: Error message
            dataset_id: Optional dataset ID
            details: Optional error context
            severity: Error severity
            
        Returns:
            IngestionError: The created error record
        """
        return self.log_error(
            error_type="NETWORK",
            message=message,
            dataset_id=dataset_id,
            severity=severity,
            details=details
        )
    
    def get_errors_by_dataset(
        self,
        dataset_id: str,
        error_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 1000
    ) -> List[IngestionError]:
        """
        Retrieve all errors for a specific dataset.
        
        Args:
            dataset_id: Dataset ID to filter by
            error_type: Optional error type filter (VALIDATION, PARSING, etc.)
            severity: Optional severity filter (ERROR, WARNING, INFO)
            limit: Maximum number of errors to return (default 1000)
            
        Returns:
            List of IngestionError records
        """
        query = self.db.query(IngestionError).filter(
            IngestionError.dataset_id == dataset_id
        )
        
        if error_type:
            query = query.filter(IngestionError.error_type == error_type)
        
        if severity:
            query = query.filter(IngestionError.severity == severity)
        
        errors = query.order_by(IngestionError.timestamp.desc()).limit(limit).all()
        
        logger.info(
            f"Retrieved {len(errors)} errors for dataset {dataset_id} "
            f"(type={error_type}, severity={severity})"
        )
        
        return errors
    
    def get_error_count(
        self,
        dataset_id: str,
        error_type: Optional[str] = None,
        severity: Optional[str] = None
    ) -> int:
        """
        Get count of errors for a dataset.
        
        Args:
            dataset_id: Dataset ID to filter by
            error_type: Optional error type filter
            severity: Optional severity filter
            
        Returns:
            Count of matching errors
        """
        query = self.db.query(IngestionError).filter(
            IngestionError.dataset_id == dataset_id
        )
        
        if error_type:
            query = query.filter(IngestionError.error_type == error_type)
        
        if severity:
            query = query.filter(IngestionError.severity == severity)
        
        return query.count()
    
    def export_errors_to_csv(
        self,
        dataset_id: str,
        error_type: Optional[str] = None,
        severity: Optional[str] = None
    ) -> str:
        """
        Export errors to CSV format.
        
        Args:
            dataset_id: Dataset ID to filter by
            error_type: Optional error type filter
            severity: Optional severity filter
            
        Returns:
            CSV content as string
        """
        errors = self.get_errors_by_dataset(
            dataset_id=dataset_id,
            error_type=error_type,
            severity=severity,
            limit=10000  # Higher limit for export
        )
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "error_id",
            "timestamp",
            "error_type",
            "severity",
            "message",
            "source_row",
            "details"
        ])
        
        # Write data
        for error in errors:
            writer.writerow([
                error.id,
                error.timestamp.isoformat(),
                error.error_type,
                error.severity,
                error.message,
                error.source_row if error.source_row else "",
                str(error.details) if error.details else ""
            ])
        
        logger.info(f"Exported {len(errors)} errors to CSV for dataset {dataset_id}")
        
        return output.getvalue()
    
    def clear_errors_by_dataset(self, dataset_id: str) -> int:
        """
        Delete all errors for a specific dataset.
        
        Args:
            dataset_id: Dataset ID to delete errors for
            
        Returns:
            Number of errors deleted
        """
        count = self.db.query(IngestionError).filter(
            IngestionError.dataset_id == dataset_id
        ).delete()
        
        self.db.commit()
        
        logger.info(f"Deleted {count} errors for dataset {dataset_id}")
        
        return count
