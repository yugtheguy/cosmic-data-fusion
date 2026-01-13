"""
Stage 4 Test: CSV Database Integration

Tests:
1. Process batch and insert into database
2. Query ingested records
3. Multiple CSV ingestion with unique dataset IDs
4. Error handling for invalid records
"""

import pytest
from io import StringIO
from sqlalchemy.orm import Session

from app.services.adapters.csv_adapter import CSVAdapter
from app.database import SessionLocal, engine
from app.models import UnifiedStarCatalog


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Drop and recreate tables
    UnifiedStarCatalog.__table__.drop(engine, checkfirst=True)
    UnifiedStarCatalog.__table__.create(engine)
    
    session = SessionLocal()
    yield session
    session.close()


def test_01_process_batch_basic(db_session: Session):
    """Test processing a batch of CSV records to database."""
    csv_data = """ra,dec,mag,parallax
10.5,20.3,12.5,5.0
45.8,-30.1,14.2,3.1
"""
    
    adapter = CSVAdapter()
    records, validation_results = adapter.process_batch(StringIO(csv_data))
    
    # Check processing results
    assert len(records) == 2
    assert len(validation_results) == 2
    assert all(r.is_valid for r in validation_results)
    
    # Insert into database
    for record in records:
        star = UnifiedStarCatalog(**record)
        db_session.add(star)
    db_session.commit()
    
    # Query back
    stars = db_session.query(UnifiedStarCatalog).all()
    assert len(stars) == 2
    assert stars[0].ra_deg == 10.5
    assert stars[1].ra_deg == 45.8


def test_02_skip_invalid_records(db_session: Session):
    """Test skipping invalid records in batch processing."""
    csv_data = """ra,dec,mag
10.5,20.3,12.5
invalid,20.3,12.5
45.8,-30.1,14.2
"""
    
    adapter = CSVAdapter()
    records, validation_results = adapter.process_batch(
        StringIO(csv_data),
        skip_invalid=True
    )
    
    # Should process 2 valid records, skip 1 invalid
    assert len(validation_results) == 3
    assert len(records) == 2
    assert sum(1 for r in validation_results if r.is_valid) == 2
    assert sum(1 for r in validation_results if not r.is_valid) == 1


def test_03_error_on_invalid_when_not_skipping(db_session: Session):
    """Test that invalid records raise error when skip_invalid=False."""
    csv_data = """ra,dec,mag
10.5,20.3,12.5
invalid,20.3,12.5
"""
    
    adapter = CSVAdapter()
    
    with pytest.raises(ValueError) as exc_info:
        adapter.process_batch(StringIO(csv_data), skip_invalid=False)
    
    assert "Invalid coordinate" in str(exc_info.value)


def test_04_unique_dataset_ids(db_session: Session):
    """Test that multiple CSV ingestions get unique dataset IDs."""
    csv_data1 = """ra,dec,mag
10.5,20.3,12.5
"""
    
    csv_data2 = """ra,dec,mag
45.8,-30.1,14.2
"""
    
    # Process first CSV
    adapter1 = CSVAdapter()
    records1, _ = adapter1.process_batch(StringIO(csv_data1))
    
    # Process second CSV
    adapter2 = CSVAdapter()
    records2, _ = adapter2.process_batch(StringIO(csv_data2))
    
    # Dataset IDs should be different
    assert records1[0]['dataset_id'] != records2[0]['dataset_id']
    
    # Insert both
    for record in records1 + records2:
        star = UnifiedStarCatalog(**record)
        db_session.add(star)
    db_session.commit()
    
    # Check unique datasets in DB
    unique_datasets = db_session.query(UnifiedStarCatalog.dataset_id).distinct().all()
    assert len(unique_datasets) == 2


def test_05_metadata_json_storage(db_session: Session):
    """Test that metadata is stored as JSON in database."""
    csv_data = """ra,dec,mag,pmra,pmdec,spectral_type
10.5,20.3,12.5,10.2,-5.3,G2V
"""
    
    adapter = CSVAdapter()
    records, _ = adapter.process_batch(StringIO(csv_data))
    
    # Insert into database
    star = UnifiedStarCatalog(**records[0])
    db_session.add(star)
    db_session.commit()
    
    # Query back and check metadata
    retrieved = db_session.query(UnifiedStarCatalog).first()
    assert retrieved.raw_metadata is not None
    assert retrieved.raw_metadata['pmra'] == '10.2'
    assert retrieved.raw_metadata['spectral_type'] == 'G2V'


def test_06_parallax_distance_calculation(db_session: Session):
    """Test parallax to distance calculation stored correctly."""
    csv_data = """ra,dec,mag,parallax
10.5,20.3,12.5,10.0
"""
    
    adapter = CSVAdapter()
    records, _ = adapter.process_batch(StringIO(csv_data))
    
    star = UnifiedStarCatalog(**records[0])
    db_session.add(star)
    db_session.commit()
    
    retrieved = db_session.query(UnifiedStarCatalog).first()
    assert retrieved.parallax_mas == 10.0
    assert retrieved.distance_pc is not None
    assert abs(retrieved.distance_pc - 100.0) < 0.1  # 1000/10 = 100 pc


def test_07_batch_summary_warnings(db_session: Session):
    """Test that batch processing reports warnings correctly."""
    csv_data = """ra,dec,mag,parallax
10.5,20.3,0.0,5.0
45.8,89.0,12.5,1500.0
"""
    
    adapter = CSVAdapter()
    records, validation_results = adapter.process_batch(StringIO(csv_data))
    
    # Both records valid but have warnings
    assert len(records) == 2
    assert all(r.is_valid for r in validation_results)
    assert any(len(r.warnings) > 0 for r in validation_results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
