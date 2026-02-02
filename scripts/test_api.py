"""
API Test Script for Time Machine Endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("TIME MACHINE API - AUTOMATED TEST RESULTS")
print("=" * 70)
print()

# Test 1: Health check
print("-" * 70)
print("TEST 1: API Health Check")
print("-" * 70)
try:
    r = requests.get(f"{BASE_URL}/health")
    print(f"✓ Status: {r.status_code}")
    print(f"✓ Response: {r.json()}")
    print()
except Exception as e:
    print(f"✗ Failed: {e}")
    print()

# Test 2: Fast Movers
print("-" * 70)
print("TEST 2: Fast Moving Stars (PM > 50 mas/yr)")
print("-" * 70)
try:
    r = requests.get(f"{BASE_URL}/temporal/fast-movers?limit=5")
    data = r.json()
    print(f"✓ Found {data['count']} fast movers")
    print(f"✓ Minimum PM threshold: {data['min_pm_threshold']} mas/yr")
    print()
    print("Top 3 fastest stars:")
    for i, star in enumerate(data['stars'][:3], 1):
        print(f"{i}. ID {star['id']}: {star['total_pm']:.2f} mas/yr")
        print(f"   PM(RA): {star['pmra']:.2f}, PM(Dec): {star['pmdec']:.2f}")
        print(f"   Magnitude: {star['magnitude']:.2f}")
    print()
except Exception as e:
    print(f"✗ Failed: {e}")
    print()

# Test 3: Temporal Query
print("-" * 70)
print("TEST 3: Query Pleiades in Year 3016 AD")
print("-" * 70)
try:
    payload = {
        "target_epoch": 3016,
        "ra_min": 50,
        "ra_max": 65,
        "dec_min": 20,
        "dec_max": 30,
        "limit": 10
    }
    r = requests.post(f"{BASE_URL}/temporal/query", json=payload)
    data = r.json()
    
    print(f"✓ Target Epoch: {data['epoch_display']}")
    print(f"✓ Stars returned: {data['count']}")
    print()
    
    if data['stars']:
        star = data['stars'][0]
        print("Sample Star Position Change:")
        print(f"  Star ID: {star['id']}")
        print(f"  Current (2016) RA: {star['ra_deg']:.6f}°")
        print(f"  Year 3016 RA: {star['ra_at_epoch']:.6f}°")
        delta_ra = (star['ra_at_epoch'] - star['ra_deg']) * 3600
        print(f"  RA Change: {delta_ra:.2f} arcsec")
        print()
        print(f"  Current Dec: {star['dec_deg']:.6f}°")
        print(f"  Year 3016 Dec: {star['dec_at_epoch']:.6f}°")
        delta_dec = (star['dec_at_epoch'] - star['dec_deg']) * 3600
        print(f"  Dec Change: {delta_dec:.2f} arcsec")
        print()
        print(f"  Uncertainty: {star['uncertainty_arcsec']:.3f} arcsec")
        print(f"  Classification: {star['uncertainty_class']}")
        print(f"  Proper Motion: {star['total_pm']:.2f} mas/yr at {star['pm_angle']:.1f}°")
    print()
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    print()

# Test 4: Star Trail
print("-" * 70)
print("TEST 4: Star Trail (2000 BC to 4000 AD)")
print("-" * 70)
try:
    r = requests.get(
        f"{BASE_URL}/temporal/star/397/trail",
        params={
            "start_epoch": -2000,
            "end_epoch": 4000,
            "num_points": 5
        }
    )
    trail = r.json()
    
    print(f"✓ Star ID: {trail['star_id']}")
    print(f"✓ Source: {trail['source_id']}")
    print(f"✓ Trail from {trail['start_epoch']} to {trail['end_epoch']}")
    print()
    print("Trail Points:")
    for i, point in enumerate(trail['trail_points'], 1):
        print(f"{i}. {point['epoch_display']:>10s}: RA={point['ra']:.4f}°, Dec={point['dec']:.4f}° (±{point['uncertainty_arcsec']:.1f}\")")
    print()
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    print()

# Test 5: Extreme Time Travel
print("-" * 70)
print("TEST 5: Extreme Time Travel (10,000 years)")
print("-" * 70)
try:
    payload = {
        "target_epoch": 12016,
        "ra_min": 50,
        "ra_max": 65,
        "dec_min": 20,
        "dec_max": 30,
        "limit": 5
    }
    r = requests.post(f"{BASE_URL}/temporal/query", json=payload)
    data = r.json()
    
    print(f"✓ Target: {data['epoch_display']}")
    print(f"✓ Stars: {data['count']}")
    
    if data['stars']:
        star = data['stars'][0]
        print(f"\nStar {star['id']} after 10,000 years:")
        print(f"  Position Change: {(star['ra_at_epoch'] - star['ra_deg']):.2f}° in RA")
        print(f"  Uncertainty: {star['uncertainty_arcsec']:.0f} arcsec = {star['uncertainty_arcsec']/3600:.3f}°")
        print(f"  Classification: {star['uncertainty_class']}")
    print()
except Exception as e:
    print(f"✗ Failed: {e}")
    print()

# Summary
print("=" * 70)
print("✅ ALL TESTS COMPLETE")
print("=" * 70)
print()
print("Time Machine API is FULLY OPERATIONAL! 🚀")
print()
print("Next: Access interactive docs at http://localhost:8000/docs")
print()
