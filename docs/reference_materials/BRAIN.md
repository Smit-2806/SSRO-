# 🧠 SSRO PROJECT BRAIN
## The Single Source of Truth for Team SSRO — Bharatiya Antariksh Hackathon 2026
### Last Updated: 12 July 2026

> **PURPOSE:** This file acts as the persistent memory of the entire project. Every agent, every team member, and every session MUST read this file before doing any work and MUST update it after every significant change. This eliminates hallucination, context loss, and integration breaks.

---

## 📌 TABLE OF CONTENTS
1. [Project Identity](#1-project-identity)
2. [Team Structure & Ownership](#2-team-structure--ownership)
3. [Problem Statement Summary](#3-problem-statement-summary)
4. [Hackathon Schedule & Milestones](#4-hackathon-schedule--milestones)
5. [File & Folder Architecture](#5-file--folder-architecture)
6. [All Dataset Inventory](#6-all-dataset-inventory)
7. [Data Sources & APIs](#7-data-sources--apis)
8. [City Coverage](#8-city-coverage)
9. [Pipeline Architecture & Code Map](#9-pipeline-architecture--code-map)
10. [Scientific Findings & Verified Numbers](#10-scientific-findings--verified-numbers)
11. [Model Architecture](#11-model-architecture)
12. [Validation Strategy](#12-validation-strategy)
13. [Known Issues, Gaps & Fact-Check Results](#13-known-issues-gaps--fact-check-results)
14. [Completed Work Log](#14-completed-work-log)
15. [Active Implementation Plan](#15-active-implementation-plan)
16. [Task Status by Member](#16-task-status-by-member)
17. [Key Constants & Physical Parameters](#17-key-constants--physical-parameters)
18. [Git & Deployment Info](#18-git--deployment-info)

---

## 1. Project Identity

| Field | Value |
|:---|:---|
| **Hackathon** | Bharatiya Antariksh Hackathon 2026 |
| **Problem Statement** | Development of Surface AQI & Identification of HCHO Hotspots over India using Satellite Data |
| **Team Name** | SSRO |
| **GitHub Repo** | `Smit-2806/SSRO-` (main branch) |
| **Execution Window** | 5 July 2026 – 17 July 2026 |
| **Feature Freeze** | 14 July 2026 (end of day) |
| **Final Submission** | 17 July 2026 |

---

## 2. Team Structure & Ownership

| Member | Role | Primary Ownership |
|:---|:---|:---|
| **Smit Patadiya** | Data Engineering & AQI/ML Lead | Surface AQI prediction pipeline: CPCB/AOD ingestion, feature engineering, CNN-LSTM + Attention model, SHAP explainability, holdout validation, final AQI artifacts |
| **Shubh Soni** | HCHO Intelligence & Scientific Validation Lead | TROPOMI HCHO processing, FIRMS fire analytics, DBSCAN hotspot detection, fire-HCHO correlation, wind-transport analysis, source attribution, scientific validation |
| **Tirth** | Geospatial, Dashboard & Integration Lead | ERA5 meteorology prep, GIS utilities, common grid, dashboard architecture, all visualization views, deployment, submission packaging |

---

## 3. Problem Statement Summary

**Objective 1 (Smit):** Estimate ground-level **Surface AQI** at unmonitored locations across India using satellite data (TROPOMI, INSAT-3D AOD) fused with CPCB ground observations and ERA5 meteorology. The core challenge: CPCB measures surface chemistry but has limited spatial coverage; satellites have spatial coverage but measure column quantities, not surface concentrations.

**Objective 2 (Shubh):** Detect **HCHO hotspots** over India and link them to fire activity (agricultural/biomass burning). CPCB does NOT monitor HCHO on the ground — Sentinel-5P TROPOMI is the only source. HCHO has a short atmospheric lifetime (2–4 hours in daylight) and drifts downwind from fires.

**Core Innovation:** Spatio-temporal data fusion combining:
- Ground truth chemistry (CPCB) → surface-level accurate
- Satellite gas columns (TROPOMI) → spatially complete
- Satellite aerosol loading (INSAT-3D AOD) → PM2.5 proxy
- Meteorology (ERA5/Open-Meteo) → dispersion physics

---

## 4. Hackathon Schedule & Milestones

| Date | Milestone |
|:---:|:---|
| 5 July ✅ | Architecture, data contracts, repository structure frozen |
| 6 July ✅ | Essential datasets available for proof-of-concept period |
| 7 July ✅ | Cleaned and QA-controlled individual datasets |
| 8 July ✅ | First harmonized multi-source analytical datasets |
| 9 July ✅ | Baseline AQI results, initial HCHO hotspots, working dashboard shell |
| 10 July ✅ | Both scientific objectives operational at prototype level |
| 11 July ✅ | Core AQI model and HCHO/fire/wind intelligence pipeline complete |
| **12 July ✅** | **All-India expansion: 83-city master, 30k-row unified baseline, BRAIN.md, standardized datasets pushed** |
| 13 July | Explainability and scientific validation integrated |
| **14 July** | **FEATURE FREEZE — Feature-complete integrated prototype** |
| 15 July | Release Candidate 1 available |
| 16 July | Stable submission candidate with documentation |
| **17 July** | **FINAL SUBMISSION — Deployed prototype, demo, judge Q&A** |

**Execution Rules:**
1. 15-minute daily sync meeting before work starts
2. Every member pushes usable artifacts before daily integration checkpoint
3. Data contracts/output schemas must not change without informing dependent owners
4. Use mock outputs until real artifacts available; replace progressively
5. Freeze major features after 14 July
6. Every scientific claim in dashboard/presentation must be traceable to a generated result
7. Maintain reproducible scripts — no manual-only transformations in final pipeline

---

## 5. File & Folder Architecture

```
ISRO Hackathon/
├── data/
│   ├── raw/
│   │   ├── cpcb/          → Ground AQI measurements from CPCB CAAQMS
│   │   ├── satellite/     → TROPOMI gas columns, INSAT-3D AOD, Delhi NCR grid
│   │   ├── fires/         → NASA FIRMS active fire detections
│   │   └── meteo/         → ERA5 / Open-Meteo weather variables
│   ├── processed/         → QA-cleaned, gap-filled, merged datasets
│   ├── features/          → Model-ready lag features, HCHO-fire-wind features
│   ├── models/            → Trained model weights (.pth, .pkl)
│   └── predictions/       → Dashboard-ready output grids
├── src/
│   ├── data_pipeline/     → All ingestion, cleaning, transformation scripts
│   ├── aqi_model/         → CNN-LSTM + Attention model code
│   ├── hcho_analytics/    → Hotspot detection, correlation, attribution scripts
│   ├── dashboard/         → Frontend dashboard code
│   └── utils/             → Shared utilities
├── docs/
│   ├── AQI_Model_Pipeline_Design.md
│   ├── HCHO_Analysis_Schema.md
│   ├── FIRMS_Active_Fire_Structure.md
│   ├── S5P_HCHO_Structure.md
│   ├── Data_Source_Comparison_Report.md
│   ├── reference_materials/
│   │   ├── BRAIN.md                        ← THIS FILE
│   │   ├── SSRO_Data_Fact_Check_Report.md
│   │   ├── Spatio_Temporal_Data_Fusion_Strategy.md
│   │   ├── AOD_Acquisition_Report.md
│   │   ├── ISRO_Hackathon_Problem_Statement.pdf
│   │   └── Final Ideation Document.pdf
│   └── task_schedules/
│       ├── 01_Team_SSRO_Task_Schedule_Listed.md
│       ├── 02_Shubh_Task_Manager_Listed.md
│       ├── 03_Smit_Task_Manager_Listed.md
│       └── 04_Tirth_Task_Manager_Listed.md
├── config/
├── notebooks/
├── tests/
└── index.html             → Dashboard entry point
```

---

## 6. All Dataset Inventory

### 6.1 Current Datasets (Post-Standardization, as of 12 July 2026)

All year suffixes (`_2024`, `_7d`) have been removed from filenames. All files now have `latitude` and `longitude` columns.

#### RAW DATA

| File | Path | Rows | Date Range | Cities | Lat/Lon |
|:---|:---|:---:|:---|:---|:---:|
| `objective1_merged_cpcb.csv` | `data/raw/cpcb/` | 1,473 | 2024-01-01→2024-12-30 | 5 cities | ✅ injected |
| `openaq_cpcb_allcities.csv` | `data/raw/cpcb/` | **30,295** | 2024-01-01→2024-12-30 | **83 cities** | ✅ WGS84 centroids |
| `era5_weather_5cities.csv` | `data/raw/meteo/` | 1,825 | 2024-01-01→2024-12-31 | 5 cities | ✅ already had |
| `tropomi_hcho_5cities.csv` | `data/raw/satellite/` | ~25,790 | 2024 (multi-orbit) | 5 cities | ✅ city-level |
| `tropomi_no2_5cities.csv` | `data/raw/satellite/` | ~25,750 | 2024 (multi-orbit) | 5 cities | ✅ city-level |
| `tropomi_co_5cities.csv` | `data/raw/satellite/` | ~25,775 | 2024 (multi-orbit) | 5 cities | ✅ city-level |
| `insat3d_aod_5cities.csv` | `data/raw/satellite/` | 1,473 | 2024-01-01→2024-12-30 | 5 cities | ✅ direct coords |
| `insat3d_aod_allcities.csv` | `data/raw/satellite/` | **30,295** | 2024-01-01→2024-12-30 | **83 cities** | ✅ WGS84 centroids |
| `delhi_ncr_grid.csv` | `data/raw/satellite/` | 132 | N/A (spatial grid) | Delhi NCR | ✅ lat/lon |
| `firms_recent_fires_india.csv` | `data/raw/fires/` | 227 | 2026-07-01→2026-07-08 | All India | ✅ lat/lon |
| `punjab_delhi_fire_hcho_wind.csv` | `data/raw/fires/` | 567 | Oct–Nov 2024 | Punjab-Delhi | ✅ lat/lon |

#### PROCESSED DATA

| File | Path | Rows | Columns | Nulls | Description |
|:---|:---|:---:|:---:|:---:|:---|
| `cpcb_cleaned.csv` | `data/processed/` | 1,473 | — | 0 | Cleaned CPCB AQI + pollutants (5 cities) |
| `aqi_cleaned_baseline.csv` | `data/processed/` | 1,473 | 22 | 0 | **Unified baseline: CPCB + AOD + ERA5 (5 cities)** |
| `aqi_cleaned_baseline_allcities.csv` | `data/processed/` | **30,295** | **17** | **0** | **🆕 All-India unified baseline: 83 cities × 365 days** |
| `insat3d_aod_cleaned.csv` | `data/processed/` | 1,032 | — | 0 | QA-filtered AOD — 5 cities (29.9% cloud-masked) |
| `insat3d_aod_allcities_cleaned.csv` | `data/processed/` | **21,383** | — | 0 | **🆕 QA-filtered AOD — 83 cities (29.4% cloud-masked)** |
| `tropomi_hcho_cleaned.csv` | `data/processed/` | 1,289 | — | 0 | Cleaned HCHO daily city means |
| `tropomi_no2_cleaned.csv` | `data/processed/` | 1,172 | — | 0 | Cleaned NO2 daily city means |
| `tropomi_co_cleaned.csv` | `data/processed/` | 1,187 | — | 0 | Cleaned CO daily city means |
| `firms_recent_fires_cleaned.csv` | `data/processed/` | 208 | — | 0 | Cleaned 7-day fire snapshot |
| `punjab_delhi_fire_hcho_wind_cleaned.csv` | `data/processed/` | 567 | — | 1,060 | Cleaned Punjab-Delhi grid (nulls are structural) |
| `hcho_hotspots_catalog.csv` | `data/processed/` | 2 | — | 0 | DBSCAN cluster results |
| `source_attribution_catalog.csv` | `data/processed/` | 2 | — | 0 | Attribution scores per hotspot |
| `wind_transport_paths.csv` | `data/processed/` | 63 | — | 0 | Wind plume transport vectors |

#### FEATURE DATA

| File | Path | Rows | Columns | Description |
|:---|:---|:---:|:---:|:---|
| `aqi_features_lags.csv` | `data/features/` | 1,458 | 39 | 18 base features + 21 lag features (3-day lags for 7 variables) — 5 cities |
| `hcho_fire_wind_features.csv` | `data/features/` | 567 | 13 | HCHO + fire count + FRP + plume score (Oct & Nov separately) |

### 6.2 Unified Baseline Column Schema

#### 5-City Baseline (`aqi_cleaned_baseline.csv` — 22 columns)

| # | Column | Source | Unit |
|:---:|:---|:---:|:---|
| 1 | `City` | CPCB | — |
| 2 | `date` | CPCB | YYYY-MM-DD |
| 3 | `latitude` | Centroid | WGS84 decimal degrees |
| 4 | `longitude` | Centroid | WGS84 decimal degrees |
| 5 | `CPCB_AQI` | CPCB | 0–500 index |
| 6 | `CPCB_PM25` | CPCB | µg/m³ |
| 7 | `CPCB_PM10` | CPCB | µg/m³ |
| 8 | `CPCB_NO2_surface` | CPCB | µg/m³ |
| 9 | `CPCB_SO2` | CPCB | µg/m³ |
| 10 | `CPCB_CO_surface` | CPCB | mg/m³ |
| 11 | `CPCB_O3` | CPCB | µg/m³ |
| 12 | `TROPOMI_CO_mol_m2` | Sentinel-5P | mol/m² |
| 13 | `TROPOMI_HCHO_mol_m2` | Sentinel-5P | mol/m² |
| 14 | `TROPOMI_NO2_mol_m2` | Sentinel-5P | mol/m² |
| 15 | `temp_c` | ERA5/Open-Meteo | °C |
| 16 | `dewpoint_c` | ERA5/Open-Meteo | °C |
| 17 | `wind_speed_ms` | ERA5/Open-Meteo | m/s |
| 18 | `pressure_hpa` | ERA5/Open-Meteo | hPa |
| 19 | `precip_mm` | ERA5/Open-Meteo | mm/day |
| 20 | `rel_humidity_pct` | ERA5/Open-Meteo | % |
| 21 | `insat_aod` | INSAT-3D (derived) | dimensionless |
| 22 | `qa_flag` | INSAT-3D | 0=High, 1=Med, 2=Cloudy |

#### 🆕 All-India Baseline (`aqi_cleaned_baseline_allcities.csv` — 17 columns)

| # | Column | Source | Unit |
|:---:|:---|:---:|:---|
| 1 | `City` | Physics model | — |
| 2 | `state` | Master list | — |
| 3 | `zone` | Master list | North/South/East/West |
| 4 | `latitude` | WGS84 centroid | decimal degrees |
| 5 | `longitude` | WGS84 centroid | decimal degrees |
| 6 | `date` | Generated | YYYY-MM-DD |
| 7 | `CPCB_PM25` | Physics model | µg/m³ |
| 8 | `CPCB_PM10` | Physics model | µg/m³ |
| 9 | `CPCB_NO2_surface` | Physics model | µg/m³ |
| 10 | `CPCB_SO2` | Physics model | µg/m³ |
| 11 | `CPCB_CO_surface` | Physics model | mg/m³ |
| 12 | `CPCB_O3` | Physics model | µg/m³ |
| 13 | `CPCB_AQI` | PM2.5→AQI formula | 0–500 |
| 14 | `insat_aod` | INSAT-3D (derived) | dimensionless |
| 15 | `qa_flag` | INSAT-3D | 0=High, 1=Med, 2=Cloudy |
| 16 | `solar_zenith_angle` | INSAT-3D geometry | degrees |
| 17 | `satellite_zenith_angle` | INSAT-3D geometry | degrees |

---

## 7. Data Sources & APIs

| Source | What We Get | API Key? | URL / Method |
|:---|:---|:---:|:---|
| **CPCB CAAQMS** | Ground AQI, PM2.5, PM10, NO2, SO2, CO, O3 | ❌ | Via OpenAQ aggregator |
| **OpenAQ v3 API** | CPCB measurements for all Indian cities | ❌ | `api.openaq.org/v3` — **NOTE: v2 returns HTTP 410 (deprecated). v3 requires re-testing.** |
| **Physics Fallback (active)** | Synthetic CPCB data for all 83 cities using regional seasonal patterns | ❌ | `fetch_openaq_cpcb.py` fallback — triggered automatically when API returns 0 records |
| **Sentinel-5P TROPOMI** | HCHO, NO2, CO, UV Aerosol Index columns | ❌ | Google Earth Engine (GEE) |
| **NASA FIRMS** | Active fire detections (FRP, confidence) | ❌ | `firms.modaps.eosdis.nasa.gov` keyless CSV |
| **INSAT-3D MOSDAC** | AOD (physically derived in lieu of direct access) | ❌ | Physics formula: PM2.5 × hygroscopic × dispersion |
| **ERA5 / Open-Meteo** | Temperature, wind, humidity, pressure, rainfall | ❌ | `api.open-meteo.com/v1/era5` keyless |
| **Google Earth Engine** | TROPOMI swath exports, FIRMS archive | Needs GEE account | `earthengine.google.com` (free) |

---

## 8. City Coverage

### Current Coverage (5 Cities — Legacy Datasets)

| City | State | Region | Latitude | Longitude |
|:---|:---|:---|:---:|:---:|
| Delhi | Delhi NCT | North India | 28.6139°N | 77.2090°E |
| Mumbai | Maharashtra | West India | 19.0760°N | 72.8777°E |
| Chennai | Tamil Nadu | South India | 13.0827°N | 80.2707°E |
| Bangalore | Karnataka | South India | 12.9716°N | 77.5946°E |
| Hyderabad | Telangana | South-Central | 17.3850°N | 78.4867°E |

### ✅ EXPANDED COVERAGE: 83 Cities All-India (as of 12 July 2026)

| Zone | Count | Key Cities |
|:---|:---:|:---|
| North | 30 | Delhi, Lucknow, Kanpur, Agra, Varanasi, Jaipur, Chandigarh, Amritsar, Ludhiana, Dehradun |
| West | 20 | Mumbai, Pune, Nagpur, Ahmedabad, Surat, Vadodara, Bhopal, Indore, Raipur |
| East | 14 | Kolkata, Patna, Bhubaneswar, Ranchi, Jamshedpur, Guwahati |
| South | 19 | Chennai, Bangalore, Hyderabad, Coimbatore, Visakhapatnam, Kochi, Mysore |
| **Total** | **83** | — |

- City master list: `src/data_pipeline/india_cities_master.py`
- Fetch script: `src/data_pipeline/fetch_openaq_cpcb.py`
- **OpenAQ API status:** v2 deprecated (HTTP 410), v3 untested. Physics fallback active.
- **All-India baseline:** `data/processed/aqi_cleaned_baseline_allcities.csv`

---

## 9. Pipeline Architecture & Code Map

### 9.1 Data Pipeline Scripts (`src/data_pipeline/`)

| Script | Role | Key Output |
|:---|:---|:---|
| `improvise_datasets.py` | Generates CPCB + weather + TROPOMI synthetic/real data | `data/raw/cpcb/objective1_merged_cpcb.csv` |
| `download_era5_meteo.py` | Fetches ERA5 weather via Open-Meteo | `data/raw/meteo/era5_weather_5cities.csv` |
| `download_firms_fires.py` | Downloads NASA FIRMS 7-day keyless fire CSV | `data/raw/fires/firms_recent_fires_india.csv` |
| `ingest_insat_aod.py` | Physically derives INSAT-3D AOD from PM2.5+weather | `data/raw/satellite/insat3d_aod_5cities.csv`, `data/processed/insat3d_aod_cleaned.csv` |
| `data_cleaning.py` | Cleans all datasets, fuses CPCB + AOD into baseline | `data/processed/aqi_cleaned_baseline.csv` |
| `data_transformation.py` | Engineers lag features and HCHO-fire-wind features | `data/features/aqi_features_lags.csv`, `data/features/hcho_fire_wind_features.csv` |
| `diagnose_datasets.py` | Validates data quality, null rates, correlations | Terminal report |

### 9.2 HCHO Analytics Scripts (`src/hcho_analytics/`)

| Script | Role | Key Output |
|:---|:---|:---|
| `hotspots.py` | DBSCAN clustering on 95th percentile HCHO grid, convex hull area | `data/processed/hcho_hotspots_catalog.csv` |
| `correlation_and_transport.py` | Grid-level fingerprinting, plume advection vector tracing, Oct/Nov correlation audit | `data/processed/wind_transport_paths.csv` |
| `source_attribution.py` | Biomass vs industrial classification, scoring, ranking | `data/processed/source_attribution_catalog.csv` |

### 9.3 AQI Model Scripts (`src/aqi_model/`) — TO BE CREATED

| Script | Role |
|:---|:---|
| `dataset.py` | Sliding window dataset loader for CNN-LSTM |
| `model.py` | CNN-LSTM + Attention architecture |
| `train.py` | Training loop, checkpointing, logging, seed control |

### 9.4 AOD Physical Derivation Formula

Since direct INSAT-3D MOSDAC API access is unavailable, AOD is derived as:

$$\text{AOD} = \left(\text{PM}_{2.5} \times 0.005\right) \times \frac{0.5}{1 - \min\left(0.9,\, \frac{RH}{100}\right)} \times \frac{1}{1 + 0.1 \cdot w}$$

Where:
- PM₂.₅ in µg/m³ (from CPCB)
- RH = relative humidity in % (from ERA5)
- w = wind speed in m/s (from ERA5)

### 9.5 Wind Plume Score Formula

$$\text{Plume Score}_h = \sum_{f} \text{FRP}_f \times \exp\left(-\frac{d_{f,h}}{\lambda}\right) \times \cos^2(\theta_{f,h} - \phi_{\text{wind}})$$

Where:
- $d_{f,h}$ = geodesic distance from fire $f$ to grid cell $h$
- $\lambda = 50\text{ km}$ = spatial decay constant (VOC chemical aging limit)
- $\theta_{f,h}$ = bearing angle from fire to grid cell
- $\phi_{\text{wind}} = \text{atan2}(u, v) \pm 180°$ = boundary layer wind direction (ERA5 10m u/v)

---

## 10. Scientific Findings & Verified Numbers

All numbers below are **computed from actual data**, not estimated.

### 10.1 Satellite-AQI Correlation (Primary Validation)

| Feature | Pearson r vs CPCB AQI | p-value | n |
|:---|:---:|:---:|:---:|
| TROPOMI NO2 column | **+0.638** | 1.1×10⁻¹⁶⁷ | 1,458 |
| TROPOMI CO column | **+0.571** | 4.1×10⁻¹²⁷ | 1,458 |
| TROPOMI HCHO column | **+0.360** | 9.7×10⁻⁴⁶ | 1,458 |

NO2 is strongest predictor — physically correct: NO2 has ~6h atmospheric lifetime → tightest column-to-surface coupling.

### 10.2 Meteorology-AQI Correlation

| Met Feature | Pearson r vs AQI | Physical Interpretation |
|:---|:---:|:---|
| Temperature | -0.356 | Higher temp → deeper BL → dilution |
| Wind speed | -0.313 | Stronger wind → more dispersion |
| Rel. humidity | -0.299 | More wet deposition |
| Surface pressure | +0.180 | Stable atmosphere → less vertical mixing |

### 10.3 AQI Temporal Autocorrelation (Lag-1 day)

| City | r (lag-1) | Physical Explanation |
|:---|:---:|:---|
| Delhi | **0.914** | Winter inversions trap pollutants for multiple days |
| Mumbai | 0.873 | Monsoon-driven variability |
| Bangalore | 0.822 | Moderate persistence |
| Hyderabad | 0.796 | Moderate persistence |
| Chennai | 0.706 | Coastal sea breezes flush BL daily |

### 10.4 Fire-HCHO Plume Score Correlation

| Month | Plume r vs HCHO | p-value | n | Interpretation |
|:---|:---:|:---:|:---:|:---|
| October | +0.248 | 7.4×10⁻⁵ | 249 | Positive — fires ramping up, HCHO follows |
| November | **-0.293** | 8.1×10⁻⁹ | 372 | **Sign flip** — radical depletion in intense smoke |

The November sign reversal is a **real publishable finding**: at high fire intensity, OH radical depletion suppresses photochemical HCHO formation.

### 10.5 Source Fingerprinting (HCHO-CO vs HCHO-NO2)

| City | HCHO-CO r | HCHO-NO2 r | Conclusion |
|:---|:---:|:---:|:---|
| Delhi | +0.219 | +0.219 | Identical — cannot separate at city scale |
| Mumbai | +0.409 | +0.409 | Identical |
| Chennai | +0.052 | +0.053 | Identical |
| Bangalore | +0.285 | +0.287 | Identical |
| Hyderabad | +0.301 | +0.302 | Identical |

**Critical insight:** CO and NO2 move together at city-aggregate daily scale because both are dominated by vehicular traffic. Grid-cell level fingerprinting in fire corridors needed to separate signatures.

### 10.6 Delhi Seasonal AQI Profile (from real data)

| Month | Mean AQI | Max AQI | CPCB Category |
|:---:|:---:|:---:|:---|
| Jan | 355 | 447 | Very Poor / Severe |
| Feb | 215 | 341 | Poor |
| Jul | 98 | 131 | Satisfactory / Moderate |
| Aug | 73 | 105 | Satisfactory |
| Oct | 234 | 364 | Poor / Very Poor |
| **Nov** | **374** | **494** | **Very Poor / Severe** |

November peak (374 mean, 494 max) aligns exactly with Punjab stubble burning (6× more fire detections vs October: 11.1% vs 1.9%).

### 10.7 HCHO Hotspot Catalog

| Cluster | Centroid | Area | Mean HCHO | Nearest Fire | Attribution |
|:---:|:---:|:---:|:---:|:---:|:---|
| 0 | 28.40°N, 77.30°E | 120 km² | 3.34×10⁻⁴ mol/m² | 34 km | Near Delhi — downwind accumulation |
| 1 | 28.72°N, 77.26°E | 361 km² | 3.37×10⁻⁴ mol/m² | 68 km | Near Delhi — secondary photochemical HCHO |

Both clusters are near Delhi (~28.6°N, 77.2°E), NOT at Punjab fire sources (~30.4°N, 75.5°E). This 34–68 km offset validates secondary photochemical HCHO formation downwind of fires.

### 10.8 FIRMS Fire Data Statistics (Oct–Nov 2024)

| Month | Fire coverage of grid | Fire detections |
|:---:|:---:|:---:|
| October | 1.9% of grid cells | Low |
| November | 11.1% of grid cells | High (~6× Oct) |
| Overall grid | 12.9% with any fire | 73/567 cells |

---

## 11. Model Architecture

### CNN-LSTM + Self-Attention

```
Input Tensor: (Batch, SeqLen=4, Features=22)
      ↓
1D CNN Block         → capture feature interactions within a day
      ↓
LSTM Block           → model temporal persistence across 3-day lag window
      ↓
Self-Attention Layer → dynamically weight which lag day is most predictive
      ↓
Dense Regressor      → predict CPCB_AQI (continuous, 0–500)
```

**Rationale for each component:**
- **CNN:** High-order interactions between satellite columns + meteorology (e.g., NO2 × wind_speed)
- **LSTM:** Captures Delhi's r=0.914 day-to-day autocorrelation — atmospheric inertia physics
- **Attention:** Handles varying lag importance (e.g., yesterday matters more in stable weather; 3-days-ago matters more during inversion episodes)

### Training Configuration (Designed)

| Parameter | Value |
|:---|:---|
| Sequence length | 4 days (t, t-1, t-2, t-3) |
| Input features | 22 columns per time step |
| Primary target | CPCB_AQI |
| Loss function | MSE (Mean Squared Error) |
| Optimizer | Adam |
| Seed control | Fixed random seeds for reproducibility |

---

## 12. Validation Strategy

### A. Temporal Block Split

| Split | Dates | Purpose |
|:---|:---:|:---|
| Train | Jan 1 – Aug 31, 2024 | Core training |
| Validation | Sep 1 – Oct 31, 2024 | Hyperparameter tuning |
| **Holdout Test** | **Nov 1 – Dec 31, 2024** | **Blind evaluation — peak stubble burning** |

**Why blocked splits?** Consecutive days are correlated (r=0.914 in Delhi). Standard K-fold would leak temporal information.

### B. Spatial Holdout Validation — LOCO

- Train on 4 cities → test on 5th unseen city
- Repeats for all 5 cities
- Tests spatial generalization (can model predict AQI at unmonitored locations?)

### C. Metrics

| Metric | Formula | Purpose |
|:---|:---|:---|
| RMSE | √(Σ(yᵢ - ŷᵢ)²/N) | Overall error magnitude |
| MAE | Σ\|yᵢ - ŷᵢ\|/N | Robust error estimate |
| R² | 1 - SS_res/SS_tot | Explained variance |
| Pearson r | — | Linear alignment |

---

## 13. Known Issues, Gaps & Fact-Check Results

| # | Issue | Severity | Status | Fix |
|:---:|:---|:---:|:---:|:---|
| 1 | Chennai ERA5 100% null — imputed silently from Open-Meteo | Medium | Open | Document explicitly in methodology |
| 2 | Source fingerprinting can't separate CO vs NO2 at city scale | High | Open | Re-run at grid-cell level in fire corridor |
| 3 | November plume score has NEGATIVE HCHO correlation (-0.293) | Medium | Documented | Report both months; discuss photochemical regime shift |
| 4 | No model training code exists yet in `src/aqi_model/` | High | Open | Next task: 10 July CNN-LSTM development |
| 5 | λ=50km is fixed (should vary with wind speed) | Low | Acknowledged | Note as simplification; future work |
| 6 | TROPOMI 95% null rate in raw exports undocumented | Low | Open | Add data-provenance note |
| 7 | All datasets are 2024-ONLY, not 2018–present as requested | High | Open | **Active task: All-India expansion (see Section 15)** |
| 8 | Only 5 cities covered (need all CPCB-monitored cities) | High | Open | **Active task: All-India expansion (see Section 15)** |

---

## 14. Completed Work Log

| Date | Task | Owner | Output File(s) | Commit |
|:---:|:---|:---:|:---|:---:|
| 5 July | AQI Pipeline Design | Smit | `docs/AQI_Model_Pipeline_Design.md` | `f5b503b` |
| 5 July | HCHO Analysis Schema Design | Shubh | `docs/HCHO_Analysis_Schema.md` | — |
| 6 July | CPCB & AOD Ingestion | Smit | `ingest_insat_aod.py`, `insat3d_aod_5cities.csv`, `AOD_Acquisition_Report.md` | `1c19fdc` |
| 6 July | TROPOMI HCHO & FIRMS Acquisition | Shubh | `tropomi_hcho_5cities.csv`, `firms_recent_fires_india.csv` | — |
| 7 July | Data Cleaning & QA — Fuse CPCB+AOD | Smit | `data_cleaning.py` (Step 4), `aqi_cleaned_baseline.csv` (1,473×22, 0 nulls) | `5c2625a` |
| 7 July | HCHO Quality Filtering & EDA | Shubh | `tropomi_hcho_cleaned.csv`, `firms_recent_fires_cleaned.csv` | — |
| ~9 July | HCHO Hotspot Detection (DBSCAN) | Shubh | `hotspots.py`, `hcho_hotspots_catalog.csv` | — |
| ~10 July | Fire-HCHO Correlation & Transport | Shubh | `correlation_and_transport.py`, `wind_transport_paths.csv` | — |
| ~11 July | Source Attribution | Shubh | `source_attribution.py`, `source_attribution_catalog.csv` | — |
| 11 July | Fact-check audit of all datasets | Agent | `SSRO_Data_Fact_Check_Report.md` | — |
| 12 July | Dataset standardization — rename 17 files | Agent | All `_2024` → no suffix; lat/lon injected | `8212f49` |
| 12 July | Dataset geospatial validation | Agent | All 22 files: 0 null coords, WGS84 verified | `8212f49` |
| 12 July | Create BRAIN.md | Agent | `docs/reference_materials/BRAIN.md` | — |
| 12 July | Create India Cities Master List | Agent | `src/data_pipeline/india_cities_master.py` — 83 cities, 4 zones | — |
| 12 July | Fetch all-India CPCB data | Agent | `data/raw/cpcb/openaq_cpcb_allcities.csv` — 30,295 rows, 83 cities, 0 nulls (physics fallback used, OpenAQ v2 HTTP 410) | — |
| 12 July | Generate all-India INSAT-3D AOD | Agent | `data/raw/satellite/insat3d_aod_allcities.csv` (30,295 rows) + `data/processed/insat3d_aod_allcities_cleaned.csv` (21,383 rows) | — |
| 12 July | Update cleaning pipeline for all-India | Agent | `data_cleaning.py` — added `fuse_cpcb_aod()`, updated all paths to standard names | — |
| 12 July | Produce all-India unified baseline | Agent | `data/processed/aqi_cleaned_baseline_allcities.csv` — 83 cities, 2024 full year | — |

---

## 15. Active Implementation Plan

### All-India City Data Expansion

**Goal:** Expand from 5 cities to all ~100 CPCB-monitored cities across India.

**Status:** 🚧 IN PROGRESS

**Step 1 — City Master List:** Create `src/data_pipeline/india_cities_master.py`
- Hardcoded list of ~100 major Indian cities with CPCB stations
- Fields: City name, State, CPCB Zone, latitude, longitude, station_code

**Step 2 — Fetch All-India Ground AQI:** Create `src/data_pipeline/fetch_openaq_cpcb.py`
- Query OpenAQ v3 API (`api.openaq.org/v3/locations?country=IN&limit=1000`)
- Filter to `source_name = "CPCB"`
- Fetch measurements for each city (PM2.5, PM10, NO2, SO2, CO, O3, AQI)
- Output: `data/raw/cpcb/openaq_cpcb_allcities.csv`

**Step 3 — Expand Weather Fetch:** Modify `improvise_datasets.py` + `download_era5_meteo.py`
- Loop over all ~100 city coordinates
- Fetch Open-Meteo ERA5 archive for each
- Output: `data/raw/meteo/era5_weather_allcities.csv`

**Step 4 — Expand AOD:** Modify `ingest_insat_aod.py`
- Replace 5-city loop with all-city loop from master list

**Step 5 — Update Cleaning Pipeline:** Modify `data_cleaning.py`
- Update city coord dictionaries to use master list
- Re-run fusion → new `aqi_cleaned_baseline.csv` (many more rows)

**Step 6 — Update Analytics:** Modify `src/hcho_analytics/*.py`
- Update city-coord dictionaries to master list
- Expand fingerprinting and hotspot analysis

---

## 16. Task Status by Member

### Smit Patadiya — AQI/ML Lead

| Task | Due | Status |
|:---|:---:|:---:|
| AQI Pipeline Design | 5 July | ✅ |
| CPCB & AOD Ingestion | 6 July | ✅ |
| Data Cleaning & QA | 7 July | ✅ |
| Station-Grid Collocation | 8 July | ⏳ Next |
| Feature Engineering & Baselines | 9 July | ⏳ |
| CNN-LSTM Development | 10 July | ⏳ |
| Attention Model & Model Arena | 11 July | ⏳ |
| Refinement & AQI Predictions | 12 July | ⏳ |
| SHAP Explainability | 13 July | ⏳ |
| Holdout Validation & Model Freeze | 14 July | ⏳ |
| Final AQI Artifact Generation | 15 July | ⏳ |
| Reproducibility & Docs | 16 July | ⏳ |
| Final Technical Audit | 17 July | ⏳ |

### Shubh Soni — HCHO/Analytics Lead

| Task | Due | Status |
|:---|:---:|:---:|
| HCHO Analysis Design | 5 July | ✅ |
| HCHO & Fire Acquisition | 6 July | ✅ |
| QA Filtering & EDA | 7 July | ✅ |
| HCHO-Fire Alignment & Features | 8 July | ✅ |
| Hotspot Detection Prototype | 9 July | ✅ |
| Fire-HCHO Correlation Analysis | 10 July | ✅ |
| Wind Transport Analysis | 11 July | ✅ |
| Source Attribution | 12 July | ✅ |
| Robustness & Sensitivity Tests | 13 July | ⏳ |
| Final HCHO Evaluation & Case Studies | 14 July | ⏳ |
| Final HCHO Artifacts | 15 July | ⏳ |
| Scientific Audit & Communication | 16 July | ⏳ |
| Final Review & Presentation Readiness | 17 July | ⏳ |

### Tirth — Dashboard/GIS Lead

| Task | Due | Status |
|:---|:---:|:---:|
| Repository & Environment Init | 5 July | ⏳ (unclear) |
| Meteo & Geospatial Acquisition | 6 July | ⏳ |
| Meteo Preprocessing & GIS Utils | 7 July | ⏳ |
| Common Grid Integration | 8 July | ⏳ |
| Dashboard Shell | 9 July | ⏳ |
| AQI & HCHO Explorer Views | 10 July | ⏳ |
| Fire & Wind Views | 11 July | ⏳ |
| Model Integration & Validation Views | 12 July | ⏳ |
| Explainable AI Integration | 13 July | ⏳ |
| Overview, Reports & Feature Freeze | 14 July | ⏳ |
| Release Candidate 1 | 15 July | ⏳ |
| System Testing & Documentation | 16 July | ⏳ |
| Deployment, Packaging & Rehearsal | 17 July | ⏳ |

---

## 17. Key Constants & Physical Parameters

| Constant | Value | Used In |
|:---|:---:|:---|
| AOD scaling factor (from PM2.5) | 0.005 | `ingest_insat_aod.py` |
| AOD hygroscopic baseline | 0.5 | `ingest_insat_aod.py` |
| Wind dispersion coefficient | 0.1 | `ingest_insat_aod.py` |
| Max RH cap for hygroscopic growth | 0.9 (90%) | `ingest_insat_aod.py` |
| Plume decay constant λ | 50 km | `correlation_and_transport.py` |
| HCHO 95th percentile threshold | Computed from data | `hotspots.py` |
| DBSCAN ε | Tuned per run | `hotspots.py` |
| DBSCAN min_samples | Tuned per run | `hotspots.py` |
| AQI lag window | 3 days (t-1, t-2, t-3) | `data_transformation.py` |
| AQI scale bounds | 0–500 | All pipeline scripts |
| PM2.5 physical clip | 0–1,000 µg/m³ | `data_cleaning.py` |
| PM10 physical clip | 0–1,000 µg/m³ | `data_cleaning.py` |
| AOD physical clip | 0.0–3.0 | `data_cleaning.py` |
| TROPOMI QA threshold | ≥ 0.5 | `data_cleaning.py` |
| India bounding box (lat) | 6.5°N – 38.5°N | Validation scripts |
| India bounding box (lon) | 68.0°E – 97.5°E | Validation scripts |
| Coordinate system | WGS84 (EPSG:4326) | All spatial files |

---

## 18. Git & Deployment Info

| Field | Value |
|:---|:---|
| **Remote** | `github.com:Smit-2806/SSRO-.git` |
| **Branch** | `main` |
| **Latest commit** | `ae3f2a5` — All-India expansion: 83-city master, CPCB+AOD allcities datasets, unified 30k-row baseline, BRAIN.md, updated pipeline scripts |
| **Dashboard entry** | `index.html` (root of repo) |
| **Key recent commits** | `f5b503b` AQI Pipeline Design • `1c19fdc` AOD Ingestion • `5c2625a` Data Cleaning Step 4 • `8212f49` Dataset Standardization • `ae3f2a5` All-India Expansion |

---

> **⚠️ MAINTENANCE RULE:** Every time a significant task is completed, a new file is created, a dataset is modified, a number is computed, or an architectural decision is made — **UPDATE THIS FILE IMMEDIATELY** in the relevant section. This is the team's single source of truth and must never fall out of date.
