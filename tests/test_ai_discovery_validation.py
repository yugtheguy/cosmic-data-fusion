"""
Stage 1A: Scientific Validation Edge Case Tests for AI Discovery Service.

Tests edge cases, error handling, and robustness of anomaly detection and clustering.
"""

import pytest
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, UnifiedStarCatalog
from app.services.ai_discovery import AIDiscoveryService, InsufficientDataError


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
def ai_service(db_session):
    """Create AIDiscoveryService instance."""
    return AIDiscoveryService(db_session)


def make_star(source_id, ra, dec, mag, parallax=None):
    """Helper to create a star with all required fields."""
    return UnifiedStarCatalog(
        source_id=source_id,
        ra_deg=ra,
        dec_deg=dec,
        brightness_mag=mag,
        parallax_mas=parallax,
        dataset_id="test",
        original_source="test",
        raw_frame="ICRS"
    )


class TestInsufficientData:
    """Test handling of insufficient data scenarios."""
    
    def test_empty_catalog(self, ai_service):
        """Test with completely empty catalog."""
        with pytest.raises(InsufficientDataError, match="Found 0 stars"):
            ai_service.detect_anomalies()
    
    def test_too_few_stars(self, db_session, ai_service):
        """Test with fewer than MIN_STARS_FOR_ANALYSIS (5) stars."""
        # Add only 3 stars
        stars = [
            make_star(f"s{i}", 180.0 + i, 45.0, 12.0 + i, 5.0)
            for i in range(3)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        with pytest.raises(InsufficientDataError, match="need at least 5"):
            ai_service.detect_anomalies()
    
    def test_minimum_stars_accepted(self, db_session, ai_service):
        """Test with exactly MIN_STARS_FOR_ANALYSIS (5) stars."""
        stars = [
            make_star(f"s{i}", 180.0 + i, 45.0, 12.0 + i * 0.5, 5.0)
            for i in range(5)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        # Should work with 5 stars
        result = ai_service.detect_anomalies(contamination=0.2)
        assert isinstance(result, list)


class TestMissingData:
    """Test handling of missing/NULL values."""
    
    def test_all_null_parallax(self, db_session, ai_service):
        """Test with all stars having NULL parallax."""
        stars = [
            make_star(f"s{i}", 180.0 + i * 10, 45.0 + i * 5, 12.0 + i, parallax=None)
            for i in range(10)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        # Should handle NULLs gracefully (fill with 0.0)
        result = ai_service.detect_anomalies()
        assert isinstance(result, list)
    
    def test_mixed_null_parallax(self, db_session, ai_service):
        """Test with some stars having NULL parallax."""
        stars = [
            make_star(f"s{i}", 180.0 + i * 10, 45.0, 12.0, 5.0 if i % 2 == 0 else None)
            for i in range(10)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = ai_service.detect_anomalies()
        assert isinstance(result, list)


class TestConstantValues:
    """Test handling of constant-value columns (no variance)."""
    
    def test_constant_magnitude(self, db_session, ai_service):
        """Test with all stars having same magnitude."""
        stars = [
            make_star(f"s{i}", 180.0 + i * 10, 45.0 + i * 5, 12.0, 5.0)  # Same mag
            for i in range(10)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        # Should handle zero-variance features
        result = ai_service.detect_anomalies()
        assert isinstance(result, list)
    
    def test_all_same_coordinates(self, db_session, ai_service):
        """Test with all stars at same position."""
        stars = [
            make_star(f"s{i}", 180.0, 45.0, 12.0 + i * 0.5, 5.0)  # Same RA/Dec
            for i in range(10)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = ai_service.detect_anomalies()
        assert isinstance(result, list)


class TestAnomalyDetectionParameters:
    """Test anomaly detection with various parameters."""
    
    def test_low_contamination(self, db_session, ai_service):
        """Test with very low contamination rate (1%)."""
        stars = [
            make_star(f"s{i}", 180.0 + i, 45.0, 12.0 + np.sin(i) * 2, 5.0)
            for i in range(100)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = ai_service.detect_anomalies(contamination=0.01)
        
        # Should find ~1 anomaly
        assert len(result) <= 5
        assert all("anomaly_score" in item for item in result)
    
    def test_high_contamination(self, db_session, ai_service):
        """Test with high contamination rate (50%)."""
        stars = [
            make_star(f"s{i}", 180.0 + i, 45.0, 12.0 + i * 0.1, 5.0)
            for i in range(20)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = ai_service.detect_anomalies(contamination=0.5)
        
        # Should find ~10 anomalies
        assert len(result) >= 5
        assert len(result) <= 15
    
    def test_anomaly_scores_sorted(self, db_session, ai_service):
        """Test that anomalies are sorted by score (most anomalous first)."""
        stars = [
            make_star(f"s{i}", 180.0 + i * 2, 45.0, 12.0 + i * 0.3, 5.0)
            for i in range(50)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = ai_service.detect_anomalies(contamination=0.1)
        
        if len(result) > 1:
            scores = [item["anomaly_score"] for item in result]
            # Scores should be in ascending order (most negative first)
            assert scores == sorted(scores)


class TestClusteringParameters:
    """Test clustering with various parameters."""
    
    def test_tight_clustering(self, db_session, ai_service):
        """Test with very tight eps (small clusters)."""
        # Create two obvious clusters
        cluster1 = [make_star(f"c1_{i}", 10.0 + i * 0.1, 20.0, 12.0, 5.0) for i in range(5)]
        cluster2 = [make_star(f"c2_{i}", 100.0 + i * 0.1, -20.0, 13.0, 5.0) for i in range(5)]
        
        db_session.bulk_save_objects(cluster1 + cluster2)
        db_session.commit()
        
        result = ai_service.detect_clusters(eps=0.5, min_samples=3)
        
        assert result["n_clusters"] >= 0  # May or may not find clusters with tight eps
        assert "cluster_stats" in result
    
    def test_wide_clustering(self, db_session, ai_service):
        """Test with wide eps (large clusters)."""
        stars = [
            make_star(f"s{i}", 180.0 + i * 5, 45.0, 12.0, 5.0)
            for i in range(20)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = ai_service.detect_clusters(eps=10.0, min_samples=5)
        
        assert result["n_clusters"] >= 0
        assert result["n_noise"] >= 0
    
    def test_minimum_samples_edge_case(self, db_session, ai_service):
        """Test with min_samples=1 (every point is a cluster)."""
        stars = [
            make_star(f"s{i}", 180.0 + i * 50, 45.0, 12.0, 5.0)
            for i in range(10)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = ai_service.detect_clusters(eps=1.0, min_samples=1)
        
        # With min_samples=1, DBSCAN may create many small clusters
        assert isinstance(result, dict)
        assert "n_clusters" in result


class TestDataQuality:
    """Test with realistic data quality issues."""
    
    def test_outlier_detection(self, db_session, ai_service):
        """Test detection of obvious outliers."""
        # Normal stars + one clear outlier
        normal_stars = [
            make_star(f"normal{i}", 180.0 + i * 0.5, 45.0, 12.0, 5.0)
            for i in range(50)
        ]
        outlier = make_star("outlier", 180.0, 45.0, 25.0, 5.0)  # Much fainter
        
        db_session.bulk_save_objects(normal_stars + [outlier])
        db_session.commit()
        
        result = ai_service.detect_anomalies(contamination=0.05)
        
        # Outlier should be in anomaly list
        assert len(result) > 0
        anomaly_ids = [item["source_id"] for item in result]
        assert "outlier" in anomaly_ids
    
    def test_extreme_coordinates(self, db_session, ai_service):
        """Test with coordinates at boundaries."""
        stars = [
            make_star("near_pole", 0.0, 89.5, 12.0, 5.0),
            make_star("equator", 180.0, 0.0, 12.0, 5.0),
            make_star("ra_wrap", 359.9, 45.0, 12.0, 5.0),
        ] + [
            make_star(f"normal{i}", 180.0 + i, 45.0, 12.0, 5.0)
            for i in range(10)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = ai_service.detect_anomalies()
        assert isinstance(result, list)


class TestInsightsGeneration:
    """Test summary insights generation."""
    
    def test_insights_with_normal_data(self, db_session, ai_service):
        """Test insights generation with typical dataset."""
        stars = [
            make_star(f"s{i}", 180.0 + i * 2, 45.0 + i * 0.5, 12.0 + i * 0.2, 5.0)
            for i in range(50)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        insights = ai_service.get_summary_insights()
        
        assert "summary" in insights
        assert "total_stars" in insights
        assert insights["total_stars"] == 50
        assert "anomaly_count" in insights
        assert "cluster_count" in insights
        assert "recommendations" in insights
        assert isinstance(insights["recommendations"], list)
    
    def test_insights_structure(self, db_session, ai_service):
        """Test that insights have all required fields."""
        stars = [
            make_star(f"s{i}", 180.0 + i * 5, 45.0, 12.0, 5.0)
            for i in range(20)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        insights = ai_service.get_summary_insights()
        
        required_fields = [
            "summary", "total_stars", "anomaly_count",
            "cluster_count", "noise_count", "recommendations"
        ]
        for field in required_fields:
            assert field in insights, f"Missing required field: {field}"


class TestResultFormats:
    """Test that results have correct formats."""
    
    def test_anomaly_result_structure(self, db_session, ai_service):
        """Test anomaly detection result structure."""
        stars = [
            make_star(f"s{i}", 180.0 + i, 45.0, 12.0 + i * 0.1, 5.0)
            for i in range(20)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = ai_service.detect_anomalies(contamination=0.1)
        
        assert isinstance(result, list)
        if len(result) > 0:
            item = result[0]
            assert "id" in item
            assert "source_id" in item
            assert "ra_deg" in item
            assert "dec_deg" in item
            assert "brightness_mag" in item
            assert "anomaly_score" in item
            assert isinstance(item["anomaly_score"], (int, float))
    
    def test_clustering_result_structure(self, db_session, ai_service):
        """Test clustering result structure."""
        stars = [
            make_star(f"s{i}", 180.0 + i * 2, 45.0, 12.0, 5.0)
            for i in range(30)
        ]
        db_session.bulk_save_objects(stars)
        db_session.commit()
        
        result = ai_service.detect_clusters(eps=2.0, min_samples=5)
        
        assert isinstance(result, dict)
        assert "n_clusters" in result
        assert "n_noise" in result
        assert "cluster_stats" in result
        assert isinstance(result["cluster_stats"], dict)
