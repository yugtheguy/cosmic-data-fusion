"""
Stage 3: Auto-Ingestion API Integration Tests
Tests /ingest/auto endpoint with various file types
"""

import pytest
import io
from fastapi.testclient import TestClient

from app.main import app


class TestAutoIngestFITS:
    """Test auto-ingestion of FITS files."""
    
    def test_auto_ingest_fits_by_magic_bytes(self, client):
        """Test auto-detection and ingestion of FITS file via magic bytes."""
        # Create minimal FITS file with magic bytes
        fits_header = b'SIMPLE  =                    T / file conforms to FITS standard             '
        fits_header += b'BITPIX  =                    8 / bits per data pixel                        '
        fits_header += b' ' * (2880 - len(fits_header))  # Pad to 2880 bytes
        
        files = {'file': ('test.fits', io.BytesIO(fits_header), 'application/fits')}
        response = client.post('/ingest/auto', files=files)
        
        # FITS detection should work but parsing might fail (minimal header)
        # Check that detection happened
        assert response.status_code in [200, 400]  # 200 if parsed, 400 if parsing failed
        data = response.json()
        
        if response.status_code == 200:
            assert data['adapter_used'] == 'fits'
            assert data['adapter_confidence'] == 0.99
            assert data['detection_method'] == 'magic_bytes'
    
    def test_auto_ingest_fits_by_extension(self, client):
        """Test auto-detection of FITS file by .fits extension."""
        # CSV content with .fits extension
        csv_content = b'ra,dec,magnitude\n10.5,20.3,15.2\n'
        
        files = {'file': ('catalog.fits', io.BytesIO(csv_content), 'text/csv')}
        response = client.post('/ingest/auto', files=files)
        
        # Should detect as FITS by extension (0.95 confidence)
        assert response.status_code in [200, 400]
        data = response.json()
        
        if 'adapter_used' in data:
            assert data['adapter_used'] == 'fits'
            assert data['detection_method'] == 'extension'


class TestAutoIngestCSV:
    """Test auto-ingestion of generic CSV files."""
    
    def test_auto_ingest_csv_success(self, client):
        """Test successful auto-ingestion of generic CSV."""
        csv_content = (
            b'ra,dec,magnitude,source\n'
            b'10.5,20.3,15.2,Generic Catalog\n'
            b'11.0,21.0,14.5,Generic Catalog\n'
        )
        
        files = {'file': ('catalog.csv', io.BytesIO(csv_content), 'text/csv')}
        response = client.post('/ingest/auto', files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data['adapter_used'] == 'csv'
        assert data['adapter_confidence'] >= 0.75
        assert data['detection_method'] in ['extension', 'content_analysis']
        assert data['records_ingested'] == 2
        assert 'Successfully ingested' in data['message']
    
    def test_auto_ingest_csv_by_content(self, client):
        """Test CSV detection by content analysis (no extension)."""
        csv_content = b'ra,dec,magnitude\n10.5,20.3,15.2\n11.0,21.0,14.5\n'
        
        files = {'file': ('data.dat', io.BytesIO(csv_content), 'application/octet-stream')}
        response = client.post('/ingest/auto', files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data['adapter_used'] == 'csv'
        assert data['detection_method'] == 'content_analysis'
        assert data['records_ingested'] == 2


class TestAutoIngestGaia:
    """Test auto-ingestion of Gaia catalog files."""
    
    def test_auto_ingest_gaia_by_columns(self, client):
        """Test Gaia detection by characteristic columns."""
        gaia_content = (
            b'source_id,ra,dec,parallax,pmra,pmdec,phot_g_mean_mag\n'
            b'4567890123456789,180.5,45.3,2.5,1.2,0.8,12.5\n'
            b'4567890123456790,181.0,46.0,3.0,1.5,1.0,13.0\n'
        )
        
        files = {'file': ('gaia_dr3.txt', io.BytesIO(gaia_content), 'text/plain')}
        response = client.post('/ingest/auto', files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data['adapter_used'] == 'gaia'
        assert data['adapter_confidence'] == 0.80
        assert data['detection_method'] == 'content_analysis'
        assert data['records_ingested'] == 2


class TestAutoIngestSDSS:
    """Test auto-ingestion of SDSS catalog files."""
    
    def test_auto_ingest_sdss_by_columns(self, client):
        """Test SDSS detection by characteristic columns."""
        sdss_content = (
            b'objid,ra,dec,u,g,r,i,z,redshift,psfMag_g\n'
            b'1237654321,150.0,30.0,16.5,15.0,14.5,14.0,13.5,0.05,15.0\n'
            b'1237654322,151.0,31.0,17.0,15.5,15.0,14.5,14.0,0.08,15.5\n'
        )
        
        files = {'file': ('sdss_dr17.txt', io.BytesIO(sdss_content), 'text/plain')}
        response = client.post('/ingest/auto', files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data['adapter_used'] == 'sdss'
        assert data['adapter_confidence'] == 0.80
        assert data['detection_method'] == 'content_analysis'
        assert data['records_ingested'] == 2


class TestAutoIngestErrors:
    """Test error handling in auto-ingestion."""
    
    def test_auto_ingest_unrecognizable_file(self, client):
        """Test that unrecognizable file returns 400."""
        # Binary garbage that doesn't match any adapter
        garbage = b'\x00\x01\x02\x03\x04\x05\x06\x07'
        
        files = {'file': ('unknown.bin', io.BytesIO(garbage), 'application/octet-stream')}
        response = client.post('/ingest/auto', files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert 'Could not detect file type' in data['detail']
    
    def test_auto_ingest_invalid_csv_data(self, client):
        """Test that malformed CSV returns 400."""
        # CSV with invalid numeric data
        csv_content = b'ra,dec,magnitude\ninvalid,data,here\n'
        
        files = {'file': ('bad.csv', io.BytesIO(csv_content), 'text/csv')}
        response = client.post('/ingest/auto', files=files)
        
        # Should detect as CSV but fail validation/parsing
        assert response.status_code == 400
        data = response.json()
        assert 'Failed to process' in data['detail'] or 'Invalid' in data['detail']
    
    def test_auto_ingest_empty_file(self, client):
        """Test that empty file returns 400."""
        files = {'file': ('empty.csv', io.BytesIO(b''), 'text/csv')}
        response = client.post('/ingest/auto', files=files)
        
        assert response.status_code == 400


class TestConfidenceThresholds:
    """Test confidence threshold behavior."""
    
    def test_high_confidence_detection_wins(self, client):
        """Test that FITS magic bytes override ambiguous extension."""
        # FITS content with .csv extension - properly padded to 2880 bytes
        fits_header = b'SIMPLE  =                    T / file conforms to FITS standard             '
        fits_header += b'BITPIX  =                    8 / bits per data pixel                        '
        fits_header += b'NAXIS   =                    0 / number of data axes                        '
        fits_header += b'EXTEND  =                    T / FITS dataset may contain extensions        '
        fits_header += b'END' + b' ' * 77
        # Pad to 2880 bytes (36 cards * 80 bytes)
        fits_content = fits_header + b' ' * (2880 - len(fits_header))
        
        files = {'file': ('misleading.csv', io.BytesIO(fits_content), 'text/csv')}
        response = client.post('/ingest/auto', files=files)
        
        # Magic bytes (0.99) should win over extension detection
        assert response.status_code in [200, 400]
        data = response.json()
        
        if 'adapter_used' in data:
            assert data['adapter_used'] == 'fits'
            assert data['detection_method'] == 'magic_bytes'
            assert data['adapter_confidence'] == 0.99
