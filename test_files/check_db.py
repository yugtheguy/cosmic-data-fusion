import sqlite3

conn = sqlite3.connect('cosmic_data_fusion.db')
c = conn.cursor()

# List tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in c.fetchall()]
print("Tables:", tables)

# Count stars
try:
    c.execute("SELECT COUNT(*) FROM unified_star_catalog")
    print("Total stars:", c.fetchone()[0])
    
    c.execute("SELECT source_id, ra_deg, dec_deg, original_source FROM unified_star_catalog LIMIT 5")
    print("Sample records:")
    for row in c.fetchall():
        print(" ", row)
except Exception as e:
    print("Error querying:", e)

# Check datasets
try:
    c.execute("SELECT COUNT(*) FROM dataset_metadata")
    print("Datasets:", c.fetchone()[0])
except Exception as e:
    print("Error querying datasets:", e)

conn.close()
