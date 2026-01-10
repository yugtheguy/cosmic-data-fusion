"""
Health check API endpoint for COSMIC Data Fusion.

Provides system health status for monitoring and debugging.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.schemas import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check API and database health status."
)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """
    Health check endpoint.
    
    Verifies:
    - API is running
    - Database connection is working
    
    Args:
        db: Database session (injected)
        
    Returns:
        HealthResponse with service and database status
    """
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        service="COSMIC Data Fusion API",
        database=db_status
    )
