"""
Test FITS adapter - Stage 2: Validation

Tests the validate() method of FITSAdapter to ensure:
- 8-point validation framework works
- Detects coordinate column variants
- Validates coordinate ranges
- Handles edge cases properly
- Generates appropriate errors and warnings
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.adapters.fits_adapter import FITSAdapter


def test_stage2_hipparcos_validation():
    """Test: Validate Hipparcos records."""
    print("\n" + "="*60)
    print("STAGE 2 TEST: Hipparcos Validation")
    print("="*60)
    
    adapter = FITSAdapter(dataset_id="test_val_hipparcos")
    
    # Parse and validate
    fits_path = Path("app/data/hipparcos_sample.fits")
    records = adapter.parse(fits_path)
    
    print(f"  Validating {len(records)} records...")
    
    valid_count = 0
    error_count = 0
    warning_count = 0
    
    for record in records:
        result = adapter.validate(record)
        if result.is_valid:
            valid_count += 1
        else:
            error_count += 1
        warning_count += len(result.warnings)
    
    print(f"  ✓ Valid: {valid_count}/{len(records)}")
    print(f"  ✓ Errors: {error_count}")
    print(f"  ✓ Warnings: {warning_count}")
    
    # All Hipparcos records should be valid
    assert valid_count == len(records), f"Expected all records valid, got {valid_count}/{len(records)}"
    
    # Check detected columns
    print(f"  ✓ Detected RA column: {adapter.detected_columns.get('ra')}")
    print(f"  ✓ Detected Dec column: {adapter.detected_columns.get('dec')}")
    print(f"  ✓ Detected Mag column: {adapter.detected_columns.get('magnitude')}")
    
    assert 'ra' in adapter.detected_columns, "RA column not detected"
    assert 'dec' in adapter.detected_columns, "Dec column not detected"
    
    print("\n✅ STAGE 2 (Hipparcos Validation): PASSED")


def test_stage2_edge_cases_validation():
    """Test: Validate edge cases with errors and warnings."""
    print("\n" + "="*60)
    print("STAGE 2 TEST: Edge Cases Validation")
    print("="*60)
    
    adapter = FITSAdapter(dataset_id="test_val_edges")
    
    # Parse edge cases
    fits_path = Path("app/data/fits_edge_cases.fits")
    records = adapter.parse(fits_path)
    
    print(f"  Validating {len(records)} edge case records...")
    
    validation_results = []
    for i, record in enumerate(records):
        result = adapter.validate(record)
        validation_results.append(result)
        
        if not result.is_valid:
            print(f"    Record {i}: INVALID - {result.errors}")
        elif result.warnings:
            print(f"    Record {i}: Valid with warnings - {result.warnings}")
    
    valid_count = sum(1 for r in validation_results if r.is_valid)
    error_count = sum(len(r.errors) for r in validation_results)
    warning_count = sum(len(r.warnings) for r in validation_results)
    
    print(f"\n  ✓ Valid: {valid_count}/{len(records)}")
    print(f"  ✓ Total errors: {error_count}")
    print(f"  ✓ Total warnings: {warning_count}")
    
    # Edge cases should have some invalid records
    assert error_count > 0, "Expected to find validation errors in edge cases"
    print(f"  ✓ Validation framework correctly detected {error_count} errors")
    
    print("\n✅ STAGE 2 (Edge Cases Validation): PASSED")


def test_stage2_2mass_validation():
    """Test: Validate 2MASS records (no parallax)."""
    print("\n" + "="*60)
    print("STAGE 2 TEST: 2MASS Validation (No Parallax)")
    print("="*60)
    
    adapter = FITSAdapter(dataset_id="test_val_2mass")
    
    # Parse and validate
    fits_path = Path("app/data/2mass_sample.fits")
    records = adapter.parse(fits_path)
    
    print(f"  Validating {len(records)} 2MASS records...")
    
    valid_count = 0
    has_magnitude_warning = False
    
    for record in records:
        result = adapter.validate(record)
        if result.is_valid:
            valid_count += 1
        
        # 2MASS uses j_m, h_m, k_m - might not detect standard "mag" column
        if any('magnitude' in w.lower() or 'mag' in w.lower() for w in result.warnings):
            has_magnitude_warning = True
    
    print(f"  ✓ Valid: {valid_count}/{len(records)}")
    print(f"  ✓ Detected columns: {adapter.detected_columns}")
    
    # All 2MASS records should be valid (coordinates are good)
    assert valid_count == len(records), f"Expected all records valid, got {valid_count}/{len(records)}"
    
    print("\n✅ STAGE 2 (2MASS Validation): PASSED")


def test_stage2_coordinate_range_validation():
    """Test: Validate coordinate range checking."""
    print("\n" + "="*60)
    print("STAGE 2 TEST: Coordinate Range Validation")
    print("="*60)
    
    adapter = FITSAdapter(dataset_id="test_ranges")
    
    # Edge cases file has out-of-range coordinates
    fits_path = Path("app/data/fits_edge_cases.fits")
    records = adapter.parse(fits_path)
    
    # Find records with out-of-range coordinates
    out_of_range_count = 0
    
    for i, record in enumerate(records):
        result = adapter.validate(record)
        
        for error in result.errors:
            if 'out of range' in error.lower():
                print(f"    Record {i}: {error}")
                out_of_range_count += 1
                break
    
    print(f"\n  ✓ Found {out_of_range_count} records with out-of-range coordinates")
    
    # Edge cases file has records with RA=-10, RA=400, Dec=100, etc.
    assert out_of_range_count > 0, "Expected to find out-of-range coordinates"
    
    print("\n✅ STAGE 2 (Coordinate Range Validation): PASSED")


def test_stage2_column_detection():
    """Test: Column name variant detection."""
    print("\n" + "="*60)
    print("STAGE 2 TEST: Column Name Detection")
    print("="*60)
    
    # Test different column name variants
    test_cases = [
        ("Hipparcos", "app/data/hipparcos_sample.fits", "RAJ2000", "DEJ2000"),
        ("2MASS", "app/data/2mass_sample.fits", "ra", "dec"),
        ("Multi-Ext", "app/data/fits_multi_extension.fits", "RA_ICRS", "DEC_ICRS"),
    ]
    
    for name, path, expected_ra_variant, expected_dec_variant in test_cases:
        adapter = FITSAdapter(dataset_id=f"test_detect_{name.lower()}")
        
        if name == "Multi-Ext":
            records = adapter.parse(Path(path), extension=2)
        else:
            records = adapter.parse(Path(path))
        
        # Validate first record to trigger detection
        adapter.validate(records[0])
        
        detected_ra = adapter.detected_columns.get('ra')
        detected_dec = adapter.detected_columns.get('dec')
        
        print(f"  {name}: RA={detected_ra}, Dec={detected_dec}")
        
        assert detected_ra is not None, f"{name}: Failed to detect RA column"
        assert detected_dec is not None, f"{name}: Failed to detect Dec column"
    
    print(f"\n  ✓ All column variants successfully detected")
    
    print("\n✅ STAGE 2 (Column Detection): PASSED")


if __name__ == '__main__':
    try:
        test_stage2_hipparcos_validation()
        test_stage2_edge_cases_validation()
        test_stage2_2mass_validation()
        test_stage2_coordinate_range_validation()
        test_stage2_column_detection()
        
        print("\n" + "="*60)
        print("🎉 ALL STAGE 2 TESTS PASSED!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
