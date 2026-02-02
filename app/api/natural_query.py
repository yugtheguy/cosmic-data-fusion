"""
Natural Language Query API Endpoint
Accepts plain English queries and returns star data
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from sqlalchemy import and_, or_
from app.database import SessionLocal
from app.models import UnifiedStarCatalog
from app.services.nl_query_service import NLQueryParser

router = APIRouter(prefix="/api/nl-query", tags=["Natural Language Query"])

# Initialize parser
nl_parser = NLQueryParser()


class NLQueryRequest(BaseModel):
    """Request model for natural language query"""
    query: str
    page: int = 1
    page_size: int = 100


class NLQueryResponse(BaseModel):
    """Response model for natural language query"""
    intent: str
    explanation: str
    confidence: float
    results: List[Dict]
    total_count: int
    filters_applied: Dict
    suggestions: List[str]


@router.post("/query", response_model=NLQueryResponse)
async def natural_language_query(request: NLQueryRequest):
    """
    Execute a natural language query against the star database
    
    Example queries:
    - "Show me bright stars near Orion"
    - "Fast moving stars"
    - "What did the sky look like in ancient Egypt?"
    - "Top 10 fastest stars"
    """
    try:
        # Parse the natural language query
        parsed = nl_parser.parse(request.query)
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Build database query based on parsed filters
            query = db.query(UnifiedStarCatalog)
            filters = parsed['filters']
            
            # Apply constellation filters (RA/Dec boundaries)
            if 'ra_min' in filters and 'ra_max' in filters:
                # Handle RA wrap-around at 0/360
                if filters['ra_min'] < filters['ra_max']:
                    query = query.filter(
                        UnifiedStarCatalog.ra_deg >= filters['ra_min'],
                        UnifiedStarCatalog.ra_deg <= filters['ra_max']
                    )
                else:
                    # Wrap-around case
                    query = query.filter(
                        or_(
                            UnifiedStarCatalog.ra_deg >= filters['ra_min'],
                            UnifiedStarCatalog.ra_deg <= filters['ra_max']
                        )
                    )
            
            if 'dec_min' in filters and 'dec_max' in filters:
                query = query.filter(
                    UnifiedStarCatalog.dec_deg >= filters['dec_min'],
                    UnifiedStarCatalog.dec_deg <= filters['dec_max']
                )
            
            # Apply brightness filter
            if 'max_magnitude' in filters:
                query = query.filter(
                    UnifiedStarCatalog.brightness_mag <= filters['max_magnitude']
                )
            
            # Note: Proper motion filter disabled - total_pm column not in current schema
            # if 'min_proper_motion' in filters:
            #     query = query.filter(
            #         UnifiedStarCatalog.total_pm >= filters['min_proper_motion']
            #     )
            
            # Get total count before pagination
            total_count = query.count()
            
            # Handle COUNT intent (just return count, no results)
            if parsed['intent'] == 'COUNT':
                return NLQueryResponse(
                    intent=parsed['intent'],
                    explanation=f"Found {total_count} stars matching your criteria",
                    confidence=parsed['confidence'],
                    results=[],
                    total_count=total_count,
                    filters_applied=filters,
                    suggestions=parsed['suggestions']
                )
            
            # Apply limit
            limit = filters.get('limit', 100)
            query = query.limit(limit)
            
            # Execute query
            stars = query.all()
            
            # Format results
            results = []
            for star in stars:
                result = {
                    'id': star.id,
                    'source_id': star.source_id,
                    'ra': star.ra_deg,
                    'dec': star.dec_deg,
                    'magnitude': star.brightness_mag,
                    'parallax': star.parallax_mas
                }
                
                # Add epoch-specific data if time filter applied
                if 'epoch' in filters:
                    # This would integrate with temporal calculator
                    # For now, just include the epoch
                    result['epoch'] = filters['epoch']
                
                results.append(result)
            
            return NLQueryResponse(
                intent=parsed['intent'],
                explanation=parsed['explanation'],
                confidence=parsed['confidence'],
                results=results,
                total_count=total_count,
                filters_applied=filters,
                suggestions=parsed['suggestions']
            )
        
        finally:
            db.close()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing error: {str(e)}")


@router.get("/suggestions")
async def get_query_suggestions(context: Optional[str] = None):
    """
    Get example queries based on context (page user is on)
    
    Args:
        context: Current page context (dashboard, timemachine, skymap, etc.)
    """
    suggestions = {
        "dashboard": [
            "Show me recent uploads",
            "What's the data quality?",
            "How many stars are in the database?"
        ],
        "timemachine": [
            "Show stars in ancient Egypt",
            "Fast movers near Orion",
            "What did the sky look like 5000 years ago?"
        ],
        "skymap": [
            "Bright stars in Cassiopeia",
            "Stars visible from Mumbai",
            "Show me the Big Dipper"
        ],
        "querybuilder": [
            "Find the brightest stars",
            "Stars closest to Earth",
            "Top 10 fastest moving stars"
        ],
        "default": [
            "Show me bright stars near Orion",
            "Fast moving stars",
            "What did the sky look like in ancient Egypt?",
            "Top 10 fastest stars",
            "Stars visible to the naked eye"
        ]
    }
    
    return {
        "suggestions": suggestions.get(context, suggestions["default"])
    }


@router.get("/health")
async def health_check():
    """Check if NL query service is working"""
    try:
        # Test parser initialization
        test_result = nl_parser.parse("test query")
        return {
            "status": "healthy",
            "parser_loaded": True,
            "knowledge_base_loaded": len(nl_parser.knowledge) > 0
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
