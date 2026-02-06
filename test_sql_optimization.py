import sqlite3

# Test the optimized SQL query directly
db_path = "cosmic_data_fusion.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

sql = """
SELECT 
    id, source_id, ra_deg, dec_deg, brightness_mag, original_source,
    json_extract(raw_metadata, '$.pmra') as pmra,
    json_extract(raw_metadata, '$.pmdec') as pmdec
FROM unified_star_catalog 
WHERE 1=1
    AND ra_deg BETWEEN 0 AND 180
    AND dec_deg BETWEEN -20 AND 40
    AND brightness_mag <= 10
    AND json_extract(raw_metadata, '$.pmra') IS NOT NULL
    AND json_extract(raw_metadata, '$.pmdec') IS NOT NULL
ORDER BY brightness_mag ASC
LIMIT 100
"""

print("Testing optimized SQL query...")
print("=" * 60)

try:
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    print(f"✅ Query successful!")
    print(f"   Rows returned: {len(rows)}")
    print()
    
    if rows:
        print("Sample row:")
        row = rows[0]
        print(f"  ID: {row[0]}")
        print(f"  Source ID: {row[1]}")
        print(f"  RA: {row[2]:.4f}°")
        print(f"  Dec: {row[3]:.4f}°")
        print(f"  Magnitude: {row[4]:.2f}")
        print(f"  Original Source: {row[5]}")
        print(f"  PMRA: {row[6]} mas/yr")
        print(f"  PMDec: {row[7]} mas/yr")
        
        print()
        print(f"Column indices verified:")
        print(f"  0: id = {row[0]}")
        print(f"  1: source_id = {row[1]}")
        print(f"  2: ra_deg = {row[2]}")
        print(f"  3: dec_deg = {row[3]}")
        print(f"  4: brightness_mag = {row[4]}")
        print(f"  5: original_source = {row[5]}")
        print(f"  6: pmra = {row[6]}")
        print(f"  7: pmdec = {row[7]}")
        
except Exception as e:
    print(f"❌ Query failed!")
    print(f"   Error: {e}")

conn.close()
print("=" * 60)
