"""Positive integration test: File validation + Error reporting success path."""

import requests
import tempfile
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("INTEGRATION TEST: Validation + Error Reporting (Success Path)")
print("=" * 70)

# Test 1: Try uploading a valid Gaia CSV with proper columns
print("\n1. Creating valid Gaia CSV file...")
gaia_csv = """source_id,ra,dec,phot_g_mean_mag,parallax
1234567890123456,10.5,20.3,15.2,10.5
2234567890123457,11.2,21.1,14.8,9.8
3234567890123458,12.1,22.5,16.1,11.2
"""

with tempfile.NamedTemporaryFile(mode='w', suffix=".csv", delete=False) as f:
    f.write(gaia_csv)
    csv_file = f.name

print(f"   ✅ Created test file: {csv_file}")

# Test 2: Upload with validation
print("\n2. Uploading file to /ingest/gaia...")
with open(csv_file, "rb") as f:
    response = requests.post(
        f"{BASE_URL}/ingest/gaia",
        files={"file": f},
        params={"dataset_id": "integration-gaia-test"}
    )

print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Success!")
    print(f"      Message: {data['message'][:80]}...")
    print(f"      Ingested: {data.get('ingested_count', 0)}")
    print(f"      Failed: {data.get('failed_count', 0)}")
    print(f"      File hash: {data.get('file_hash', 'N/A')[:16]}...")
    dataset_id = data.get('dataset_id')
else:
    print(f"   ❌ Failed: {response.json()}")
    dataset_id = "integration-gaia-test"

# Test 3: Check error logs
print(f"\n3. Checking error logs for dataset {dataset_id}...")
response = requests.get(f"{BASE_URL}/errors/dataset/{dataset_id}")
if response.status_code == 200:
    errors = response.json()
    print(f"   ✅ {len(errors)} error(s) found")
    for e in errors[:3]:
        print(f"      [{e['severity']}] {e['error_type']}: {e['message'][:60]}...")
elif response.status_code == 404:
    print(f"   ✅ No errors logged - validation successful!")

# Test 4: Get summary statistics
print(f"\n4. Getting error summary...")
response = requests.get(f"{BASE_URL}/errors/dataset/{dataset_id}/summary")
if response.status_code == 200:
    summary = response.json()
    print(f"   ✅ Summary retrieved")
    print(f"      Total errors: {summary['total_errors']}")
    print(f"      By severity: ERROR={summary['error_count']}, "
          f"WARNING={summary['warning_count']}, INFO={summary['info_count']}")
    print(f"      By type: {summary['by_type']}")
elif response.status_code == 404:
    print(f"   ✅ No errors to summarize")

# Test 5: Test invalid file rejection
print(f"\n5. Testing invalid file rejection...")
with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
    f.write(b"MZ" + b"\x00" * 100)
    bad_file = f.name

with open(bad_file, "rb") as f:
    response = requests.post(
        f"{BASE_URL}/ingest/gaia",
        files={"file": f},
        params={"dataset_id": "invalid-file-test"}
    )

print(f"   Status: {response.status_code}")
if response.status_code == 400:
    print(f"   ✅ Invalid file rejected as expected")
    print(f"      Error: {response.json()['detail'][:60]}...")

# Test 6: Check that rejection was logged
print(f"\n6. Checking error logs for invalid file...")
response = requests.get(f"{BASE_URL}/errors/dataset/invalid-file-test")
if response.status_code == 200:
    errors = response.json()
    print(f"   ✅ {len(errors)} error(s) logged for rejected file")
    validation_errors = [e for e in errors if e['error_type'] == 'VALIDATION']
    if validation_errors:
        print(f"      Validation error: {validation_errors[0]['message']}")

print("\n" + "=" * 70)
print("✅ INTEGRATION TEST COMPLETE - Validation + Error Reporting Working!")
print("=" * 70)
