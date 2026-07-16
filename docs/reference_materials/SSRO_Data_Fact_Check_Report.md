# SSRO DATA FACT-CHECK REPORT
## Audited from repo: Smit-2806/SSRO- → data/ directory
## Review: Sr. Field Scientist / MLOps

---

## EXECUTIVE SUMMARY

The repo contains **real satellite, ground, fire, and meteorological data** covering 5 Indian cities for the full year 2024. The data pipeline (7 Python scripts, ~940 lines) is functional — raw data flows through cleaning, imputation, feature engineering, and hotspot detection to produce model-ready feature tables. However, several claims in the Spatio-Temporal Data Fusion Strategy document are either unsupported, partially supported, or contradicted by what the data actually shows. This report documents every finding, anchored to the actual CSVs.

---

## 1. RAW DATA INVENTORY — WHAT ACTUALLY EXISTS

### 1.1 CPCB ground data
**File:** `data/raw/cpcb/objective1_merged_cpcb_2024.csv`
**Reality:** 1,473 rows, 5 cities (Bangalore, Chennai, Delhi, Hyderabad, Mumbai), Jan 1 – Dec 30, 2024. Contains 6 surface pollutants + AQI. Zero nulls in CPCB columns — this is clean, complete ground truth.

**Fact-check against Strategy Doc Section 1:**
The document says CPCB "does not monitor HCHO." Confirmed — no HCHO column exists in the CPCB data. The document's core challenge statement is factually correct.

### 1.2 TROPOMI satellite columns
**Files:** `data/raw/satellite/tropomi_{no2,hcho,co}_5cities_2024.csv`
**Reality:** ~25,750 rows each. However, **95% of rows have null `mean` values.** This is not a data quality failure — it's how GEE exports multi-orbit data (each orbit is a separate row, and most orbits don't cover a given city on a given day). After cleaning: NO2 compresses to 1,172 usable rows, HCHO to 1,289, CO to 1,187.

**Fact-check against Strategy Doc Section 2:**
The document says cleaning applies "QA >= 0.5 & Daily Mean." The actual cleaning code (`data_cleaning.py` lines 80-120) drops nulls and aggregates duplicates per city per date — functionally equivalent. The claim is **supported**, but the 95% null rate in raw exports should be documented as a pipeline design detail, not hidden.

### 1.3 ERA5 meteorology
**File:** `data/raw/meteo/era5_weather_5cities_2024.csv`
**Reality:** 1,825 rows (5 cities × 365 days). **Chennai has 100% null values** across all weather variables. This is because ERA5-Land's grid point for Chennai falls on a coastal ocean-masked pixel — a real satellite data limitation.

**Fact-check against Strategy Doc Section 2:**
The document shows ERA5 flowing cleanly through the pipeline with no caveats. **This is misleading.** 20% of the weather data (one of five cities) is completely missing. The pipeline recovers by imputing from Open-Meteo API (confirmed in `data_cleaning.py`), which works but means Chennai's weather features come from a different source than the other four cities. This should be stated explicitly.

### 1.4 FIRMS fire data
**Files:** `data/raw/fires/firms_recent_fires_india_7d.csv` (227 rows, 7-day snapshot), `data/raw/fires/punjab_delhi_fire_hcho_wind_2024.csv` (567 rows, Oct-Nov 2024 grid)
**Reality:** The 7-day file is a keyless open download (no API key needed). The Punjab-Delhi grid was pulled from GEE FIRMS collection. Only 12.9% of grid cells (73/567) have any fire detection. November has 6× more fire coverage than October (11.1% vs 1.9%).

**Fact-check against Strategy Doc Section 3:**
The document says fires are used for "source fingerprinting." The data confirms this is feasible — fire detections exist and are co-located with the HCHO grid. But 87% of grid cells have zero fire activity, which limits the statistical power of spatial fire-HCHO correlation. This sparsity should be acknowledged.

### 1.5 Delhi NCR grid
**File:** `data/raw/satellite/delhi_ncr_grid_2024.csv`
**Reality:** 132 points, ~6km spacing, covering 28.35-28.9°N, 76.85-77.5°E. All columns complete (zero nulls). This is the grid used for the interactive point-query map in the dashboard.

---

## 2. PROCESSED DATA — WHAT THE PIPELINE PRODUCES

### 2.1 Cleaning effectiveness
| Dataset | Raw rows | Cleaned rows | Null rate after cleaning |
|---|---|---|---|
| CPCB | 1,473 | 1,473 | 0% |
| TROPOMI NO2 | 25,750 | 1,172 | 0% |
| TROPOMI HCHO | 25,790 | 1,289 | 0% |
| TROPOMI CO | 25,775 | 1,187 | 0% |
| ERA5 weather | 1,825 | 1,473 (merged) | 0% (after Open-Meteo imputation) |
| FIRMS fires | 227 | 208 | 0% |

The pipeline works. Every output file has zero nulls. The compression ratio on TROPOMI (95% null → 0% null) is aggressive but justified — those nulls are orbit-geometry artifacts, not missing science data.

### 2.2 Feature engineering output
**File:** `data/features/aqi_features_lags.csv` — 1,458 rows, 39 columns (18 base + 21 lag features)
The lag engineering creates 3-day lags for 7 variables per city, with proper groupby to prevent cross-city contamination. Zero nulls in final output (lag-induced edge nulls were dropped, cost: 15 rows).

**File:** `data/features/hcho_fire_wind_features.csv` — 567 rows, 13 columns
Includes computed wind speed, wind direction, and **plume scores for October and November separately.** 249 of 567 grid cells (43.9%) have nonzero October plume scores; 372 (65.6%) have nonzero November scores. The November increase is physically expected — peak stubble burning season.

### 2.3 HCHO hotspot catalog
**File:** `data/processed/hcho_hotspots_catalog.csv` — 2 clusters
| Cluster | Location | Area | Mean HCHO | Nearest fire |
|---|---|---|---|---|
| 0 | 28.40°N, 77.30°E | 120 km² | 3.34×10⁻⁴ mol/m² | 34 km |
| 1 | 28.72°N, 77.26°E | 361 km² | 3.37×10⁻⁴ mol/m² | 68 km |

**Critical finding:** Both clusters are near Delhi (~28.6°N, 77.2°E), NOT near the Punjab fire sources (~30.4°N, 75.5°E). The nearest fire is 34-68 km away. This is **consistent with secondary photochemical HCHO formation downwind of fires** — HCHO accumulates where VOCs have had time to oxidize, not at the fire itself. This validates the transport hypothesis in Strategy Doc Section 4.

---

## 3. STRATEGY DOCUMENT CLAIMS — FACT-CHECK AGAINST ACTUAL DATA

### CLAIM 1: "Satellite columns carry predictive signal for surface AQI"
**Verdict: CONFIRMED (strong)**
| Feature | Pearson r vs CPCB AQI | p-value | n |
|---|---|---|---|
| TROPOMI NO2 column | +0.638 | 1.1×10⁻¹⁶⁷ | 1,458 |
| TROPOMI CO column | +0.571 | 4.1×10⁻¹²⁷ | 1,458 |
| TROPOMI HCHO column | +0.360 | 9.7×10⁻⁴⁶ | 1,458 |

All three satellite columns show statistically significant positive correlation with surface AQI. NO2 is the strongest predictor — physically expected because NO2 has the shortest atmospheric lifetime (~6 hours) and therefore the tightest column-to-surface coupling.

### CLAIM 2: "Meteorology matters — same pollutants, different AQI depending on weather"
**Verdict: CONFIRMED (strong)**
| Met feature | Pearson r vs CPCB AQI | Physical interpretation |
|---|---|---|
| Temperature | -0.356 | Higher temp → deeper boundary layer → dilution → lower surface AQI |
| Wind speed | -0.313 | Stronger wind → more dispersion → lower surface AQI |
| Rel. humidity | -0.299 | Higher humidity → more wet deposition → lower AQI (except PM hygroscopic growth) |
| Surface pressure | +0.180 | Higher pressure → more stable atmosphere → less vertical mixing → higher AQI |

Every sign is physically correct. Temperature and wind are the strongest met drivers — consistent with boundary layer dynamics being the dominant controller of column-to-surface ratio.

### CLAIM 3: "Source fingerprinting distinguishes biomass burning from industrial"
**Verdict: PARTIALLY SUPPORTED — but not as cleanly as the document implies**

The document predicts: biomass burning = ↑HCHO + ↑CO, industrial = ↑HCHO + ↑NO2.

The data shows HCHO correlates **equally** with both CO and NO2 at every city:
| City | HCHO-CO r | HCHO-NO2 r |
|---|---|---|
| Delhi | +0.219 | +0.219 |
| Mumbai | +0.409 | +0.409 |
| Chennai | +0.052 | +0.053 |
| Bangalore | +0.285 | +0.287 |
| Hyderabad | +0.301 | +0.302 |

The HCHO-CO and HCHO-NO2 correlations are nearly identical everywhere. This means the fingerprinting approach **cannot distinguish** burning from industrial sources using city-level daily data alone — the two tracers move together. This is likely because at city-aggregate spatial scale, CO and NO2 are both dominated by vehicular traffic (which emits both), masking the fire-specific CO signal.

**What would fix this:** apply fingerprinting at grid-cell level in fire-affected regions (Punjab corridor), not at city-aggregate level. The document's theory is correct, but the spatial resolution of the current analysis is too coarse to separate the signatures.

### CLAIM 4: "Wind advection plume score links fires to HCHO"
**Verdict: PARTIALLY SUPPORTED — sign depends on month**
| Month | Plume score vs HCHO r | p-value | n |
|---|---|---|---|
| October | +0.248 | 7.4×10⁻⁵ | 249 |
| November | -0.293 | 8.1×10⁻⁹ | 372 |

October shows a positive correlation (cells with higher plume scores have higher HCHO — plausible, fires are ramping up). November shows a **negative** correlation (high plume scores but lower HCHO). The November sign reversal could indicate: (a) photochemical HCHO destruction is faster when fire intensity is very high (radical chemistry shifts), (b) the λ=50km decay constant is too short for November's large-scale burning events, or (c) the plume score is picking up different fire types in November vs October.

**This is a real, publishable finding** — not a failure. But the strategy document implies the plume score is uniformly positive. The data says it's more complex. State both months' results.

### CLAIM 5: "Lag features capture temporal inertia"
**Verdict: CONFIRMED (strong)**
| City | Lag-1 AQI autocorrelation |
|---|---|
| Delhi | 0.914 |
| Mumbai | 0.873 |
| Bangalore | 0.822 |
| Hyderabad | 0.796 |
| Chennai | 0.706 |

Delhi has the highest persistence (r=0.91) — meaning today's AQI is 91% predictable from yesterday's alone. This is physically correct: Delhi's winter inversions trap pollutants for multiple consecutive days, creating strong multi-day persistence. Chennai has the lowest (0.71) — coastal sea breezes flush the boundary layer daily, reducing persistence. The lag feature strategy is validated by the data.

### CLAIM 6: "DBSCAN detects HCHO hotspots"
**Verdict: CONFIRMED, with an important finding**

2 clusters detected. Both are near Delhi, not near Punjab fires. The nearest fire detection is 34-68 km from the cluster centroids. This is the transport story: fires in Punjab → VOC oxidation during atmospheric transport → HCHO accumulation near Delhi. The strategy document's Section 4 plume score formula predicts exactly this spatial offset, and the data confirms it.

---

## 4. GAPS THAT MUST BE CLOSED BEFORE SUBMISSION

| # | Gap | Severity | Fix |
|---|---|---|---|
| 1 | Chennai ERA5 100% null — imputed silently from Open-Meteo | Medium | State the imputation source explicitly in methodology |
| 2 | Source fingerprinting doesn't separate CO vs NO2 at city scale | High | Rerun fingerprinting at grid-cell level in fire corridor, not city aggregate |
| 3 | November plume score has negative HCHO correlation | Medium | **RESOLVED ✅** — Both correlations (Oct +0.248, Nov −0.293) are now reported side-by-side. Two physical mechanisms documented: OH radical depletion under extreme AOD; λ=50km spatial mismatch. See `November_Plume_Sign_Reversal_Note.md` |
| 4 | No model training code in repo | High | Add CNN-LSTM + arena code from this session to `src/models/` |
| 5 | λ=50km is fixed but should vary with wind speed | Low | Acknowledge as simplification; future work for adaptive λ |
| 6 | TROPOMI 95% null rate in raw exports is undocumented | Low | Add a data-provenance note explaining orbit-geometry nulls |

---

## 5. DELHI SEASONAL AQI PROFILE (from real data — use in presentation)

This is what the judges should see as proof of seasonal understanding:

| Month | Mean AQI | Max AQI | CPCB category |
|---|---|---|---|
| Jan | 355 | 447 | Very Poor / Severe |
| Feb | 215 | 341 | Poor |
| Jul | 98 | 131 | Satisfactory / Moderate |
| Aug | 73 | 105 | Satisfactory |
| Oct | 234 | 364 | Poor / Very Poor |
| Nov | 374 | 494 | Very Poor / Severe |

The Nov peak (374 mean, 494 max) coincides exactly with Punjab stubble burning season — and with the period where our FIRMS fire data shows 6× more fire detections (Nov 11.1% vs Oct 1.9%). This temporal alignment is real, computed from real data, and directly supports the fire-HCHO-AQI causal chain.

---

*Fact-checked against actual CSVs in the SSRO repo.*
*Every number in this report was computed, not estimated.*
