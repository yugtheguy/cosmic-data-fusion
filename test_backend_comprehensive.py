import requests

# Test if backend is even accessible
print("Testing backend accessibility...")
print("=" * 60)

try:
    # Test health endpoint
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"✅ Health endpoint: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()
    
    # Test root endpoint
    response = requests.get("http://localhost:8000/", timeout=5)
    print(f"✅ Root endpoint: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()
    
    # Test temporal endpoint with minimal payload
    payload = {
        "target_epoch": 2000,
        "limit": 10
    }
    print(f"Testing temporal endpoint with minimal payload: {payload}")
    response = requests.post("http://localhost:8000/temporal/query", json=payload, timeout=30)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! {data.get('count', 0)} stars returned")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("=" * 60)
