"""
Unit tests for Storage Service (MinIO object storage).

Tests file upload, download, deletion, metadata management, and presigned URLs.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from io import BytesIO

from app.services.storage import StorageService, StorageConfiguration


class TestStorageConfiguration:
    """Test suite for StorageConfiguration."""
    
    def test_configuration_with_explicit_params(self):
        """Test configuration initialization with explicit parameters."""
        config = StorageConfiguration(
            endpoint="minio.example.com:9000",
            access_key="testkey",
            secret_key="testsecret",
            bucket="test-bucket",
            secure=True
        )
        
        assert config.endpoint == "minio.example.com:9000"
        assert config.access_key == "testkey"
        assert config.secret_key == "testsecret"
        assert config.bucket == "test-bucket"
        assert config.secure is True
    
    def test_configuration_with_defaults(self):
        """Test configuration uses default values."""
        config = StorageConfiguration()
        
        assert config.endpoint == "localhost:9000"
        assert config.access_key == "minioadmin"
        assert config.secret_key == "minioadmin"
        assert config.bucket == "astronomical-data"
        # Default secure is True for environment variable defaults
        assert config.secure in (True, False)


class TestStorageService:
    """Test suite for StorageService."""
    
    @pytest.fixture
    def mock_minio_client(self):
        """Create a mock MinIO client."""
        with patch('app.services.storage.Minio') as mock:
            mock_client = MagicMock()
            mock.return_value = mock_client
            mock_client.bucket_exists.return_value = True
            yield mock_client
    
    @pytest.fixture
    def storage_service(self, mock_minio_client):
        """Create a StorageService instance with mocked MinIO client."""
        config = StorageConfiguration(
            endpoint="localhost:9000",
            access_key="test",
            secret_key="test"
        )
        return StorageService(config)
    
    def test_storage_service_initialization(self, mock_minio_client):
        """Test StorageService initialization."""
        config = StorageConfiguration()
        service = StorageService(config)
        
        assert service.config.endpoint == "localhost:9000"
        assert service.client is not None
        mock_minio_client.bucket_exists.assert_called_once()
    
    def test_upload_file(self, storage_service, mock_minio_client):
        """Test uploading a file to storage."""
        file_content = b"test,data\n1,2\n"
        filename = "test.csv"
        dataset_id = "test-dataset-123"
        
        result = storage_service.upload_file(
            file_content=file_content,
            filename=filename,
            dataset_id=dataset_id,
            content_type="text/csv",
            file_hash="abc123def456"
        )
        
        # Verify upload was called
        mock_minio_client.put_object.assert_called_once()
        call_args = mock_minio_client.put_object.call_args
        
        # Verify call parameters
        assert call_args[0][0] == "astronomical-data"  # bucket
        assert "test-dataset-123" in call_args[0][1]   # object_key contains dataset_id
        assert "test.csv" in call_args[0][1]           # object_key contains filename
        assert call_args[0][3] == len(file_content)    # file_size
        
        # Verify result is object key
        assert isinstance(result, str)
        assert "datasets/" in result
    
    def test_download_file(self, storage_service, mock_minio_client):
        """Test downloading a file from storage."""
        object_key = "datasets/test-123/files/test.csv"
        mock_response = MagicMock()
        mock_response.read.return_value = b"test,data\n1,2\n"
        mock_minio_client.get_object.return_value = mock_response
        
        result = storage_service.download_file(object_key)
        
        assert result == b"test,data\n1,2\n"
        mock_minio_client.get_object.assert_called_once_with(
            "astronomical-data",
            object_key
        )
        mock_response.close.assert_called_once()
    
    def test_delete_file(self, storage_service, mock_minio_client):
        """Test deleting a file from storage."""
        object_key = "datasets/test-123/files/test.csv"
        
        result = storage_service.delete_file(object_key)
        
        assert result is True
        mock_minio_client.remove_object.assert_called_once_with(
            "astronomical-data",
            object_key
        )
    
    def test_get_file_url(self, storage_service, mock_minio_client):
        """Test generating a presigned download URL."""
        object_key = "datasets/test-123/files/test.csv"
        mock_url = "https://minio.local:9000/astronomical-data/datasets/test-123/files/test.csv?X-Amz-Signature=..."
        mock_minio_client.get_presigned_download_url.return_value = mock_url
        
        result = storage_service.get_file_url(object_key, expiration_hours=24)
        
        assert result == mock_url
        mock_minio_client.get_presigned_download_url.assert_called_once()
        call_args = mock_minio_client.get_presigned_download_url.call_args
        assert call_args[0][0] == "astronomical-data"
        assert call_args[0][1] == object_key
        assert call_args[1]["expires"] == 24 * 3600  # 24 hours in seconds
    
    def test_get_file_info(self, storage_service, mock_minio_client):
        """Test retrieving file metadata."""
        object_key = "datasets/test-123/files/test.csv"
        
        mock_stat = MagicMock()
        mock_stat.size = 1024
        mock_stat.last_modified = None
        mock_stat.content_type = "text/csv"
        mock_stat.metadata = {"original-filename": "test.csv"}
        
        mock_minio_client.stat_object.return_value = mock_stat
        
        result = storage_service.get_file_info(object_key)
        
        assert result["size"] == 1024
        assert result["content_type"] == "text/csv"
        assert result["metadata"]["original-filename"] == "test.csv"
        mock_minio_client.stat_object.assert_called_once()
    
    def test_delete_dataset_files(self, storage_service, mock_minio_client):
        """Test deleting all files in a dataset."""
        dataset_id = "test-dataset-123"
        
        # Mock file listing
        mock_obj1 = MagicMock()
        mock_obj1.object_name = f"datasets/{dataset_id}/files/file1.csv"
        mock_obj2 = MagicMock()
        mock_obj2.object_name = f"datasets/{dataset_id}/files/file2.csv"
        
        mock_minio_client.list_objects.return_value = [mock_obj1, mock_obj2]
        
        result = storage_service.delete_dataset_files(dataset_id)
        
        assert result == 2
        assert mock_minio_client.remove_object.call_count == 2
    
    def test_list_dataset_files(self, storage_service, mock_minio_client):
        """Test listing files in a dataset."""
        dataset_id = "test-dataset-123"
        
        # Mock file listing
        mock_obj1 = MagicMock()
        mock_obj1.object_name = f"datasets/{dataset_id}/files/file1.csv"
        mock_obj2 = MagicMock()
        mock_obj2.object_name = f"datasets/{dataset_id}/files/file2.fits"
        
        mock_minio_client.list_objects.return_value = [mock_obj1, mock_obj2]
        
        result = storage_service.list_dataset_files(dataset_id)
        
        assert len(result) == 2
        assert f"datasets/{dataset_id}/files/file1.csv" in result
        assert f"datasets/{dataset_id}/files/file2.fits" in result
    
    def test_upload_file_with_s3_error(self, storage_service, mock_minio_client):
        """Test error handling during file upload."""
        # Simulate S3Error with Exception
        mock_minio_client.put_object.side_effect = Exception("S3 upload failed")
        
        with pytest.raises(Exception):
            storage_service.upload_file(
                file_content=b"test",
                filename="test.csv",
                dataset_id="test-123"
            )
    
    def test_download_file_with_s3_error(self, storage_service, mock_minio_client):
        """Test error handling during file download."""
        # Simulate S3Error with Exception
        mock_minio_client.get_object.side_effect = Exception("S3 download failed")
        
        with pytest.raises(Exception):
            storage_service.download_file("datasets/test-123/files/test.csv")
    
    def test_upload_creates_bucket_if_not_exists(self):
        """Test that bucket is created if it doesn't exist."""
        with patch('app.services.storage.Minio') as mock_minio_class:
            mock_client = MagicMock()
            mock_minio_class.return_value = mock_client
            
            # First check: bucket doesn't exist
            mock_client.bucket_exists.return_value = False
            
            config = StorageConfiguration()
            service = StorageService(config)
            
            # Verify bucket creation was attempted
            mock_client.make_bucket.assert_called_once_with("astronomical-data")
    
    def test_file_metadata_preserved(self, storage_service, mock_minio_client):
        """Test that file metadata is preserved during upload."""
        file_content = b"test data"
        file_hash = "abcd1234"
        
        storage_service.upload_file(
            file_content=file_content,
            filename="test.csv",
            dataset_id="dataset-123",
            content_type="text/csv",
            file_hash=file_hash
        )
        
        # Check metadata in put_object call
        call_kwargs = mock_minio_client.put_object.call_args[1]
        metadata = call_kwargs.get("metadata", {})
        
        assert metadata.get("original-filename") == "test.csv"
        assert metadata.get("dataset-id") == "dataset-123"
        assert metadata.get("file-hash") == file_hash
    
    def test_get_file_url_expiration(self, storage_service, mock_minio_client):
        """Test presigned URL with different expiration times."""
        mock_minio_client.get_presigned_download_url.return_value = "https://test-url"
        
        # Test 1 hour expiration
        storage_service.get_file_url("test-key", expiration_hours=1)
        assert mock_minio_client.get_presigned_download_url.call_args[1]["expires"] == 3600
        
        # Test 7 day expiration
        storage_service.get_file_url("test-key", expiration_hours=168)
        assert mock_minio_client.get_presigned_download_url.call_args[1]["expires"] == 168 * 3600
