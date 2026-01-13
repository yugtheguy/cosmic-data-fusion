"""
Schema Mapper API endpoints for automatic column detection and mapping.

Provides endpoints to:
- Preview mapping suggestions from file headers
- Analyze sample data for better detection
- Apply and persist mappings to datasets
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import (
    MappingSuggestionResponse,
    PreviewMappingRequest,
    ApplyMappingRequest,
    SuggestFromHeadersRequest
)
from app.services.schema_mapper import SchemaMapper


router = APIRouter(prefix="/api/mapper", tags=["schema_mapper"])


@router.post("/suggest/headers", response_model=MappingSuggestionResponse)
async def suggest_from_headers(request: SuggestFromHeadersRequest):
    """
    Suggest column mappings based on header names only.
    
    Fast preview that doesn't require reading the file data.
    Useful for quick suggestions before ingestion.
    
    Args:
        request: SuggestFromHeadersRequest with columns and optional existing mapping
        
    Returns:
        MappingSuggestionResponse with detected mappings and confidence scores
    """
    try:
        mapper = SchemaMapper()
        suggestion = mapper.suggest_from_header(request.columns, request.existing_mapping)
        return suggestion.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to suggest mappings: {str(e)}")


@router.post("/preview", response_model=MappingSuggestionResponse)
async def preview_file_mapping(request: PreviewMappingRequest):
    """
    Preview mapping suggestions by analyzing a file (headers + sample data).
    
    Reads sample rows from the file to improve detection accuracy.
    Does not ingest data - only provides suggestions.
    
    Args:
        request: PreviewMappingRequest with file path and options
        
    Returns:
        MappingSuggestionResponse with comprehensive mapping suggestions
    """
    try:
        mapper = SchemaMapper()
        suggestion = mapper.preview_mapping_from_file(
            file_path=request.file_path,
            sample_size=request.sample_size
        )
        return suggestion.to_dict()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to preview mapping: {str(e)}")


@router.post("/apply")
async def apply_column_mapping(
    request: ApplyMappingRequest,
    db: Session = Depends(get_db)
):
    """
    Apply and persist a column mapping to an existing dataset.
    
    Updates the dataset metadata with the provided mapping.
    The mapping will be used for future queries and exports.
    
    Args:
        request: ApplyMappingRequest with dataset ID and mapping
        db: Database session
        
    Returns:
        Success confirmation with applied mapping
    """
    try:
        mapper = SchemaMapper()
        success = mapper.apply_mapping(
            dataset_id=request.dataset_id,
            mapping=request.mapping,
            confidence_threshold=request.confidence_threshold
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to apply mapping")
        
        return {
            "success": True,
            "dataset_id": request.dataset_id,
            "applied_mapping": request.mapping
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply mapping: {str(e)}")
