#!/usr/bin/env python3
"""
Clean up pre-existing bundled data from the database.

This script deletes all stars and datasets that don't belong to any user
(i.e., the pre-loaded sample data from Gaia, SDSS, etc.).
"""

from app.database import SessionLocal
from app.models import UnifiedStarCatalog, DatasetMetadata
from sqlalchemy import delete

def cleanup_bundled_data():
    """Delete all pre-existing bundled data."""
    db = SessionLocal()
    try:
        # Delete all stars without user ownership (the pre-bundled data)
        result = db.execute(delete(UnifiedStarCatalog).where(UnifiedStarCatalog.user_id == None))
        db.commit()
        deleted_stars = result.rowcount
        
        # Delete bundled datasets (those with no user ownership)
        result = db.execute(delete(DatasetMetadata).where(DatasetMetadata.user_id == None))
        db.commit()
        deleted_datasets = result.rowcount
        
        print(f"✅ Deleted {deleted_stars} pre-existing stars")
        print(f"✅ Deleted {deleted_datasets} bundled datasets")
        print(f"\n🎉 Database cleaned! Only user-uploaded data remains.")
        
        return deleted_stars, deleted_datasets
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        return 0, 0
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_bundled_data()
