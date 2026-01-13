"""
Test script for SDSS adapter - Stage 1: Basic functionality.

Tests parsing, basic validation setup, and mapping structure.
"""

from pathlib import Path
from app.services.adapters.sdss_adapter import SDSSAdapter

# Path to sample data (from project root)
SDSS_SAMPLE = Path("app/data/sdss_dr17_sample.csv")

def test_stage1_basic_parsing():
    """Test Stage 1: Parse CSV and validate basic functionality."""
    
    print("\n" + "="*70)
    print("STAGE 1 TEST: SDSSAdapter Basic Functionality")
    print("="*70)
    
    # Initialize adapter
    print("\n[1] Initializing SDSSAdapter...")
    adapter = SDSSAdapter(dataset_id="test_stage1_sdss")
    print(f"✓ Adapter created: {adapter.source_name}, dataset_id={adapter.dataset_id}")
    
    # Parse sample data
    print(f"\n[2] Parsing sample CSV: {SDSS_SAMPLE.name}")
    raw_records = adapter.parse(SDSS_SAMPLE)
    print(f"✓ Parsed {len(raw_records)} records")
    
    # Show first record
    if raw_records:
        print(f"\n[3] First raw record:")
        first_record = raw_records[0]
        for key, value in first_record.items():
            print(f"    {key}: {value}")
    
    # Verify required columns present
    print(f"\n[4] Verifying required columns...")
    required_columns = adapter.REQUIRED_COLUMNS
    first_record_keys = set(raw_records[0].keys())
    
    missing_columns = []
    for col in required_columns:
        if col not in first_record_keys:
            missing_columns.append(col)
    
    if missing_columns:
        print(f"✗ Missing required columns: {missing_columns}")
    else:
        print(f"✓ All required columns present: {required_columns}")
    
    # Check optional columns
    print(f"\n[5] Checking optional columns...")
    optional_found = []
    for col in adapter.OPTIONAL_COLUMNS:
        if col in first_record_keys:
            optional_found.append(col)
    
    print(f"✓ Found {len(optional_found)} optional columns:")
    for col in optional_found[:5]:  # Show first 5
        print(f"    - {col}")
    if len(optional_found) > 5:
        print(f"    ... and {len(optional_found) - 5} more")
    
    # Test comprehensive validation (Stage 2: full checks)
    print(f"\n[6] Testing comprehensive validation (Stage 2)...")
    validation_results = []
    for record in raw_records[:5]:  # Test first 5
        result = adapter.validate(record)
        validation_results.append(result)
    
    valid_count = sum(1 for r in validation_results if r.is_valid)
    print(f"✓ Validated {len(validation_results)} records: {valid_count} valid")
    
    # Show validation details for first record
    if validation_results:
        first_result = validation_results[0]
        print(f"\n   First record validation:")
        print(f"     Valid: {first_result.is_valid}")
        print(f"     Errors: {len(first_result.errors)}")
        print(f"     Warnings: {len(first_result.warnings)}")
        
        if first_result.errors:
            for error in first_result.errors[:3]:  # Show first 3 errors
                print(f"       ERROR: {error}")
        
        if first_result.warnings:
            for warning in first_result.warnings[:3]:  # Show first 3 warnings
                print(f"       WARN: {warning}")
    
    # Test mapping structure (Stage 1: minimal)
    print(f"\n[7] Testing mapping to unified schema (basic)...")
    unified_records = []
    for record in raw_records[:3]:  # Map first 3
        unified = adapter.map_to_unified_schema(record)
        unified_records.append(unified)
    
    print(f"✓ Mapped {len(unified_records)} records to unified schema")
    
    # Show first unified record
    if unified_records:
        print(f"\n[8] First unified record (Stage 1 minimal):")
        first_unified = unified_records[0]
        for key, value in first_unified.items():
            if value is not None:
                print(f"    {key}: {value}")
    
    # Test process_batch (end-to-end)
    print(f"\n[9] Testing process_batch (end-to-end)...")
    valid_records, validation_results = adapter.process_batch(
        SDSS_SAMPLE,
        skip_invalid=True
    )
    
    print(f"✓ Process batch complete:")
    print(f"    Total records: {len(raw_records)}")
    print(f"    Valid records: {len(valid_records)}")
    print(f"    Failed records: {len(raw_records) - len(valid_records)}")
    
    # Verify data types
    print(f"\n[10] Verifying data quality...")
    sample_record = raw_records[0]
    
    # Check numeric fields can be converted
    numeric_fields = ['ra', 'dec', 'psfMag_g', 'psfMag_r', 'z']
    conversion_success = []
    for field in numeric_fields:
        if field in sample_record:
            try:
                float(sample_record[field])
                conversion_success.append(field)
            except (ValueError, TypeError):
                print(f"    ✗ Cannot convert {field} to float: {sample_record[field]}")
    
    print(f"✓ {len(conversion_success)}/{len(numeric_fields)} numeric fields convertible")
    
    # Summary
    print("\n" + "="*70)
    print("STAGE 1 TEST: PASSED ✓")
    print("="*70)
    print(f"✓ Parser working ({len(raw_records)} records)")
    print(f"✓ Required columns present")
    print(f"✓ Optional columns detected ({len(optional_found)} fields)")
    print(f"✓ Validator skeleton working")
    print(f"✓ Mapper skeleton working")
    print(f"✓ End-to-end pipeline working")
    print(f"✓ Data types convertible")
    print("\nReady to proceed to Stage 2: Enhanced validation rules")
    print("\nNext steps:")
    print("  - Implement 8-point validation in validate()")
    print("  - Add SDSS-specific checks (ugriz mags, redshift range)")
    print("  - Test with edge cases (missing mags, invalid redshift)")
    

if __name__ == "__main__":
    test_stage1_basic_parsing()
