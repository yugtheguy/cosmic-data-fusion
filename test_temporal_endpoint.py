import requests
import json

# Test the temporal query endpoint
url = "http://localhost:8000/temporal/query"

payload = {
    "target_epoch": 2000,
    "ra_min": 0,
    "ra_max": 180,
    "dec_min": -20,
    "dec_max": 40,
    "max_magnitude": 13,
    "limit": 100
}

print("Testing temporal query endpoint...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Received {len(data.get('stars', []))} stars")
        print(f"Response keys: {list(data.keys())}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError as e:
    print(f"❌ Connection Error: Cannot connect to {url}")
    print(f"   Make sure the backend server is running on port 8000")
    print(f"   Error: {e}")
    
except Exception as e:
    print(f"❌ Error: {e}")
