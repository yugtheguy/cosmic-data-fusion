"""
Object Storage Service for COSMIC Data Fusion.

Handles file persistence using MinIO (S3-compatible object storage).
Provides upload, download, and metadata management for astronomical data files.
"""

import logging
import os
from io import BytesIO
from datetime import datetime, timezone
from typing import Optional, BinaryIO
from pathlib import Path

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class StorageConfiguration:
    """Configuration for MinIO object storage."""
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket: str = "astronomical-data",
        secure: bool = True
    ):
        """
        Initialize storage configuration.
        
        Reads from environment variables if parameters not provided:
        - MINIO_ENDPOINT
        - MINIO_ACCESS_KEY
        - MINIO_SECRET_KEY
        - MINIO_BUCKET
        - MINIO_SECURE
        
        Args:
            endpoint: MinIO server endpoint (host:port)
            access_key: MinIO access key
            secret_key: MinIO secret key
            bucket: Bucket name for storing files
            secure: Whether to use HTTPS
        """
        self.endpoint = endpoint or os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = access_key or os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = secret_key or os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket = os.getenv("MINIO_BUCKET", bucket or "astronomical-data")
        self.secure = secure or os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        logger.info(
            f"Storage configured for {self.endpoint} "
            f"(bucket={self.bucket}, secure={self.secure})"
        )


class StorageService:
    """
    Service for managing file persistence using MinIO object storage.
    
    Features:
    - Upload validated files to object storage
    - Download files by dataset/file ID
    - Metadata tracking (upload time, size, hash)
    - Bucket management
    - File lifecycle management
    
    Example Usage:
        >>> config = StorageConfiguration()
        >>> storage = StorageService(config)
        >>> file_url = storage.upload_file(
        ...     file_content=file_bytes,
        ...     filename="gaia_sample.csv",
        ...     dataset_id="abc-123",
        ...     content_type="text/csv"
        ... )
    """
    
    def __init__(self, config: Optional[StorageConfiguration] = None):
        """
        Initialize the storage service with MinIO client.
        
        Args:
            config: StorageConfiguration instance (uses defaults if None)
        """
        self.config = config or StorageConfiguration()
        
        # Initialize MinIO client
        try:
            self.client = Minio(
                self.config.endpoint,
                access_key=self.config.access_key,
                secret_key=self.config.secret_key,
                secure=self.config.secure
            )
            logger.info("MinIO client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            raise
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.config.bucket):
                self.client.make_bucket(self.config.bucket)
                logger.info(f"Created bucket: {self.config.bucket}")
            else:
                logger.debug(f"Bucket already exists: {self.config.bucket}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise
    
    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        dataset_id: str,
        content_type: str = "application/octet-stream",
        file_hash: Optional[str] = None
    ) -> str:
        """
        Upload a file to object storage.
        
        Args:
            file_content: Binary file content
            filename: Original filename
            dataset_id: Dataset ID for organization
            content_type: MIME type of the file
            file_hash: SHA256 hash for integrity verification
            
        Returns:
            Object key (path) in storage
            
        Raises:
            S3Error: If upload fails
        """
        # Create object key with dataset organization
        # Pattern: datasets/{dataset_id}/files/{timestamp}_{filename}
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        object_key = f"datasets/{dataset_id}/files/{timestamp}_{filename}"
        
        file_obj = BytesIO(file_content)
        file_size = len(file_content)
        
        try:
            # Upload file
            self.client.put_object(
                self.config.bucket,
                object_key,
                file_obj,
                file_size,
                content_type=content_type,
                metadata={
                    "original-filename": filename,
                    "dataset-id": dataset_id,
                    "upload-timestamp": datetime.now(timezone.utc).isoformat(),
                    "file-hash": file_hash or ""
                }
            )
            
            logger.info(
                f"File uploaded: {object_key} "
                f"(size={file_size}, hash={file_hash})"
            )
            
            return object_key
            
        except S3Error as e:
            logger.error(f"Failed to upload file {filename}: {e}")
            raise
    
    def download_file(self, object_key: str) -> bytes:
        """
        Download a file from object storage.
        
        Args:
            object_key: Object key (path) returned from upload_file()
            
        Returns:
            Binary file content
            
        Raises:
            S3Error: If download fails
        """
        try:
            response = self.client.get_object(self.config.bucket, object_key)
            content = response.read()
            response.close()
            
            logger.info(f"File downloaded: {object_key} ({len(content)} bytes)")
            
            return content
            
        except S3Error as e:
            logger.error(f"Failed to download file {object_key}: {e}")
            raise
    
    def get_file_url(
        self,
        object_key: str,
        expiration_hours: int = 24
    ) -> str:
        """
        Generate a presigned URL for file download.
        
        URL is valid for the specified expiration time.
        Useful for serving files to users without direct MinIO access.
        
        Args:
            object_key: Object key (path)
            expiration_hours: URL expiration time in hours (max 168/7 days)
            
        Returns:
            Presigned download URL
            
        Raises:
            S3Error: If URL generation fails
        """
        try:
            url = self.client.get_presigned_download_url(
                self.config.bucket,
                object_key,
                expires=3600 * expiration_hours  # Convert to seconds
            )
            
            logger.debug(f"Generated presigned URL for {object_key}")
            
            return url
            
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def delete_file(self, object_key: str) -> bool:
        """
        Delete a file from object storage.
        
        Args:
            object_key: Object key (path)
            
        Returns:
            True if deletion was successful
            
        Raises:
            S3Error: If deletion fails
        """
        try:
            self.client.remove_object(self.config.bucket, object_key)
            logger.info(f"File deleted: {object_key}")
            return True
            
        except S3Error as e:
            logger.error(f"Failed to delete file {object_key}: {e}")
            raise
    
    def delete_dataset_files(self, dataset_id: str) -> int:
        """
        Delete all files associated with a dataset.
        
        Args:
            dataset_id: Dataset ID to delete files for
            
        Returns:
            Number of files deleted
            
        Raises:
            S3Error: If deletion fails
        """
        prefix = f"datasets/{dataset_id}/"
        deleted_count = 0
        
        try:
            # List all objects with the dataset prefix
            objects = self.client.list_objects(
                self.config.bucket,
                prefix=prefix,
                recursive=True
            )
            
            # Delete each object
            for obj in objects:
                self.client.remove_object(self.config.bucket, obj.object_name)
                deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} files for dataset {dataset_id}")
            
            return deleted_count
            
        except S3Error as e:
            logger.error(f"Failed to delete dataset files: {e}")
            raise
    
    def get_file_info(self, object_key: str) -> dict:
        """
        Get metadata about a stored file.
        
        Args:
            object_key: Object key (path)
            
        Returns:
            Dictionary with file information:
            - size: File size in bytes
            - last_modified: Last modification timestamp
            - content_type: MIME type
            - metadata: Custom metadata (if available)
            
        Raises:
            S3Error: If metadata retrieval fails
        """
        try:
            stat = self.client.stat_object(self.config.bucket, object_key)
            
            return {
                "size": stat.size,
                "last_modified": stat.last_modified.isoformat() if stat.last_modified else None,
                "content_type": stat.content_type,
                "metadata": stat.metadata or {}
            }
            
        except S3Error as e:
            logger.error(f"Failed to get file info: {e}")
            raise
    
    def list_dataset_files(self, dataset_id: str) -> list:
        """
        List all files in a dataset.
        
        Args:
            dataset_id: Dataset ID to list files for
            
        Returns:
            List of object keys in the dataset
            
        Raises:
            S3Error: If listing fails
        """
        prefix = f"datasets/{dataset_id}/"
        files = []
        
        try:
            objects = self.client.list_objects(
                self.config.bucket,
                prefix=prefix,
                recursive=True
            )
            
            for obj in objects:
                files.append(obj.object_name)
            
            logger.debug(f"Listed {len(files)} files for dataset {dataset_id}")
            
            return files
            
        except S3Error as e:
            logger.error(f"Failed to list dataset files: {e}")
            raise
