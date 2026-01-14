"""Test AI Discovery Service."""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.services.ai_discovery import AIDiscoveryService

db = SessionLocal()
try:
    service = AIDiscoveryService(db)
    
    # Test anomaly detection - returns list of anomalies
    anomalies = service.detect_anomalies(contamination=0.1)
    print(f"Anomaly Detection: {len(anomalies)} anomalies found")
    
    # Test clustering - returns dict
    result = service.detect_clusters(eps=5.0, min_samples=3)
    print(f"Clustering: {result.get('n_clusters', 0)} clusters found")
    print(f"  Noise points: {result.get('n_noise', 0)}")
    
    print("\n=== AI Discovery Service working ===")
finally:
    db.close()
