# 🖥️ Frontend Integration Guide

> **COSMIC Data Fusion — Handoff Document for Frontend Team**  
> Everything you need to build the React/Next.js dashboard

**🎉 THE DATABASE IS NOW POPULATED WITH REAL SCIENCE!**

The backend is running with **1,000 real stars** from the **Pleiades Cluster (Messier 45)** — one of the most iconic star clusters in the sky. When you build the 3D sky map, you should see a **distinct, tight cluster of bright blue stars** centered at **RA 56.75°, Dec 24.1167°**.

**Key Stats:**
- ✅ 500 stars from Gaia DR3 (ESA) — ultra-precise positions
- ✅ 500 stars from NASA TESS — planet-hunting mission data
- ✅ 459 fusion groups — same stars observed by both telescopes
- ✅ 50 AI-detected anomalies — interesting objects for follow-up

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Recommended Tech Stack](#-recommended-tech-stack)
3. [API Base Configuration](#-api-base-configuration)
4. [Key Workflows](#-key-workflows)
   - [Workflow A: Sky Map Visualization](#workflow-a-sky-map-visualization-google-maps-for-space)
   - [Workflow B: AI Insights Overlay](#workflow-b-ai-insights-overlay-highlighting-anomalies)
   - [Workflow C: Harmonization View](#workflow-c-harmonization-view-cross-matched-stars)
   - [Workflow D: Data Export](#workflow-d-data-export)
5. [Data Dictionary](#-data-dictionary)
6. [Response Schemas](#-response-schemas)
7. [Error Handling](#-error-handling)
8. [Example Component Architecture](#-example-component-architecture)

---

## 🎯 Overview

The backend is **fully operational** and contains **REAL astronomical data from the Pleiades Cluster**. Your job is to build an interactive dashboard that:

1. **Displays stars on a sky map** — You'll see the famous Pleiades cluster formation (tight grouping of bright blue stars)
2. **Highlights AI-detected anomalies** — 50 real anomalous objects identified by our ML pipeline
3. **Shows cross-matched observations** — 459 fusion groups where Gaia and TESS observed the same star
4. **Allows data export** — Download real science data in CSV, JSON, or VOTable

The API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI).

### What You'll See in the Data

**The Pleiades (M45)** is one of the nearest open clusters:
- **Visual Appearance**: Tight cluster of bright blue stars (young, hot stars)
- **Coordinates**: Centered at RA ~56.75°, Dec ~24.1°
- **Notable Stars**: 
  - Atlas, Alcyone, Maia, Merope, Electra, Taygeta (the "Seven Sisters")
  - All will appear in your dataset with magnitudes 2-5 (very bright)
- **Cluster Spread**: Most members within ~1 degree radius
- **Expected Visualization**: Dense concentration of points in that region

When you query the data, you'll notice:
- ✨ **Bright stars (mag 2-5)**: The famous naked-eye members
- 🌟 **Medium stars (mag 6-10)**: Additional cluster members
- 🔍 **Faint stars (mag 11-13)**: Fainter members only visible to telescopes

---

## 🛠️ Recommended Tech Stack

| Category | Recommendation | Why |
|----------|----------------|-----|
| **Framework** | Next.js 14+ or React 18+ | SSR for initial load, excellent TypeScript support |
| **Sky Map** | [Aladin Lite](https://aladin.cds.unistra.fr/AladinLite/) | Industry-standard astronomical sky viewer, supports overlays |
| **Charts** | [Plotly.js](https://plotly.com/javascript/) or [D3.js](https://d3js.org/) | Interactive scatter plots with zoom/pan |
| **Data Fetching** | TanStack Query (React Query) | Caching, background refetching, optimistic updates |
| **State Management** | Zustand or React Context | Lightweight, perfect for filter state |
| **Styling** | Tailwind CSS | Rapid prototyping, dark theme support |

### Quick Setup Commands

```bash
# Create Next.js project
npx create-next-app@latest cosmic-frontend --typescript --tailwind

# Install dependencies
cd cosmic-frontend
npm install @tanstack/react-query axios plotly.js react-plotly.js
```

### Aladin Lite Integration

```html
<!-- Add to your HTML head or _document.tsx -->
<link rel="stylesheet" href="https://aladin.cds.unistra.fr/AladinLite/api/v3/latest/aladin.min.css" />
<script src="https://aladin.cds.unistra.fr/AladinLite/api/v3/latest/aladin.min.js"></script>
```

---

## 🔌 API Base Configuration

```typescript
// lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
```

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🗺️ Key Workflows

### Workflow A: Sky Map Visualization ("Google Maps for Space")

**Goal**: Display all stars as points on a 2D sky map.

#### Step 1: Fetch Star Data

```typescript
// POST /query/search
const fetchStars = async (filters?: {
  min_mag?: number;
  max_mag?: number;
  ra_min?: number;
  ra_max?: number;
  dec_min?: number;
  dec_max?: number;
  limit?: number;
}) => {
  const response = await api.post('/query/search', {
    limit: 1000,
    ...filters,
  });
  return response.data.records; // Array of star objects
};
```

#### Step 2: Map RA/Dec to Plot Coordinates

```typescript
// RA (0-360°) maps to X-axis
// Dec (-90° to +90°) maps to Y-axis
// NOTE: Astronomical convention often reverses RA (360 on left, 0 on right)

interface Star {
  id: number;
  source_id: string;
  ra_deg: number;      // 0-360
  dec_deg: number;     // -90 to +90
  brightness_mag: number;
  original_source: string;
}

const mapToPlotCoordinates = (stars: Star[]) => {
  return stars.map(star => ({
    x: 360 - star.ra_deg,  // Reverse for astronomical convention
    y: star.dec_deg,
    size: Math.max(2, 15 - star.brightness_mag), // Brighter = bigger
    id: star.id,
    label: star.source_id,
  }));
};
```

#### Step 3: Plotly.js Scatter Plot Example

```tsx
import Plot from 'react-plotly.js';

const SkyMap = ({ stars }: { stars: Star[] }) => {
  const plotData = mapToPlotCoordinates(stars);
  
  return (
    <Plot
      data={[{
        type: 'scatter',
        mode: 'markers',
        x: plotData.map(p => p.x),
        y: plotData.map(p => p.y),
        marker: {
          size: plotData.map(p => p.size),
          color: '#4A90D9',
          opacity: 0.7,
        },
        text: plotData.map(p => p.label),
        hoverinfo: 'text',
      }]}
      layout={{
        title: 'Sky Map',
        xaxis: { title: 'Right Ascension (°)', range: [360, 0] },
        yaxis: { title: 'Declination (°)', range: [-90, 90] },
        paper_bgcolor: '#1a1a2e',
        plot_bgcolor: '#16213e',
        font: { color: '#fff' },
      }}
    />
  );
};
```

---

### Workflow B: AI Insights Overlay (Highlighting Anomalies)

**Goal**: Highlight anomalous stars in **RED** on the sky map.

#### Step 1: Fetch Anomalies

```typescript
// POST /ai/anomalies
const fetchAnomalies = async (contamination: number = 0.05) => {
  const response = await api.post('/ai/anomalies', { contamination });
  return response.data.anomalies; // Array of 50 REAL anomalies from Pleiades
};

// Expected: ~50 anomalous objects that differ from the cluster pattern
// Most Pleiades members have parallax ~7.5 mas (distance ~136 pc)
// Anomalies likely include:
// - Foreground stars (higher parallax, closer to us)
// - Background stars (lower parallax, much farther away)
// - High proper motion objects passing through the field
```

#### Step 2: Create a Set of Anomaly IDs

```typescript
const anomalyIds = new Set(anomalies.map(a => a.id));
```

#### Step 3: Overlay on Sky Map

```tsx
const SkyMapWithAnomalies = ({ stars, anomalies }: Props) => {
  const anomalyIds = new Set(anomalies.map(a => a.id));
  
  // Split into normal and anomaly traces
  const normalStars = stars.filter(s => !anomalyIds.has(s.id));
  const anomalyStars = stars.filter(s => anomalyIds.has(s.id));
  
  return (
    <Plot
      data={[
        // Normal stars - blue
        {
          type: 'scatter',
          mode: 'markers',
          name: 'Normal Stars',
          x: normalStars.map(s => 360 - s.ra_deg),
          y: normalStars.map(s => s.dec_deg),
          marker: { size: 8, color: '#4A90D9' },
        },
        // Anomalies - RED with star marker
        {
          type: 'scatter',
          mode: 'markers',
          name: '⚠️ Anomalies',
          x: anomalyStars.map(s => 360 - s.ra_deg),
          y: anomalyStars.map(s => s.dec_deg),
          marker: { 
            size: 14, 
            color: '#FF4757',
            symbol: 'star',
            line: { width: 2, color: '#fff' }
          },
        },
      ]}
      layout={{
        title: 'Sky Map with AI Anomaly Detection',
        showlegend: true,
        // ... rest of layout
      }}
    />
  );
};
```

#### Anomaly Score Interpretation

```typescript
// anomaly_score is NEGATIVE for anomalies
// More negative = MORE anomalous
// Example: -0.45 is more anomalous than -0.15

const getAnomalyIntensity = (score: number) => {
  // Normalize to 0-1 scale (assuming scores range from -0.5 to 0)
  return Math.min(1, Math.abs(score) * 2);
};

// Use for color gradient: lighter red -> darker red
const getAnomalyColor = (score: number) => {
  const intensity = getAnomalyIntensity(score);
  return `rgba(255, 71, 87, ${0.5 + intensity * 0.5})`;
};
```

---

### Workflow C: Harmonization View (Cross-Matched Stars)

**Goal**: Visualize stars from different catalogs that are the **same physical object**.

#### Understanding `fusion_group_id` — **CRITICAL CONCEPT**

After running cross-match (`POST /harmonize/cross-match`), stars that represent the same physical object will share a `fusion_group_id` (UUID).

**In Your Pleiades Dataset:**
- **Total Stars**: 1,000 (500 from Gaia DR3, 500 from NASA TESS)
- **Fusion Groups Created**: 459
- **What This Means**: 459 stars were observed by BOTH space agencies!

```
Real Example from Your Database:
┌─────────────────────────────────────────────────────────────┐
│  fusion_group_id: "7f3a8c21-..."                            │
│  ├── ID 42  (Gaia DR3)    RA: 56.751°  Dec: 24.102°        │
│  └── ID 587 (NASA TESS)   RA: 56.752°  Dec: 24.101°        │
│       ↑ Alcyone (brightest Pleiades star) seen by both!     │
└─────────────────────────────────────────────────────────────┘
```

**Visualization Idea**: Toggle between "Gaia View" (high-precision positions) and "TESS View" (photometric time-series data). Stars with `fusion_group_id` are the same physical object in both views.

#### Step 1: Fetch Cross-Match Stats

```typescript
// GET /harmonize/stats
const fetchHarmonizationStats = async () => {
  const response = await api.get('/harmonize/stats');
  return response.data;
  // Expected for Pleiades Dataset:
  // {
  //   total_stars: 1000,
  //   stars_in_fusion_groups: 918,  // (459 groups × 2 observations each)
  //   isolated_stars: 82,            // Only observed by one mission
  //   unique_fusion_groups: 459
  // }
};

// 🎯 KEY INSIGHT: 91.8% cross-match rate shows excellent positional agreement
// between Gaia (ESA) and TESS (NASA) for the same stars!
```

#### Step 2: Query Stars and Group by `fusion_group_id`

```typescript
// Group stars by their fusion_group_id
const groupByFusion = (stars: Star[]) => {
  const groups: Record<string, Star[]> = {};
  
  stars.forEach(star => {
    if (star.fusion_group_id) {
      if (!groups[star.fusion_group_id]) {
        groups[star.fusion_group_id] = [];
      }
      groups[star.fusion_group_id].push(star);
    }
  });
  
  return groups;
};
```

#### Step 3: Draw Lines Connecting Cross-Matched Stars

```tsx
const CrossMatchOverlay = ({ stars }: { stars: Star[] }) => {
  const fusionGroups = groupByFusion(stars);
  
  // Create line traces for each fusion group
  const lineTraces = Object.values(fusionGroups)
    .filter(group => group.length > 1)
    .map((group, i) => ({
      type: 'scatter',
      mode: 'lines+markers',
      name: `Fusion Group ${i + 1}`,
      x: group.map(s => 360 - s.ra_deg),
      y: group.map(s => s.dec_deg),
      line: { color: '#FFD93D', width: 2, dash: 'dot' },
      marker: { size: 10, symbol: 'diamond' },
    }));
  
  return (
    <Plot
      data={lineTraces}
      layout={{
        title: 'Cross-Matched Observations',
        annotations: [{
          text: '⚡ Connected stars = Same physical object from different surveys',
          showarrow: false,
          x: 0.5, y: 1.1, xref: 'paper', yref: 'paper',
        }],
      }}
    />
  );
};
```

#### Alternative: Merged View

Instead of drawing lines, you could **merge** cross-matched stars into a single point:

```typescript
const mergeStars = (group: Star[]) => {
  // Average the positions
  const avgRa = group.reduce((sum, s) => sum + s.ra_deg, 0) / group.length;
  const avgDec = group.reduce((sum, s) => sum + s.dec_deg, 0) / group.length;
  
  // Take the brightest magnitude
  const bestMag = Math.min(...group.map(s => s.brightness_mag));
  
  return {
    ra_deg: avgRa,
    dec_deg: avgDec,
    brightness_mag: bestMag,
    sources: group.map(s => s.original_source),
    sourceCount: group.length,
  };
};
```

---

### Workflow D: Data Export

**Goal**: Allow users to download filtered data.

#### Export Formats

| Format | Endpoint | Use Case |
|--------|----------|----------|
| CSV | `/query/export?format=csv` | Excel, spreadsheets |
| JSON | `/query/export?format=json` | JavaScript processing |
| VOTable | `/query/export?format=votable` | Professional astronomy tools (TOPCAT, Aladin) |

#### Implementation

```typescript
const downloadExport = async (format: 'csv' | 'json' | 'votable') => {
  const response = await api.get(`/query/export`, {
    params: { format },
    responseType: 'blob',
  });
  
  // Create download link
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `cosmic_export.${format === 'votable' ? 'vot' : format}`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};
```

---

## 📖 Data Dictionary

### Star Object Fields

| Field | Type | Unit | Range | Description |
|-------|------|------|-------|-------------|
| `id` | integer | — | — | Database primary key |
| `source_id` | string | — | — | Original catalog identifier (e.g., `"Gaia DR3 12345"`) |
| `ra_deg` | float | degrees | **0 to 360** | Right Ascension (celestial longitude) |
| `dec_deg` | float | degrees | **-90 to +90** | Declination (celestial latitude) |
| `brightness_mag` | float | magnitude | ~-2 to 25 | Apparent brightness. **Lower = Brighter!** |
| `parallax_mas` | float \| null | milliarcseconds | 0 to ~100 | Parallax angle. **Higher = Closer!** |
| `distance_pc` | float \| null | parsecs | — | Distance (if calculated from parallax) |
| `original_source` | string | — | — | Source catalog name (`"Gaia DR3"`, `"TESS"`) |
| `fusion_group_id` | string \| null | UUID | — | **CRITICAL**: Links same star from different missions |

**Note on `fusion_group_id`**: In your Pleiades dataset, 459 stars have this field populated, meaning they appear in BOTH Gaia and TESS datasets. Use this for "Toggle Data Source" features.

### Understanding Coordinates

```
                     North Celestial Pole
                           Dec = +90°
                              │
                              │
    RA = 180° ────────────────┼──────────────── RA = 0° / 360°
    (12 hours)                │                 (0 hours)
                              │
                              │
                     South Celestial Pole
                           Dec = -90°
```

- **RA (Right Ascension)**: Like longitude on Earth, but measured in degrees (0-360) or hours (0-24)
- **Dec (Declination)**: Like latitude on Earth (-90° South pole to +90° North pole)
- **Convention**: Astronomers often display RA reversed (360° on left, 0° on right) because that's how the sky appears when looking up

### Understanding Magnitude

```
Magnitude Scale (logarithmic):

   Brighter ←───────────────────────────────────────→ Fainter
   
   -2     0      2      4      6      8     10    ...    25
    │     │      │      │      │      │      │            │
  Sirius Sun  Polaris Naked  Naked  Binoc- Small      Hubble
  (star) (!)   (star)  Eye    Eye   ulars  Scope      Limit
                      (city) (dark)
                      
  🌟 PLEIADES STARS IN YOUR DATA:
     - Seven Sisters (brightest): mag 2-5
     - Cluster members: mag 6-10
     - Faint members: mag 11-13
```

- **Each magnitude = 2.5x brightness difference**
- Magnitude 1 star is ~2.5x brighter than magnitude 2
- Magnitude 1 star is ~100x brighter than magnitude 6

### Understanding Parallax

```
Parallax = apparent shift due to Earth's orbit

High parallax (e.g., 100 mas) = CLOSE star (~10 parsecs)
Low parallax (e.g., 1 mas) = FAR star (~1000 parsecs)

Distance (parsecs) = 1000 / parallax (mas)

🎯 PLEIADES CLUSTER:
   - Average parallax: ~7.5 mas
   - Distance: ~133 parsecs (434 light-years)
   - Stars with very different parallax are likely foreground/background!
```

---

## 📦 Response Schemas

### Query Search Response

```typescript
// POST /query/search
interface QuerySearchResponse {
  success: boolean;
  message: string;
  total_count: number;    // Total matching stars (before pagination)
  returned_count: number; // Stars in this response
  limit: number;
  offset: number;
  records: Star[];        // ⬅️ THE STAR DATA IS HERE
}
```

### Anomaly Detection Response

```typescript
// POST /ai/anomalies
interface AnomalyResponse {
  success: boolean;
  message: string;
  total_stars_analyzed: number;
  anomaly_count: number;
  contamination_used: number;
  anomalies: Array<{
    id: number;
    source_id: string;
    original_source: string;
    ra_deg: number;
    dec_deg: number;
    brightness_mag: number;
    parallax_mas: number;
    anomaly_score: number;  // Negative = anomalous
  }>;
}
```

### Clustering Response

```typescript
// POST /ai/clusters
interface ClusterResponse {
  success: boolean;
  message: string;
  n_clusters: number;
  n_noise: number;         // Stars not in any cluster
  total_stars: number;
  parameters: { eps: number; min_samples: number };
  clusters: Record<string, number[]>;  // cluster_id -> array of star IDs
  cluster_stats: Record<string, {
    count: number;
    mean_ra: number;
    mean_dec: number;
    mean_magnitude: number;
    mean_parallax: number;
    ra_range: [number, number];
    dec_range: [number, number];
    mag_range: [number, number];
  }>;
}
```

---

## ⚠️ Error Handling

```typescript
// All API errors return this structure
interface APIError {
  detail: string;
}

// Axios error handling
try {
  const response = await api.post('/ai/anomalies', { contamination: 0.05 });
} catch (error) {
  if (axios.isAxiosError(error)) {
    const message = error.response?.data?.detail || 'Unknown error';
    console.error(`API Error: ${message}`);
  }
}
```

### Common HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Check request parameters |
| 404 | Not Found | Resource doesn't exist |
| 422 | Validation Error | Request body invalid |
| 500 | Server Error | Report to backend team |

---

## 🏗️ Example Component Architecture

```
src/
├── components/
│   ├── SkyMap/
│   │   ├── SkyMap.tsx           # Main Plotly scatter plot
│   │   ├── AnomalyOverlay.tsx   # Red anomaly markers
│   │   ├── ClusterOverlay.tsx   # Colored cluster regions
│   │   └── CrossMatchLines.tsx  # Fusion group connections
│   ├── Sidebar/
│   │   ├── FilterPanel.tsx      # RA/Dec/Mag sliders
│   │   ├── DataSourceToggle.tsx # Gaia/SDSS checkboxes
│   │   └── ExportButton.tsx     # Download dropdown
│   ├── StatsPanel/
│   │   ├── CatalogStats.tsx     # Total stars, sources
│   │   └── AIInsights.tsx       # Anomaly/cluster counts
│   └── Layout/
│       ├── Header.tsx
│       └── Dashboard.tsx        # Main layout grid
├── hooks/
│   ├── useStars.ts              # React Query for /query/search
│   ├── useAnomalies.ts          # React Query for /ai/anomalies
│   └── useClusters.ts           # React Query for /ai/clusters
├── lib/
│   ├── api.ts                   # Axios instance
│   └── coordinates.ts           # RA/Dec transformation utils
└── types/
    └── index.ts                 # TypeScript interfaces
```

---

## 🚀 Quick Start Checklist

- [ ] Set up Next.js project with TypeScript
- [ ] Configure API base URL in `.env.local`
- [ ] Install Plotly.js or integrate Aladin Lite
- [ ] Create `useStars` hook with React Query
- [ ] Build basic SkyMap component with RA/Dec scatter
  - **Expected**: Tight cluster of points centered at RA 56.75°, Dec 24.1°
- [ ] Add anomaly overlay with red markers
  - **Expected**: ~50 red stars scattered across the field
- [ ] Implement filter panel (magnitude, RA/Dec range)
  - **Try filtering**: mag 2-5 to isolate the Seven Sisters
- [ ] Add "Toggle Data Source" button (Gaia vs TESS views)
  - **Use**: `fusion_group_id` to show cross-matched stars in both
- [ ] Add export button with format dropdown
- [ ] Style with dark theme (space aesthetic!)

---

## 🎯 Visual Expectations

When you first load the sky map, you should see:

1. **Dense Cluster**: Most stars concentrated in a ~1° radius around RA 56.75°, Dec 24.1°
2. **Bright Outliers**: A handful of very bright stars (mag 2-5) — these are the famous Seven Sisters
3. **Color Coding**: If you color by magnitude, you'll see a gradient from bright (blue/white) to faint (red/orange)
4. **Anomaly Scatter**: Red markers distributed throughout the field (foreground/background objects)
5. **Cross-Match Pairs**: If viewing fusion groups, yellow lines connecting Gaia↔TESS pairs

**Pro Tip**: Set initial zoom to RA 54-60°, Dec 22-26° to frame the Pleiades perfectly!

---

## 🤝 Need Help?

- **API Docs**: http://localhost:8000/docs
- **Backend Team Contact**: [Your Team Channel]
- **Example Requests**: Use the Swagger UI to test endpoints interactively
- **Test Data**: All 1,000 stars are REAL science data from ESA Gaia DR3 and NASA TESS

---

<p align="center">
  <b>Good luck, Frontend Team! 🚀🌟</b><br>
  <i>You're visualizing real observations of the Pleiades Cluster (M45).</i><br>
  <i>Let's make 459 fusion groups shine!</i>
</p>
