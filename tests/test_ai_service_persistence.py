"""
Stage 3 Test: AI Service Result Persistence
Tests that AI Discovery Service saves results to database when requested.
"""
import pytest
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.models import UnifiedStarCatalog
from app.services.ai_discovery import AIDiscoveryService
from app.repository.discovery import DiscoveryRepository


@pytest.fixture(scope="module")
def setup_database():
    """Create all tables before tests."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session(setup_database):
    """Provide a database session for each test."""
    db = next(get_db())
    yield db
    db.close()


@pytest.fixture
def ai_service(db_session):
    """Provide an AIDiscoveryService instance."""
    return AIDiscoveryService(db_session)


@pytest.fixture
def repository(db_session):
    """Provide a DiscoveryRepository instance."""
    return DiscoveryRepository(db_session)


@pytest.fixture
def sample_stars(db_session):
    """Create sample stars with varied properties for ML analysis."""
    stars = []
    
    # Create 30 normal stars
    for i in range(30):
        stars.append(UnifiedStarCatalog(
            original_source="Test",
            source_id=f"ai_test_normal_{i}",
            ra_deg=180.0 + i * 0.5,
            dec_deg=45.0 + i * 0.3,
            brightness_mag=12.0 + i * 0.1,
            parallax_mas=5.0 + i * 0.2,
            raw_frame="ICRS"
        ))
    
    # Create 5 anomalous stars (very different properties)
    for i in range(5):
        stars.append(UnifiedStarCatalog(
            original_source="Test",
            source_id=f"ai_test_anomaly_{i}",
            ra_deg=50.0 + i * 10,
            dec_deg=-30.0 + i * 5,
            brightness_mag=20.0 + i,
            parallax_mas=50.0 + i * 10,
            raw_frame="ICRS"
        ))
    
    db_session.add_all(stars)
    db_session.commit()
    return stars


def test_anomaly_detection_without_save(ai_service, sample_stars):
    """Test that anomaly detection works without saving (baseline test)."""
    # Load data and run detection
    ai_service.load_data()
    anomalies = ai_service.detect_anomalies(
        contamination=0.1,
        random_state=42,
        save_results=False
    )
    
    # Should find some anomalies
    assert len(anomalies) > 0
    assert all("anomaly_score" in a for a in anomalies)
    
    print(f"✅ Detected {len(anomalies)} anomalies without saving")


def test_anomaly_detection_with_save(ai_service, repository, sample_stars):
    """Test that anomaly detection saves results when requested."""
    # Load data and run detection with save=True
    ai_service.load_data()
    anomalies = ai_service.detect_anomalies(
        contamination=0.15,
        random_state=42,
        save_results=True,
        dataset_filter={"magnitude_min": 10.0, "magnitude_max": 25.0}
    )
    
    # Should still return anomalies
    assert len(anomalies) > 0
    
    # Verify a discovery run was created
    runs = repository.list_discovery_runs(run_type="anomaly", limit=10)
    assert len(runs) > 0
    
    # Get the most recent run
    latest_run = runs[0]
    assert latest_run.run_type == "anomaly"
    assert latest_run.parameters["contamination"] == 0.15
    assert latest_run.parameters["algorithm"] == "IsolationForest"
    assert latest_run.total_stars >= len(sample_stars)  # May include stars from other tests
    assert latest_run.results_summary["n_anomalies"] == len(anomalies)
    
    # Verify results were saved for all analyzed stars
    results_count = repository.count_results_by_run_id(latest_run.run_id)
    assert results_count == latest_run.total_stars
    
    # Verify anomaly count matches
    anomaly_count = repository.count_anomalies_by_run_id(latest_run.run_id)
    assert anomaly_count == len(anomalies)
    
    print(f"✅ Saved {len(anomalies)} anomalies in run {latest_run.run_id}")


def test_anomaly_detection_results_retrievable(ai_service, repository, sample_stars):
    """Test that saved anomaly results can be retrieved with star data."""
    # Run detection with save
    ai_service.load_data()
    anomalies = ai_service.detect_anomalies(
        contamination=0.1,
        random_state=123,
        save_results=True
    )
    
    # Get latest run
    runs = repository.list_discovery_runs(run_type="anomaly", limit=1)
    run = runs[0]
    
    # Retrieve results with star data
    enriched_results = repository.get_results_with_star_data(
        run.run_id,
        anomalies_only=True,
        limit=len(anomalies)  # Get all anomalies
    )
    
    # Should have enriched results for all anomalies
    assert len(enriched_results) == len(anomalies)
    
    # Verify structure
    for result in enriched_results:
        assert result["is_anomaly"] is True
        assert result["anomaly_score"] is not None
        assert result["anomaly_score"] < 0  # Anomalies have negative scores
        assert "star" in result
        assert result["star"]["ra_deg"] is not None
        assert result["star"]["dec_deg"] is not None
        assert result["star"]["brightness_mag"] is not None
    
    print(f"✅ Retrieved {len(enriched_results)} enriched anomaly results")


def test_clustering_without_save(ai_service, sample_stars):
    """Test that clustering works without saving (baseline test)."""
    # Load data and run clustering
    ai_service.load_data()
    result = ai_service.detect_clusters(
        eps=0.5,
        min_samples=3,
        save_results=False
    )
    
    # Should find some clusters
    assert result["n_clusters"] >= 0
    assert result["total_stars"] >= len(sample_stars)  # May include stars from other tests
    assert "clusters" in result
    
    print(f"✅ Found {result['n_clusters']} clusters without saving")


def test_clustering_with_save(ai_service, repository, sample_stars):
    """Test that clustering saves results when requested."""
    # Load data and run clustering with save=True
    ai_service.load_data()
    result = ai_service.detect_clusters(
        eps=0.8,
        min_samples=5,
        use_position_and_magnitude=True,
        save_results=True,
        dataset_filter={"ra_min": 0, "ra_max": 360}
    )
    
    # Should return clustering results
    assert result["n_clusters"] >= 0
    
    # Verify a discovery run was created
    runs = repository.list_discovery_runs(run_type="cluster", limit=10)
    assert len(runs) > 0
    
    # Get the most recent run
    latest_run = runs[0]
    assert latest_run.run_type == "cluster"
    assert latest_run.parameters["eps"] == 0.8
    assert latest_run.parameters["min_samples"] == 5
    assert latest_run.parameters["algorithm"] == "DBSCAN"
    assert latest_run.total_stars >= len(sample_stars)  # May include stars from other tests
    assert latest_run.results_summary["n_clusters"] == result["n_clusters"]
    assert latest_run.results_summary["n_noise"] == result["n_noise"]
    
    # Verify results were saved for all analyzed stars
    results_count = repository.count_results_by_run_id(latest_run.run_id)
    assert results_count == latest_run.total_stars
    
    print(f"✅ Saved clustering with {result['n_clusters']} clusters in run {latest_run.run_id}")


def test_clustering_results_by_cluster_id(ai_service, repository, sample_stars):
    """Test that saved clustering results can be queried by cluster_id."""
    # Run clustering with save
    ai_service.load_data()
    result = ai_service.detect_clusters(
        eps=0.7,
        min_samples=3,
        save_results=True
    )
    
    # Get latest run
    runs = repository.list_discovery_runs(run_type="cluster", limit=1)
    run = runs[0]
    
    # If we found any clusters, verify we can query their members
    if result["n_clusters"] > 0:
        # Get expected size first to set appropriate limit
        expected_size = result["cluster_stats"]["cluster_0"]["count"]
        
        # Get members of cluster 0 with sufficient limit
        cluster_0_members = repository.get_cluster_members(run.run_id, cluster_id=0, limit=expected_size)
        
        # Should have members in cluster 0
        assert len(cluster_0_members) > 0
        assert all(r.cluster_id == 0 for r in cluster_0_members)
        
        # Verify cluster size matches the result
        assert len(cluster_0_members) == expected_size
        
        print(f"✅ Retrieved {len(cluster_0_members)} stars from cluster 0")
    else:
        print("✅ No clusters found (all noise) - this is valid")


def test_multiple_runs_tracked_separately(ai_service, repository, sample_stars):
    """Test that multiple discovery runs are tracked separately."""
    ai_service.load_data()
    
    # Run anomaly detection twice with different parameters
    ai_service.detect_anomalies(contamination=0.05, random_state=1, save_results=True)
    ai_service.detect_anomalies(contamination=0.15, random_state=2, save_results=True)
    
    # Run clustering twice with different parameters
    ai_service.detect_clusters(eps=0.5, min_samples=3, save_results=True)
    ai_service.detect_clusters(eps=1.0, min_samples=10, save_results=True)
    
    # Verify all 4 runs were saved
    all_runs = repository.list_discovery_runs(limit=10)
    assert len(all_runs) >= 4
    
    # Verify runs have different parameters
    anomaly_runs = repository.list_discovery_runs(run_type="anomaly", limit=10)
    assert len(anomaly_runs) >= 2
    
    cluster_runs = repository.list_discovery_runs(run_type="cluster", limit=10)
    assert len(cluster_runs) >= 2
    
    # Verify each run has unique run_id
    run_ids = [r.run_id for r in all_runs]
    assert len(run_ids) == len(set(run_ids))  # All unique
    
    print(f"✅ Tracked {len(all_runs)} separate discovery runs")


def test_dataset_filter_preserved(ai_service, repository, sample_stars):
    """Test that dataset filters are preserved in saved runs."""
    ai_service.load_data()
    
    # Run with specific filters
    filters = {
        "magnitude_min": 10.0,
        "magnitude_max": 20.0,
        "parallax_min": 1.0
    }
    
    ai_service.detect_anomalies(
        contamination=0.1,
        save_results=True,
        dataset_filter=filters
    )
    
    # Retrieve run
    runs = repository.list_discovery_runs(run_type="anomaly", limit=1)
    run = runs[0]
    
    # Verify filters were saved
    assert run.dataset_filter is not None
    assert run.dataset_filter["magnitude_min"] == 10.0
    assert run.dataset_filter["magnitude_max"] == 20.0
    assert run.dataset_filter["parallax_min"] == 1.0
    
    print(f"✅ Dataset filter preserved in run {run.run_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
