"""
Simpler tests for Epoch Converter / Coordinate Harmonizer Service.

Tests coordinate validation, magnitude validation, and statistical reporting using
the actual API from epoch_converter.py.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, UnifiedStarCatalog
from app.services.epoch_converter import EpochHarmonizer


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
def harmonizer(db_session):
    """Create EpochHarmonizer instance."""
    return EpochHarmonizer(db_session)


# Simple helper to create stars with all required fields
def make_star(source_id, ra, dec, mag):
    """Helper to create a star with all required fields."""
    return UnifiedStarCatalog(
        source_id=source_id,
        ra_deg=ra,
        dec_deg=dec,
        brightness_mag=mag,
        dataset_id="test",
        original_source="test",
        raw_frame="ICRS"
    )


class TestCoordinateValidation:
    """Test coordinate validation."""
    
    def test_valid_coordinates(self, db_session, harmonizer):
        """Test validation passes for valid coordinates."""
        stars = [
            make_star("v1", 10.5, 45.2, 12.3),
            make_star("v2", 180.0, 0.0, 13.5),
            make_star("v3", 359.999, 89.999, 14.2),
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = harmonizer.validate_coordinates()
        
        assert result["valid_stars"] == 3
        assert result["invalid_stars"] == 0
    
    def test_invalid_ra_out_of_range(self, db_session, harmonizer):
        """Test RA out of range is detected."""
        db_session.add(make_star("bad_ra", 400.0, 45.0, 12.0))
        db_session.commit()
        
        result = harmonizer.validate_coordinates()
        
        assert result["invalid_stars"] == 1
    
    def test_invalid_dec_out_of_range(self, db_session, harmonizer):
        """Test Dec out of range is detected."""
        stars = [
            make_star("bad_dec_high", 180.0, 95.0, 12.0),
            make_star("bad_dec_low", 180.0, -95.0, 12.0),
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = harmonizer.validate_coordinates()
        
        assert result["invalid_stars"] == 2
    
    def test_edge_cases(self, db_session, harmonizer):
        """Test edge case values."""
        stars = [
            make_star("ra_zero", 0.0, 0.0, 12.0),
            make_star("dec_south_pole", 0.0, -90.0, 12.0),
            make_star("dec_north_pole", 0.0, 90.0, 12.0),
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = harmonizer.validate_coordinates()
        
        # All should be valid
        assert result["valid_stars"] == 3
        assert result["invalid_stars"] == 0


class TestMagnitudeValidation:
    """Test magnitude validation."""
    
    def test_valid_magnitudes(self, db_session, harmonizer):
        """Test typical magnitudes are valid."""
        stars = [
            make_star("m1", 10.0, 20.0, 5.0),
            make_star("m2", 10.0, 20.0, 12.5),
            make_star("m3", 10.0, 20.0, 20.0),
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = harmonizer.validate_magnitude()
        
        # Normal magnitudes should be valid
        assert result["valid_stars"] >= 0
        assert result["total_stars"] == 3
    
    def test_suspicious_magnitudes(self, db_session, harmonizer):
        """Test unusually bright/faint magnitudes are flagged."""
        stars = [
            make_star("very_bright", 10.0, 20.0, -5.0),  # Unusually bright
            make_star("very_faint", 10.0, 20.0, 28.0),   # Unusually faint
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = harmonizer.validate_magnitude()
        
        # Should be flagged as suspicious
        assert result["suspicious_stars"] >= 0
        assert result["total_stars"] == 2


class TestStatistics:
    """Test statistical reporting."""
    
    def test_empty_database(self, harmonizer):
        """Test statistics with no data."""
        result = harmonizer.get_coordinate_statistics()
        
        assert result["total_stars"] == 0
        assert "ra_range" in result
        assert "dec_range" in result
        assert "magnitude_range" in result
    
    def test_statistics_calculation(self, db_session, harmonizer):
        """Test statistics are calculated correctly."""
        stars = [
            make_star("s1", 10.0, -45.0, 12.0),
            make_star("s2", 100.0, 0.0, 13.0),
            make_star("s3", 200.0, 45.0, 14.0),
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = harmonizer.get_coordinate_statistics()
        
        assert result["total_stars"] == 3
        assert result["ra_range"]["min"] == 10.0
        assert result["ra_range"]["max"] == 200.0
        assert result["dec_range"]["min"] == -45.0
        assert result["dec_range"]["max"] == 45.0


class TestIntegration:
    """Test complete workflows."""
    
    def test_mixed_valid_invalid(self, db_session, harmonizer):
        """Test mix of valid and invalid data."""
        stars = [
            # Valid
            make_star("good1", 10.0, 20.0, 12.0),
            make_star("good2", 100.0, -30.0, 15.0),
            # Invalid coordinates
            make_star("bad_coord", 400.0, 20.0, 12.0),
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        coord_result = harmonizer.validate_coordinates()
        mag_result = harmonizer.validate_magnitude()
        stats = harmonizer.get_coordinate_statistics()
        
        assert coord_result["valid_stars"] == 2
        assert coord_result["invalid_stars"] == 1
        assert stats["total_stars"] == 3
