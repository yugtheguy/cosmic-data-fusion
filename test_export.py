"""Complete export test with proper columns."""
import requests

response = requests.get(
    "http://localhost:8000/temporal/export",
    params={
        "target_epoch": -3000,
        "format": "json",
        "limit": 5
    }
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Epoch: {data['epoch_display']}")
    print(f"Star count: {data['count']}")
    if data['stars']:
        for star in data['stars'][:3]:
            print(f"  Star {star['id']}: RA={star['ra_epoch']:.4f}, Dec={star['dec_epoch']:.4f}")
    else:
        print("  No stars returned")
else:
    print(f"Error: {response.text}")
