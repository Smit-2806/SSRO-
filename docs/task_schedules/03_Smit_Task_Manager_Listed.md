# Smit Patadiya --- Person-Specific Task Manager

**Role:** Data Engineering and AQI/ML Lead\
**Execution Window:** 5 July 2026 -- 17 July 2026

## Primary Ownership

Smit owns the complete Surface AQI pipeline: INSAT-3D AOD and CPCB data
preparation, station-grid collocation, AQI feature engineering, baseline
benchmarking, CNN-LSTM + Attention development, model selection, holdout
validation, explainability, uncertainty analysis, prediction generation,
reproducibility, and technical explanation of the model.

## Daily Task Plan

### 5 July --- AQI Pipeline Design

**Tasks** - Finalize AQI targets and input feature schema. - Inspect
INSAT-3D AOD and CPCB data structures. - Define artifact conventions for
raw data, processed data, features, models, metrics, and predictions. -
Define model evaluation and validation strategy.

**Expected output:** AQI pipeline specification and data contract.

### 6 July --- CPCB and AOD Acquisition

**Tasks** - Acquire CPCB AQI and pollutant observations for the selected
proof-of-concept period. - Begin INSAT-3D AOD acquisition. - Validate
station IDs, coordinates, timestamps, units, and coverage. - Produce
missing-data and coverage summaries.

**Expected output:** Raw CPCB/AOD datasets and acquisition report.

### 7 July --- Data Cleaning and QA

**Tasks** - Remove duplicates and invalid observations. - Normalize
timestamps and coordinate formats. - Handle missing values using
documented rules. - Apply AOD QA and cloud filtering. - Validate CPCB
pollutant ranges and unit consistency.

**Expected output:** Cleaned CPCB and AOD datasets.

### 8 July --- Station-Grid Collocation

**Tasks** - Map CPCB stations to target grid cells. - Align satellite
observations and ground measurements temporally. - Merge meteorological
covariates supplied by Tirth. - Check data leakage, coverage, and
station representation. - Create first model-ready training table.

**Expected output:** Harmonized AQI training dataset.

### 9 July --- Feature Engineering and Baselines

**Tasks** - Create lagged AQI and pollutant features. - Create rolling
and moving averages. - Add seasonal and day-of-year encoding. -
Integrate meteorological features. - Train feasible baseline models and
record comparable metrics.

**Expected output:** Feature matrix and baseline benchmark table.

### 10 July --- CNN-LSTM Development

**Tasks** - Build sequential input windows. - Define
train/validation/test splits without leakage. - Implement CNN-LSTM. -
Create training loop, checkpoints, logging, and seed control. - Run
initial experiments and diagnose tensor/data issues.

**Expected output:** Working CNN-LSTM training pipeline.

### 11 July --- Attention Model and Model Arena

**Tasks** - Add Attention to the CNN-LSTM pipeline. - Train CNN-LSTM +
Attention. - Compare with baseline models. - Calculate RMSE, MAE, R²,
and Pearson correlation. - Select candidates for tuning.

**Expected output:** Model comparison results and candidate model.

### 12 July --- Refinement and AQI Predictions

**Tasks** - Tune important hyperparameters. - Inspect residuals and
error patterns. - Diagnose overfitting and underfitting. - Generate
pilot-city and selected-date predictions. - Export dashboard-ready
prediction files.

**Expected output:** Refined model and prediction artifacts.

### 13 July --- Explainability and Confidence

**Tasks** - Implement SHAP analysis for suitable model components or
surrogate explanations. - Generate global feature-importance results. -
Generate local explanations for selected predictions. - Analyze
Attention behavior where scientifically meaningful. - Develop confidence
or uncertainty indicators.

**Expected output:** Explainability package and confidence outputs.

### 14 July --- Holdout Validation and Model Freeze

**Tasks** - Run spatial holdout validation on unseen stations where
feasible. - Run temporal holdout validation. - Finalize model comparison
table. - Document model-selection rationale. - Freeze production model
and inference schema.

**Expected output:** Final validation report and frozen model.

### 15 July --- Final AQI Artifact Generation

**Tasks** - Generate final daily AQI predictions. - Generate city-level
trend files. - Generate AQI map layers. - Export metrics, model package,
and inference assets. - Verify that outputs can be reproduced from
scripts.

**Expected output:** Final AQI artifact package.

### 16 July --- Reproducibility and Documentation

**Tasks** - Re-run critical experiments and inference tests. - Clean
notebooks and scripts. - Remove dead code and document dependencies. -
Prepare methodology, architecture, model-selection, validation, and
uncertainty explanations. - Support integration troubleshooting.

**Expected output:** Reproducible AQI pipeline and technical
documentation.

### 17 July --- Final Technical Audit

**Tasks** - Verify model files and versions. - Verify metrics and
prediction outputs. - Verify backup outputs for offline demo. - Prepare
judge answers on model choice, spatial-temporal learning, Attention,
validation, generalization, and uncertainty. - Participate in complete
rehearsal.

**Expected output:** Submission-ready AQI pipeline and presentation
readiness.

## Completion Checklist

-   [ ] CPCB dataset acquired and cleaned.
-   [ ] INSAT-3D AOD acquired and QA-filtered.
-   [ ] Station-grid collocation complete.
-   [ ] Model-ready AQI table generated.
-   [ ] Lag.
-   Rolling.
-   Seasonal.
-   And meteorological features generated.
-   [ ] Baseline models benchmarked.
-   [ ] CNN-LSTM implemented.
-   [ ] CNN-LSTM + Attention implemented.
-   [ ] RMSE.
-   MAE.
-   R².
-   And Pearson R calculated.
-   [ ] Spatial and temporal holdout validation complete.
-   [ ] Explainability outputs generated.
-   [ ] Confidence/uncertainty outputs generated.
-   [ ] Final model frozen.
-   [ ] AQI maps.
-   Trends.
-   Predictions.
-   And metrics exported.
-   [ ] Reproducibility and judge Q&A prepared.
