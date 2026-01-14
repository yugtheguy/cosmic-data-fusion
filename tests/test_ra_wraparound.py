"""
Test RA=0° wraparound handling in bounding box searches.

Verifies that searches crossing the RA=0°/360° boundary work correctly.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, UnifiedStarCatalog
from app.repository.star_catalog import StarCatalogRepository


@pytest.fixture
def test_db():
    """Create in-memory test database with stars near RA=0°."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    
    db = TestingSessionLocal()
    
    # Add stars around RA=0° boundary
    test_stars = [
        # Stars near RA=0° (low RA)
        UnifiedStarCatalog(
            source_id="WRAP_STAR_1",
            ra_deg=1.0,  # Just past 0°
            dec_deg=10.0,
            brightness_mag=5.0,
            parallax_mas=50.0,
            distance_pc=20.0,
            original_source="Test",
            raw_frame="ICRS"
        ),
        UnifiedStarCatalog(
            source_id="WRAP_STAR_2",
            ra_deg=5.0,
            dec_deg=15.0,
            brightness_mag=6.0,
            parallax_mas=40.0,
            distance_pc=25.0,
            original_source="Test",
            raw_frame="ICRS"
        ),
        # Stars near RA=360° (high RA)
        UnifiedStarCatalog(
            source_id="WRAP_STAR_3",
            ra_deg=355.0,
            dec_deg=10.0,
            brightness_mag=7.0,
            parallax_mas=30.0,
            distance_pc=33.3,
            original_source="Test",
            raw_frame="ICRS"
        ),
        UnifiedStarCatalog(
            source_id="WRAP_STAR_4",
            ra_deg=359.0,
            dec_deg=15.0,
            brightness_mag=8.0,
            parallax_mas=25.0,
            distance_pc=40.0,
            original_source="Test",
            raw_frame="ICRS"
        ),
        # Star far from boundary (control)
        UnifiedStarCatalog(
            source_id="CONTROL_STAR",
            ra_deg=180.0,
            dec_deg=0.0,
            brightness_mag=10.0,
            parallax_mas=10.0,
            distance_pc=100.0,
            original_source="Test",
            raw_frame="ICRS"
        ),
    ]
    
    db.add_all(test_stars)
    db.commit()
    
    yield db
    
    db.close()


def test_wraparound_basic(test_db):
    """Test basic RA wraparound detection."""
    repo = StarCatalogRepository(test_db)
    
    # Search from RA=355° to RA=5° (crosses 0°)
    results = repo.search_bounding_box(
        ra_min=355.0,
        ra_max=5.0,
        dec_min=5.0,
        dec_max=20.0,
        limit=100
    )
    
    # Should find WRAP_STAR_3, WRAP_STAR_4 (355°, 359°) and WRAP_STAR_1, WRAP_STAR_2 (1°, 5°)
    assert len(results) == 4
    
    source_ids = {star.source_id for star in results}
    assert "WRAP_STAR_1" in source_ids  # RA=1°
    assert "WRAP_STAR_2" in source_ids  # RA=5°
    assert "WRAP_STAR_3" in source_ids  # RA=355°
    assert "WRAP_STAR_4" in source_ids  # RA=359°
    assert "CONTROL_STAR" not in source_ids  # RA=180° (outside range)


def test_wraparound_narrow_window(test_db):
    """Test wraparound with narrow RA window."""
    repo = StarCatalogRepository(test_db)
    
    # Search from RA=358° to RA=2° (narrow window around 0°)
    results = repo.search_bounding_box(
        ra_min=358.0,
        ra_max=2.0,
        dec_min=0.0,
        dec_max=20.0,
        limit=100
    )
    
    # Should find WRAP_STAR_4 (359°) and WRAP_STAR_1 (1°)
    assert len(results) == 2
    
    source_ids = {star.source_id for star in results}
    assert "WRAP_STAR_1" in source_ids  # RA=1°
    assert "WRAP_STAR_4" in source_ids  # RA=359°


def test_no_wraparound(test_db):
    """Test normal search without wraparound."""
    repo = StarCatalogRepository(test_db)
    
    # Normal search: RA=0° to RA=10° (no wraparound)
    results = repo.search_bounding_box(
        ra_min=0.0,
        ra_max=10.0,
        dec_min=0.0,
        dec_max=20.0,
        limit=100
    )
    
    # Should find WRAP_STAR_1 (1°) and WRAP_STAR_2 (5°)
    assert len(results) == 2
    
    source_ids = {star.source_id for star in results}
    assert "WRAP_STAR_1" in source_ids
    assert "WRAP_STAR_2" in source_ids
    assert "WRAP_STAR_3" not in source_ids  # RA=355° (outside range)
    assert "WRAP_STAR_4" not in source_ids  # RA=359° (outside range)


def test_wraparound_respects_dec_filter(test_db):
    """Test that wraparound search still respects Dec filter."""
    repo = StarCatalogRepository(test_db)
    
    # Search with Dec filter that excludes some stars
    results = repo.search_bounding_box(
        ra_min=355.0,
        ra_max=5.0,
        dec_min=12.0,  # Only stars with Dec >= 12°
        dec_max=20.0,
        limit=100
    )
    
    # Should find only stars with Dec >= 12°
    # WRAP_STAR_2 (Dec=15°) and WRAP_STAR_4 (Dec=15°)
    assert len(results) == 2
    
    source_ids = {star.source_id for star in results}
    assert "WRAP_STAR_2" in source_ids  # Dec=15°
    assert "WRAP_STAR_4" in source_ids  # Dec=15°
    assert "WRAP_STAR_1" not in source_ids  # Dec=10° (too low)
    assert "WRAP_STAR_3" not in source_ids  # Dec=10° (too low)


def test_wraparound_respects_limit(test_db):
    """Test that wraparound search respects limit parameter."""
    repo = StarCatalogRepository(test_db)
    
    # Search with limit=2
    results = repo.search_bounding_box(
        ra_min=355.0,
        ra_max=5.0,
        dec_min=0.0,
        dec_max=20.0,
        limit=2
    )
    
    # Should return at most 2 results
    assert len(results) <= 2
    
    # All returned stars should be in the correct RA range
    for star in results:
        assert star.ra_deg >= 355.0 or star.ra_deg <= 5.0


def test_full_sky_search(test_db):
    """Test search covering entire sky (RA=0° to 360°)."""
    repo = StarCatalogRepository(test_db)
    
    # Full sky search
    results = repo.search_bounding_box(
        ra_min=0.0,
        ra_max=360.0,
        dec_min=-90.0,
        dec_max=90.0,
        limit=100
    )
    
    # Should find all stars (5 total)
    assert len(results) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
