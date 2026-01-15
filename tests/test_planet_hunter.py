"""
Test suite for Planet Hunter module.

Tests exoplanet detection using TESS light curves and BLS analysis.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models_exoplanet import ExoplanetCandidate
from app.services.planet_hunter import PlanetHunterService


# ==================== Fixtures ====================

@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(bind=engine)
    db = TestSessionLocal()
    yield db
    db.close()


@pytest.fixture
def mock_lightkurve_success():
    """Mock successful lightkurve data retrieval."""
    with patch('app.services.planet_hunter.lk') as mock_lk:
        # Mock search result
        mock_search = MagicMock()
        mock_search.__len__ = Mock(return_value=1)
        mock_search.table = {'observation': ['TESS Sector 9']}
        
        # Mock light curve with realistic data
        mock_lc = MagicMock()
        mock_lc.__len__ = Mock(return_value=10000)
        
        # Create synthetic transit signal
        import numpy as np
        time = np.linspace(0, 27, 10000)  # 27 days
        flux = np.ones(10000) + np.random.normal(0, 0.001, 10000)  # Add noise
        
        # Add periodic transits (period=3.85 days, depth=0.005)
        period = 3.85
        for t0 in np.arange(0, 27, period):
            mask = np.abs(time - t0) < 0.05  # Transit duration ~ 0.1 day
            flux[mask] *= 0.995  # 0.5% depth
        
        mock_lc.time.value = time
        mock_lc.flux.value = flux
        mock_lc.normalize.return_value = mock_lc
        mock_lc.remove_nans.return_value = mock_lc
        mock_lc.remove_outliers.return_value = mock_lc
        mock_lc.flatten.return_value = mock_lc
        
        # Mock periodogram
        mock_periodogram = MagicMock()
        mock_periodogram.period_at_max_power.value = 3.852826
        mock_periodogram.max_power.value = 15.2
        mock_periodogram.power.value = np.random.uniform(0, 5, 1000)
        
        # Mock transit parameters
        mock_params = {
            'transit_time': Mock(value=1683.4521),
            'duration': Mock(to=Mock(return_value=Mock(value=2.34))),
            'depth': Mock(value=0.00453)
        }
        mock_periodogram.get_transit_parameters.return_value = mock_params
        
        mock_lc.to_periodogram.return_value = mock_periodogram
        
        # Mock folded light curve
        mock_folded = MagicMock()
        phase = np.linspace(-0.5, 0.5, 1000)
        folded_flux = np.ones(1000)
        transit_mask = np.abs(phase) < 0.05
        folded_flux[transit_mask] = 0.995
        
        mock_folded.phase.value = phase
        mock_folded.flux.value = folded_flux
        mock_folded.bin.return_value = mock_folded
        
        mock_lc.fold.return_value = mock_folded
        
        # Setup mock chain
        mock_search.download.return_value = [mock_lc]
        mock_lk.search_lightcurve.return_value = mock_search
        
        yield mock_lk


@pytest.fixture
def mock_lightkurve_no_data():
    """Mock lightkurve with no data available."""
    with patch('app.services.planet_hunter.lk') as mock_lk:
        mock_search = MagicMock()
        mock_search.__len__ = Mock(return_value=0)
        mock_lk.search_lightcurve.return_value = mock_search
        yield mock_lk


# ==================== Database Model Tests ====================

def test_exoplanet_candidate_model(test_db):
    """Test ExoplanetCandidate model creation and fields."""
    viz_data = json.dumps({
        "phase_binned": [-0.5, 0.0, 0.5],
        "flux_binned": [1.0, 0.995, 1.0],
        "period": 3.85,
        "depth": 0.005
    })
    
    candidate = ExoplanetCandidate(
        source_id="261136679",
        period=3.852826,
        transit_time=1683.4521,
        duration=2.34,
        depth=0.00453,
        power=15.2,
        snr=8.5,
        num_transits=12,
        visualization_json=viz_data,
        mission="TESS",
        sector=9,
        status="candidate"
    )
    
    test_db.add(candidate)
    test_db.commit()
    test_db.refresh(candidate)
    
    assert candidate.id is not None
    assert candidate.source_id == "261136679"
    assert candidate.period == 3.852826
    assert candidate.depth == 0.00453
    assert candidate.status == "candidate"
    
    # Test to_dict method
    data = candidate.to_dict()
    assert data['source_id'] == "261136679"
    assert data['period_days'] == 3.852826
    assert data['depth_ppm'] == 4530.0
    assert data['depth_percent'] == 0.453


def test_candidate_repr(test_db):
    """Test string representation."""
    candidate = ExoplanetCandidate(
        source_id="12345",
        period=5.0,
        transit_time=1000.0,
        duration=3.0,
        depth=0.01,
        power=10.0,
        visualization_json="{}"
    )
    
    repr_str = repr(candidate)
    assert "12345" in repr_str
    assert "5.000d" in repr_str
    assert "1.00%" in repr_str


# ==================== Service Tests ====================

def test_planet_hunter_service_initialization(test_db):
    """Test service initialization."""
    service = PlanetHunterService(test_db)
    assert service.db == test_db


def test_analyze_tic_target_success(test_db, mock_lightkurve_success):
    """Test successful planet detection."""
    service = PlanetHunterService(test_db)
    
    candidate = service.analyze_tic_target("261136679", save_to_db=True)
    
    assert candidate is not None
    assert candidate.source_id == "261136679"
    assert candidate.period > 0
    assert candidate.depth > 0
    assert candidate.power > 0
    assert candidate.mission == "TESS"
    
    # Verify database persistence
    db_candidate = test_db.query(ExoplanetCandidate).first()
    assert db_candidate is not None
    assert db_candidate.source_id == "261136679"


def test_analyze_tic_target_no_data(test_db, mock_lightkurve_no_data):
    """Test handling of missing TESS data."""
    service = PlanetHunterService(test_db)
    
    candidate = service.analyze_tic_target("999999999")
    
    assert candidate is None


def test_analyze_tic_target_custom_period_range(test_db, mock_lightkurve_success):
    """Test custom period search range."""
    service = PlanetHunterService(test_db)
    
    candidate = service.analyze_tic_target(
        "261136679",
        min_period=1.0,
        max_period=10.0,
        num_periods=5000
    )
    
    assert candidate is not None
    assert 1.0 <= candidate.period <= 10.0


def test_get_candidates_by_tic(test_db, mock_lightkurve_success):
    """Test retrieving candidates by TIC ID."""
    service = PlanetHunterService(test_db)
    
    # Create multiple candidates
    service.analyze_tic_target("261136679", save_to_db=True)
    
    candidates = service.get_candidates_by_tic("261136679")
    assert len(candidates) > 0
    assert all(c.source_id == "261136679" for c in candidates)


def test_get_all_candidates(test_db, mock_lightkurve_success):
    """Test retrieving all candidates with filters."""
    service = PlanetHunterService(test_db)
    
    # Create candidate
    candidate = service.analyze_tic_target("261136679", save_to_db=True)
    
    # Get all candidates
    all_candidates = service.get_all_candidates()
    assert len(all_candidates) > 0
    
    # Filter by power
    high_power = service.get_all_candidates(min_power=10.0)
    assert all(c.power >= 10.0 for c in high_power)


def test_update_candidate_status(test_db, mock_lightkurve_success):
    """Test updating candidate validation status."""
    service = PlanetHunterService(test_db)
    
    # Create candidate
    candidate = service.analyze_tic_target("261136679", save_to_db=True)
    original_id = candidate.id
    
    # Update status
    updated = service.update_candidate_status(
        original_id,
        "confirmed",
        "Validated with RV follow-up"
    )
    
    assert updated is not None
    assert updated.status == "confirmed"
    assert updated.notes == "Validated with RV follow-up"


def test_visualization_json_structure(test_db, mock_lightkurve_success):
    """Test visualization JSON contains required fields."""
    service = PlanetHunterService(test_db)
    
    candidate = service.analyze_tic_target("261136679", save_to_db=True)
    
    viz_data = json.loads(candidate.visualization_json)
    
    # Check required fields
    assert "phase_binned" in viz_data
    assert "flux_binned" in viz_data
    assert "period" in viz_data
    assert "depth" in viz_data
    assert "duration_hours" in viz_data
    
    # Check data types
    assert isinstance(viz_data["phase_binned"], list)
    assert isinstance(viz_data["flux_binned"], list)
    assert len(viz_data["phase_binned"]) == len(viz_data["flux_binned"])


def test_candidate_metrics(test_db, mock_lightkurve_success):
    """Test calculation of detection metrics."""
    service = PlanetHunterService(test_db)
    
    candidate = service.analyze_tic_target("261136679", save_to_db=True)
    
    # Verify metrics are reasonable
    assert 0.5 <= candidate.period <= 20.0  # Within search range
    assert 0 < candidate.depth < 0.1  # Reasonable transit depth
    assert 0.1 < candidate.duration < 10.0  # Reasonable duration (hours)
    assert candidate.power > 0
    assert candidate.snr is not None and candidate.snr > 0
    assert candidate.num_transits >= 0


# ==================== API Integration Tests ====================

@pytest.mark.asyncio
async def test_api_planet_hunt_endpoint():
    """Test API endpoint (requires running server)."""
    # Note: This is a placeholder for integration testing
    # In production, use TestClient from fastapi.testclient
    pass


# ==================== Error Handling Tests ====================

def test_error_handling_empty_light_curve(test_db):
    """Test handling of empty light curve."""
    with patch('app.services.planet_hunter.lk') as mock_lk:
        mock_search = MagicMock()
        mock_search.__len__ = Mock(return_value=1)
        mock_search.table = {'observation': ['TESS Sector 9']}
        
        # Empty light curve
        mock_lc = MagicMock()
        mock_lc.__len__ = Mock(return_value=10)  # Too few points
        mock_lc.normalize.return_value = mock_lc
        mock_lc.remove_nans.return_value = mock_lc
        mock_lc.remove_outliers.return_value = mock_lc
        mock_lc.flatten.return_value = mock_lc
        
        mock_search.download.return_value = [mock_lc]
        mock_lk.search_lightcurve.return_value = mock_search
        
        service = PlanetHunterService(test_db)
        candidate = service.analyze_tic_target("261136679")
        
        assert candidate is None


def test_database_rollback_on_error(test_db):
    """Test database rollback on analysis failure."""
    service = PlanetHunterService(test_db)
    
    with patch('app.services.planet_hunter.lk.search_lightcurve') as mock_search:
        mock_search.side_effect = Exception("MAST archive error")
        
        with pytest.raises(Exception):
            service.analyze_tic_target("261136679")
        
        # Verify no partial records in database
        candidates = test_db.query(ExoplanetCandidate).all()
        assert len(candidates) == 0


# ==================== Performance Tests ====================

def test_large_visualization_data_handling(test_db, mock_lightkurve_success):
    """Test handling of large visualization datasets."""
    service = PlanetHunterService(test_db)
    
    candidate = service.analyze_tic_target("261136679", save_to_db=True)
    
    viz_data = json.loads(candidate.visualization_json)
    
    # Verify binning keeps data size reasonable
    assert len(viz_data["phase_binned"]) <= 500
    assert len(viz_data["flux_binned"]) <= 500
    
    # Full data should be limited to 1000 points
    if "phase_full" in viz_data:
        assert len(viz_data["phase_full"]) <= 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
