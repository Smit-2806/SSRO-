# Shubh Soni --- Person-Specific Task Manager

**Role:** HCHO Intelligence, Analytics and Scientific Validation Lead\
**Execution Window:** 5 July 2026 -- 17 July 2026

## Primary Ownership

Shubh owns the complete HCHO intelligence branch: TROPOMI HCHO
processing, MODIS/VIIRS fire analytics, hotspot detection, fire-HCHO
correlation, wind-transport interpretation, source attribution,
robustness testing, scientific validation, final analytical artifacts,
and technical communication of the HCHO objective.

## Daily Task Plan

### 5 July --- HCHO Analysis Design

**Tasks** - Define HCHO analysis inputs, intermediate tables, and final
outputs. - Inspect TROPOMI HCHO and FIRMS MODIS/VIIRS structures. -
Define hotspot metadata fields: cluster ID, centroid, area,
concentration statistics, persistence, nearest fire distance, local fire
count, mean FRP, and transport evidence. - Establish scientific
questions for correlation, transport, and source attribution.

**Expected output:** HCHO pipeline specification and output schema.

### 6 July --- HCHO and Fire Data Acquisition

**Tasks** - Acquire TROPOMI HCHO data for the agreed pilot period and
geography. - Acquire MODIS/VIIRS fire observations. - Inspect QA values,
FRP, confidence, coordinates, and temporal coverage. - Create a source
inventory and identify coverage gaps.

**Expected output:** Raw HCHO and fire datasets with acquisition log.

### 7 July --- Quality Filtering and Exploratory Analysis

**Tasks** - Apply appropriate HCHO QA filtering. - Remove invalid or
unusable observations. - Standardize timestamps and coordinates. - Clean
fire data and apply confidence criteria. - Explore HCHO distributions,
spatial patterns, fire density, FRP distribution, and seasonal
variation.

**Expected output:** Cleaned HCHO/fire data and exploratory findings.

### 8 July --- HCHO-Fire Alignment and Feature Engineering

**Tasks** - Align HCHO pixels and fire observations spatially and
temporally. - Compute nearest-fire distance. - Compute fire-count
buffers for relevant radii. - Aggregate FRP around target grid cells. -
Prepare analysis tables for hotspot detection and correlation.

**Expected output:** Analysis-ready HCHO-fire feature dataset.

### 9 July --- Hotspot Detection Prototype

**Tasks** - Implement percentile-based anomaly thresholding. - Implement
DBSCAN clustering. - Compare sensitivity of cluster count, size, and
persistence. - Generate cluster geometries, centroids, and summary
statistics. - Export initial hotspot layer for dashboard use.

**Expected output:** Initial HCHO hotspot catalog and map-ready layer.

### 10 July --- Fire-HCHO Correlation Analysis

**Tasks** - Measure relationships between HCHO enhancement and fire
count. - Measure relationships between HCHO enhancement and FRP. -
Compare same-day and lagged relationships. - Examine distance-dependent
behavior. - Identify strong case-study episodes and regions.

**Expected output:** Correlation tables, plots, and case-study
shortlist.

### 11 July --- Wind Transport Analysis

**Tasks** - Use U/V wind components to derive speed and direction. -
Determine upwind/downwind relationships. - Develop transport-vector
logic. - Examine whether HCHO enhancements appear downwind of active
fires. - Produce map-ready transport paths or vector summaries.

**Expected output:** Wind-transport analytical layer and interpretation
notes.

### 12 July --- Source Attribution

**Tasks** - Build evidence rules for fire-linked hotspots. - Separate
likely biomass-burning-linked hotspots from unexplained or
non-fire-dominant hotspots. - Rank clusters using concentration,
persistence, fire proximity, fire intensity, and wind consistency. -
Produce structured source-attribution metadata.

**Expected output:** Ranked hotspot catalog with source-attribution
evidence.

### 13 July --- Robustness and Scientific Validation

**Tasks** - Test hotspot sensitivity to thresholds. - Test DBSCAN
parameter sensitivity. - Analyze temporal-lag sensitivity in fire-HCHO
correlation. - Assess transport-path plausibility against meteorological
fields. - Record limitations and avoid unsupported causal claims.

**Expected output:** Robustness report and validated interpretation
notes.

### 14 July --- Final HCHO Evaluation and Case Studies

**Tasks** - Finalize hotspot evaluation. - Use IoU or spatial overlap
metrics where a defensible reference zone exists. - Verify continuous
overlap across HCHO, fire, and meteorological sources. - Finalize
case-study regions and evidence chains. - Freeze HCHO methodology and
output schema.

**Expected output:** Final validation summary and frozen analytical
pipeline.

### 15 July --- Final HCHO Artifacts

**Tasks** - Generate final hotspot maps. - Generate fire-correlation
plots and tables. - Generate transport-pathway outputs. - Generate
source-attribution summaries. - Write concise, evidence-based findings
for dashboard and presentation.

**Expected output:** Final analytical artifact package.

### 16 July --- Scientific Audit and Communication

**Tasks** - Verify every scientific claim against actual outputs. -
Ensure maps and statistics tell a consistent story. - Write methodology,
results, limitations, and future-scope notes. - Prepare judge Q&A on
HCHO, VOC relevance, fire correlation, hotspot algorithms, wind
transport, and limitations.

**Expected output:** Scientific narrative and Q&A sheet.

### 17 July --- Final Review and Presentation Readiness

**Tasks** - Audit hotspot statistics and maps. - Audit correlation
claims. - Audit transport and source-attribution interpretation. -
Prepare concise speaking points. - Participate in full demo rehearsal
and final submission verification.

**Expected output:** Presentation-ready HCHO analysis with verified
evidence.

## Completion Checklist

-   [chcked] TROPOMI HCHO acquired and QA-filtered.
-   [ ] MODIS/VIIRS fire data cleaned.
-   [ ] HCHO-fire spatial-temporal alignment complete.
-   [ ] Fire distance.
-   Buffers.
-   Counts.
-   And FRP features generated.
-   [ ] Threshold-based hotspot detection complete.
-   [ ] DBSCAN hotspot clustering complete.
-   [ ] Fire-HCHO correlation analysis complete.
-   [ ] Wind-transport analysis complete.
-   [ ] Source-attribution logic complete.
-   [ ] Robustness and sensitivity tests complete.
-   [ ] Final maps.
-   Tables.
-   Plots.
-   And metadata exported.
-   [ ] Scientific claims audited.
-   [ ] Judge Q&A prepared.
