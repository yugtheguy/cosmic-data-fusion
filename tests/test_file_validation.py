"""
Unit tests for File Validation Service.

Tests all file validation functionality:
- MIME type detection
- File size validation
- Encoding detection
- Hash generation
- Error handling
"""

import pytest
import tempfile
from pathlib import Path
from io import BytesIO

from app.services.file_validation import (
    FileValidator,
    FileValidationResult,
    FileValidationError,
    AllowedMimeType
)


class TestFileValidator:
    """Test FileValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create FileValidator instance."""
        return FileValidator()
    
    @pytest.fixture
    def temp_csv_file(self):
        """Create temporary CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("ra,dec,magnitude\n")
            f.write("10.5,20.3,12.5\n")
            f.write("15.2,25.1,13.2\n")
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
    
    @pytest.fixture
    def temp_large_file(self):
        """Create temporary large file (> 500MB)."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
            # Write 600 MB of data
            chunk_size = 1024 * 1024  # 1 MB
            for _ in range(600):
                f.write(b'a' * chunk_size)
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
    
    @pytest.fixture
    def temp_empty_file(self):
        """Create temporary empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
    
    def test_validate_valid_csv_file(self, validator, temp_csv_file):
        """Test validation of valid CSV file."""
        result = validator.validate_file(file_path=temp_csv_file)
        
        assert result.is_valid is True
        assert result.mime_type == AllowedMimeType.CSV.value
        assert result.file_size > 0
        assert result.encoding in ['utf-8', 'ascii']
        assert result.file_hash is not None
        assert len(result.file_hash) == 64  # SHA256 hex digest
        assert len(result.errors) == 0
    
    def test_validate_file_not_found(self, validator):
        """Test validation of non-existent file."""
        result = validator.validate_file(file_path="/nonexistent/file.csv")
        
        assert result.is_valid is False
        assert "not found" in result.errors[0].lower()
    
    def test_validate_empty_file(self, validator, temp_empty_file):
        """Test validation of empty file."""
        result = validator.validate_file(file_path=temp_empty_file)
        
        assert result.is_valid is False
        assert any("empty" in error.lower() for error in result.errors)
        assert result.file_size == 0
    
    def test_validate_large_file(self, validator, temp_large_file):
        """Test validation of file exceeding size limit."""
        result = validator.validate_file(file_path=temp_large_file)
        
        assert result.is_valid is False
        assert any("too large" in error.lower() for error in result.errors)
        assert result.file_size > validator.max_file_size
    
    def test_validate_invalid_extension(self, validator):
        """Test validation of file with invalid extension."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.exe', delete=False) as f:
            f.write("test")
            temp_path = Path(f.name)
        
        try:
            result = validator.validate_file(file_path=temp_path)
            
            assert result.is_valid is False
            assert any("extension" in error.lower() for error in result.errors)
        finally:
            temp_path.unlink()
    
    def test_validate_fits_file_extension(self, validator):
        """Test FITS file extension detection."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.fits', delete=False) as f:
            f.write(b'SIMPLE  =                    T')  # FITS header
            temp_path = Path(f.name)
        
        try:
            result = validator.validate_file(file_path=temp_path)
            
            assert result.mime_type == AllowedMimeType.FITS.value
        finally:
            temp_path.unlink()
    
    def test_validate_fits_gz_file_extension(self, validator):
        """Test FITS.GZ file extension detection."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.fits.gz', delete=False) as f:
            f.write(b'\x1f\x8b')  # Gzip magic bytes
            temp_path = Path(f.name)
        
        try:
            result = validator.validate_file(file_path=temp_path)
            
            assert result.mime_type == AllowedMimeType.FITS_GZ.value
        finally:
            temp_path.unlink()
    
    def test_validate_json_file(self, validator):
        """Test JSON file validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"ra": 10.5, "dec": 20.3}')
            temp_path = Path(f.name)
        
        try:
            result = validator.validate_file(file_path=temp_path)
            
            assert result.is_valid is True
            assert result.mime_type == AllowedMimeType.JSON.value
            assert result.encoding is not None
        finally:
            temp_path.unlink()
    
    def test_validate_file_object(self, validator):
        """Test validation of file-like object (upload)."""
        content = b"ra,dec,magnitude\n10.5,20.3,12.5\n"
        file_obj = BytesIO(content)
        
        result = validator.validate_file(file_obj=file_obj, filename="test.csv")
        
        assert result.is_valid is True
        assert result.mime_type == AllowedMimeType.CSV.value
        assert result.file_size == len(content)
        assert result.file_hash is not None
    
    def test_validate_no_file_provided(self, validator):
        """Test validation with no file provided."""
        result = validator.validate_file()
        
        assert result.is_valid is False
        assert any("no file provided" in error.lower() for error in result.errors)
    
    def test_encoding_detection_utf8(self, validator):
        """Test UTF-8 encoding detection."""
        content = "ra,dec,magnitude\n10.5,20.3,12.5\n".encode('utf-8')
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            result = validator.validate_file(file_path=temp_path)
            
            assert result.encoding == 'utf-8'
        finally:
            temp_path.unlink()
    
    def test_encoding_detection_latin1(self, validator):
        """Test Latin-1 encoding detection."""
        # Create Latin-1 encoded text with special character
        content = "ra,dec,magnitude,name\n10.5,20.3,12.5,Café\n".encode('latin-1')
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            result = validator.validate_file(file_path=temp_path)
            
            # Should detect as latin-1 or fallback to utf-8
            assert result.encoding in ['latin-1', 'utf-8']
        finally:
            temp_path.unlink()
    
    def test_hash_calculation_consistency(self, validator, temp_csv_file):
        """Test that hash calculation is consistent."""
        result1 = validator.validate_file(file_path=temp_csv_file)
        result2 = validator.validate_file(file_path=temp_csv_file)
        
        assert result1.file_hash == result2.file_hash
        assert len(result1.file_hash) == 64  # SHA256 hex
    
    def test_hash_calculation_different_files(self, validator):
        """Test that different files have different hashes."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f1:
            f1.write("file1 content")
            path1 = Path(f1.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f2:
            f2.write("file2 content")
            path2 = Path(f2.name)
        
        try:
            result1 = validator.validate_file(file_path=path1)
            result2 = validator.validate_file(file_path=path2)
            
            assert result1.file_hash != result2.file_hash
        finally:
            path1.unlink()
            path2.unlink()
    
    def test_validate_mime_type_only(self, validator):
        """Test standalone MIME type validation."""
        assert validator.validate_mime_type_only(AllowedMimeType.CSV.value) is True
        assert validator.validate_mime_type_only(AllowedMimeType.FITS.value) is True
        assert validator.validate_mime_type_only("application/pdf") is False
        assert validator.validate_mime_type_only("image/png") is False
    
    def test_validate_file_size_only(self, validator):
        """Test standalone file size validation."""
        # Valid size
        is_valid, error = validator.validate_file_size_only(1024 * 1024)  # 1 MB
        assert is_valid is True
        assert error is None
        
        # Empty file
        is_valid, error = validator.validate_file_size_only(0)
        assert is_valid is False
        assert "empty" in error.lower()
        
        # Too large
        is_valid, error = validator.validate_file_size_only(600 * 1024 * 1024)  # 600 MB
        assert is_valid is False
        assert "too large" in error.lower()
    
    def test_custom_max_file_size(self):
        """Test validator with custom max file size."""
        validator = FileValidator(max_file_size=1024 * 1024)  # 1 MB
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Write 2 MB of data
            f.write('a' * (2 * 1024 * 1024))
            temp_path = Path(f.name)
        
        try:
            result = validator.validate_file(file_path=temp_path)
            
            assert result.is_valid is False
            assert any("too large" in error.lower() for error in result.errors)
        finally:
            temp_path.unlink()
    
    def test_allowed_extensions(self, validator):
        """Test that all allowed extensions are recognized."""
        allowed_extensions = ['.csv', '.fits', '.fits.gz', '.json', '.jsonl', '.txt']
        
        for ext in allowed_extensions:
            assert validator._validate_extension(f"test{ext}") is True
        
        # Test invalid extensions
        assert validator._validate_extension("test.exe") is False
        assert validator._validate_extension("test.pdf") is False
