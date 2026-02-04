import requests

# Test query endpoint
response = requests.post('http://localhost:8000/query/search', json={'limit': 10})
print(f'Status Code: {response.status_code}')
data = response.json()
print(f'Total stars: {data["total_count"]}')
print(f'Returned: {data["returned_count"]}')
print(f'Success: {data["success"]}')
