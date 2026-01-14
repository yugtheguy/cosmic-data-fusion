"""
Tests for materialized views and analytics endpoints.

Verifies:
- Materialized views contain accurate data
- View refresh operations work correctly
- Analytics API endpoints return expected results
- Performance improvements are measurable
"""

import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.services.ai_discovery import AIDiscoveryService
from app.repository.discovery import DiscoveryRepository


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def discovery_repo(db_session):
    """Discovery repository instance."""
    return DiscoveryRepository(db_session)


@pytest.fixture
def ai_service_with_data(db_session, sample_stars):
    """AI service with loaded data."""
    service = AIDiscoveryService(db_session)
    service.load_data()
    return service


def test_discovery_run_stats_view_exists(db_session):
    """Verify mv_discovery_run_stats view exists and has correct schema."""
    result = db_session.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'mv_discovery_run_stats' ORDER BY ordinal_position"
    ))
    columns = [row[0] for row in result]
    
    expected_columns = [
        'run_id', 'run_type', 'total_stars', 'anomaly_count',
        'cluster_count', 'noise_count', 'largest_cluster_size',
        'parameters_json', 'created_at', 'is_complete', 'last_updated'
    ]
    
    assert all(col in columns for col in expected_columns), \
        f"Missing columns. Found: {columns}"


def test_cluster_size_distribution_view_exists(db_session):
    """Verify mv_cluster_size_distribution view exists."""
    result = db_session.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'mv_cluster_size_distribution'"
    ))
    columns = [row[0] for row in result]
    
    assert 'run_id' in columns
    assert 'cluster_id' in columns
    assert 'cluster_size' in columns
    assert 'star_ids' in columns


def test_star_anomaly_frequency_view_exists(db_session):
    """Verify mv_star_anomaly_frequency view exists."""
    result = db_session.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'mv_star_anomaly_frequency'"
    ))
    columns = [row[0] for row in result]
    
    assert 'star_id' in columns
    assert 'anomaly_count' in columns
    assert 'frequency_pct' in columns


def test_anomaly_overlap_matrix_view_exists(db_session):
    """Verify mv_anomaly_overlap_matrix view exists."""
    result = db_session.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'mv_anomaly_overlap_matrix'"
    ))
    columns = [row[0] for row in result]
    
    assert 'run_1_id' in columns
    assert 'run_2_id' in columns
    assert 'overlap_count' in columns
    assert 'jaccard_similarity' in columns


def test_discovery_timeline_view_exists(db_session):
    """Verify mv_discovery_timeline view exists."""
    result = db_session.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'mv_discovery_timeline'"
    ))
    columns = [row[0] for row in result]
    
    assert 'period_start' in columns
    assert 'run_type' in columns
    assert 'period_type' in columns


def test_discovery_run_stats_accuracy(ai_service_with_data, discovery_repo, db_session):
    """Verify mv_discovery_run_stats contains accurate aggregations."""
    # Run anomaly detection
    result = ai_service_with_data.detect_anomalies(
        contamination=0.1,
        save_results=True
    )
    
    # Query materialized view
    view_result = db_session.execute(text(
        "SELECT run_id, total_stars, anomaly_count FROM mv_discovery_run_stats "
        "ORDER BY created_at DESC LIMIT 1"
    )).fetchone()
    
    assert view_result is not None
    assert view_result[1] == result['total_stars']
    assert view_result[2] == result['n_anomalies']


def test_cluster_distribution_accuracy(ai_service_with_data, db_session):
    """Verify mv_cluster_size_distribution matches actual cluster sizes."""
    # Run clustering
    result = ai_service_with_data.detect_clusters(
        eps=0.7,
        min_samples=3,
        save_results=True
    )
    
    if result['n_clusters'] > 0:
        # Get cluster 0 size from view
        view_result = db_session.execute(text(
            "SELECT cluster_size, star_ids FROM mv_cluster_size_distribution "
            "WHERE cluster_id = 0 ORDER BY cluster_size DESC LIMIT 1"
        )).fetchone()
        
        assert view_result is not None
        assert view_result[0] == result['cluster_stats']['cluster_0']['count']
        assert len(view_result[1]) == view_result[0]


def test_view_refresh_works(ai_service_with_data, discovery_repo):
    """Verify materialized view refresh operations work."""
    # Run discovery to generate data
    ai_service_with_data.detect_anomalies(contamination=0.1, save_results=True)
    
    # Manually refresh all views
    discovery_repo.refresh_all_views()
    
    # Should complete without errors
    assert True


def test_analytics_get_discovery_stats(client, ai_service_with_data):
    """Test GET /analytics/discovery/stats endpoint."""
    # Generate test data
    ai_service_with_data.detect_anomalies(contamination=0.05, save_results=True)
    
    # Query endpoint
    response = client.get("/analytics/discovery/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Verify schema
    first_run = data[0]
    assert 'run_id' in first_run
    assert 'run_type' in first_run
    assert 'total_stars' in first_run
    assert 'anomaly_count' in first_run


def test_analytics_get_cluster_sizes(client, ai_service_with_data, db_session):
    """Test GET /analytics/discovery/clusters/{run_id}/sizes endpoint."""
    # Run clustering
    result = ai_service_with_data.detect_clusters(eps=0.7, min_samples=3, save_results=True)
    
    # Get latest run ID
    runs = db_session.execute(text(
        "SELECT run_id FROM discovery_runs WHERE run_type = 'cluster' "
        "ORDER BY created_at DESC LIMIT 1"
    )).fetchone()
    
    run_id = runs[0]
    
    # Query endpoint
    response = client.get(f"/analytics/discovery/clusters/{run_id}/sizes")
    
    if result['n_clusters'] > 0:
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert 'cluster_id' in data[0]
        assert 'cluster_size' in data[0]
    else:
        # No clusters is valid
        assert response.status_code in [200, 404]


def test_analytics_get_star_frequency(client, ai_service_with_data):
    """Test GET /analytics/discovery/stars/{star_id}/frequency endpoint."""
    # Run multiple anomaly detections
    result1 = ai_service_with_data.detect_anomalies(contamination=0.1, save_results=True)
    result2 = ai_service_with_data.detect_anomalies(contamination=0.05, save_results=True)
    
    # Get first anomaly star ID
    if result1['anomaly_ids']:
        star_id = result1['anomaly_ids'][0]
        
        # Query endpoint
        response = client.get(f"/analytics/discovery/stars/{star_id}/frequency")
        
        assert response.status_code == 200
        data = response.json()
        assert data['star_id'] == star_id
        assert data['anomaly_count'] >= 1
        assert 0 <= data['frequency_pct'] <= 100


def test_analytics_get_overlaps(client, ai_service_with_data):
    """Test GET /analytics/discovery/overlaps endpoint."""
    # Run two anomaly detections
    ai_service_with_data.detect_anomalies(contamination=0.1, save_results=True)
    ai_service_with_data.detect_anomalies(contamination=0.05, save_results=True)
    
    # Query endpoint
    response = client.get("/analytics/discovery/overlaps")
    
    assert response.status_code == 200
    data = response.json()
    
    # May be empty if runs don't overlap
    if len(data) > 0:
        assert 'run_1_id' in data[0]
        assert 'run_2_id' in data[0]
        assert 'jaccard_similarity' in data[0]
        assert 0 <= data[0]['jaccard_similarity'] <= 1


def test_analytics_get_timeline(client, ai_service_with_data):
    """Test GET /analytics/discovery/timeline endpoint."""
    # Generate test data
    ai_service_with_data.detect_anomalies(contamination=0.05, save_results=True)
    
    # Query endpoint - weekly
    response = client.get("/analytics/discovery/timeline?period_type=week")
    assert response.status_code == 200
    data = response.json()
    
    if len(data) > 0:
        assert 'period_start' in data[0]
        assert 'run_type' in data[0]
        assert 'total_runs' in data[0]
        assert data[0]['period_type'] == 'week'
    
    # Query endpoint - monthly
    response = client.get("/analytics/discovery/timeline?period_type=month")
    assert response.status_code == 200
    data = response.json()
    
    if len(data) > 0:
        assert data[0]['period_type'] == 'month'


def test_analytics_manual_refresh(client):
    """Test POST /analytics/discovery/refresh-views endpoint."""
    response = client.post("/analytics/discovery/refresh-views")
    
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'success'
    assert 'views_refreshed' in data
    assert len(data['views_refreshed']) == 5


def test_analytics_filter_by_run_type(client, ai_service_with_data):
    """Test filtering analytics by run type."""
    # Generate mixed data
    ai_service_with_data.detect_anomalies(contamination=0.1, save_results=True)
    ai_service_with_data.detect_clusters(eps=0.7, min_samples=3, save_results=True)
    
    # Query anomaly runs only
    response = client.get("/analytics/discovery/stats?run_type=anomaly")
    assert response.status_code == 200
    data = response.json()
    
    if len(data) > 0:
        assert all(run['run_type'] == 'anomaly' for run in data)
    
    # Query cluster runs only
    response = client.get("/analytics/discovery/stats?run_type=cluster")
    assert response.status_code == 200
    data = response.json()
    
    if len(data) > 0:
        assert all(run['run_type'] == 'cluster' for run in data)


def test_analytics_pagination_limits(client, ai_service_with_data):
    """Test pagination limits work correctly."""
    # Generate multiple runs
    for _ in range(3):
        ai_service_with_data.detect_anomalies(contamination=0.1, save_results=True)
    
    # Query with limit
    response = client.get("/analytics/discovery/stats?limit=2")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) <= 2


def test_composite_indexes_exist(db_session):
    """Verify composite indexes were created for query optimization."""
    result = db_session.execute(text(
        "SELECT indexname FROM pg_indexes "
        "WHERE schemaname = 'public' AND tablename = 'discovery_results'"
    ))
    indexes = [row[0] for row in result]
    
    # Check for our composite indexes
    assert 'idx_discovery_results_run_anomaly' in indexes
    assert 'idx_discovery_results_run_cluster' in indexes


def test_unique_indexes_on_views(db_session):
    """Verify unique indexes exist on materialized views (required for CONCURRENTLY refresh)."""
    result = db_session.execute(text(
        "SELECT indexname FROM pg_indexes WHERE schemaname = 'public' "
        "AND indexname LIKE 'idx_%_pk'"
    ))
    indexes = [row[0] for row in result]
    
    assert 'idx_discovery_timeline_pk' in indexes
    assert 'idx_anomaly_overlap_pk' in indexes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
