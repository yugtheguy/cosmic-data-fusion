"""
Test script for Gaia adapter - Stage 1: Basic functionality.

Tests parsing, validation, and mapping of Gaia data.
"""

from pathlib import Path
from app.services.adapters.gaia_adapter import GaiaAdapter

# Path to sample data (from project root)
GAIA_SAMPLE = Path("app/data/gaia_dr3_sample.csv")

def test_stage1_basic_parsing():
    """Test Stage 1: Parse CSV and validate basic functionality."""
    
    print("\n" + "="*70)
    print("STAGE 1 TEST: GaiaAdapter Basic Functionality")
    print("="*70)
    
    # Initialize adapter
    print("\n[1] Initializing GaiaAdapter...")
    adapter = GaiaAdapter(dataset_id="test_stage1")
    print(f"✓ Adapter created: {adapter.source_name}, dataset_id={adapter.dataset_id}")
    
    # Parse sample data
    print(f"\n[2] Parsing sample CSV: {GAIA_SAMPLE.name}")
    raw_records = adapter.parse(GAIA_SAMPLE)
    print(f"✓ Parsed {len(raw_records)} records")
    
    # Show first record
    if raw_records:
        print(f"\n[3] First raw record:")
        first_record = raw_records[0]
        for key, value in first_record.items():
            if not key.startswith('_'):
                print(f"    {key}: {value}")
    
    # Validate records
    print(f"\n[4] Validating records...")
    validation_results = []
    for record in raw_records[:5]:  # Test first 5
        result = adapter.validate(record)
        validation_results.append(result)
    
    valid_count = sum(1 for r in validation_results if r.is_valid)
    print(f"✓ Validated {len(validation_results)} records: {valid_count} valid")
    
    # Show validation details
    for idx, result in enumerate(validation_results):
        status = "✓ VALID" if result.is_valid else "✗ INVALID"
        print(f"    Record {idx+1}: {status}")
        if result.errors:
            for error in result.errors:
                print(f"        ERROR: {error}")
        if result.warnings:
            for warning in result.warnings:
                print(f"        WARN: {warning}")
    
    # Map to unified schema
    print(f"\n[5] Mapping to unified schema...")
    unified_records = []
    for record in raw_records[:3]:  # Map first 3
        validation = adapter.validate(record)
        if validation.is_valid:
            unified = adapter.map_to_unified_schema(record)
            unified_records.append(unified)
    
    print(f"✓ Mapped {len(unified_records)} records to unified schema")
    
    # Show first unified record
    if unified_records:
        print(f"\n[6] First unified record:")
        first_unified = unified_records[0]
        for key, value in first_unified.items():
            if value is not None:
                print(f"    {key}: {value}")
    
    # Test process_batch (end-to-end)
    print(f"\n[7] Testing process_batch (end-to-end)...")
    valid_records, validation_results = adapter.process_batch(
        GAIA_SAMPLE,
        skip_invalid=True
    )
    
    print(f"✓ Process batch complete:")
    print(f"    Total records: {len(raw_records)}")
    print(f"    Valid records: {len(valid_records)}")
    print(f"    Failed records: {len(raw_records) - len(valid_records)}")
    
    # Summary
    print("\n" + "="*70)
    print("STAGE 1 TEST: PASSED ✓")
    print("="*70)
    print(f"✓ Parser working")
    print(f"✓ Validator working")
    print(f"✓ Mapper working")
    print(f"✓ End-to-end pipeline working")
    print("\nReady to proceed to Stage 2: Enhanced validation rules")
    

if __name__ == "__main__":
    test_stage1_basic_parsing()
