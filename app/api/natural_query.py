"""
Natural Language Query API Endpoint
Accepts plain English queries and returns star data
Enhanced with optional AI Research Assistant
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from sqlalchemy import and_, or_
from app.database import SessionLocal
from app.models import UnifiedStarCatalog
from app.services.nl_query_service import NLQueryParser
from app.services.ai_research_assistant import AIResearchAssistant
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nl-query", tags=["Natural Language Query"])

# Initialize parser and optional AI assistant
nl_parser = NLQueryParser()
ai_assistant = AIResearchAssistant()


class NLQueryRequest(BaseModel):
    """Request model for natural language query"""
    query: str
    page: int = 1
    page_size: int = 100
    ai_enhanced: bool = False  # Optional: Enable AI Research Assistant


class NLQueryResponse(BaseModel):
    """Response model for natural language query"""
    intent: str
    explanation: str
    confidence: float
    results: List[Dict]
    total_count: int
    filters_applied: Dict
    # AI Research Assistant fields (optional, only when ai_enhanced=True)
    ai_analysis: Optional[Dict] = None
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
        
        # Check if intent is unsupported
        if parsed.get('status') == 'UNSUPPORTED':
            # Return educational feedback without database query
            return NLQueryResponse(
                intent=parsed['intent'],
                explanation=parsed['explanation'],
                confidence=0.0,
                results=[],
                total_count=0,
                filters_applied={},
                suggestions=parsed.get('suggestions', []),
                ai_analysis={
                    'unsupported_intent': True,
                    'reason': parsed.get('reason', ''),
                    'educational': parsed.get('educational', ''),
                    'supported_intents': parsed.get('supported_intents', [])
                }
            )
        
        # Optional: Enhance with AI Research Assistant
        if request.ai_enhanced:
            try:
                parsed = ai_assistant.enhance_query_intent(parsed)
                logger.info(f"AI-enhanced query interpretation: {parsed.get('research_context', {})}")
            except Exception as ai_error:
                logger.warning(f"AI enhancement failed, continuing with standard parsing: {ai_error}")
        
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
                    confidence=parsed.get('parse_confidence', 0.5),  # Use new field name
                    results=[],
                    total_count=total_count,
                    filters_applied=filters,
                    suggestions=parsed['suggestions'],
                    ai_analysis=None  # No results to analyze
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
            
            # Optional: Apply AI Research Assistant analysis
            ai_analysis = None
            if request.ai_enhanced and results:
                try:
                    research_context = parsed.get('research_context', {})
                    analysis_result = ai_assistant.analyze_results(
                        results, 
                        research_context,
                        parsed['intent']
                    )
                    ai_analysis = ai_assistant.format_for_api(analysis_result, results)
                    logger.info(f"AI analysis complete: {len(analysis_result.get('insights', []))} insights generated")
                except Exception as ai_error:
                    logger.warning(f"AI analysis failed, returning standard results: {ai_error}")
                    ai_analysis = ai_assistant.fallback_response(str(ai_error))
            
            return NLQueryResponse(
                intent=parsed['intent'],
                explanation=parsed['explanation'],
                confidence=parsed.get('parse_confidence', 0.5),  # Use new field name
                results=results,
                total_count=total_count,
                filters_applied=filters,
                suggestions=parsed['suggestions'],
                ai_analysis=ai_analysis
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
