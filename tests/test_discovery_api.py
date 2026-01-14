"""
Tests for Discovery Overlay API Endpoints

Validates REST API endpoints for querying with AI discovery metadata.
Tests all endpoints with various filter combinations.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import UnifiedStarCatalog, DiscoveryRun, DiscoveryResult
from app.database import get_db


client = TestClient(app)


@pytest.fixture
def setup_discovery_data(db_session: Session):
    """Create test data with discovery results"""
    # Create test stars
    stars = [
        UnifiedStarCatalog(
            source_id=f"TEST_{i}",
            ra_deg=10.0 + i * 0.1,
            dec_deg=20.0 + i * 0.1,
            brightness_mag=12.5,
            parallax_mas=5.0,
            original_source="TEST",
            raw_frame="ICRS"
        )
        for i in range(10)
    ]
    db_session.add_all(stars)
    db_session.flush()
    
    # Create discovery run
    run = DiscoveryRun(
        run_type="anomaly",
        parameters={"contamination": 0.1},
        total_stars=10,
        results_summary={}
    )
    db_session.add(run)
    db_session.flush()
    
    # Create discovery results (mark first 3 as anomalies, rest in clusters)
    results = []
    for i, star in enumerate(stars):
        if i < 3:
            # Anomalies
            results.append(DiscoveryResult(
                run_id=run.run_id,
                star_id=star.id,
                is_anomaly=True,
                anomaly_score=0.8 + i * 0.05,
                cluster_id=None
            ))
        else:
            # Cluster members (2 clusters)
            cluster_id = 0 if i < 6 else 1
            results.append(DiscoveryResult(
                run_id=run.run_id,
                star_id=star.id,
                is_anomaly=False,
                anomaly_score=None,
                cluster_id=cluster_id
            ))
    
    db_session.add_all(results)
    db_session.commit()
    
    return {
        "run_id": run.run_id,
        "star_ids": [s.id for s in stars],
        "anomaly_ids": [stars[i].id for i in range(3)],
        "cluster_0_ids": [stars[i].id for i in range(3, 6)],
        "cluster_1_ids": [stars[i].id for i in range(6, 10)]
    }


# ==================== Test /discovery/query ====================

def test_query_with_discovery_basic(setup_discovery_data):
    """Test basic query with discovery overlay"""
    run_id = setup_discovery_data["run_id"]
    
    response = client.post("/discovery/query", json={
        "run_id": run_id,
        "limit": 100,
        "offset": 0
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_count" in data
    assert "run_info" in data
    assert data["total_count"] >= 10
    assert len(data["results"]) >= 10


def test_query_with_discovery_spatial_filter(setup_discovery_data):
    """Test query with spatial constraints"""
    run_id = setup_discovery_data["run_id"]
    
    response = client.post("/discovery/query", json={
        "run_id": run_id,
        "ra_min": 10.0,
        "ra_max": 10.5,
        "dec_min": 20.0,
        "dec_max": 20.5,
        "limit": 100
    })
    
    assert response.status_code == 200
    data = response.json()
    # Should return subset of stars within spatial bounds
    assert data["total_count"] >= 1


def test_query_with_discovery_pagination(setup_discovery_data):
    """Test pagination in discovery query"""
    run_id = setup_discovery_data["run_id"]
    
    # Get first page
    response1 = client.post("/discovery/query", json={
        "run_id": run_id,
        "limit": 5,
        "offset": 0
    })
    
    # Get second page
    response2 = client.post("/discovery/query", json={
        "run_id": run_id,
        "limit": 5,
        "offset": 5
    })
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Should have different results
    ids1 = {r["star_id"] for r in data1["results"]}
    ids2 = {r["star_id"] for r in data2["results"]}
    assert ids1 != ids2


def test_query_with_discovery_invalid_run(setup_discovery_data):
    """Test query with non-existent run ID"""
    response = client.post("/discovery/query", json={
        "run_id": "99999999-9999-9999-9999-999999999999",  # Non-existent UUID
        "limit": 100
    })
    
    assert response.status_code == 404


# ==================== Test /discovery/anomalies ====================

def test_find_anomalies_basic(setup_discovery_data):
    """Test finding anomalies"""
    run_id = setup_discovery_data["run_id"]
    
    response = client.post("/discovery/anomalies", json={
        "run_id": run_id,
        "limit": 100,
        "offset": 0
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 3  # We created 3 anomalies
    assert len(data["results"]) == 3
    
    # All results should be anomalies
    for result in data["results"]:
        assert result["is_anomaly"] is True
        assert result["anomaly_score"] is not None


def test_find_anomalies_with_filters(setup_discovery_data):
    """Test finding anomalies with spatial filter"""
    run_id = setup_discovery_data["run_id"]
    
    response = client.post("/discovery/anomalies", json={
        "run_id": run_id,
        "ra_min": 10.0,
        "ra_max": 10.15,  # Should include first 2 anomalies
        "limit": 100
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] >= 1
    assert data["total_count"] <= 3


def test_find_anomalies_pagination(setup_discovery_data):
    """Test anomaly pagination"""
    run_id = setup_discovery_data["run_id"]
    
    response = client.post("/discovery/anomalies", json={
        "run_id": run_id,
        "limit": 2,
        "offset": 0
    })
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    assert data["total_count"] == 3


# ==================== Test /discovery/clusters/members ====================

def test_find_cluster_members_basic(setup_discovery_data):
    """Test finding cluster members"""
    run_id = setup_discovery_data["run_id"]
    
    response = client.post("/discovery/clusters/members", json={
        "run_id": run_id,
        "cluster_id": 0,
        "limit": 100
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 3  # Cluster 0 has 3 members
    assert len(data["results"]) == 3
    
    # All results should be in cluster 0
    for result in data["results"]:
        assert result["cluster_id"] == 0
        assert result["is_anomaly"] is False


def test_find_cluster_members_with_filters(setup_discovery_data):
    """Test finding cluster members with spatial filter"""
    run_id = setup_discovery_data["run_id"]
    
    response = client.post("/discovery/clusters/members", json={
        "run_id": run_id,
        "cluster_id": 0,
        "dec_min": 20.0,
        "dec_max": 20.4,
        "limit": 100
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] >= 1


def test_find_cluster_members_different_cluster(setup_discovery_data):
    """Test finding members of different cluster"""
    run_id = setup_discovery_data["run_id"]
    
    # Get cluster 1 members
    response = client.post("/discovery/clusters/members", json={
        "run_id": run_id,
        "cluster_id": 1,
        "limit": 100
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 4  # Cluster 1 has 4 members


# ==================== Test /discovery/compare ====================

def test_compare_runs(setup_discovery_data, db_session: Session):
    """Test comparing two discovery runs"""
    run_id_1 = setup_discovery_data["run_id"]
    
    # Create second run with overlapping but different results
    run_2 = DiscoveryRun(
        run_type="clustering",
        parameters={"eps": 0.5},
        total_stars=8,
        results_summary={}
    )
    db_session.add(run_2)
    db_session.flush()
    
    # Use subset of stars (skip first 2, include rest)
    star_ids = setup_discovery_data["star_ids"][2:]
    results_2 = [
        DiscoveryResult(
            run_id=run_2.run_id,
            star_id=sid,
            is_anomaly=False,
            cluster_id=0
        )
        for sid in star_ids
    ]
    db_session.add_all(results_2)
    db_session.commit()
    
    # Compare runs
    response = client.post("/discovery/compare", json={
        "run_id_1": run_id_1,
        "run_id_2": run_2.run_id
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Service returns comparison_type, run1, run2, results, stats
    assert "comparison_type" in data
    assert "run1" in data
    assert "run2" in data
    assert "results" in data
    assert "stats" in data
    
    # Verify run metadata
    assert data["run1"]["run_id"] == run_id_1
    assert data["run2"]["run_id"] == run_2.run_id


def test_compare_runs_with_filters(setup_discovery_data, db_session: Session):
    """Test comparing runs with spatial filters"""
    run_id_1 = setup_discovery_data["run_id"]
    
    # Create second run
    run_2 = DiscoveryRun(
        run_type="clustering",
        parameters={},
        total_stars=10,
        results_summary={}
    )
    db_session.add(run_2)
    db_session.flush()
    
    results_2 = [
        DiscoveryResult(
            run_id=run_2.run_id,
            star_id=sid,
            is_anomaly=False,
            cluster_id=0
        )
        for sid in setup_discovery_data["star_ids"]
    ]
    db_session.add_all(results_2)
    db_session.commit()
    
    # Compare with spatial filter
    response = client.post("/discovery/compare", json={
        "run_id_1": run_id_1,
        "run_id_2": run_2.run_id,
        "ra_min": 10.0,
        "ra_max": 10.5
    })
    
    assert response.status_code == 200
    data = response.json()
    # Should return comparison for filtered subset
    assert "comparison_type" in data
    assert "stats" in data
    assert "results" in data


# ==================== Test /discovery/runs ====================

def test_list_discovery_runs(setup_discovery_data):
    """Test listing all discovery runs"""
    response = client.get("/discovery/runs")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check run structure
    run = data[0]
    assert "run_id" in run
    assert "run_type" in run
    assert "parameters" in run
    assert "total_stars" in run
    assert "timestamp" in run


def test_list_discovery_runs_filtered(setup_discovery_data):
    """Test listing discovery runs with type filter"""
    response = client.get("/discovery/runs?run_type=anomaly")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    
    # All runs should be anomaly type
    for run in data:
        assert run["run_type"] == "anomaly"


def test_list_discovery_runs_pagination(setup_discovery_data):
    """Test pagination for run listing"""
    response = client.get("/discovery/runs?limit=1&offset=0")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 1


# ==================== Test /discovery/runs/{run_id} ====================

def test_get_discovery_run(setup_discovery_data):
    """Test getting specific discovery run"""
    run_id = setup_discovery_data["run_id"]
    
    response = client.get(f"/discovery/runs/{run_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == run_id
    assert data["run_type"] == "anomaly"
    assert data["total_stars"] == 10


def test_get_discovery_run_not_found(setup_discovery_data):
    """Test getting non-existent discovery run"""
    response = client.get("/discovery/runs/99999")
    
    assert response.status_code == 404
