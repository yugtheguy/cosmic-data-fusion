"""Test with fixed parameter names."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
import sys
sys.path.insert(0, '.')
from app.services.temporal_calculator import TemporalCalculator

engine = create_engine("sqlite:///cosmic_data_fusion.db")
Session = sessionmaker(bind=engine)
db = Session()

temporal_calc = TemporalCalculator()

# Get stars
query = "SELECT id, source_id, ra_deg, dec_deg, brightness_mag, raw_metadata FROM unified_star_catalog LIMIT 3"
result = db.execute(text(query)).fetchall()
print(f"Query returned {len(result)} rows")

for row in result:
    try:
        print(f"\nProcessing row {row[0]}...")
        
        metadata = json.loads(row[5]) if isinstance(row[5], str) else (row[5] or {})
        pmra = metadata.get('pmra', 0)
        pmdec = metadata.get('pmdec', 0)
        
        pos_result = temporal_calc.calculate_position_at_epoch(
            ra_deg=row[2],
            dec_deg=row[3],
            pmra_mas_yr=pmra if pmra else None,
            pmdec_mas_yr=pmdec if pmdec else None,
            target_epoch=-3000
        )
        
        print(f"  pos_result type: {type(pos_result)}")
        print(f"  pos_result: {pos_result}")
        
        # Try dict access
        try:
            print(f"  pos_result['ra_deg']: {pos_result['ra_deg']}")
        except Exception as e:
            print(f"  Dict access failed: {e}")
            
        # Try attribute access
        try:
            print(f"  pos_result.ra_deg: {pos_result.ra_deg}")
        except Exception as e:
            print(f"  Attribute access failed: {e}")
            
    except Exception as e:
        print(f"  EXCEPTION: {type(e).__name__}: {e}")

db.close()
