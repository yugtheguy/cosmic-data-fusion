import sqlite3

# Connect to database
db_path = "app/cosmic_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 60)
print("DATABASE SCHEMA CHECK")
print("=" * 60)
print()

# Check if table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='unified_star_catalog'")
table_exists = cursor.fetchone()

if table_exists:
    print("✅ Table 'unified_star_catalog' exists")
    print()
    
    # Get table schema
    cursor.execute("PRAGMA table_info(unified_star_catalog)")
    columns = cursor.fetchall()
    
    print("Table Columns:")
    print("-" * 60)
    for col in columns:
        col_id, name, type_, notnull, default, pk = col
        print(f"{col_id:2d}. {name:25s} {type_:15s} {'NOT NULL' if notnull else ''}")
    print()
    
    # Count rows
    cursor.execute("SELECT COUNT(*) FROM unified_star_catalog")
    count = cursor.fetchone()[0]
    print(f"Total rows: {count:,}")
    print()
    
    # Sample a row to see structure
    cursor.execute("SELECT * FROM unified_star_catalog LIMIT 1")
    row = cursor.fetchone()
    
    if row:
        print("Sample Row:")
        print("-" * 60)
        for i, (col, val) in enumerate(zip(columns, row)):
            col_name = col[1]
            print(f"{i:2d}. {col_name:25s} = {str(val)[:50]}")
    
else:
    print("❌ Table 'unified_star_catalog' does NOT exist!")
    print()
    print("Available tables:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table[0]}")

conn.close()
print()
print("=" * 60)
