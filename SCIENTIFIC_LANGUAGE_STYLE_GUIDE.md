# 📝 SEDEX Scientific Language Style Guide

**Version**: 2.0 (Research-Grade)  
**Purpose**: Ensure scientifically conservative, precise language throughout system  
**Audience**: Developers, researchers, technical judges  
**Date**: February 5, 2026

---

## CORE PRINCIPLES

1. **No Discovery Claims**: System ranks, does not discover
2. **No Prediction**: Exploratory analysis, not forecasting
3. **Query-Bounded**: All results scoped to query constraints
4. **Explainable**: Every score must be traceable to features
5. **Deterministic**: Same query → same results (no stochasticity)

---

## PROHIBITED TERMS & APPROVED REPLACEMENTS

### **❌ Discovery Language**

| **NEVER SAY** | **INSTEAD SAY** | **Rationale** |
|---------------|-----------------|---------------|
| "AI discovered 15 anomalous stars" | "SEDEX ranked 15 objects with composite deviation scores > 0.70" | System ranks, doesn't discover |
| "System found hidden patterns" | "Algorithm identified objects ranking in top 5% by deviation metrics" | No "hidden" — explicit statistical methods |
| "Detected previously unknown objects" | "Ranked objects by distinctiveness within query results" | All objects in input database |

### **❌ Confidence Language (Probabilistic)**

| **NEVER SAY** | **INSTEAD SAY** | **Rationale** |
|---------------|-----------------|---------------|
| "94% confidence" | "HIGH consensus (multiple methods agree)" | NOT Bayesian confidence intervals |
| "p < 0.05 statistically significant" | "Ranks in top 5% of query results" | No hypothesis testing performed |
| "95% confidence interval: 2.3 ± 0.4" | "Magnitude: 2.3 (photometric z-score: 2.8σ from query mean)" | Descriptive, not inferential |
| "Confident this is a red giant" | "Object ranks highly by brightness and distance metrics" | No classification performed |

### **❌ Prediction Language**

| **NEVER SAY** | **INSTEAD SAY** | **Rationale** |
|---------------|-----------------|---------------|
| "Model predicts this star will explode" | "Object shows high proper motion (ranked top 3%)" | No temporal forecasting |
| "Likely to go supernova within 1000 years" | "System does not predict stellar evolution" | Physics-based models required |
| "Expected to have exoplanets" | "Object ranks distinctively by [features], candidate for follow-up" | No causal inference |

### **❌ Learning Language**

| **NEVER SAY** | **INSTEAD SAY** | **Rationale** |
|---------------|-----------------|---------------|
| "AI learns from your queries" | "Algorithm applies consistent ranking methods" | No online learning implemented |
| "System gets smarter over time" | "Deterministic statistical methods (no adaptation)" | Fixed algorithms |
| "Trained on millions of stars" | "Applies unsupervised methods (Isolation Forest, z-scores)" | No supervised training |

### **❌ Accuracy/Precision Claims**

| **NEVER SAY** | **INSTEAD SAY** | **Rationale** |
|---------------|-----------------|---------------|
| "99% accurate classification" | "Rankings stable under 5% noise (ρ=0.87)" | Accuracy requires ground truth |
| "Precise stellar type identification" | "Composite deviation scoring (no classification)" | No labeling performed |

---

## APPROVED TERMINOLOGY

### ✅ **Ranking & Deviation**
- "Composite deviation score"
- "Ranks in top X% of query results"
- "Photometric z-score: Y standard deviations from mean"
- "Distinctive within query-scoped distribution"
- "Outlier relative to returned dataset"

### ✅ **Consensus (Not Confidence)**
- "HIGH consensus: multiple methods agree"
- "MEDIUM consensus: 2 of 3 metrics show distinctiveness"
- "LOW consensus: limited deviation across metrics"
- "Multi-method agreement score"

### ✅ **Exploratory Language**
- "Exploratory data analysis"
- "Query-bounded ranking"
- "Hypothesis generation (not testing)"
- "Candidate for follow-up observation"
- "Suggests further investigation"

### ✅ **Statistical Methods**
- "Z-score normalization"
- "Percentile ranking (scipy.stats.percentileofscore)"
- "Euclidean distance from query centroid"
- "StandardScaler: (x - μ) / σ"
- "Spearman rank correlation"

### ✅ **Algorithmic Transparency**
- "Isolation Forest: tree-based anomaly detection"
- "DBSCAN: density-based clustering"
- "Composite scoring: 40% photometric + 30% spatial + 30% distance"
- "Deterministic pattern matching (no LLM)"

---

## BEFORE/AFTER EXAMPLES

### **Example 1: Query Results Summary**

#### ❌ **WRONG (Hackathon Language)**:
```
"AI discovered 127 stars with 89% confidence! Our intelligent system 
learned that 15 of these are likely exoplanet hosts. Model predicts 
3 will go supernova within 10,000 years. Statistically significant 
outliers detected (p < 0.001)."
```

#### ✅ **CORRECT (Research Language)**:
```
"SEDEX ranked 127 objects by composite deviation score. Top 15 rank 
in 95th percentile or higher across photometric, spatial, and distance 
metrics (HIGH consensus). Rankings scoped to query constraints. 
Exploratory analysis only — no prediction or hypothesis testing performed."
```

---

### **Example 2: Object Explanation**

#### ❌ **WRONG**:
```
"Star #42: AI is 94% confident this is a nearby red giant that will 
likely have exoplanets. Machine learning detected unusual spectral 
signature suggesting binary companion."
```

#### ✅ **CORRECT**:
```
"Object #42: Ranks in top 2% by brightness (magnitude -0.3, z-score 
2.9σ) and distance (parallax 45.2 mas, top 3% nearest). HIGH consensus 
across 3 independent metrics. Candidate for follow-up spectroscopy. 
Query-scoped ranking — not classification."
```

---

### **Example 3: Confidence Explanation**

#### ❌ **WRONG**:
```
"The model is 87% confident in this classification. Standard error: 
±0.12. P-value < 0.05 indicates statistical significance."
```

#### ✅ **CORRECT**:
```
"HIGH consensus: Photometric z-score (0.82), spatial deviation (0.71), 
and distance significance (0.68) agree this object is distinctive. 
Composite score: 0.74 (top 26%). Multi-method agreement indicates 
robustness within query scope."
```

---

### **Example 4: System Limitations**

#### ❌ **WRONG**:
```
"Our advanced AI can detect all anomalous stars with high precision. 
System learns from expert feedback to improve accuracy over time."
```

#### ✅ **CORRECT**:
```
"SEDEX identifies statistical outliers within query-bounded datasets 
using deterministic methods (Isolation Forest, z-scores). Limitations: 
(1) Rankings relative to query, not universal; (2) No causal inference; 
(3) Observational uncertainties not modeled; (4) No prediction capability. 
Designed for exploratory workflows, not confirmatory analysis."
```

---

### **Example 5: Parser Failure Handling**

#### ❌ **WRONG**:
```
"Sorry, I don't understand that query. Try asking something else."
```

#### ✅ **CORRECT**:
```
"Intent: PREDICT (UNSUPPORTED). SEDEX is an exploratory tool for 
ranking observations, not a predictive model. Stellar evolution 
requires physics-based simulations (e.g., MESA), not statistical 
ranking. Suggestion: Try 'Find stars with high proper motion' 
(descriptive query)."
```

---

## UI/FRONTEND LANGUAGE GUIDELINES

### **Header Descriptions**

#### ❌ **WRONG**:
```html
<h1>AI-Powered Star Discovery Platform</h1>
<p>Our intelligent system learns patterns and predicts stellar properties</p>
```

#### ✅ **CORRECT**:
```html
<h1>SEDEX: Statistical Exploratory Data analysis for astronomical EXploration</h1>
<p>Deterministic ranking and outlier detection for query-scoped astronomical catalogs</p>
```

---

### **Result Cards**

#### ❌ **WRONG**:
```
Object: Gaia DR3 123456789
Confidence: 94%
AI Classification: Likely red giant
Probability of exoplanets: 78%
```

#### ✅ **CORRECT**:
```
Object: Gaia DR3 123456789
Composite Deviation Score: 0.87
Consensus: HIGH (3/3 metrics agree)
Ranks: Top 13% brightness, Top 7% distance
Suggestion: Candidate for follow-up observation
```

---

### **Loading Messages**

#### ❌ **WRONG**:
```
"AI is analyzing your query..."
"Machine learning in progress..."
"Training model on your data..."
```

#### ✅ **CORRECT**:
```
"Applying statistical ranking methods..."
"Computing z-scores and percentiles..."
"Running deterministic pattern matching..."
```

---

## API RESPONSE STRUCTURE (JSON)

### ❌ **WRONG**:
```json
{
  "confidence": 0.94,
  "prediction": "red giant",
  "ai_accuracy": "high",
  "probability_exoplanet": 0.78,
  "statistical_significance": "p < 0.01"
}
```

### ✅ **CORRECT**:
```json
{
  "composite_score": 0.87,
  "consensus_level": "HIGH",
  "consensus_explanation": "Multiple metrics agree (photometric, spatial, distance)",
  "percentile_rank": 13,
  "deviation_category": "strong (score: 0.87)",
  "query_scope": "Results bounded to query constraints (no universal claims)",
  "method": "exploratory ranking (z-score + spatial + distance)",
  "limitations": "Query-scoped, no prediction, no hypothesis testing"
}
```

---

## ERROR MESSAGES

### ❌ **WRONG**:
```
"AI failed to process your query. System encountered an error."
```

### ✅ **CORRECT**:
```
"Insufficient data for statistical ranking (n < 50 objects). 
Suggestion: Broaden query constraints to increase sample size. 
SEDEX requires minimum 50 objects for stable percentile calculations."
```

---

## DOCUMENTATION LANGUAGE

### **README / Abstract**

#### ❌ **WRONG**:
```
COSMIC Data Fusion uses cutting-edge AI to discover hidden patterns 
in astronomical data. Our machine learning models learn from millions 
of stars to predict stellar properties with 95% accuracy.
```

#### ✅ **CORRECT**:
```
SEDEX (Statistical Exploratory Data analysis for astronomical EXploration) 
applies deterministic unsupervised learning (Isolation Forest, DBSCAN) 
and statistical ranking (z-scores, percentiles) to identify outliers 
within query-bounded astronomical catalogs. System provides explainable 
composite deviation scores for exploratory workflows. No prediction, 
classification, or hypothesis testing performed.
```

---

### **Methods Section**

#### ❌ **WRONG**:
```
We trained a deep neural network on 2 million stars from Gaia DR3. 
The model achieves 97% classification accuracy and predicts stellar 
evolution with high confidence.
```

#### ✅ **CORRECT**:
```
We apply Isolation Forest (100 estimators, contamination=0.05) for 
unsupervised anomaly detection on 4 features: RA, Dec, magnitude, 
parallax. Features normalized via StandardScaler (z-score: (x-μ)/σ). 
Composite scores combine photometric z-scores (40%), spatial Euclidean 
distance (30%), and parallax-based significance (30%). No training 
required — methods applied on-the-fly to query results. Consensus 
confidence determined by multi-method agreement (HIGH: 2+ methods > 0.6).
```

---

## STYLE RULES SUMMARY

### **DO**:
- ✅ Use precise statistical terminology (z-score, percentile, Spearman ρ)
- ✅ Scope all statements ("within query results", "relative to dataset")
- ✅ Explain methods transparently (Isolation Forest, StandardScaler)
- ✅ Acknowledge limitations explicitly
- ✅ Use "exploratory", "ranking", "deviation", "consensus"
- ✅ Provide quantitative context (top X%, score Y, z-score Z)

### **DO NOT**:
- ❌ Claim discovery, prediction, or learning
- ❌ Use probabilistic language without Bayesian framework
- ❌ Imply accuracy/precision without ground truth validation
- ❌ Overstate capabilities ("intelligent", "smart", "learns")
- ❌ Use marketing language ("cutting-edge", "advanced AI")
- ❌ Forget query-scope disclaimers

---

## VALIDATION CHECKLIST

Before finalizing any text (code comments, UI, docs):

- [ ] No "discovered" → Use "ranked" or "identified"
- [ ] No "confidence" (probabilistic) → Use "consensus level" or "agreement"
- [ ] No "predicts" → Use "ranks" or "suggests candidate"
- [ ] No "learns" → Use "computes" or "applies"
- [ ] No "statistically significant" → Use "ranks in top X%"
- [ ] Includes query-scope disclaimer
- [ ] Cites specific method (Isolation Forest, z-score, etc.)
- [ ] Quantitative context provided (percentiles, scores)
- [ ] Limitations acknowledged where appropriate

---

## EXEMPTIONS (When Probabilistic Language IS Allowed)

### ✅ **Acceptable Use Cases**:

1. **Evaluation Metrics** (internal, not user-facing):
   - "Spearman correlation ρ = 0.87 (p < 0.001)"
   - "Bootstrap confidence interval for rank stability"
   
2. **Algorithm Parameters** (technical docs):
   - "Isolation Forest contamination parameter (expected outlier fraction)"
   
3. **Measurement Uncertainties** (citing external data):
   - "Gaia parallax: 45.2 ± 0.8 mas (published error)"

4. **Statistical Tests** (evaluation framework only):
   - "Rank stability: Spearman ρ = 0.87 ± 0.03 (30 trials)"

### ❌ **NEVER Say** (even in technical docs):
- "AI confidence: 94%" (sounds like Bayesian posterior)
- "Model is certain this is a red giant" (no classification)
- "Predicts with 99% accuracy" (no prediction task)

---

## EXAMPLES BY CONTEXT

### **Code Comments**

#### ❌ **WRONG**:
```python
# AI learns from data to discover anomalies
confidence = model.predict_proba(X)
```

#### ✅ **CORRECT**:
```python
# Apply Isolation Forest for unsupervised anomaly detection
# Returns anomaly scores (not probabilities): negative = more anomalous
anomaly_scores = isolation_forest.decision_function(X_scaled)
```

---

### **Logging Messages**

#### ❌ **WRONG**:
```python
logger.info("AI model training complete. Accuracy: 97%")
```

#### ✅ **CORRECT**:
```python
logger.info("Isolation Forest fitted. 100 estimators, contamination=0.05")
```

---

### **Exception Messages**

#### ❌ **WRONG**:
```python
raise ValueError("AI confidence too low to make prediction")
```

#### ✅ **CORRECT**:
```python
raise ValueError("Insufficient data for ranking (n < 50). Broaden query.")
```

---

## FINAL REMINDER

**Every piece of text in SEDEX must pass this test**:

> "If a skeptical astronomer reads this, will they think we're overclaiming?"

If YES → Rewrite with more conservative language.

**Default to understatement, not hype.**

---

**Approved by**: Research Team  
**Review Date**: February 5, 2026  
**Next Review**: Before any public demo or paper submission

---

**END OF STYLE GUIDE**
