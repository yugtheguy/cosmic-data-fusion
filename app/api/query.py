"""
Query & Export API endpoints for COSMIC Data Fusion.

Provides endpoints for:
- Advanced search with multiple filters
- Data export in CSV, JSON, and VOTable formats

This module is READ-ONLY and does not modify any database records.

Phase: 3 - Query & Export Engine
"""

import logging
from typing import Optional, List
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.query_builder import QueryBuilder, QueryFilters
from app.services.exporter import DataExporter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["Query & Export"])


# ============================================================
# ENUMS
# ============================================================

class ExportFormat(str, Enum):
    """Supported export formats."""
    CSV = "csv"
    JSON = "json"
    VOTABLE = "votable"


# ============================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================

class FilterParams(BaseModel):
    """
    Filter parameters for querying the star catalog.
    
    All fields are optional - only provided values will be used as filters.
    This enables flexible queries from simple to complex.
    """
    
    min_mag: Optional[float] = Field(
        default=None,
        description="Minimum magnitude (brightest limit). Lower values = brighter stars.",
        examples=[0.0, 5.0]
    )
    max_mag: Optional[float] = Field(
        default=None,
        description="Maximum magnitude (faintest limit). Higher values = dimmer stars.",
        examples=[10.0, 15.0]
    )
    min_parallax: Optional[float] = Field(
        default=None,
        ge=0,
        description="Minimum parallax in milliarcseconds. Higher parallax = closer stars.",
        examples=[1.0, 10.0]
    )
    max_parallax: Optional[float] = Field(
        default=None,
        ge=0,
        description="Maximum parallax in milliarcseconds.",
        examples=[100.0, 1000.0]
    )
    ra_min: Optional[float] = Field(
        default=None,
        ge=0,
        le=360.0,
        description="Minimum Right Ascension in degrees [0, 360].",
        examples=[0.0, 180.0]
    )
    ra_max: Optional[float] = Field(
        default=None,
        ge=0,
        le=360.0,
        description="Maximum Right Ascension in degrees [0, 360].",
        examples=[90.0, 270.0]
    )
    dec_min: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90,
        description="Minimum Declination in degrees [-90, +90].",
        examples=[-45.0, 0.0]
    )
    dec_max: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90,
        description="Maximum Declination in degrees [-90, +90].",
        examples=[45.0, 90.0]
    )
    original_source: Optional[str] = Field(
        default=None,
        description="Filter by source catalog name (e.g., 'Gaia DR3').",
        examples=["Gaia DR3", "SDSS"]
    )
    limit: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum number of results to return (default 1000, max 10000)."
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of results to skip (for pagination)."
    )


class StarRecord(BaseModel):
    """Schema for a single star record in search results."""
    id: int
    source_id: str
    ra_deg: float
    dec_deg: float
    brightness_mag: float
    parallax_mas: Optional[float]
    distance_pc: Optional[float]
    original_source: str


class SearchResponse(BaseModel):
    """Response schema for search endpoint."""
    success: bool
    message: str
    total_count: int
    returned_count: int
    limit: int
    offset: int
    records: List[StarRecord]


# ============================================================
# API ENDPOINTS
# ============================================================

@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search star catalog with filters",
    description="""
Search the unified star catalog with optional filters.

**Available Filters:**
- **Magnitude**: `min_mag`, `max_mag` (brightness range)
- **Parallax**: `min_parallax`, `max_parallax` (distance proxy)
- **Position**: `ra_min`, `ra_max`, `dec_min`, `dec_max` (bounding box)
- **Source**: `original_source` (filter by catalog, e.g., "Gaia DR3")

**Pagination:**
- `limit`: Max results per page (default 1000, max 10000)
- `offset`: Skip N results (for pagination)

**Example Use Cases:**
1. Find bright stars: `{"max_mag": 5.0}`
2. Northern hemisphere: `{"dec_min": 0.0}`
3. Gaia stars only: `{"original_source": "Gaia DR3"}`
4. Combined: `{"min_mag": 2.0, "max_mag": 8.0, "dec_min": -45, "dec_max": 45}`
    """
)
async def search_stars(
    filters: FilterParams,
    db: Session = Depends(get_db)
) -> SearchResponse:
    """
    Search the star catalog with flexible filters.
    
    All filter parameters are optional. Only non-null values are applied.
    Results are limited to prevent memory issues (default 1000, max 10000).
    """
    try:
        logger.info(f"Search request with filters: {filters}")
        
        # Convert Pydantic model to QueryFilters dataclass
        query_filters = QueryFilters(
            min_mag=filters.min_mag,
            max_mag=filters.max_mag,
            min_parallax=filters.min_parallax,
            max_parallax=filters.max_parallax,
            ra_min=filters.ra_min,
            ra_max=filters.ra_max,
            dec_min=filters.dec_min,
            dec_max=filters.dec_max,
            original_source=filters.original_source,
            limit=filters.limit,
            offset=filters.offset
        )
        
        # Build and execute query
        builder = QueryBuilder(db)
        query = builder.build_query(query_filters)
        results = query.all()
        
        # Get total count (without pagination)
        total_count = builder.count_results(query_filters)
        
        # Convert to response records
        records = []
        for star in results:
            records.append(StarRecord(
                id=star.id,
                source_id=star.source_id,
                ra_deg=star.ra_deg,
                dec_deg=star.dec_deg,
                brightness_mag=star.brightness_mag,
                parallax_mas=star.parallax_mas,
                distance_pc=star.distance_pc,
                original_source=star.original_source
            ))
        
        return SearchResponse(
            success=True,
            message=f"Found {total_count} matching stars, returning {len(records)}.",
            total_count=total_count,
            returned_count=len(records),
            limit=filters.limit,
            offset=filters.offset,
            records=records
        )
        
    except Exception as e:
        logger.exception(f"Search error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "search_failed", "message": str(e)}
        )


@router.get(
    "/export",
    summary="Export star catalog data",
    description="""
Export filtered star catalog data in various formats.

**Supported Formats:**
- `csv`: Comma-separated values (Excel compatible)
- `json`: JSON with metadata and records
- `votable`: Virtual Observatory Table (astronomical standard)

**VOTable Format:**
The VOTable format is the international standard for astronomical data exchange.
It includes:
- Column metadata (descriptions, units)
- UCDs (Unified Content Descriptors) for semantic meaning
- Compatible with TOPCAT, Aladin, DS9, and other astronomy tools

**All filters from /search are available as query parameters.**

The response will trigger a file download with appropriate filename.
    """
)
async def export_data(
    format: ExportFormat = QueryParam(
        default=ExportFormat.CSV,
        description="Export format: csv, json, or votable"
    ),
    min_mag: Optional[float] = QueryParam(default=None, description="Minimum magnitude"),
    max_mag: Optional[float] = QueryParam(default=None, description="Maximum magnitude"),
    min_parallax: Optional[float] = QueryParam(default=None, ge=0, description="Minimum parallax (mas)"),
    max_parallax: Optional[float] = QueryParam(default=None, ge=0, description="Maximum parallax (mas)"),
    ra_min: Optional[float] = QueryParam(default=None, ge=0, lt=360, description="Min RA (degrees)"),
    ra_max: Optional[float] = QueryParam(default=None, ge=0, lt=360, description="Max RA (degrees)"),
    dec_min: Optional[float] = QueryParam(default=None, ge=-90, le=90, description="Min Dec (degrees)"),
    dec_max: Optional[float] = QueryParam(default=None, ge=-90, le=90, description="Max Dec (degrees)"),
    original_source: Optional[str] = QueryParam(default=None, description="Source catalog name"),
    limit: int = QueryParam(default=10000, ge=1, le=100000, description="Max records to export"),
    db: Session = Depends(get_db)
) -> Response:
    """
    Export star catalog data with optional filters.
    
    Returns a file download response with the data in the requested format.
    The Content-Disposition header triggers browser download.
    """
    try:
        logger.info(f"Export request: format={format}, limit={limit}")
        
        # Build query filters
        query_filters = QueryFilters(
            min_mag=min_mag,
            max_mag=max_mag,
            min_parallax=min_parallax,
            max_parallax=max_parallax,
            ra_min=ra_min,
            ra_max=ra_max,
            dec_min=dec_min,
            dec_max=dec_max,
            original_source=original_source,
            limit=limit,
            offset=0
        )
        
        # Execute query
        builder = QueryBuilder(db)
        query = builder.build_query(query_filters)
        results = query.all()
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail={"error": "no_data", "message": "No records match the specified filters"}
            )
        
        # Create exporter
        exporter = DataExporter(results)
        
        # Generate timestamp for filename
        from datetime import datetime
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Export based on format
        if format == ExportFormat.CSV:
            content = exporter.to_csv()
            media_type = "text/csv"
            filename = f"cosmic_export_{timestamp}.csv"
            
        elif format == ExportFormat.JSON:
            content = exporter.to_json()
            media_type = "application/json"
            filename = f"cosmic_export_{timestamp}.json"
            
        elif format == ExportFormat.VOTABLE:
            content = exporter.to_votable()
            media_type = "application/x-votable+xml"
            filename = f"cosmic_export_{timestamp}.vot"
        
        logger.info(f"Exporting {exporter.get_record_count()} records as {format.value}")
        
        # Return response with download headers
        # Content-Disposition: attachment forces browser to download
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Record-Count": str(exporter.get_record_count()),
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Export error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "export_failed", "message": str(e)}
        )


@router.get(
    "/sources",
    summary="List available source catalogs",
    description="Get a list of all unique source catalogs in the database."
)
async def list_sources(
    db: Session = Depends(get_db)
) -> dict:
    """
    List all unique source catalogs available for filtering.
    
    Returns the distinct values in the original_source column.
    """
    try:
        from app.models import UnifiedStarCatalog
        from sqlalchemy import distinct
        
        sources = db.query(distinct(UnifiedStarCatalog.original_source)).all()
        source_list = [s[0] for s in sources if s[0]]
        
        return {
            "success": True,
            "count": len(source_list),
            "sources": source_list
        }
        
    except Exception as e:
        logger.exception(f"Error listing sources: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)}
        )
