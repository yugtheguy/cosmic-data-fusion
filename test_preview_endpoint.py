"""Test preview endpoint with real HTTP request"""
import requests

files = {'file': ('2mass_sample.fits', open('app/data/2mass_sample.fits', 'rb'), 'application/octet-stream')}
params = {'adapter_type': 'auto', 'limit': 20}

try:
    response = requests.post('http://localhost:8000/ingest/preview', files=files, params=params)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'response'):
        print(f"Status: {e.response.status_code}")
        print(f"Body: {e.response.text}")
