
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from app.database import DATABASE_URL

engine = create_engine(DATABASE_URL)

def check_star_source():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, source_id, original_source FROM unified_star_catalog WHERE id = 269"))
        row = result.fetchone()
        if row:
            print(f"ID: {row[0]}")
            print(f"Source ID: '{row[1]}'")
            print(f"Original Source: '{row[2]}'")
        else:
            print("Star 269 not found")

if __name__ == "__main__":
    check_star_source()
