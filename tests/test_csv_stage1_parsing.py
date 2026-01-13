"""
Stage 1 Test: CSV Parser Core Functionality

Tests:
1. Parse basic CSV file
2. Auto-detect delimiter (comma, tab, semicolon)
3. Column detection
4. Handle comments and empty lines
"""

import pytest
from pathlib import Path
from io import StringIO

from app.services.adapters.csv_adapter import CSVAdapter


def test_01_parse_basic_csv():
    """Test basic CSV parsing with standard columns."""
    csv_data = """ra,dec,mag,parallax
10.5,20.3,12.5,5.2
45.8,-30.1,14.2,3.1
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    assert len(records) == 2
    assert records[0]['ra'] == '10.5'
    assert records[0]['dec'] == '20.3'
    assert records[1]['ra'] == '45.8'


def test_02_auto_detect_delimiter():
    """Test auto-detection of different delimiters."""
    # Tab-delimited
    tsv_data = "ra\tdec\tmag\n10.5\t20.3\t12.5\n"
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(tsv_data))
    assert len(records) == 1
    assert adapter.detected_delimiter == '\t'
    
    # Semicolon-delimited
    csv_data = "ra;dec;mag\n10.5;20.3;12.5\n"
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    assert len(records) == 1
    assert adapter.detected_delimiter == ';'


def test_03_column_detection():
    """Test detection of various column name formats."""
    csv_data = """RIGHT_ASCENSION,DECLINATION,Magnitude,Parallax
10.5,20.3,12.5,5.2
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    # Validate to trigger column detection
    result = adapter.validate(records[0])
    
    assert result.is_valid
    assert adapter.detected_columns['ra'] == 'RIGHT_ASCENSION'
    assert adapter.detected_columns['dec'] == 'DECLINATION'


def test_04_skip_comments_empty_lines():
    """Test handling of comments and empty lines."""
    csv_data = """# This is a comment
ra,dec,mag

# Another comment
10.5,20.3,12.5

45.8,-30.1,14.2
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    assert len(records) == 2  # Only data rows


def test_05_custom_column_mapping():
    """Test custom column mapping for non-standard names."""
    csv_data = """my_ra,my_dec,my_mag
10.5,20.3,12.5
"""
    
    adapter = CSVAdapter(
        column_mapping={
            "ra": "my_ra",
            "dec": "my_dec",
            "magnitude": "my_mag"
        }
    )
    records = adapter.parse(StringIO(csv_data))
    result = adapter.validate(records[0])
    
    assert result.is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
