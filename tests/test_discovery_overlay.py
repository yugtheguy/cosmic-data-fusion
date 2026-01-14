"""
Stage 4 Test: Discovery Overlay Service
Tests combining query filters with AI discovery results.
"""
import pytest
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.models import UnifiedStarCatalog
from app.services.ai_discovery import AIDiscoveryService
from app.services.discovery_overlay import DiscoveryOverlayService
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
def overlay_service(db_session):
    """Provide a DiscoveryOverlayService instance."""
    return DiscoveryOverlayService(db_session)


@pytest.fixture
def ai_service(db_session):
    """Provide an AIDiscoveryService instance."""
    return AIDiscoveryService(db_session)


@pytest.fixture
def repository(db_session):
    """Provide a DiscoveryRepository instance."""
    return DiscoveryRepository(db_session)


@pytest.fixture
def stars_with_discoveries(db_session, ai_service):
    """Create stars and run discoveries on them."""
    # Create 40 test stars with varied properties
    stars = []
    
    # Normal stars (30)
    for i in range(30):
        stars.append(UnifiedStarCatalog(
            original_source="OverlayTest",
            source_id=f"overlay_normal_{i}",
            ra_deg=100.0 + i * 1.0,
            dec_deg=20.0 + i * 0.5,
            brightness_mag=11.0 + i * 0.2,
            parallax_mas=10.0 + i * 0.5,
            raw_frame="ICRS"
        ))
    
    # Anomalous stars (10)
    for i in range(10):
        stars.append(UnifiedStarCatalog(
            original_source="OverlayTest",
            source_id=f"overlay_anomaly_{i}",
            ra_deg=200.0 + i * 5.0,
            dec_deg=-45.0 + i * 3.0,
            brightness_mag=18.0 + i,
            parallax_mas=100.0 + i * 10,
            raw_frame="ICRS"
        ))
    
    db_session.add_all(stars)
    db_session.commit()
    
    # Run anomaly detection with save
    ai_service.load_data()
    ai_service.detect_anomalies(
        contamination=0.2,
        random_state=42,
        save_results=True,
        dataset_filter={"source": "OverlayTest"}
    )
    
    # Run clustering with save
    ai_service.detect_clusters(
        eps=0.6,
        min_samples=5,
        save_results=True,
        dataset_filter={"source": "OverlayTest"}
    )
    
    return stars


def test_query_with_discovery_basic(overlay_service, repository, stars_with_discoveries):
    """Test basic query with discovery overlay."""
    # Get most recent anomaly run
    runs = repository.list_discovery_runs(run_type="anomaly", limit=1)
    assert len(runs) > 0
    run = runs[0]
    
    # Query with discovery overlay
    result = overlay_service.query_with_discovery(
        run_id=run.run_id,
        limit=100
    )
    
    # Verify structure
    assert "run_info" in result
    assert "results" in result
    assert "total_count" in result
    assert "returned_count" in result
    
    # Verify run info
    assert result["run_info"]["run_id"] == run.run_id
    assert result["run_info"]["run_type"] == "anomaly"
    assert "parameters" in result["run_info"]
    
    # Verify results have proper structure
    assert len(result["results"]) > 0
    for item in result["results"]:
        assert "star" in item
        assert "discovery" in item
        assert "is_anomaly" in item["discovery"]
        assert "anomaly_score" in item["discovery"]
    
    print(f"✅ Query with discovery returned {result['returned_count']} results")


def test_query_with_discovery_anomalies_only(overlay_service, repository, stars_with_discoveries):
    """Test filtering to anomalies only."""
    # Get most recent anomaly run
    runs = repository.list_discovery_runs(run_type="anomaly", limit=1)
    run = runs[0]
    
    # Query anomalies only
    result = overlay_service.query_with_discovery(
        run_id=run.run_id,
        anomalies_only=True,
        limit=100
    )
    
    # All results should be anomalies
    assert len(result["results"]) > 0
    for item in result["results"]:
        assert item["discovery"]["is_anomaly"] is True
        assert item["discovery"]["anomaly_score"] is not None
        assert item["discovery"]["anomaly_score"] < 0  # Anomalies have negative scores
    
    print(f"✅ Found {result['returned_count']} anomalies")


def test_query_with_discovery_cluster_filter(overlay_service, repository, stars_with_discoveries):
    """Test filtering to specific cluster."""
    # Get most recent clustering run
    runs = repository.list_discovery_runs(run_type="cluster", limit=1)
    run = runs[0]
    
    # Check if any clusters were found
    if run.results_summary["n_clusters"] > 0:
        # Query cluster 0 members
        result = overlay_service.query_with_discovery(
            run_id=run.run_id,
            cluster_id=0,
            limit=100
        )
        
        # All results should be in cluster 0
        assert len(result["results"]) > 0
        for item in result["results"]:
            assert item["discovery"]["cluster_id"] == 0
        
        print(f"✅ Found {result['returned_count']} stars in cluster 0")
    else:
        print("✅ No clusters found (all noise) - skipping cluster filter test")


def test_query_with_discovery_catalog_filters(overlay_service, repository, stars_with_discoveries):
    """Test combining discovery overlay with catalog filters."""
    # Get most recent anomaly run
    runs = repository.list_discovery_runs(run_type="anomaly", limit=1)
    run = runs[0]
    
    # Query with catalog filters
    result = overlay_service.query_with_discovery(
        run_id=run.run_id,
        filters={
            "magnitude_min": 10.0,
            "magnitude_max": 15.0,
            "ra_min": 90.0,
            "ra_max": 150.0
        },
        limit=100
    )
    
    # Verify filters were applied
    for item in result["results"]:
        mag = item["star"]["brightness_mag"]
        ra = item["star"]["ra_deg"]
        assert 10.0 <= mag <= 15.0
        assert 90.0 <= ra <= 150.0
    
    print(f"✅ Filtered query returned {result['returned_count']} results")


def test_query_with_discovery_pagination(overlay_service, repository, stars_with_discoveries):
    """Test pagination of discovery overlay results."""
    # Get most recent run
    runs = repository.list_discovery_runs(limit=1)
    run = runs[0]
    
    # Get first page
    page1 = overlay_service.query_with_discovery(
        run_id=run.run_id,
        limit=10,
        offset=0
    )
    
    # Get second page
    page2 = overlay_service.query_with_discovery(
        run_id=run.run_id,
        limit=10,
        offset=10
    )
    
    # Verify pagination
    assert page1["returned_count"] <= 10
    assert page2["returned_count"] <= 10
    
    # Verify different results
    if page1["returned_count"] > 0 and page2["returned_count"] > 0:
        page1_ids = {item["star"]["id"] for item in page1["results"]}
        page2_ids = {item["star"]["id"] for item in page2["results"]}
        assert page1_ids != page2_ids  # Different stars on each page
    
    print(f"✅ Pagination working: page1={page1['returned_count']}, page2={page2['returned_count']}")


def test_query_with_discovery_nonexistent_run(overlay_service):
    """Test handling of non-existent run_id."""
    result = overlay_service.query_with_discovery(
        run_id="00000000-0000-0000-0000-000000000000",
        limit=100
    )
    
    assert "error" in result
    assert result["total_count"] == 0
    assert len(result["results"]) == 0
    
    print("✅ Non-existent run handled gracefully")


def test_find_anomalies_default_run(overlay_service, stars_with_discoveries):
    """Test finding anomalies using most recent run."""
    result = overlay_service.find_anomalies(limit=100)
    
    # Should use most recent anomaly run
    assert "error" not in result
    assert len(result["results"]) > 0
    
    # All should be anomalies
    for item in result["results"]:
        assert item["discovery"]["is_anomaly"] is True
    
    print(f"✅ Found {result['returned_count']} anomalies from latest run")


def test_find_anomalies_with_filters(overlay_service, stars_with_discoveries):
    """Test finding anomalies with catalog filters."""
    result = overlay_service.find_anomalies(
        filters={
            "magnitude_min": 15.0,
            "magnitude_max": 25.0
        },
        limit=100
    )
    
    # Should return filtered anomalies
    for item in result["results"]:
        assert item["discovery"]["is_anomaly"] is True
        assert 15.0 <= item["star"]["brightness_mag"] <= 25.0
    
    print(f"✅ Found {result['returned_count']} bright anomalies")


def test_find_anomalies_specific_run(overlay_service, repository, stars_with_discoveries):
    """Test finding anomalies from specific run."""
    # Get a specific run
    runs = repository.list_discovery_runs(run_type="anomaly", limit=2)
    if len(runs) >= 2:
        run_id = runs[1].run_id  # Use second-most recent
        
        result = overlay_service.find_anomalies(
            run_id=run_id,
            limit=100
        )
        
        # Should use specified run
        assert result["run_info"]["run_id"] == run_id
        
        print(f"✅ Found anomalies from specific run {run_id}")
    else:
        print("✅ Skipping (not enough anomaly runs)")


def test_find_cluster_members_default_run(overlay_service, repository, stars_with_discoveries):
    """Test finding cluster members using most recent run."""
    # Get most recent clustering run
    runs = repository.list_discovery_runs(run_type="cluster", limit=1)
    run = runs[0]
    
    # Check if any clusters exist
    if run.results_summary["n_clusters"] > 0:
        result = overlay_service.find_cluster_members(
            cluster_id=0,
            limit=100
        )
        
        # Should return cluster members
        assert "error" not in result
        assert len(result["results"]) > 0
        
        # All should be in cluster 0
        for item in result["results"]:
            assert item["discovery"]["cluster_id"] == 0
        
        print(f"✅ Found {result['returned_count']} members of cluster 0")
    else:
        print("✅ No clusters found (all noise) - skipping")


def test_find_cluster_members_with_filters(overlay_service, repository, stars_with_discoveries):
    """Test finding cluster members with catalog filters."""
    # Get most recent clustering run
    runs = repository.list_discovery_runs(run_type="cluster", limit=1)
    run = runs[0]
    
    if run.results_summary["n_clusters"] > 0:
        result = overlay_service.find_cluster_members(
            cluster_id=0,
            filters={
                "magnitude_min": 10.0,
                "magnitude_max": 14.0
            },
            limit=100
        )
        
        # Verify filters applied
        for item in result["results"]:
            assert item["discovery"]["cluster_id"] == 0
            assert 10.0 <= item["star"]["brightness_mag"] <= 14.0
        
        print(f"✅ Found {result['returned_count']} filtered cluster members")
    else:
        print("✅ No clusters found - skipping")


def test_find_cluster_members_noise(overlay_service, stars_with_discoveries):
    """Test finding noise points (cluster_id = -1)."""
    result = overlay_service.find_cluster_members(
        cluster_id=-1,
        limit=100
    )
    
    # Should return noise points
    if result["returned_count"] > 0:
        for item in result["results"]:
            assert item["discovery"]["cluster_id"] == -1
        
        print(f"✅ Found {result['returned_count']} noise points")
    else:
        print("✅ No noise points found")


def test_compare_runs_anomaly_overlap(overlay_service, ai_service, repository, stars_with_discoveries):
    """Test comparing two anomaly runs for overlap."""
    # Create a second anomaly run with different parameters
    ai_service.load_data()
    ai_service.detect_anomalies(
        contamination=0.1,  # Different contamination
        random_state=99,
        save_results=True
    )
    
    # Get two most recent anomaly runs
    runs = repository.list_discovery_runs(run_type="anomaly", limit=2)
    if len(runs) >= 2:
        result = overlay_service.compare_runs(
            run_id_1=runs[0].run_id,
            run_id_2=runs[1].run_id,
            comparison_type="anomaly_overlap"
        )
        
        # Verify structure
        assert "comparison_type" in result
        assert "stats" in result
        assert "results" in result
        
        # Verify stats
        assert "run1_anomalies" in result["stats"]
        assert "run2_anomalies" in result["stats"]
        assert "overlap_count" in result["stats"]
        
        print(f"✅ Comparison: {result['stats']['overlap_count']} anomalies in both runs")
    else:
        print("✅ Need 2+ anomaly runs for comparison (skipping)")


def test_compare_runs_anomaly_difference(overlay_service, repository, stars_with_discoveries):
    """Test finding anomalies unique to one run."""
    # Get two most recent anomaly runs
    runs = repository.list_discovery_runs(run_type="anomaly", limit=2)
    if len(runs) >= 2:
        result = overlay_service.compare_runs(
            run_id_1=runs[0].run_id,
            run_id_2=runs[1].run_id,
            comparison_type="anomaly_difference"
        )
        
        # Verify structure
        assert "comparison_type" in result
        assert result["comparison_type"] == "anomaly_difference"
        assert "stats" in result
        
        print(f"✅ Found {result['stats']['run1_only_count']} anomalies unique to run1")
    else:
        print("✅ Need 2+ anomaly runs for comparison (skipping)")


def test_overlay_service_integration(overlay_service, repository, stars_with_discoveries):
    """Test full integration: query + filter + discovery overlay."""
    # Get latest anomaly run
    runs = repository.list_discovery_runs(run_type="anomaly", limit=1)
    run = runs[0]
    
    # Complex query with multiple filters and discovery overlay
    result = overlay_service.query_with_discovery(
        run_id=run.run_id,
        filters={
            "magnitude_min": 10.0,
            "magnitude_max": 20.0,
            "ra_min": 0.0,
            "ra_max": 360.0,
            "dec_min": -90.0,
            "dec_max": 90.0
        },
        anomalies_only=False,
        limit=50
    )
    
    # Verify comprehensive response
    assert "run_info" in result
    assert "results" in result
    assert result["total_count"] > 0
    
    # Verify each result has complete data
    for item in result["results"]:
        # Star data
        assert "star" in item
        assert "ra_deg" in item["star"]
        assert "dec_deg" in item["star"]
        assert "brightness_mag" in item["star"]
        
        # Discovery data
        assert "discovery" in item
        assert "is_anomaly" in item["discovery"]
        assert "anomaly_score" in item["discovery"]
    
    print(f"✅ Integration test: {result['returned_count']} results with full overlay")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
