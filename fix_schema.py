import sqlite3

# Connect to database
conn = sqlite3.connect('cosmic_data_fusion.db')
cursor = conn.cursor()

try:
    # Add user_id to dataset_metadata if not exists
    try:
        cursor.execute('ALTER TABLE dataset_metadata ADD COLUMN user_id INTEGER')
        print("✅ Added user_id to dataset_metadata")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⏭️  user_id already exists in dataset_metadata")
        else:
            raise

    # Add user_id to ingestion_errors if not exists
    try:
        cursor.execute('ALTER TABLE ingestion_errors ADD COLUMN user_id INTEGER')
        print("✅ Added user_id to ingestion_errors")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⏭️  user_id already exists in ingestion_errors")
        else:
            raise

    # Create users table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            is_active BOOLEAN DEFAULT 1,
            is_verified BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Created users table")

    # Create indexes
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_unified_star_catalog_user_id ON unified_star_catalog(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_dataset_metadata_user_id ON dataset_metadata(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_ingestion_errors_user_id ON ingestion_errors(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS ix_users_email ON users(email)')
        print("✅ Created indexes")
    except Exception as e:
        print(f"⚠️  Index creation: {e}")

    conn.commit()
    print("\n🎉 Database schema updated successfully!")

except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()
