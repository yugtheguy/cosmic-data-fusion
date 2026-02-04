#!/usr/bin/env python3
"""
Fetch Extended Astronomical Data (SDSS, 2MASS, Tycho-2)
for COSMIC Data Fusion

This script fetches data from additional catalogs to ensure all UI filters
are functional with real data.

Data Sources:
    1. SDSS DR16 (Optical) - Deep sky survey
    2. 2MASS (Infrared) - Infrared all-sky survey
    3. Tycho-2 (Optical) - Brightest 2.5 million stars

Target: Pleiades Cluster (M45)
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from typing import List

# Astronomy libraries
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u
import numpy as np

# Database imports
from app.database import SessionLocal, init_db
from app.models import UnifiedStarCatalog

# Configuration
PLEIADES_RA = 56.75       # degrees
PLEIADES_DEC = 24.1167    # degrees
SEARCH_RADIUS = 0.5       # degrees (smaller radius for denser catalogs like SDSS)
LIMIT_PER_CATALOG = 300   # Limit to keep database size manageable

def fetch_vizier_catalog(catalog_id: str, name: str, mag_col: str, ra_col: str, dec_col: str) -> List[dict]:
    print(f"\n📡 Fetching from {name} ({catalog_id})...")
    
    cutoff_mag = 18 if "SDSS" in name else 14
    
    try:
        Vizier.ROW_LIMIT = LIMIT_PER_CATALOG
        coord = SkyCoord(ra=PLEIADES_RA, dec=PLEIADES_DEC, unit=(u.deg, u.deg), frame='icrs')
        
        # Query
        result = Vizier.query_region(coord, radius=SEARCH_RADIUS*u.deg, catalog=catalog_id)
        
        if not result:
            print(f"   ⚠️  No results found for {name}")
            return []
            
        table = result[0]
        print(f"   ✅ Received {len(table)} records")
        print(f"   Columns: {table.colnames}") # Debugging
        
        stars = []
        for i, row in enumerate(table):
            # Extract basic data
            ra = float(row[ra_col])
            dec = float(row[dec_col])
            mag = float(row[mag_col]) 
            
            star_data = {
                'source_id': f"{name}_{i}", 
                'ra_deg': ra,
                'dec_deg': dec,
                'brightness_mag': mag,
                'original_source': name,
                'raw_frame': 'ICRS',
                'raw_metadata': {
                    'catalog': catalog_id,
                    'filter': mag_col
                }
            }
            
            # Try to find a real source ID if possible
            if 'Source' in table.colnames:
                 star_data['source_id'] = str(row['Source'])
            elif 'objID' in table.colnames: # SDSS
                 star_data['source_id'] = str(row['objID'])
            elif '2MASS' in table.colnames: # 2MASS designation
                 star_data['source_id'] = f"2MASS J{str(row['2MASS'])}"
            elif 'TYC1' in table.colnames and 'TYC2' in table.colnames: # Tycho-2
                 star_data['source_id'] = f"TYC {row['TYC1']}-{row['TYC2']}-{row['TYC3']}"
            
            stars.append(star_data)
                
        return stars
        
    except Exception as e:
        print(f"   ❌ Query failed: {e}")
        return []

def insert_data(all_stars: List[dict]):
    print("\n💾 Inserting into database...")
    init_db()
    db = SessionLocal()
    
    count = 0
    errors = 0
    
    for star_data in all_stars:
        try:
            # Check if exists (simple check by source_id to avoid dupes)
            exists = db.query(UnifiedStarCatalog).filter_by(source_id=star_data['source_id']).first()
            if exists:
                continue
                
            obj = UnifiedStarCatalog(
                source_id=star_data['source_id'],
                ra_deg=star_data['ra_deg'],
                dec_deg=star_data['dec_deg'],
                brightness_mag=star_data['brightness_mag'],
                parallax_mas=None, # Vizier simple queries might not have this easily mapped
                distance_pc=None,
                original_source=star_data['original_source'],
                raw_frame=star_data['raw_frame'],
                raw_metadata=star_data['raw_metadata'],
                created_at=datetime.now(timezone.utc)
            )
            db.add(obj)
            count += 1
            
            if count % 100 == 0:
                db.commit()
                
        except Exception:
            errors += 1
            db.rollback()
            
    db.commit()
    print(f"   ✅ Successfully inserted {count} new records")
    if errors > 0:
        print(f"   ⚠️  Skipped {errors} invalid/duplicate records")
    db.close()

def main():
    print("="*60)
    print("🌌 COSMIC | Extended Catalog Fetcher")
    print("="*60)
    
    all_new_stars = []
    
    # 1. SDSS - Skipping for now as it returns no results in this region
    # sdss = fetch_vizier_catalog("V/154/sdss16", "SDSS", "gmag", "RA_ICRS", "DE_ICRS")
    # all_new_stars.extend(sdss)
    
    # 2. 2MASS (II/246/out)
    # Colnames: 'RAJ2000', 'DEJ2000', '2MASS', 'Jmag'
    tmass = fetch_vizier_catalog("II/246/out", "2MASS", "Jmag", "RAJ2000", "DEJ2000")
    all_new_stars.extend(tmass)
    
    # 3. Tycho-2 (I/259/tyc2)
    # Colnames: 'RA(ICRS)', 'DE(ICRS)', 'VTmag'
    tycho = fetch_vizier_catalog("I/259/tyc2", "Tycho-2", "VTmag", "RA(ICRS)", "DE(ICRS)")
    all_new_stars.extend(tycho)
    
    if all_new_stars:
        insert_data(all_new_stars)
        print("\n🎉 Done! Refresh your dashboard to see the new data.")
    else:
        print("\n❌ No data fetched.")

if __name__ == "__main__":
    main()
