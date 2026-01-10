# 🔭 COSMIC Data Fusion

**Astronomical Data Standardization Backend**

A research-grade FastAPI backend for ingesting, standardizing, and visualizing astronomical catalog data. All coordinates are automatically transformed to ICRS J2000 using Astropy.

## ✨ Features

- **Multi-Frame Ingestion** — Accept coordinates in ICRS, FK5, or Galactic frames
- **Automatic Transformation** — All coordinates converted to ICRS J2000 via Astropy SkyCoord
- **Spatial Search** — Bounding box and cone search with proper spherical geometry
- **Visualization APIs** — Pre-formatted data for sky maps, heatmaps, and dashboards
- **Gaia DR3 Integration** — Bundled sample dataset ready to load

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI 0.109+ |
| Database | SQLite (SQLAlchemy 2.0 ORM) |
| Validation | Pydantic v2 |
| Astronomy | Astropy 6.0+ |
| Server | Uvicorn |

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/cosmic-data-fusion.git
cd cosmic-data-fusion

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Quick Start

```bash
# Start the server
uvicorn app.main:app --reload

# Load Gaia sample data
curl -X POST http://localhost:8000/datasets/gaia/load

# Check sky visualization endpoint
curl "http://localhost:8000/visualize/sky?limit=100"
```

## 📡 API Endpoints

### Ingestion
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest/star` | Ingest single star with coordinate transformation |
| POST | `/ingest/bulk` | Bulk insert up to 10,000 stars |

### Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/search/box` | Rectangular RA/Dec bounding box query |
| GET | `/search/cone` | Circular search with angular separation |

### Datasets
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/datasets/gaia/load` | Load bundled Gaia DR3 sample (~200 stars) |
| GET | `/datasets/gaia/stats` | Get Gaia dataset statistics |

### Visualization
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/visualize/sky` | Points for scatter plot (sorted by brightness) |
| GET | `/visualize/density` | Binned counts for heatmap |
| GET | `/visualize/stats` | Catalog statistics for dashboards |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service and database health check |

## 📁 Project Structure

```
app/
├── main.py              # FastAPI application entry point
├── database.py          # SQLAlchemy engine and session
├── models.py            # ORM models (UnifiedStarCatalog)
├── schemas.py           # Pydantic request/response schemas
├── api/
│   ├── ingest.py        # Ingestion endpoints
│   ├── search.py        # Search endpoints
│   ├── datasets.py      # Dataset loading endpoints
│   ├── visualize.py     # Visualization endpoints
│   └── health.py        # Health check endpoint
├── services/
│   ├── standardizer.py  # Astropy coordinate transformations
│   ├── ingestion.py     # Ingestion business logic
│   ├── search.py        # Search business logic
│   ├── visualization.py # Visualization data prep
│   ├── csv_ingestion.py # Generic CSV parser
│   └── gaia_ingestion.py# Gaia-specific loader
├── repository/
│   └── star_catalog.py  # Database CRUD operations
└── data/
    └── gaia_dr3_sample.csv  # Bundled Gaia sample
```

## 🌌 Coordinate Systems

| Frame | Description | Input Parameters |
|-------|-------------|------------------|
| ICRS | International Celestial Reference System (modern standard) | RA (0-360°), Dec (-90° to +90°) |
| FK5 | Fifth Fundamental Catalog (J2000 epoch) | RA, Dec |
| Galactic | Galactic coordinate system | l (longitude), b (latitude) |

All coordinates are stored internally as **ICRS J2000**.

## 📊 Example: Ingest a Star

```bash
curl -X POST http://localhost:8000/ingest/star \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "HD_12345",
    "coord1": 180.5,
    "coord2": -45.2,
    "brightness_mag": 4.5,
    "original_source": "Manual Entry",
    "frame": "galactic"
  }'
```

## 📊 Example: Cone Search

```bash
# Search 2° radius around Galactic Center
curl "http://localhost:8000/search/cone?ra=266.4&dec=-29.0&radius=2.0&limit=100"
```

## 📜 License & Attribution

This project is for educational and hackathon purposes.

**Gaia Data**: The bundled Gaia DR3 sample is provided by ESA under the [Gaia Archive terms](https://gea.esac.esa.int/archive/). This excerpt is for demonstration purposes only — not for scientific use.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

Built with ☕ and 🔭 for the COSMIC hackathon
