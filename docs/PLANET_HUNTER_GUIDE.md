# 🪐 Planet Hunter Module - Installation & Usage Guide

## Overview

The **Planet Hunter** module adds exoplanet detection capabilities to COSMIC Data Fusion using NASA's TESS mission data and Box Least Squares (BLS) transit analysis.

**Detection Algorithm:** Identifies periodic dimming in stellar light curves caused by orbiting planets.

---

## 📦 Installation

### 1. Install Dependencies

```bash
pip install lightkurve numpy matplotlib
```

**Package Details:**
- `lightkurve` (2.4+) - NASA's official tool for Kepler/TESS data analysis
- `numpy` - Already installed (scientific computing)
- `matplotlib` - Required by lightkurve for plotting

**Verify Installation:**
```bash
python -c "import lightkurve; print(f'lightkurve {lightkurve.__version__}')"
```

### 2. Database Migration

The module automatically creates the `exoplanet_candidates` table on first run. No manual migration needed.

**Verify Table Creation:**
```bash
# Start the server
uvicorn app.main:app --reload

# Check logs for:
# "Database tables initialized successfully (including exoplanet_candidates)"
```

---

## 🚀 Quick Start

### Example 1: Detect Planet Around Known Host

```bash
# TIC 261136679 = TOI 270 (known triple-planet system)
curl -X POST "http://localhost:8000/analysis/planet-hunt/261136679" \
     -H "Content-Type: application/json" \
     -d '{}'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Planet candidate detected! Period: 3.853 days, Depth: 0.453%, Power: 15.20",
  "candidate": {
    "id": 1,
    "source_id": "261136679",
    "period_days": 3.852826,
    "transit_time_btjd": 1683.4521,
    "duration_hours": 2.34,
    "depth_ppm": 4530.0,
    "depth_percent": 0.453,
    "power": 15.2,
    "snr": 8.5,
    "num_transits": 12,
    "mission": "TESS",
    "sector": 9,
    "status": "candidate"
  },
  "plot_data": {
    "phase_binned": [-0.5, -0.4, ..., 0.4, 0.5],
    "flux_binned": [1.0, 1.0, ..., 0.995, 1.0],
    "period": 3.852826,
    "depth": 0.00453,
    "duration_hours": 2.34
  }
}
```

### Example 2: Custom Period Search Range

```bash
# Search for short-period planets only (0.5-5 days)
curl -X POST "http://localhost:8000/analysis/planet-hunt/307210830" \
     -H "Content-Type: application/json" \
     -d '{
       "min_period": 0.5,
       "max_period": 5.0,
       "num_periods": 20000
     }'
```

---

## 📊 API Endpoints

### 1. **Hunt for Planets**
```
POST /analysis/planet-hunt/{tic_id}
```

**Description:** Analyze TESS light curve for transit signals.

**Path Parameters:**
- `tic_id` (string) - TESS Input Catalog ID (e.g., "261136679")

**Request Body (optional):**
```json
{
  "min_period": 0.5,     // Minimum period (days), default: 0.5
  "max_period": 20.0,    // Maximum period (days), default: 20.0
  "num_periods": 10000   // Number of trial periods, default: 10000
}
```

**Response:** `PlanetHuntResponse` with candidate parameters and plot data.

**Example Known Targets:**
- `261136679` - TOI 270 (triple-planet system, Neptune-sized)
- `307210830` - TOI 700 (Earth-sized planet in habitable zone)
- `38846515` - Pi Mensae (super-Earth + Jupiter)
- `150428135` - L 98-59 (five rocky planets)
- `231663901` - AU Mic (Neptune-sized planet around young star)

---

### 2. **List All Candidates**
```
GET /analysis/candidates
```

**Query Parameters:**
- `status` (string, optional) - Filter by status (candidate, confirmed, false_positive)
- `min_power` (float, optional) - Minimum BLS power threshold
- `limit` (integer, default: 100) - Maximum results

**Example:**
```bash
curl "http://localhost:8000/analysis/candidates?status=candidate&min_power=10&limit=50"
```

**Response:**
```json
{
  "total": 3,
  "candidates": [
    {
      "id": 1,
      "source_id": "261136679",
      "period_days": 3.852826,
      "depth_percent": 0.453,
      "power": 15.2,
      "status": "candidate"
    },
    ...
  ]
}
```

---

### 3. **Get Candidates for Specific Star**
```
GET /analysis/candidates/{tic_id}
```

**Example:**
```bash
curl "http://localhost:8000/analysis/candidates/261136679"
```

---

### 4. **Get Candidate Details with Plot Data**
```
GET /analysis/candidate/{candidate_id}
```

**Example:**
```bash
curl "http://localhost:8000/analysis/candidate/1"
```

**Response:** Full candidate details + folded light curve data for plotting.

---

### 5. **Update Candidate Status**
```
PATCH /analysis/candidate/{candidate_id}/status
```

**Request Body:**
```json
{
  "status": "confirmed",
  "notes": "Validated with radial velocity follow-up"
}
```

**Valid Statuses:**
- `candidate` - Initial detection, not yet validated
- `confirmed` - Validated as real exoplanet
- `false_positive` - Identified as stellar activity or error
- `under_review` - Being analyzed by researchers

---

### 6. **Delete Candidate**
```
DELETE /analysis/candidate/{candidate_id}
```

---

## 🧪 Testing

### Test with Known Planet Host

```python
import requests

# Analyze TOI 270 (known triple-planet system)
response = requests.post(
    "http://localhost:8000/analysis/planet-hunt/261136679"
)

data = response.json()
print(f"Success: {data['success']}")
print(f"Message: {data['message']}")

if data['success']:
    candidate = data['candidate']
    print(f"\nDetected Planet:")
    print(f"  Period: {candidate['period_days']} days")
    print(f"  Depth: {candidate['depth_percent']}%")
    print(f"  Transit Duration: {candidate['duration_hours']} hours")
    print(f"  BLS Power: {candidate['power']}")
    print(f"  Number of Transits: {candidate['num_transits']}")
```

---

## 📈 Frontend Integration

### Plotting Folded Light Curve

The API returns `plot_data` with folded light curve coordinates:

**JavaScript Example (Plotly.js):**
```javascript
const response = await fetch('/analysis/planet-hunt/261136679', {
  method: 'POST'
});

const data = await response.json();

if (data.success) {
  const plotData = data.plot_data;
  
  // Plot with Plotly
  Plotly.newPlot('lightcurve-chart', [{
    type: 'scatter',
    mode: 'markers',
    x: plotData.phase_binned,
    y: plotData.flux_binned,
    marker: {
      size: 4,
      color: 'blue'
    },
    name: 'Folded Light Curve'
  }], {
    title: `Planet Candidate - Period: ${plotData.period.toFixed(3)} days`,
    xaxis: { title: 'Orbital Phase' },
    yaxis: { title: 'Normalized Flux' }
  });
}
```

**React Component Example:**
```jsx
import Plot from 'react-plotly.js';

function PlanetHunterChart({ plotData }) {
  return (
    <Plot
      data={[{
        type: 'scatter',
        mode: 'markers',
        x: plotData.phase_binned,
        y: plotData.flux_binned,
        marker: { size: 3, color: '#4A90D9' },
        name: 'Binned Data'
      }]}
      layout={{
        title: `Transit Detection - Period: ${plotData.period.toFixed(3)}d`,
        xaxis: { title: 'Phase', range: [-0.5, 0.5] },
        yaxis: { title: 'Normalized Flux' },
        paper_bgcolor: '#1a1a2e',
        plot_bgcolor: '#0f3460'
      }}
    />
  );
}
```

---

## 🔬 Science Background

### What is BLS?

**Box Least Squares (BLS)** is a fast algorithm for detecting periodic box-shaped dips in light curves, optimized for exoplanet transits.

**How it Works:**
1. **Trial Periods:** Test thousands of orbital periods (0.5-20 days)
2. **Phase Folding:** Fold light curve at each period
3. **Box Model:** Fit a box-shaped transit model
4. **Power Calculation:** Measure goodness-of-fit (higher = better detection)
5. **Best Period:** Select period with maximum power

**Key Metrics:**
- **Period:** Orbital period (Earth = 365 days, Hot Jupiters = 1-5 days)
- **Depth:** Fractional flux loss = (R_planet / R_star)²
- **Duration:** Transit duration ~ R_star / orbital_velocity
- **Power:** BLS signal strength (>10 = significant detection)

### TESS Mission

**Transiting Exoplanet Survey Satellite (NASA, 2018-present):**
- **Cadence:** 30-minute exposures (FFI), 2-minute for targets
- **Coverage:** ~85% of sky over 2 years
- **Targets:** 200,000+ pre-selected stars per sector
- **Sectors:** 27 days each, observing different sky regions

**Data Products:**
- **SPOC (Science Processing Operations Center):** Official pipeline
- **QLP (Quick-Look Pipeline):** Faster, less refined
- **TESS-SPOC:** Best for planet detection (used by this module)

---

## ⚠️ Limitations & Notes

### 1. **Data Availability**
- Not all stars have TESS data (only observed sectors)
- Use https://heasarc.gsfc.nasa.gov/cgi-bin/tess/webtess/wtv.py to check coverage
- API returns `success: false` if no data available

### 2. **False Positives**
- Eclipsing binaries (stars, not planets)
- Stellar activity (starspots rotating)
- Instrumental systematics
- **Always validate** with follow-up observations

### 3. **Detection Limits**
- **Small planets:** Harder to detect (shallow transits)
- **Long periods:** Need more data (fewer transits)
- **Bright stars:** Better signal-to-noise
- **Optimal:** Neptune-sized planets, 1-10 day periods

### 4. **Analysis Time**
- **Typical:** 30-60 seconds per target
- **Download:** 5-10 seconds (MAST archive)
- **BLS:** 20-40 seconds (10,000 trial periods)
- **Async recommended** for production (use Celery)

---

## 🎯 Interpreting Results

### Strong Candidate (Likely Planet)
✅ **Power > 15**  
✅ **SNR > 7**  
✅ **Depth 0.1-5% (Earth to Jupiter-sized)**  
✅ **Duration 1-6 hours**  
✅ **Multiple transits (>3)**  
✅ **Clean folded light curve (smooth "U" or "V" shape)**

### Weak Candidate (Needs Validation)
⚠️ **Power 8-15**  
⚠️ **SNR 4-7**  
⚠️ **Noisy folded light curve**  
⚠️ **Only 1-2 transits**

### False Positive (Not a Planet)
❌ **Power < 5**  
❌ **Depth > 10% (likely eclipsing binary)**  
❌ **Irregular shape (stellar activity)**  
❌ **No clear periodicity**

---

## 🚀 Production Deployment

### Async Processing (Recommended)

For production, use Celery to offload analysis:

```python
# app/tasks/planet_hunter.py
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task
def analyze_tic_async(tic_id: str):
    from app.database import SessionLocal
    from app.services.planet_hunter import PlanetHunterService
    
    db = SessionLocal()
    service = PlanetHunterService(db)
    candidate = service.analyze_tic_target(tic_id)
    db.close()
    
    return candidate.id if candidate else None
```

**Modified API Endpoint:**
```python
@router.post("/planet-hunt/{tic_id}/async")
async def hunt_async(tic_id: str):
    task = analyze_tic_async.delay(tic_id)
    return {"task_id": task.id, "status": "processing"}
```

---

## 📚 Additional Resources

- **lightkurve Docs:** https://docs.lightkurve.org/
- **TESS Mission:** https://tess.mit.edu/
- **BLS Paper:** Kovács et al. 2002 (A&A 391, 369)
- **Exoplanet Archive:** https://exoplanetarchive.ipac.caltech.edu/

---

## 🐛 Troubleshooting

### Error: "No TESS data available"
**Solution:** Star not observed by TESS. Try different TIC ID or check observation coverage.

### Error: "Too few data points after cleaning"
**Solution:** Light curve too short or too noisy. Try different sector or star.

### Error: "lightkurve not installed"
**Solution:** `pip install lightkurve`

### Low BLS Power (<5)
**Solution:** No significant signal detected. Star may have no planets, or planets are too small/long-period.

---

## 📝 Example Workflow

```python
# Complete analysis workflow

import requests

# 1. Hunt for planets
response = requests.post("http://localhost:8000/analysis/planet-hunt/261136679")
data = response.json()

if data['success']:
    candidate_id = data['candidate']['id']
    
    # 2. Get full details
    details = requests.get(f"http://localhost:8000/analysis/candidate/{candidate_id}")
    
    # 3. Update status after validation
    requests.patch(
        f"http://localhost:8000/analysis/candidate/{candidate_id}/status",
        json={"status": "confirmed", "notes": "RV confirmation"}
    )
    
    # 4. List all confirmed planets
    confirmed = requests.get("http://localhost:8000/analysis/candidates?status=confirmed")
    print(f"Total confirmed: {confirmed.json()['total']}")
```

---

**Module Status:** ✅ **Production Ready**  
**Dependencies:** lightkurve, numpy, matplotlib  
**Database Table:** `exoplanet_candidates` (auto-created)  
**API Prefix:** `/analysis`  
**Last Updated:** January 14, 2026
