"""
Test FITS adapter - Stage 4: Database Integration

Tests complete end-to-end workflow:
- Parse FITS files
- Validate records
- Map to unified schema
- Insert into database
- Query and retrieve
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, init_db
from app.models import UnifiedStarCatalog
from app.services.adapters.fits_adapter import FITSAdapter
from sqlalchemy import and_


def setup_test_database():
    """Initialize clean test database."""
    print("  Setting up test database...")
    
    # Force drop and recreate tables
    from app.database import Base, engine
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    db = SessionLocal()
    
    # Clear existing data (for test isolation)
    db.query(UnifiedStarCatalog).delete()
    db.commit()
    
    return db


def test_stage4_hipparcos_database_integration():
    """Test: Ingest Hipparcos data into database."""
    print("\n" + "="*60)
    print("STAGE 4 TEST: Hipparcos Database Integration")
    print("="*60)
    
    db = setup_test_database()
    
    try:
        # Initialize adapter and process
        adapter = FITSAdapter(dataset_id="hipparcos_db_test")
        fits_path = Path("app/data/hipparcos_sample.fits")
        
        print(f"  Processing: {fits_path}")
        valid_records, validation_results = adapter.process_batch(
            input_data=fits_path,
            skip_invalid=True
        )
        
        print(f"  ✓ Processed {len(valid_records)} valid records")
        
        # Insert into database
        print(f"  Inserting into database...")
        db_records = []
        for record in valid_records:
            db_record = UnifiedStarCatalog(**record)
            db_records.append(db_record)
        
        db.bulk_save_objects(db_records)
        db.commit()
        
        print(f"  ✓ Inserted {len(db_records)} records into database")
        
        # Verify records exist
        count = db.query(UnifiedStarCatalog).filter(
            UnifiedStarCatalog.dataset_id == "hipparcos_db_test"
        ).count()
        
        assert count == len(db_records), f"Expected {len(db_records)}, found {count}"
        print(f"  ✓ Verified {count} records in database")
        
        # Test spatial query (cone search)
        # Get center of first record
        first = db.query(UnifiedStarCatalog).filter(
            UnifiedStarCatalog.dataset_id == "hipparcos_db_test"
        ).first()
        
        ra_center = first.ra_deg
        dec_center = first.dec_deg
        radius = 5.0  # 5 degree radius
        
        nearby_stars = db.query(UnifiedStarCatalog).filter(
            and_(
                UnifiedStarCatalog.dataset_id == "hipparcos_db_test",
                UnifiedStarCatalog.ra_deg.between(ra_center - radius, ra_center + radius),
                UnifiedStarCatalog.dec_deg.between(dec_center - radius, dec_center + radius)
            )
        ).all()
        
        print(f"  ✓ Spatial query: Found {len(nearby_stars)} stars within {radius}° of RA={ra_center:.2f}, Dec={dec_center:.2f}")
        
        # Verify metadata
        sample = db.query(UnifiedStarCatalog).filter(
            UnifiedStarCatalog.dataset_id == "hipparcos_db_test"
        ).first()
        
        print(f"\n  ✓ Sample record from database:")
        print(f"    - object_id: {sample.object_id}")
        print(f"    - RA: {sample.ra_deg:.4f}°")
        print(f"    - Dec: {sample.dec_deg:.4f}°")
        print(f"    - Magnitude: {sample.brightness_mag:.2f}")
        print(f"    - Parallax: {sample.parallax_mas:.2f} mas")
        print(f"    - Distance: {sample.distance_pc:.2f} pc")
        
        print("\n✅ STAGE 4 (Hipparcos Integration): PASSED")
        
    finally:
        db.close()


def test_stage4_multi_catalog_integration():
    """Test: Ingest multiple catalogs and query across them."""
    print("\n" + "="*60)
    print("STAGE 4 TEST: Multi-Catalog Integration")
    print("="*60)
    
    db = setup_test_database()
    
    try:
        catalogs = [
            ("hipparcos", Path("app/data/hipparcos_sample.fits")),
            ("2mass", Path("app/data/2mass_sample.fits")),
        ]
        
        total_ingested = 0
        dataset_ids = []
        
        for catalog_name, fits_path in catalogs:
            print(f"\n  Processing {catalog_name}...")
            
            adapter = FITSAdapter(dataset_id=f"{catalog_name}_multi_test")
            dataset_ids.append(adapter.dataset_id)
            
            valid_records, _ = adapter.process_batch(
                input_data=fits_path,
                skip_invalid=True
            )
            
            # Insert
            db_records = [UnifiedStarCatalog(**r) for r in valid_records]
            db.bulk_save_objects(db_records)
            db.commit()
            
            print(f"    ✓ Ingested {len(db_records)} records from {catalog_name}")
            total_ingested += len(db_records)
        
        # Query combined dataset
        total_in_db = db.query(UnifiedStarCatalog).count()
        print(f"\n  ✓ Total in database: {total_in_db} records from {len(dataset_ids)} catalogs")
        
        # Verify by dataset
        for dataset_id in dataset_ids:
            count = db.query(UnifiedStarCatalog).filter(
                UnifiedStarCatalog.dataset_id == dataset_id
            ).count()
            print(f"    - {dataset_id}: {count} records")
        
        assert total_in_db == total_ingested, f"Count mismatch: {total_in_db} vs {total_ingested}"
        
        print("\n✅ STAGE 4 (Multi-Catalog): PASSED")
        
    finally:
        db.close()


def test_stage4_query_by_magnitude():
    """Test: Query database by magnitude range."""
    print("\n" + "="*60)
    print("STAGE 4 TEST: Magnitude Range Query")
    print("="*60)
    
    db = setup_test_database()
    
    try:
        # Ingest Hipparcos
        adapter = FITSAdapter(dataset_id="mag_query_test")
        fits_path = Path("app/data/hipparcos_sample.fits")
        
        valid_records, _ = adapter.process_batch(
            input_data=fits_path,
            skip_invalid=True
        )
        
        db_records = [UnifiedStarCatalog(**r) for r in valid_records]
        db.bulk_save_objects(db_records)
        db.commit()
        
        # Get min/max magnitudes
        min_mag = min(r['brightness_mag'] for r in valid_records if r['brightness_mag'])
        max_mag = max(r['brightness_mag'] for r in valid_records if r['brightness_mag'])
        
        print(f"  Magnitude range in database: {min_mag:.2f} to {max_mag:.2f}")
        
        # Query mid-range
        mid_range_stars = db.query(UnifiedStarCatalog).filter(
            and_(
                UnifiedStarCatalog.dataset_id == "mag_query_test",
                UnifiedStarCatalog.brightness_mag.between(min_mag + 1, max_mag - 1)
            )
        ).all()
        
        print(f"  ✓ Found {len(mid_range_stars)} stars in mid-magnitude range")
        
        # Query bright stars
        bright_stars = db.query(UnifiedStarCatalog).filter(
            and_(
                UnifiedStarCatalog.dataset_id == "mag_query_test",
                UnifiedStarCatalog.brightness_mag <= 8.0
            )
        ).all()
        
        print(f"  ✓ Found {len(bright_stars)} bright stars (mag ≤ 8.0)")
        
        print("\n✅ STAGE 4 (Magnitude Query): PASSED")
        
    finally:
        db.close()


def test_stage4_parallax_distance_queries():
    """Test: Query by distance/parallax."""
    print("\n" + "="*60)
    print("STAGE 4 TEST: Distance/Parallax Queries")
    print("="*60)
    
    db = setup_test_database()
    
    try:
        # Ingest Hipparcos
        adapter = FITSAdapter(dataset_id="dist_query_test")
        fits_path = Path("app/data/hipparcos_sample.fits")
        
        valid_records, _ = adapter.process_batch(
            input_data=fits_path,
            skip_invalid=True
        )
        
        db_records = [UnifiedStarCatalog(**r) for r in valid_records]
        db.bulk_save_objects(db_records)
        db.commit()
        
        # Query nearby stars (< 100 pc)
        nearby = db.query(UnifiedStarCatalog).filter(
            and_(
                UnifiedStarCatalog.dataset_id == "dist_query_test",
                UnifiedStarCatalog.distance_pc.isnot(None),
                UnifiedStarCatalog.distance_pc < 100.0
            )
        ).all()
        
        print(f"  ✓ Found {len(nearby)} nearby stars (distance < 100 pc)")
        
        # Query by parallax
        high_parallax = db.query(UnifiedStarCatalog).filter(
            and_(
                UnifiedStarCatalog.dataset_id == "dist_query_test",
                UnifiedStarCatalog.parallax_mas.isnot(None),
                UnifiedStarCatalog.parallax_mas > 10.0
            )
        ).all()
        
        print(f"  ✓ Found {len(high_parallax)} high parallax stars (parallax > 10 mas)")
        
        if high_parallax:
            sample = high_parallax[0]
            print(f"    Sample: parallax={sample.parallax_mas:.2f} mas, distance={sample.distance_pc:.2f} pc")
        
        print("\n✅ STAGE 4 (Distance Queries): PASSED")
        
    finally:
        db.close()


if __name__ == '__main__':
    try:
        test_stage4_hipparcos_database_integration()
        test_stage4_multi_catalog_integration()
        test_stage4_query_by_magnitude()
        test_stage4_parallax_distance_queries()
        
        print("\n" + "="*60)
        print("🎉 ALL STAGE 4 TESTS PASSED!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
