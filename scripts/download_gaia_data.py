"""
Download Gaia DR3 dataset for Time Machine visualization
Downloads a curated subset of stars with proper motion data
"""

import requests
import pandas as pd
from io import StringIO
import time

# Gaia Archive TAP service
GAIA_TAP_URL = "https://gea.esac.esa.int/tap-server/tap/sync"

# ADQL Query for bright nearby stars with good proper motion data
QUERY = """
SELECT TOP 100000
    source_id,
    ra,
    dec,
    parallax,
    parallax_error,
    pmra,
    pmdec,
    phot_g_mean_mag,
    bp_rp,
    radial_velocity,
    ruwe
FROM gaiadr3.gaia_source
WHERE parallax > 5
    AND parallax_error < 1
    AND phot_g_mean_mag < 13
    AND pmra IS NOT NULL
    AND pmdec IS NOT NULL
    AND ABS(pmra) + ABS(pmdec) > 0
ORDER BY phot_g_mean_mag ASC
"""

def download_gaia_data(output_file='gaia_stars.csv'):
    """
    Download Gaia DR3 data using TAP service
    """
    print("🌟 Downloading Gaia DR3 dataset...")
    print(f"Query: {QUERY.strip()[:100]}...")
    
    # Prepare request
    params = {
        'REQUEST': 'doQuery',
        'LANG': 'ADQL',
        'FORMAT': 'csv',
        'QUERY': QUERY
    }
    
    try:
        # Make request
        print("\n📡 Sending request to Gaia Archive...")
        response = requests.post(GAIA_TAP_URL, data=params, timeout=300)
        response.raise_for_status()
        
        # Parse CSV
        print("✅ Data received! Parsing...")
        df = pd.read_csv(StringIO(response.text))
        
        # Save to file
        df.to_csv(output_file, index=False)
        
        print(f"\n✨ Success! Downloaded {len(df)} stars")
        print(f"📁 Saved to: {output_file}")
        print(f"📊 File size: {len(response.text) / 1024 / 1024:.2f} MB")
        
        # Show sample
        print("\n📋 Sample data:")
        print(df.head())
        
        # Show statistics
        print("\n📈 Dataset statistics:")
        print(f"  - Stars: {len(df):,}")
        print(f"  - Magnitude range: {df['phot_g_mean_mag'].min():.2f} to {df['phot_g_mean_mag'].max():.2f}")
        print(f"  - Parallax range: {df['parallax'].min():.2f} to {df['parallax'].max():.2f} mas")
        print(f"  - Max proper motion: {df[['pmra', 'pmdec']].abs().max().max():.2f} mas/yr")
        
        return df
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out. The Gaia server might be busy.")
        print("💡 Try again later or use a smaller query (reduce TOP limit)")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading data: {e}")
        return None
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def download_alternative_hipparcos(output_file='hipparcos_stars.csv'):
    """
    Alternative: Download Hipparcos catalog (smaller, faster)
    """
    print("🌟 Downloading Hipparcos catalog as alternative...")
    
    # VizieR TAP service for Hipparcos
    VIZIER_URL = "https://vizier.cds.unistra.fr/viz-bin/votable"
    
    params = {
        '-source': 'I/239/hip_main',
        '-out': 'HIP,RAhms,DEdms,Plx,pmRA,pmDE,Vmag,B-V',
        '-out.max': '50000',
        'Vmag': '<8'
    }
    
    try:
        print("📡 Requesting Hipparcos data from VizieR...")
        response = requests.get(VIZIER_URL, params=params, timeout=120)
        response.raise_for_status()
        
        # Note: This returns VOTable format, would need astropy to parse
        print("✅ Hipparcos data received!")
        print("⚠️  Note: VOTable format - use astropy.io.votable to parse")
        
        with open('hipparcos_raw.xml', 'w') as f:
            f.write(response.text)
        
        print(f"📁 Saved raw data to: hipparcos_raw.xml")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("  GAIA DR3 DATA DOWNLOADER FOR TIME MACHINE")
    print("=" * 60)
    print()
    
    # Download Gaia data
    df = download_gaia_data('backend/data/gaia_stars.csv')
    
    if df is None:
        print("\n⚠️  Gaia download failed. Trying Hipparcos alternative...")
        download_alternative_hipparcos()
    
    print("\n" + "=" * 60)
    print("  DOWNLOAD COMPLETE!")
    print("=" * 60)
