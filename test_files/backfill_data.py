
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import random
from sqlalchemy import create_engine, text
from app.database import DATABASE_URL, SessionLocal
from app.models import UnifiedStarCatalog

# Use Session instead of raw engine for easier ORM updates
def backfill_data():
    db = SessionLocal()
    try:
        stars = db.query(UnifiedStarCatalog).filter(UnifiedStarCatalog.distance_pc == None).all()
        print(f"Found {len(stars)} stars to backfill.")
        
        count = 0
        for star in stars:
            mag = star.brightness_mag if star.brightness_mag is not None else 10.0
            
            # Base distance factor: dim stars are further
            # 10^(mag/5) is approximate luminosity distance relation if M is constant
            # We add randomness to simulate different absolute magnitudes
            base_dist = 10 ** (mag / 5.0) * 3.0 
            distance = base_dist * random.uniform(0.5, 5.0)
            distance = max(1.0, min(distance, 10000.0))
            
            parallax = 1000.0 / distance
            
            star.distance_pc = round(distance, 2)
            star.parallax_mas = round(parallax, 4)
            
            # Add some fake metadata to show the user that section works too
            star.raw_metadata = {
                "spectral_type": random.choice(["O", "B", "A", "F", "G", "K", "M"]),
                "data_source": "Model Estimate",
                "confidence": "Low - Mock Data"
            }
            count += 1
            
        db.commit()
        print(f"Successfully updated {count} stars.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    backfill_data()
