<div align="center">

  <h1>🌌 COSMIC Data Fusion 🌌</h1>
  <h3><em>Unified astronomical data platform powered by AI-driven harmonization.</em></h3>

</div>

<!-- Terminal Intro Animation -->
<div align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&duration=2000&pause=800&color=3B82F6&center=true&width=600&lines=Initializing+Data+Pipeline...;Connecting+to+Gaia+DR3...;Harmonizing+Multi-Source+Catalogs...;Running+AI+Discovery+Engine...;System+Ready!" alt="Terminal Animation">
</div>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" alt="Divider">

## 🎯 Problem & Inspiration

<table>
<tr>
<td>

Astronomical research is hindered by **data fragmentation, incompatible formats, and manual cross-matching**. Major sky surveys like Gaia DR3, SDSS, and 2MASS each use different coordinate systems, magnitude scales, and data formats. Researchers spend countless hours manually harmonizing catalogs instead of making discoveries.

**COSMIC Data Fusion** revolutionizes this landscape by providing an automated pipeline that ingests multi-source astronomical data, harmonizes it into a unified catalog, and uses AI to discover interesting celestial objects—all through a modern REST API and interactive dashboard.

</td>
<td width="40%">
<img src="./images/landing_page.png" width="100%" alt="COSMIC Data Fusion Dashboard">
</td>
</tr>
</table>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=100&section=divider">

## 💡 Why We Chose This Problem

<table>
<tr>
<td width="60%">

### The Reality We Witnessed

As astronomy enthusiasts and data scientists, we've witnessed the frustrating data harmonization process firsthand:

- 📊 **Format chaos**: CSV, FITS, VOTable—every survey uses different formats
- 🌍 **Coordinate confusion**: ICRS, FK5, Galactic—manual conversion is error-prone
- 🔄 **Duplicate observations**: Same star appears multiple times across surveys
- ⏳ **Manual cross-matching**: Hours spent matching stars by coordinates
- 🔍 **Lost discoveries**: Interesting objects buried in petabytes of data

### The Statistics That Moved Us

- **100+ petabytes** of astronomical data collected globally
- **80%** of researcher time spent on data wrangling vs. science
- **Millions** of duplicate observations across major surveys
- **Inconsistent** magnitude scales delay time-domain astronomy

### Our Mission

We believe **astronomy should be data-driven, not data-blocked**. By combining modern APIs, AI-powered discovery, and standardized formats, we're creating a system where:
- Every observation is harmonized to ICRS J2000
- Every duplicate is identified and merged
- Every anomaly is surfaced automatically

</td>
</tr>
</table>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 🧠 What It Does

<div align="center">
  <table>
    <tr>
      <td align="center"><h3>🚀</h3><h4>Multi-Source Ingestion</h4><p>Native adapters for Gaia DR3 and NASA TESS catalogs</p></td>
      <td align="center"><h3>🔗</h3><h4>Data Harmonization</h4><p>Automatic cross-matching and coordinate standardization</p></td>
    </tr>
    <tr>
      <td align="center"><h3>🤖</h3><h4>AI Discovery Engine</h4><p>Isolation Forest anomaly detection and DBSCAN clustering</p></td>
      <td align="center"><h3>📊</h3><h4>Unified Catalog</h4><p>Single queryable database with merged observations</p></td>
    </tr>
    <tr>
      <td align="center"><h3>🔍</h3><h4>Advanced Search</h4><p>Cone search, bounding box, and multi-parameter filtering</p></td>
      <td align="center"><h3>📤</h3><h4>Export Formats</h4><p>CSV, JSON, and IVOA-compliant VOTable</p></td>
    </tr>
    <tr>
      <td align="center"><h3>🌐</h3><h4>REST API</h4><p>FastAPI with automatic OpenAPI documentation</p></td>
      <td align="center"><h3>📈</h3><h4>Analytics Dashboard</h4><p>Real-time statistics and visualizations</p></td>
    </tr>
    <tr>
      <td align="center"><h3>⚡</h3><h4>Query Optimization</h4><p>Indexed spatial queries for fast searches</p></td>
      <td align="center"><h3>🔬</h3><h4>Science Ready</h4><p>Proper magnitude conversions and error propagation</p></td>
    </tr>
    <tr>
      <td align="center"><h3>🎯</h3><h4>Planet Hunter View</h4><p>Specialized filtering for exoplanet host candidates</p></td>
      <td align="center"><h3>📐</h3><h4>Astrometry Tools</h4><p>Coordinate transformations and epoch conversions</p></td>
    </tr>
  </table>
</div>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## ⚙️ Tech Stack

<div align="center">

### Backend
🐍 Python 3.11+ • ⚡ FastAPI • 🗄️ SQLAlchemy • 🐘 PostgreSQL (or SQLite)  
📊 Alembic Migrations • 🔐 JWT Authentication • 📡 RESTful APIs • 🧪 Pytest

### Data Processing
🔭 Astropy • 🌍 Astroquery • 📊 NumPy • 🐼 Pandas  
🤖 Scikit-learn • 📈 Matplotlib • 🔬 SciPy

### AI & Machine Learning
🤖 **Isolation Forest**: Anomaly detection in multi-dimensional stellar parameter space  
🎯 **DBSCAN Clustering**: Spatial clustering to identify star clusters and associations  
📊 **Feature Engineering**: Proper motion, parallax, magnitude anomalies

### Frontend
⚛️ React • 🎨 Tailwind CSS • 📊 Recharts • 🗺️ Aladin Lite (Sky Maps)  
🔄 Axios • 🧭 React Router • 📱 Responsive Design

### DevOps & Tools
🐳 Docker • 🐳 Docker Compose • 🔧 Git • 📝 VS Code  
📚 Swagger UI • 🧪 Postman • 📊 pgAdmin

</div>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:F59E0B,100:EF4444&height=100&section=divider&text=AI%20Discovery%20Deep%20Dive&fontColor=ffffff&fontSize=28&animation=twinkling">

## 🤖 How AI Powers Our Platform

<div align="center">
<img src="https://media.giphy.com/media/xT9IgzoKnwFNmISR8I/giphy.gif" width="400px" alt="AI Neural Network Animation">
</div>

### 🔐 The Discovery Problem We Solve

Traditional astronomical analysis requires:
- ❌ Manual inspection of thousands of objects
- ❌ Expert knowledge to identify anomalies
- ❌ Time-consuming visual analysis of light curves
- ❌ Statistical outliers missed in large catalogs

**Our AI solution automates discovery at scale.**

### 🏗️ AI Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     COSMIC AI DISCOVERY ENGINE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │ Feature Extract  │    │ Isolation Forest │    │ DBSCAN Cluster   │  │
│  │                  │    │                  │    │                  │  │
│  │ • Proper motion  │───>│ • Anomaly score  │───>│ • Spatial groups │  │
│  │ • Parallax       │    │ • Multi-dim      │    │ • Star clusters  │  │
│  │ • Magnitudes     │    │ • Outlier detect │    │ • Associations   │  │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘  │
│           │                       │                       │             │
│           └───────────────────────┼───────────────────────┘             │
│                                   ▼                                      │
│                    ┌──────────────────────────┐                         │
│                    │     Discovery API        │                         │
│                    │                          │                         │
│                    │ • Get anomalies          │                         │
│                    │ • Get clusters           │                         │
│                    │ • Thresholds & filters   │                         │
│                    └──────────────────────────┘                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 🎯 Key AI Features

| Feature | How It Works | Why It Matters |
|---------|-------------|----------------|
| **Isolation Forest** | Identifies stars with unusual parameter combinations | Discovers rare objects like white dwarfs, high-velocity stars |
| **Multi-dimensional** | Analyzes 5+ stellar parameters simultaneously | Finds patterns invisible in single parameters |
| **DBSCAN Clustering** | Groups stars by spatial proximity on sky | Identifies open clusters, stellar associations |
| **Adaptive Thresholding** | User-configurable contamination rate | Balance between sensitivity and false positives |
| **Feature Scaling** | StandardScaler normalization | Ensures fair comparison across different units |
| **Persistent Results** | Cached anomaly scores in database | Fast retrieval without re-computation |

### 🔄 The Discovery Flow - Step by Step

```mermaid
sequenceDiagram
    participant U as User
    participant API as REST API
    participant DB as Database
    participant AI as AI Engine
    
    U->>API: 1. Request /ai/discover
    API->>DB: 2. Fetch unified catalog
    DB-->>API: 3. Return star data
    
    API->>AI: 4. Extract features
    AI->>AI: 5. Train Isolation Forest
    AI->>AI: 6. Calculate anomaly scores
    AI->>AI: 7. Run DBSCAN clustering
    
    AI-->>API: 8. Return discoveries
    API->>DB: 9. Cache results
    API-->>U: 10. Return anomalies + clusters
    
    U->>API: 11. Export interesting objects
    API-->>U: 12. VOTable/CSV download
```

### 🛡️ Data Quality Guarantees

<table>
<tr>
<td width="50%">

**What AI CAN Do:**
- ✅ Identify 5-sigma outliers automatically
- ✅ Cluster 1000+ stars in seconds
- ✅ Detect multi-parameter anomalies
- ✅ Adapt to different contamination rates

</td>
<td width="50%">

**What AI CANNOT Do:**
- ❌ Replace expert astrophysical analysis
- ❌ Determine physical causes of anomalies
- ❌ Work with incomplete/null data
- ❌ Guarantee every anomaly is scientifically interesting

</td>
</tr>
</table>

### 💎 Why These Algorithms?

- **Isolation Forest**: Handles high-dimensional data without labeled examples
- **DBSCAN**: No need to specify number of clusters beforehand
- **Scikit-learn**: Battle-tested, well-documented, actively maintained
- **Feature Engineering**: Domain knowledge (astrometry) + ML best practices

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:3B82F6,100:8B5CF6&height=100&section=divider&text=Target%20Users&fontColor=ffffff&fontSize=28&animation=twinkling">

## 🔬 Target Users

- 🔭 **Professional Astronomers** – Researchers needing unified multi-survey catalogs for science papers
- 🎓 **Graduate Students** – PhD candidates working on statistical stellar population studies
- 🏫 **Educational Institutions** – Universities teaching observational astronomy and data science
- 📊 **Data Scientists** – ML practitioners exploring astronomical datasets
- 🌌 **Amateur Astronomers** – Enthusiasts analyzing publicly available survey data
- 💼 **Observatory Staff** – Facilities cross-referencing observations with historical catalogs
- 🤖 **AI Researchers** – Scientists developing anomaly detection for time-domain astronomy

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 🏗️ How We Built It

<table>
<tr>
<td>

COSMIC Data Fusion is architected as a production-grade data pipeline:

### Architecture
- ⚡ **FastAPI Backend**: High-performance async Python web framework
- 🗄️ **SQLAlchemy ORM**: Type-safe database operations with Alembic migrations
- 🔭 **Astropy Core**: Professional-grade astronomical coordinate transformations
- 🤖 **Scikit-learn**: Industry-standard machine learning for discovery
- ⚛️ **React Frontend**: Modern component-based UI with Recharts

### Key Components
- **Ingestion Layer**: Source adapters for Gaia DR3 and TESS Input Catalog
- **Harmonization Engine**: Cross-matching with 1 arcsecond tolerance
- **AI Discovery**: Isolation Forest + DBSCAN for automated object identification
- **Query Layer**: Optimized spatial indexes for cone search and bounding box
- **Export Service**: IVOA VOTable compliance for interoperability

### Development Workflow
- **Alembic Migrations**: Version-controlled database schema evolution
- **Pytest Suite**: Unit and integration tests for critical pipelines
- **Docker Compose**: One-command development environment
- **Git Workflow**: Feature branches with code review

</td>
<td width="40%">
<img src="https://media.giphy.com/media/26tn33aiTi1jkl6H6/giphy.gif" width="100%" alt="Coding Animation">
</td>
</tr>
</table>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=100&section=divider&text=Key%20Features&fontColor=ffffff&fontSize=28&animation=twinkling">

## ✨ Core Features

### 🚀 Multi-Source Data Ingestion
- Gaia DR3 adapter with automatic column mapping
- NASA TESS Input Catalog (TIC) integration
- FITS and CSV file format support
- Automatic coordinate standardization to ICRS J2000
- Magnitude system conversion (Gaia G/BP/RP to standard)
- Error propagation for astrometric parameters
- Batch ingestion with progress tracking
- Validation and quality checks

### 🔗 Data Harmonization
- Positional cross-matching using Astropy spherical geometry
- 1 arcsecond matching tolerance (configurable)
- Duplicate detection and merging
- Source priority rules (prefer Gaia for astrometry)
- Unified star ID assignment
- Multi-epoch coordinate handling
- Proper motion validation
- Parallax-based distance calculations

### 🤖 AI-Powered Discovery
- **Isolation Forest**: Anomaly detection in 5D parameter space
- **DBSCAN Clustering**: Spatial grouping for star clusters
- Configurable contamination rate (default: 0.1)
- Anomaly score ranking
- Feature importance analysis
- Persistent caching of results
- Real-time discovery API endpoints
- Export anomalies for follow-up

### 🔍 Advanced Query API
- Cone search (RA, Dec, radius)
- Bounding box search (RA/Dec ranges)
- Multi-parameter filtering (magnitude, parallax, proper motion)
- Pagination for large result sets
- Sorting by multiple columns
- Full-text search on source IDs
- Query result caching
- JSON and CSV response formats

### 📊 Unified Catalog Management
- Single table with harmonized observations
- Indexed spatial queries (RA/Dec)
- Source tracking (Gaia, TESS, etc.)
- Observation metadata preservation
- Quality flags and validation status
- Duplicate observation links
- Cross-reference IDs
- Complete audit trail

### 📤 Export & Interoperability
- IVOA VOTable format (XML)
- CSV export with custom columns
- JSON API responses
- Proper UCD (Unified Content Descriptors)
- FITS table export (planned)
- Virtual Observatory compliance
- Bulk download endpoints
- Streaming for large datasets

### 🎯 Planet Hunter View
- Pre-filtered for TESS targets
- Brightness threshold filtering (G < 14 mag)
- Proper motion cuts for nearby stars
- Parallax quality requirements
- Exoplanet host star candidates
- Light curve availability flags
- Priority ranking for observations
- Observability calculations

### 📐 Astrometry Tools
- Coordinate transformation (ICRS, Galactic, Ecliptic)
- Epoch conversion (J2000, J2015.5, etc.)
- Proper motion corrections
- Parallax-based distances with uncertainties
- Angular separation calculations
- Position angle computations
- Precession and nutation
- Barycentric corrections

### 📊 Analytics Dashboard
- Platform statistics (total stars, sources, duplicates)
- Data quality metrics
- Ingestion history and logs
- Anomaly detection results
- Clustering visualizations
- Sky coverage maps
- Magnitude distributions
- Interactive Recharts visualizations

### 🔐 Security Features
- JWT authentication for protected endpoints
- API key management
- Rate limiting per user
- Input validation and sanitization
- SQL injection protection (ORM)
- CORS configuration
- HTTPS enforcement (production)
- Audit logging

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" alt="Divider">

## 📂 Project Structure

```
cosmic-data-fusion/
│
├── 📱 frontend/                    # React Frontend Application
│   ├── src/
│   │   ├── components/            # Reusable UI components
│   │   ├── pages/                 # Route pages
│   │   ├── services/              # API client
│   │   └── assets/                # Images and static files
│   ├── public/                    # Public assets
│   └── package.json
│
├── 🔧 app/                         # FastAPI Backend Application
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── database.py                # SQLAlchemy setup
│   ├── models.py                  # Database models
│   ├── schemas.py                 # Pydantic schemas
│   ├── api/                       # API route handlers
│   │   ├── ingestion.py
│   │   ├── query.py
│   │   ├── ai_discovery.py
│   │   ├── analytics.py
│   │   └── export.py
│   ├── services/                  # Business logic
│   │   ├── harmonization.py
│   │   ├── ai_engine.py
│   │   └── coordinate_tools.py
│   └── repository/                # Data access layer
│
├── 🗄️ alembic/                    # Database Migrations
│   ├── versions/                  # Migration scripts
│   └── env.py
│
├── 📊 scripts/                     # Data Processing Scripts
│   ├── fetch_real_data.py         # Download Gaia/TESS data
│   ├── verify_fits.py             # FITS file validation
│   └── visualize_clusters.py      # Plot clustering results
│
├── 📚 documentation/               # Project Documentation
│   ├── DATABASE_SETUP_GUIDE.md
│   ├── FRONTEND_HANDOFF.md
│   ├── PLANET_HUNTER_GUIDE.md
│   └── DOCUMENTATION_INDEX.md
│
├── 🐳 Deployment
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── .env.example
│
└── 📖 Configuration Files
    ├── requirements.txt
    ├── alembic.ini
    └── README.md
```

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:8e2de2,100:4a00e0&height=100&section=divider&text=Installation&fontColor=ffffff&fontSize=28">

## 🚀 Quick Start Guide

### Prerequisites
```bash
Python 3.11+
PostgreSQL (or SQLite for development)
Node.js 18+ (for frontend)
Git
```

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/cosmic-data-fusion.git
cd cosmic-data-fusion
```

### 2️⃣ Backend Setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure .env file
DATABASE_URL="sqlite:///./cosmic_data_fusion.db"
# Or for PostgreSQL:
# DATABASE_URL="postgresql://user:password@localhost:5432/cosmic"

# Run Alembic migrations
alembic upgrade head

# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
# Server runs on http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 3️⃣ Ingest Real Data
```bash
# Download and ingest Pleiades cluster data
python scripts/fetch_real_data.py

# This will:
# 1. Query Gaia DR3 for Pleiades (1000 stars)
# 2. Query NASA TESS Input Catalog
# 3. Harmonize coordinates to ICRS J2000
# 4. Cross-match duplicates
# 5. Store in unified catalog
```

### 4️⃣ Frontend Setup
```bash
cd frontend
npm install

# Configure .env.local file
VITE_API_URL=http://localhost:8000

# Start the React app
npm run dev
# App runs on http://localhost:5173
```

### 5️⃣ Run AI Discovery
```bash
# Discover anomalies and clusters
curl http://localhost:8000/api/ai/discover

# View results
curl http://localhost:8000/api/ai/anomalies?limit=50
curl http://localhost:8000/api/ai/clusters
```

### 6️⃣ Docker Quick Start (Alternative)
```bash
# Start all services with Docker Compose
docker-compose up -d

# Services:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:5173
# - PostgreSQL: localhost:5432
```

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 📸 Demo Screenshots

<div align="center">
  <table>
    <tr>
      <td><b>🏠 Landing Page</b></td>
      <td><b>📊 Dashboard</b></td>
    </tr>
    <tr>
      <td><img src="./images/landing_page.png" alt="Landing Page" width="400"></td>
      <td><img src="./images/dahsboard.png" alt="Dashboard" width="400"></td>
    </tr>
    <tr>
      <td><b>🤖 AI Lab</b></td>
      <td><b>🔍 Query Builder</b></td>
    </tr>
    <tr>
      <td><img src="./images/AI_Lab_Page.png" alt="AI Lab" width="400"></td>
      <td><img src="./images/query_builder.png" alt="Query Builder" width="400"></td>
    </tr>
    <tr>
      <td><b>🗺️ Sky Map</b></td>
      <td><b>🔗 Data Harmonizer</b></td>
    </tr>
    <tr>
      <td><img src="./images/sky_map.png" alt="Sky Map" width="400"></td>
      <td><img src="./images/Data_fusion_harmonizer_page.png" alt="Data Harmonizer" width="400"></td>
    </tr>
    <tr>
      <td><b>📋 Data Table</b></td>
      <td><b>🔐 Sign In</b></td>
    </tr>
    <tr>
      <td><img src="./images/data_table_pafe.png" alt="Data Table" width="400"></td>
      <td><img src="./images/sing_in_page.png" alt="Sign In" width="400"></td>
    </tr>
  </table>
</div>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:3B82F6,100:1E40AF&height=100&section=divider&text=Demo&fontColor=ffffff&fontSize=28">

## 📽️ Demo Video

<div align="center">
  <a href="https://drive.google.com/drive/folders/1NGhnJ-7C9azPE2Tu-0HtQx-ZAjK5msUR" target="_blank">
    <img src="https://img.shields.io/badge/▶️-Watch_Demo_Video-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="Watch Demo">
  </a>
  <br><br>
  <p><em>Click above to view our complete demo video showcasing the platform features</em></p>
</div>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" alt="Divider">

## 📊 Project Presentation

<div align="center">
  <a href="https://drive.google.com/drive/folders/1NGhnJ-7C9azPE2Tu-0HtQx-ZAjK5msUR" target="_blank">
    <img src="https://img.shields.io/badge/View%20Presentation-D62828?style=for-the-badge&logo=google-drive&logoColor=white" alt="View Presentation">
  </a>
  <p><em>Click above to view the complete project presentation and documentation</em></p>
</div>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" alt="Divider">

## 📽️ API Examples

### 🔍 Cone Search
```bash
# Search for stars within 1 degree of Pleiades center
curl "http://localhost:8000/api/query/cone?ra=56.75&dec=24.12&radius_deg=1.0"
```

### 📊 Get Anomalies
```bash
# Get top 50 anomalous stars
curl "http://localhost:8000/api/ai/anomalies?limit=50&threshold=-0.1"
```

### 📤 Export to VOTable
```bash
# Export search results to IVOA VOTable
curl "http://localhost:8000/api/export/votable?source=Gaia" -o gaia_export.xml
```

### 🎯 Planet Hunter Targets
```bash
# Get bright stars for exoplanet transit searches
curl "http://localhost:8000/api/query/planet-hunter?max_gmag=12&min_parallax=5"
```

## 📱 API Documentation

<div align="center">
  <a href="http://localhost:8000/docs" target="_blank">
    <img src="https://img.shields.io/badge/📚-Interactive_API_Docs-3B82F6?style=for-the-badge&logo=swagger&logoColor=white">
  </a>
  <a href="http://localhost:8000/redoc" target="_blank">
    <img src="https://img.shields.io/badge/📖-ReDoc_Documentation-10B981?style=for-the-badge&logo=readthedocs&logoColor=white">
  </a>
  <br><br>
  <p><strong>20+ API endpoints documented</strong> | <strong>Complete OpenAPI specification</strong></p>
  
  <table>
    <tr>
      <td><b>📚 Category</b></td>
      <td><b>🔢 Endpoints</b></td>
      <td><b>📝 Description</b></td>
    </tr>
    <tr>
      <td>🚀 Ingestion</td>
      <td>4</td>
      <td>Upload and process Gaia/TESS data</td>
    </tr>
    <tr>
      <td>🔍 Query</td>
      <td>5</td>
      <td>Cone search, bounding box, filters</td>
    </tr>
    <tr>
      <td>🤖 AI Discovery</td>
      <td>3</td>
      <td>Anomalies, clusters, statistics</td>
    </tr>
    <tr>
      <td>📤 Export</td>
      <td>3</td>
      <td>VOTable, CSV, JSON formats</td>
    </tr>
    <tr>
      <td>📊 Analytics</td>
      <td>4</td>
      <td>Platform statistics and metrics</td>
    </tr>
    <tr>
      <td>🎯 Planet Hunter</td>
      <td>2</td>
      <td>Exoplanet target selection</td>
    </tr>
  </table>
  
  <br>
  <p><em>🔥 Total: <strong>21+ API Endpoints</strong> for astronomical data access</em></p>
</div>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" alt="Divider">

## 🗺️ Roadmap

### ✅ Completed Phases

- ✅ **Phase 1**: Core data models and SQLAlchemy setup
- ✅ **Phase 2**: Gaia DR3 adapter with coordinate standardization
- ✅ **Phase 3**: NASA TESS Input Catalog integration
- ✅ **Phase 4**: Cross-matching engine with Astropy
- ✅ **Phase 5**: AI anomaly detection (Isolation Forest)
- ✅ **Phase 6**: DBSCAN spatial clustering
- ✅ **Phase 7**: REST API with FastAPI
- ✅ **Phase 8**: Export to VOTable format
- ✅ **Phase 9**: Query optimization and indexing
- ✅ **Phase 10**: React frontend with Recharts
- ✅ **Phase 11**: Planet Hunter specialized view
- ✅ **Phase 12**: Analytics dashboard
- ✅ **Phase 13**: Docker containerization
- ✅ **Phase 14**: Comprehensive documentation

### 🚀 Future Enhancements

- 🔜 **SDSS DR17 adapter** for spectroscopic data
- 🔜 **2MASS integration** for infrared magnitudes
- 🔜 **Time-series analysis** for variable stars
- 🔜 **Aladin Lite integration** for interactive sky maps
- 🔜 **PostgreSQL + PostGIS** for production deployment
- 🔜 **GraphQL API** for flexible queries
- 🔜 **WebSocket support** for real-time ingestion updates
- 🔜 **Redis caching** for frequently accessed queries
- 🔜 **Kubernetes deployment** for scalability
- 🔜 **ML model for stellar classification** (main sequence, giants, white dwarfs)

### 🎯 Platform Status: Production Ready

The core pipeline is feature-complete and tested with real Gaia DR3 and TESS data. The system has successfully:
- Ingested 1,000 stars from the Pleiades Cluster
- Cross-matched 459 duplicate observations
- Identified 50 anomalous objects
- Served queries with sub-second response times

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 🧠 What We Learned

- 🔭 **Astrometry Fundamentals**: Deep understanding of coordinate systems, epochs, and proper motion corrections
- 🤖 **ML for Astronomy**: Applying unsupervised learning to unlabeled stellar catalogs
- 📊 **Data Pipeline Design**: Building scalable ETL for petabyte-scale astronomical surveys
- ⚡ **FastAPI Performance**: Async Python for high-throughput API endpoints
- 🗄️ **Spatial Indexing**: Optimizing RA/Dec queries with database indexes
- 📤 **IVOA Standards**: Implementing VOTable and UCD for interoperability
- 🔬 **Domain Expertise**: Collaborating with astronomers to define scientifically useful features
- 🧪 **Testing Strategies**: Validating against known star clusters (Pleiades, Hyades)
- 🐳 **Containerization**: Reproducible environments with Docker Compose
- 📈 **Data Visualization**: Creating meaningful charts for multi-dimensional stellar data
- 🔍 **Query Optimization**: Balancing flexibility and performance in search APIs
- 🔗 **Cross-Matching**: Handling ambiguous matches and duplicate observations

---

## 🧩 Challenges Faced

- ⚠️ **Coordinate Ambiguity**: Handling stars near RA=0°/360° and Dec=±90° poles
- 🔍 **Cross-Match Accuracy**: Balancing false positives (wrong matches) vs. false negatives (missed duplicates)
- 💾 **Data Volume**: Processing 1.8 billion Gaia sources requires careful memory management
- 🤖 **Anomaly Validation**: Determining which AI-flagged objects are scientifically interesting vs. data artifacts
- ⏰ **Epoch Conversion**: Proper motion corrections for stars observed decades apart
- 📊 **Magnitude Systems**: Converting between Gaia G/BP/RP and standard Johnson-Cousins UBVRI
- 🌐 **API Design**: Creating intuitive endpoints for both novice users and expert astronomers
- 🔄 **Data Freshness**: Keeping catalog synchronized with upstream survey releases
- 📱 **Frontend Complexity**: Rendering thousands of stars on interactive sky maps without lag
- 🧪 **Testing Real Data**: Unit tests are straightforward, but validating against actual sky surveys is challenging
- 🔌 **Astroquery Rate Limits**: Respecting ESA and NASA API quotas during bulk downloads
- 🎨 **UX for Scientists**: Designing interfaces that match astronomers' mental models
- 🗃️ **Database Schema Evolution**: Alembic migrations while preserving user-ingested data
- 🔒 **Data Quality**: Handling null values, measurement uncertainties, and quality flags from surveys

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" alt="Divider">

## 👥 Team BitBuilders

<div align="center">
  <table>
    <tr>
      <td align="center">
        <img src="https://media.giphy.com/media/bGgsc5mWoryfgKBx1u/giphy.gif" width="150px" alt="Abhishek Chaudhari" style="border-radius: 50%;"><br>
        <h3>🧑‍💻 Abhishek Chaudhari</h3>
        <p>Full Stack Developer</p>
        <a href="https://www.linkedin.com/in/abhishek-chaudhari-949002356" target="_blank">
          <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn">
        </a>
        <a href="https://github.com/Abhi-786-coder" target="_blank">
          <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
        </a>
      </td>
      <td align="center">
        <img src="https://media.giphy.com/media/bGgsc5mWoryfgKBx1u/giphy.gif" width="150px" alt="Lokesh Gile" style="border-radius: 50%;"><br>
        <h3>🧑‍💻 Lokesh Gile</h3>
        <p>Backend & AI Developer</p>
        <a href="https://www.linkedin.com/in/lokesh-gile-b61145248" target="_blank">
          <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn">
        </a>
        <a href="https://github.com/Loki3306" target="_blank">
          <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
        </a>
      </td>
    </tr>
    <tr>
      <td align="center">
        <img src="https://media.giphy.com/media/bGgsc5mWoryfgKBx1u/giphy.gif" width="150px" alt="Yug Deshmukh" style="border-radius: 50%;"><br>
        <h3>🧑‍💻 Yug Deshmukh</h3>
        <p>Frontend Developer</p>
        <a href="https://www.linkedin.com/in/yugtheguy" target="_blank">
          <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn">
        </a>
        <a href="https://github.com/yugtheguy" target="_blank">
          <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
        </a>
      </td>
      <td align="center">
        <img src="https://media.giphy.com/media/bGgsc5mWoryfgKBx1u/giphy.gif" width="150px" alt="Deep Mehta" style="border-radius: 50%;"><br>
        <h3>🧑‍💻 Deep Mehta</h3>
        <p>Data Pipeline & DevOps</p>
        <a href="https://www.linkedin.com/in/deep-mehta-857a09304" target="_blank">
          <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn">
        </a>
        <a href="https://github.com/DeepMehta06" target="_blank">
          <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
        </a>
      </td>
    </tr>
  </table>
</div>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 🔗 Project Links

<div align="center">
  <a href="./documentation/DATABASE_SETUP_GUIDE.md">
    <img src="https://img.shields.io/badge/📖-Database_Setup-3B82F6?style=for-the-badge" alt="Database Setup">
  </a>
  <a href="./documentation/PLANET_HUNTER_GUIDE.md">
    <img src="https://img.shields.io/badge/🎯-Planet_Hunter-8B5CF6?style=for-the-badge" alt="Planet Hunter">
  </a>
  <a href="./documentation/FRONTEND_HANDOFF.md">
    <img src="https://img.shields.io/badge/⚛️-Frontend_Guide-10B981?style=for-the-badge" alt="Frontend">
  </a>
  <a href="./documentation/DOCUMENTATION_INDEX.md">
    <img src="https://img.shields.io/badge/📚-Full_Docs-F59E0B?style=for-the-badge" alt="Documentation">
  </a>
  <br><br>
  <a href="http://localhost:8000/docs">
    <img src="https://img.shields.io/badge/🚀-API_Docs-06B6D4?style=for-the-badge" alt="API Docs">
  </a>
  <a href="./docker-compose.yml">
    <img src="https://img.shields.io/badge/🐳-Docker_Compose-2496ED?style=for-the-badge" alt="Docker">
  </a>
  <a href="./requirements.txt">
    <img src="https://img.shields.io/badge/📦-Dependencies-EC4899?style=for-the-badge" alt="Requirements">
  </a>
</div>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" alt="Divider">

## 📊 Project Statistics

<div align="center">

| Component | Technology | Count |
|-----------|-----------|-------|
| 🐍 Python Files | FastAPI/Astropy | 35+ |
| 🛣️ API Endpoints | REST | 21+ |
| ⚛️ React Components | Next.js | 25+ |
| 📄 Pages | React Router | 8+ |
| 🗄️ Database Tables | SQLAlchemy | 5 |
| 🤖 ML Models | Scikit-learn | 2 |
| 📊 Data Sources | Gaia + TESS | 2 |
| 🔐 Auth Methods | JWT | 1 |
| 📝 Migrations | Alembic | 3+ |
| 🧪 Test Files | Pytest | 8+ |
| 📚 Documentation | Markdown | 4 |
| ⭐ Stars Ingested | Real Data | 1,000+ |

</div>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=100&section=divider&text=Impact&fontColor=ffffff&fontSize=28&animation=twinkling">

## 🌟 Impact & Vision

### Current Impact
- 🔬 Automated harmonization of Gaia DR3 and TESS catalogs for 1,000+ stars
- 🤖 AI-discovered 50 anomalous objects in the Pleiades Cluster
- 🔗 Successfully cross-matched 459 duplicate observations across surveys
- ⚡ Sub-second cone search queries for time-domain astronomy
- 📤 IVOA-compliant VOTable exports for interoperability
- 📊 Real-time analytics dashboard for data quality monitoring
- 🎯 Planet Hunter view for exoplanet transit search target selection
- 🐳 Docker-based reproducible deployment

### Platform Achievements
- ✅ Production-ready FastAPI backend with 21+ endpoints
- ✅ Comprehensive data harmonization pipeline
- ✅ Unsupervised ML for automated discovery
- ✅ Modern React frontend with interactive visualizations
- ✅ Complete API documentation (Swagger + ReDoc)
- ✅ Alembic migrations for schema evolution
- ✅ Pytest test suite with real data validation
- ✅ Docker Compose for one-command deployment

### Future Vision
This platform represents the future of multi-survey astronomy—automated, AI-driven, and interoperable. By eliminating manual data wrangling, we enable astronomers to focus on discovery rather than data processing. Our long-term vision includes:

- 🌍 **Global Catalog**: Harmonize all major sky surveys (SDSS, 2MASS, Pan-STARRS, WISE)
- 🤖 **Deep Learning**: Train CNNs on light curves for variable star classification
- 📡 **Real-Time Ingestion**: Stream transient alerts from LSST/ZTF for immediate follow-up
- 🌌 **3D Universe**: Build a 3D spatial catalog using parallax-based distances
- 🔬 **Science Platform**: Jupyter notebooks for interactive analysis on our unified catalog

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 🔒 Security Considerations

- ✅ SQLAlchemy ORM prevents SQL injection
- ✅ JWT authentication for protected endpoints
- ✅ Input validation with Pydantic schemas
- ✅ Rate limiting on ingestion endpoints (planned)
- ✅ CORS configuration for API security
- ✅ Environment variables for secrets (.env)
- ✅ HTTPS enforcement in production
- ✅ API key rotation support
- ✅ Audit logging for data modifications
- ✅ Read-only database user for query endpoints

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test files
pytest tests/test_harmonization.py
pytest tests/test_ai_discovery.py

# Test against real Gaia data
python scripts/verify_fits.py
```

## 🤝 Contributing

We welcome contributions from astronomers, data scientists, and developers! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Contribution Ideas
- 🔭 Add adapters for new astronomical surveys
- 🤖 Improve ML models for stellar classification
- 📊 Create new visualization types
- 📚 Write tutorials for specific science use cases
- 🐛 Report bugs or suggest enhancements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **ESA Gaia Mission** for providing DR3 catalog through Astroquery
- **NASA TESS Mission** for exoplanet host star candidate data
- **Astropy Community** for professional-grade astronomical Python tools
- **FastAPI Team** for the excellent web framework
- **Scikit-learn Contributors** for battle-tested ML algorithms
- **IVOA Standards** for defining interoperable astronomical data formats
- All open-source contributors whose work made this possible

### Data Sources
- Gaia DR3: ESA/Gaia/DPAC, A&A 674, A1 (2023)
- TESS Input Catalog: Stassun et al., AJ 156, 102 (2018)

---

> 🔭 *"Unifying the cosmos, one star at a time. Empowering discovery through data harmonization."*

<div align="center">
  <sub>Built with 💙 by Team BitBuilders</sub>
  <br>
  <sub>Powered by AI & Astrometry</sub>
</div>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=120&section=footer">
