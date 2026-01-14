"""
Base adapter interface for data source ingestion.

Defines the common contract that all adapters must implement and adds a
minimal persistence helper used by the full-stack integration tests.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


@dataclass
class AdapterIngestMetadata:
    """Lightweight ingestion metadata returned to callers."""
    id: int
    dataset_id: str
    record_count: int
    source_type: str
    format_type: str
    filename: str
    file_hash: Optional[str] = None
    status: str = "completed"  # Default status


class ValidationResult:
    """
    Result of data validation.
    
    Attributes:
        is_valid: Whether the data passed validation
        errors: List of error messages
        warnings: List of warning messages
    """
    
    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def add_error(self, message: str):
        """Add an error message and mark as invalid."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
    
    def __repr__(self) -> str:
        return f"<ValidationResult valid={self.is_valid} errors={len(self.errors)} warnings={len(self.warnings)}>"


class BaseAdapter(ABC):
    """
    Abstract base class for all data source adapters.
    
    All adapters (Gaia, SDSS, FITS, CSV) must inherit from this class
    and implement the required methods.
    
    Workflow:
        1. parse() - Parse input data into raw records
        2. validate() - Validate each record
        3. map_to_unified_schema() - Transform to unified schema
        4. Optional: transform_coordinates() if not in ICRS J2000
    """
    
    def __init__(
        self,
        source_name: str,
        dataset_id: Optional[str] = None,
        db=None,
        error_reporter=None,
    ):
        """
        Initialize adapter.
        
        Args:
            source_name: Name of the data source (e.g., "Gaia DR3", "SDSS DR17")
            dataset_id: Optional dataset identifier for tracking
        """
        self.source_name = source_name
        self.dataset_id = dataset_id or self._generate_dataset_id()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.db = db
        self.error_reporter = error_reporter
    
    def _generate_dataset_id(self) -> str:
        """Generate a unique dataset ID."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        return f"{self.source_name.lower().replace(' ', '_')}_{timestamp}"
    
    @abstractmethod
    def parse(self, input_data: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        Parse input data into raw records.
        
        Args:
            input_data: Input data (file path, DataFrame, dict, etc.)
            **kwargs: Additional parsing options
            
        Returns:
            List of raw records as dictionaries
            
        Raises:
            ValueError: If input data is invalid or cannot be parsed
        """
        pass
    
    @abstractmethod
    def validate(self, record: Dict[str, Any]) -> ValidationResult:
        """
        Validate a single record.
        
        Args:
            record: Raw record dictionary
            
        Returns:
            ValidationResult with errors and warnings
        """
        pass
    
    @abstractmethod
    def map_to_unified_schema(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a raw record to the unified schema.
        
        Args:
            record: Raw record dictionary
            
        Returns:
            Dictionary with unified schema fields:
                - object_id (str)
                - source_id (str)
                - ra_deg (float)
                - dec_deg (float)
                - brightness_mag (float)
                - parallax_mas (float, optional)
                - distance_pc (float, optional)
                - original_source (str)
                - raw_frame (str)
                - observation_time (datetime, optional)
                - dataset_id (str)
                - raw_metadata (dict, optional)
        """
        pass
    
    def process_batch(
        self,
        input_data: Any,
        skip_invalid: bool = False,
        **kwargs
    ) -> tuple[List[Dict[str, Any]], List[ValidationResult]]:
        """
        Process a batch of records end-to-end.
        
        This is the main entry point for ingestion.
        
        Args:
            input_data: Input data to process
            skip_invalid: Whether to skip invalid records or raise error
            **kwargs: Additional options for parsing
            
        Returns:
            Tuple of (valid_records, validation_results)
            
        Raises:
            ValueError: If any record is invalid and skip_invalid=False
        """
        # Parse input
        raw_records = self.parse(input_data, **kwargs)
        self.logger.info(f"Parsed {len(raw_records)} records from {self.source_name}")
        
        valid_records = []
        validation_results = []
        
        for idx, record in enumerate(raw_records):
            # Validate
            validation = self.validate(record)
            validation_results.append(validation)
            
            if not validation.is_valid:
                if skip_invalid:
                    self.logger.warning(
                        f"Skipping invalid record {idx}: {validation.errors}"
                    )
                    continue
                else:
                    raise ValueError(
                        f"Invalid record at index {idx}: {validation.errors}"
                    )
            
            # Map to unified schema
            try:
                unified_record = self.map_to_unified_schema(record)
                valid_records.append(unified_record)
            except Exception as e:
                self.logger.error(f"Failed to map record {idx}: {e}")
                if not skip_invalid:
                    raise
        
        self.logger.info(
            f"Processed {len(valid_records)}/{len(raw_records)} valid records"
        )
        
        return valid_records, validation_results
    
    def get_column_mapping(self) -> Dict[str, str]:
        """
        Get the column mapping for this adapter.
        
        Returns:
            Dictionary mapping source columns to unified schema fields
        """
        return {}

    # ------------------------------------------------------------------
    # Persistence helper used by integration tests
    # ------------------------------------------------------------------
    def ingest_file(self, file_path: Any, db=None, error_reporter=None, skip_invalid: bool = True):
        """
        Parse, validate, map, and persist a file to the database.

        Returns the created stars and a small metadata object used by tests.
        """

        # Resolve dependencies lazily to avoid circular imports at module load time
        from app.services.file_validation import FileValidator
        from app.repository.star_catalog import StarCatalogRepository
        from app.repository.dataset_repository import DatasetRepository
        from app.services.error_reporter import ErrorReporter

        db_session = db or self.db
        reporter = error_reporter or self.error_reporter

        if db_session is None:
            raise ValueError("Database session is required for ingest_file")

        path = Path(file_path)
        validator = FileValidator()
        validation_result = validator.validate_file(path)

        if not validation_result.is_valid:
            if reporter:
                for msg in validation_result.errors:
                    reporter.log_validation_error(message=msg, dataset_id=self.dataset_id)
            raise ValueError(f"File validation failed: {validation_result.errors}")

        # Parse, validate, and map records
        try:
            valid_records, validation_results = self.process_batch(
                path,
                skip_invalid=skip_invalid,
                encoding=validation_result.encoding or "utf-8",
            )
        except ValueError as exc:
            if reporter:
                reporter.log_parsing_error(
                    message=str(exc),
                    dataset_id=self.dataset_id,
                    severity="ERROR",
                )
            raise

        # Log per-row warnings/errors when available
        if reporter:
            for idx, result in enumerate(validation_results):
                for msg in result.errors:
                    reporter.log_parsing_error(
                        message=msg,
                        dataset_id=self.dataset_id,
                        source_row=idx + 1,
                        severity="ERROR",
                    )
                for msg in result.warnings:
                    reporter.log_parsing_error(
                        message=msg,
                        dataset_id=self.dataset_id,
                        source_row=idx + 1,
                        severity="WARNING",
                    )

        # Persist stars
        star_repo = StarCatalogRepository(db_session)
        db_stars = star_repo.create_bulk(valid_records) if valid_records else []

        # Persist dataset metadata
        dataset_repo = DatasetRepository(db_session)
        dataset = dataset_repo.create(
            {
                "dataset_id": self.dataset_id,
                "source_name": self.get_source_type(),
                "catalog_type": self.get_catalog_type(),
                "adapter_used": self.__class__.__name__,
                "schema_version": getattr(self, "schema_version", None),
                "record_count": len(db_stars),
                "original_filename": path.name,
                "file_size_bytes": validation_result.file_size,
                "file_hash": validation_result.file_hash,
                "column_mappings": self.get_column_mapping(),
                "raw_config": self._get_raw_config(),
                "license_info": self.get_license_info(),
            }
        )

        metadata = AdapterIngestMetadata(
            id=dataset.id,
            dataset_id=dataset.dataset_id,
            record_count=dataset.record_count,
            source_type=self.get_source_type(),
            format_type=self.get_format_type(path),
            filename=str(path),
            file_hash=validation_result.file_hash,
        )

        return db_stars, metadata

    # These helpers keep adapter-specific details overrideable
    def get_catalog_type(self) -> str:
        return self.source_name.lower().split()[0]

    def get_source_type(self) -> str:
        return self.source_name

    def get_format_type(self, path: Path) -> str:
        suffix = path.suffix.lower().lstrip('.')
        return suffix or "unknown"

    def get_license_info(self) -> Optional[str]:
        return None

    def _get_raw_config(self) -> Optional[dict]:
        return None
