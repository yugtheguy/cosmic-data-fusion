import sqlite3

conn = sqlite3.connect('cosmic_data_fusion.db')
cursor = conn.cursor()

# Get table schema
cursor.execute("PRAGMA table_info(dataset_metadata)")
columns = cursor.fetchall()
print("Columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Check dataset_metadata table with correct columns
cursor.execute('SELECT * FROM dataset_metadata')
rows = cursor.fetchall()
print("\nDatasets:")
for r in rows:
    print(f"  {r}")
        
conn.close()
