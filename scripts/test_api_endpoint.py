"""
Quick test of NL Query API endpoint
"""
import requests
import json

# Test the API endpoint
url = "http://localhost:8000/api/nl-query/query"
payload = {
    "query": "Show me bright stars near Orion",
    "page": 1,
    "page_size": 10
}

print("Testing NL Query API...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\n" + "="*60 + "\n")

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"\nResponse:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
