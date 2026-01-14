
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from app.database import DATABASE_URL

engine = create_engine(DATABASE_URL)

def check_star_241():
    print(f"Checking Star 241 in {DATABASE_URL}")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, source_id, ra_deg, dec_deg FROM unified_star_catalog WHERE id = 241"))
        row = result.fetchone()
        if row:
            print(f"ID: {row[0]}")
            print(f"Source ID: '{row[1]}'")
            print(f"RA: {row[2]}")
            print(f"Dec: {row[3]}")
        else:
            print("Star 241 not found")

if __name__ == "__main__":
    check_star_241()
