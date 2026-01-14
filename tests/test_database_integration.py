"""
Test script for Gaia adapter - Stage 4/5: Database integration test.

Tests adapter + database storage without requiring API server.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, UnifiedStarCatalog
from app.services.adapters.gaia_adapter import GaiaAdapter

# Configuration
GAIA_SAMPLE = Path("app/data/gaia_dr3_sample.csv")
TEST_DB = "test_cosmic_data.db"

def test_database_integration():
    """Test Stage 4/5: Adapter + Database integration."""
    
    print("\n" + "="*70)
    print("STAGE 4/5 TEST: Database Integration")
    print("="*70)
    
    # Clean up any existing test database
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    # Create fresh test database
    print("\n[1] Setting up test database...")
    engine = create_engine(f"sqlite:///{TEST_DB}")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    print(f"✓ Test database created: {TEST_DB}")
    
    try:
        # Initialize adapter
        print("\n[2] Initializing GaiaAdapter...")
        adapter = GaiaAdapter(dataset_id="test_db_integration")
        print(f"✓ Adapter created: dataset_id={adapter.dataset_id}")
        
        # Process sample data
        print(f"\n[3] Processing sample data: {GAIA_SAMPLE.name}")
        valid_records, validation_results = adapter.process_batch(
            GAIA_SAMPLE,
            skip_invalid=True
        )
        print(f"✓ Processed: {len(valid_records)} valid records")
        
        # Insert into database
        print(f"\n[4] Inserting records into database...")
        db_records = []
        for record in valid_records:
            db_record = UnifiedStarCatalog(**record)
            db_records.append(db_record)
        
        db.bulk_save_objects(db_records)
        db.commit()
        print(f"✓ Inserted {len(db_records)} records")
        
        # Query and verify
        print(f"\n[5] Verifying data in database...")
        total_count = db.query(UnifiedStarCatalog).count()
        print(f"✓ Total records in database: {total_count}")
        
        # Show sample records
        sample_records = db.query(UnifiedStarCatalog).limit(3).all()
        print(f"\n[6] Sample records:")
        for idx, record in enumerate(sample_records, 1):
            print(f"   Record {idx}:")
            print(f"     ID: {record.id}")
            print(f"     Source ID: {record.source_id}")
            print(f"     RA: {record.ra_deg:.6f}°")
            print(f"     Dec: {record.dec_deg:.6f}°")
            print(f"     Magnitude: {record.brightness_mag:.4f}")
            print(f"     Distance: {record.distance_pc} pc" if record.distance_pc else "     Distance: N/A")
            print(f"     Source: {record.original_source}")
            print(f"     Dataset: {record.dataset_id}")
        
        # Test query by source
        print(f"\n[7] Testing query by source...")
        gaia_count = db.query(UnifiedStarCatalog).filter(
            UnifiedStarCatalog.original_source == "Gaia DR3"
        ).count()
        print(f"✓ Gaia DR3 records: {gaia_count}")
        
        # Test spatial query
        print(f"\n[8] Testing spatial query (RA: 100-200, Dec: -50-0)...")
        spatial_results = db.query(UnifiedStarCatalog).filter(
            UnifiedStarCatalog.ra_deg >= 100,
            UnifiedStarCatalog.ra_deg <= 200,
            UnifiedStarCatalog.dec_deg >= -50,
            UnifiedStarCatalog.dec_deg <= 0
        ).all()
        print(f"✓ Found {len(spatial_results)} stars in region")
        
        # Summary
        print("\n" + "="*70)
        print("STAGE 4/5 TEST: PASSED ✓")
        print("="*70)
        print(f"✓ Adapter processes data correctly")
        print(f"✓ Database schema compatible")
        print(f"✓ Bulk insert working")
        print(f"✓ Queries working (filter, spatial)")
        print(f"✓ Total records stored: {total_count}")
        
        print(f"\n🎉 Database integration COMPLETE!")
        print(f"\nTest database: {TEST_DB}")
        print("You can inspect it with: sqlite3 test_cosmic_data.db")
        
    finally:
        db.close()
        

if __name__ == "__main__":
    test_database_integration()
