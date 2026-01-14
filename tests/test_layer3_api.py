"""
Layer 3 API Integration Tests

Tests actual HTTP endpoints for Query & Export Engine:
- Search endpoints (bounding box, cone)
- Query endpoints (filter, export)
- Visualization endpoints (sky, density, stats)

Uses FastAPI TestClient for real HTTP request/response testing.
"""

import pytest
import json
from io import BytesIO

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models import Base, UnifiedStarCatalog
from app.database import get_db


# Test client setup
client = TestClient(app)


@pytest.fixture
def test_db():
    """Create in-memory test database and override dependency."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Add sample data
    db = TestingSessionLocal()
    sample_stars = [
        UnifiedStarCatalog(
            source_id="TEST_STAR_1",
            ra_deg=10.0,
            dec_deg=45.0,
            brightness_mag=5.0,
            parallax_mas=50.0,
            distance_pc=20.0,
            original_source="Gaia DR3",
            raw_frame="ICRS"
        ),
        UnifiedStarCatalog(
            source_id="TEST_STAR_2",
            ra_deg=15.0,
            dec_deg=50.0,
            brightness_mag=8.0,
            parallax_mas=30.0,
            distance_pc=33.3,
            original_source="Gaia DR3",
            raw_frame="ICRS"
        ),
        UnifiedStarCatalog(
            source_id="TEST_STAR_3",
            ra_deg=180.0,
            dec_deg=-30.0,
            brightness_mag=12.0,
            parallax_mas=5.0,
            distance_pc=200.0,
            original_source="SDSS DR17",
            raw_frame="ICRS"
        ),
        UnifiedStarCatalog(
            source_id="TEST_STAR_4",
            ra_deg=200.0,
            dec_deg=0.0,
            brightness_mag=7.0,
            parallax_mas=25.0,
            distance_pc=40.0,
            original_source="Gaia DR3",
            raw_frame="ICRS"
        ),
    ]
    db.add_all(sample_stars)
    db.commit()
    db.close()
    
    yield engine
    
    app.dependency_overrides.clear()


class TestSearchAPI:
    """Test /search/* endpoints."""
    
    def test_search_box_success(self, test_db):
        """Test bounding box search with valid parameters."""
        response = client.get(
            "/search/box",
            params={
                "ra_min": 5.0,
                "ra_max": 20.0,
                "dec_min": 40.0,
                "dec_max": 60.0,
                "limit": 100
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "count" in data
        assert "stars" in data
        assert data["count"] == 2  # TEST_STAR_1 and TEST_STAR_2
        assert len(data["stars"]) == 2
        
        # Verify stars are in correct range
        for star in data["stars"]:
            assert 5.0 <= star["ra_deg"] <= 20.0
            assert 40.0 <= star["dec_deg"] <= 60.0
    
    def test_search_box_empty_region(self, test_db):
        """Test bounding box search in empty region."""
        response = client.get(
            "/search/box",
            params={
                "ra_min": 300.0,
                "ra_max": 310.0,
                "dec_min": 80.0,
                "dec_max": 85.0,
                "limit": 100
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert len(data["stars"]) == 0
    
    def test_search_box_invalid_params(self, test_db):
        """Test bounding box search with invalid parameters."""
        # RA out of range
        response = client.get(
            "/search/box",
            params={
                "ra_min": -10.0,  # Invalid
                "ra_max": 20.0,
                "dec_min": 40.0,
                "dec_max": 60.0,
                "limit": 100
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_search_box_wraparound(self, test_db):
        """Test bounding box search with RA wraparound at 0°/360°."""
        # This test requires stars near RA=0° boundary
        # We'll add two stars: one at RA=359° and one at RA=1°
        from app.models import UnifiedStarCatalog
        from app.database import get_db
        
        # Get the actual database session from test_db fixture
        # Note: This is a bit tricky - we need to add to the same session
        # For now, we'll skip this advanced test or implement it differently
        pass  # Placeholder - wraparound functionality tested in test_ra_wraparound.py
    
    def test_search_cone_success(self, test_db):
        """Test cone search with valid parameters."""
        response = client.get(
            "/search/cone",
            params={
                "ra": 200.0,
                "dec": 0.0,
                "radius": 5.0,
                "limit": 100
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "count" in data
        assert "stars" in data
        assert data["count"] >= 1  # At least TEST_STAR_4
    
    def test_search_cone_respects_limit(self, test_db):
        """Test cone search respects limit parameter."""
        response = client.get(
            "/search/cone",
            params={
                "ra": 200.0,
                "dec": 0.0,
                "radius": 100.0,  # Large radius
                "limit": 2
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["stars"]) <= 2


class TestQueryAPI:
    """Test /query/* endpoints."""
    
    def test_query_filter_magnitude_range(self, test_db):
        """Test query with magnitude filter."""
        response = client.post(
            "/query/search",
            json={
                "min_mag": 5.0,
                "max_mag": 10.0,
                "limit": 100
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_count" in data
        assert "records" in data
        assert data["total_count"] == 3  # TEST_STAR_1, TEST_STAR_2, TEST_STAR_4
        assert len(data["records"]) == 3
        
        # Verify stars are in correct magnitude range
        for star in data["records"]:
            assert 5.0 <= star["brightness_mag"] <= 10.0
    
    def test_query_filter_source(self, test_db):
        """Test query filtered by source."""
        response = client.post(
            "/query/search",
            json={
                "original_source": "Gaia DR3",
                "limit": 100
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] == 3  # 3 Gaia stars
        assert all(star["original_source"] == "Gaia DR3" for star in data["records"])
    
    def test_query_filter_combined(self, test_db):
        """Test query with combined filters."""
        response = client.post(
            "/query/search",
            json={
                "min_mag": 5.0,
                "max_mag": 8.0,
                "original_source": "Gaia DR3",
                "limit": 100
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should match TEST_STAR_1, TEST_STAR_2, TEST_STAR_4 (all Gaia with mag 5-8)
        assert data["total_count"] == 3
        for star in data["records"]:
            assert 5.0 <= star["brightness_mag"] <= 8.0
            assert star["original_source"] == "Gaia DR3"
    
    def test_query_pagination(self, test_db):
        """Test query pagination."""
        # Page 1
        response1 = client.post(
            "/query/search",
            json={"limit": 2, "offset": 0}
        )
        assert response1.status_code == 200
        page1 = response1.json()["records"]
        
        # Page 2
        response2 = client.post(
            "/query/search",
            json={"limit": 2, "offset": 2}
        )
        assert response2.status_code == 200
        page2 = response2.json()["records"]
        
        # Pages should have different stars
        page1_ids = {star["source_id"] for star in page1}
        page2_ids = {star["source_id"] for star in page2}
        assert page1_ids.isdisjoint(page2_ids)
    
    def test_query_sources(self, test_db):
        """Test query sources endpoint."""
        response = client.get("/query/sources")
        
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert "count" in data
        assert data["count"] == 2  # Gaia DR3 and SDSS DR17
        assert "Gaia DR3" in data["sources"]
    
    def test_export_csv(self, test_db):
        """Test CSV export."""
        response = client.get(
            "/query/export",
            params={
                "format": "csv",
                "min_mag": 5.0,
                "max_mag": 10.0
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        
        # Verify CSV content
        content = response.text
        assert "source_id" in content
        assert "ra_deg" in content
        assert "TEST_STAR" in content
    
    def test_export_json(self, test_db):
        """Test JSON export."""
        response = client.get(
            "/query/export",
            params={
                "format": "json",
                "min_mag": 5.0,
                "max_mag": 10.0
            }
        )
        
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        
        data = response.json()
        assert "metadata" in data
        assert "count" in data
        assert "records" in data
        assert data["count"] == 3
    
    def test_export_votable(self, test_db):
        """Test VOTable export."""
        response = client.get(
            "/query/export",
            params={
                "format": "votable",
                "min_mag": 5.0,
                "max_mag": 10.0
            }
        )
        
        assert response.status_code == 200
        assert "xml" in response.headers["content-type"].lower()
        
        # Verify VOTable structure
        content = response.content.decode('utf-8')
        assert "VOTABLE" in content or "votable" in content


class TestVisualizationAPI:
    """Test /visualize/* endpoints."""
    
    def test_visualize_sky_points(self, test_db):
        """Test sky points endpoint."""
        response = client.get(
            "/visualize/sky",
            params={"limit": 100}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "count" in data
        assert "points" in data
        assert data["count"] == 4
        assert len(data["points"]) == 4
        
        # Verify point structure
        point = data["points"][0]
        assert "source_id" in point
        assert "ra" in point
        assert "dec" in point
        assert "mag" in point
    
    def test_visualize_sky_brightness_filter(self, test_db):
        """Test sky points with brightness filter."""
        response = client.get(
            "/visualize/sky",
            params={
                "limit": 100,
                "max_mag": 8.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only include stars with mag <= 8.0
        assert data["count"] == 3
        assert all(point["mag"] <= 8.0 for point in data["points"])
    
    def test_visualize_density_grid(self, test_db):
        """Test density grid endpoint."""
        response = client.get(
            "/visualize/density",
            params={
                "ra_bin_size": 30.0,
                "dec_bin_size": 30.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cells" in data
        assert len(data["cells"]) > 0
        
        # Verify cell structure
        cell_item = data["cells"][0]
        assert "ra_bin" in cell_item
        assert "dec_bin" in cell_item
        assert "count" in cell_item
    
    def test_visualize_catalog_stats(self, test_db):
        """Test catalog statistics endpoint."""
        response = client.get("/visualize/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_stars" in data
        assert data["total_stars"] == 4
        
        assert "coordinate_ranges" in data
        coord_ranges = data["coordinate_ranges"]
        assert "ra" in coord_ranges
        assert "dec" in coord_ranges
        assert coord_ranges["ra"]["min"] == 10.0
        assert coord_ranges["ra"]["max"] == 200.0
        
        assert "brightness" in data
        brightness = data["brightness"]
        assert "min_mag" in brightness
        assert "max_mag" in brightness
        assert brightness["min_mag"] == 5.0
        assert brightness["max_mag"] == 12.0


class TestAPIResponseSchemas:
    """Test API response schemas match OpenAPI spec."""
    
    def test_openapi_schema_available(self):
        """Test OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
    
    def test_search_endpoints_in_schema(self):
        """Test search endpoints are documented."""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema["paths"]
        
        assert "/search/box" in paths
        assert "/search/cone" in paths
        assert "get" in paths["/search/box"]
        assert "get" in paths["/search/cone"]
    
    def test_query_endpoints_in_schema(self):
        """Test query endpoints are documented."""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema["paths"]
        
        assert "/query/search" in paths
        assert "/query/sources" in paths
        assert "/query/export" in paths
    
    def test_visualize_endpoints_in_schema(self):
        """Test visualization endpoints are documented."""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema["paths"]
        
        assert "/visualize/sky" in paths
        assert "/visualize/density" in paths
        assert "/visualize/stats" in paths


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
