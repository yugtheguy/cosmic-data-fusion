# 🗄️ Database Setup Guide: PostgreSQL, PostGIS & Redis

**Current Status:** Using SQLite (local development)  
**Next Level:** PostgreSQL + PostGIS + Redis (production-ready)

---

## 📋 DATABASE UPGRADE STRATEGY

### What We Have Now (SQLite)
```
✓ Simple, file-based
✓ Good for development
✓ Limited spatial features
✗ Not scalable for 100K+ records
✗ No caching layer
```

### What We Should Add (Production Stack)
```
PostgreSQL + PostGIS:
  ✓ Relational database (scalable)
  ✓ ACID transactions
  ✓ Spatial queries (cone search, bounding box)
  ✓ Handles millions of records
  ✓ Vector/raster support
  
Redis:
  ✓ In-memory cache layer
  ✓ Fast query results
  ✓ Session management
  ✓ Real-time data aggregation
```

---

## 🔧 SETUP PLAN (4 Steps)

### Step 1: Install PostgreSQL + PostGIS

**Windows:**
```bash
# Option A: PostgreSQL installer with PostGIS
# Download: https://www.postgresql.org/download/windows/
# During installation, select "PostGIS" extension

# Option B: Using Docker (recommended)
docker run --name cosmic_postgres \
  -e POSTGRES_DB=cosmic_data \
  -e POSTGRES_USER=cosmic_user \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  postgis/postgis:15-3.3 \
  -d
```

**Connection String:**
```
postgresql://cosmic_user:secure_password@localhost:5432/cosmic_data
```

---

### Step 2: Install Redis

**Windows:**
```bash
# Option A: Using Docker (easiest)
docker run --name cosmic_redis \
  -p 6379:6379 \
  -d \
  redis:7-alpine

# Option B: WSL2 (Windows Subsystem for Linux)
wsl apt-get install redis-server
redis-server
```

**Connection String:**
```
redis://localhost:6379/0
```

---

### Step 3: Update SQLAlchemy Configuration

**File to modify:** `app/database.py`

```python
# Current (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./cosmic_data.db"

# New (PostgreSQL)
SQLALCHEMY_DATABASE_URL = "postgresql://cosmic_user:secure_password@localhost:5432/cosmic_data"

# Or from environment variables (recommended)
import os
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cosmic_user:secure_password@localhost:5432/cosmic_data"
)
```

---

### Step 4: Add PostGIS Support

**Install dependency:**
```bash
pip install geoalchemy2
```

**Update models.py to use PostGIS geometry:**
```python
from geoalchemy2 import Geometry

# Instead of separate ra_deg, dec_deg
# Add spatial column:
location = Column(Geometry('POINT', srid=4035))  # ICRS coordinates

# Or keep both for flexibility:
# ra_deg + dec_deg (numeric)
# location (geometry point)
```

---

## 🎯 RECOMMENDED SETUP (Production)

```
┌─────────────────────────────────────────────────────────────┐
│                FastAPI Application                           │
│             (Gaia + SDSS + FITS + CSV Adapters)              │
└────────────┬──────────────────────────────────────────────────┘
             │
    ┌────────┴────────┬────────────────────┐
    ▼                 ▼                    ▼
┌──────────┐   ┌──────────────┐   ┌─────────────┐
│ PostgreSQL   │ PostGIS      │   │   Redis     │
│ (Primary DB) │ (Spatial)    │   │ (Cache)     │
│              │              │   │             │
│ ✓ 10M+ stars │ ✓ Cone search│   │ ✓ Query cache
│ ✓ ACID      │ ✓ Bounding box│  │ ✓ Sessions
│ ✓ Indexes   │ ✓ Nearest N  │   │ ✓ Analytics
└──────────┘   └──────────────┘   └─────────────┘
```

---

## 💾 WHAT TO MIGRATE

| Feature | SQLite | PostgreSQL | PostGIS | Redis |
|---------|--------|------------|---------|-------|
| **Data Storage** | ✓ | ✓ | ✓ | ✗ |
| **ACID Transactions** | ✓ | ✓ | ✓ | ✗ |
| **Spatial Queries** | ✗ | ~ | ✓✓✓ | ✗ |
| **Cone Search** | ✗ | ✗ | ✓ | ✗ |
| **Bounding Box** | ✓ | ✓ | ✓✓ | ✗ |
| **KNN (K-Nearest)** | ✗ | ✗ | ✓ | ✗ |
| **Caching** | ✗ | ✗ | ✗ | ✓✓✓ |
| **Real-time Aggregation** | ✗ | ✗ | ✗ | ✓✓ |
| **Scale (Records)** | 100K | 100M | 100M | N/A |

---

## 🔄 MIGRATION PATH (Step-by-Step)

### Phase 1: PostgreSQL (Keep SQLite temporarily)
```
1. Install PostgreSQL
2. Create database: cosmic_data
3. Update DATABASE_URL in code
4. Run migrations (create tables)
5. Migrate data: SQLite → PostgreSQL
6. Keep SQLite as backup
7. Switch application to PostgreSQL
```

### Phase 2: Add PostGIS
```
1. Install PostGIS extension
2. Add geometry columns to tables
3. Add spatial indexes
4. Update queries to use ST_Distance, ST_DWithin, etc.
5. Test cone search queries
```

### Phase 3: Add Redis Caching
```
1. Install Redis
2. Add redis-py package
3. Cache frequent queries
4. Cache visualization data (/visualize/*)
5. Cache dataset statistics
```

---

## 📝 EXAMPLE: CONE SEARCH WITH PostGIS

**Current SQLite (approximate):**
```python
# Distance calculation at application level
results = db.query(UnifiedStarCatalog).filter(
    (UnifiedStarCatalog.ra_deg >= ra - radius/cos(dec)) &
    (UnifiedStarCatalog.ra_deg <= ra + radius/cos(dec)) &
    (UnifiedStarCatalog.dec_deg >= dec - radius) &
    (UnifiedStarCatalog.dec_deg <= dec + radius)
).all()
```

**With PostGIS (optimized):**
```python
from geoalchemy2.functions import ST_DWithin
from geoalchemy2 import Geometry

# Direct spatial query (much faster!)
results = db.query(UnifiedStarCatalog).filter(
    ST_DWithin(
        UnifiedStarCatalog.location,
        f'POINT({ra} {dec})',
        radius / 3600.0  # Convert arcsec to degrees
    )
).all()
```

---

## 🚀 IMPLEMENTATION PRIORITY

**NOW (Keep SQLite for dev):**
- ✓ Gaia adapter working with SQLite
- ✓ SDSS adapter working with SQLite
- ✓ FITS adapter working with SQLite

**NEXT SPRINT (Add PostgreSQL):**
- 1. Set up PostgreSQL + PostGIS
- 2. Migrate UnifiedStarCatalog schema
- 3. Update connection string
- 4. Test all adapters with PostgreSQL
- 5. Optimize spatial indexes

**FUTURE SPRINTS (Add Redis):**
- 1. Set up Redis
- 2. Cache visualization endpoints
- 3. Cache dataset statistics
- 4. Performance testing

---
