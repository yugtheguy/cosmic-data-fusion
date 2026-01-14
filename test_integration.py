"""Integration test: File validation + Error reporting in real ingest workflow."""

import requests
from pathlib import Path
import tempfile

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("INTEGRATION TEST: File Validation + Error Reporting")
print("=" * 60)

# Test 1: Upload invalid file (too large - will fail MIME validation)
print("\n1. Testing invalid file rejection...")
with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
    f.write(b"MZ\x90\x00" + b"\x00" * 100)  # Fake EXE file
    temp_file = f.name

try:
    with open(temp_file, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/ingest/gaia",
            files={"file": f},
            params={"dataset_id": "invalid-file-test"}
        )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 400:
        print(f"   ✅ Invalid file rejected: {response.json()['detail'][:60]}...")
    else:
        print(f"   ❌ Unexpected status: {response.status_code}")

except Exception as e:
    print(f"   Error: {e}")

# Test 2: Check that error was logged
print("\n2. Checking error logs for invalid file...")
response = requests.get(f"{BASE_URL}/errors/dataset/invalid-file-test")
if response.status_code == 200:
    errors = response.json()
    print(f"   ✅ Found {len(errors)} error(s) logged")
    for error in errors:
        print(f"      - {error['error_type']}: {error['message'][:50]}...")
elif response.status_code == 404:
    print("   ⚠️  No errors logged (validation may be too lenient)")
else:
    print(f"   Error: {response.status_code}")

# Test 3: Create a valid but minimal CSV file
print("\n3. Testing valid file ingestion...")
with tempfile.NamedTemporaryFile(mode='w', suffix=".csv", delete=False) as f:
    f.write("ra_deg,dec_deg,mag\n")
    f.write("123.456,45.678,15.5\n")
    temp_csv = f.name

try:
    with open(temp_csv, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/ingest/gaia",
            files={"file": f},
            params={"dataset_id": "valid-file-test"}
        )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ File accepted")
        print(f"      Ingested: {data.get('ingested_count', 0)} records")
        print(f"      Failed: {data.get('failed_count', 0)} records")
        print(f"      File hash: {data.get('file_hash', 'N/A')[:16]}...")

except Exception as e:
    print(f"   Error: {e}")

# Test 4: Check error logs for valid file (should have parsing errors if any)
print("\n4. Checking error logs for valid file...")
response = requests.get(f"{BASE_URL}/errors/dataset/valid-file-test")
if response.status_code == 200:
    errors = response.json()
    print(f"   Found {len(errors)} error(s)")
    for error in errors[:3]:  # Show first 3
        print(f"      - {error['error_type']}: {error['message'][:50]}...")
elif response.status_code == 404:
    print("   ✅ No errors (file validated successfully)")

# Test 5: Get error summary
print("\n5. Testing error summary endpoint...")
response = requests.get(f"{BASE_URL}/errors/dataset/invalid-file-test/summary")
if response.status_code == 200:
    summary = response.json()
    print(f"   ✅ Error summary retrieved")
    print(f"      Total: {summary['total_errors']}")
    print(f"      Errors: {summary['error_count']}")
    print(f"      Warnings: {summary['warning_count']}")
    print(f"      By type: {summary['by_type']}")

# Test 6: Export errors to CSV
print("\n6. Testing CSV export...")
response = requests.get(f"{BASE_URL}/errors/dataset/invalid-file-test/export")
if response.status_code == 200:
    csv_lines = response.text.split('\n')
    print(f"   ✅ CSV exported ({len(response.text)} bytes)")
    print(f"      Header: {csv_lines[0]}")
    if len(csv_lines) > 1:
        print(f"      Data rows: {len([l for l in csv_lines[1:] if l.strip()])}")

print("\n" + "=" * 60)
print("INTEGRATION TEST COMPLETE")
print("=" * 60)
