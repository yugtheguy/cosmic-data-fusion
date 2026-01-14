"""Quick test of analytics API endpoints."""
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Test GET /analytics/discovery/stats
response = client.get('/analytics/discovery/stats?limit=5')
print(f'✅ GET /analytics/discovery/stats - Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    print(f'   Found {len(data)} runs')
    if data:
        print(f'   Sample: {data[0]["run_type"]} - {data[0]["total_stars"]} stars, {data[0]["anomaly_count"]} anomalies')
else:
    print(f'   Error: {response.text[:200]}')

# Test POST /analytics/discovery/refresh-views
response = client.post('/analytics/discovery/refresh-views')
print(f'\n✅ POST /analytics/discovery/refresh-views - Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    print(f'   {data["message"]}')
    print(f'   Views refreshed: {len(data["views_refreshed"])}')
else:
    print(f'   Error: {response.text[:200]}')

print('\n✅ Analytics API tests complete!')
