"""Quick script to fix database schema"""
import sqlite3

conn = sqlite3.connect('cosmic_data_fusion.db')
cursor = conn.cursor()

# Check existing tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print("Existing tables:", tables)

# Create User table if it doesn't exist
if 'user' not in tables:
    print("Creating User table...")
    cursor.execute("""
        CREATE TABLE user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255) NOT NULL UNIQUE,
            username VARCHAR(100) NOT NULL UNIQUE,
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            is_superuser BOOLEAN DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ User table created")
else:
    print("✅ User table already exists")

conn.commit()
conn.close()
print("\n✅ Database schema fixed successfully!")
