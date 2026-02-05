# ⚠️ SEDEX: Limitations & Failure Modes

**System**: Statistical Exploratory Data analysis for astronomical EXploration (SEDEX)  
**Version**: 2.0 (Research-Grade)  
**Purpose**: Explicit documentation of constraints, edge cases, and scientific boundaries  
**Audience**: Users, reviewers, researchers, technical judges  
**Date**: February 5, 2026

---

## CORE PRINCIPLE: SCIENTIFIC HONESTY

> **"A system that knows its limits is more trustworthy than one that doesn't."**

SEDEX is designed for exploratory ranking of query-bounded astronomical data. This document explicitly states what the system **cannot do**, when it **will fail**, and why certain **design choices limit applicability**.

---

## 1️⃣ FUNDAMENTAL LIMITATIONS

### **A. Query-Scope Dependency**

**Limitation**: Rankings are **relative to query results**, not universal astronomical properties.

**Example**:
```
Query 1: "Bright stars in Orion"
→ Object X ranks in top 1% (brightest within Orion)

Query 2: "All bright stars"
→ Same Object X ranks in top 30% (less distinctive in all-sky context)
```

**Impact**:
- Cross-query comparisons are **invalid** without normalization
- An object ranked highly in one query may not be scientifically significant
- "Top 5%" is meaningful only within query boundaries

**Mitigation**:
- All results include disclaimer: "Rankings scoped to current query"
- Future work: Cross-query normalization against all-sky catalog statistics

**When This Matters**:
- Users comparing results across different queries
- Scientific claims about "most unusual star in catalog" (impossible with query-scoped ranking)

---

### **B. No Causal Inference**

**Limitation**: SEDEX identifies **correlations**, not causes.

**What This Means**:
- High proper motion does NOT imply membership in a moving group (could be measurement error)
- Spatial clustering does NOT prove physical association (could be projection effect)
- Brightness anomalies do NOT indicate specific stellar type (could be distance effect)

**Example**:
```
SEDEX Output: "Object ranks in top 2% by proper motion"
❌ WRONG Interpretation: "This star is part of a moving group"
✅ CORRECT Interpretation: "Object shows distinctive kinematics; candidate for astrometric follow-up"
```

**Impact**:
- Rankings suggest **candidates**, not confirmed discoveries
- Physical validation requires additional data (spectroscopy, parallax refinement)
- Users may misinterpret statistical outliers as astrophysical phenomena

**Mitigation**:
- Explanations use "candidate for" language, not claims
- System does not assign categorical labels (e.g., "red giant", "binary")

---

### **C. No Predictive Capability**

**Limitation**: SEDEX analyzes **existing observations**, does not forecast future states.

**Cannot Do**:
- Predict stellar evolution ("will go supernova in X years")
- Forecast exoplanet transits
- Model binary orbits
- Extrapolate proper motion beyond ~1000 years (non-linear effects)

**Example**:
```
User Query: "Will this star explode?"
SEDEX Response: "UNSUPPORTED INTENT: PREDICT. System performs exploratory ranking, 
not temporal forecasting. Stellar evolution requires physics-based models (MESA, PARSEC)."
```

**Why**:
- Prediction requires domain-specific physics (nuclear reactions, gravitational dynamics)
- Statistical ranking does not capture physical laws
- Proper motion extrapolation assumes linear motion (valid only for isolated stars over short timescales)

**Mitigation**:
- Explicit failure handling for PREDICT intent (Domain-Constrained Semantic Parsing)
- Educational feedback explains why prediction is out-of-scope

---

### **D. No Categorical Classification**

**Limitation**: SEDEX does **not assign labels** (e.g., spectral type, stellar class).

**Cannot Do**:
- "Is this a red giant?" → NO classification
- "Separate white dwarfs from main sequence" → NO supervised learning
- "Classify stars by spectral type" → NO labeled training data

**Why**:
- Classification requires labeled training sets (e.g., SDSS spectral types)
- SEDEX uses **unsupervised methods** (Isolation Forest, z-scores) with no labels
- Adding classification would require external catalogs and validation

**What SEDEX Does Instead**:
- Ranks by **feature similarity** (without category assignment)
- Groups via **DBSCAN clustering** (descriptive, not prescriptive)
- Compares **relative positions** in feature space

**Example**:
```
User Query: "Is this a white dwarf?"
SEDEX Response: "UNSUPPORTED INTENT: CLASSIFY. System does not assign categorical labels. 
Try: 'Compare brightness and distance of [star name]' (feature-based comparison)."
```

---

### **E. Observational Uncertainty Not Modeled**

**Limitation**: Input data assumed **error-free**. Measurement uncertainties (σ) **ignored** in ranking.

**Impact**:
```
Star A: Parallax = 5.0 ± 0.1 mas (2% error)
Star B: Parallax = 1.0 ± 0.5 mas (50% error)

SEDEX treats both equally, even though Star B's distance is highly uncertain.
```

**Why This Is Bad**:
- Distant stars (small parallax, large fractional error) may rank unreliably
- Photometric errors propagate into z-score calculations without weighting
- High-error objects can appear as outliers spuriously

**Current Mitigation** (Partial):
- Median imputation for missing parallax (robust to outliers)
- Phase 4 failure detection: warns if >30% of data is missing

**Future Work**:
- Weight features by inverse measurement error (σ⁻¹)
- Downweight objects with parallax_error/parallax > 0.2 (20% threshold)
- Incorporate Gaia error columns (parallax_error, phot_g_mean_flux_error)

**When This Matters**:
- Users studying faint/distant objects (high photometric/parallax errors)
- Scientific claims requir ing uncertainty quantification

---

### **F. Arbitrary Feature Weighting**

**Limitation**: Composite scores use **fixed weights** (40% photometric, 30% spatial, 30% distance) **without scientific justification**.

**Why This Is Arbitrary**:
- No domain theory dictates 40/30/30 split
- Weights not optimized for any objective function
- Different science goals (e.g., finding nearby vs. bright stars) benefit from different weights

**Example**:
```
For finding "interesting stars for amateur observation":
→ Brightness should weight 70% (visibility priority)

For finding "kinematically unusual stars":
→ Proper motion should weight 70% (motion priority)

SEDEX uses 40/30/30 universally (one-size-fits-all).
```

**Impact**:
- Rankings may not align with user's unstated science goals
- Sensitivity to weight changes not quantified

**Mitigation** (Planned):
- Allow user-configurable weights via API parameter
- Evaluate rank stability across weight perturbations
- Document sensitivity: "Rankings stable for 40±10% photometric weight"

---

### **G. Cold Start Problem (Small Samples)**

**Limitation**: **Sparse queries** (< 50 objects) produce **unstable statistics**.

**Why**:
- Z-scores unreliable for n < 30 (Central Limit Theorem threshold)
- Percentiles poorly defined for small samples (e.g., "top 1%" of 10 objects = 1 object)
- Isolation Forest requires ~100 objects for robust anomaly detection

**Example**:
```
Query: "Stars in constellation Crux" → 8 results
→ Photometric z-score: Dividing by std of 8 values (high variance)
→ Percentiles: "Top 12.5%" = 1st object (not meaningful)
```

**Impact**:
- Rankings for n < 50 are **query-specific noise**, not generalizable patterns
- Users may trust rankings that are statistically meaningless

**Mitigation**:
- System warning: "Limited data for robust ranking (n < 50). Broaden query."
- Confidence downgraded to LOW for n < 50
- Future work: Bayesian ranking with prior from all-sky catalog

**When This Matters**:
- Rare object searches (e.g., "brown dwarfs within 10 parsecs")
- Narrowly constrained spatial queries

---

### **H. No Temporal Evolution Modeling**

**Limitation**: Proper motion extrapolation assumes **linear motion** (constant velocity).

**Breaks Down For**:
- **Binary stars**: Non-linear orbits (periods 1-100 years)
- **Exoplanet systems**: Reflex motion of host star
- **Cluster members**: Gravitational interactions
- **Long timescales**: > ±1000 years (non-linear galactic potential effects)

**Example**:
```
Query: "Show Betelgeuse in 3000 BC"
SEDEX: Uses linear proper motion
Reality: Betelgeuse may have non-linear motion (potential binary companion)
Error: Position could be off by arcminutes over 5000 years
```

**Impact**:
- Historical/future position queries **approximate only**
- Not suitable for high-precision astrometry

**Mitigation**:
- Disclaimer: "Linear proper motion. Accurate ±1000 years for isolated stars."
- Future work: Integrate GAIA DR3 epoch photometry for non-linear motion detection

---

### **I. Feature Degeneracy**

**Limitation**: If all objects have **same value** for a feature, that feature contributes **zero signal**.

**Example**:
```
Query: "Stars with magnitude = 5.0 ± 0.01"
→ All objects have identical brightness
→ Photometric z-scores = 0 (no variance)
→ Spatial/distance features dominate ranking
```

**Impact**:
- Composite scores effectively become 2-feature rankings (not 3-feature)
- Users unaware that one dimension is degenerate

**Detection**:
- Phase 4 failure mode: "Warning: No photometric variance detected (σ < 0.01)"

**Mitigation**:
- System checks for zero variance and warns user
- Suggests query broadening: "Try removing magnitude constraint"

---

### **J. Missing Critical Features**

**Limitation**: **> 30% missing values** for a feature degrades ranking quality.

**Common Missing Data**:
- Parallax: ~20% of Gaia DR3 stars have parallax_error/parallax > 0.2 (unreliable)
- Proper motion: ~10% missing for faint stars
- Radial velocity: ~90% of stars lack spectroscopic RV

**Current Handling**:
- **Median imputation**: Missing parallax replaced with dataset median
  - **Pro**: Robust to outliers, preserves sample size
  - **Con**: Artificially clusters imputed objects near median (not representative)

**Example**:
```
Query: 100 stars, 40 missing parallax
→ 40 stars assigned median parallax (e.g., 10 mas)
→ These 40 stars now appear "similar" in distance
→ Rankings biased toward photometric/spatial features
```

**Impact**:
- Imputed objects rank toward the middle (not distinctive)
- Composite scores less reliable for high-missing-data queries

**Better Approach** (Future):
- Exclude objects with > 20% missing features from ranking
- Show separately: "15 objects excluded due to incomplete data"

---

## 2️⃣ ALGORITHMIC LIMITATIONS

### **A. Isolation Forest: Contamination Parameter Sensitivity**

**Algorithm**: Isolation Forest for anomaly detection  
**Parameter**: `contamination = 0.05` (expect 5% outliers)

**Limitation**: Fixed contamination may not match true outlier fraction.

**Example**:
```
True outliers: 1% (contamination too high)
→ System labels 5% as anomalies (4% false positives)

True outliers: 15% (contamination too low)
→ System labels only 5% (10% false negatives)
```

**Impact**:
- Contamination hardcoded to 0.05 (one-size-fits-all)
- No automatic tuning based on data distribution

**Mitigation**:
- Future work: Adaptive contamination via silhouette score optimization
- Or: Allow user to specify expected outlier fraction

---

### **B. DBSCAN: Epsilon Parameter (eps) Tuning**

**Algorithm**: DBSCAN for clustering  
**Parameters**: `eps = 0.5` (distance threshold), `min_samples = 10`

**Limitation**: Fixed eps may not suit all spatial distributions.

**Too Small eps** (e.g., 0.1):
- Many small clusters (~2-3 members each)
- Most objects labeled as noise (-1)

**Too Large eps** (e.g., 2.0):
- Single giant cluster containing most objects
- Few meaningful groupings

**Current Value** (0.5):
- Optimized for Gaia DR3 all-sky catalogs (empirical testing)
- May not generalize to:
  - Small spatial queries (e.g., single constellation)
  - Dense regions (e.g., globular clusters → eps too large)

**Impact**:
- Clustering quality varies by query spatial distribution
- No automatic parameter tuning

**Mitigation**:
- Phase 4 failure detection: "Poor clustering (silhouette < 0.3)"
- Suggests: "Try adjusting spatial query boundaries"

---

### **C. StandardScaler: Outlier Sensitivity**

**Method**: Z-score normalization: `z = (x - μ) / σ`

**Limitation**: **Sensitive to outliers** (uses mean/std, not median/MAD).

**Example**:
```
Magnitudes: [5.0, 5.1, 5.2, 5.0, 5.1, 15.0] (one extreme outlier)
→ Mean = 6.4, Std = 3.7 (inflated by outlier)
→ Z-scores compressed for normal stars (5.0-5.2 all near z=0)
→ Outlier dominates scaling
```

**Impact**:
- Strong outliers in raw data can distort normalization
- Other objects appear less distinctive than they are

**Better Approach** (Future):
- **RobustScaler**: Use median/MAD instead of mean/std
  - Resistant to outliers
  - Formula: `z_robust = (x - median) / MAD`

**Current Mitigation**:
- Median imputation reduces some outlier effects
- But scaling still uses mean/std (not robust)

---

## 3️⃣ DATA QUALITY LIMITATIONS

### **A. Gaia DR3 Catalog Biases**

**SEDEX inherits biases from input data (Gaia DR3)**:

1. **Bright Star Saturation**:
   - Gaia struggles with mag < 3 (CCD saturation)
   - Brightest stars may have poor astrometry

2. **Distance Bias**:
   - Parallax errors increase with distance
   - Stars > 10 kpc effectively unmeasurable

3. **Crowded Field Degeneracy**:
   - Globular clusters: blended sources
   - Galactic plane: high extinction, confusion

4. **Completeness**:
   - Gaia ~85% complete for mag < 20
   - Missing: very faint stars, brown dwarfs

**Impact**:
- SEDEX rankings reflect **Gaia's selection function**, not true sky population
- Users studying inherently faint objects (e.g., white dwarfs) face incompleteness

**Mitigation**:
- Document in Methods: "Rankings reflect Gaia DR3 biases"
- Future work: Cross-match with 2MASS (infrared), SDSS (spectroscopy) to diversify features

---

### **B. Photometric Errors Not Propagated**

**Gaia Provides**:
- `phot_g_mean_mag` (brightness)
- `phot_g_mean_flux_error` (measurement uncertainty)

**SEDEX Uses**:
- ✅ Magnitude value
- ❌ Magnitude error (ignored)

**Why This Is Bad**:
```
Star A: mag = 10.0 ± 0.01 (precise)
Star B: mag = 10.0 ± 0.5 (uncertain)

SEDEX treats both identically, even though Star B's brightness is poorly known.
```

**Impact**:
- High-error objects can rank spuriously high (uncertainty mistaken for signal)

**Future Work**:
- Weight z-scores by inverse error: `w = 1 / phot_error`
- Downweight stars with phot_error > 0.1 mag

---

## 4️⃣ USER INTERFACE LIMITATIONS

### **A. No Real-Time Interaction**

**Limitation**: SEDEX processes **static queries**, does not support interactive refinement.

**Cannot Do**:
- "Show me more like this star" (no click-to-refine)
- "Adjust feature weights dynamically" (no sliders)
- "Expand this cluster" (no hierarchical zoom)

**Why**:
- System designed for batch processing
- No stateful session management

**Mitigation** (Future):
- Add interactive mode with session storage
- Implement "more like this" via k-nearest neighbors in feature space

---

### **B. No Visualization Embeddings**

**Limitation**: No 2D/3D feature space visualizations (t-SNE, UMAP).

**Current Output**:
- Text-based rankings
- Tabular data

**Not Provided**:
- Interactive star map with clusters colored
- Feature space scatterplot (RA vs Dec with anomalies highlighted)

**Why**:
- Focus on backend ranking, not frontend visualization
- Reduces scope creep

**Mitigation**:
- Frontend handoff document provides visualization guidelines
- Future work: Integrate Plotly/D3.js for interactive plots

---

## 5️⃣ EVALUATION LIMITATIONS

### **A. No Ground Truth for Validation**

**Limitation**: **No labeled dataset** (e.g., "confirmed anomalies") to measure accuracy.

**Cannot Compute**:
- Precision: TP / (TP + FP) → Requires knowing true anomalies
- Recall: TP / (TP + FN) → Requires knowing all missed anomalies
- F1-score, ROC-AUC, etc.

**What We Do Instead**:
- **Rank stability** under noise perturbation (Spearman ρ)
- **Baseline comparisons** (vs magnitude-only, random)
- **Multi-method agreement** (MMA score)

**Why This Is Acceptable**:
- Exploratory tools don't require supervised metrics
- Unsupervised evaluation standard in anomaly detection research

---

### **B. Evaluation Framework Assumptions**

**Rank Stability Test**:
- Assumes Gaussian noise (not realistic for all error sources)
- Photometric errors may be **non-Gaussian** (e.g., CCD saturation)

**Baseline Comparisons**:
- MMA score assumes all methods equally valid (may not be true)
- Magnitude-only baseline may actually be "correct" for brightness-focused queries

---

## 6️⃣ DOMAIN-CONSTRAINED SEMANTIC PARSING LIMITATIONS

### **A. Precision-Recall Trade-off**

**Design Choice**: **Precision > Recall** (100% correct parses, but fewer supported queries).

**Supported**:
- "Bright stars in Orion" ✅
- "Fast moving stars near Betelgeuse" ✅
- "Compare Sirius and Vega" ✅

**Unsupported**:
- "Interesting stars for astrophotography" ❌ (vague)
- "Stars similar to the Sun" ❌ (requires spectral parameters)
- "Best targets for tonight in Seattle" ❌ (requires visibility calculation)

**Impact**:
- ~40-60% of natural language queries unsupported (by design)
- Users may be frustrated by rejection rate

**Why This Is Acceptable**:
- Determinism > coverage for scientific tooling
- Unsupported queries get educational feedback (not silent failure)

---

### **B. No Synonym Expansion**

**Limitation**: Pattern matching uses **exact keywords**, not semantic similarity.

**Example**:
```
"Luminous stars" → ✅ Recognized (in brightness_synonyms)
"Radiant stars" → ❌ Not recognized (synonym not in hardcoded list)
```

**Why**:
- No word embeddings (Word2Vec, BERT) for semantic matching
- Hardcoded synonym lists incomplete

**Mitigation**:
- Expand synonym dictionaries based on user feedback
- Or: Future work: Add word embeddings (but would reduce determinism)

---

## 7️⃣ COMPUTATIONAL LIMITATIONS

### **A. Scalability Bounds**

**Tested Performance**:
- ✅ 100-10,000 objects: < 5 seconds (good)
- ⚠️ 10,000-50,000 objects: 5-30 seconds (moderate)
- ❌ > 50,000 objects: > 60 seconds (poor)

**Bottlenecks**:
- Isolation Forest: O(n log n × trees) → 100 trees expensive
- DBSCAN with spatial index: O(n log n) → But high constant factor
- Z-score computation: O(n) → Fast, not a bottleneck

**Impact**:
- All-sky queries (millions of stars) infeasible without pre-filtering
- Not suitable for real-time streaming data

**Mitigation**:
- Pre-filter queries to < 50k objects via database indexes
- Future: Parallelized Isolation Forest (joblib backend)

---

### **B. Memory Footprint**

**Typical Usage**:
- 10,000 objects × 4 features × 8 bytes = 320 KB (negligible)
- Isolation Forest: 100 trees × ~50 KB each = 5 MB (moderate)

**Breaks Down**:
- 1 million objects → 32 MB data + 500 MB model = 532 MB (manageable)
- 10 million objects → Out-of-memory on 8 GB RAM systems

**Future Work**:
- Mini-batch processing for large catalogs
- Sparse matrix representations for missing data

---

## 8️⃣ KNOWN FAILURE MODES (WITH DETECTION)

### **Table: Failure Modes & System Responses**

| **Failure Mode** | **Trigger** | **Detection Method** | **System Response** | **User Action** |
|------------------|-------------|----------------------|---------------------|-----------------|
| **Sparse Dataset** | n < 50 objects | Check sample size | ⚠️ Warning: "Limited data for robust ranking" | Broaden query constraints |
| **Feature Degeneracy** | σ < 0.01 for a feature | Check variance | ⚠️ Warning: "No photometric variance detected" | Remove tight magnitude filter |
| **High Missing Data** | > 30% NaN values | Count NaNs | ⚠️ Warning: "Insufficient parallax data. Rankings may be unreliable." | Filter by data quality (parallax_error < 0.2) |
| **Clustering Failure** | All DBSCAN labels = -1 | Check cluster count | ⚠️ Warning: "No clusters detected. Adjust eps or query scope." | Increase spatial area or reduce eps |
| **Anomaly Saturation** | All Isolation Forest scores negative | Check score distribution | ⚠️ Warning: "No clear anomalies. All objects similar." | Query lacks diversity |
| **Unsupported NL Intent** | Query contains "predict", "classify", "recommend" | Regex pattern matching | ❌ Error: "UNSUPPORTED INTENT: PREDICT" + educational feedback | Rephrase as descriptive query |
| **Low Parse Confidence** | parse_confidence < 0.3 | Check entity extraction | ⚠️ Warning: "Query interpretation uncertain. Did you mean...?" | Clarify with specific constellation/brightness terms |
| **Consensus Disagreement** | |photo_score - spatial_score| > 0.5 | Check score variance | ⚠️ LOW confidence: "Methods disagree, rankings uncertain" | Review individual metric contributions |

---

## 9️⃣ ETHICAL & SOCIAL LIMITATIONS

### **A. Not Suitable for High-Stakes Decisions**

**SEDEX should NOT be used for**:
- Spacecraft navigation (requires cm-level astrometry)
- Time-critical observations (transient events, GRBs)
- Medical/safety applications (obviously)

**Why**:
- Exploratory tool, not validated for mission-critical use
- No formal verification/validation process
- Rankings subject to data quality issues

---

### **B. Potential for Misuse**

**Risk**: Users may treat rankings as "ground truth" discoveries.

**Example Misuse**:
```
User: "SEDEX says this is the most interesting star!"
Reality: Object ranks top 1% in ONE query, may not be globally significant
```

**Mitigation**:
- Prominent disclaimers: "Rankings scoped to query, not universal"
- No "discovery" language in UI
- Encourage expert validation before scientific claims

---

## 🔟 LIMITATIONS SUMMARY TABLE

| **Category** | **Limitation** | **Impact** | **Mitigation Status** |
|--------------|----------------|------------|------------------------|
| Query Scope | Relative rankings | Cross-query comparisons invalid | ✅ Documented, UI warnings |
| Causality | Correlations ≠ causes | Misinterpretation risk | ✅ Language style guide |
| Prediction | No temporal forecasting | Cannot answer "will X happen?" | ✅ DCSP failure handling |
| Classification | No labels assigned | Cannot answer "is X a red giant?" | ✅ DCSP failure handling |
| Uncertainty | Errors not modeled | High-error objects misranked | ❌ Future work (error weighting) |
| Feature Weights | Arbitrary 40/30/30 | May not match user goals | ❌ Future work (adaptive weights) |
| Small Samples | n < 50 unstable | Unreliable rankings | ✅ Phase 4 detection + warnings |
| Temporal | Linear motion only | Historical queries approximate | ✅ Documented (±1000 yr limit) |
| Missing Data | Median imputation | Artificial clustering at median | ⚠️ Partial (future: exclude high-missing) |
| Contamination | Fixed at 5% | May not match true outlier rate | ❌ Future work (adaptive tuning) |
| DBSCAN eps | Fixed at 0.5 | Variable clustering quality | ⚠️ Partial (silhouette detection) |
| Outlier Scaling | Mean/std sensitive | Extreme values distort normalization | ❌ Future work (RobustScaler) |
| Gaia Biases | Inherited from catalog | Selection effects | ✅ Documented in Methods |
| No Ground Truth | Cannot measure accuracy | Precision/recall unknown | ✅ Alternative metrics (rank stability, MMA) |
| Scalability | Slow for > 50k objects | Not suitable for all-sky | ⚠️ Partial (pre-filtering) |
| Memory | Fails at ~10M objects | Out-of-memory | ❌ Future work (mini-batching) |

**Legend**:
- ✅ Mitigated (warnings, docs, design)
- ⚠️ Partially addressed (future work planned)
- ❌ Unresolved (acknowledged limitation)

---

## CONCLUSION

> **"SEDEX is a well-scoped exploratory tool, not a universal solution."**

This system is designed for:
- ✅ Query-bounded exploratory ranking
- ✅ Hypothesis generation for follow-up
- ✅ Educational use (undergraduate research)
- ✅ Observational planning assistance

This system is **NOT** designed for:
- ❌ Predictive modeling
- ❌ Classification into stellar types
- ❌ High-precision astrometry
- ❌ Mission-critical applications
- ❌ Confirmatory statistical testing

**Every limitation documented here makes SEDEX more trustworthy.**

Users who understand these bounds can use the system appropriately.  
Reviewers can evaluate the system fairly.  
Future developers know where to improve.

---

**Document Maintainer**: SEDEX Research Team  
**Last Updated**: February 5, 2026  
**Review Cycle**: Before any public release or paper submission

---

**END OF LIMITATIONS DOCUMENT**
