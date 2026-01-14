
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text, func
from app.database import DATABASE_URL, SessionLocal
from app.models import UnifiedStarCatalog

def check_dec_distribution():
    db = SessionLocal()
    try:
        # Get min, max, and count
        result = db.query(
            func.min(UnifiedStarCatalog.dec_deg),
            func.max(UnifiedStarCatalog.dec_deg),
            func.count(UnifiedStarCatalog.id)
        ).first()
        
        min_dec, max_dec, count = result
        print(f"Total Stars: {count}")
        print(f"Min Dec: {min_dec}")
        print(f"Max Dec: {max_dec}")
        
        # Check standard distribution
        print("\nDistribution:")
        ranges = [(-90, -45), (-45, 0), (0, 45), (45, 90)]
        for r_min, r_max in ranges:
            c = db.query(UnifiedStarCatalog).filter(
                UnifiedStarCatalog.dec_deg >= r_min,
                UnifiedStarCatalog.dec_deg < r_max
            ).count()
            print(f"  {r_min} to {r_max}: {c} stars")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_dec_distribution()
