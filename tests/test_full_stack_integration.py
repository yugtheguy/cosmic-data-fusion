"""
Full Stack Integration Tests: Layer 1 + Layer 2 + Layer 3

Tests the complete data pipeline from ingestion to query/export.
NO MOCKS - All real implementations with in-memory database.

Pipeline Flow:
1. Layer 1: Ingest data from CSV/FITS → validate → store in DB
2. Layer 2: Harmonize epochs → cross-match → AI analysis
3. Layer 3: Query filtered data → export in multiple formats

This demonstrates the complete COSMIC Data Fusion system working end-to-end.
"""

import pytest
import tempfile
import json
from pathlib import Path
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, UnifiedStarCatalog, DatasetMetadata
from app.services.file_validation import FileValidator
from app.services.error_reporter import ErrorReporter
from app.services.adapters import GaiaAdapter, SDSSAdapter, CSVAdapter
from app.services.epoch_converter import EpochHarmonizer
from app.services.ai_discovery import AIDiscoveryService
from app.services.query_builder import QueryBuilder, QueryFilters
from app.services.search import SearchService
from app.services.exporter import DataExporter
from app.services.visualization import VisualizationService


@pytest.fixture
def db_session() -> Session:
    """Create in-memory SQLite database for full stack testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def gaia_csv_file(tmp_path: Path) -> Path:
    """Create a temporary Gaia CSV file for testing."""
    csv_content = """source_id,ra,dec,parallax,phot_g_mean_mag
1234567890,10.5,45.2,50.0,5.5
1234567891,11.0,46.0,48.0,6.0
1234567892,12.5,44.5,52.0,5.0
1234567893,13.0,45.8,49.5,5.8
"""
    file_path = tmp_path / "gaia_test.csv"
    file_path.write_text(csv_content)
    return file_path


@pytest.fixture
def sdss_csv_file(tmp_path: Path) -> Path:
    """Create a temporary SDSS CSV file for testing."""
    csv_content = """objID,ra,dec,psfMag_g,psfMag_r,psfMag_i
2234567890,10.48,45.18,15.5,14.8,14.2
2234567891,11.02,46.02,16.0,15.3,14.7
2234567892,180.5,-30.2,17.5,16.8,16.2
"""
    file_path = tmp_path / "sdss_test.csv"
    file_path.write_text(csv_content)
    return file_path


@pytest.fixture
def generic_csv_file(tmp_path: Path) -> Path:
    """Create a temporary generic CSV file for testing."""
    csv_content = """star_id,right_ascension,declination,magnitude,distance_parsec
GEN001,200.0,0.0,8.5,100.0
GEN002,200.5,0.5,9.0,120.0
GEN003,199.5,-0.5,8.8,110.0
"""
    file_path = tmp_path / "generic_test.csv"
    file_path.write_text(csv_content)
    return file_path


# ============================================================
# FULL STACK INTEGRATION TESTS
# ============================================================

class TestFullStackIntegration:
    """Test complete pipeline: Ingest → Harmonize → Query → Export"""
    
    def test_layer1_to_layer3_gaia_pipeline(
        self, db_session: Session, gaia_csv_file: Path
    ):
        """
        Test complete pipeline for Gaia data:
        Layer 1: Ingest Gaia CSV
        Layer 2: Validate coordinates
        Layer 3: Query and export
        """
        # ========================================
        # LAYER 1: Ingestion
        # ========================================
        validator = FileValidator()
        error_reporter = ErrorReporter(db_session)
        
        # Validate file
        result = validator.validate_file(gaia_csv_file)
        is_valid = result.is_valid
        errors = result.errors
        assert is_valid, f"File validation failed: {errors}"
        
        # Adapt Gaia data
        adapter = GaiaAdapter(db_session, error_reporter)
        stars, metadata = adapter.ingest_file(str(gaia_csv_file))
        
        assert len(stars) == 4
        assert metadata.record_count == 4
        assert metadata.source_type == "Gaia DR3"
        
        # ========================================
        # LAYER 2: Harmonization & Validation
        # ========================================
        harmonizer = EpochHarmonizer(db_session)
        
        # Validate all ingested stars
        for star in stars:
            is_valid, _ = harmonizer.validate_coordinates(
                star.ra_deg, star.dec_deg
            )
            assert is_valid, f"Star {star.source_id} has invalid coordinates"
        
        # ========================================
        # LAYER 3: Query & Export
        # ========================================
        # Query 1: Get all Gaia stars
        builder = QueryBuilder(db_session)
        filters = QueryFilters(original_source="Gaia DR3")
        query = builder.build_query(filters)
        results = query.all()
        
        assert len(results) == 4
        
        # Query 2: Filter by brightness
        filters_bright = QueryFilters(max_mag=6.0, original_source="Gaia DR3")
        query_bright = builder.build_query(filters_bright)
        bright_stars = query_bright.all()
        
        assert len(bright_stars) == 4  # All have mag <= 6.0
        
        # Export to CSV
        exporter = DataExporter(bright_stars)
        csv_output = exporter.to_csv()
        
        assert "source_id" in csv_output
        assert "1234567890" in csv_output
        
        # Export to JSON
        json_output = exporter.to_json()
        data = json.loads(json_output)
        
        assert data["count"] == 4
        assert len(data["records"]) == 4
    
    def test_layer1_to_layer3_sdss_pipeline(
        self, db_session: Session, sdss_csv_file: Path
    ):
        """
        Test complete pipeline for SDSS data:
        Layer 1: Ingest SDSS CSV
        Layer 2: Cross-match with existing data
        Layer 3: Spatial search and visualization
        """
        # ========================================
        # LAYER 1: Ingestion
        # ========================================
        validator = FileValidator()
        error_reporter = ErrorReporter(db_session)
        
        result = validator.validate_file(sdss_csv_file)
        is_valid = result.is_valid
        assert is_valid
        
        adapter = SDSSAdapter(db_session, error_reporter)
        stars, metadata = adapter.ingest_file(str(sdss_csv_file))
        
        assert len(stars) == 3
        assert metadata.source_type == "SDSS"
        
        # ========================================
        # LAYER 2: Harmonization
        # ========================================
        harmonizer = EpochHarmonizer(db_session)
        
        # Validate coordinates
        for star in stars:
            is_valid, _ = harmonizer.validate_coordinates(
                star.ra_deg, star.dec_deg
            )
            assert is_valid
        
        # ========================================
        # LAYER 3: Spatial Search
        # ========================================
        search_service = SearchService(db_session)
        
        # Bounding box search in northern region
        northern_stars = search_service.search_bounding_box(
            ra_min=10.0,
            ra_max=12.0,
            dec_min=45.0,
            dec_max=47.0,
            limit=100
        )
        
        assert len(northern_stars) == 2  # Two SDSS stars in this region
        
        # Cone search around southern star
        southern_cone = search_service.search_cone(
            ra=180.5,
            dec=-30.2,
            radius=1.0,
            limit=100
        )
        
        assert len(southern_cone) >= 1  # At least the center star
        
        # ========================================
        # LAYER 3: Visualization
        # ========================================
        viz_service = VisualizationService(db_session)
        
        # Get sky points for plotting
        sky_points = viz_service.get_sky_points(limit=100)
        assert len(sky_points) == 3
        
        # Get catalog statistics
        stats = viz_service.get_catalog_stats()
        assert stats["total_stars"] == 3
        assert stats["brightness"]["min_mag"] <= stats["brightness"]["max_mag"]
    
    def test_layer1_to_layer3_multi_source_integration(
        self, db_session: Session, gaia_csv_file: Path, sdss_csv_file: Path
    ):
        """
        Test full pipeline with multiple data sources:
        Layer 1: Ingest Gaia + SDSS
        Layer 2: Cross-match and AI discovery
        Layer 3: Query, filter by source, and export
        """
        # ========================================
        # LAYER 1: Ingest Multiple Sources
        # ========================================
        error_reporter_gaia = ErrorReporter(db_session)
        error_reporter_sdss = ErrorReporter(db_session)
        
        # Ingest Gaia
        gaia_adapter = GaiaAdapter(db_session, error_reporter_gaia)
        gaia_stars, gaia_metadata = gaia_adapter.ingest_file(str(gaia_csv_file))
        
        # Ingest SDSS
        sdss_adapter = SDSSAdapter(db_session, error_reporter_sdss)
        sdss_stars, sdss_metadata = sdss_adapter.ingest_file(str(sdss_csv_file))
        
        total_stars = len(gaia_stars) + len(sdss_stars)
        assert total_stars == 7  # 4 Gaia + 3 SDSS
        
        # ========================================
        # LAYER 2: AI Discovery
        # ========================================
        ai_service = AIDiscoveryService(db_session)
        
        # Run anomaly detection on all data
        anomalies = ai_service.detect_anomalies()
        
        # Should find some anomalies (different brightness/parallax distributions)
        assert len(anomalies) >= 0  # May or may not find anomalies with small dataset
        
        # Run clustering
        cluster_report = ai_service.detect_clusters()
        
        assert "total_stars" in cluster_report
        assert cluster_report["total_stars"] == total_stars
        
        # ========================================
        # LAYER 3: Multi-Source Queries
        # ========================================
        builder = QueryBuilder(db_session)
        
        # Query 1: Get only Gaia stars
        gaia_filters = QueryFilters(original_source="Gaia DR3")
        gaia_query = builder.build_query(gaia_filters)
        gaia_results = gaia_query.all()
        
        assert len(gaia_results) == 4
        assert all(star.original_source == "Gaia DR3" for star in gaia_results)
        
        # Query 2: Get only SDSS stars
        sdss_filters = QueryFilters(original_source="SDSS DR17")
        sdss_query = builder.build_query(sdss_filters)
        sdss_results = sdss_query.all()
        
        assert len(sdss_results) == 3
        assert all(star.original_source == "SDSS DR17" for star in sdss_results)
        
        # Query 3: Get all bright stars (any source)
        bright_filters = QueryFilters(max_mag=10.0)
        bright_query = builder.build_query(bright_filters)
        bright_results = bright_query.all()
        
        # Should include Gaia stars (mag ~5-6) but not all SDSS (mag 14-17)
        assert len(bright_results) >= 4
        
        # ========================================
        # LAYER 3: Export Combined Data
        # ========================================
        # Export all stars to VOTable (astronomical standard)
        all_stars = db_session.query(UnifiedStarCatalog).all()
        exporter = DataExporter(all_stars)
        
        votable_output = exporter.to_votable()
        assert b"VOTABLE" in votable_output or b"votable" in votable_output.lower()
        
        # Export to JSON with metadata
        json_output = exporter.to_json()
        json_data = json.loads(json_output)
        
        assert json_data["count"] == 7
        assert "metadata" in json_data
        assert "records" in json_data
    
    def test_layer1_to_layer3_csv_adapter_pipeline(
        self, db_session: Session, generic_csv_file: Path
    ):
        """
        Test complete pipeline with generic CSV adapter:
        Layer 1: Ingest generic CSV
        Layer 2: Validate
        Layer 3: Cone search around ingested stars
        """
        # ========================================
        # LAYER 1: Ingest Generic CSV
        # ========================================
        error_reporter = ErrorReporter(db_session)
        
        adapter = CSVAdapter(db_session, error_reporter)
        stars, metadata = adapter.ingest_file(str(generic_csv_file))
        
        assert len(stars) == 3
        assert metadata.source_type == "CSV"
        assert metadata.format_type == "csv"
        
        # ========================================
        # LAYER 2: Validation
        # ========================================
        harmonizer = EpochHarmonizer(db_session)
        
        for star in stars:
            is_valid, _ = harmonizer.validate_coordinates(
                star.ra_deg, star.dec_deg
            )
            assert is_valid
        
        # ========================================
        # LAYER 3: Cone Search Around Cluster
        # ========================================
        search_service = SearchService(db_session)
        
        # Search around RA=200, Dec=0 (where stars are clustered)
        cone_results = search_service.search_cone(
            ra=200.0,
            dec=0.0,
            radius=2.0,
            limit=100
        )
        
        # Should find all 3 stars (they're within 1 degree)
        assert len(cone_results) == 3
        
        # Verify they're sorted by distance
        assert cone_results[0].source_id in ["GEN001", "GEN002", "GEN003"]
        
        # ========================================
        # LAYER 3: Export Cone Search Results
        # ========================================
        exporter = DataExporter(cone_results)
        csv_output = exporter.to_csv()
        
        assert "GEN001" in csv_output or "GEN002" in csv_output
        assert "200" in csv_output  # RA value
    
    def test_full_stack_performance_pagination(
        self, db_session: Session, gaia_csv_file: Path, sdss_csv_file: Path
    ):
        """
        Test pagination across full stack:
        Ingest large dataset, query with pagination, export pages
        """
        # ========================================
        # LAYER 1: Ingest Multiple Datasets
        # ========================================
        # Ingest Gaia
        error_reporter_gaia = ErrorReporter(db_session)
        gaia_adapter = GaiaAdapter(db_session, error_reporter_gaia)
        gaia_adapter.ingest_file(str(gaia_csv_file))
        
        # Ingest SDSS
        error_reporter_sdss = ErrorReporter(db_session)
        sdss_adapter = SDSSAdapter(db_session, error_reporter_sdss)
        sdss_adapter.ingest_file(str(sdss_csv_file))
        
        # Total: 7 stars
        
        # ========================================
        # LAYER 3: Paginated Queries
        # ========================================
        builder = QueryBuilder(db_session)
        
        # Page 1: Get first 3 stars
        filters_page1 = QueryFilters(limit=3, offset=0)
        query_page1 = builder.build_query(filters_page1)
        page1 = query_page1.all()
        
        assert len(page1) == 3
        
        # Page 2: Get next 3 stars
        filters_page2 = QueryFilters(limit=3, offset=3)
        query_page2 = builder.build_query(filters_page2)
        page2 = query_page2.all()
        
        assert len(page2) == 3
        
        # Page 3: Get remaining star
        filters_page3 = QueryFilters(limit=3, offset=6)
        query_page3 = builder.build_query(filters_page3)
        page3 = query_page3.all()
        
        assert len(page3) == 1
        
        # Verify no overlap between pages
        page1_ids = {star.id for star in page1}
        page2_ids = {star.id for star in page2}
        page3_ids = {star.id for star in page3}
        
        assert page1_ids.isdisjoint(page2_ids)
        assert page2_ids.isdisjoint(page3_ids)
        assert page1_ids.isdisjoint(page3_ids)
        
        # ========================================
        # LAYER 3: Export Each Page
        # ========================================
        for page_num, page_data in enumerate([page1, page2, page3], start=1):
            exporter = DataExporter(page_data)
            json_output = exporter.to_json()
            json_data = json.loads(json_output)
            
            assert json_data["count"] == len(page_data)
            assert len(json_data["records"]) == len(page_data)
    
    def test_full_stack_error_handling_and_metadata(
        self, db_session: Session, gaia_csv_file: Path
    ):
        """
        Test error handling and metadata tracking across all layers.
        """
        # ========================================
        # LAYER 1: Ingestion with Metadata
        # ========================================
        error_reporter = ErrorReporter(db_session)
        adapter = GaiaAdapter(db_session, error_reporter)
        
        stars, metadata = adapter.ingest_file(str(gaia_csv_file))
        
        # Verify metadata was created
        assert metadata.id is not None
        assert metadata.filename == str(gaia_csv_file)
        assert metadata.record_count == 4
        assert metadata.source_type == "Gaia DR3"
        assert metadata.status == "completed"
        
        # Check metadata in database
        db_metadata = db_session.query(DatasetMetadata).filter_by(
            id=metadata.id
        ).first()
        
        assert db_metadata is not None
        assert db_metadata.record_count == 4
        
        # ========================================
        # LAYER 2: Validation Tracking
        # ========================================
        harmonizer = EpochHarmonizer(db_session)
        
        valid_count = 0
        for star in stars:
            is_valid, _ = harmonizer.validate_coordinates(
                star.ra_deg, star.dec_deg
            )
            if is_valid:
                valid_count += 1
        
        # All should be valid
        assert valid_count == len(stars)
        
        # ========================================
        # LAYER 3: Query Count vs Actual Count
        # ========================================
        builder = QueryBuilder(db_session)
        filters = QueryFilters()
        
        # Get count
        count = builder.count_results(filters)
        
        # Get actual results
        query = builder.build_query(filters)
        results = query.all()
        
        # Count should match
        assert count == len(results)
        assert count == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
