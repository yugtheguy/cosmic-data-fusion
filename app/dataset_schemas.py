"""
Dataset metadata schemas for COSMIC Data Fusion API.
These will be merged into schemas.py.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class DatasetRegisterRequest(BaseModel):
    """Schema for registering a new dataset."""
    
    source_name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Human-readable source name"
    )
    catalog_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Type of catalog (gaia, sdss, fits, csv)"
    )
    adapter_used: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Adapter that processed this data"
    )
    schema_version: Optional[str] = Field(
        None,
        max_length=20,
        description="Schema version used"
    )
    original_filename: Optional[str] = Field(
        None,
        max_length=500,
        description="Original filename if uploaded"
    )
    file_size_bytes: Optional[int] = Field(
        None,
        ge=0,
        description="File size in bytes"
    )
    column_mappings: Optional[dict] = Field(
        None,
        description="Column mapping dictionary"
    )
    raw_config: Optional[dict] = Field(
        None,
        description="Adapter configuration"
    )
    license_info: Optional[str] = Field(
        None,
        max_length=500,
        description="License/attribution information"
    )
    notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="User notes about this dataset"
    )


class DatasetMetadataResponse(BaseModel):
    """Schema for dataset metadata response."""
    
    id: int = Field(description="Database primary key")
    dataset_id: str = Field(description="Unique UUID identifier")
    source_name: str = Field(description="Human-readable source name")
    catalog_type: str = Field(description="Type of catalog")
    ingestion_time: datetime = Field(description="When dataset was ingested")
    adapter_used: str = Field(description="Adapter used for processing")
    schema_version: Optional[str] = Field(description="Schema version")
    record_count: int = Field(description="Number of records ingested")
    original_filename: Optional[str] = Field(description="Original filename")
    file_size_bytes: Optional[int] = Field(description="File size in bytes")
    column_mappings: Optional[dict] = Field(description="Column mappings")
    raw_config: Optional[dict] = Field(description="Adapter configuration")
    license_info: Optional[str] = Field(description="License information")
    notes: Optional[str] = Field(description="User notes")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class DatasetListResponse(BaseModel):
    """Schema for paginated dataset list response."""
    
    datasets: List[DatasetMetadataResponse] = Field(description="List of datasets")
    total: int = Field(description="Total number of datasets")
    limit: int = Field(description="Results per page")
    offset: int = Field(description="Offset for pagination")


class DatasetRegistryStats(BaseModel):
    """Schema for dataset registry statistics response."""
    
    total_datasets: int = Field(description="Total number of datasets")
    total_records: int = Field(description="Total records across all datasets")
    by_catalog_type: dict = Field(description="Statistics grouped by catalog type")
    
    model_config = ConfigDict(from_attributes=True)
