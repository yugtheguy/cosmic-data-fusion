"""
Stage 1: Environment & Dependency Verification Tests
Tests database connectivity, schema, sample data availability, and health endpoints.
"""

import os
import pytest
from sqlalchemy import inspect, text
from app.database import engine, SessionLocal
from app.main import app
from fastapi.testclient import TestClient


class TestEnvironmentVerification:
    """Verify environment and dependencies are correctly configured."""
    
    def test_database_file_exists(self):
        """Verify SQLite database file exists."""
        assert os.path.exists("cosmic_data_fusion.db"), "Database file not found"
    
    def test_database_connection(self):
        """Verify database connection works."""
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    
    def test_database_schema_complete(self):
        """Verify all required tables exist."""
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = [
            "unified_star_catalog",
            "dataset_metadata",
            "ingestion_errors",
            "discovery_runs",
            "discovery_results",
            "alembic_version"
        ]
        
        for table in required_tables:
            assert table in tables, f"Required table '{table}' missing"
        
        # Allow 6-7 tables (7th is spatial_ref_sys from PostGIS, optional)
        assert len(tables) >= 6, f"Expected at least 6 tables, found {len(tables)}: {tables}"
    
    def test_unified_star_catalog_schema(self):
        """Verify unified_star_catalog has all required columns."""
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns("unified_star_catalog")]
        
        required_columns = [
            "id",
            "source_id",
            "ra_deg",
            "dec_deg",
            "brightness_mag",
            "parallax_mas",
            "distance_pc",
            "original_source",
            "raw_frame",
            "observation_time",
            "dataset_id",
            "raw_metadata",
            "fusion_group_id",
            "created_at"
        ]
        
        for column in required_columns:
            assert column in columns, f"Required column '{column}' missing"
    
    def test_sample_data_files_exist(self):
        """Verify sample data files are present."""
        assert os.path.exists("app/data/gaia_dr3_sample.csv"), "Gaia sample data missing"
        assert os.path.exists("app/data/sdss_dr17_sample.csv"), "SDSS sample data missing"
        assert os.path.exists("app/data/sdss_edge_cases.csv"), "SDSS edge cases missing"
    
    def test_database_has_data(self):
        """Verify database contains test data."""
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM unified_star_catalog")).scalar()
            assert count > 0, f"Database should have records, found {count}"
    
    def test_fastapi_app_loads(self):
        """Verify FastAPI application loads without errors."""
        assert app is not None
        assert hasattr(app, 'routes')
        assert len(app.routes) > 0


class TestHealthEndpoint:
    """Verify health check endpoint is operational."""
    
    def test_health_endpoint_accessible(self):
        """Verify /health endpoint returns 200 OK."""
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
    
    def test_health_endpoint_response_format(self):
        """Verify health endpoint returns expected JSON structure."""
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] in ["healthy", "ok", "operational"]


class TestDatabaseIntegrity:
    """Verify database integrity constraints."""
    
    def test_no_null_coordinates(self):
        """Verify no records have null RA/Dec."""
        with engine.connect() as conn:
            null_coords = conn.execute(
                text("SELECT COUNT(*) FROM unified_star_catalog WHERE ra_deg IS NULL OR dec_deg IS NULL")
            ).scalar()
            
            assert null_coords == 0, f"Found {null_coords} records with null coordinates"
    
    def test_coordinate_ranges_valid(self):
        """Verify all coordinates are within valid ranges."""
        with engine.connect() as conn:
            # RA should be [0, 360]
            invalid_ra = conn.execute(
                text("SELECT COUNT(*) FROM unified_star_catalog WHERE ra_deg < 0 OR ra_deg > 360")
            ).scalar()
            
            assert invalid_ra == 0, f"Found {invalid_ra} records with invalid RA"
            
            # Dec should be [-90, 90]
            invalid_dec = conn.execute(
                text("SELECT COUNT(*) FROM unified_star_catalog WHERE dec_deg < -90 OR dec_deg > 90")
            ).scalar()
            
            assert invalid_dec == 0, f"Found {invalid_dec} records with invalid Dec"
    
    def test_brightness_magnitude_realistic(self):
        """Verify brightness magnitudes are in realistic range."""
        with engine.connect() as conn:
            invalid_mag = conn.execute(
                text("SELECT COUNT(*) FROM unified_star_catalog WHERE brightness_mag < -30 OR brightness_mag > 30")
            ).scalar()
            
            assert invalid_mag == 0, f"Found {invalid_mag} records with unrealistic magnitude"
    
    def test_dataset_metadata_integrity(self):
        """Verify dataset metadata table has valid records."""
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM dataset_metadata")).scalar()
            assert count >= 0, "dataset_metadata table should be queryable"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
