# 🚀 CDS Full Integration - Detailed Implementation Plan

## Project Overview
**Goal:** Integrate SIMBAD, VizieR, X-Match, and Aladin Lite into COSMIC Data Fusion  
**Timeline:** 2-3 days  
**Status:** Ready to start  

---

## 📋 Prerequisites & Setup

### Task 0.1: Install Python Dependencies
**File:** `requirements.txt`
- [ ] Add `astroquery>=0.4.6`
- [ ] Add `astropy>=5.0`
- [ ] Add `pandas>=2.0.0` (if not already present)
- [ ] Run `pip install -r requirements.txt`

**Commands:**
```bash
cd c:\Users\lokes\OneDrive\Documents\GitHub\cosmic-data-fusion
.venv\Scripts\Activate.ps1
pip install astroquery astropy
pip freeze > requirements.txt
```

### Task 0.2: Test Astroquery Connection
**File:** `test_cds_connection.py` (temporary test file)
- [ ] Create test script to verify CDS API access
- [ ] Test SIMBAD query
- [ ] Test VizieR query
- [ ] Delete test file after verification

**Verification Script:**
```python
from astroquery.simbad import Simbad
from astroquery.vizier import Vizier

# Test SIMBAD
result = Simbad.query_object("M31")
print(f"SIMBAD test: {'✓ Success' if result else '✗ Failed'}")

# Test VizieR
result = Vizier.query_object("M31", radius='5m')
print(f"VizieR test: {'✓ Success' if result else '✗ Failed'}")
```

---

## 🏗️ Phase 1: Backend Services Layer (Day 1, Morning)

### Task 1.1: Create External Services Directory Structure
- [ ] Create `app/services/external/` directory
- [ ] Create `app/services/external/__init__.py`
- [ ] Create `app/services/external/simbad_service.py`
- [ ] Create `app/services/external/vizier_service.py`
- [ ] Create `app/services/external/xmatch_service.py`

**Files to create:**
```
app/services/external/
├── __init__.py
├── simbad_service.py
├── vizier_service.py
└── xmatch_service.py
```

### Task 1.2: Implement SIMBAD Service
**File:** `app/services/external/simbad_service.py`

- [ ] Import required libraries (astroquery, astropy)
- [ ] Create `SimbadService` class
- [ ] Implement `query_by_coordinates(ra_deg, dec_deg, radius_arcmin)` method
- [ ] Implement `query_by_name(object_name)` method
- [ ] Implement `get_object_info(object_id)` method
- [ ] Add error handling for connection issues
- [ ] Add logging for queries
- [ ] Configure SIMBAD fields (otype, sp, flux, identifiers)

**Key Methods:**
```python
class SimbadService:
    def query_by_coordinates(self, ra_deg, dec_deg, radius_arcmin=2.0)
    def query_by_name(self, object_name)
    def get_object_info(self, object_id)
    def _parse_result(self, result)  # Helper method
```

### Task 1.3: Implement VizieR Service
**File:** `app/services/external/vizier_service.py`

- [ ] Import required libraries
- [ ] Create `VizieRService` class
- [ ] Implement `query_gaia_dr3(ra_deg, dec_deg, radius_arcmin)` method
- [ ] Implement `query_2mass(ra_deg, dec_deg, radius_arcmin)` method
- [ ] Implement `query_sdss(ra_deg, dec_deg, radius_arcmin)` method
- [ ] Implement `query_catalog(catalog_id, ra_deg, dec_deg, radius_arcmin)` method
- [ ] Implement `list_available_catalogs()` method
- [ ] Add row limit configuration (default 50, max 500)
- [ ] Add error handling

**Catalog IDs to support:**
- Gaia DR3: `I/355/gaiadr3`
- 2MASS: `II/246/out`
- SDSS DR17: `V/154/sdss17`
- TESS: `IV/39/tic82`

### Task 1.4: Implement X-Match Service
**File:** `app/services/external/xmatch_service.py`

- [ ] Import required libraries
- [ ] Create `XMatchService` class
- [ ] Implement `cross_match_with_gaia(df, max_distance_arcsec)` method
- [ ] Implement `cross_match_with_catalog(df, catalog_id, max_distance_arcsec)` method
- [ ] Implement `get_match_statistics(result)` helper method
- [ ] Add pandas DataFrame validation
- [ ] Add error handling for large files (>100MB warning)
- [ ] Add timeout handling

**Key Methods:**
```python
class XMatchService:
    def cross_match_with_gaia(self, df, max_distance_arcsec=5.0)
    def cross_match_with_catalog(self, df, catalog_id, max_distance_arcsec)
    def _validate_input_table(self, df)
    def _parse_match_result(self, result)
```

### Task 1.5: Create Service Tests
**File:** `tests/test_external_services.py`

- [ ] Test SIMBAD queries with known objects
- [ ] Test VizieR queries with sample coordinates
- [ ] Test X-Match with small dataset
- [ ] Test error handling (invalid coordinates, timeout)
- [ ] Test rate limiting

---

## 🔌 Phase 2: API Endpoints (Day 1, Afternoon)

### Task 2.1: Create External Catalogs Router
**File:** `app/api/external_catalogs.py`

- [ ] Create new APIRouter with prefix `/external`
- [ ] Add tags `["External Catalogs"]`
- [ ] Import service classes
- [ ] Add common response models
- [ ] Add error handling middleware

**Structure:**
```python
router = APIRouter(prefix="/external", tags=["External Catalogs"])

# Endpoints to create:
# - /external/simbad/lookup
# - /external/simbad/object/{name}
# - /external/vizier/gaia-dr3
# - /external/vizier/catalog
# - /external/xmatch/gaia
# - /external/xmatch/catalog
# - /external/catalogs/list
```

### Task 2.2: Implement SIMBAD Endpoints
**File:** `app/api/external_catalogs.py`

- [ ] **Endpoint:** `GET /external/simbad/lookup`
  - [ ] Parameters: `ra`, `dec`, `radius` (optional, default 2.0)
  - [ ] Call `SimbadService.query_by_coordinates()`
  - [ ] Format response with attribution
  - [ ] Add error handling

- [ ] **Endpoint:** `GET /external/simbad/object/{name}`
  - [ ] Parameter: `name` (path parameter)
  - [ ] Call `SimbadService.query_by_name()`
  - [ ] Format response
  - [ ] Handle "object not found" gracefully

**Response Format:**
```json
{
  "success": true,
  "found": true,
  "count": 2,
  "matches": [...],
  "attribution": "SIMBAD Astronomical Database (CDS, Strasbourg)",
  "citation": "Wenger et al., A&AS 143, 9 (2000)"
}
```

### Task 2.3: Implement VizieR Endpoints
**File:** `app/api/external_catalogs.py`

- [ ] **Endpoint:** `GET /external/vizier/gaia-dr3`
  - [ ] Parameters: `ra`, `dec`, `radius` (optional, default 5.0)
  - [ ] Call `VizieRService.query_gaia_dr3()`
  - [ ] Parse parallax, proper motion, magnitudes
  - [ ] Add Gaia attribution

- [ ] **Endpoint:** `GET /external/vizier/2mass`
  - [ ] Parameters: `ra`, `dec`, `radius`
  - [ ] Query 2MASS catalog
  - [ ] Add 2MASS attribution

- [ ] **Endpoint:** `GET /external/vizier/catalog`
  - [ ] Parameters: `catalog_id`, `ra`, `dec`, `radius`
  - [ ] Query any VizieR catalog
  - [ ] Generic attribution

- [ ] **Endpoint:** `GET /external/catalogs/list`
  - [ ] Return list of supported catalogs
  - [ ] Include descriptions and IDs

### Task 2.4: Implement X-Match Endpoints
**File:** `app/api/external_catalogs.py`

- [ ] **Endpoint:** `POST /external/xmatch/gaia`
  - [ ] Body: `{ "stars": [{"ra_deg": ..., "dec_deg": ...}], "max_distance_arcsec": 5.0 }`
  - [ ] Call `XMatchService.cross_match_with_gaia()`
  - [ ] Return match statistics
  - [ ] Return matched data

- [ ] **Endpoint:** `POST /external/xmatch/catalog`
  - [ ] Body: `{ "stars": [...], "catalog_id": "...", "max_distance_arcsec": 5.0 }`
  - [ ] Call `XMatchService.cross_match_with_catalog()`
  - [ ] Support multiple catalogs

- [ ] Add rate limiting (max 10 requests/minute per user)
- [ ] Add request size validation (max 1000 stars per request)

### Task 2.5: Register Router in Main App
**File:** `app/main.py`

- [ ] Import `external_catalogs` router
- [ ] Add `app.include_router(external_catalogs.router)`
- [ ] Test endpoints appear in `/docs`

---

## 🎨 Phase 3: Frontend Components (Day 2, Morning)

### Task 3.1: Create External Catalog Components Directory
- [ ] Create `frontend/src/components/external/` directory
- [ ] Create component files:
  - `ExternalCatalogMatch.jsx`
  - `ExternalCatalogMatch.css`
  - `CrossMatchPanel.jsx`
  - `CrossMatchPanel.css`
  - `AladinViewer.jsx`
  - `AladinViewer.css`

### Task 3.2: Implement ExternalCatalogMatch Component
**File:** `frontend/src/components/external/ExternalCatalogMatch.jsx`

- [ ] Create functional component accepting `ra`, `dec` props
- [ ] Add state for `simbadData`, `gaiaData`, `loading`, `error`
- [ ] Implement `fetchExternalData()` function
  - [ ] Call `/external/simbad/lookup`
  - [ ] Call `/external/vizier/gaia-dr3`
  - [ ] Handle errors gracefully
- [ ] Create UI sections:
  - [ ] Search button
  - [ ] Loading spinner
  - [ ] SIMBAD results card
  - [ ] Gaia DR3 results card
  - [ ] Attribution badges
- [ ] Add expand/collapse functionality
- [ ] Style with dark theme

**Component Structure:**
```jsx
function ExternalCatalogMatch({ ra, dec }) {
  const [loading, setLoading] = useState(false);
  const [simbadData, setSimbadData] = useState(null);
  const [gaiaData, setGaiaData] = useState(null);
  
  const fetchExternalData = async () => { ... }
  
  return (
    <div className="external-catalog-match">
      {/* Search button */}
      {/* Results cards */}
      {/* Attribution */}
    </div>
  );
}
```

### Task 3.3: Implement CrossMatchPanel Component
**File:** `frontend/src/components/external/CrossMatchPanel.jsx`

- [ ] Create component accepting `stars` array prop
- [ ] Add state for `results`, `loading`, `selectedCatalog`
- [ ] Implement `runCrossMatch()` function
  - [ ] Prepare star data
  - [ ] Call `/external/xmatch/gaia` (or selected catalog)
  - [ ] Parse results
- [ ] Create UI:
  - [ ] Catalog selector dropdown (Gaia, 2MASS, SDSS)
  - [ ] Match distance slider (1-10 arcsec)
  - [ ] "Run Cross-Match" button
  - [ ] Statistics display (input count, matches, rate)
  - [ ] Results table or download button
  - [ ] Attribution badge
- [ ] Add progress indicator for large batches
- [ ] Handle empty results

### Task 3.4: Implement AladinViewer Component
**File:** `frontend/src/components/external/AladinViewer.jsx`

- [ ] Create component accepting `ra`, `dec`, `fov`, `userStars` props
- [ ] Add script loader for Aladin Lite CDN
  - [ ] URL: `https://aladin.cds.unistra.fr/AladinLite/api/v3/latest/aladin.js`
  - [ ] Load dynamically on mount
- [ ] Initialize Aladin instance
  - [ ] Set survey (DSS2, PanSTARRS, or user choice)
  - [ ] Set target coordinates
  - [ ] Set field of view
- [ ] Add user stars as catalog overlay
  - [ ] Green markers for user data
  - [ ] Show name/magnitude on hover
- [ ] Add controls:
  - [ ] Survey selector
  - [ ] FOV slider
  - [ ] Layer toggles (Gaia, 2MASS)
  - [ ] Fullscreen button
- [ ] Add attribution banner
- [ ] Handle cleanup on unmount

**Aladin Setup:**
```javascript
useEffect(() => {
  const script = document.createElement('script');
  script.src = 'https://aladin.cds.unistra.fr/AladinLite/api/v3/latest/aladin.js';
  script.onload = () => {
    const A = window.A;
    const aladin = A.aladin(containerRef.current, {
      survey: 'P/DSS2/color',
      fov: fov,
      target: `${ra} ${dec}`
    });
    // Add overlays
  };
  document.body.appendChild(script);
}, [ra, dec, fov]);
```

### Task 3.5: Style Components
**Files:** `*.css`

- [ ] Dark theme consistent with existing dashboard
- [ ] Card-based layout for results
- [ ] Loading skeletons
- [ ] Attribution badges (small, subtle, bottom-right)
- [ ] Responsive design
- [ ] Hover effects
- [ ] Error states styling

**CSS Variables to use:**
```css
--background-dark: rgba(30, 41, 59, 0.5);
--border-color: rgba(148, 163, 184, 0.1);
--text-primary: #e2e8f0;
--text-secondary: #94a3b8;
--accent-blue: #3b82f6;
```

---

## 🔗 Phase 4: Dashboard Integration (Day 2, Afternoon)

### Task 4.1: Add External Catalog Tab to Dashboard
**File:** `frontend/src/pages/Dashboard.jsx`

- [ ] Import `ExternalCatalogMatch` component
- [ ] Import `CrossMatchPanel` component
- [ ] Import `AladinViewer` component
- [ ] Add "External Catalogs" to navigation menu
  - [ ] Icon: `Database` or `Globe`
  - [ ] Label: "Catalog Lookup"
- [ ] Create tab content section:
  - [ ] Brief explanation of feature
  - [ ] Coordinate input form (reuse coordinate parser)
  - [ ] `ExternalCatalogMatch` component
  - [ ] `AladinViewer` component
- [ ] Add "Enrich Data" button to existing star results
  - [ ] When clicked, opens modal with external catalog match
  - [ ] Passes current star's RA/Dec

### Task 4.2: Integrate into Star Detail View
**File:** Component showing individual star details

- [ ] Add "🔍 Lookup in External Catalogs" button
- [ ] On click, show `ExternalCatalogMatch` component in expandable section
- [ ] Pre-fill with star's coordinates
- [ ] Auto-fetch on expand (optional)

### Task 4.3: Add Bulk Enrichment Feature
**File:** `frontend/src/pages/Dashboard.jsx`

- [ ] Add "Bulk Enrich" button to results table header
- [ ] When clicked, open `CrossMatchPanel` modal
- [ ] Pass all visible stars to cross-match
- [ ] Show progress (e.g., "Matching 245 stars with Gaia DR3...")
- [ ] After completion, offer to:
  - [ ] Download enriched CSV
  - [ ] Replace current view with enriched data
  - [ ] View match statistics

### Task 4.4: Add Aladin Sky Map Tab
**File:** `frontend/src/pages/Dashboard.jsx`

- [ ] Add "Sky Map" navigation item (already exists? Check and enhance)
- [ ] If new: Create full-screen Aladin viewer
- [ ] Overlay all user stars from current filters
- [ ] Add layer controls:
  - [ ] Toggle Gaia overlay
  - [ ] Toggle 2MASS overlay
  - [ ] Toggle user stars
- [ ] Click on star to show details

---

## 📚 Phase 5: Documentation & Attribution (Day 3, Morning)

### Task 5.1: Update README.md
**File:** `README.md`

- [ ] Add "External Catalog Integration" section
- [ ] List supported catalogs:
  - [ ] SIMBAD (20M+ objects)
  - [ ] Gaia DR3 (ESA mission, 1.8B sources)
  - [ ] 2MASS (470M sources)
  - [ ] SDSS (1B+ objects)
- [ ] Add "Data Sources & Acknowledgments" section
- [ ] Include all required citations:
  - [ ] SIMBAD citation
  - [ ] VizieR citation
  - [ ] Gaia DR3 citation
  - [ ] CDS X-Match citation
  - [ ] Aladin Lite citation
- [ ] Add usage examples with screenshots
- [ ] Update architecture diagram to show CDS integration

**Required Citations:**
```markdown
## Data Sources & Acknowledgments

### External Catalog Services (CDS, Strasbourg)

- **SIMBAD Database** - "The SIMBAD astronomical database"
  Wenger et al., A&AS 143, 9 (2000)
  
- **VizieR Catalog Service** - "The VizieR database of astronomical catalogues"
  Ochsenbein et al., A&AS 143, 23 (2000)
  
- **CDS X-Match Service** - Cross-identification of astronomical sources
  
- **Aladin Lite** - Interactive sky visualization
  Bonnarel et al., A&AS 143, 33 (2000)

### Astronomical Data

- **Gaia DR3** - ESA mission
  Gaia Collaboration, A&A 649, A1 (2021)
  
- **2MASS** - Two Micron All Sky Survey
  Skrutskie et al., AJ 131, 1163 (2006)
  
- **SDSS** - Sloan Digital Sky Survey
  https://www.sdss.org/
```

### Task 5.2: Add Attribution to UI
**Files:** Multiple component files

- [ ] Add footer to dashboard with CDS logo/link
- [ ] Add "About External Data" modal explaining sources
- [ ] Add info tooltips next to "Lookup" buttons
  - [ ] "Data from SIMBAD (CDS, Strasbourg)"
  - [ ] "Cross-matched with Gaia DR3 via CDS X-Match"
- [ ] Add attribution badge to all external data displays
  - [ ] Small icon + "Source: SIMBAD"
  - [ ] Click to show full citation

### Task 5.3: Create User Documentation
**File:** `documentation/EXTERNAL_CATALOGS.md`

- [ ] Introduction to external catalog features
- [ ] How to use SIMBAD lookup
- [ ] How to use cross-match feature
- [ ] How to interpret results
- [ ] Limitations (rate limits, data availability)
- [ ] Troubleshooting common issues
- [ ] API endpoint documentation

### Task 5.4: Create API Documentation
**File:** Update OpenAPI/Swagger docs

- [ ] Document all `/external/*` endpoints
- [ ] Add example requests/responses
- [ ] Document error codes
- [ ] Add rate limit information
- [ ] Link to CDS documentation for details

---

## ✅ Phase 6: Testing & Validation (Day 3, Afternoon)

### Task 6.1: Backend Testing

- [ ] **Test SIMBAD Service:**
  - [ ] Query known object (M31, HD 209458)
  - [ ] Query coordinates with no match
  - [ ] Query coordinates with multiple matches
  - [ ] Test invalid coordinates
  - [ ] Test timeout handling

- [ ] **Test VizieR Service:**
  - [ ] Query Gaia DR3 in populated region
  - [ ] Query Gaia DR3 in empty region
  - [ ] Query 2MASS catalog
  - [ ] Query SDSS catalog
  - [ ] Test invalid catalog ID

- [ ] **Test X-Match Service:**
  - [ ] Cross-match 10 stars with Gaia
  - [ ] Cross-match 100 stars (larger batch)
  - [ ] Test with 100% match rate (known stars)
  - [ ] Test with 0% match rate (invalid coordinates)
  - [ ] Test timeout with large dataset

### Task 6.2: API Endpoint Testing

- [ ] Test all endpoints in Swagger UI (`/docs`)
- [ ] Verify response formats match schema
- [ ] Test error responses (400, 404, 500)
- [ ] Test rate limiting
- [ ] Verify attribution strings present in all responses

### Task 6.3: Frontend Testing

- [ ] **ExternalCatalogMatch Component:**
  - [ ] Click "Search" button
  - [ ] Verify loading state
  - [ ] Verify SIMBAD results display
  - [ ] Verify Gaia results display
  - [ ] Verify "No results" state
  - [ ] Verify error handling

- [ ] **CrossMatchPanel Component:**
  - [ ] Select different catalogs
  - [ ] Adjust match distance
  - [ ] Run cross-match with sample data
  - [ ] Verify statistics display
  - [ ] Download matched catalog (CSV)

- [ ] **AladinViewer Component:**
  - [ ] Verify sky map loads
  - [ ] Verify user stars appear as overlay
  - [ ] Test survey selector
  - [ ] Test FOV adjustment
  - [ ] Test fullscreen mode
  - [ ] Verify attribution visible

### Task 6.4: Integration Testing

- [ ] **End-to-End Flow 1: Upload → Enrich → Export**
  - [ ] Upload CSV with coordinates
  - [ ] View in dashboard
  - [ ] Click "Lookup in SIMBAD"
  - [ ] See matched object
  - [ ] Run cross-match with Gaia
  - [ ] Download enriched data
  - [ ] Verify CSV contains both user + external data

- [ ] **End-to-End Flow 2: Search → Visualize → Explore**
  - [ ] Search stars in region
  - [ ] View on Aladin sky map
  - [ ] Click star to see details
  - [ ] Lookup in external catalogs
  - [ ] View additional properties

- [ ] **End-to-End Flow 3: Coordinate Finder → External Lookup**
  - [ ] Use coordinate finder (already implemented)
  - [ ] Find stars in our database
  - [ ] Lookup same coordinates in SIMBAD
  - [ ] Compare results

### Task 6.5: Performance Testing

- [ ] Test SIMBAD query response time (should be < 2 sec)
- [ ] Test VizieR query response time (should be < 3 sec)
- [ ] Test X-Match with 100 stars (should be < 10 sec)
- [ ] Test X-Match with 500 stars (should be < 30 sec)
- [ ] Test Aladin Lite initialization (should be < 3 sec)
- [ ] Monitor memory usage with multiple queries
- [ ] Test concurrent requests (5 users simultaneously)

### Task 6.6: Error Handling Testing

- [ ] Test with CDS service down (mock/simulate)
- [ ] Test with slow network (throttle connection)
- [ ] Test with invalid API responses
- [ ] Test with malformed user input
- [ ] Verify user-friendly error messages display
- [ ] Verify errors logged properly in backend

---

## 🎬 Phase 7: Demo Preparation (Day 3, Evening)

### Task 7.1: Create Demo Dataset

- [ ] Prepare sample CSV with interesting objects:
  - [ ] Known stars (Vega, Sirius, Betelgeuse)
  - [ ] Known exoplanet hosts (HD 209458, Kepler-10)
  - [ ] Mix of bright and faint stars
  - [ ] Mix of objects with/without SIMBAD matches
- [ ] Upload to dashboard
- [ ] Save demo state

### Task 7.2: Create Demo Script
**File:** `DEMO_SCRIPT.md`

- [ ] Write step-by-step demo walkthrough
- [ ] Include talking points for each feature
- [ ] Add screenshots/GIFs
- [ ] Highlight competitive advantages
- [ ] Prepare answers to expected questions:
  - [ ] "Is this your data?"
  - [ ] "How does this differ from just using SIMBAD?"
  - [ ] "What's your unique value?"

**Demo Flow:**
```markdown
1. Introduction (30 sec)
   "COSMIC Data Fusion connects your data with professional catalogs..."

2. Data Upload (30 sec)
   Upload demo CSV → Show harmonization

3. SIMBAD Lookup (45 sec)
   Click star → "Lookup in SIMBAD" → Show HD 209458 match

4. Gaia Enrichment (45 sec)
   Show parallax, proper motion from Gaia DR3

5. Cross-Match (60 sec)
   "Bulk Enrich" → Match 50 stars → 95% match rate!

6. Sky Visualization (45 sec)
   Aladin sky map → Interactive exploration

7. Conclusion (30 sec)
   "Unified platform: Your data + AI + Professional catalogs"
```

### Task 7.3: Record Demo Video (Optional)

- [ ] Record 3-5 minute demo video
- [ ] Show all key features
- [ ] Add captions/annotations
- [ ] Export in HD format
- [ ] Upload to YouTube (unlisted)
- [ ] Add link to README

### Task 7.4: Prepare Presentation Slides

- [ ] Slide 1: Title + Team
- [ ] Slide 2: Problem statement
- [ ] Slide 3: Solution overview
- [ ] Slide 4: Architecture diagram (with CDS integration)
- [ ] Slide 5: Key features list
- [ ] Slide 6: External catalog integration (NEW!)
- [ ] Slide 7: Demo screenshots
- [ ] Slide 8: Technology stack
- [ ] Slide 9: Future roadmap
- [ ] Slide 10: Thank you + links

---

## 🐛 Phase 8: Bug Fixes & Polish (Ongoing)

### Task 8.1: Code Review Checklist

- [ ] Remove console.log statements
- [ ] Remove commented-out code
- [ ] Add JSDoc comments to all functions
- [ ] Add Python docstrings to all methods
- [ ] Format code (Black for Python, Prettier for JS)
- [ ] Check for hardcoded values (move to config)
- [ ] Verify environment variables used properly
- [ ] Remove unused imports

### Task 8.2: Security Review

- [ ] Verify no API keys exposed in frontend
- [ ] Check rate limiting works
- [ ] Validate all user inputs
- [ ] Sanitize external data before display
- [ ] Add CORS headers properly
- [ ] Check SQL injection prevention
- [ ] Verify authentication on sensitive endpoints

### Task 8.3: Performance Optimization

- [ ] Add caching for SIMBAD queries (1 hour TTL)
- [ ] Add caching for VizieR queries (30 min TTL)
- [ ] Implement request debouncing in frontend
- [ ] Lazy load Aladin Lite script
- [ ] Optimize star overlay rendering
- [ ] Add pagination to large result sets
- [ ] Monitor backend memory usage

### Task 8.4: Accessibility

- [ ] Add ARIA labels to interactive elements
- [ ] Ensure keyboard navigation works
- [ ] Test with screen reader
- [ ] Add alt text to attribution badges
- [ ] Verify color contrast ratios
- [ ] Add loading announcements

---

## 📊 Verification Checklist

### Functional Requirements
- [ ] User can lookup coordinates in SIMBAD
- [ ] User can query Gaia DR3 via VizieR
- [ ] User can cross-match stars with catalogs
- [ ] User can visualize stars on Aladin sky map
- [ ] Attribution is displayed on all external data
- [ ] Error messages are user-friendly
- [ ] All features work together seamlessly

### Technical Requirements
- [ ] Backend API endpoints return JSON
- [ ] Frontend handles loading states
- [ ] Frontend handles error states
- [ ] Rate limiting prevents abuse
- [ ] Logging captures queries
- [ ] Cache reduces redundant queries
- [ ] Code follows project conventions

### Documentation Requirements
- [ ] README includes external catalogs section
- [ ] API docs updated with new endpoints
- [ ] User guide explains features
- [ ] Citations included properly
- [ ] Code comments explain logic
- [ ] Demo script ready

### Ethical Requirements
- [ ] Attribution visible in UI
- [ ] Citations in documentation
- [ ] Clear distinction: user data vs external
- [ ] No CDS branding misuse
- [ ] Proper acknowledgment in README
- [ ] Rate limiting respects CDS servers

---

## 🎯 Success Criteria

### Must Have (Critical)
✅ SIMBAD lookup works  
✅ Gaia DR3 query works  
✅ Cross-match works  
✅ Attribution displayed  
✅ Documentation complete  

### Should Have (Important)
✅ Aladin Lite visualization  
✅ Multiple catalog support  
✅ Bulk enrichment  
✅ Export enriched data  
✅ Performance optimized  

### Nice to Have (Optional)
⭕ Demo video recorded  
⭕ Presentation slides ready  
⭕ Real-time query progress  
⭕ Advanced Aladin features  
⭕ Catalog comparison view  

---

## 📅 Timeline Summary

### Day 1 (8 hours)
- **Morning (4h):** Phase 1 - Backend Services
- **Afternoon (4h):** Phase 2 - API Endpoints

### Day 2 (8 hours)
- **Morning (4h):** Phase 3 - Frontend Components
- **Afternoon (4h):** Phase 4 - Dashboard Integration

### Day 3 (8 hours)
- **Morning (3h):** Phase 5 - Documentation
- **Afternoon (3h):** Phase 6 - Testing
- **Evening (2h):** Phase 7 - Demo Prep

**Total Estimated Time:** 24 hours (3 full days)

---

## 🚀 Ready to Start?

**Next Actions:**
1. ✅ Review this plan
2. ✅ Approve approach
3. ✅ Start with Task 0.1 (Install dependencies)
4. ✅ Work through each phase sequentially
5. ✅ Check off tasks as completed
6. ✅ Test continuously
7. ✅ Deploy when all tests pass

**Questions to Confirm:**
- [ ] Timeline acceptable? (3 days)
- [ ] Scope acceptable? (All 4 features)
- [ ] Attribution approach clear?
- [ ] Ready to install astroquery?

---

**When you're ready, say "START" and I'll begin with Task 0.1!** 🎯
