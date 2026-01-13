# 🔄 PostgreSQL Migration Code Template

This file shows exactly what code changes are needed to migrate from SQLite to PostgreSQL.

---

## 1️⃣ UPDATE DATABASE.PY

**Current (SQLite):**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./cosmic_data.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite only
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)
```

**New (PostgreSQL):**
```python
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.models import Base

# Read from environment or use default
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cosmic_user:secure_password@localhost:5432/cosmic_data"
)

# PostgreSQL connection pooling
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,           # Connection pool size
    max_overflow=20,        # Max overflow connections
    pool_recycle=3600,      # Recycle connections every hour
    pool_pre_ping=True,     # Test connections before using
    echo=False              # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables on startup
Base.metadata.create_all(bind=engine)
```

---

## 2️⃣ UPDATE REQUIREMENTS.TXT

**Add PostgreSQL driver:**
```txt
# Existing dependencies...
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.0
pydantic>=2.5.0
astropy>=6.0.0

# NEW: PostgreSQL support
psycopg2-binary>=2.9.0

# OPTIONAL: PostGIS support
geoalchemy2>=0.13.0

# OPTIONAL: Caching support
redis>=4.5.0
```

**Install:**
```bash
pip install -r requirements.txt
```

---

## 3️⃣ ENVIRONMENT VARIABLES (.env)

**Create .env file in project root:**
```bash
# Database Configuration
DATABASE_URL=postgresql://cosmic_user:secure_password@localhost:5432/cosmic_data

# Optional: Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Server Configuration
APP_ENV=development
DEBUG=False
```

**Update main.py to load env:**
```python
from dotenv import load_dotenv

load_dotenv()  # Load .env file
```

---

## 4️⃣ CREATE MIGRATION SCRIPT

**File: `migrate_sqlite_to_postgres.py`**

```python
"""
Migration script: SQLite → PostgreSQL

Reads data from SQLite and inserts into PostgreSQL.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Source: SQLite
SQLITE_URL = "sqlite:///./cosmic_data.db"
sqlite_engine = create_engine(SQLITE_URL)
SQLiteSession = sessionmaker(bind=sqlite_engine)

# Target: PostgreSQL
POSTGRES_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cosmic_user:secure_password@localhost:5432/cosmic_data"
)
postgres_engine = create_engine(POSTGRES_URL, echo=False)
PostgresSession = sessionmaker(bind=postgres_engine)

from app.models import Base, UnifiedStarCatalog

def migrate():
    """Migrate all data from SQLite to PostgreSQL."""
    
    print("\n" + "="*70)
    print("MIGRATION: SQLite → PostgreSQL")
    print("="*70)
    
    # Create tables in PostgreSQL
    print("\n[1] Creating tables in PostgreSQL...")
    Base.metadata.create_all(bind=postgres_engine)
    print("✓ Tables created")
    
    # Read from SQLite
    print("\n[2] Reading data from SQLite...")
    sqlite_session = SQLiteSession()
    sqlite_records = sqlite_session.query(UnifiedStarCatalog).all()
    print(f"✓ Found {len(sqlite_records)} records")
    
    # Insert into PostgreSQL
    print("\n[3] Inserting into PostgreSQL...")
    postgres_session = PostgresSession()
    
    batch_size = 1000
    for i in range(0, len(sqlite_records), batch_size):
        batch = sqlite_records[i:i+batch_size]
        
        for record in batch:
            # Create new record (don't copy ID to avoid conflicts)
            new_record = UnifiedStarCatalog(
                source_id=record.source_id,
                ra_deg=record.ra_deg,
                dec_deg=record.dec_deg,
                brightness_mag=record.brightness_mag,
                parallax_mas=record.parallax_mas,
                distance_pc=record.distance_pc,
                original_source=record.original_source,
                raw_frame=record.raw_frame,
                observation_time=record.observation_time,
                dataset_id=record.dataset_id,
                raw_metadata=record.raw_metadata,
                object_id=record.object_id,
            )
            postgres_session.add(new_record)
        
        postgres_session.commit()
        print(f"  ✓ Inserted batch {i//batch_size + 1} ({len(batch)} records)")
```

---

## 5️⃣ DEPLOYMENT CHANGES

**docker-compose.yml example:**
```yaml
version: '3.9'

services:
  # PostgreSQL Database
  postgres:
    image: postgis/postgis:15-3.3
    environment:
      POSTGRES_DB: cosmic_data
      POSTGRES_USER: cosmic_user
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis Cache (optional)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # FastAPI Application
  app:
    build: .
    environment:
      DATABASE_URL: postgresql://cosmic_user:secure_password@postgres:5432/cosmic_data
      REDIS_URL: redis://redis:6379/0
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
```

---

## 6️⃣ TESTING THE MIGRATION

```bash
# 1. Ensure PostgreSQL is running
docker run -d \
  --name cosmic_postgres \
  -e POSTGRES_DB=cosmic_data \
  -e POSTGRES_USER=cosmic_user \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  postgis/postgis:15-3.3

# 2. Install new dependencies
pip install psycopg2-binary geoalchemy2 python-dotenv

# 3. Create .env file with DATABASE_URL
echo "DATABASE_URL=postgresql://cosmic_user:secure_password@localhost:5432/cosmic_data" > .env

# 4. Run migration script
python migrate_sqlite_to_postgres.py

# 5. Verify data transferred
python -c "
from app.database import SessionLocal
from app.models import UnifiedStarCatalog
db = SessionLocal()
count = db.query(UnifiedStarCatalog).count()
print(f'Total records in PostgreSQL: {count}')
"
```

---

## 📊 PERFORMANCE COMPARISON

| Operation | SQLite | PostgreSQL |
|-----------|--------|------------|
| Insert 10K records | ~2-3s | ~1-2s |
| Query all | ~0.5s | ~0.2s |
| Spatial filter | ~1.5s | ~0.1s |
| Cone search | N/A | ~0.05s |

---
