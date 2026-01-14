"""
Layer 1 + Layer 2 End-to-End Integration Tests

This test suite verifies that Layer 1 (data ingestion) and Layer 2 (harmonization)
work together seamlessly in a complete pipeline from raw CSV files to validated,
cross-matched, AI-analyzed astronomical catalog.

Test Flow:
1. Layer 1: Ingest Gaia + SDSS CSV files → UnifiedStarCatalog
2. Layer 2: Validate coordinates/magnitudes
3. Layer 2: Cross-match to find duplicate observations
4. Layer 2: AI anomaly detection and clustering
5. Verify end-to-end data quality
"""

import pytest
import tempfile
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import UnifiedStarCatalog
from app.services.adapters.gaia_adapter import GaiaAdapter
from app.services.adapters.sdss_adapter import SDSSAdapter
from app.services.epoch_converter import EpochHarmonizer
from app.services.harmonizer import CrossMatchService
from app.services.ai_discovery import AIDiscoveryService


@pytest.fixture
def session():
    """Create in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def gaia_csv_file():
    """Create a realistic Gaia DR3 CSV sample file."""
    content = """source_id,ra,dec,parallax,phot_g_mean_mag,bp_rp
1234567890,180.5,45.2,5.3,12.5,0.8
1234567891,180.50001,45.20001,5.2,12.6,0.85
2345678901,200.0,-30.0,8.1,14.2,1.2
2345678902,200.00001,-30.00001,8.0,14.3,1.25
3456789012,185.0,46.0,3.5,13.8,0.9
3456789013,250.0,-60.0,12.5,11.2,0.6
4567890123,181.0,45.5,4.8,13.1,0.95
5678901234,199.5,-29.5,7.9,14.8,1.3
6789012345,186.0,46.5,3.2,25.5,1.5
7890123456,182.0,46.0,50.0,8.0,0.3
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def sdss_csv_file():
    """Create a realistic SDSS DR17 CSV sample file."""
    content = """objid,ra,dec,psfMag_g,psfMag_r,psfMag_i,type
1001,180.5,45.2,13.1,12.5,12.2,6
1002,200.0,-30.0,14.8,14.2,13.9,6
1003,185.0,46.0,14.4,13.8,13.5,6
1004,181.0,45.5,13.7,13.1,12.8,6
1005,220.0,10.0,15.2,14.6,14.3,6
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


class TestLayer1Layer2Integration:
    """Test complete Layer 1 → Layer 2 pipeline."""
    
    def test_gaia_ingestion_to_validation(self, session, gaia_csv_file):
        """Test Gaia ingestion (Layer 1) → coordinate validation (Layer 2)."""
        # Layer 1: Ingest Gaia data using adapter
        adapter = GaiaAdapter(dataset_id="gaia_test")
        valid_records, validation_results = adapter.process_batch(gaia_csv_file, skip_invalid=False)
        
        # Save to database
        for record in valid_records:
            star = UnifiedStarCatalog(**record)
            session.add(star)
        session.commit()
        
        assert len(valid_records) == 10
        
        # Layer 2: Validate coordinates
        harmonizer = EpochHarmonizer(session)
        coord_results = harmonizer.validate_coordinates()
        
        assert coord_results["total_stars"] == 10
        assert coord_results["valid_stars"] == 10
        assert coord_results["invalid_stars"] == 0
    
    def test_sdss_ingestion_to_validation(self, session, sdss_csv_file):
        """Test SDSS ingestion (Layer 1) → magnitude validation (Layer 2)."""
        # Layer 1: Ingest SDSS data using adapter
        adapter = SDSSAdapter(dataset_id="sdss_test")
        valid_records, validation_results = adapter.process_batch(sdss_csv_file, skip_invalid=False)
        
        # Save to database
        for record in valid_records:
            star = UnifiedStarCatalog(**record)
            session.add(star)
        session.commit()
        
        assert len(valid_records) == 5
        
        # Layer 2: Validate magnitudes
        harmonizer = EpochHarmonizer(session)
        mag_results = harmonizer.validate_magnitude()
        
        assert mag_results["total_stars"] == 5
        # All SDSS magnitudes should be valid (13-15 mag range is normal)
        assert mag_results["valid_stars"] >= 4
    
    def test_multi_catalog_cross_matching(self, session, gaia_csv_file, sdss_csv_file):
        """Test ingesting multiple catalogs → cross-matching for duplicates."""
        # Layer 1: Ingest both Gaia and SDSS using adapters
        gaia_adapter = GaiaAdapter(dataset_id="gaia_test")
        gaia_records, _ = gaia_adapter.process_batch(gaia_csv_file, skip_invalid=False)
        
        for record in gaia_records:
            session.add(UnifiedStarCatalog(**record))
        session.commit()
        
        sdss_adapter = SDSSAdapter(dataset_id="sdss_test")
        sdss_records, _ = sdss_adapter.process_batch(sdss_csv_file, skip_invalid=False)
        
        for record in sdss_records:
            session.add(UnifiedStarCatalog(**record))
        session.commit()
        
        total_ingested = len(gaia_records) + len(sdss_records)
        assert total_ingested == 15  # 10 Gaia + 5 SDSS
        
        # Verify both catalogs are present
        all_stars = session.query(UnifiedStarCatalog).all()
        assert len(all_stars) == 15
        
        gaia_stars = [s for s in all_stars if "gaia" in s.original_source.lower()]
        sdss_stars = [s for s in all_stars if "sdss" in s.original_source.lower()]
        assert len(gaia_stars) == 10
        assert len(sdss_stars) == 5
        
        # Layer 2: Cross-match to find duplicate observations
        # Gaia star at (180.5, 45.2) should match SDSS star at (180.5, 45.2)
        # Gaia star at (200.0, -30.0) should match SDSS star at (200.0, -30.0)
        # etc.
        cross_matcher = CrossMatchService(session)
        match_results = cross_matcher.perform_cross_match(radius_arcsec=2.0)
        
        assert match_results["total_stars"] == 15
        # Should find at least 4 matches (4 SDSS stars match Gaia stars)
        assert match_results["stars_in_groups"] >= 8  # At least 4 pairs = 8 stars
        assert match_results["groups_created"] >= 4
    
    def test_full_pipeline_with_ai_discovery(self, session, gaia_csv_file):
        """Test complete pipeline: Ingest → Validate → Cross-match → AI Analysis."""
        # Layer 1: Ingest Gaia data using adapter
        adapter = GaiaAdapter(dataset_id="gaia_full")
        valid_records, _ = adapter.process_batch(gaia_csv_file, skip_invalid=False)
        
        for record in valid_records:
            session.add(UnifiedStarCatalog(**record))
        session.commit()
        
        assert len(valid_records) == 10
        
        # Layer 2 Step 1: Coordinate validation
        harmonizer = EpochHarmonizer(session)
        coord_results = harmonizer.validate_coordinates()
        assert coord_results["valid_stars"] == 10
        
        # Layer 2 Step 2: Magnitude validation
        mag_results = harmonizer.validate_magnitude()
        # We have outliers: mag=25.5 (very faint) and mag=8.0 (very bright)
        # mag=25.5 should be flagged as unusually faint (>25)
        assert mag_results["suspicious_stars"] >= 1
        
        # Layer 2 Step 3: Cross-matching
        cross_matcher = CrossMatchService(session)
        match_results = cross_matcher.perform_cross_match(radius_arcsec=2.0)
        # Some stars are very close (< 1 arcsec apart) and will form groups
        # (180.5, 45.2) and (180.50001, 45.20001) are ~0.036 arcsec apart
        # (200.0, -30.0) and (200.00001, -30.00001) are ~0.036 arcsec apart
        assert match_results["groups_created"] >= 2
        
        # Layer 2 Step 4: AI Anomaly Detection
        ai_service = AIDiscoveryService(session)
        anomaly_results = ai_service.detect_anomalies(contamination=0.2)
        
        # Should detect outliers: mag=25.5 (faint), mag=8.0 (bright), parallax=50.0 (very close)
        assert len(anomaly_results) >= 1
        assert len(anomaly_results) <= 2  # Max 20% of 10 stars = 2 anomalies
        
        # Layer 2 Step 5: Clustering
        cluster_results = ai_service.detect_clusters(eps=2.0, min_samples=2)
        # Most stars should form at least one cluster
        assert len(cluster_results["clusters"]) >= 1
        
        # Layer 2 Step 6: Summary insights
        insights = ai_service.get_summary_insights()
        assert insights["total_stars"] == 10
        assert "anomaly_count" in insights
        assert "cluster_count" in insights
    
    def test_data_quality_report_generation(self, session, gaia_csv_file, sdss_csv_file):
        """Test generating comprehensive data quality report across both layers."""
        # Layer 1: Ingest both catalogs using adapters
        gaia_adapter = GaiaAdapter(dataset_id="gaia_quality")
        gaia_records, _ = gaia_adapter.process_batch(gaia_csv_file, skip_invalid=False)
        for record in gaia_records:
            session.add(UnifiedStarCatalog(**record))
        session.commit()
        
        sdss_adapter = SDSSAdapter(dataset_id="sdss_quality")
        sdss_records, _ = sdss_adapter.process_batch(sdss_csv_file, skip_invalid=False)
        for record in sdss_records:
            session.add(UnifiedStarCatalog(**record))
        session.commit()
        
        # Layer 2: Run all validation checks
        harmonizer = EpochHarmonizer(session)
        cross_matcher = CrossMatchService(session)
        ai_service = AIDiscoveryService(session)
        
        coord_results = harmonizer.validate_coordinates()
        mag_results = harmonizer.validate_magnitude()
        match_results = cross_matcher.perform_cross_match(radius_arcsec=2.0)
        anomaly_results = ai_service.detect_anomalies(contamination=0.15)
        cluster_results = ai_service.detect_clusters(eps=2.0, min_samples=3)
        match_stats = cross_matcher.get_cross_match_statistics()
        
        # Generate comprehensive quality report
        quality_report = {
            "ingestion": {
                "total_catalogs": 2,
                "total_records": coord_results["total_stars"]
            },
            "coordinate_validation": {
                "valid": coord_results["valid_stars"],
                "invalid": coord_results["invalid_stars"],
                "validation_rate": coord_results["validation_rate"]
            },
            "magnitude_validation": {
                "valid": mag_results["valid_stars"],
                "suspicious": mag_results["suspicious_stars"]
            },
            "cross_matching": {
                "total_stars": match_results["total_stars"],
                "fusion_groups": match_results["groups_created"],
                "stars_in_groups": match_results["stars_in_groups"],
                "isolated_stars": match_results["isolated_stars"]
            },
            "anomaly_detection": {
                "anomalies_found": len(anomaly_results),
                "anomaly_rate": round(len(anomaly_results) / coord_results["total_stars"] * 100, 2)
            },
            "clustering": {
                "clusters_found": len(cluster_results["clusters"]),
                "clustered_stars": sum(len(c) for c in cluster_results["clusters"].values())
            }
        }
        
        # Verify report completeness
        assert quality_report["ingestion"]["total_records"] == 15
        assert quality_report["coordinate_validation"]["validation_rate"] == 100.0
        assert quality_report["cross_matching"]["fusion_groups"] >= 4
        assert quality_report["anomaly_detection"]["anomalies_found"] >= 1
        assert quality_report["clustering"]["clusters_found"] >= 1
    
    def test_error_handling_across_layers(self, session):
        """Test that errors are properly handled across Layer 1 and Layer 2."""
        # Layer 1: Try to process non-existent file
        adapter = GaiaAdapter(dataset_id="error_test")
        
        with pytest.raises(ValueError, match="File not found"):
            adapter.process_batch("/nonexistent/file.csv", skip_invalid=False)
        
        # Verify database is still clean
        star_count = session.query(UnifiedStarCatalog).count()
        assert star_count == 0
        
        # Layer 2: Try to run validation on empty database
        harmonizer = EpochHarmonizer(session)
        coord_results = harmonizer.validate_coordinates()
        
        assert coord_results["total_stars"] == 0
        assert coord_results["message"] == "No stars found in database"
        
        # Layer 2: Try to run AI analysis on empty database
        ai_service = AIDiscoveryService(session)
        
        with pytest.raises(Exception, match="Insufficient data"):
            ai_service.detect_anomalies()
    
    def test_performance_with_realistic_dataset(self, session, gaia_csv_file):
        """Test that the pipeline performs reasonably with realistic data size."""
        import time
        
        # Layer 1: Ingest (should be fast)
        start_time = time.time()
        adapter = GaiaAdapter(dataset_id="perf_test")
        valid_records, _ = adapter.process_batch(gaia_csv_file, skip_invalid=False)
        for record in valid_records:
            session.add(UnifiedStarCatalog(**record))
        session.commit()
        ingestion_time = time.time() - start_time
        
        assert ingestion_time < 5.0  # Should complete in < 5 seconds
        
        # Layer 2: Full pipeline (should also be fast for 10 stars)
        start_time = time.time()
        
        harmonizer = EpochHarmonizer(session)
        harmonizer.validate_coordinates()
        harmonizer.validate_magnitude()
        
        cross_matcher = CrossMatchService(session)
        cross_matcher.perform_cross_match(radius_arcsec=2.0)
        
        ai_service = AIDiscoveryService(session)
        ai_service.detect_anomalies(contamination=0.2)
        ai_service.detect_clusters(eps=2.0, min_samples=2)
        
        pipeline_time = time.time() - start_time
        
        assert pipeline_time < 10.0  # Full Layer 2 pipeline in < 10 seconds
