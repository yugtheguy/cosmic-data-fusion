"""
Stage 2 Test: Discovery Repository Layer
Tests CRUD operations for discovery runs and results.
"""
import pytest
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.models import UnifiedStarCatalog
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
def repository(db_session):
    """Provide a DiscoveryRepository instance."""
    return DiscoveryRepository(db_session)


@pytest.fixture
def sample_stars(db_session):
    """Create sample stars for testing."""
    stars = [
        UnifiedStarCatalog(
            original_source="Test",
            source_id=f"repo_test_star_{i}",
            ra_deg=float(i * 10),
            dec_deg=float(i * 5),
            brightness_mag=12.0 + i * 0.5,
            raw_frame="ICRS"
        )
        for i in range(10)
    ]
    db_session.add_all(stars)
    db_session.commit()
    return stars


def test_save_discovery_run(repository):
    """Test saving a discovery run."""
    run = repository.save_discovery_run(
        run_type="anomaly",
        parameters={"contamination": 0.05, "random_state": 42},
        dataset_filter={"magnitude_min": 10.0, "magnitude_max": 15.0},
        total_stars=500,
        results_summary={"n_anomalies": 25, "mean_score": -0.12}
    )
    
    assert run.id is not None
    assert run.run_id is not None
    assert len(run.run_id) == 36  # UUID format
    assert run.run_type == "anomaly"
    assert run.parameters["contamination"] == 0.05
    assert run.total_stars == 500
    assert run.results_summary["n_anomalies"] == 25
    assert run.created_at is not None
    
    print(f"✅ Saved discovery run: {run.run_id}")


def test_get_discovery_run(repository):
    """Test retrieving a discovery run by ID."""
    # Create a run
    created_run = repository.save_discovery_run(
        run_type="cluster",
        parameters={"eps": 0.5, "min_samples": 5},
        dataset_filter=None,
        total_stars=1000,
        results_summary={"n_clusters": 8}
    )
    
    # Retrieve it
    retrieved_run = repository.get_discovery_run(created_run.run_id)
    
    assert retrieved_run is not None
    assert retrieved_run.run_id == created_run.run_id
    assert retrieved_run.run_type == "cluster"
    assert retrieved_run.parameters["eps"] == 0.5
    assert retrieved_run.total_stars == 1000
    
    print(f"✅ Retrieved run: {retrieved_run.run_id}")


def test_get_nonexistent_run(repository):
    """Test retrieving a non-existent run returns None."""
    result = repository.get_discovery_run("00000000-0000-0000-0000-000000000000")
    assert result is None
    print("✅ Non-existent run correctly returned None")


def test_list_discovery_runs_all(repository):
    """Test listing all discovery runs."""
    # Create multiple runs
    repository.save_discovery_run(
        run_type="anomaly",
        parameters={"contamination": 0.1},
        dataset_filter=None,
        total_stars=100,
        results_summary={}
    )
    repository.save_discovery_run(
        run_type="cluster",
        parameters={"eps": 1.0},
        dataset_filter=None,
        total_stars=200,
        results_summary={}
    )
    
    # List all runs
    runs = repository.list_discovery_runs(limit=50)
    
    assert len(runs) > 0
    assert all(hasattr(r, "run_id") for r in runs)
    
    # Verify ordering (newest first)
    if len(runs) > 1:
        assert runs[0].created_at >= runs[1].created_at
    
    print(f"✅ Listed {len(runs)} discovery runs")


def test_list_discovery_runs_filtered(repository):
    """Test listing discovery runs with type filter."""
    # Create runs of both types
    repository.save_discovery_run(
        run_type="anomaly",
        parameters={"contamination": 0.05},
        dataset_filter=None,
        total_stars=100,
        results_summary={}
    )
    repository.save_discovery_run(
        run_type="cluster",
        parameters={"eps": 0.5},
        dataset_filter=None,
        total_stars=200,
        results_summary={}
    )
    
    # Filter by anomaly type
    anomaly_runs = repository.list_discovery_runs(run_type="anomaly", limit=50)
    assert len(anomaly_runs) > 0
    assert all(r.run_type == "anomaly" for r in anomaly_runs)
    
    # Filter by cluster type
    cluster_runs = repository.list_discovery_runs(run_type="cluster", limit=50)
    assert len(cluster_runs) > 0
    assert all(r.run_type == "cluster" for r in cluster_runs)
    
    print(f"✅ Filtered runs: {len(anomaly_runs)} anomaly, {len(cluster_runs)} cluster")


def test_list_discovery_runs_pagination(repository):
    """Test pagination of discovery runs."""
    # Create several runs
    for i in range(5):
        repository.save_discovery_run(
            run_type="anomaly",
            parameters={"contamination": 0.05},
            dataset_filter=None,
            total_stars=100,
            results_summary={}
        )
    
    # Get first page
    page1 = repository.list_discovery_runs(limit=2, offset=0)
    assert len(page1) == 2
    
    # Get second page
    page2 = repository.list_discovery_runs(limit=2, offset=2)
    assert len(page2) == 2
    
    # Verify different results
    assert page1[0].run_id != page2[0].run_id
    
    print("✅ Pagination working correctly")


def test_save_discovery_results(repository, sample_stars):
    """Test batch saving discovery results."""
    # Create a run
    run = repository.save_discovery_run(
        run_type="anomaly",
        parameters={"contamination": 0.1},
        dataset_filter=None,
        total_stars=len(sample_stars),
        results_summary={"n_anomalies": 2}
    )
    
    # Save results for all stars
    results = [
        {
            "star_id": star.id,
            "is_anomaly": 1 if i < 2 else 0,
            "anomaly_score": -0.5 if i < 2 else 0.2
        }
        for i, star in enumerate(sample_stars)
    ]
    
    count = repository.save_discovery_results(run.run_id, results)
    
    assert count == len(sample_stars)
    print(f"✅ Saved {count} discovery results")


def test_get_results_by_run_id(repository, sample_stars):
    """Test retrieving all results for a run."""
    # Create run and results
    run = repository.save_discovery_run(
        run_type="anomaly",
        parameters={},
        dataset_filter=None,
        total_stars=len(sample_stars),
        results_summary={}
    )
    
    results = [
        {"star_id": star.id, "is_anomaly": 0, "anomaly_score": 0.1}
        for star in sample_stars
    ]
    repository.save_discovery_results(run.run_id, results)
    
    # Retrieve results
    retrieved = repository.get_results_by_run_id(run.run_id, limit=100)
    
    assert len(retrieved) == len(sample_stars)
    assert all(r.run_id == run.run_id for r in retrieved)
    
    print(f"✅ Retrieved {len(retrieved)} results for run")


def test_get_anomalies_by_run_id(repository, sample_stars):
    """Test retrieving only anomalies for a run."""
    # Create run
    run = repository.save_discovery_run(
        run_type="anomaly",
        parameters={},
        dataset_filter=None,
        total_stars=len(sample_stars),
        results_summary={"n_anomalies": 3}
    )
    
    # Save results with 3 anomalies
    results = [
        {
            "star_id": star.id,
            "is_anomaly": 1 if i < 3 else 0,
            "anomaly_score": -0.7 if i < 3 else 0.3
        }
        for i, star in enumerate(sample_stars)
    ]
    repository.save_discovery_results(run.run_id, results)
    
    # Get anomalies only
    anomalies = repository.get_anomalies_by_run_id(run.run_id, limit=100)
    
    assert len(anomalies) == 3
    assert all(r.is_anomaly == 1 for r in anomalies)
    assert all(r.anomaly_score < 0 for r in anomalies)
    
    print(f"✅ Retrieved {len(anomalies)} anomalies")


def test_get_cluster_members(repository, sample_stars):
    """Test retrieving stars in a specific cluster."""
    # Create clustering run
    run = repository.save_discovery_run(
        run_type="cluster",
        parameters={"eps": 0.5},
        dataset_filter=None,
        total_stars=len(sample_stars),
        results_summary={"n_clusters": 3}
    )
    
    # Save results with 3 clusters
    results = [
        {
            "star_id": star.id,
            "is_anomaly": 0,
            "cluster_id": i % 3  # Distribute across 3 clusters
        }
        for i, star in enumerate(sample_stars)
    ]
    repository.save_discovery_results(run.run_id, results)
    
    # Get cluster 0 members
    cluster_0 = repository.get_cluster_members(run.run_id, cluster_id=0, limit=100)
    
    assert len(cluster_0) > 0
    assert all(r.cluster_id == 0 for r in cluster_0)
    
    # Get cluster 1 members
    cluster_1 = repository.get_cluster_members(run.run_id, cluster_id=1, limit=100)
    
    assert len(cluster_1) > 0
    assert all(r.cluster_id == 1 for r in cluster_1)
    
    print(f"✅ Retrieved cluster members: cluster 0 = {len(cluster_0)}, cluster 1 = {len(cluster_1)}")


def test_get_results_with_star_data(repository, sample_stars):
    """Test retrieving results joined with star catalog data."""
    # Create run and results
    run = repository.save_discovery_run(
        run_type="anomaly",
        parameters={},
        dataset_filter=None,
        total_stars=len(sample_stars),
        results_summary={"n_anomalies": 2}
    )
    
    results = [
        {
            "star_id": star.id,
            "is_anomaly": 1 if i < 2 else 0,
            "anomaly_score": -0.6 if i < 2 else 0.2
        }
        for i, star in enumerate(sample_stars)
    ]
    repository.save_discovery_results(run.run_id, results)
    
    # Get all results with star data
    enriched = repository.get_results_with_star_data(run.run_id, limit=100)
    
    assert len(enriched) > 0
    assert all("star" in r for r in enriched)
    assert all("ra_deg" in r["star"] for r in enriched)
    assert all("dec_deg" in r["star"] for r in enriched)
    assert all("brightness_mag" in r["star"] for r in enriched)
    
    print(f"✅ Retrieved {len(enriched)} enriched results with star data")


def test_get_results_with_star_data_anomalies_only(repository, sample_stars):
    """Test retrieving only anomalies with star data."""
    # Create run
    run = repository.save_discovery_run(
        run_type="anomaly",
        parameters={},
        dataset_filter=None,
        total_stars=len(sample_stars),
        results_summary={"n_anomalies": 3}
    )
    
    # Save results with 3 anomalies
    results = [
        {
            "star_id": star.id,
            "is_anomaly": 1 if i < 3 else 0,
            "anomaly_score": -0.8 if i < 3 else 0.1
        }
        for i, star in enumerate(sample_stars)
    ]
    repository.save_discovery_results(run.run_id, results)
    
    # Get anomalies with star data
    anomaly_enriched = repository.get_results_with_star_data(
        run.run_id,
        anomalies_only=True,
        limit=100
    )
    
    assert len(anomaly_enriched) == 3
    assert all(r["is_anomaly"] for r in anomaly_enriched)
    assert all("star" in r for r in anomaly_enriched)
    
    print(f"✅ Retrieved {len(anomaly_enriched)} anomalies with star data")


def test_count_results_by_run_id(repository, sample_stars):
    """Test counting total results for a run."""
    # Create run and results
    run = repository.save_discovery_run(
        run_type="anomaly",
        parameters={},
        dataset_filter=None,
        total_stars=len(sample_stars),
        results_summary={}
    )
    
    results = [
        {"star_id": star.id, "is_anomaly": 0}
        for star in sample_stars
    ]
    repository.save_discovery_results(run.run_id, results)
    
    # Count results
    count = repository.count_results_by_run_id(run.run_id)
    
    assert count == len(sample_stars)
    print(f"✅ Counted {count} total results")


def test_count_anomalies_by_run_id(repository, sample_stars):
    """Test counting anomalies for a run."""
    # Create run
    run = repository.save_discovery_run(
        run_type="anomaly",
        parameters={},
        dataset_filter=None,
        total_stars=len(sample_stars),
        results_summary={"n_anomalies": 4}
    )
    
    # Save results with 4 anomalies
    results = [
        {
            "star_id": star.id,
            "is_anomaly": 1 if i < 4 else 0
        }
        for i, star in enumerate(sample_stars)
    ]
    repository.save_discovery_results(run.run_id, results)
    
    # Count anomalies
    count = repository.count_anomalies_by_run_id(run.run_id)
    
    assert count == 4
    print(f"✅ Counted {count} anomalies")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
