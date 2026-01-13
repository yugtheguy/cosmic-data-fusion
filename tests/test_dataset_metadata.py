"""
Comprehensive tests for Dataset Metadata functionality.

Tests cover:
- DatasetRepository CRUD operations
- Dataset API endpoints (POST, GET, DELETE)
- Dataset statistics
- Integration with ingestion (auto-registration)
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import DatasetMetadata, UnifiedStarCatalog
from app.repository.dataset_repository import DatasetRepository


# ============================================================
# TEST FIXTURES
# ============================================================

@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    # Use StaticPool to maintain single in-memory database across tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def dataset_repo(db_session):
    """Create DatasetRepository instance."""
    return DatasetRepository(db_session)


@pytest.fixture
def sample_dataset_data():
    """Sample dataset registration data."""
    return {
        "source_name": "Test NGC 2244 FITS",
        "catalog_type": "fits",
        "adapter_used": "FITSAdapter",
        "schema_version": "1.0",
        "original_filename": "ngc2244.fits",
        "file_size_bytes": 1024000,
        "column_mappings": {"RA": "ra_deg", "DEC": "dec_deg", "MAG": "brightness_mag"},
        "raw_config": {"hdu_index": 1, "skip_rows": 0},
        "license_info": "Public Domain",
        "notes": "Test observation of NGC 2244 cluster"
    }


# ============================================================
# REPOSITORY TESTS
# ============================================================

class TestDatasetRepository:
    """Test DatasetRepository CRUD operations."""
    
    def test_create_dataset(self, dataset_repo, sample_dataset_data):
        """Test creating a dataset record."""
        dataset = dataset_repo.create(sample_dataset_data)
        
        assert dataset.id is not None
        assert dataset.dataset_id is not None
        assert len(dataset.dataset_id) == 36  # UUID format
        assert dataset.source_name == "Test NGC 2244 FITS"
        assert dataset.catalog_type == "fits"
        assert dataset.record_count == 0  # Default
        assert dataset.created_at is not None
    
    def test_get_by_id(self, dataset_repo, sample_dataset_data):
        """Test retrieving dataset by UUID."""
        created = dataset_repo.create(sample_dataset_data)
        
        retrieved = dataset_repo.get_by_id(created.dataset_id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.source_name == created.source_name
    
    def test_get_by_id_not_found(self, dataset_repo):
        """Test retrieving non-existent dataset returns None."""
        result = dataset_repo.get_by_id("00000000-0000-0000-0000-000000000000")
        
        assert result is None
    
    def test_get_by_filename(self, dataset_repo, sample_dataset_data):
        """Test retrieving dataset by filename."""
        created = dataset_repo.create(sample_dataset_data)
        
        retrieved = dataset_repo.get_by_filename("ngc2244.fits")
        
        assert retrieved is not None
        assert retrieved.id == created.id
    
    def test_list_all(self, dataset_repo, sample_dataset_data):
        """Test listing all datasets."""
        # Create multiple datasets
        dataset_repo.create(sample_dataset_data)
        
        sample_dataset_data["source_name"] = "Gaia DR3 Query"
        sample_dataset_data["catalog_type"] = "gaia"
        sample_dataset_data["original_filename"] = None
        dataset_repo.create(sample_dataset_data)
        
        # List all
        datasets = dataset_repo.list_all()
        
        assert len(datasets) == 2
        # Should be ordered by ingestion_time DESC (newest first)
        assert datasets[0].source_name == "Gaia DR3 Query"
    
    def test_list_all_with_filter(self, dataset_repo, sample_dataset_data):
        """Test listing datasets with catalog type filter."""
        # Create datasets of different types
        dataset_repo.create(sample_dataset_data)  # fits
        
        sample_dataset_data["source_name"] = "SDSS DR17 Query"
        sample_dataset_data["catalog_type"] = "sdss"
        dataset_repo.create(sample_dataset_data)
        
        sample_dataset_data["source_name"] = "Another FITS"
        sample_dataset_data["catalog_type"] = "fits"
        dataset_repo.create(sample_dataset_data)
        
        # Filter by fits
        fits_datasets = dataset_repo.list_all(catalog_type="fits")
        
        assert len(fits_datasets) == 2
        assert all(d.catalog_type == "fits" for d in fits_datasets)
    
    def test_list_all_pagination(self, dataset_repo, sample_dataset_data):
        """Test pagination works correctly."""
        # Create 5 datasets
        for i in range(5):
            data = sample_dataset_data.copy()
            data["source_name"] = f"Dataset {i}"
            dataset_repo.create(data)
        
        # Get first page (limit 2)
        page1 = dataset_repo.list_all(limit=2, offset=0)
        assert len(page1) == 2
        
        # Get second page
        page2 = dataset_repo.list_all(limit=2, offset=2)
        assert len(page2) == 2
        
        # Ensure different results
        assert page1[0].id != page2[0].id
    
    def test_count_all(self, dataset_repo, sample_dataset_data):
        """Test counting datasets."""
        dataset_repo.create(sample_dataset_data)
        
        sample_dataset_data["source_name"] = "Another Dataset"
        dataset_repo.create(sample_dataset_data)
        
        count = dataset_repo.count_all()
        
        assert count == 2
    
    def test_count_all_with_filter(self, dataset_repo, sample_dataset_data):
        """Test counting with catalog type filter."""
        dataset_repo.create(sample_dataset_data)  # fits
        
        sample_dataset_data["catalog_type"] = "gaia"
        dataset_repo.create(sample_dataset_data)
        
        fits_count = dataset_repo.count_all(catalog_type="fits")
        gaia_count = dataset_repo.count_all(catalog_type="gaia")
        
        assert fits_count == 1
        assert gaia_count == 1
    
    def test_update_record_count(self, dataset_repo, sample_dataset_data):
        """Test updating record count."""
        dataset = dataset_repo.create(sample_dataset_data)
        assert dataset.record_count == 0
        
        updated = dataset_repo.update_record_count(dataset.dataset_id, 150)
        
        assert updated is not None
        assert updated.record_count == 150
        assert updated.updated_at > updated.created_at
    
    def test_increment_record_count(self, dataset_repo, sample_dataset_data):
        """Test incrementing record count."""
        dataset = dataset_repo.create(sample_dataset_data)
        
        dataset_repo.update_record_count(dataset.dataset_id, 100)
        
        # Increment by 25
        updated = dataset_repo.increment_record_count(dataset.dataset_id, 25)
        
        assert updated.record_count == 125
    
    def test_update(self, dataset_repo, sample_dataset_data):
        """Test updating dataset fields."""
        dataset = dataset_repo.create(sample_dataset_data)
        
        updated = dataset_repo.update(dataset.dataset_id, {
            "notes": "Updated notes",
            "license_info": "CC BY 4.0"
        })
        
        assert updated is not None
        assert updated.notes == "Updated notes"
        assert updated.license_info == "CC BY 4.0"
        # Other fields unchanged
        assert updated.source_name == sample_dataset_data["source_name"]
    
    def test_delete(self, dataset_repo, sample_dataset_data):
        """Test deleting dataset."""
        dataset = dataset_repo.create(sample_dataset_data)
        dataset_id = dataset.dataset_id
        
        deleted = dataset_repo.delete(dataset_id)
        
        assert deleted is True
        
        # Verify it's gone
        retrieved = dataset_repo.get_by_id(dataset_id)
        assert retrieved is None
    
    def test_delete_not_found(self, dataset_repo):
        """Test deleting non-existent dataset returns False."""
        deleted = dataset_repo.delete("00000000-0000-0000-0000-000000000000")
        
        assert deleted is False
    
    def test_get_statistics(self, dataset_repo, sample_dataset_data):
        """Test getting dataset statistics."""
        # Create datasets
        data1 = sample_dataset_data.copy()
        data1["catalog_type"] = "fits"
        d1 = dataset_repo.create(data1)
        dataset_repo.update_record_count(d1.dataset_id, 100)
        
        data2 = sample_dataset_data.copy()
        data2["catalog_type"] = "gaia"
        d2 = dataset_repo.create(data2)
        dataset_repo.update_record_count(d2.dataset_id, 250)
        
        data3 = sample_dataset_data.copy()
        data3["catalog_type"] = "fits"
        d3 = dataset_repo.create(data3)
        dataset_repo.update_record_count(d3.dataset_id, 50)
        
        stats = dataset_repo.get_statistics()
        
        assert stats["total_datasets"] == 3
        assert stats["total_records"] == 400
        assert "fits" in stats["by_catalog_type"]
        assert "gaia" in stats["by_catalog_type"]
        assert stats["by_catalog_type"]["fits"]["dataset_count"] == 2
        assert stats["by_catalog_type"]["fits"]["record_count"] == 150
        assert stats["by_catalog_type"]["gaia"]["dataset_count"] == 1
        assert stats["by_catalog_type"]["gaia"]["record_count"] == 250


# ============================================================
# API ENDPOINT TESTS
# ============================================================

class TestDatasetAPI:
    """Test dataset API endpoints."""
    
    def test_register_dataset(self, db_session):
        """Test POST /datasets/register endpoint."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        # Override get_db dependency
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        from app.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.post("/datasets/register", json={
            "source_name": "API Test Dataset",
            "catalog_type": "csv",
            "adapter_used": "CSVAdapter"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["source_name"] == "API Test Dataset"
        assert data["catalog_type"] == "csv"
        assert data["record_count"] == 0
        assert "dataset_id" in data
    
    def test_register_duplicate_filename(self, db_session, dataset_repo, sample_dataset_data):
        """Test registering dataset with duplicate filename fails."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        # Create existing dataset
        dataset_repo.create(sample_dataset_data)
        
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        from app.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        # Try to register with same filename
        response = client.post("/datasets/register", json={
            "source_name": "Duplicate",
            "catalog_type": "fits",
            "adapter_used": "FITSAdapter",
            "original_filename": "ngc2244.fits"  # Duplicate
        })
        
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"]
    
    def test_list_datasets(self, db_session, dataset_repo, sample_dataset_data):
        """Test GET /datasets endpoint."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        # Create datasets
        dataset_repo.create(sample_dataset_data)
        
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        from app.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.get("/datasets")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["datasets"]) == 1
        assert data["limit"] == 100
        assert data["offset"] == 0
    
    def test_get_dataset_statistics(self, db_session, dataset_repo, sample_dataset_data):
        """Test GET /datasets/statistics endpoint."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        # Create dataset
        dataset = dataset_repo.create(sample_dataset_data)
        dataset_repo.update_record_count(dataset.dataset_id, 200)
        
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        from app.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.get("/datasets/statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_datasets"] == 1
        assert data["total_records"] == 200
        assert "fits" in data["by_catalog_type"]
    
    def test_get_dataset_by_id(self, db_session, dataset_repo, sample_dataset_data):
        """Test GET /datasets/{dataset_id} endpoint."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        dataset = dataset_repo.create(sample_dataset_data)
        
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        from app.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.get(f"/datasets/{dataset.dataset_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["dataset_id"] == dataset.dataset_id
        assert data["source_name"] == "Test NGC 2244 FITS"
    
    def test_get_dataset_by_id_not_found(self, db_session):
        """Test GET /datasets/{dataset_id} returns 404 if not found."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        from app.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.get("/datasets/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 404
    
    def test_delete_dataset(self, db_session, dataset_repo, sample_dataset_data):
        """Test DELETE /datasets/{dataset_id} endpoint."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        dataset = dataset_repo.create(sample_dataset_data)
        dataset_id = dataset.dataset_id
        
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        from app.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.delete(f"/datasets/{dataset_id}")
        
        assert response.status_code == 204
        
        # Verify deletion
        retrieved = dataset_repo.get_by_id(dataset_id)
        assert retrieved is None


# ============================================================
# INTEGRATION TESTS
# ============================================================

class TestDatasetIngestionIntegration:
    """Test integration between dataset registration and ingestion."""
    
    def test_auto_ingest_creates_dataset(self, db_session):
        """Test that auto-ingest automatically creates dataset record."""
        from fastapi.testclient import TestClient
        from app.main import app
        import io
        
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        from app.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        # Create test CSV
        csv_content = "source_id,ra,dec,mag\nTEST001,10.5,20.3,12.5\nTEST002,11.2,21.1,13.2"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        # Ingest
        response = client.post("/ingest/auto", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["records_ingested"] == 2
        
        # Verify dataset was created
        repo = DatasetRepository(db_session)
        datasets = repo.list_all()
        
        assert len(datasets) == 1
        assert datasets[0].record_count == 2
        assert datasets[0].original_filename == "test.csv"
    
    def test_ingested_records_have_dataset_id(self, db_session):
        """Test that ingested records have dataset_id set."""
        from fastapi.testclient import TestClient
        from app.main import app
        import io
        
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        from app.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        # Ingest
        csv_content = "source_id,ra,dec,mag\nTEST_DS001,15.5,25.3,11.5"
        files = {"file": ("test_ds.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = client.post("/ingest/auto", files=files)
        assert response.status_code == 200
        
        # Check star record
        star = db_session.query(UnifiedStarCatalog).filter(
            UnifiedStarCatalog.source_id == "TEST_DS001"
        ).first()
        
        assert star is not None
        assert star.dataset_id is not None
        assert len(star.dataset_id) == 36  # UUID format


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
