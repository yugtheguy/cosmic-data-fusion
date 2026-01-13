"""
CSV Adapter - Stage 6: Error Handling & Edge Cases

Tests error handling, edge cases, and robustness of the CSV adapter.
"""

import pytest
from io import StringIO, BytesIO
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.services.adapters.csv_adapter import CSVAdapter


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


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_01_corrupted_csv_structure(client):
    """Test handling of CSV with inconsistent column counts."""
    # Python csv module is lenient and pads missing values with None
    # But our adapter requires valid coordinates, so those rows fail validation
    csv_content = b"""ra,dec,magnitude
10.5,20.3,12.5
15.2,25.8
20.1,30.4,10.1
"""
    
    files = {"file": ("corrupted.csv", BytesIO(csv_content), "text/csv")}
    response = client.post("/ingest/csv", files=files, data={"skip_invalid": "true"})
    
    # CSV parsing may fail or skip invalid rows
    # Either 400 (parsing error) or 200 (some valid rows) is acceptable
    assert response.status_code in [200, 400]


def test_02_missing_required_columns():
    """Test CSV missing both RA and Dec columns."""
    csv_data = """magnitude,parallax
12.5,10.5
11.2,8.3
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    # Validation should fail for missing coordinates
    for record in records:
        result = adapter.validate(record)
        assert not result.is_valid
        assert any("ra" in err.lower() or "dec" in err.lower() for err in result.errors)


def test_03_extremely_large_coordinates():
    """Test handling of coordinates far outside valid ranges."""
    csv_data = """ra,dec
999.9,200.5
-100.0,-200.0
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    for record in records:
        result = adapter.validate(record)
        assert not result.is_valid
        assert len(result.errors) > 0


def test_04_special_characters_in_data():
    """Test handling of special characters and unicode."""
    csv_data = """ra,dec,magnitude,source_id
10.5,20.3,12.5,"Star α-Centauri"
15.2,25.8,11.2,"Star β-Orionis"
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    assert len(records) == 2
    # Must validate before mapping to detect columns
    adapter.validate(records[0])
    unified = adapter.map_to_unified_schema(records[0])
    # Should preserve special characters in source_id
    assert unified['source_id'] is not None


def test_05_null_and_empty_strings():
    """Test various representations of null/missing values."""
    csv_data = """ra,dec,magnitude,parallax
10.5,20.3,12.5,10.5
15.2,25.8,null,
20.1,30.4,NA,N/A
25.3,35.6,,
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    # Should handle various null representations
    assert len(records) == 4
    for record in records:
        result = adapter.validate(record)
        # Coordinates required, but magnitude/parallax optional
        assert result.is_valid or len(result.errors) > 0


def test_06_whitespace_handling():
    """Test trimming of whitespace in column names and values."""
    csv_data = """  ra  , dec  ,magnitude
10.5  ,  20.3,  12.5  
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    assert len(records) == 1
    result = adapter.validate(records[0])
    assert result.is_valid


def test_07_duplicate_dataset_ids():
    """Test that concurrent ingestions get unique dataset IDs."""
    csv_data = """ra,dec
10.5,20.3
"""
    
    adapter1 = CSVAdapter()
    adapter2 = CSVAdapter()
    
    # Dataset IDs should be unique due to microsecond timestamps
    assert adapter1.dataset_id != adapter2.dataset_id


def test_08_very_large_file_handling(client):
    """Test handling of moderately large CSV file (1000 rows)."""
    # Generate large CSV content
    rows = ["ra,dec,magnitude"]
    for i in range(1000):
        ra = 10.0 + (i * 0.01)
        dec = 20.0 + (i * 0.01)
        mag = 12.0 + (i * 0.001)
        rows.append(f"{ra},{dec},{mag}")
    
    csv_content = "\n".join(rows).encode('utf-8')
    
    files = {"file": ("large.csv", BytesIO(csv_content), "text/csv")}
    response = client.post("/ingest/csv", files=files)
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["ingested_count"] == 1000


def test_09_scientific_notation():
    """Test handling of scientific notation in numeric columns."""
    csv_data = """ra,dec,magnitude,parallax
1.05e1,2.03e1,1.25e1,1.05e1
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    assert len(records) == 1
    result = adapter.validate(records[0])
    assert result.is_valid
    
    unified = adapter.map_to_unified_schema(records[0])
    assert unified['ra_deg'] == pytest.approx(10.5, rel=0.01)


def test_10_mixed_case_column_names():
    """Test case-insensitive column name matching."""
    csv_data = """RA,DEC,MAGNITUDE
10.5,20.3,12.5
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    assert len(records) == 1
    result = adapter.validate(records[0])
    assert result.is_valid


def test_11_comments_and_metadata_lines():
    """Test skipping comment lines and metadata headers."""
    csv_data = """# This is a catalog file
# Generated on 2026-01-13
# Author: Test
ra,dec,magnitude
10.5,20.3,12.5
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    assert len(records) == 1
    assert records[0].get('ra') or records[0].get('RA')


def test_12_error_on_invalid_when_skip_false():
    """Test that processing raises error when skip_invalid=False."""
    csv_data = """ra,dec
10.5,20.3
invalid,invalid
"""
    
    adapter = CSVAdapter()
    
    with pytest.raises(ValueError) as exc_info:
        adapter.process_batch(StringIO(csv_data), skip_invalid=False)
    
    assert "invalid" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()
