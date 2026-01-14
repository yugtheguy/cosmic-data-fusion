
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from app.database import DATABASE_URL

# Create engine 
engine = create_engine(DATABASE_URL)

def check_star(star_id):
    print(f"Checking star {star_id} in {DATABASE_URL}")
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT id, source_id, parallax_mas, distance_pc FROM unified_star_catalog WHERE id = {star_id}"))
        row = result.fetchone()
        if row:
            print(f"Star Found: {row}")
            # Access row by index or name depending on sqlalchemy version/result proxy
            # Using index for safety: 0=id, 1=source_id, 2=parallax_mas, 3=distance_pc
            print(f"Parallax: {row[2]} (Type: {type(row[2])})")
            print(f"Distance: {row[3]} (Type: {type(row[3])})")
        else:
            print(f"Star {star_id} not found")

if __name__ == "__main__":
    check_star(269)
