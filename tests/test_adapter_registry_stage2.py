"""
Stage 2: Adapter Detection Tests
Tests auto-detection functionality: extension matching, magic bytes, content analysis
"""

import pytest
import tempfile
import os
from pathlib import Path
from app.services.adapter_registry import (
    AdapterRegistry,
    AdapterDetectionError,
    registry as global_registry
)


class TestExtensionDetection:
    """Test adapter detection based on file extensions."""
    
    def test_detect_fits_by_extension(self):
        """Test detecting FITS files by .fits extension."""
        with tempfile.NamedTemporaryFile(suffix='.fits', delete=False) as f:
            f.write(b'SIMPLE  = T')
            temp_path = f.name
        
        try:
            adapter_name, confidence, method = global_registry.detect_adapter(temp_path)
            assert adapter_name == 'fits'
            assert confidence == 0.99  # Magic bytes detection
            assert method == 'magic_bytes'
        finally:
            os.unlink(temp_path)
    
    def test_detect_csv_by_extension(self):
        """Test detecting CSV files by .csv extension."""
        with tempfile.NamedTemporaryFile(suffix='.csv', mode='w', delete=False) as f:
            f.write('ra,dec,magnitude\n1.0,2.0,3.0\n')
            temp_path = f.name
        
        try:
            adapter_name, confidence, method = global_registry.detect_adapter(temp_path)
            assert adapter_name == 'csv'
            assert confidence >= 0.75
            assert method in ['extension', 'content_analysis']
        finally:
            os.unlink(temp_path)
    
    def test_detect_gaia_by_filename_pattern(self):
        """Test detecting Gaia files by filename pattern."""
        with tempfile.NamedTemporaryFile(suffix='.csv', prefix='gaia_dr3_', mode='w', delete=False) as f:
            f.write('source_id,ra,dec,parallax\n12345,10.5,20.3,1.2\n')
            temp_path = f.name
        
        try:
            adapter_name, confidence, method = global_registry.detect_adapter(temp_path)
            # Should detect either by filename pattern or content
            assert adapter_name in ['gaia', 'csv']
            assert confidence >= 0.75
        finally:
            os.unlink(temp_path)
    
    def test_detect_sdss_by_filename_pattern(self):
        """Test detecting SDSS files by filename pattern."""
        with tempfile.NamedTemporaryFile(suffix='.csv', prefix='sdss_dr17_', mode='w', delete=False) as f:
            f.write('objid,ra,dec,u,g,r,i,z\n123,10.0,20.0,15.0,14.5,14.0,13.5,13.0\n')
            temp_path = f.name
        
        try:
            adapter_name, confidence, method = global_registry.detect_adapter(temp_path)
            # Should detect either by filename pattern or content
            assert adapter_name in ['sdss', 'csv']
            assert confidence >= 0.75
        finally:
            os.unlink(temp_path)


class TestMagicBytesDetection:
    """Test adapter detection based on magic bytes (binary headers)."""
    
    def test_detect_fits_by_magic_bytes(self):
        """Test detecting FITS files by SIMPLE header."""
        with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as f:
            # FITS magic bytes: "SIMPLE  = " at start
            f.write(b'SIMPLE  =                    T / file does conform to FITS standard')
            temp_path = f.name
        
        try:
            adapter_name, confidence, method = global_registry.detect_adapter(temp_path)
            assert adapter_name == 'fits'
            assert confidence == 0.99
            assert method == 'magic_bytes'
        finally:
            os.unlink(temp_path)
    
    def test_magic_bytes_override_extension(self):
        """Test that magic bytes detection overrides misleading extension."""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            # FITS content but CSV extension
            f.write(b'SIMPLE  =                    T / FITS header\n')
            temp_path = f.name
        
        try:
            adapter_name, confidence, method = global_registry.detect_adapter(temp_path)
            assert adapter_name == 'fits'
            assert confidence == 0.99
            assert method == 'magic_bytes'
        finally:
            os.unlink(temp_path)


class TestContentAnalysisDetection:
    """Test adapter detection based on content analysis."""
    
    def test_detect_gaia_by_column_names(self):
        """Test detecting Gaia files by characteristic column names."""
        with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', delete=False) as f:
            # Gaia-specific columns
            f.write('source_id,ra,dec,parallax,pmra,pmdec,phot_g_mean_mag\n')
            f.write('4567890123456789,180.5,45.3,2.5,1.2,0.8,12.5\n')
            temp_path = f.name
        
        try:
            adapter_name, confidence, method = global_registry.detect_adapter(temp_path)
            assert adapter_name == 'gaia'
            assert confidence == 0.80
            assert method == 'content_analysis'
        finally:
            os.unlink(temp_path)
    
    def test_detect_sdss_by_column_names(self):
        """Test detecting SDSS files by characteristic column names."""
        with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', delete=False) as f:
            # SDSS-specific columns (5-band photometry)
            f.write('objid,ra,dec,u,g,r,i,z,redshift\n')
            f.write('1237654321,150.0,30.0,16.5,15.0,14.5,14.0,13.5,0.05\n')
            temp_path = f.name
        
        try:
            adapter_name, confidence, method = global_registry.detect_adapter(temp_path)
            assert adapter_name == 'sdss'
            assert confidence == 0.80
            assert method == 'content_analysis'
        finally:
            os.unlink(temp_path)
    
    def test_detect_generic_csv_by_delimiters(self):
        """Test detecting generic CSV by delimiter presence."""
        with tempfile.NamedTemporaryFile(suffix='.dat', mode='w', delete=False) as f:
            # Generic columns with comma delimiter
            f.write('star_name,brightness,distance\n')
            f.write('Alpha Centauri,0.01,4.37\n')
            temp_path = f.name
        
        try:
            adapter_name, confidence, method = global_registry.detect_adapter(temp_path)
            assert adapter_name == 'csv'
            assert confidence >= 0.75
            assert method == 'content_analysis'
        finally:
            os.unlink(temp_path)


class TestConfidenceThreshold:
    """Test confidence threshold and detection failure cases."""
    
    def test_high_confidence_threshold(self):
        """Test that high confidence threshold rejects low-confidence matches."""
        with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', delete=False) as f:
            f.write('some,random,data\n1,2,3\n')
            temp_path = f.name
        
        try:
            # Should succeed with low threshold
            adapter_name, confidence, method = global_registry.detect_adapter(temp_path, confidence_threshold=0.70)
            assert adapter_name == 'csv'
            
            # Should fail with high threshold
            with pytest.raises(AdapterDetectionError, match="Could not detect adapter"):
                global_registry.detect_adapter(temp_path, confidence_threshold=0.95)
        finally:
            os.unlink(temp_path)
    
    def test_detection_error_contains_results(self):
        """Test that detection error includes attempted detection results."""
        with tempfile.NamedTemporaryFile(suffix='.unknown', mode='w', delete=False) as f:
            f.write('unrecognizable content\n')
            temp_path = f.name
        
        try:
            with pytest.raises(AdapterDetectionError) as exc_info:
                global_registry.detect_adapter(temp_path, confidence_threshold=0.95)
            
            error = exc_info.value
            assert error.file_path == temp_path
            assert isinstance(error.detection_results, dict)
        finally:
            os.unlink(temp_path)
    
    def test_file_not_found_error(self):
        """Test that non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            global_registry.detect_adapter('/nonexistent/path/file.csv')


class TestDetectionPriority:
    """Test that detection strategies are applied in correct priority order."""
    
    def test_magic_bytes_highest_priority(self):
        """Test that magic bytes detection takes precedence over extension."""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            # FITS magic bytes with CSV extension
            f.write(b'SIMPLE  =                    T / FITS\n')
            temp_path = f.name
        
        try:
            adapter_name, confidence, method = global_registry.detect_adapter(temp_path)
            assert adapter_name == 'fits'
            assert method == 'magic_bytes'
            assert confidence == 0.99
        finally:
            os.unlink(temp_path)
    
    def test_extension_over_content(self):
        """Test that extension detection takes precedence over content analysis."""
        with tempfile.NamedTemporaryFile(suffix='.fits', mode='w', delete=False) as f:
            # CSV content but FITS extension (no magic bytes)
            f.write('ra,dec,mag\n1.0,2.0,3.0\n')
            temp_path = f.name
        
        try:
            adapter_name, confidence, method = global_registry.detect_adapter(temp_path)
            # Extension should win (0.95) over content analysis (0.75)
            assert adapter_name == 'fits'
            assert method == 'extension'
            assert confidence == 0.95
        finally:
            os.unlink(temp_path)
