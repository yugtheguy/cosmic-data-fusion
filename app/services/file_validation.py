"""
File Validation Service for Layer 1 Data Ingestion.

Validates incoming files before processing:
- MIME type detection
- File size validation
- Encoding detection
- Hash generation for deduplication
- Format validation

This ensures only valid files enter the ingestion pipeline.
"""

import hashlib
import logging
import mimetypes
from pathlib import Path
from typing import Optional, Union, BinaryIO
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FileValidationError(Exception):
    """Raised when file validation fails."""
    pass


class AllowedMimeType(str, Enum):
    """Allowed MIME types for ingestion."""
    CSV = "text/csv"
    FITS = "application/fits"
    FITS_GZ = "application/x-gzip"  # .fits.gz files
    JSON = "application/json"
    JSONL = "application/x-ndjson"  # JSON lines
    PLAIN = "text/plain"  # Fallback for CSV without proper MIME


@dataclass
class FileValidationResult:
    """Result of file validation."""
    is_valid: bool
    mime_type: Optional[str] = None
    file_size: int = 0
    encoding: Optional[str] = None
    file_hash: Optional[str] = None
    errors: list[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class FileValidator:
    """
    Validates files before ingestion.
    
    Checks:
    1. File exists and is readable
    2. MIME type is allowed
    3. File size within limits
    4. Encoding detection
    5. SHA256 hash generation
    """
    
    # Configuration
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
    ALLOWED_EXTENSIONS = {'.csv', '.fits', '.fits.gz', '.json', '.jsonl', '.txt'}
    
    def __init__(self, max_file_size: Optional[int] = None):
        """
        Initialize file validator.
        
        Args:
            max_file_size: Maximum allowed file size in bytes (default: 500MB)
        """
        self.max_file_size = max_file_size or self.MAX_FILE_SIZE
        logger.info(f"FileValidator initialized with max_file_size={self.max_file_size / 1024 / 1024:.2f} MB")
    
    def validate_file(
        self, 
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        filename: Optional[str] = None
    ) -> FileValidationResult:
        """
        Validate a file for ingestion.
        
        Args:
            file_path: Path to file on disk
            file_obj: File-like object (for uploads)
            filename: Original filename (required if using file_obj)
        
        Returns:
            FileValidationResult with validation details
        
        Raises:
            FileValidationError: If validation fails critically
        """
        result = FileValidationResult(is_valid=True)
        
        try:
            # Validate inputs
            if file_path is None and file_obj is None:
                result.is_valid = False
                result.errors.append("No file provided (file_path or file_obj required)")
                return result
            
            # Handle file path
            if file_path is not None:
                file_path = Path(file_path)
                if not file_path.exists():
                    result.is_valid = False
                    result.errors.append(f"File not found: {file_path}")
                    return result
                
                if not file_path.is_file():
                    result.is_valid = False
                    result.errors.append(f"Not a file: {file_path}")
                    return result
                
                filename = file_path.name
            
            # Validate file extension
            extension_valid = self._validate_extension(filename)
            if not extension_valid:
                result.is_valid = False
                result.errors.append(
                    f"Invalid file extension. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
                )
                return result
            
            # Validate MIME type
            mime_type = self._detect_mime_type(file_path, file_obj, filename)
            result.mime_type = mime_type
            
            if not self._is_mime_allowed(mime_type):
                result.is_valid = False
                result.errors.append(
                    f"Invalid MIME type: {mime_type}. Allowed types: {', '.join([m.value for m in AllowedMimeType])}"
                )
            
            # Validate file size
            file_size = self._get_file_size(file_path, file_obj)
            result.file_size = file_size
            
            if file_size > self.max_file_size:
                result.is_valid = False
                result.errors.append(
                    f"File too large: {file_size / 1024 / 1024:.2f} MB "
                    f"(max: {self.max_file_size / 1024 / 1024:.2f} MB)"
                )
            
            if file_size == 0:
                result.is_valid = False
                result.errors.append("File is empty (0 bytes)")
            
            # Detect encoding (for text files)
            if mime_type in [AllowedMimeType.CSV.value, AllowedMimeType.PLAIN.value, AllowedMimeType.JSON.value]:
                encoding = self._detect_encoding(file_path, file_obj)
                result.encoding = encoding
                logger.debug(f"Detected encoding: {encoding}")
            
            # Calculate SHA256 hash
            file_hash = self._calculate_hash(file_path, file_obj)
            result.file_hash = file_hash
            logger.debug(f"File hash: {file_hash}")
            
            if result.is_valid:
                logger.info(
                    f"File validation SUCCESS: {filename} "
                    f"({file_size / 1024:.2f} KB, {mime_type}, hash={file_hash[:16]}...)"
                )
            else:
                logger.warning(
                    f"File validation FAILED: {filename} - Errors: {'; '.join(result.errors)}"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"File validation error: {e}", exc_info=True)
            result.is_valid = False
            result.errors.append(f"Validation exception: {str(e)}")
            return result
    
    def _validate_extension(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        if not filename:
            return False
        
        filename_lower = filename.lower()
        
        # Handle .fits.gz specially
        if filename_lower.endswith('.fits.gz'):
            return True
        
        # Check other extensions
        extension = Path(filename_lower).suffix
        return extension in self.ALLOWED_EXTENSIONS
    
    def _detect_mime_type(
        self, 
        file_path: Optional[Path],
        file_obj: Optional[BinaryIO],
        filename: str
    ) -> str:
        """
        Detect MIME type of file.
        
        Uses multiple strategies:
        1. File extension mapping
        2. Python mimetypes library
        3. Content inspection (future: use python-magic if installed)
        """
        # Strategy 1: Extension-based detection
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.csv'):
            return AllowedMimeType.CSV.value
        elif filename_lower.endswith('.fits') or filename_lower.endswith('.fit'):
            return AllowedMimeType.FITS.value
        elif filename_lower.endswith('.fits.gz'):
            return AllowedMimeType.FITS_GZ.value
        elif filename_lower.endswith('.json'):
            return AllowedMimeType.JSON.value
        elif filename_lower.endswith('.jsonl'):
            return AllowedMimeType.JSONL.value
        
        # Strategy 2: Use mimetypes library
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            return mime_type
        
        # Fallback: plain text
        return AllowedMimeType.PLAIN.value
    
    def _is_mime_allowed(self, mime_type: str) -> bool:
        """Check if MIME type is in allowed list."""
        allowed_values = [m.value for m in AllowedMimeType]
        return mime_type in allowed_values
    
    def _get_file_size(
        self, 
        file_path: Optional[Path],
        file_obj: Optional[BinaryIO]
    ) -> int:
        """Get file size in bytes."""
        if file_path is not None:
            return file_path.stat().st_size
        
        if file_obj is not None:
            # Get current position
            current_pos = file_obj.tell()
            
            # Seek to end to get size
            file_obj.seek(0, 2)  # SEEK_END
            size = file_obj.tell()
            
            # Restore original position
            file_obj.seek(current_pos)
            
            return size
        
        return 0
    
    def _detect_encoding(
        self, 
        file_path: Optional[Path],
        file_obj: Optional[BinaryIO]
    ) -> str:
        """
        Detect file encoding.
        
        Tries to detect encoding by reading first 8KB of file.
        Falls back to UTF-8 if detection fails.
        """
        sample_size = 8192  # 8 KB sample
        
        try:
            # Read sample
            if file_path is not None:
                with open(file_path, 'rb') as f:
                    sample = f.read(sample_size)
            elif file_obj is not None:
                current_pos = file_obj.tell()
                sample = file_obj.read(sample_size)
                file_obj.seek(current_pos)  # Restore position
            else:
                return 'utf-8'
            
            # Try UTF-8 first
            try:
                sample.decode('utf-8')
                return 'utf-8'
            except UnicodeDecodeError:
                pass
            
            # Try Latin-1
            try:
                sample.decode('latin-1')
                return 'latin-1'
            except UnicodeDecodeError:
                pass
            
            # Try ASCII
            try:
                sample.decode('ascii')
                return 'ascii'
            except UnicodeDecodeError:
                pass
            
            # Fallback to UTF-8 (will handle with errors='replace' in parsing)
            logger.warning("Encoding detection failed, defaulting to UTF-8")
            return 'utf-8'
            
        except Exception as e:
            logger.warning(f"Encoding detection error: {e}, defaulting to UTF-8")
            return 'utf-8'
    
    def _calculate_hash(
        self, 
        file_path: Optional[Path],
        file_obj: Optional[BinaryIO]
    ) -> str:
        """
        Calculate SHA256 hash of file.
        
        Used for deduplication and integrity verification.
        """
        hash_obj = hashlib.sha256()
        chunk_size = 65536  # 64 KB chunks
        
        try:
            if file_path is not None:
                with open(file_path, 'rb') as f:
                    while chunk := f.read(chunk_size):
                        hash_obj.update(chunk)
            
            elif file_obj is not None:
                current_pos = file_obj.tell()
                file_obj.seek(0)  # Start from beginning
                
                while chunk := file_obj.read(chunk_size):
                    hash_obj.update(chunk)
                
                file_obj.seek(current_pos)  # Restore position
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            logger.error(f"Hash calculation error: {e}")
            return ""
    
    def validate_mime_type_only(self, mime_type: str) -> bool:
        """
        Quick validation of MIME type without file access.
        
        Args:
            mime_type: MIME type string
        
        Returns:
            True if MIME type is allowed
        """
        return self._is_mime_allowed(mime_type)
    
    def validate_file_size_only(self, size: int) -> tuple[bool, Optional[str]]:
        """
        Quick validation of file size.
        
        Args:
            size: File size in bytes
        
        Returns:
            (is_valid, error_message)
        """
        if size == 0:
            return False, "File is empty (0 bytes)"
        
        if size > self.max_file_size:
            return False, (
                f"File too large: {size / 1024 / 1024:.2f} MB "
                f"(max: {self.max_file_size / 1024 / 1024:.2f} MB)"
            )
        
        return True, None
