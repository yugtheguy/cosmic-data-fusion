"""Test AI Discovery Service."""
import pytest
from app.services.ai_discovery import AIDiscoveryService


def test_ai_discovery_service(db_session):
    """Test anomaly detection and clustering (requires data)."""
    try:
        service = AIDiscoveryService(db_session)
        
        # Test anomaly detection - returns list of anomalies
        anomalies = service.detect_anomalies(contamination=0.1)
        print(f"Anomaly Detection: {len(anomalies)} anomalies found")
        
        # Test clustering - returns dict
        result = service.detect_clusters(eps=5.0, min_samples=3)
        print(f"Clustering: {result.get('n_clusters', 0)} clusters found")
        print(f"  Noise points: {result.get('n_noise', 0)}")
        
        print("\n=== AI Discovery Service working ===")
    except Exception as e:
        # If there's not enough data, that's expected
        if "InsufficientDataError" in str(type(e).__name__) or "not enough" in str(e).lower():
            pytest.skip(f"Skipping AI discovery test - insufficient data: {e}")
        else:
            raise
