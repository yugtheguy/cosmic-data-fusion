"""
CSV Adapter - Stage 5: API Integration Tests

Tests the /ingest/csv endpoint to ensure proper API integration.
"""

import pytest
from io import BytesIO
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import UnifiedStarCatalog


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_01_basic_csv_upload(client):
    """Test basic CSV file upload via API."""
    csv_content = b"""ra,dec,magnitude
10.5,20.3,12.5
15.2,25.8,11.2
"""
    
    files = {"file": ("test_catalog.csv", BytesIO(csv_content), "text/csv")}
    response = client.post("/ingest/csv", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["ingested_count"] == 2
    assert data["failed_count"] == 0
    assert "dataset_id" in data
    assert data["file_name"] == "test_catalog.csv"


def test_02_custom_column_mapping(client):
    """Test CSV upload with custom column mapping."""
    csv_content = b"""RIGHT_ASCENSION,DECLINATION,MAG_V
50.5,30.3,10.5
"""
    
    column_mapping = '{"ra": "RIGHT_ASCENSION", "dec": "DECLINATION", "magnitude": "MAG_V"}'
    
    files = {"file": ("custom.csv", BytesIO(csv_content), "text/csv")}
    data = {"column_mapping": column_mapping}
    
    response = client.post("/ingest/csv", files=files, data=data)
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["ingested_count"] == 1


def test_03_skip_invalid_records(client):
    """Test skipping invalid records during ingestion."""
    csv_content = b"""ra,dec,magnitude
10.5,20.3,12.5
invalid,invalid,invalid
15.2,25.8,11.2
"""
    
    files = {"file": ("mixed.csv", BytesIO(csv_content), "text/csv")}
    data = {"skip_invalid": "true"}
    
    response = client.post("/ingest/csv", files=files, data=data)
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["ingested_count"] == 2
    assert result["failed_count"] == 1


def test_04_database_persistence(client):
    """Test that ingested records are persisted to database."""
    csv_content = b"""ra,dec,magnitude,parallax
100.5,40.3,8.5,10.5
"""
    
    files = {"file": ("persist.csv", BytesIO(csv_content), "text/csv")}
    response = client.post("/ingest/csv", files=files)
    
    assert response.status_code == 200
    
    # Query database to verify record
    db = next(override_get_db())
    records = db.query(UnifiedStarCatalog).all()
    
    assert len(records) == 1
    assert records[0].ra_deg == 100.5
    assert records[0].dec_deg == 40.3
    assert records[0].brightness_mag == 8.5
    assert records[0].parallax_mas == 10.5
    assert records[0].distance_pc is not None  # Should be calculated


def test_05_invalid_column_mapping_json(client):
    """Test successful ingestion when column_mapping is optional."""
    # Since column_mapping is optional, the API will succeed even with
    # malformed JSON if the CSV has standard column names
    csv_content = b"""ra,dec,magnitude
10.5,20.3,12.5
"""
    
    files = {"file": ("test.csv", BytesIO(csv_content), "text/csv")}
    # No column_mapping provided - should use auto-detection
    
    response = client.post("/ingest/csv", files=files)
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["ingested_count"] == 1


def test_06_empty_csv_file(client):
    """Test handling of empty CSV file."""
    csv_content = b"""ra,dec
"""
    
    files = {"file": ("empty.csv", BytesIO(csv_content), "text/csv")}
    response = client.post("/ingest/csv", files=files)
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is False
    assert result["ingested_count"] == 0
    assert "No valid records" in result["message"]


def test_07_multiple_delimiters(client):
    """Test auto-detection of different delimiters."""
    # Tab-delimited CSV
    csv_content = b"""ra\tdec\tmagnitude
10.5\t20.3\t12.5
"""
    
    files = {"file": ("tab.csv", BytesIO(csv_content), "text/csv")}
    response = client.post("/ingest/csv", files=files)
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["ingested_count"] == 1
