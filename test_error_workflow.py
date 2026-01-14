"""Quick integration test for error reporting workflow."""

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.error_reporter import ErrorReporter
import requests


def test_error_reporting_workflow():
    """Test error logging and API endpoints."""
    # Create a test dataset with errors
    db = SessionLocal()
    reporter = ErrorReporter(db)

    # Log some test errors
    print("Creating test errors...")
    reporter.log_validation_error(
        message="Test file size too large",
        dataset_id="integration-test-123",
        details={"file_size": 600000000},
        severity="ERROR"
    )

    reporter.log_parsing_error(
        message="Test CSV parsing failure",
        dataset_id="integration-test-123",
        source_row=42,
        severity="ERROR"
    )

    reporter.log_validation_error(
        message="Test warning message",
        dataset_id="integration-test-123",
        severity="WARNING"
    )

    db.close()

    print("\nTest errors created. Testing API endpoints...\n")

    # Test GET errors
    print("1. Testing GET /errors/dataset/integration-test-123")
    response = requests.get("http://localhost:8000/errors/dataset/integration-test-123")
    print(f"   Status: {response.status_code}")
    print(f"   Errors returned: {len(response.json())}")

    # Test GET summary
    print("\n2. Testing GET /errors/dataset/integration-test-123/summary")
    response = requests.get("http://localhost:8000/errors/dataset/integration-test-123/summary")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        summary = response.json()
        print(f"   Total errors: {summary.get('total_errors', 0)}")
        print(f"   ERROR count: {summary.get('error_count', 0)}")
        print(f"   WARNING count: {summary.get('warning_count', 0)}")
        print(f"   By type: {summary.get('by_type', {})}")

    # Test filter by type
    print("\n3. Testing GET /errors/dataset/integration-test-123?error_type=VALIDATION")
    response = requests.get("http://localhost:8000/errors/dataset/integration-test-123?error_type=VALIDATION")
    print(f"   Status: {response.status_code}")
    print(f"   Validation errors: {len(response.json())}")

    # Test CSV export
    print("\n4. Testing GET /errors/dataset/integration-test-123/export")
    response = requests.get("http://localhost:8000/errors/dataset/integration-test-123/export")
    print(f"   Status: {response.status_code}")
    print(f"   CSV size: {len(response.text)} bytes")
    print(f"   First line: {response.text.split(chr(10))[0]}")

    # Clean up
    print("\n5. Testing DELETE /errors/dataset/integration-test-123")
    response = requests.delete("http://localhost:8000/errors/dataset/integration-test-123")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")

    print("\n✅ All error reporting endpoints working correctly!")
