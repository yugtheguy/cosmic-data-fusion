# 🚀 Planet Hunter - Quick Start

## Install Dependencies
```bash
pip install lightkurve matplotlib
```

## Restart Server
```bash
uvicorn app.main:app --reload
```

## Test First Detection
```bash
# TOI 270 - Known triple-planet system
curl -X POST "http://localhost:8000/analysis/planet-hunt/261136679"
```

## API Endpoints
```
POST   /analysis/planet-hunt/{tic_id}      # Run analysis
GET    /analysis/candidates                 # List all
GET    /analysis/candidates/{tic_id}        # Get by star
GET    /analysis/candidate/{id}             # Get details
PATCH  /analysis/candidate/{id}/status      # Update status
DELETE /analysis/candidate/{id}             # Delete
```

## Known Test Targets
- `261136679` - TOI 270 (triple-planet system)
- `307210830` - TOI 700 (habitable zone planet)
- `38846515` - Pi Mensae (super-Earth)

## Docs
- Full Guide: `docs/PLANET_HUNTER_GUIDE.md`
- API Docs: http://localhost:8000/docs

## Files Created
- `app/models_exoplanet.py` - Database model
- `app/services/planet_hunter.py` - BLS analysis service
- `app/api/analysis.py` - REST API endpoints
- `tests/test_planet_hunter.py` - Test suite

## Database
Table `exoplanet_candidates` auto-created on startup.

## Analysis Time
30-60 seconds per target (MAST download + BLS computation)

---

**Status:** ✅ Ready for testing!
