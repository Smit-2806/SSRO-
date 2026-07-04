# Team SSRO --- Complete Task Scheduling and Task Assignment Plan

**Hackathon:** Bharatiya Antariksh Hackathon 2026\
**Problem Statement:** Development of Surface AQI & Identification of
HCHO Hotspots over India using Satellite Data\
**Execution Window:** 5 July 2026 -- 17 July 2026\
**Team Members:** Smit Patadiya, Shubh Soni, Tirth\
**Execution Strategy:** Parallel development with daily integration
checkpoints and a feature freeze on 14 July.

## 1. Team Responsibility Model

### Smit --- Data Engineering and AQI/ML Lead

Smit owns the Surface AQI prediction pipeline. His responsibilities
cover INSAT-3D AOD and CPCB data preparation, AQI feature engineering,
model benchmarking, CNN-LSTM + Attention development, validation,
explainability, uncertainty analysis, and generation of final AQI
artifacts.

### Shubh --- HCHO Intelligence, Analytics and Scientific Validation Lead

Shubh owns the HCHO intelligence pipeline. His responsibilities cover
TROPOMI HCHO processing, MODIS/VIIRS fire analysis, hotspot detection,
fire-HCHO correlation, wind-transport analysis, source attribution,
robustness testing, scientific interpretation, and preparation of
results and judge-facing technical explanations.

### Tirth --- Geospatial, Dashboard and Integration Lead

Tirth owns the geospatial and product integration layer. His
responsibilities cover meteorological preprocessing, target-grid
preparation, GIS utilities, dashboard architecture, map visualization,
frontend implementation, model-output integration, reports, deployment,
testing, and final submission packaging.

## 2. Day-wise Team Schedule

### 5 July --- Architecture and Project Initialization

**Smit** - Finalize the Surface AQI input schema and target variables. -
Inspect INSAT-3D AOD and CPCB dataset structures. - Define raw,
processed, feature, model, and prediction artifact conventions. -
Document the AQI pipeline inputs, outputs, dependencies, and validation
targets.

**Shubh** - Finalize the HCHO analysis schema. - Inspect TROPOMI HCHO
and FIRMS MODIS/VIIRS structures. - Define expected hotspot,
correlation, transport, and source-attribution outputs. - Establish
scientific assumptions and analysis questions for the HCHO branch.

**Tirth** - Initialize the Git repository, branches, environment files,
dependency management, and shared configuration. - Define dashboard
information architecture and route structure. - Define geospatial layer
contracts for AQI, HCHO, fire, wind, and validation outputs. - Prepare
the common project folder structure.

**Milestone:** Architecture, data contracts, repository structure, and
ownership frozen.

### 6 July --- Data Acquisition

**Smit** - Acquire pilot-period CPCB AQI and pollutant observations. -
Begin INSAT-3D AOD ingestion. - Verify timestamps, station identifiers,
coordinates, and variable availability. - Produce an acquisition log and
missing-data summary.

**Shubh** - Acquire TROPOMI HCHO observations. - Acquire MODIS/VIIRS
active-fire records. - Inspect QA values, FRP, confidence, date-time
coverage, and coordinate consistency. - Define the common observation
period for HCHO-fire analysis.

**Tirth** - Acquire required ERA5/IMDAA meteorological variables. -
Prepare India and pilot-region administrative boundaries. - Create the
initial common spatial grid. - Validate CRS, geometry, and temporal
coverage.

**Milestone:** Essential datasets available for the selected
proof-of-concept period.

### 7 July --- Cleaning and Quality Control

**Smit** - Clean CPCB and AOD observations. - Remove duplicates and
invalid coordinates. - Handle missingness and document imputation or
exclusion rules. - Apply AOD QA and cloud-related filtering. - Normalize
timestamps.

**Shubh** - Apply HCHO QA filtering. - Clean fire observations and
standardize fire coordinates and timestamps. - Filter low-confidence
fire detections where required. - Perform initial exploratory analysis
of HCHO distributions, fire activity, and seasonal behavior.

**Tirth** - Preprocess wind, temperature, humidity, pressure, rainfall,
and PBL variables. - Standardize CRS and spatial resolution. - Build
reusable interpolation, regridding, clipping, and export utilities. -
Produce quality-control summaries for meteorological layers.

**Milestone:** Cleaned and quality-controlled individual datasets.

### 8 July --- Spatial-Temporal Harmonization

**Smit** - Spatially collocate CPCB stations with AOD grid cells. -
Align daily or hourly temporal windows. - Prepare the first AQI
model-ready training table. - Run coverage and leakage checks.

**Shubh** - Align HCHO and fire observations in space and time. -
Compute fire counts and FRP aggregates. - Generate nearest-fire distance
and fire-buffer features. - Prepare hotspot-analysis and
correlation-ready tables.

**Tirth** - Regrid meteorological data to the target grid. - Merge wind
and meteorological covariates into AQI and HCHO branches. - Verify
spatial-temporal overlap across all sources. - Produce integration
diagnostics.

**Milestone:** First harmonized multi-source analytical datasets.

### 9 July --- Feature Engineering and First Prototypes

**Smit** - Create AQI lag features, rolling means, moving averages,
seasonal encodings, and meteorological covariates. - Train baseline
models such as Linear/Ridge Regression, Random Forest, Gradient
Boosting, XGBoost, SVR, and MLP as feasible. - Record comparable metrics
and training times.

**Shubh** - Implement percentile-based HCHO anomaly detection. -
Implement DBSCAN hotspot clustering. - Compare hotspot definitions and
generate initial cluster statistics. - Export initial hotspot geometries
and metadata.

**Tirth** - Build dashboard shell and navigation. - Implement reusable
map components. - Load mock or sample AQI, HCHO, fire, and wind
layers. - Establish shared chart, map, filter, and data-loading
patterns.

**Milestone:** Baseline AQI results, initial HCHO hotspots, and working
dashboard shell.

### 10 July --- Core Model and Analytics Development

**Smit** - Convert AQI data into sequential training windows. -
Implement CNN-LSTM architecture. - Establish training, checkpointing,
logging, and reproducibility workflow. - Run the first complete
deep-learning experiment.

**Shubh** - Conduct fire-HCHO correlation analysis using FRP, fire
count, distance, and temporal lags. - Compare same-day and lagged
relationships. - Identify high-value case-study regions and periods. -
Export correlation summaries.

**Tirth** - Implement AQI Explorer and HCHO Explorer. - Add map layers,
date controls, city/state filters, legends, tooltips, and summary
cards. - Prepare interfaces for real analytical artifacts.

**Milestone:** Both scientific objectives operational at prototype
level.

### 11 July --- Advanced Modeling and Wind Transport

**Smit** - Add the Attention mechanism to the CNN-LSTM pipeline. - Train
and compare CNN-LSTM + Attention against baselines. - Evaluate RMSE,
MAE, R², and Pearson correlation. - Select candidates for refinement.

**Shubh** - Derive wind speed and direction from U/V components. -
Develop downwind enhancement logic. - Implement wind-transport vector
analysis and pathway interpretation. - Link hotspot clusters with
potential upwind fire activity.

**Tirth** - Build Fire Correlation and Wind Transport views. - Implement
wind-vector or trajectory visualization. - Add layer controls and
synchronized map/chart interactions. - Integrate Shubh's intermediate
analytical outputs.

**Milestone:** Core AQI model and HCHO/fire/wind intelligence pipeline
complete.

### 12 July --- Refinement, Source Attribution and Integration

**Smit** - Refine hyperparameters. - Diagnose residuals, bias, and
overfitting. - Generate AQI predictions for pilot locations and selected
dates. - Export model-ready dashboard artifacts.

**Shubh** - Perform source-attribution analysis. - Separate fire-linked
hotspots from potentially non-fire hotspots. - Rank hotspot clusters
using concentration, persistence, fire proximity, FRP, and transport
evidence. - Generate structured hotspot metadata.

**Tirth** - Build benchmark, validation, and statistics views. - Connect
AQI and HCHO artifacts to dashboard data loaders or API layer. -
Validate map performance and data consistency.

**Milestone:** End-to-end scientific outputs visible in the dashboard.

### 13 July --- Explainability and Scientific Validation

**Smit** - Implement SHAP analysis. - Generate global and local
feature-importance outputs. - Analyze Attention behavior where
technically meaningful. - Develop prediction confidence or uncertainty
indicators.

**Shubh** - Test hotspot robustness across thresholds and clustering
settings. - Perform fire-HCHO temporal-lag sensitivity analysis. -
Evaluate transport-path plausibility against wind fields. - Document
scientific interpretation and limitations.

**Tirth** - Build Explainable AI and Validation views. - Integrate SHAP
plots, metrics, confidence information, and validation summaries. -
Ensure consistent visual explanation across dashboard pages.

**Milestone:** Explainability and scientific validation integrated.

### 14 July --- Final Validation and Feature Freeze

**Smit** - Run spatial holdout and temporal holdout experiments. -
Finalize model-comparison table. - Document final-model selection
rationale. - Freeze the production model and prediction schema.

**Shubh** - Finalize hotspot evaluation. - Implement IoU/overlap
assessment where suitable reference zones are available. - Check
multi-source continuity and overlap. - Finalize case-study
interpretation and scientific conclusions.

**Tirth** - Complete Overview and Reports pages. - Improve responsive
layout, legends, loading states, tooltips, and error handling. - Freeze
features at end of day.

**Milestone:** Feature-complete integrated prototype; no major new
features after this date.

### 15 July --- Final Artifacts and Release Candidate 1

**Smit** - Generate final daily AQI maps and city-level trends. - Export
predictions, metrics, selected model package, and inference assets. -
Verify reproducible generation of outputs.

**Shubh** - Generate final HCHO hotspot maps. - Export fire-correlation
outputs, transport pathways, source-attribution summaries, and
scientific findings. - Prepare concise insight statements backed by
outputs.

**Tirth** - Optimize integration and deployment pipeline. - Resolve map,
API, data-loading, and performance issues. - Add report/download
assets. - Produce Release Candidate 1.

**Milestone:** Release Candidate 1 available.

### 16 July --- System Hardening and Documentation

**Smit** - Re-run critical model tests. - Verify reproducibility. -
Clean notebooks and scripts. - Prepare model methodology and
architecture documentation.

**Shubh** - Cross-check all scientific claims against actual results. -
Prepare methodology, limitations, results narrative, and judge Q&A
material. - Verify consistency between maps, statistics, and
presentation claims.

**Tirth** - Perform full-system testing and deployment verification. -
Polish UI and demo flow. - Prepare screenshots, README, setup
instructions, and backup demo assets.

**Milestone:** Stable submission candidate with documentation and backup
paths.

### 17 July --- Final Audit, Submission and Rehearsal

**Smit** - Audit model files, metrics, inference outputs, architecture
explanation, and backup artifacts. - Prepare concise answers on model
selection, validation, generalization, and uncertainty.

**Shubh** - Audit hotspot claims, correlation results, transport
interpretation, source attribution, and limitations. - Finalize
scientific speaking points and judge Q&A.

**Tirth** - Audit deployment and repository. - Package dashboard,
reports, presentation assets, and submission material. - Conduct
complete demo rehearsal and verify backup presentation route.

**Milestone:** Final submission package, stable demo, and rehearsed
technical presentation.

## 3. Execution Rules

1.  Conduct a 15-minute daily synchronization meeting before work
    starts.
2.  Every member must push or submit usable artifacts before the daily
    integration checkpoint.
3.  Data contracts and output schemas must not change without informing
    dependent owners.
4.  Use sample/mock outputs only until real artifacts are available;
    replace them progressively.
5.  Freeze major features after 14 July.
6.  Keep 15--17 July focused on reliability, evidence, documentation,
    presentation, and contingency.
7.  Every scientific claim shown in the dashboard or presentation must
    be traceable to a generated result.
8.  Maintain reproducible scripts and avoid manual-only transformations
    in the final pipeline.

## 4. Final Deliverables

-   Harmonized multi-source pilot dataset.
-   Surface AQI prediction pipeline and selected model.
-   AQI predictions.
-   Maps.
-   Trends.
-   Confidence information.
-   And. validation metrics.
-   HCHO hotspot detection outputs and cluster metadata.
-   Fire-HCHO correlation analysis.
-   Wind-transport and source-attribution analysis.
-   Explainable AI outputs.
-   Interactive decision-support dashboard.
-   Technical documentation and reproducibility instructions.
-   Final presentation.
-   Demo flow.
-   Judge Q&A preparation.
-   And submission. package.
