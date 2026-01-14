"""
Layer 3: Unified Spatial Data Repository Tests

Tests the Query & Export Engine with NO MOCKS - full database integration.

Layer 3 Components Tested:
1. QueryBuilder - Dynamic filtering with multiple criteria
2. SearchService - Spatial queries (bounding box and cone search)
3. DataExporter - Export to CSV, JSON, VOTable formats
4. VisualizationService - Data aggregations for frontend
5. Repository layer - StarCatalogRepository operations

All tests use real database operations with in-memory SQLite.
"""

import pytest
import json
from io import BytesIO
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, UnifiedStarCatalog
from app.services.query_builder import QueryBuilder, QueryFilters
from app.services.search import SearchService
from app.services.exporter import DataExporter
from app.services.visualization import VisualizationService
from app.repository.star_catalog import StarCatalogRepository


@pytest.fixture
def db_session() -> Session:
    """Create in-memory SQLite database for testing."""
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
def sample_stars(db_session: Session) -> List[UnifiedStarCatalog]:
    """
    Create diverse sample star data for testing Layer 3 queries.
    
    Creates stars with varied:
    - Positions (different RA/Dec regions)
    - Brightness (magnitude range)
    - Parallax (distance proxy)
    - Sources (Gaia, SDSS, FITS)
    """
    stars = [
        # Bright stars in northern hemisphere
        UnifiedStarCatalog(
            source_id="BRIGHT_NORTH_1",
            ra_deg=10.0,
            dec_deg=45.0,
            brightness_mag=2.5,
            parallax_mas=50.0,
            distance_pc=20.0,
            original_source="Gaia DR3",
            raw_frame="ICRS"
        ),
        UnifiedStarCatalog(
            source_id="BRIGHT_NORTH_2",
            ra_deg=15.0,
            dec_deg=50.0,
            brightness_mag=3.0,
            parallax_mas=40.0,
            distance_pc=25.0,
            original_source="Gaia DR3",
            raw_frame="ICRS"
        ),
        # Dim stars in southern hemisphere
        UnifiedStarCatalog(
            source_id="DIM_SOUTH_1",
            ra_deg=180.0,
            dec_deg=-30.0,
            brightness_mag=12.0,
            parallax_mas=5.0,
            distance_pc=200.0,
            original_source="SDSS",
            raw_frame="ICRS"
        ),
        UnifiedStarCatalog(
            source_id="DIM_SOUTH_2",
            ra_deg=185.0,
            dec_deg=-35.0,
            brightness_mag=14.0,
            parallax_mas=3.0,
            distance_pc=333.0,
            original_source="SDSS",
            raw_frame="ICRS"
        ),
        # Medium stars near equator
        UnifiedStarCatalog(
            source_id="MED_EQUATOR_1",
            ra_deg=90.0,
            dec_deg=5.0,
            brightness_mag=8.0,
            parallax_mas=20.0,
            distance_pc=50.0,
            original_source="FITS",
            raw_frame="ICRS"
        ),
        UnifiedStarCatalog(
            source_id="MED_EQUATOR_2",
            ra_deg=95.0,
            dec_deg=-5.0,
            brightness_mag=9.0,
            parallax_mas=15.0,
            distance_pc=66.7,
            original_source="FITS",
            raw_frame="ICRS"
        ),
        # Stars for cone search testing (clustered around RA=200, Dec=0)
        UnifiedStarCatalog(
            source_id="CONE_CENTER",
            ra_deg=200.0,
            dec_deg=0.0,
            brightness_mag=7.0,
            parallax_mas=25.0,
            distance_pc=40.0,
            original_source="Gaia DR3",
            raw_frame="ICRS"
        ),
        UnifiedStarCatalog(
            source_id="CONE_NEAR_1",
            ra_deg=200.5,
            dec_deg=0.5,
            brightness_mag=7.5,
            parallax_mas=23.0,
            distance_pc=43.5,
            original_source="Gaia DR3",
            raw_frame="ICRS"
        ),
        UnifiedStarCatalog(
            source_id="CONE_NEAR_2",
            ra_deg=199.5,
            dec_deg=-0.5,
            brightness_mag=8.0,
            parallax_mas=22.0,
            distance_pc=45.5,
            original_source="Gaia DR3",
            raw_frame="ICRS"
        ),
        UnifiedStarCatalog(
            source_id="CONE_FAR",
            ra_deg=205.0,
            dec_deg=0.0,
            brightness_mag=10.0,
            parallax_mas=10.0,
            distance_pc=100.0,
            original_source="SDSS",
            raw_frame="ICRS"
        ),
    ]
    
    db_session.add_all(stars)
    db_session.commit()
    
    # Refresh to get IDs
    for star in stars:
        db_session.refresh(star)
    
    return stars


# ============================================================
# LAYER 3: QueryBuilder Tests
# ============================================================

class TestQueryBuilder:
    """Test the QueryBuilder service with various filter combinations."""
    
    def test_query_no_filters_returns_all(self, db_session: Session, sample_stars):
        """QueryBuilder with no filters should return all stars."""
        builder = QueryBuilder(db_session)
        filters = QueryFilters()
        
        query = builder.build_query(filters)
        results = query.all()
        
        assert len(results) == len(sample_stars)
    
    def test_query_magnitude_filter_min(self, db_session: Session, sample_stars):
        """Filter by minimum magnitude (brightness)."""
        builder = QueryBuilder(db_session)
        filters = QueryFilters(min_mag=7.0)
        
        query = builder.build_query(filters)
        results = query.all()
        
        # Should include stars with mag >= 7.0
        assert all(star.brightness_mag >= 7.0 for star in results)
        assert len(results) == 8  # Stars with mag 7.0 and higher (includes dim stars)
    
    def test_query_magnitude_filter_max(self, db_session: Session, sample_stars):
        """Filter by maximum magnitude (faintness limit)."""
        builder = QueryBuilder(db_session)
        filters = QueryFilters(max_mag=10.0)
        
        query = builder.build_query(filters)
        results = query.all()
        
        # Should include stars with mag <= 10.0
        assert all(star.brightness_mag <= 10.0 for star in results)
        assert len(results) == 8  # All except the two dimmest
    
    def test_query_magnitude_range(self, db_session: Session, sample_stars):
        """Filter by magnitude range."""
        builder = QueryBuilder(db_session)
        filters = QueryFilters(min_mag=5.0, max_mag=10.0)
        
        query = builder.build_query(filters)
        results = query.all()
        
        # Should include stars with 5.0 <= mag <= 10.0
        assert all(5.0 <= star.brightness_mag <= 10.0 for star in results)
        assert len(results) == 6
    
    def test_query_parallax_filter(self, db_session: Session, sample_stars):
        """Filter by parallax (distance proxy)."""
        builder = QueryBuilder(db_session)
        filters = QueryFilters(min_parallax=20.0)
        
        query = builder.build_query(filters)
        results = query.all()
        
        # Should include stars with parallax >= 20.0 (closer stars)
        assert all(star.parallax_mas >= 20.0 for star in results)
        assert len(results) == 6  # 6 stars with parallax >= 20
    
    def test_query_spatial_bounding_box(self, db_session: Session, sample_stars):
        """Filter by spatial bounding box."""
        builder = QueryBuilder(db_session)
        filters = QueryFilters(
            ra_min=80.0,
            ra_max=100.0,
            dec_min=-10.0,
            dec_max=10.0
        )
        
        query = builder.build_query(filters)
        results = query.all()
        
        # Should include stars in the box
        assert all(
            80.0 <= star.ra_deg <= 100.0 and
            -10.0 <= star.dec_deg <= 10.0
            for star in results
        )
        assert len(results) == 2  # MED_EQUATOR_1 and MED_EQUATOR_2
    
    def test_query_source_filter(self, db_session: Session, sample_stars):
        """Filter by original source catalog."""
        builder = QueryBuilder(db_session)
        filters = QueryFilters(original_source="Gaia DR3")
        
        query = builder.build_query(filters)
        results = query.all()
        
        assert all(star.original_source == "Gaia DR3" for star in results)
        assert len(results) == 5  # 5 Gaia stars
    
    def test_query_combined_filters(self, db_session: Session, sample_stars):
        """Test combination of multiple filters."""
        builder = QueryBuilder(db_session)
        filters = QueryFilters(
            min_mag=2.0,
            max_mag=10.0,
            min_parallax=15.0,
            original_source="Gaia DR3"
        )
        
        query = builder.build_query(filters)
        results = query.all()
        
        # Should match all criteria
        for star in results:
            assert 2.0 <= star.brightness_mag <= 10.0
            assert star.parallax_mas >= 15.0
            assert star.original_source == "Gaia DR3"
        
        assert len(results) == 5  # 5 Gaia stars matching criteria
    
    def test_query_pagination_limit(self, db_session: Session, sample_stars):
        """Test query limit (pagination)."""
        builder = QueryBuilder(db_session)
        filters = QueryFilters(limit=5)
        
        query = builder.build_query(filters)
        results = query.all()
        
        assert len(results) == 5
    
    def test_query_pagination_offset(self, db_session: Session, sample_stars):
        """Test query offset (pagination)."""
        builder = QueryBuilder(db_session)
        
        # Get first page
        filters_page1 = QueryFilters(limit=5, offset=0)
        query1 = builder.build_query(filters_page1)
        page1 = query1.all()
        
        # Get second page
        filters_page2 = QueryFilters(limit=5, offset=5)
        query2 = builder.build_query(filters_page2)
        page2 = query2.all()
        
        assert len(page1) == 5
        assert len(page2) == 5
        
        # Pages should have different stars
        page1_ids = {star.id for star in page1}
        page2_ids = {star.id for star in page2}
        assert page1_ids.isdisjoint(page2_ids)
    
    def test_query_count_results(self, db_session: Session, sample_stars):
        """Test count_results method."""
        builder = QueryBuilder(db_session)
        filters = QueryFilters(min_mag=5.0, max_mag=10.0)
        
        count = builder.count_results(filters)
        
        assert count == 6


# ============================================================
# LAYER 3: SearchService Tests
# ============================================================

class TestSearchService:
    """Test the SearchService for spatial queries."""
    
    def test_bounding_box_search_northern(self, db_session: Session, sample_stars):
        """Test bounding box search in northern hemisphere."""
        service = SearchService(db_session)
        
        results = service.search_bounding_box(
            ra_min=5.0,
            ra_max=20.0,
            dec_min=40.0,
            dec_max=60.0,
            limit=100
        )
        
        assert len(results) == 2  # BRIGHT_NORTH_1 and BRIGHT_NORTH_2
        assert all(
            5.0 <= star.ra_deg <= 20.0 and
            40.0 <= star.dec_deg <= 60.0
            for star in results
        )
    
    def test_bounding_box_search_southern(self, db_session: Session, sample_stars):
        """Test bounding box search in southern hemisphere."""
        service = SearchService(db_session)
        
        results = service.search_bounding_box(
            ra_min=175.0,
            ra_max=190.0,
            dec_min=-40.0,
            dec_max=-25.0,
            limit=100
        )
        
        assert len(results) == 2  # DIM_SOUTH_1 and DIM_SOUTH_2
        assert all(star.dec_deg < 0 for star in results)
    
    def test_cone_search_finds_nearby_stars(self, db_session: Session, sample_stars):
        """Test cone search finds stars within radius."""
        service = SearchService(db_session)
        
        # Search around RA=200, Dec=0 with 2 degree radius
        results = service.search_cone(
            ra=200.0,
            dec=0.0,
            radius=2.0,
            limit=100
        )
        
        # Should find CONE_CENTER, CONE_NEAR_1, CONE_NEAR_2
        # but NOT CONE_FAR (5 degrees away)
        assert len(results) >= 3
        
        # Verify all results are within radius using angular separation
        for star in results:
            # Simple distance check (not exact spherical, but close enough for test)
            ra_diff = abs(star.ra_deg - 200.0)
            dec_diff = abs(star.dec_deg - 0.0)
            # Rough angular distance
            angular_dist = (ra_diff**2 + dec_diff**2)**0.5
            assert angular_dist <= 2.5  # Allow some margin for spherical geometry
    
    def test_cone_search_respects_limit(self, db_session: Session, sample_stars):
        """Test cone search respects result limit."""
        service = SearchService(db_session)
        
        # Large radius that would catch many stars, but limit to 2
        results = service.search_cone(
            ra=200.0,
            dec=0.0,
            radius=10.0,
            limit=2
        )
        
        assert len(results) <= 2
    
    def test_cone_search_empty_region(self, db_session: Session, sample_stars):
        """Test cone search in empty region returns no results."""
        service = SearchService(db_session)
        
        # Search in empty region
        results = service.search_cone(
            ra=300.0,
            dec=80.0,
            radius=1.0,
            limit=100
        )
        
        assert len(results) == 0


# ============================================================
# LAYER 3: DataExporter Tests
# ============================================================

class TestDataExporter:
    """Test the DataExporter for multiple output formats."""
    
    def test_export_to_csv(self, db_session: Session, sample_stars):
        """Test CSV export format."""
        # Get sample data
        stars = db_session.query(UnifiedStarCatalog).limit(5).all()
        
        exporter = DataExporter(stars)
        csv_output = exporter.to_csv()
        
        # Verify CSV structure
        assert csv_output is not None
        assert "source_id" in csv_output
        assert "ra_deg" in csv_output
        assert "dec_deg" in csv_output
        assert "brightness_mag" in csv_output
        
        # Verify data rows exist
        lines = csv_output.strip().split("\n")
        assert len(lines) >= 6  # Header + 5 data rows
    
    def test_export_to_json(self, db_session: Session, sample_stars):
        """Test JSON export format."""
        stars = db_session.query(UnifiedStarCatalog).limit(3).all()
        
        exporter = DataExporter(stars)
        json_output = exporter.to_json()
        
        # Verify JSON structure
        data = json.loads(json_output)
        
        assert "metadata" in data
        assert "count" in data
        assert "records" in data
        
        assert data["count"] == 3
        assert len(data["records"]) == 3
        
        # Verify record structure
        record = data["records"][0]
        assert "source_id" in record
        assert "ra_deg" in record
        assert "dec_deg" in record
        assert "brightness_mag" in record
    
    def test_export_to_votable(self, db_session: Session, sample_stars):
        """Test VOTable export format (astronomical standard)."""
        stars = db_session.query(UnifiedStarCatalog).limit(5).all()
        
        exporter = DataExporter(stars)
        votable_bytes = exporter.to_votable()
        
        # Verify VOTable is valid XML
        assert votable_bytes is not None
        assert b"<?xml version" in votable_bytes or b"<VOTABLE" in votable_bytes
        
        # Verify astronomical content
        votable_str = votable_bytes.decode('utf-8')
        assert "VOTABLE" in votable_str
        assert "RESOURCE" in votable_str or "TABLE" in votable_str
    
    def test_export_empty_data(self, db_session: Session):
        """Test export with empty dataset."""
        exporter = DataExporter([])
        
        # CSV with empty data should still work (may be empty or header-only)
        csv_output = exporter.to_csv()
        assert csv_output is not None
        assert len(csv_output) >= 0  # Empty or has headers
        
        # JSON should have zero count
        json_output = exporter.to_json()
        data = json.loads(json_output)
        assert data["count"] == 0
        assert len(data["records"]) == 0


# ============================================================
# LAYER 3: VisualizationService Tests
# ============================================================

class TestVisualizationService:
    """Test the VisualizationService for frontend data."""
    
    def test_get_sky_points(self, db_session: Session, sample_stars):
        """Test sky points extraction for scatter plots."""
        service = VisualizationService(db_session)
        
        points = service.get_sky_points(limit=100)
        
        assert len(points) == len(sample_stars)
        
        # Verify point structure
        point = points[0]
        assert "source_id" in point
        assert "ra" in point
        assert "dec" in point
        assert "mag" in point
    
    def test_get_sky_points_brightness_filter(self, db_session: Session, sample_stars):
        """Test sky points with brightness filter."""
        service = VisualizationService(db_session)
        
        points = service.get_sky_points(
            limit=100,
            max_brightness=8.0
        )
        
        # Should only include stars with mag <= 8.0
        assert all(point["mag"] <= 8.0 for point in points)
        assert len(points) == 6  # 6 stars with mag <= 8.0
    
    def test_get_sky_points_sorted_by_brightness(self, db_session: Session, sample_stars):
        """Test sky points are sorted by brightness (brightest first)."""
        service = VisualizationService(db_session)
        
        points = service.get_sky_points(limit=100)
        
        # Points should be sorted by magnitude (ascending)
        magnitudes = [point["mag"] for point in points]
        assert magnitudes == sorted(magnitudes)
    
    def test_get_density_grid(self, db_session: Session, sample_stars):
        """Test density grid generation for heatmaps."""
        service = VisualizationService(db_session)
        
        grid = service.get_density_grid(ra_bin_size=30.0, dec_bin_size=30.0)
        
        assert len(grid) > 0
        
        # Verify grid cell structure
        cell = grid[0]
        assert "ra_bin" in cell
        assert "dec_bin" in cell
        assert "count" in cell
        assert cell["count"] > 0
    
    def test_get_catalog_stats(self, db_session: Session, sample_stars):
        """Test catalog statistics aggregation."""
        service = VisualizationService(db_session)
        
        stats = service.get_catalog_stats()
        
        assert "total_stars" in stats
        assert stats["total_stars"] == len(sample_stars)
        
        # Stats returned in nested structure
        assert "coordinate_ranges" in stats
        assert "brightness" in stats
        
        # Check coordinate ranges
        coord_ranges = stats["coordinate_ranges"]
        assert coord_ranges["ra"]["min"] == 10.0
        assert coord_ranges["ra"]["max"] == 205.0
        assert coord_ranges["dec"]["min"] == -35.0
        assert coord_ranges["dec"]["max"] == 50.0
        
        # Check brightness stats
        brightness = stats["brightness"]
        assert brightness["min_mag"] == 2.5
        assert brightness["max_mag"] == 14.0


# ============================================================
# LAYER 3: StarCatalogRepository Tests
# ============================================================

class TestStarCatalogRepository:
    """Test the repository layer for database operations."""
    
    def test_repository_search_bounding_box(self, db_session: Session, sample_stars):
        """Test repository bounding box search method."""
        repo = StarCatalogRepository(db_session)
        
        results = repo.search_bounding_box(
            ra_min=5.0,
            ra_max=20.0,
            dec_min=40.0,
            dec_max=60.0,
            limit=100
        )
        
        assert len(results) == 2
        assert all(isinstance(star, UnifiedStarCatalog) for star in results)
    
    def test_repository_search_bounding_box_for_cone(self, db_session: Session, sample_stars):
        """Test repository method for cone search pre-filtering."""
        repo = StarCatalogRepository(db_session)
        
        # Get bounding box around RA=200, Dec=0
        results = repo.search_bounding_box_for_cone(
            ra_min=195.0,
            ra_max=205.0,
            dec_min=-5.0,
            dec_max=5.0,
            limit=100
        )
        
        # Should get all stars in the box
        assert len(results) >= 3
        assert all(
            195.0 <= star.ra_deg <= 205.0 and
            -5.0 <= star.dec_deg <= 5.0
            for star in results
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
