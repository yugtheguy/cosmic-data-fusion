"""
API routes package for COSMIC Data Fusion.

Available routers:
- ingest: Star ingestion endpoints
- search: Spatial search endpoints
- datasets: Dataset management endpoints
- visualize: Visualization data endpoints
- ai: AI Discovery endpoints (anomaly detection, clustering)
- query: Query & Export endpoints (advanced search, CSV/JSON/VOTable export)
- health: Health check endpoint
"""

from app.api import ingest, search, datasets, visualize, ai, query, health

__all__ = ["ingest", "search", "datasets", "visualize", "ai", "query", "health"]
