"""
Stage 1 Test: Discovery Models Database Integration
Tests that DiscoveryRun and DiscoveryResult models work with PostgreSQL.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.models import DiscoveryRun, DiscoveryResult, UnifiedStarCatalog


@pytest.fixture(scope="module")
def setup_database():
    """Create all tables before tests."""
    Base.metadata.create_all(bind=engine)
    yield
    # Tables persist for other tests


@pytest.fixture
def db_session(setup_database):
    """Provide a database session for each test."""
    db = next(get_db())
    yield db
    db.close()


def test_discovery_run_creation(db_session: Session):
    """Test creating a DiscoveryRun record."""
    run = DiscoveryRun(
        run_type="anomaly",
        parameters={"contamination": 0.05, "random_state": 42},
        dataset_filter={"magnitude_min": 10.0, "magnitude_max": 15.0},
        total_stars=1000,
        results_summary={"n_anomalies": 50, "mean_score": -0.15}
    )
    
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    
    # Verify auto-generated fields
    assert run.id is not None
    assert run.run_id is not None
    assert len(run.run_id) == 36  # UUID format
    assert run.created_at is not None
    assert isinstance(run.created_at, datetime)
    
    # Verify data fields
    assert run.run_type == "anomaly"
    assert run.parameters["contamination"] == 0.05
    assert run.total_stars == 1000
    assert run.results_summary["n_anomalies"] == 50
    
    print(f"✅ Created DiscoveryRun: {run}")


def test_discovery_run_query_by_run_id(db_session: Session):
    """Test querying DiscoveryRun by run_id index."""
    # Create a run
    run = DiscoveryRun(
        run_type="cluster",
        parameters={"eps": 0.5, "min_samples": 5},
        dataset_filter=None,
        total_stars=2000,
        results_summary={"n_clusters": 10, "n_noise": 100}
    )
    db_session.add(run)
    db_session.commit()
    
    run_id = run.run_id
    
    # Query by run_id (indexed column)
    retrieved = db_session.query(DiscoveryRun).filter(DiscoveryRun.run_id == run_id).first()
    
    assert retrieved is not None
    assert retrieved.run_id == run_id
    assert retrieved.run_type == "cluster"
    assert retrieved.parameters["eps"] == 0.5
    
    print(f"✅ Queried DiscoveryRun by run_id: {retrieved}")


def test_discovery_run_query_by_type(db_session: Session):
    """Test querying DiscoveryRuns by type (indexed column)."""
    # Create multiple runs
    anomaly_run = DiscoveryRun(
        run_type="anomaly",
        parameters={"contamination": 0.1},
        total_stars=500,
        results_summary={}
    )
    cluster_run = DiscoveryRun(
        run_type="cluster",
        parameters={"eps": 1.0},
        total_stars=1500,
        results_summary={}
    )
    
    db_session.add_all([anomaly_run, cluster_run])
    db_session.commit()
    
    # Query by run_type
    anomaly_runs = db_session.query(DiscoveryRun).filter(
        DiscoveryRun.run_type == "anomaly"
    ).all()
    
    assert len(anomaly_runs) >= 1
    assert all(r.run_type == "anomaly" for r in anomaly_runs)
    
    print(f"✅ Found {len(anomaly_runs)} anomaly runs")


def test_discovery_result_creation(db_session: Session):
    """Test creating DiscoveryResult records."""
    # First create a discovery run
    run = DiscoveryRun(
        run_type="anomaly",
        parameters={"contamination": 0.05},
        total_stars=100,
        results_summary={"n_anomalies": 5}
    )
    db_session.add(run)
    db_session.commit()
    
    # Create a star to reference
    star = UnifiedStarCatalog(
        original_source="Gaia",
        source_id="test_star_123",
        ra_deg=180.0,
        dec_deg=45.0,
        brightness_mag=12.0,
        raw_frame="ICRS"
    )
    db_session.add(star)
    db_session.commit()
    
    # Create discovery results
    result = DiscoveryResult(
        run_id=run.run_id,
        star_id=star.id,
        is_anomaly=1,
        anomaly_score=-0.75,
        cluster_id=None
    )
    
    db_session.add(result)
    db_session.commit()
    db_session.refresh(result)
    
    # Verify fields
    assert result.id is not None
    assert result.run_id == run.run_id
    assert result.star_id == star.id
    assert result.is_anomaly == 1
    assert result.anomaly_score == -0.75
    assert result.cluster_id is None
    assert result.created_at is not None
    
    print(f"✅ Created DiscoveryResult: {result}")


def test_discovery_results_query_by_run_id(db_session: Session):
    """Test querying DiscoveryResults by run_id (indexed)."""
    # Create a run
    run = DiscoveryRun(
        run_type="anomaly",
        parameters={"contamination": 0.1},
        total_stars=50,
        results_summary={"n_anomalies": 5}
    )
    db_session.add(run)
    db_session.commit()
    
    # Create multiple stars
    stars = [
        UnifiedStarCatalog(
            original_source="Test",
            source_id=f"star_{i}",
            ra_deg=float(i),
            dec_deg=0.0,
            brightness_mag=12.0,
            raw_frame="ICRS"
        )
        for i in range(3)
    ]
    db_session.add_all(stars)
    db_session.commit()
    
    # Create results for each star
    results = [
        DiscoveryResult(
            run_id=run.run_id,
            star_id=star.id,
            is_anomaly=i % 2,  # Alternate anomaly status
            anomaly_score=-0.5 if i % 2 else 0.3
        )
        for i, star in enumerate(stars)
    ]
    db_session.add_all(results)
    db_session.commit()
    
    # Query all results for this run
    retrieved_results = db_session.query(DiscoveryResult).filter(
        DiscoveryResult.run_id == run.run_id
    ).all()
    
    assert len(retrieved_results) == 3
    assert all(r.run_id == run.run_id for r in retrieved_results)
    
    print(f"✅ Queried {len(retrieved_results)} results for run {run.run_id}")


def test_discovery_results_query_by_anomaly_status(db_session: Session):
    """Test querying DiscoveryResults by is_anomaly (indexed)."""
    # Create a run
    run = DiscoveryRun(
        run_type="anomaly",
        parameters={"contamination": 0.05},
        total_stars=100,
        results_summary={}
    )
    db_session.add(run)
    db_session.commit()
    
    # Create stars
    stars = [
        UnifiedStarCatalog(
            original_source="Test",
            source_id=f"anomaly_star_{i}",
            ra_deg=float(i * 10),
            dec_deg=0.0,
            brightness_mag=12.0,
            raw_frame="ICRS"
        )
        for i in range(5)
    ]
    db_session.add_all(stars)
    db_session.commit()
    
    # Create results (2 anomalies, 3 normal)
    results = [
        DiscoveryResult(
            run_id=run.run_id,
            star_id=stars[0].id,
            is_anomaly=1,
            anomaly_score=-0.8
        ),
        DiscoveryResult(
            run_id=run.run_id,
            star_id=stars[1].id,
            is_anomaly=1,
            anomaly_score=-0.6
        ),
        DiscoveryResult(
            run_id=run.run_id,
            star_id=stars[2].id,
            is_anomaly=0,
            anomaly_score=0.2
        ),
        DiscoveryResult(
            run_id=run.run_id,
            star_id=stars[3].id,
            is_anomaly=0,
            anomaly_score=0.1
        ),
        DiscoveryResult(
            run_id=run.run_id,
            star_id=stars[4].id,
            is_anomaly=0,
            anomaly_score=0.3
        ),
    ]
    db_session.add_all(results)
    db_session.commit()
    
    # Query anomalies only for this run
    anomalies = db_session.query(DiscoveryResult).filter(
        DiscoveryResult.run_id == run.run_id,
        DiscoveryResult.is_anomaly == 1
    ).all()
    
    assert len(anomalies) == 2  # Exactly 2 anomalies in this run
    assert all(r.is_anomaly == 1 for r in anomalies)
    assert all(r.anomaly_score < 0 for r in anomalies)
    
    print(f"✅ Found {len(anomalies)} anomaly results")


def test_discovery_results_query_by_cluster_id(db_session: Session):
    """Test querying DiscoveryResults by cluster_id (indexed)."""
    # Create a clustering run
    run = DiscoveryRun(
        run_type="cluster",
        parameters={"eps": 0.5, "min_samples": 3},
        total_stars=200,
        results_summary={"n_clusters": 5}
    )
    db_session.add(run)
    db_session.commit()
    
    # Create stars
    stars = [
        UnifiedStarCatalog(
            original_source="Test",
            source_id=f"cluster_star_{i}",
            ra_deg=float(i * 5),
            dec_deg=0.0,
            brightness_mag=12.0,
            raw_frame="ICRS"
        )
        for i in range(4)
    ]
    db_session.add_all(stars)
    db_session.commit()
    
    # Create results with different clusters
    results = [
        DiscoveryResult(run_id=run.run_id, star_id=stars[0].id, is_anomaly=0, cluster_id=0),
        DiscoveryResult(run_id=run.run_id, star_id=stars[1].id, is_anomaly=0, cluster_id=0),
        DiscoveryResult(run_id=run.run_id, star_id=stars[2].id, is_anomaly=0, cluster_id=1),
        DiscoveryResult(run_id=run.run_id, star_id=stars[3].id, is_anomaly=0, cluster_id=-1),  # Noise
    ]
    db_session.add_all(results)
    db_session.commit()
    
    # Query cluster 0 members
    cluster_0_members = db_session.query(DiscoveryResult).filter(
        DiscoveryResult.cluster_id == 0
    ).all()
    
    assert len(cluster_0_members) >= 2  # May have more from previous tests
    assert all(r.cluster_id == 0 for r in cluster_0_members)
    
    # Query noise points (cluster_id = -1)
    noise_points = db_session.query(DiscoveryResult).filter(
        DiscoveryResult.cluster_id == -1
    ).all()
    
    assert len(noise_points) >= 1
    assert all(r.cluster_id == -1 for r in noise_points)
    
    print(f"✅ Found {len(cluster_0_members)} stars in cluster 0, {len(noise_points)} noise points")


def test_discovery_results_combined_query(db_session: Session):
    """Test complex query combining run_id and anomaly status."""
    # Create a run
    run = DiscoveryRun(
        run_type="anomaly",
        parameters={"contamination": 0.1},
        total_stars=100,
        results_summary={"n_anomalies": 10}
    )
    db_session.add(run)
    db_session.commit()
    
    # Create stars
    stars = [
        UnifiedStarCatalog(
            original_source="Test",
            source_id=f"combined_star_{i}",
            ra_deg=float(i * 15),
            dec_deg=0.0,
            brightness_mag=12.0,
            raw_frame="ICRS"
        )
        for i in range(6)
    ]
    db_session.add_all(stars)
    db_session.commit()
    
    # Create mixed results
    results = [
        DiscoveryResult(run_id=run.run_id, star_id=stars[0].id, is_anomaly=1, anomaly_score=-0.9),
        DiscoveryResult(run_id=run.run_id, star_id=stars[1].id, is_anomaly=1, anomaly_score=-0.7),
        DiscoveryResult(run_id=run.run_id, star_id=stars[2].id, is_anomaly=0, anomaly_score=0.1),
        DiscoveryResult(run_id=run.run_id, star_id=stars[3].id, is_anomaly=0, anomaly_score=0.2),
    ]
    db_session.add_all(results)
    db_session.commit()
    
    # Complex query: get anomalies for this specific run, ordered by score
    anomalies_in_run = db_session.query(DiscoveryResult).filter(
        DiscoveryResult.run_id == run.run_id,
        DiscoveryResult.is_anomaly == 1
    ).order_by(DiscoveryResult.anomaly_score).all()
    
    assert len(anomalies_in_run) == 2
    assert anomalies_in_run[0].anomaly_score <= anomalies_in_run[1].anomaly_score
    assert all(r.run_id == run.run_id for r in anomalies_in_run)
    assert all(r.is_anomaly == 1 for r in anomalies_in_run)
    
    print(f"✅ Complex query returned {len(anomalies_in_run)} anomalies, properly ordered")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
