"""
Data validation script for Time Machine feature.
Checks if proper motion columns exist and contain usable data.
"""

import sys
sys.path.insert(0, '.')

from app.database import get_db
from sqlalchemy import text
import json

def check_proper_motion_data():
    """Check database for proper motion columns and data coverage."""
    
    print("=" * 60)
    print("COSMIC Time Machine - Data Validation Report")
    print("=" * 60)
    print()
    
    db = next(get_db())
    
    try:
        # Check if table exists (SQLite compatible)
        result = db.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table'
        """))
        tables = [row[0] for row in result]
        print(f"✓ Found {len(tables)} tables in database")
        print(f"  Tables: {', '.join(tables)}")
        print()
        
        #Check for our main tables
        if 'unified_star_catalog' in tables or 'unified_observations' in tables:
            table_name = 'unified_star_catalog' if 'unified_star_catalog' in tables else 'unified_observations'
            
            # Get total count
            result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            total_count = result.scalar()
            print(f"✓ Table: {table_name}")
            print(f"  Total stars: {total_count:,}")
            print()
            
            if total_count > 0:
                # Sample some stars with metadata
                result = db.execute(text(f"""
                    SELECT id, ra_deg, dec_deg, brightness_mag, raw_metadata, original_source
                    FROM {table_name}
                    WHERE raw_metadata IS NOT NULL
                    LIMIT 100
                """))
                
                stars = list(result)
                print(f"Analyzing {len(stars)} stars with metadata...")
                print()
                
                if len(stars) == 0:
                    print("⚠ No stars with metadata found!")
                    print("  The database may need proper Gaia DR3 data with PM fields")
                    print()
                else:
                    # Parse metadata and count PM fields
                    with_pmra = 0
                    with_pmdec = 0
                    with_both = 0
                    sample_star = None
                    
                    for star in stars:
                        metadata_str = star[4]
                        if metadata_str:
                            try:
                                if isinstance(metadata_str, str):
                                    metadata = json.loads(metadata_str)
                                else:
                                    metadata = metadata_str
                                    
                                has_pmra = 'pmra' in metadata
                                has_pmdec = 'pmdec' in metadata
                                
                                if has_pmra:
                                    with_pmra += 1
                                if has_pmdec:
                                    with_pmdec += 1
                                if has_pmra and has_pmdec:
                                    with_both += 1
                                    if not sample_star:
                                        sample_star = (star, metadata)
                            except:
                                pass
                    
                    print("Proper Motion Data Coverage (sample of 100):")
                    print(f"  Stars with pmra: {with_pmra} ({with_pmra/len(stars)*100:.1f}%)")
                    print(f"  Stars with pmdec: {with_pmdec} ({with_pmdec/len(stars)*100:.1f}%)")
                    print(f"  Stars with BOTH: {with_both} ({with_both/len(stars)*100:.1f}%)")
                    print()
                    
                    # Show sample
                    if sample_star:
                        star, metadata = sample_star
                        print("Sample star with proper motion:")
                        print(f"  ID: {star[0]}")
                        print(f"  RA: {star[1]:.4f}°")
                        print(f"  Dec: {star[2]:.4f}°")
                        print(f"  Mag: {star[3]:.2f}")
                        print(f"  Source: {star[5]}")
                        print(f"  pmra: {metadata.get('pmra')} mas/yr")
                        print(f"  pmdec: {metadata.get('pmdec')} mas/yr")
                        if 'ref_epoch' in metadata:
                            print(f"  ref_epoch: {metadata.get('ref_epoch')}")
                        print()
                    
                    # Estimate total with PM
                    estimated_total_with_pm = int((with_both / len(stars)) * total_count)
                    print(f"Estimated total stars with PM data: ~{estimated_total_with_pm:,}")
                    print()
                    
                    # Verdict
                    print("=" * 60)
                    if with_both >0:
                        print("✓ VALIDATION PASSED")
                        print(f"  Database contains proper motion data!")
                        print(f"  Found {with_both}/{len(stars)} stars with pmra+pmdec in sample")
                        print("  Time Machine feature can proceed!")
                    else:
                        print("⚠ LIMITED DATA")
                        print("  Few or no stars with proper motion found in sample")
                        print("  May need to ingest more Gaia data with PM columns")
                    print("=" * 60)
                
        else:
            print("✗ Main table not found!")
            print("  Please run database migrations and ingest data first")
            
    except Exception as e:
        print(f"✗ Error during validation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_proper_motion_data()
