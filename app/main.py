"""
FastAPI application for COSMIC Data Fusion.

Main entry point that:
- Configures logging
- Initializes database
- Registers API routers
- Provides OpenAPI documentation

Run with: uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.api import ingest, search, health, datasets, visualize, ai, query, harmonize, schema_mapper, errors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Startup:
        - Initialize database tables
        - Log startup message
        
    Shutdown:
        - Log shutdown message
        - (Add cleanup if needed)
    """
    # Startup
    logger.info("Starting COSMIC Data Fusion API...")
    init_db()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down COSMIC Data Fusion API...")


# Create FastAPI application
app = FastAPI(
    title="COSMIC Data Fusion API",
    description="""
## Astronomical Data Standardization Backend

A research-grade backend for ingesting and querying astronomical data
with automatic coordinate standardization to ICRS J2000.

### Features

* **Multi-Frame Ingestion**: Accept coordinates in ICRS, FK5, or Galactic frames
* **Automatic Transformation**: All coordinates converted to ICRS J2000 using Astropy
* **Bounding Box Search**: Rectangular region queries on RA/Dec
* **Cone Search**: Circular region queries with proper spherical geometry
* **AI Discovery**: Anomaly detection and clustering for stellar analysis

### Coordinate Systems

| Frame | Description | Input Parameters |
|-------|-------------|------------------|
| ICRS | International Celestial Reference System (modern standard) | RA, Dec |
| FK5 | Fifth Fundamental Catalog (J2000 epoch) | RA, Dec |
| Galactic | Galactic coordinate system | l (longitude), b (latitude) |

### Technical Notes

- All transformations use Astropy's SkyCoord for accuracy
- Coordinates stored as Float64 (sub-microarcsecond precision)
- Database uses composite index on (ra_deg, dec_deg) for fast spatial queries
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register API routers
app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(datasets.router)
app.include_router(visualize.router)
app.include_router(ai.router)  # AI Discovery endpoints (Phase 5)
app.include_router(query.router)  # Query & Export endpoints (Phase 3)
app.include_router(harmonize.router)  # Harmonization endpoints (Phase 2)
app.include_router(schema_mapper.router)  # Schema Mapper endpoints
app.include_router(errors.router)  # Error Reporting endpoints (Layer 1)
app.include_router(health.router)


@app.get("/", tags=["Root"])
def root():
    """
    Root endpoint with API information.
    
    Returns:
        Welcome message and documentation links
    """
    return {
        "service": "COSMIC Data Fusion API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health"
    }


# Entry point for direct execution
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
