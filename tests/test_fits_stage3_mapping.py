"""
Test FITS adapter - Stage 3: Schema Mapping & Unit Conversion

Tests the map_to_unified_schema() method to ensure:
- Records are correctly mapped to UnifiedStarCatalog schema
- Unit conversions work properly
- Object IDs are generated correctly
- Metadata is preserved
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.adapters.fits_adapter import FITSAdapter


def test_stage3_hipparcos_mapping():
    """Test: Map Hipparcos records to unified schema."""
    print("\n" + "="*60)
    print("STAGE 3 TEST: Hipparcos Schema Mapping")
    print("="*60)
    
    adapter = FITSAdapter(dataset_id="hipparcos_test")
    
    # Parse and process
    fits_path = Path("app/data/hipparcos_sample.fits")
    records = adapter.parse(fits_path)
    
    print(f"  Mapping {len(records)} records...")
    
    mapped_count = 0
    for record in records:
        # Validate first
        result = adapter.validate(record)
        if not result.is_valid:
            continue
        
        # Map to unified schema
        unified_record = adapter.map_to_unified_schema(record)
        
        if mapped_count == 0:
            # Print first record as example
            print(f"\n  ✓ Sample mapped record:")
            print(f"    - object_id: {unified_record['object_id']}")
            print(f"    - source_id: {unified_record['source_id']}")
            print(f"    - ra_deg: {unified_record['ra_deg']}")
            print(f"    - dec_deg: {unified_record['dec_deg']}")
            print(f"    - brightness_mag: {unified_record['brightness_mag']}")
            print(f"    - parallax_mas: {unified_record['parallax_mas']}")
            print(f"    - distance_pc: {unified_record['distance_pc']}")
            print(f"    - original_source: {unified_record['original_source']}")
            print(f"    - dataset_id: {unified_record['dataset_id']}")
        
        # Verify required fields
        assert unified_record['object_id'] is not None, "object_id is None"
        assert unified_record['source_id'] is not None, "source_id is None"
        assert 0 <= unified_record['ra_deg'] < 360, f"RA out of range: {unified_record['ra_deg']}"
        assert -90 <= unified_record['dec_deg'] <= 90, f"Dec out of range: {unified_record['dec_deg']}"
        
        # Verify unit conversion
        if unified_record['parallax_mas'] is not None and unified_record['parallax_mas'] > 0:
            assert unified_record['distance_pc'] is not None, "Distance not calculated from parallax"
            # Verify inverse relationship: distance = 1000 / parallax
            expected_distance = 1000.0 / unified_record['parallax_mas']
            assert abs(unified_record['distance_pc'] - expected_distance) < 0.01, \
                f"Distance calculation error: expected {expected_distance}, got {unified_record['distance_pc']}"
        
        mapped_count += 1
    
    print(f"\n  ✓ Successfully mapped {mapped_count} records")
    assert mapped_count == len(records), f"Failed to map all records: {mapped_count}/{len(records)}"
    
    print("\n✅ STAGE 3 (Hipparcos Mapping): PASSED")


def test_stage3_parallax_distance_conversion():
    """Test: Parallax to distance conversion accuracy."""
    print("\n" + "="*60)
    print("STAGE 3 TEST: Parallax to Distance Conversion")
    print("="*60)
    
    adapter = FITSAdapter(dataset_id="conversion_test")
    
    # Parse Hipparcos
    fits_path = Path("app/data/hipparcos_sample.fits")
    records = adapter.parse(fits_path)
    
    print(f"  Testing parallax conversions...")
    
    conversion_tests = []
    
    for record in records[:5]:  # Test first 5
        result = adapter.validate(record)
        if not result.is_valid:
            continue
        
        unified_record = adapter.map_to_unified_schema(record)
        
        if unified_record['parallax_mas'] and unified_record['parallax_mas'] > 0:
            parallax = unified_record['parallax_mas']
            distance = unified_record['distance_pc']
            
            # Verify: distance (pc) = 1000 / parallax (mas)
            expected = 1000.0 / parallax
            
            conversion_tests.append({
                'parallax': parallax,
                'expected_distance': expected,
                'calculated_distance': distance,
                'error': abs(distance - expected)
            })
            
            print(f"    Parallax {parallax:.2f} mas → Distance {distance:.2f} pc (expected {expected:.2f})")
    
    # Verify all conversions are within tolerance
    for test in conversion_tests:
        assert test['error'] < 0.01, \
            f"Conversion error > 0.01: {test['error']}"
    
    print(f"\n  ✓ All {len(conversion_tests)} conversions accurate (error < 0.01 pc)")
    
    print("\n✅ STAGE 3 (Parallax Conversion): PASSED")


def test_stage3_2mass_mapping():
    """Test: Map 2MASS records (no parallax)."""
    print("\n" + "="*60)
    print("STAGE 3 TEST: 2MASS Schema Mapping (No Parallax)")
    print("="*60)
    
    adapter = FITSAdapter(dataset_id="2mass_test")
    
    # Parse and process
    fits_path = Path("app/data/2mass_sample.fits")
    records = adapter.parse(fits_path)
    
    print(f"  Mapping {len(records)} 2MASS records...")
    
    mapped_count = 0
    for record in records:
        result = adapter.validate(record)
        if not result.is_valid:
            continue
        
        unified_record = adapter.map_to_unified_schema(record)
        
        if mapped_count == 0:
            # Print first record
            print(f"\n  ✓ Sample 2MASS mapped record:")
            print(f"    - source_id: {unified_record['source_id']}")
            print(f"    - brightness_mag: {unified_record['brightness_mag']}")
            print(f"    - parallax_mas: {unified_record['parallax_mas']}")
            print(f"    - distance_pc: {unified_record['distance_pc']}")
        
        # 2MASS shouldn't have parallax or distance
        assert unified_record['parallax_mas'] is None, "2MASS shouldn't have parallax"
        assert unified_record['distance_pc'] is None, "2MASS shouldn't have distance"
        
        # But should have magnitude and coordinates
        assert unified_record['brightness_mag'] is not None, "2MASS should have magnitude"
        assert unified_record['ra_deg'] is not None, "2MASS should have RA"
        assert unified_record['dec_deg'] is not None, "2MASS should have Dec"
        
        mapped_count += 1
    
    print(f"\n  ✓ Successfully mapped {mapped_count} records")
    
    print("\n✅ STAGE 3 (2MASS Mapping): PASSED")


def test_stage3_metadata_preservation():
    """Test: Raw metadata preservation."""
    print("\n" + "="*60)
    print("STAGE 3 TEST: Metadata Preservation")
    print("="*60)
    
    adapter = FITSAdapter(dataset_id="metadata_test")
    
    # Parse Hipparcos (has extra columns: pmRA, pmDE)
    fits_path = Path("app/data/hipparcos_sample.fits")
    records = adapter.parse(fits_path)
    
    print(f"  Checking metadata preservation...")
    
    for record in records[:1]:  # Check first record
        result = adapter.validate(record)
        if not result.is_valid:
            continue
        
        unified_record = adapter.map_to_unified_schema(record)
        
        # raw_metadata should contain non-standard fields
        metadata = unified_record.get('raw_metadata')
        
        if metadata:
            print(f"  ✓ Preserved metadata: {list(metadata.keys())}")
        else:
            print(f"  ✓ No extra metadata (all fields are standard)")
        
        # Should preserve proper motion if present
        if 'pmRA' in record or 'pmDE' in record:
            assert metadata is not None, "Proper motion not preserved in metadata"
        
        break
    
    print("\n✅ STAGE 3 (Metadata Preservation): PASSED")


def test_stage3_object_id_generation():
    """Test: Object ID generation."""
    print("\n" + "="*60)
    print("STAGE 3 TEST: Object ID Generation")
    print("="*60)
    
    adapter = FITSAdapter(dataset_id="objid_test")
    
    # Parse Hipparcos
    fits_path = Path("app/data/hipparcos_sample.fits")
    records = adapter.parse(fits_path)
    
    print(f"  Checking object ID generation...")
    
    object_ids = set()
    
    for record in records:
        result = adapter.validate(record)
        if not result.is_valid:
            continue
        
        unified_record = adapter.map_to_unified_schema(record)
        obj_id = unified_record['object_id']
        
        # Should contain dataset_id
        assert "objid_test" in obj_id, f"Dataset ID not in object_id: {obj_id}"
        
        # Should be unique
        object_ids.add(obj_id)
    
    print(f"  ✓ Generated {len(object_ids)} unique object IDs")
    print(f"  ✓ Sample ID: {next(iter(object_ids))}")
    
    # All should be unique
    assert len(object_ids) == len([r for r in records if adapter.validate(r).is_valid]), \
        "Not all object IDs are unique"
    
    print("\n✅ STAGE 3 (Object ID Generation): PASSED")


if __name__ == '__main__':
    try:
        test_stage3_hipparcos_mapping()
        test_stage3_parallax_distance_conversion()
        test_stage3_2mass_mapping()
        test_stage3_metadata_preservation()
        test_stage3_object_id_generation()
        
        print("\n" + "="*60)
        print("🎉 ALL STAGE 3 TESTS PASSED!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
