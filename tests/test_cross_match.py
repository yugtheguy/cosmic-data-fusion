"""
Simplified tests for Cross-Match Service.

Tests the positional cross-matching functionality that identifies the same
physical star across multiple catalogs using the Union-Find algorithm.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, UnifiedStarCatalog
from app.services.harmonizer import CrossMatchService


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def cross_match_service(db_session):
    """Create CrossMatchService instance."""
    return CrossMatchService(db_session)


def make_star(source_id, ra, dec, mag, source="test"):
    """Helper to create a star with all required fields."""
    return UnifiedStarCatalog(
        source_id=source_id,
        ra_deg=ra,
        dec_deg=dec,
        brightness_mag=mag,
        dataset_id="test",
        original_source=source,
        raw_frame="ICRS"
    )


class TestBasicMatching:
    """Test basic cross-matching functionality."""
    
    def test_no_matches_far_apart(self, db_session, cross_match_service):
        """Test stars far apart don't match."""
        stars = [
            make_star("star1", 10.0, 20.0, 12.0),
            make_star("star2", 100.0, 20.0, 13.0),  # 90 degrees away
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = cross_match_service.perform_cross_match(radius_arcsec=2.0)
        
        assert result["total_stars"] == 2
        assert result["isolated_stars"] == 2
        assert result["groups_created"] == 0
    
    def test_single_match_pair(self, db_session, cross_match_service):
        """Test two nearby stars match."""
        stars = [
            make_star("gaia_1", 180.0, 45.0, 12.0, "Gaia"),
            make_star("sdss_1", 180.00027778, 45.00027778, 12.5, "SDSS"),  # ~1 arcsec away
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = cross_match_service.perform_cross_match(radius_arcsec=2.0)
        
        assert result["total_stars"] == 2
        assert result["groups_created"] == 1
        assert result["stars_in_groups"] == 2
        
        # Check both have same fusion_group_id
        stars_db = db_session.query(UnifiedStarCatalog).all()
        fusion_ids = [s.fusion_group_id for s in stars_db]
        assert all(fid is not None for fid in fusion_ids)
        assert fusion_ids[0] == fusion_ids[1]
    
    def test_transitive_matching(self, db_session, cross_match_service):
        """Test chain matching: A matches B, B matches C => all in same group."""
        stars = [
            make_star("star_a", 180.0, 45.0, 12.0),
            make_star("star_b", 180.00027778, 45.0, 12.1),  # ~1 arcsec from A
            make_star("star_c", 180.00055556, 45.0, 12.2),  # ~2 arcsec from A, ~1 arcsec from B
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = cross_match_service.perform_cross_match(radius_arcsec=2.0)
        
        assert result["total_stars"] == 3
        assert result["groups_created"] >= 1
        
        # All three should be in same fusion group
        stars_db = db_session.query(UnifiedStarCatalog).all()
        fusion_ids = [s.fusion_group_id for s in stars_db if s.fusion_group_id]
        assert len(set(fusion_ids)) == 1


class TestMatchingRadius:
    """Test different matching radii."""
    
    def test_tight_radius(self, db_session, cross_match_service):
        """Test tight radius (1 arcsec)."""
        stars = [
            make_star("s1", 180.0, 45.0, 12.0),
            make_star("s2", 180.00027778, 45.0, 12.1),  # ~1 arcsec
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = cross_match_service.perform_cross_match(radius_arcsec=1.0)
        
        # Should match with 1 arcsec radius
        assert result["groups_created"] >= 1
    
    def test_wide_radius(self, db_session, cross_match_service):
        """Test wide radius (5 arcsec)."""
        stars = [
            make_star("s1", 180.0, 45.0, 12.0),
            make_star("s2", 180.00138889, 45.0, 12.1),  # ~5 arcsec
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = cross_match_service.perform_cross_match(radius_arcsec=5.0)
        
        # Should match with wide radius
        assert result["groups_created"] >= 1


class TestFusionGroups:
    """Test fusion group management."""
    
    def test_fusion_group_retrieval(self, db_session, cross_match_service):
        """Test retrieving stars in a fusion group."""
        stars = [
            make_star("s1", 180.0, 45.0, 12.0),
            make_star("s2", 180.00027778, 45.0, 12.1),
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        cross_match_service.perform_cross_match(radius_arcsec=2.0)
        
        # Get fusion group ID
        star = db_session.query(UnifiedStarCatalog).first()
        fusion_id = star.fusion_group_id
        
        # Retrieve group
        group_stars = cross_match_service.get_fusion_group(fusion_id)
        
        assert len(group_stars) == 2
    
    def test_statistics(self, db_session, cross_match_service):
        """Test cross-match statistics."""
        stars = [
            # Group 1
            make_star("g1_a", 10.0, 20.0, 12.0),
            make_star("g1_b", 10.00027778, 20.0, 12.1),
            # Group 2
            make_star("g2_a", 100.0, -30.0, 13.0),
            make_star("g2_b", 100.00027778, -30.0, 13.1),
            # Isolated
            make_star("solo", 200.0, 50.0, 14.0),
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        cross_match_service.perform_cross_match(radius_arcsec=2.0)
        
        stats = cross_match_service.get_cross_match_statistics()
        
        assert stats["total_stars"] == 5
        assert stats["unique_fusion_groups"] == 2
        assert stats["stars_in_fusion_groups"] == 4
        assert stats["isolated_stars"] == 1


class TestEdgeCases:
    """Test edge cases."""
    
    def test_empty_catalog(self, cross_match_service):
        """Test with no stars."""
        result = cross_match_service.perform_cross_match(radius_arcsec=2.0)
        
        assert result["total_stars"] == 0
        assert result["groups_created"] == 0
    
    def test_single_star(self, db_session, cross_match_service):
        """Test with one star."""
        db_session.add(make_star("solo", 180.0, 45.0, 12.0))
        db_session.commit()
        
        result = cross_match_service.perform_cross_match(radius_arcsec=2.0)
        
        assert result["total_stars"] == 1
        assert result["groups_created"] == 0
        assert result["isolated_stars"] == 1
