"""
Integration tests for Error Reporting API endpoints.

Tests the full error reporting workflow through the FastAPI endpoints.
"""

import pytest
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.api.errors import router
from app.services.error_reporter import ErrorReporter


# Test database setup - use file-based for proper sharing
TEST_DATABASE_URL = "sqlite:///./test_errors.db"

# Global engine and session maker
engine = None
TestingSessionLocal = None


# Create a minimal FastAPI app for testing
test_app = FastAPI()
test_app.include_router(router)


@pytest.fixture(scope="module")
def setup_database():
    """Set up test database once for all tests."""
    global engine, TestingSessionLocal
    
    # Import models to ensure they're registered
    from app.models import IngestionError, DatasetMetadata, UnifiedStarCatalog
    
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield
    
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    
    # Clean up test database file
    if os.path.exists("./test_errors.db"):
        os.remove("./test_errors.db")


@pytest.fixture
def test_db(setup_database):
    """Create a test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        # Clean up all data after each test
        from app.models import IngestionError
        db.query(IngestionError).delete()
        db.commit()
        db.close()


@pytest.fixture
def client(setup_database):
    """Create a test client with database override."""
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    test_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(test_app) as test_client:
        yield test_client
    
    test_app.dependency_overrides.clear()


@pytest.fixture
def sample_errors(test_db):
    """Create sample errors for testing."""
    reporter = ErrorReporter(test_db)
    
    # Log validation errors
    reporter.log_validation_error(
        message="File size too large",
        dataset_id="dataset-123",
        details={"file_size": 600000000},
        severity="ERROR"
    )
    
    # Log parsing errors
    reporter.log_parsing_error(
        message="Invalid CSV row",
        dataset_id="dataset-123",
        source_row=42,
        details={"column": "ra_deg"},
        severity="ERROR"
    )
    
    # Log warnings
    reporter.log_validation_error(
        message="Missing optional column",
        dataset_id="dataset-123",
        severity="WARNING"
    )
    
    test_db.commit()


class TestErrorAPIEndpoints:
    """Test suite for error reporting API endpoints."""
    
    def test_get_dataset_errors(self, client, sample_errors):
        """Test GET /errors/dataset/{dataset_id}"""
        response = client.get("/errors/dataset/dataset-123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        assert any(e["error_type"] == "VALIDATION" for e in data)
        assert any(e["error_type"] == "PARSING" for e in data)
        assert any(e["message"] == "File size too large" for e in data)
    
    def test_get_dataset_errors_not_found(self, client):
        """Test GET /errors/dataset/{dataset_id} with non-existent dataset"""
        response = client.get("/errors/dataset/nonexistent")
        
        assert response.status_code == 404
        assert "No errors found" in response.json()["detail"]
    
    def test_filter_errors_by_type(self, client, sample_errors):
        """Test filtering errors by type"""
        response = client.get("/errors/dataset/dataset-123?error_type=VALIDATION")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2  # 2 validation errors
        assert all(e["error_type"] == "VALIDATION" for e in data)
    
    def test_filter_errors_by_severity(self, client, sample_errors):
        """Test filtering errors by severity"""
        response = client.get("/errors/dataset/dataset-123?severity=ERROR")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2  # 2 error severity
        assert all(e["severity"] == "ERROR" for e in data)
    
    def test_filter_errors_by_type_and_severity(self, client, sample_errors):
        """Test filtering errors by both type and severity"""
        response = client.get(
            "/errors/dataset/dataset-123?error_type=VALIDATION&severity=ERROR"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["error_type"] == "VALIDATION"
        assert data[0]["severity"] == "ERROR"
    
    def test_get_error_summary(self, client, sample_errors):
        """Test GET /errors/dataset/{dataset_id}/summary"""
        response = client.get("/errors/dataset/dataset-123/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_errors"] == 3
        assert data["error_count"] == 2
        assert data["warning_count"] == 1
        assert data["info_count"] == 0
        assert data["by_type"]["VALIDATION"] == 2
        assert data["by_type"]["PARSING"] == 1
    
    def test_get_error_summary_not_found(self, client):
        """Test GET /errors/dataset/{dataset_id}/summary with no errors"""
        response = client.get("/errors/dataset/nonexistent/summary")
        
        assert response.status_code == 404
        assert "No errors found" in response.json()["detail"]
    
    def test_export_errors_csv(self, client, sample_errors):
        """Test GET /errors/dataset/{dataset_id}/export"""
        response = client.get("/errors/dataset/dataset-123/export")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "errors_dataset-123.csv" in response.headers["content-disposition"]
        
        csv_content = response.text
        assert "error_id" in csv_content
        assert "timestamp" in csv_content
        assert "error_type" in csv_content
        assert "File size too large" in csv_content
        assert "Invalid CSV row" in csv_content
    
    def test_export_errors_csv_filtered(self, client, sample_errors):
        """Test exporting filtered errors to CSV"""
        response = client.get(
            "/errors/dataset/dataset-123/export?error_type=VALIDATION"
        )
        
        assert response.status_code == 200
        csv_content = response.text
        
        assert "File size too large" in csv_content
        assert "Invalid CSV row" not in csv_content  # Should be filtered out
    
    def test_export_errors_csv_not_found(self, client):
        """Test exporting CSV with no errors"""
        response = client.get("/errors/dataset/nonexistent/export")
        
        assert response.status_code == 404
        assert "No errors found" in response.json()["detail"]
    
    def test_clear_dataset_errors(self, client, sample_errors):
        """Test DELETE /errors/dataset/{dataset_id}"""
        # Verify errors exist
        response = client.get("/errors/dataset/dataset-123")
        assert response.status_code == 200
        assert len(response.json()) == 3
        
        # Delete errors
        response = client.delete("/errors/dataset/dataset-123")
        assert response.status_code == 200
        data = response.json()
        
        assert data["deleted_count"] == 3
        assert "Deleted 3 errors" in data["message"]
        
        # Verify errors are gone
        response = client.get("/errors/dataset/dataset-123")
        assert response.status_code == 404
    
    def test_clear_dataset_errors_not_found(self, client):
        """Test deleting errors for non-existent dataset"""
        response = client.delete("/errors/dataset/nonexistent")
        
        assert response.status_code == 404
        assert "No errors found" in response.json()["detail"]
    
    def test_error_response_structure(self, client, sample_errors):
        """Test that error responses have correct structure"""
        response = client.get("/errors/dataset/dataset-123")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check first error structure
        error = data[0]
        assert "id" in error
        assert "dataset_id" in error
        assert "error_type" in error
        assert "severity" in error
        assert "message" in error
        assert "details" in error
        assert "source_row" in error
        assert "timestamp" in error
        
        # Verify timestamp is ISO format
        assert "T" in error["timestamp"]
        assert isinstance(error["id"], int)
    
    def test_error_limit_parameter(self, client, test_db):
        """Test that limit parameter works"""
        # Create many errors
        reporter = ErrorReporter(test_db)
        for i in range(20):
            reporter.log_validation_error(
                message=f"Error {i}",
                dataset_id="dataset-limit-test"
            )
        test_db.commit()
        
        # Request with limit
        response = client.get("/errors/dataset/dataset-limit-test?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
    
    def test_error_ordering_newest_first(self, client, test_db):
        """Test that errors are returned newest first"""
        reporter = ErrorReporter(test_db)
        
        # Log errors in sequence
        reporter.log_validation_error(
            message="First error",
            dataset_id="dataset-ordering"
        )
        reporter.log_validation_error(
            message="Second error",
            dataset_id="dataset-ordering"
        )
        reporter.log_validation_error(
            message="Third error",
            dataset_id="dataset-ordering"
        )
        test_db.commit()
        
        response = client.get("/errors/dataset/dataset-ordering")
        
        assert response.status_code == 200
        data = response.json()
        
        # Newest should be first
        assert "Third error" in data[0]["message"]
        assert "Second error" in data[1]["message"]
        assert "First error" in data[2]["message"]
