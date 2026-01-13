#!/usr/bin/env python3
"""
COSMIC Data Fusion - Integration Sanity Check

This script verifies the entire pipeline works end-to-end by testing:
1. Health check (server running)
2. Phase 1: Data ingestion (Gaia DR3)
3. Phase 5: AI anomaly detection
4. Phase 3: Query and export functionality

Requirements:
    pip install requests

Usage:
    python tests/integration_sanity_check.py
"""

import sys
import requests

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30  # seconds

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def print_pass(step_name: str) -> None:
    """Print a passing test result in green."""
    print(f"{GREEN}✅ [{step_name}]: PASS{RESET}")


def print_fail(step_name: str, error_msg: str) -> None:
    """Print a failing test result in red and exit."""
    print(f"{RED}❌ [{step_name}]: FAIL{RESET}")
    print(f"{RED}   Error: {error_msg}{RESET}")
    sys.exit(1)


def test_health_check() -> None:
    """Setup Check: Ping GET /health to ensure the server is running."""
    step_name = "Health Check"
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            print_pass(step_name)
        else:
            print_fail(step_name, f"Expected status 200, got {response.status_code}")
    except requests.exceptions.ConnectionError:
        print_fail(step_name, f"Cannot connect to server at {BASE_URL}. Is it running?")
    except Exception as e:
        print_fail(step_name, str(e))


def test_gaia_ingestion() -> None:
    """Phase 1 Check: Load Gaia sample data and verify ingestion."""
    step_name = "Gaia Data Load"
    try:
        # Load Gaia sample data
        response = requests.post(f"{BASE_URL}/datasets/gaia/load", timeout=TIMEOUT)
        if response.status_code not in (200, 201):
            print_fail(step_name, f"Expected status 200 or 201, got {response.status_code}")
        print_pass(step_name)
    except Exception as e:
        print_fail(step_name, str(e))

    # Check stats
    step_name = "Gaia Stats Verification"
    try:
        response = requests.get(f"{BASE_URL}/datasets/gaia/stats", timeout=TIMEOUT)
        if response.status_code != 200:
            print_fail(step_name, f"Expected status 200, got {response.status_code}")
        
        data = response.json()
        # Handle different response structures
        count = data.get("count") or data.get("total") or data.get("record_count") or 0
        
        if count > 0:
            print_pass(f"{step_name} (count={count})")
        else:
            print_fail(step_name, f"Expected count > 0, got {count}. Response: {data}")
    except Exception as e:
        print_fail(step_name, str(e))


def test_ai_anomaly_detection() -> None:
    """Phase 5 Check: Run anomaly detection and verify results."""
    step_name = "AI Anomaly Detection"
    try:
        payload = {"contamination": 0.05}
        response = requests.post(
            f"{BASE_URL}/ai/anomalies",
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            print_fail(step_name, f"Expected status 200, got {response.status_code}. Response: {response.text}")
        
        data = response.json()
        
        # Check for anomalies in response
        anomalies = data.get("anomalies") or data.get("results") or []
        anomaly_count = data.get("anomaly_count") or data.get("count") or len(anomalies)
        
        if anomaly_count > 0:
            print_pass(f"{step_name} (found {anomaly_count} anomalies)")
        else:
            print_fail(step_name, f"Expected anomaly count > 0, got {anomaly_count}. Response: {data}")
    except Exception as e:
        print_fail(step_name, str(e))


def test_query_search() -> None:
    """Phase 3 Check: Test query search with limit."""
    step_name = "Query Search (limit=5)"
    try:
        payload = {"limit": 5}
        response = requests.post(
            f"{BASE_URL}/query/search",
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            print_fail(step_name, f"Expected status 200, got {response.status_code}. Response: {response.text}")
        
        data = response.json()
        
        # Handle different response structures
        results = (
            data.get("records") or 
            data.get("results") or 
            data.get("stars") or 
            data.get("data") or 
            data
        )
        if isinstance(results, list):
            result_count = len(results)
        else:
            result_count = 0
        
        if result_count == 5:
            print_pass(f"{step_name} (returned {result_count} stars)")
        else:
            print_fail(step_name, f"Expected exactly 5 results, got {result_count}.")
    except Exception as e:
        print_fail(step_name, str(e))


def test_votable_export() -> None:
    """Phase 3 Check: Test VOTable export functionality."""
    step_name = "VOTable Export"
    try:
        response = requests.get(
            f"{BASE_URL}/query/export?format=votable",
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            print_fail(step_name, f"Expected status 200, got {response.status_code}. Response: {response.text}")
        
        # Check Content-Disposition header for attachment
        content_disposition = response.headers.get("Content-Disposition", "")
        if "attachment" not in content_disposition.lower():
            print_fail(
                step_name,
                f"Expected 'attachment' in Content-Disposition header, got: '{content_disposition}'"
            )
        
        # Check content starts with valid XML
        content = response.text.strip()
        valid_xml_starts = ("<?xml", "<VOTABLE")
        if not any(content.startswith(tag) for tag in valid_xml_starts):
            print_fail(
                step_name,
                f"Expected content to start with <?xml or <VOTABLE, got: '{content[:100]}...'"
            )
        
        print_pass(f"{step_name} (valid VOTable XML received)")
    except Exception as e:
        print_fail(step_name, str(e))


def main() -> None:
    """Run all integration tests in sequence."""
    print("=" * 60)
    print("COSMIC Data Fusion - Integration Sanity Check")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print("-" * 60)
    
    # Run tests in strict sequence
    test_health_check()
    test_gaia_ingestion()
    test_ai_anomaly_detection()
    test_query_search()
    test_votable_export()
    
    print("-" * 60)
    print(f"{GREEN}✅ All integration tests passed!{RESET}")
    print("=" * 60)


if __name__ == "__main__":
    main()
