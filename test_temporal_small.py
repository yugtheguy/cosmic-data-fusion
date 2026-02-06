import requests
import json

# Test with reduced limit
url = "http://localhost:8000/temporal/query"

payload = {
    "target_epoch": 2000,
    "ra_min": 0,
    "ra_max": 180,
    "dec_min": -20,
    "dec_max": 40,
    "max_magnitude": 10,  # Only bright stars
    "limit": 100  # Small limit for testing
}

print("Testing temporal query with reduced limit...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Received {data.get('count', 0)} stars")
        print(f"Epoch: {data.get('epoch_display', 'N/A')}")
        if data.get('stars'):
            print(f"\nSample star:")
            star = data['stars'][0]
            print(f"  - ID: {star.get('id')}")
            print(f"  - RA: {star.get('ra_at_epoch'):.4f}°")
            print(f"  - Dec: {star.get('dec_at_epoch'):.4f}°")
            print(f"  - Magnitude: {star.get('brightness_mag'):.2f}")
            print(f"  - Uncertainty: {star.get('uncertainty_arcsec'):.2f} arcsec")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.Timeout:
    print("❌ Request timed out after 30 seconds")
    print("   The backend might still be processing the large dataset")
    
except requests.exceptions.ConnectionError as e:
    print(f"❌ Connection Error: Cannot connect to {url}")
    print(f"   Make sure the backend server is running on port 8000")
    
except Exception as e:
    print(f"❌ Error: {e}")
