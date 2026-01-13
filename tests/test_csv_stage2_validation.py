"""
Stage 2 Test: CSV Validation Framework

Tests 8-point validation:
1. Required fields present (RA, Dec)
2. Coordinate ranges (RA: 0-360°, Dec: -90-90°)
3. Coordinate type validation
4. Magnitude reasonableness
5. Distance/Parallax validity
6. Metadata integrity
7. No NaN/Inf values
8. Missing value handling
"""

import pytest
from io import StringIO

from app.services.adapters.csv_adapter import CSVAdapter


def test_01_valid_record():
    """Test validation of a completely valid record."""
    csv_data = """ra,dec,mag,parallax
10.5,20.3,12.5,5.2
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    result = adapter.validate(records[0])
    
    assert result.is_valid
    assert len(result.errors) == 0


def test_02_missing_ra_column():
    """Test validation fails when RA column is missing."""
    csv_data = """dec,mag
20.3,12.5
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    result = adapter.validate(records[0])
    
    assert not result.is_valid
    assert any("No RA column found" in err for err in result.errors)


def test_03_missing_dec_column():
    """Test validation fails when Dec column is missing."""
    csv_data = """ra,mag
10.5,12.5
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    result = adapter.validate(records[0])
    
    assert not result.is_valid
    assert any("No Dec column found" in err for err in result.errors)


def test_04_ra_out_of_range():
    """Test validation fails for out-of-range RA."""
    csv_data = """ra,dec,mag
370.0,20.3,12.5
-10.0,20.3,12.5
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    # First record: RA > 360
    result1 = adapter.validate(records[0])
    assert not result1.is_valid
    assert any("RA out of range" in err for err in result1.errors)
    
    # Second record: RA < 0
    result2 = adapter.validate(records[1])
    assert not result2.is_valid
    assert any("RA out of range" in err for err in result2.errors)


def test_05_dec_out_of_range():
    """Test validation fails for out-of-range Dec."""
    csv_data = """ra,dec,mag
10.5,95.0,12.5
10.5,-95.0,12.5
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    # First record: Dec > 90
    result1 = adapter.validate(records[0])
    assert not result1.is_valid
    assert any("Dec out of range" in err for err in result1.errors)
    
    # Second record: Dec < -90
    result2 = adapter.validate(records[1])
    assert not result2.is_valid
    assert any("Dec out of range" in err for err in result2.errors)


def test_06_invalid_coordinate_types():
    """Test validation fails for non-numeric coordinates."""
    csv_data = """ra,dec,mag
abc,20.3,12.5
10.5,xyz,12.5
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    # First record: invalid RA
    result1 = adapter.validate(records[0])
    assert not result1.is_valid
    assert any("Invalid coordinate" in err for err in result1.errors)
    
    # Second record: invalid Dec
    result2 = adapter.validate(records[1])
    assert not result2.is_valid
    assert any("Invalid coordinate" in err for err in result2.errors)


def test_07_magnitude_warnings():
    """Test warnings for unusual magnitude values."""
    csv_data = """ra,dec,mag
10.5,20.3,0.0
10.5,20.3,-10.0
10.5,20.3,35.0
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    # Zero magnitude
    result1 = adapter.validate(records[0])
    assert result1.is_valid  # Valid but warning
    assert any("0.0" in warn for warn in result1.warnings)
    
    # Out of typical range (low)
    result2 = adapter.validate(records[1])
    assert result2.is_valid
    assert any("typical range" in warn for warn in result2.warnings)
    
    # Out of typical range (high)
    result3 = adapter.validate(records[2])
    assert result3.is_valid
    assert any("typical range" in warn for warn in result3.warnings)


def test_08_parallax_warnings():
    """Test warnings for unusual parallax values."""
    csv_data = """ra,dec,mag,parallax
10.5,20.3,12.5,-1.0
10.5,20.3,12.5,1500.0
10.5,20.3,12.5,0.05
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    # Negative parallax
    result1 = adapter.validate(records[0])
    assert result1.is_valid
    assert any("Non-positive parallax" in warn for warn in result1.warnings)
    
    # Very large parallax
    result2 = adapter.validate(records[1])
    assert result2.is_valid
    assert any("Very large parallax" in warn for warn in result2.warnings)
    
    # Very small parallax
    result3 = adapter.validate(records[2])
    assert result3.is_valid
    assert any("Very small parallax" in warn for warn in result3.warnings)


def test_09_null_empty_coordinates():
    """Test validation fails for null/empty coordinates."""
    csv_data = """ra,dec,mag
,20.3,12.5
10.5,,12.5
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    # Null RA
    result1 = adapter.validate(records[0])
    assert not result1.is_valid
    assert any("null or empty" in err for err in result1.errors)
    
    # Null Dec
    result2 = adapter.validate(records[1])
    assert not result2.is_valid
    assert any("null or empty" in err for err in result2.errors)


def test_10_near_pole_warning():
    """Test warning for near-pole objects."""
    csv_data = """ra,dec,mag
10.5,87.5,12.5
10.5,-88.0,12.5
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    # North pole
    result1 = adapter.validate(records[0])
    assert result1.is_valid
    assert any("Near-pole" in warn for warn in result1.warnings)
    
    # South pole
    result2 = adapter.validate(records[1])
    assert result2.is_valid
    assert any("Near-pole" in warn for warn in result2.warnings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
