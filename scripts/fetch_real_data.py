#!/usr/bin/env python3
"""
Fetch Real Astronomical Data for COSMIC Data Fusion

This script populates the local database with REAL scientific data from
two major astronomical archives to demonstrate multi-source data fusion.

Target: The Pleiades Cluster (Messier 45)
        - One of the nearest and most recognizable open star clusters
        - Contains ~1,000 confirmed members
        - Distance: ~136 parsecs (444 light-years)

Data Sources:
    1. Gaia DR3 (ESA) - European Space Agency's astrometric mission
    2. TESS Input Catalog (NASA/MAST) - NASA's planet-hunting mission catalog

Usage:
    python scripts/fetch_real_data.py

Requirements:
    pip install astroquery

Author: COSMIC Data Fusion Team
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from typing import List, Optional

# Astronomy libraries
from astroquery.gaia import Gaia
from astroquery.mast import Catalogs
from astropy.coordinates import SkyCoord
from astropy import units as u
import numpy as np

# Database imports
from app.database import SessionLocal, init_db
from app.models import UnifiedStarCatalog

# Try to import tqdm for progress bars, fall back to simple print
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    def tqdm(iterable, desc="", total=None):
        """Fallback progress indicator."""
        items = list(iterable)
        total = total or len(items)
        for i, item in enumerate(items):
            if i % 50 == 0 or i == total - 1:
                print(f"  {desc}: {i+1}/{total}")
            yield item


# ============================================================
# CONFIGURATION
# ============================================================

# Pleiades Cluster (Messier 45) coordinates
PLEIADES_RA = 56.75       # degrees
PLEIADES_DEC = 24.1167    # degrees
SEARCH_RADIUS = 1.0       # degrees

# Query limits
MAX_GAIA_STARS = 500
MAX_TESS_STARS = 500


# ============================================================
# PART A: FETCH FROM GAIA DR3 (ESA)
# ============================================================

def fetch_gaia_data() -> List[dict]:
    """
    Fetch star data from ESA's Gaia DR3 archive.
    
    Gaia is the European Space Agency's mission to chart a 3D map of our Galaxy.
    DR3 (Data Release 3) contains positions, distances, and motions for ~1.8 billion stars.
    
    Returns:
        List of dictionaries with star data ready for database insertion
    """
    print("\n" + "="*60)
    print("📡 PART A: Fetching from ESA Gaia DR3")
    print("="*60)
    print(f"   Target: Pleiades Cluster (M45)")
    print(f"   Center: RA={PLEIADES_RA}°, Dec={PLEIADES_DEC}°")
    print(f"   Radius: {SEARCH_RADIUS}°")
    print(f"   Limit:  {MAX_GAIA_STARS} brightest stars")
    print("-"*60)
    
    # ADQL query for Gaia archive
    # CONTAINS() with POINT and CIRCLE performs cone search
    # We filter for non-null parallax (critical for distance calculations and AI stability)
    adql_query = f"""
    SELECT TOP {MAX_GAIA_STARS}
        source_id,
        ra,
        dec,
        phot_g_mean_mag,
        parallax,
        pmra,
        pmdec,
        bp_rp
    FROM gaiadr3.gaia_source
    WHERE 1=CONTAINS(
        POINT('ICRS', ra, dec),
        CIRCLE('ICRS', {PLEIADES_RA}, {PLEIADES_DEC}, {SEARCH_RADIUS})
    )
    AND parallax IS NOT NULL
    AND phot_g_mean_mag IS NOT NULL
    ORDER BY phot_g_mean_mag ASC
    """
    
    print("   Executing ADQL query...")
    
    try:
        # Launch async job on Gaia archive
        job = Gaia.launch_job(adql_query, verbose=False)
        result_table = job.get_results()
        
        print(f"   ✅ Received {len(result_table)} stars from Gaia DR3")
        
    except Exception as e:
        print(f"   ❌ Gaia query failed: {e}")
        return []
    
    # Convert to list of dictionaries
    stars = []
    
    print("   Processing Gaia records...")
    for row in tqdm(result_table, desc="Gaia", total=len(result_table)):
        try:
            # Calculate distance from parallax (distance_pc = 1000 / parallax_mas)
            parallax = float(row['parallax'])
            distance_pc = 1000.0 / parallax if parallax > 0 else None
            
            star_data = {
                'source_id': str(row['source_id']),
                'ra_deg': float(row['ra']),
                'dec_deg': float(row['dec']),
                'brightness_mag': float(row['phot_g_mean_mag']),
                'parallax_mas': parallax,
                'distance_pc': distance_pc,
                'original_source': 'Gaia DR3',
                'raw_frame': 'ICRS',
                'raw_metadata': {
                    'pmra': float(row['pmra']) if row['pmra'] else None,
                    'pmdec': float(row['pmdec']) if row['pmdec'] else None,
                    'bp_rp': float(row['bp_rp']) if row['bp_rp'] else None,
                    'catalog': 'gaiadr3.gaia_source',
                }
            }
            stars.append(star_data)
            
        except (ValueError, TypeError) as e:
            # Skip rows with conversion errors
            continue
    
    print(f"   ✅ Processed {len(stars)} valid Gaia records")
    return stars


# ============================================================
# PART B: FETCH FROM TESS INPUT CATALOG (NASA/MAST)
# ============================================================

def fetch_tess_data() -> List[dict]:
    """
    Fetch star data from NASA's TESS Input Catalog (TIC).
    
    TESS (Transiting Exoplanet Survey Satellite) is NASA's mission to discover
    exoplanets around nearby bright stars. The TIC contains ~1.7 billion objects.
    
    Returns:
        List of dictionaries with star data ready for database insertion
    """
    print("\n" + "="*60)
    print("🚀 PART B: Fetching from NASA TESS Input Catalog")
    print("="*60)
    print(f"   Target: Pleiades Cluster (M45)")
    print(f"   Center: RA={PLEIADES_RA}°, Dec={PLEIADES_DEC}°")
    print(f"   Radius: {SEARCH_RADIUS}°")
    print(f"   Limit:  {MAX_TESS_STARS} stars")
    print("-"*60)
    
    # Create coordinate object for query
    coords = SkyCoord(
        ra=PLEIADES_RA * u.degree,
        dec=PLEIADES_DEC * u.degree,
        frame='icrs'
    )
    
    print("   Querying MAST archive...")
    
    try:
        # Query TIC via MAST
        result_table = Catalogs.query_region(
            coords,
            radius=SEARCH_RADIUS * u.degree,
            catalog="TIC"
        )
        
        # Limit results
        if len(result_table) > MAX_TESS_STARS:
            # Sort by TESS magnitude and take brightest
            result_table.sort('Tmag')
            result_table = result_table[:MAX_TESS_STARS]
        
        print(f"   ✅ Received {len(result_table)} stars from TIC")
        
    except Exception as e:
        print(f"   ❌ TESS query failed: {e}")
        return []
    
    # Convert to list of dictionaries
    stars = []
    skipped_no_mag = 0
    skipped_no_parallax = 0
    
    print("   Processing TESS records...")
    for row in tqdm(result_table, desc="TESS", total=len(result_table)):
        try:
            # Get TESS magnitude (Tmag)
            tmag = row['Tmag']
            
            # Check if magnitude is valid (not masked/null)
            if tmag is None or (hasattr(tmag, 'mask') and tmag.mask):
                skipped_no_mag += 1
                continue
            
            tmag = float(tmag)
            if np.isnan(tmag):
                skipped_no_mag += 1
                continue
            
            # Get coordinates
            ra = float(row['ra'])
            dec = float(row['dec'])
            
            # Get parallax (may be null in TIC)
            parallax = row['plx']
            if parallax is None or (hasattr(parallax, 'mask') and parallax.mask):
                parallax_mas = None
                distance_pc = None
            else:
                parallax_mas = float(parallax)
                if np.isnan(parallax_mas) or parallax_mas <= 0:
                    parallax_mas = None
                    distance_pc = None
                else:
                    distance_pc = 1000.0 / parallax_mas
            
            # Get TIC ID
            tic_id = str(row['ID'])
            
            star_data = {
                'source_id': f"TIC {tic_id}",
                'ra_deg': ra,
                'dec_deg': dec,
                'brightness_mag': tmag,
                'parallax_mas': parallax_mas,
                'distance_pc': distance_pc,
                'original_source': 'NASA TESS',
                'raw_frame': 'ICRS',
                'raw_metadata': {
                    'tic_id': tic_id,
                    'Tmag': tmag,
                    'Vmag': float(row['Vmag']) if row['Vmag'] and not (hasattr(row['Vmag'], 'mask') and row['Vmag'].mask) else None,
                    'Jmag': float(row['Jmag']) if row['Jmag'] and not (hasattr(row['Jmag'], 'mask') and row['Jmag'].mask) else None,
                    'catalog': 'TESS Input Catalog',
                }
            }
            stars.append(star_data)
            
        except (ValueError, TypeError, KeyError) as e:
            # Skip rows with conversion errors
            continue
    
    print(f"   ✅ Processed {len(stars)} valid TESS records")
    if skipped_no_mag > 0:
        print(f"   ⚠️  Skipped {skipped_no_mag} records (missing magnitude)")
    
    return stars


# ============================================================
# PART C: DATABASE INSERTION
# ============================================================

def insert_into_database(gaia_stars: List[dict], tess_stars: List[dict]) -> dict:
    """
    Insert fetched star data into the local SQLite database.
    
    Args:
        gaia_stars: List of star dictionaries from Gaia DR3
        tess_stars: List of star dictionaries from TESS TIC
        
    Returns:
        Statistics dictionary with insertion counts
    """
    print("\n" + "="*60)
    print("💾 PART C: Database Insertion")
    print("="*60)
    
    # Initialize database tables if they don't exist
    print("   Initializing database tables...")
    init_db()
    
    db = SessionLocal()
    stats = {
        'gaia_inserted': 0,
        'tess_inserted': 0,
        'errors': 0,
    }
    
    try:
        # Check for existing data
        existing_count = db.query(UnifiedStarCatalog).count()
        print(f"   Existing records in database: {existing_count}")
        
        # Prepare Gaia star objects
        print(f"\n   Preparing {len(gaia_stars)} Gaia DR3 records...")
        gaia_objects = []
        for star_data in gaia_stars:
            try:
                obj = UnifiedStarCatalog(
                    source_id=star_data['source_id'],
                    ra_deg=star_data['ra_deg'],
                    dec_deg=star_data['dec_deg'],
                    brightness_mag=star_data['brightness_mag'],
                    parallax_mas=star_data['parallax_mas'],
                    distance_pc=star_data['distance_pc'],
                    original_source=star_data['original_source'],
                    raw_frame=star_data['raw_frame'],
                    raw_metadata=star_data['raw_metadata'],
                    created_at=datetime.now(timezone.utc)
                )
                gaia_objects.append(obj)
            except Exception as e:
                stats['errors'] += 1
        
        # Prepare TESS star objects
        print(f"   Preparing {len(tess_stars)} NASA TESS records...")
        tess_objects = []
        for star_data in tess_stars:
            try:
                obj = UnifiedStarCatalog(
                    source_id=star_data['source_id'],
                    ra_deg=star_data['ra_deg'],
                    dec_deg=star_data['dec_deg'],
                    brightness_mag=star_data['brightness_mag'],
                    parallax_mas=star_data['parallax_mas'],
                    distance_pc=star_data['distance_pc'],
                    original_source=star_data['original_source'],
                    raw_frame=star_data['raw_frame'],
                    raw_metadata=star_data['raw_metadata'],
                    created_at=datetime.now(timezone.utc)
                )
                tess_objects.append(obj)
            except Exception as e:
                stats['errors'] += 1
        
        # Bulk insert
        print(f"\n   Inserting {len(gaia_objects)} Gaia records...")
        db.bulk_save_objects(gaia_objects)
        stats['gaia_inserted'] = len(gaia_objects)
        
        print(f"   Inserting {len(tess_objects)} TESS records...")
        db.bulk_save_objects(tess_objects)
        stats['tess_inserted'] = len(tess_objects)
        
        # Commit transaction
        db.commit()
        
        # Verify insertion
        final_count = db.query(UnifiedStarCatalog).count()
        print(f"\n   ✅ Database now contains {final_count} records")
        
    except Exception as e:
        print(f"\n   ❌ Database error: {e}")
        db.rollback()
        raise
        
    finally:
        db.close()
    
    return stats


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    """Main entry point for the data fetching script."""
    
    print("\n" + "="*60)
    print("🌌 COSMIC Data Fusion — Real Data Fetcher")
    print("="*60)
    print(f"   Target: Pleiades Cluster (Messier 45)")
    print(f"   Center: RA {PLEIADES_RA}°, Dec {PLEIADES_DEC}°")
    print(f"   Radius: {SEARCH_RADIUS}°")
    print("="*60)
    
    # Part A: Fetch Gaia data
    gaia_stars = fetch_gaia_data()
    
    # Part B: Fetch TESS data
    tess_stars = fetch_tess_data()
    
    # Part C: Insert into database
    if gaia_stars or tess_stars:
        stats = insert_into_database(gaia_stars, tess_stars)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        print(f"   Gaia DR3 stars inserted:  {stats['gaia_inserted']}")
        print(f"   NASA TESS stars inserted: {stats['tess_inserted']}")
        print(f"   Total new records:        {stats['gaia_inserted'] + stats['tess_inserted']}")
        if stats['errors'] > 0:
            print(f"   Errors:                   {stats['errors']}")
        print("="*60)
        
        print("\n🎉 Data fusion ready! You now have REAL astronomical data")
        print("   from TWO major space agencies (ESA & NASA).")
        print("\n💡 Next steps:")
        print("   1. Start the API:  uvicorn app.main:app --reload --port 8000")
        print("   2. Run cross-match: POST /harmonize/cross-match")
        print("   3. Detect anomalies: POST /ai/anomalies")
        print("   4. View in browser: http://localhost:8000/docs")
        
    else:
        print("\n❌ No data fetched. Check your internet connection.")
        sys.exit(1)


if __name__ == "__main__":
    main()
