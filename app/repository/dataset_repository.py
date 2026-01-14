"""
Repository layer for DatasetMetadata database operations.

Contains all database queries using SQLAlchemy ORM.
NO raw SQL. NO business logic.
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import DatasetMetadata

logger = logging.getLogger(__name__)


class DatasetRepository:
    """
    Repository for dataset metadata database operations.
    
    Provides clean interface for CRUD operations on dataset registry.
    All methods use SQLAlchemy ORM, no raw SQL.
    """
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy session from FastAPI dependency injection
        """
        self.db = db
    
    def create(self, dataset_data: dict) -> DatasetMetadata:
        """
        Create a new dataset metadata record.
        
        Args:
            dataset_data: Dictionary with dataset attributes
            
        Returns:
            Created DatasetMetadata instance
        """
        db_dataset = DatasetMetadata(**dataset_data)
        self.db.add(db_dataset)
        self.db.commit()
        self.db.refresh(db_dataset)
        
        logger.info(f"Created dataset record: {db_dataset.dataset_id} ({db_dataset.source_name})")
        return db_dataset
    
    def get_by_id(self, dataset_id: str) -> Optional[DatasetMetadata]:
        """
        Retrieve a dataset by its UUID.
        
        Args:
            dataset_id: Dataset UUID string
            
        Returns:
            DatasetMetadata or None if not found
        """
        return self.db.query(DatasetMetadata).filter(
            DatasetMetadata.dataset_id == dataset_id
        ).first()
    
    def get_by_filename(self, filename: str) -> Optional[DatasetMetadata]:
        """
        Retrieve a dataset by its original filename.
        
        Useful for detecting duplicate uploads.
        
        Args:
            filename: Original filename
            
        Returns:
            DatasetMetadata or None if not found
        """
        return self.db.query(DatasetMetadata).filter(
            DatasetMetadata.original_filename == filename
        ).first()
    
    def list_all(
        self,
        catalog_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DatasetMetadata]:
        """
        List all datasets with optional filtering.
        
        Args:
            catalog_type: Filter by catalog type (gaia, sdss, fits, csv)
            limit: Maximum number of results
            offset: Number of results to skip (for pagination)
            
        Returns:
            List of DatasetMetadata instances
        """
        query = self.db.query(DatasetMetadata)
        
        # Apply catalog type filter if specified
        if catalog_type:
            query = query.filter(DatasetMetadata.catalog_type == catalog_type)
        
        # Order by ingestion time (newest first)
        query = query.order_by(desc(DatasetMetadata.ingestion_time))
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        return query.all()
    
    def count_all(self, catalog_type: Optional[str] = None) -> int:
        """
        Count total datasets with optional filtering.
        
        Args:
            catalog_type: Filter by catalog type (gaia, sdss, fits, csv)
            
        Returns:
            Total count of datasets
        """
        query = self.db.query(DatasetMetadata)
        
        if catalog_type:
            query = query.filter(DatasetMetadata.catalog_type == catalog_type)
        
        return query.count()
    
    def update_record_count(self, dataset_id: str, new_count: int) -> Optional[DatasetMetadata]:
        """
        Update the record count for a dataset.
        
        Called after ingestion to track how many records were imported.
        
        Args:
            dataset_id: Dataset UUID string
            new_count: New record count
            
        Returns:
            Updated DatasetMetadata or None if not found
        """
        dataset = self.get_by_id(dataset_id)
        
        if dataset:
            dataset.record_count = new_count
            dataset.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(dataset)
            
            logger.info(f"Updated record count for dataset {dataset_id}: {new_count}")
        
        return dataset
    
    def increment_record_count(self, dataset_id: str, increment: int = 1) -> Optional[DatasetMetadata]:
        """
        Increment the record count for a dataset.
        
        Used when adding records incrementally.
        
        Args:
            dataset_id: Dataset UUID string
            increment: Number to add to current count
            
        Returns:
            Updated DatasetMetadata or None if not found
        """
        dataset = self.get_by_id(dataset_id)
        
        if dataset:
            dataset.record_count += increment
            dataset.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(dataset)
            
            logger.debug(f"Incremented record count for dataset {dataset_id} by {increment}")
        
        return dataset
    
    def update(self, dataset_id: str, update_data: dict) -> Optional[DatasetMetadata]:
        """
        Update dataset metadata fields.
        
        Args:
            dataset_id: Dataset UUID string
            update_data: Dictionary with fields to update
            
        Returns:
            Updated DatasetMetadata or None if not found
        """
        dataset = self.get_by_id(dataset_id)
        
        if dataset:
            for key, value in update_data.items():
                if hasattr(dataset, key):
                    setattr(dataset, key, value)
            
            dataset.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(dataset)
            
            logger.info(f"Updated dataset {dataset_id}: {list(update_data.keys())}")
        
        return dataset
    
    def delete(self, dataset_id: str) -> bool:
        """
        Delete a dataset metadata record.
        
        Note: This does NOT cascade delete associated star records.
        Use with caution - consider setting a soft delete flag instead.
        
        Args:
            dataset_id: Dataset UUID string
            
        Returns:
            True if deleted, False if not found
        """
        dataset = self.get_by_id(dataset_id)
        
        if dataset:
            self.db.delete(dataset)
            self.db.commit()
            
            logger.warning(f"Deleted dataset {dataset_id} ({dataset.source_name})")
            return True
        
        return False
    
    def get_total_records_across_datasets(self) -> int:
        """
        Get the sum of all record counts across all datasets.
        
        Returns:
            Total number of records across all datasets
        """
        from sqlalchemy import func
        
        result = self.db.query(func.sum(DatasetMetadata.record_count)).scalar()
        return result if result else 0
    
    def get_statistics(self) -> dict:
        """
        Get summary statistics about all datasets.
        
        Returns:
            Dictionary with statistics (total_datasets, total_records, by_catalog_type)
        """
        from sqlalchemy import func
        
        total_datasets = self.db.query(DatasetMetadata).count()
        total_records = self.get_total_records_across_datasets()
        
        # Group by catalog type
        by_type = self.db.query(
            DatasetMetadata.catalog_type,
            func.count(DatasetMetadata.id).label('dataset_count'),
            func.sum(DatasetMetadata.record_count).label('record_count')
        ).group_by(DatasetMetadata.catalog_type).all()
        
        by_catalog_type = {
            row.catalog_type: {
                'dataset_count': row.dataset_count,
                'record_count': row.record_count or 0
            }
            for row in by_type
        }
        
        return {
            'total_datasets': total_datasets,
            'total_records': total_records,
            'by_catalog_type': by_catalog_type
        }
