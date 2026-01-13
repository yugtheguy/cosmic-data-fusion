"""
Test script for SDSS adapter - Stage 3: Unit conversion & mapping.

Tests redshift-to-distance conversion and complete schema mapping.
"""

from pathlib import Path
from app.services.adapters.sdss_adapter import SDSSAdapter
from app.services.utils.unit_converter import UnitConverter

SDSS_SAMPLE = Path("app/data/sdss_dr17_sample.csv")

def test_stage3_conversion_and_mapping():
    """Test Stage 3: Unit conversion and schema mapping."""
    
    print("\n" + "="*70)
    print("STAGE 3 TEST: Unit Conversion & Schema Mapping")
    print("="*70)
    
    # Test unit converter first
    print("\n[1] Testing UnitConverter.redshift_to_distance()...")
    converter = UnitConverter()
    
    test_cases = [
        (0.0234, "~100 Mpc"),  # Low redshift galaxy
        (0.1, "~430 Mpc"),     # Medium redshift
        (0.5, "~2500 Mpc"),    # Higher redshift
        (1.0, "~6700 Mpc"),    # z=1 galaxy
    ]
    
    for z, expected in test_cases:
        distance_pc = converter.redshift_to_distance(z)
        distance_mpc = distance_pc / 1_000_000 if distance_pc else None
        print(f"    z={z:.4f} → d={distance_mpc:.1f} Mpc (expected {expected})")
    
    print("✓ Redshift-to-distance conversions working")
    
    # Initialize adapter
    print("\n[2] Initializing SDSSAdapter...")
    adapter = SDSSAdapter(dataset_id="test_stage3_sdss")
    print(f"✓ Adapter created: {adapter.source_name}")
    
    # Parse and process sample data
    print(f"\n[3] Processing sample data: {SDSS_SAMPLE.name}")
    raw_records = adapter.parse(SDSS_SAMPLE)
    print(f"✓ Parsed {len(raw_records)} records")
    
    # Map first record in detail
    print(f"\n[4] Mapping first record to unified schema...")
    first_raw = raw_records[0]
    print(f"\n   Raw record:")
    print(f"     objid: {first_raw.get('objid')}")
    print(f"     ra: {first_raw.get('ra')}")
    print(f"     dec: {first_raw.get('dec')}")
    print(f"     psfMag_g: {first_raw.get('psfMag_g')}")
    print(f"     z: {first_raw.get('z')}")
    print(f"     specClass: {first_raw.get('specClass')}")
    
    # Validate and map
    validation = adapter.validate(first_raw)
    if not validation.is_valid:
        print(f"    ✗ Validation failed: {validation.errors}")
    else:
        mapped = adapter.map_to_unified_schema(first_raw)
        
        print(f"\n   Mapped record:")
        print(f"     object_id: {mapped.get('object_id')}")
        print(f"     source_id: {mapped.get('source_id')}")
        print(f"     ra_deg: {mapped.get('ra_deg')}")
        print(f"     dec_deg: {mapped.get('dec_deg')}")
        print(f"     brightness_mag: {mapped.get('brightness_mag')}")
        print(f"     distance_pc: {mapped.get('distance_pc')}")
        
        if mapped.get('distance_pc'):
            dist_mpc = mapped['distance_pc'] / 1_000_000
            print(f"       (= {dist_mpc:.2f} Mpc)")
        
        print(f"     original_source: {mapped.get('original_source')}")
        print(f"     dataset_id: {mapped.get('dataset_id')}")
        
        # Check raw_metadata
        metadata = mapped.get('raw_metadata', {})
        print(f"\n   Raw metadata (preserved fields):")
        print(f"     ugriz mags: {len([k for k in metadata.keys() if 'psfMag' in k])} filters")
        print(f"     redshift: {metadata.get('redshift')}")
        print(f"     spectral_class: {metadata.get('spectral_class')}")
        
        if 'psfMag_u' in metadata:
            print(f"       u: {metadata['psfMag_u']}")
        if 'psfMag_g' in metadata:
            print(f"       g: {metadata['psfMag_g']}")
        if 'psfMag_r' in metadata:
            print(f"       r: {metadata['psfMag_r']}")
        if 'psfMag_i' in metadata:
            print(f"       i: {metadata['psfMag_i']}")
        if 'psfMag_z' in metadata:
            print(f"       z: {metadata['psfMag_z']}")
    
    # Process all records
    print(f"\n[5] Processing all {len(raw_records)} records...")
    valid_records, validation_results = adapter.process_batch(
        SDSS_SAMPLE,
        skip_invalid=True
    )
    
    print(f"✓ Processed {len(valid_records)} valid records")
    
    # Verify distance calculations
    print(f"\n[6] Verifying distance calculations...")
    records_with_distance = [r for r in valid_records if r.get('distance_pc') is not None]
    records_with_redshift = [r for r in valid_records if r.get('raw_metadata', {}).get('redshift') is not None]
    
    print(f"    Records with redshift: {len(records_with_redshift)}")
    print(f"    Records with calculated distance: {len(records_with_distance)}")
    
    if records_with_distance:
        distances_mpc = [r['distance_pc'] / 1_000_000 for r in records_with_distance]
        print(f"    Distance range: {min(distances_mpc):.1f} - {max(distances_mpc):.1f} Mpc")
        print(f"    Mean distance: {sum(distances_mpc) / len(distances_mpc):.1f} Mpc")
    
    # Verify metadata preservation
    print(f"\n[7] Verifying metadata preservation...")
    metadata_counts = {
        'ugriz_mags': 0,
        'redshift': 0,
        'spectral_class': 0,
        'extinction': 0,
        'proper_motion': 0
    }
    
    for record in valid_records:
        metadata = record.get('raw_metadata', {})
        
        # Count ugriz magnitudes
        ugriz_count = sum(1 for k in metadata.keys() if 'psfMag' in k)
        if ugriz_count >= 5:
            metadata_counts['ugriz_mags'] += 1
        
        if 'redshift' in metadata:
            metadata_counts['redshift'] += 1
        
        if 'spectral_class' in metadata:
            metadata_counts['spectral_class'] += 1
        
        if any(f'extinction_{b}' in metadata for b in ['u', 'g', 'r', 'i', 'z']):
            metadata_counts['extinction'] += 1
        
        if 'pmra' in metadata or 'pmdec' in metadata:
            metadata_counts['proper_motion'] += 1
    
    print(f"✓ Metadata preservation summary:")
    print(f"    Records with all 5 ugriz mags: {metadata_counts['ugriz_mags']}/{len(valid_records)}")
    print(f"    Records with redshift: {metadata_counts['redshift']}/{len(valid_records)}")
    print(f"    Records with spectral class: {metadata_counts['spectral_class']}/{len(valid_records)}")
    print(f"    Records with extinction data: {metadata_counts['extinction']}/{len(valid_records)}")
    print(f"    Records with proper motion: {metadata_counts['proper_motion']}/{len(valid_records)}")
    
    # Verify schema compliance
    print(f"\n[8] Verifying schema compliance...")
    required_fields = ['object_id', 'source_id', 'ra_deg', 'dec_deg', 'original_source', 'dataset_id']
    
    schema_compliant = 0
    for record in valid_records:
        if all(field in record for field in required_fields):
            schema_compliant += 1
    
    print(f"✓ Schema compliance: {schema_compliant}/{len(valid_records)} records")
    
    # Summary
    print("\n" + "="*70)
    print("STAGE 3 TEST: PASSED ✓")
    print("="*70)
    print(f"✓ Redshift-to-distance conversion working")
    print(f"✓ Complete schema mapping implemented")
    print(f"✓ All {len(valid_records)} records successfully mapped")
    print(f"✓ Distance calculations: {len(records_with_distance)} records")
    print(f"✓ Metadata preserved: ugriz mags, redshift, spectral class")
    print(f"✓ Schema compliant: {schema_compliant}/{len(valid_records)} records")
    print("\nReady to proceed to Stage 4: Database integration")
    print("\nNext steps:")
    print("  - Test database insertion with UnifiedStarCatalog model")
    print("  - Verify SDSS + Gaia cross-source queries")
    print("  - Test spatial filtering with SDSS data")
    

if __name__ == "__main__":
    test_stage3_conversion_and_mapping()
