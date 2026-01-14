"""
Unit tests for Error Reporting Service.

Tests error logging, retrieval, export, and filtering functionality.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import IngestionError
from app.services.error_reporter import ErrorReporter


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def error_reporter(db_session):
    """Create an ErrorReporter instance."""
    return ErrorReporter(db_session)


class TestErrorReporter:
    """Test suite for ErrorReporter service."""
    
    def test_log_validation_error(self, error_reporter):
        """Test logging a validation error."""
        error = error_reporter.log_validation_error(
            message="File size exceeds maximum limit",
            dataset_id="test-dataset-1",
            details={"file_size": 600000000, "max_size": 500000000},
            severity="ERROR"
        )
        
        assert error.id is not None
        assert error.dataset_id == "test-dataset-1"
        assert error.error_type == "VALIDATION"
        assert error.severity == "ERROR"
        assert "exceeds maximum limit" in error.message
        assert error.details["file_size"] == 600000000
    
    def test_log_parsing_error(self, error_reporter):
        """Test logging a parsing error."""
        error = error_reporter.log_parsing_error(
            message="Invalid CSV format on row 42",
            dataset_id="test-dataset-2",
            source_row=42,
            details={"column": "ra_deg", "value": "invalid"}
        )
        
        assert error.error_type == "PARSING"
        assert error.source_row == 42
        assert error.dataset_id == "test-dataset-2"
    
    def test_log_mapping_error(self, error_reporter):
        """Test logging a mapping error."""
        error = error_reporter.log_mapping_error(
            message="Required column 'ra_deg' not found",
            dataset_id="test-dataset-3",
            details={"available_columns": ["RA", "DEC", "MAG"]}
        )
        
        assert error.error_type == "MAPPING"
        assert "not found" in error.message
    
    def test_log_coordinate_error(self, error_reporter):
        """Test logging a coordinate transformation error."""
        error = error_reporter.log_coordinate_error(
            message="Invalid RA value: 400 degrees",
            dataset_id="test-dataset-4",
            source_row=100,
            details={"ra": 400, "valid_range": [0, 360]}
        )
        
        assert error.error_type == "COORDINATE"
        assert error.source_row == 100
    
    def test_log_database_error(self, error_reporter):
        """Test logging a database error."""
        error = error_reporter.log_database_error(
            message="Duplicate key violation",
            dataset_id="test-dataset-5",
            source_row=50,
            details={"object_id": "GAIA-123"}
        )
        
        assert error.error_type == "DATABASE"
        assert "Duplicate" in error.message
    
    def test_log_network_error(self, error_reporter):
        """Test logging a network error."""
        error = error_reporter.log_network_error(
            message="API request timeout",
            dataset_id="test-dataset-6",
            details={"url": "https://api.example.com", "timeout": 30}
        )
        
        assert error.error_type == "NETWORK"
        assert "timeout" in error.message
    
    def test_get_errors_by_dataset(self, error_reporter):
        """Test retrieving errors by dataset."""
        # Log multiple errors
        error_reporter.log_validation_error(
            message="Error 1",
            dataset_id="test-dataset-7"
        )
        error_reporter.log_parsing_error(
            message="Error 2",
            dataset_id="test-dataset-7"
        )
        error_reporter.log_mapping_error(
            message="Error 3",
            dataset_id="test-dataset-7"
        )
        
        # Retrieve all errors
        errors = error_reporter.get_errors_by_dataset("test-dataset-7")
        
        assert len(errors) == 3
        assert any(e.error_type == "VALIDATION" for e in errors)
        assert any(e.error_type == "PARSING" for e in errors)
        assert any(e.error_type == "MAPPING" for e in errors)
    
    def test_filter_errors_by_type(self, error_reporter):
        """Test filtering errors by type."""
        # Log different error types
        error_reporter.log_validation_error(
            message="Validation error",
            dataset_id="test-dataset-8"
        )
        error_reporter.log_parsing_error(
            message="Parsing error",
            dataset_id="test-dataset-8"
        )
        error_reporter.log_parsing_error(
            message="Another parsing error",
            dataset_id="test-dataset-8"
        )
        
        # Filter by PARSING
        parsing_errors = error_reporter.get_errors_by_dataset(
            "test-dataset-8",
            error_type="PARSING"
        )
        
        assert len(parsing_errors) == 2
        assert all(e.error_type == "PARSING" for e in parsing_errors)
    
    def test_filter_errors_by_severity(self, error_reporter):
        """Test filtering errors by severity."""
        # Log different severities
        error_reporter.log_validation_error(
            message="Critical error",
            dataset_id="test-dataset-9",
            severity="ERROR"
        )
        error_reporter.log_validation_error(
            message="Warning",
            dataset_id="test-dataset-9",
            severity="WARNING"
        )
        error_reporter.log_validation_error(
            message="Info",
            dataset_id="test-dataset-9",
            severity="INFO"
        )
        
        # Filter by ERROR severity
        errors = error_reporter.get_errors_by_dataset(
            "test-dataset-9",
            severity="ERROR"
        )
        
        assert len(errors) == 1
        assert errors[0].severity == "ERROR"
    
    def test_get_error_count(self, error_reporter):
        """Test getting error count."""
        # Log errors
        for i in range(5):
            error_reporter.log_validation_error(
                message=f"Error {i}",
                dataset_id="test-dataset-10"
            )
        
        count = error_reporter.get_error_count("test-dataset-10")
        assert count == 5
    
    def test_get_error_count_by_type(self, error_reporter):
        """Test getting error count by type."""
        # Log mixed errors
        error_reporter.log_validation_error(
            message="Val 1",
            dataset_id="test-dataset-11"
        )
        error_reporter.log_validation_error(
            message="Val 2",
            dataset_id="test-dataset-11"
        )
        error_reporter.log_parsing_error(
            message="Parse 1",
            dataset_id="test-dataset-11"
        )
        
        validation_count = error_reporter.get_error_count(
            "test-dataset-11",
            error_type="VALIDATION"
        )
        parsing_count = error_reporter.get_error_count(
            "test-dataset-11",
            error_type="PARSING"
        )
        
        assert validation_count == 2
        assert parsing_count == 1
    
    def test_export_errors_to_csv(self, error_reporter):
        """Test exporting errors to CSV."""
        # Log errors
        error_reporter.log_validation_error(
            message="CSV Export Error 1",
            dataset_id="test-dataset-12",
            details={"test": "data"}
        )
        error_reporter.log_parsing_error(
            message="CSV Export Error 2",
            dataset_id="test-dataset-12",
            source_row=42
        )
        
        # Export to CSV
        csv_content = error_reporter.export_errors_to_csv("test-dataset-12")
        
        assert "error_id" in csv_content
        assert "timestamp" in csv_content
        assert "error_type" in csv_content
        assert "CSV Export Error 1" in csv_content
        assert "CSV Export Error 2" in csv_content
        assert "42" in csv_content  # source_row
    
    def test_clear_errors_by_dataset(self, error_reporter):
        """Test clearing all errors for a dataset."""
        # Log errors
        for i in range(3):
            error_reporter.log_validation_error(
                message=f"Error {i}",
                dataset_id="test-dataset-13"
            )
        
        # Verify errors exist
        assert error_reporter.get_error_count("test-dataset-13") == 3
        
        # Clear errors
        deleted_count = error_reporter.clear_errors_by_dataset("test-dataset-13")
        
        assert deleted_count == 3
        assert error_reporter.get_error_count("test-dataset-13") == 0
    
    def test_error_ordering(self, error_reporter):
        """Test that errors are ordered by timestamp (newest first)."""
        # Log errors with slight delays
        error_reporter.log_validation_error(
            message="Error 1",
            dataset_id="test-dataset-14"
        )
        error_reporter.log_validation_error(
            message="Error 2",
            dataset_id="test-dataset-14"
        )
        error_reporter.log_validation_error(
            message="Error 3",
            dataset_id="test-dataset-14"
        )
        
        errors = error_reporter.get_errors_by_dataset("test-dataset-14")
        
        # Should be in reverse chronological order
        assert "Error 3" in errors[0].message
        assert "Error 2" in errors[1].message
        assert "Error 1" in errors[2].message
    
    def test_error_limit(self, error_reporter):
        """Test that error retrieval respects limit."""
        # Log many errors
        for i in range(20):
            error_reporter.log_validation_error(
                message=f"Error {i}",
                dataset_id="test-dataset-15"
            )
        
        # Retrieve with limit
        errors = error_reporter.get_errors_by_dataset("test-dataset-15", limit=10)
        
        assert len(errors) == 10
    
    def test_error_with_null_dataset_id(self, error_reporter):
        """Test logging error without dataset_id (pre-ingestion errors)."""
        error = error_reporter.log_validation_error(
            message="File validation failed before dataset creation",
            dataset_id=None,
            details={"filename": "test.csv"}
        )
        
        assert error.dataset_id is None
        assert error.error_type == "VALIDATION"
    
    def test_error_details_json_storage(self, error_reporter):
        """Test that error details are properly stored as JSON."""
        complex_details = {
            "file_path": "/path/to/file.csv",
            "line_number": 42,
            "column_name": "ra_deg",
            "expected_type": "float",
            "actual_value": "invalid",
            "validation_rules": ["required", "numeric", "range"]
        }
        
        error = error_reporter.log_validation_error(
            message="Complex error",
            dataset_id="test-dataset-16",
            details=complex_details
        )
        
        assert error.details["file_path"] == "/path/to/file.csv"
        assert error.details["line_number"] == 42
        assert error.details["validation_rules"] == ["required", "numeric", "range"]
    
    def test_multiple_datasets_isolation(self, error_reporter):
        """Test that errors from different datasets are isolated."""
        # Log errors for different datasets
        error_reporter.log_validation_error(
            message="Dataset A error",
            dataset_id="test-dataset-a"
        )
        error_reporter.log_validation_error(
            message="Dataset B error",
            dataset_id="test-dataset-b"
        )
        
        # Retrieve errors for each dataset
        errors_a = error_reporter.get_errors_by_dataset("test-dataset-a")
        errors_b = error_reporter.get_errors_by_dataset("test-dataset-b")
        
        assert len(errors_a) == 1
        assert len(errors_b) == 1
        assert "Dataset A" in errors_a[0].message
        assert "Dataset B" in errors_b[0].message
