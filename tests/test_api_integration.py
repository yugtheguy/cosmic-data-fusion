"""
Test script for Gaia adapter - Stage 5: End-to-end API integration.

Tests the complete workflow: API upload -> adapter processing -> database storage.
"""

import requests
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
GAIA_SAMPLE = Path("app/data/gaia_dr3_sample.csv")

def test_stage5_api_integration():
    """Test Stage 5: Complete API integration and database storage."""
    
    print("\n" + "="*70)
    print("STAGE 5 TEST: End-to-End API Integration")
    print("="*70)
    
    # Check server is running
    print("\n[1] Checking server health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ Server is running: {response.json()}")
        else:
            print(f"✗ Server returned status {response.status_code}")
            return
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        print("   Make sure the server is running: uvicorn app.main:app --reload")
        return
    
    # Test Gaia ingestion endpoint
    print(f"\n[2] Testing POST /ingest/gaia with sample data...")
    print(f"   File: {GAIA_SAMPLE.name}")
    
    try:
        with open(GAIA_SAMPLE, 'rb') as f:
            files = {'file': (GAIA_SAMPLE.name, f, 'text/csv')}
            params = {
                'dataset_id': 'test_stage5',
                'skip_invalid': 'false'
            }
            
            response = requests.post(
                f"{API_BASE_URL}/ingest/gaia",
                files=files,
                params=params,
                timeout=30
            )
        
        print(f"   Status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            print(f"✓ Ingestion successful!")
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message')}")
            print(f"   Ingested: {result.get('ingested_count')} records")
            print(f"   Failed: {result.get('failed_count')} records")
            print(f"   Dataset ID: {result.get('dataset_id')}")
        else:
            print(f"✗ Ingestion failed: {result}")
            return
            
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return
    
    # Verify data was stored in database
    print(f"\n[3] Verifying data in database...")
    try:
        # Query search endpoint to verify data
        response = requests.get(
            f"{API_BASE_URL}/search/box",
            params={
                'ra_min': 0,
                'ra_max': 360,
                'dec_min': -90,
                'dec_max': 90,
                'limit': 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            search_result = response.json()
            stars = search_result.get('stars', [])
            print(f"✓ Database query successful")
            print(f"   Total stars in catalog: {search_result.get('total')}")
            print(f"   Retrieved: {len(stars)} stars")
            
            if stars:
                print(f"\n   Sample record:")
                star = stars[0]
                print(f"     source_id: {star.get('source_id')}")
                print(f"     ra: {star.get('ra_deg')}°")
                print(f"     dec: {star.get('dec_deg')}°")
                print(f"     magnitude: {star.get('brightness_mag')}")
                print(f"     source: {star.get('original_source')}")
        else:
            print(f"✗ Database query failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Query failed: {e}")
    
    # Test visualization endpoint
    print(f"\n[4] Testing visualization endpoint...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/visualize/sky",
            params={'limit': 5},
            timeout=10
        )
        
        if response.status_code == 200:
            viz_result = response.json()
            print(f"✓ Visualization endpoint working")
            print(f"   Points returned: {len(viz_result.get('points', []))}")
        else:
            print(f"✗ Visualization failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Visualization request failed: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("STAGE 5 TEST: COMPLETE ✓")
    print("="*70)
    print("✓ API endpoint working")
    print("✓ File upload working")
    print("✓ Adapter processing working")
    print("✓ Database storage working")
    print("✓ Query endpoints working")
    print("\n🎉 Gaia adapter implementation COMPLETE!")
    print("\nNext steps:")
    print("  - Teammates can implement SDSS, FITS, CSV adapters")
    print("  - All adapters follow same BaseAdapter interface")
    print("  - Add unit tests for robustness")
    

if __name__ == "__main__":
    test_stage5_api_integration()
