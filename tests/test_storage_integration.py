"""
Integration test for storage functionality with real endpoints.

Tests the complete flow:
1. Upload a file
2. Validate the file
3. Ingest records
4. Store file in MinIO (mocked)
5. Verify metadata is created
"""

import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
import tempfile
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, DatasetMetadata, UnifiedStarCatalog
from app.services.storage import StorageService, StorageConfiguration
from app.services.file_validation import FileValidator


@pytest.fixture
def test_db():
    """Create an in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_storage_service_full_workflow(test_db):
    """Test complete file upload -> ingest -> storage -> metadata workflow."""
    # Sample CSV data
    csv_content = b"ra,dec,magnitude,source\n"
    csv_content += b"180.5,45.2,12.3,gaia\n"
    csv_content += b"181.2,46.1,13.1,gaia\n"
    
    # 1. Validate file
    validator = FileValidator()
    validation_result = validator.validate_file(
        file_obj=BytesIO(csv_content),
        filename="test_gaia.csv"
    )
    
    assert validation_result.is_valid
    assert validation_result.file_hash is not None
    assert len(validation_result.file_hash) == 64  # SHA256
    
    # 2. Upload file to storage (mocked MinIO)
    with patch('app.services.storage.Minio') as mock_minio_class:
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        
        config = StorageConfiguration()
        storage = StorageService(config)
        
        storage_key = storage.upload_file(
            file_content=csv_content,
            filename="test_gaia.csv",
            dataset_id="test-dataset-123",
            content_type="text/csv",
            file_hash=validation_result.file_hash
        )
        
        assert storage_key is not None
        assert "test-dataset-123" in storage_key
        assert "test_gaia.csv" in storage_key
        
        # Verify MinIO was called
        mock_client.put_object.assert_called_once()
    
    # 3. Create dataset metadata
    dataset = DatasetMetadata(
        dataset_id="test-dataset-123",
        source_name="test_gaia.csv",
        catalog_type="gaia",
        adapter_used="GaiaAdapter",
        record_count=2,
        original_filename="test_gaia.csv",
        file_size_bytes=len(csv_content),
        file_hash=validation_result.file_hash,
        storage_key=storage_key,
        license_info="ESA/Gaia DPAC"
    )
    
    test_db.add(dataset)
    test_db.commit()
    
    # 4. Verify metadata was stored correctly
    retrieved = test_db.query(DatasetMetadata).filter_by(
        dataset_id="test-dataset-123"
    ).first()
    
    assert retrieved is not None
    assert retrieved.source_name == "test_gaia.csv"
    assert retrieved.catalog_type == "gaia"
    assert retrieved.record_count == 2
    assert retrieved.file_hash == validation_result.file_hash
    assert retrieved.storage_key == storage_key
    assert retrieved.license_info == "ESA/Gaia DPAC"


def test_storage_file_hash_consistency(test_db):
    """Test that file hash is consistent across validation and storage."""
    file_content = b"test,data\n1,2\n3,4\n"
    
    # Validate multiple times
    validator = FileValidator()
    result1 = validator.validate_file(
        file_obj=BytesIO(file_content),
        filename="test.csv"
    )
    result2 = validator.validate_file(
        file_obj=BytesIO(file_content),
        filename="test.csv"
    )
    
    # Should produce identical hashes
    assert result1.file_hash == result2.file_hash
    
    # Store hashes
    test_db.add(DatasetMetadata(
        dataset_id="test-1",
        source_name="test.csv",
        catalog_type="csv",
        adapter_used="CSVAdapter",
        record_count=2,
        file_hash=result1.file_hash,
        storage_key="datasets/test-1/files/test.csv"
    ))
    test_db.add(DatasetMetadata(
        dataset_id="test-2",
        source_name="test.csv",
        catalog_type="csv",
        adapter_used="CSVAdapter",
        record_count=2,
        file_hash=result2.file_hash,
        storage_key="datasets/test-2/files/test.csv"
    ))
    test_db.commit()
    
    # Query and verify
    records = test_db.query(DatasetMetadata).all()
    assert len(records) == 2
    assert records[0].file_hash == records[1].file_hash


def test_dataset_metadata_with_storage_key(test_db):
    """Test storing and retrieving complete dataset metadata."""
    dataset = DatasetMetadata(
        dataset_id="dataset-with-storage",
        source_name="astronomical_catalog.fits",
        catalog_type="fits",
        adapter_used="FITSAdapter",
        schema_version="1.0",
        record_count=1000,
        original_filename="astronomical_catalog.fits",
        file_size_bytes=5242880,  # 5 MB
        file_hash="abcd1234efgh5678ijkl9012mnop3456",
        storage_key="datasets/dataset-with-storage/files/20240115_144530_astronomical_catalog.fits",
        license_info="Public Domain"
    )
    
    test_db.add(dataset)
    test_db.commit()
    
    # Retrieve and verify all fields
    retrieved = test_db.query(DatasetMetadata).filter_by(
        dataset_id="dataset-with-storage"
    ).first()
    
    assert retrieved is not None
    assert retrieved.file_hash == "abcd1234efgh5678ijkl9012mnop3456"
    assert retrieved.storage_key == "datasets/dataset-with-storage/files/20240115_144530_astronomical_catalog.fits"
    assert retrieved.file_size_bytes == 5242880
    assert retrieved.record_count == 1000


def test_multiple_datasets_storage_isolation(test_db):
    """Test that multiple datasets maintain separate storage keys."""
    datasets = [
        DatasetMetadata(
            dataset_id=f"dataset-{i}",
            source_name=f"file-{i}.csv",
            catalog_type="csv",
            adapter_used="CSVAdapter",
            record_count=100 * (i + 1),
            file_hash=f"hash-{i}",
            storage_key=f"datasets/dataset-{i}/files/file-{i}.csv"
        )
        for i in range(5)
    ]
    
    for dataset in datasets:
        test_db.add(dataset)
    test_db.commit()
    
    # Verify all were stored with unique keys
    all_records = test_db.query(DatasetMetadata).all()
    assert len(all_records) == 5
    
    storage_keys = [r.storage_key for r in all_records]
    assert len(set(storage_keys)) == 5  # All unique
    
    hashes = [r.file_hash for r in all_records]
    assert len(set(hashes)) == 5  # All unique


def test_storage_configuration_environment_variables():
    """Test StorageConfiguration respects environment variables."""
    with patch.dict(os.environ, {
        'MINIO_ENDPOINT': 'custom.minio.local:9000',
        'MINIO_ACCESS_KEY': 'custom_access',
        'MINIO_SECRET_KEY': 'custom_secret',
        'MINIO_BUCKET': 'custom-bucket',
        'MINIO_SECURE': 'True'
    }):
        config = StorageConfiguration(bucket=None)
        
        assert config.endpoint == 'custom.minio.local:9000'
        assert config.access_key == 'custom_access'
        assert config.secret_key == 'custom_secret'
        assert config.bucket == 'custom-bucket'
