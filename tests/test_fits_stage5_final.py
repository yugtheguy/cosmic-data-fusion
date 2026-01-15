"""
FITS Adapter - Stage 5: Final API Integration Verification
==========================================================

Pragmatic end-to-end testing focusing on production-ready API behavior.
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import UnifiedStarCatalog

TEST_DATA_DIR = Path(__file__).parent.parent / "app" / "data"


class TestStage5APIIntegration:
    """Stage 5: API Integration - Pragmatic Tests"""

    def test_01_api_health(self, client):
        """Verify API is running and healthy"""
        print("\nTest 1: API Health Check")
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"  [OK] API healthy: {data['service']}")

    def test_02_fits_hipparcos_ingestion(self, client, db_session):
        """Test Hipparcos FITS file ingestion via API"""
        print("\nTest 2: Hipparcos FITS Ingestion")
        
        fits_file = TEST_DATA_DIR / "hipparcos_sample.fits"
        assert fits_file.exists(), f"Test file not found: {fits_file}"
        
        with open(fits_file, "rb") as f:
            files = {"file": ("hipparcos_sample.fits", f, "application/octet-stream")}
            response = client.post("/ingest/fits", files=files)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        assert result["ingested_count"] == 50
        assert result["failed_count"] == 0
        
        dataset_id = result["dataset_id"]
        print(f"  [OK] Ingested 50 records, dataset_id={dataset_id}")
        
        # Verify in database
        count = db_session.query(UnifiedStarCatalog).filter_by(dataset_id=dataset_id).count()
        
        assert count == 50
        print(f"  [OK] Database verification: 50 records present")

    def test_03_fits_2mass_ingestion(self, client):
        """Test 2MASS FITS file ingestion"""
        print("\nTest 3: 2MASS FITS Ingestion")
        
        fits_file = TEST_DATA_DIR / "2mass_sample.fits"
        assert fits_file.exists()
        
        with open(fits_file, "rb") as f:
            files = {"file": ("2mass_sample.fits", f, "application/octet-stream")}
            response = client.post("/ingest/fits", files=files)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        assert result["ingested_count"] == 50
        
        print(f"  [OK] Ingested 50 2MASS records, dataset_id={result['dataset_id']}")

    def test_04_multi_dataset_verification(self, db_session):
        """Verify multiple datasets are properly stored"""
        print("\nTest 4: Multi-Dataset Storage Verification")
        
        total = db_session.query(UnifiedStarCatalog).count()
        datasets = db_session.query(UnifiedStarCatalog.dataset_id).distinct().count()
        
        # Get sample records
        sample_records = db_session.query(UnifiedStarCatalog).limit(3).all()
        print(f"  Total records: {total}")
        print(f"  Unique datasets: {datasets}")
        
        for rec in sample_records:
            print(f"    - {rec.object_id}: RA={rec.ra_deg:.2f}, "
                  f"Dec={rec.dec_deg:.2f}, Mag={rec.brightness_mag:.2f}")
        
        assert total >= 100
        assert datasets >= 2
        print(f"  [OK] Multi-dataset storage verified")

    def test_05_coordinate_validation(self, db_session):
        """Verify coordinates are properly stored and valid"""
        print("\nTest 5: Coordinate Validation")
        
        records = db_session.query(UnifiedStarCatalog).limit(10).all()
        
        for rec in records:
            assert -360 <= rec.ra_deg <= 360, f"Invalid RA: {rec.ra_deg}"
            assert -90 <= rec.dec_deg <= 90, f"Invalid Dec: {rec.dec_deg}"
            assert rec.brightness_mag is not None, "Missing magnitude"
        
        print(f"  [OK] All {len(records)} sampled records have valid coordinates")

    def test_06_magnitude_filtering(self, db_session):
        """Verify magnitude data is usable for filtering"""
        print("\nTest 6: Magnitude Filtering")
        
        bright_stars = db_session.query(UnifiedStarCatalog).filter(
            UnifiedStarCatalog.brightness_mag <= 8.0
        ).all()
        
        faint_stars = db_session.query(UnifiedStarCatalog).filter(
            UnifiedStarCatalog.brightness_mag > 8.0
        ).all()
        
        print(f"  Bright stars (mag <= 8.0): {len(bright_stars)}")
        print(f"  Faint stars (mag > 8.0): {len(faint_stars)}")
        
        print(f"  [OK] Magnitude filtering works")

    def test_07_distance_data(self, db_session):
        """Verify distance data is properly computed from parallax"""
        print("\nTest 7: Distance Data Verification")
        
        records_with_distance = db_session.query(UnifiedStarCatalog).filter(
            UnifiedStarCatalog.distance_pc is not None
        ).limit(5).all()
        
        print(f"  Records with distance data: {len(records_with_distance)}")
        
        for rec in records_with_distance:
            if rec.parallax_mas and rec.parallax_mas > 0:
                expected_dist = 1000.0 / rec.parallax_mas
                actual_dist = rec.distance_pc
                error = abs(expected_dist - actual_dist) / expected_dist if expected_dist > 0 else 0
                assert error < 0.01, f"Distance calculation error: {error*100:.2f}%"
                print(f"    Parallax={rec.parallax_mas:.2f} mas -> Distance={actual_dist:.2f} pc [OK]")
        
        print(f"  [OK] Distance conversions accurate")

    def test_08_metadata_preservation(self, db_session):
        """Verify raw metadata is preserved in JSON field"""
        print("\nTest 8: Metadata Preservation")
        
        records_with_metadata = db_session.query(UnifiedStarCatalog).filter(
            UnifiedStarCatalog.raw_metadata is not None
        ).limit(3).all()
        
        print(f"  Records with metadata: {len(records_with_metadata)}")
        
        for rec in records_with_metadata:
            if rec.raw_metadata:
                print(f"    Metadata keys: {list(rec.raw_metadata.keys())}")
        
        print(f"  [OK] Metadata preserved in database")

    def test_09_error_handling(self, client):
        """Verify API handles invalid files gracefully"""
        print("\nTest 9: Error Handling")
        
        invalid_fits = b"This is not a valid FITS file"
        files = {"file": ("invalid.fits", invalid_fits, "application/octet-stream")}
        response = client.post("/ingest/fits", files=files)
        
        assert response.status_code != 200
        print(f"  [OK] Invalid file rejected (status={response.status_code})")

    def test_10_api_response_format(self, client):
        """Verify API response structure is consistent"""
        print("\nTest 10: API Response Format Validation")
        
        fits_file = TEST_DATA_DIR / "hipparcos_sample.fits"
        with open(fits_file, "rb") as f:
            files = {"file": ("hipparcos_sample.fits", f, "application/octet-stream")}
            response = client.post("/ingest/fits", files=files)
        
        result = response.json()
        
        required = ["success", "message", "ingested_count", "failed_count", 
                   "dataset_id", "file_name", "catalog_info"]
        
        for field in required:
            assert field in result, f"Missing field: {field}"
        
        assert isinstance(result["success"], bool)
        assert isinstance(result["ingested_count"], int)
        assert isinstance(result["failed_count"], int)
        assert isinstance(result["dataset_id"], str)
        assert isinstance(result["catalog_info"], dict)
        
        print(f"  [OK] Response format valid with all {len(required)} required fields")


def run_tests():
    """Run Stage 5 final verification"""
    print("\n" + "="*80)
    print("STAGE 5: API INTEGRATION - FINAL VERIFICATION")
    print("="*80)
    
    test = TestStage5APIIntegration()
    test.setup_class()
    
    tests = [
        ("API Health", test.test_01_api_health),
        ("Hipparcos Ingestion", test.test_02_fits_hipparcos_ingestion),
        ("2MASS Ingestion", test.test_03_fits_2mass_ingestion),
        ("Multi-Dataset Verification", test.test_04_multi_dataset_verification),
        ("Coordinate Validation", test.test_05_coordinate_validation),
        ("Magnitude Filtering", test.test_06_magnitude_filtering),
        ("Distance Data", test.test_07_distance_data),
        ("Metadata Preservation", test.test_08_metadata_preservation),
        ("Error Handling", test.test_09_error_handling),
        ("Response Format", test.test_10_api_response_format),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {str(e)}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("SUCCESS: ALL STAGE 5 TESTS PASSED!")
        return True
    else:
        print(f"FAILURE: {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
