# Tirth --- Person-Specific Task Manager

**Role:** Geospatial, Dashboard and Integration Lead\
**Execution Window:** 5 July 2026 -- 17 July 2026

## Primary Ownership

Tirth owns the geospatial engineering and integrated decision-support
product: meteorological data preparation, common grid and GIS utilities,
dashboard architecture, AQI/HCHO/fire/wind visualization, frontend
implementation, analytical-output integration, validation and
explainability views, reporting, deployment, system testing,
documentation, and final submission packaging.

## Daily Task Plan

### 5 July --- Repository, Environment and Product Architecture

**Tasks** - Initialize repository and branch strategy. - Create shared
folder structure and configuration conventions. - Prepare
environment/dependency files. - Define dashboard route structure and
information architecture. - Define map-layer and analytical artifact
contracts with Smit and Shubh.

**Expected output:** Working project foundation and dashboard
specification.

### 6 July --- Meteorological and Geospatial Acquisition

**Tasks** - Acquire required ERA5/IMDAA meteorological variables for the
agreed period. - Prepare India boundary and pilot-region boundaries. -
Define common target grid. - Validate CRS, geometry, and temporal
coverage. - Document variables and file formats.

**Expected output:** Raw meteorological package and geospatial base
layers.

### 7 July --- Meteorological Preprocessing and GIS Utilities

**Tasks** - Process wind U/V, temperature, humidity, pressure, rainfall,
and PBL variables. - Standardize CRS and spatial resolution. - Build
clipping, regridding, interpolation, spatial join, and export
utilities. - Produce meteorological QA summaries.

**Expected output:** Clean meteorological layers and reusable GIS
utilities.

### 8 July --- Common Grid Integration

**Tasks** - Regrid meteorological variables to the target grid. - Merge
meteorological features into AQI and HCHO branches. - Verify spatial and
temporal overlap. - Produce diagnostics for missing grid-time
combinations. - Coordinate fixes with Smit and Shubh.

**Expected output:** Integrated meteorological covariates and overlap
report.

### 9 July --- Dashboard Shell

**Tasks** - Build application shell and navigation. - Implement reusable
map component. - Implement common chart and card components. - Add
mock/sample AQI, HCHO, fire, and wind layers. - Establish filter and
data-loading patterns.

**Expected output:** Navigable dashboard prototype.

### 10 July --- AQI and HCHO Explorer Views

**Tasks** - Implement AQI Explorer. - Implement HCHO Explorer. - Add
date controls, city/state selection, legends, tooltips, and summary
statistics. - Prepare the views to accept real outputs from Smit and
Shubh.

**Expected output:** Functional AQI and HCHO exploration interfaces.

### 11 July --- Fire and Wind Views

**Tasks** - Build Fire Correlation view. - Build Wind Transport view. -
Visualize fire points, hotspot clusters, wind vectors, and transport
pathways. - Add layer controls and synchronized analytical panels. -
Integrate Shubh's intermediate outputs.

**Expected output:** Interactive fire and wind intelligence views.

### 12 July --- Model Integration and Validation Views

**Tasks** - Build model benchmark view. - Build validation and
statistics view. - Connect AQI predictions and HCHO outputs to data
loaders or API layer. - Verify map rendering, filtering, and analytical
consistency. - Optimize heavy layer loading.

**Expected output:** End-to-end analytical outputs visible in dashboard.

### 13 July --- Explainable AI Integration

**Tasks** - Build Explainable AI view. - Integrate SHAP plots and
feature-importance results. - Integrate confidence information and
validation summaries. - Improve explanatory text, labels, legends, and
visual hierarchy.

**Expected output:** Explainability and validation experience
integrated.

### 14 July --- Overview, Reports and Feature Freeze

**Tasks** - Complete Overview page. - Complete Reports page. - Add final
navigation links and status indicators. - Improve responsiveness,
loading states, error handling, legends, and tooltips. - Freeze major
features by end of day.

**Expected output:** Feature-complete dashboard.

### 15 July --- Release Candidate Integration

**Tasks** - Integrate final AQI artifacts from Smit. - Integrate final
HCHO, correlation, transport, and source-attribution artifacts from
Shubh. - Resolve schema and data-loading issues. - Optimize deployment
pipeline and map performance. - Add report/download assets. - Produce
Release Candidate 1.

**Expected output:** Deployable Release Candidate 1.

### 16 July --- System Testing and Documentation

**Tasks** - Test all routes, filters, maps, charts, and downloads. -
Verify deployment stability. - Fix UI and integration defects. - Prepare
README, setup instructions, architecture notes, screenshots, and demo
flow. - Prepare offline screenshots/video or static fallback where
useful.

**Expected output:** Stable documented submission candidate.

### 17 July --- Deployment, Packaging and Rehearsal

**Tasks** - Verify live deployment. - Audit repository and required
assets. - Package dashboard, reports, presentation material, and backup
demo assets. - Conduct complete demo rehearsal with the team. - Verify
final submission contents and links.

**Expected output:** Final deployed prototype and complete submission
package.

## Completion Checklist

-   [ ] Repository and environment initialized.
-   [ ] Common project structure established.
-   [ ] Meteorological data acquired and processed.
-   [ ] Target grid and geospatial utilities complete.
-   [ ] Meteorological covariates integrated into both analytical
    branches.
-   [ ] Dashboard shell and navigation complete.
-   [ ] AQI Explorer complete.
-   [ ] HCHO Explorer complete.
-   [ ] Fire Correlation view complete.
-   [ ] Wind Transport view complete.
-   [ ] Benchmark and Validation views complete.
-   [ ] Explainable AI view complete.
-   [ ] Overview and Reports views complete.
-   [ ] Final analytical artifacts integrated.
-   [ ] Deployment tested.
-   [ ] README and setup documentation complete.
-   [ ] Backup demo path prepared.
-   [ ] Final submission package verified.
