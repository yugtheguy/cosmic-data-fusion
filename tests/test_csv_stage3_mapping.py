"""
Stage 3 Test: CSV Schema Mapping

Tests transformation to unified schema:
1. Basic coordinate mapping
2. Magnitude mapping
3. Parallax to distance conversion
4. Metadata preservation
5. Dataset tracking
"""

import pytest
from io import StringIO
from datetime import datetime

from app.services.adapters.csv_adapter import CSVAdapter


def test_01_basic_coordinate_mapping():
    """Test basic RA/Dec mapping to unified schema."""
    csv_data = """ra,dec,mag
10.5,20.3,12.5
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    adapter.validate(records[0])  # Trigger column detection
    
    unified = adapter.map_to_unified_schema(records[0])
    
    assert unified['ra_deg'] == 10.5
    assert unified['dec_deg'] == 20.3
    assert unified['brightness_mag'] == 12.5
    assert unified['original_source'] == 'CSV Catalog'
    assert 'dataset_id' in unified
    assert 'observation_time' in unified


def test_02_parallax_to_distance():
    """Test parallax to distance conversion."""
    csv_data = """ra,dec,mag,parallax
10.5,20.3,12.5,5.0
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    adapter.validate(records[0])
    
    unified = adapter.map_to_unified_schema(records[0])
    
    assert unified['parallax_mas'] == 5.0
    assert 'distance_pc' in unified
    assert abs(unified['distance_pc'] - 200.0) < 0.1  # 1000/5 = 200 pc


def test_03_negative_parallax_no_distance():
    """Test that negative parallax does not produce distance."""
    csv_data = """ra,dec,mag,parallax
10.5,20.3,12.5,-1.0
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    adapter.validate(records[0])
    
    unified = adapter.map_to_unified_schema(records[0])
    
    assert unified['parallax_mas'] == -1.0
    assert 'distance_pc' not in unified  # Should not compute distance


def test_04_distance_column_direct():
    """Test direct distance column (when no parallax)."""
    csv_data = """ra,dec,mag,distance
10.5,20.3,12.5,150.0
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    adapter.validate(records[0])
    
    unified = adapter.map_to_unified_schema(records[0])
    
    assert unified['distance_pc'] == 150.0


def test_05_metadata_preservation():
    """Test that extra columns are preserved as metadata."""
    csv_data = """ra,dec,mag,pmra,pmdec,spectral_type,catalog_id
10.5,20.3,12.5,10.2,-5.3,G2V,HD12345
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    adapter.validate(records[0])
    
    unified = adapter.map_to_unified_schema(records[0])
    
    assert 'raw_metadata' in unified
    assert unified['raw_metadata']['pmra'] == '10.2'
    assert unified['raw_metadata']['pmdec'] == '-5.3'
    assert unified['raw_metadata']['spectral_type'] == 'G2V'
    # catalog_id is detected as source_id variant, so it's mapped directly
    assert unified['source_id'] == 'HD12345'


def test_06_source_id_mapping():
    """Test source ID detection and mapping."""
    csv_data = """ra,dec,mag,source_id
10.5,20.3,12.5,ABC123
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    adapter.validate(records[0])
    
    unified = adapter.map_to_unified_schema(records[0])
    
    assert unified['source_id'] == 'ABC123'


def test_07_case_insensitive_columns():
    """Test case-insensitive column name mapping."""
    csv_data = """RA,DEC,MAG,PARALLAX
10.5,20.3,12.5,8.0
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    adapter.validate(records[0])
    
    unified = adapter.map_to_unified_schema(records[0])
    
    assert unified['ra_deg'] == 10.5
    assert unified['dec_deg'] == 20.3
    assert unified['brightness_mag'] == 12.5
    assert unified['parallax_mas'] == 8.0


def test_08_custom_column_mapping():
    """Test custom column name mapping."""
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
    adapter.validate(records[0])
    
    unified = adapter.map_to_unified_schema(records[0])
    
    assert unified['ra_deg'] == 10.5
    assert unified['dec_deg'] == 20.3
    assert unified['brightness_mag'] == 12.5


def test_09_missing_optional_fields():
    """Test handling of missing optional fields."""
    csv_data = """ra,dec
10.5,20.3
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    adapter.validate(records[0])
    
    unified = adapter.map_to_unified_schema(records[0])
    
    assert unified['ra_deg'] == 10.5
    assert unified['dec_deg'] == 20.3
    # brightness_mag has default value since it's required by DB
    assert unified['brightness_mag'] == 12.0
    assert 'parallax_mas' not in unified
    assert 'distance_pc' not in unified


def test_10_dataset_id_consistency():
    """Test that dataset_id is consistent across records."""
    csv_data = """ra,dec,mag
10.5,20.3,12.5
45.8,-30.1,14.2
"""
    
    adapter = CSVAdapter()
    records = adapter.parse(StringIO(csv_data))
    
    # Validate and map both records
    adapter.validate(records[0])
    unified1 = adapter.map_to_unified_schema(records[0])
    
    adapter.validate(records[1])
    unified2 = adapter.map_to_unified_schema(records[1])
    
    # Same adapter should use same dataset_id
    assert unified1['dataset_id'] == unified2['dataset_id']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
