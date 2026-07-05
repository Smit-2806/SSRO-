# HCHO Hotspot & Transport Analysis Schema

This document defines the mathematical, physical, and engineering schema for **Objective 2: HCHO Hotspots, Fire Correlation, and Wind Transport Analysis**.

---

## 1. Hotspot Detection Engine

To identify anomalous formaldehyde (HCHO) enhancements over India, we use a hybrid **statistical-spatial clustering pipeline**.

### Pipeline Stages
1. **Grid Ingestion:** Extract Sentinel-5P TROPOMI gridded HCHO observations at $0.05^\circ$ grid cells (approx. $5.5\text{ km} \times 5.5\text{ km}$).
2. **Quality Masking:** Retain pixels with `qa_value >= 0.5` and filter out cloud fractions $> 20\%$.
3. **Statistical Thresholding:** Compute the **95th percentile** of the historical HCHO column density distribution for the current month and grid cell. Select cells exceeding this threshold:
   $$\text{Anomaly}_i(t) = \mathbb{I}\left(\text{HCHO}_i(t) > \text{Percentile}_{95}(\text{HCHO}_i)\right)$$
4. **Spatial Clustering (DBSCAN):** Group the active anomaly coordinate points $(x, y)$ using the DBSCAN algorithm.

### DBSCAN Parameter Selection & Justifications
* **$\epsilon = 0.15^\circ$ (approx. $16\text{ km}$):** 
  * *Justification:* Formaldehyde has a short atmospheric lifetime (approx. $2\text{ to }4\text{ hours}$ in sunlight). Within this lifespan, wind speeds of $4\text{ m/s}$ transport HCHO approximately $15\text{ to }30\text{ km}$ from the source before it photolyzes. An $\epsilon$ of $16\text{ km}$ captures the spatial footprint of this primary dispersion.
* **`min_samples = 3`:**
  * *Justification:* Filters out random sensor noise and transient localized spikes, ensuring that only clustered emissions are flagged.

### Output Geometry Schema (Table format)
Each detected hotspot cluster is exported as a record with the following schema:

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| **cluster_id** | String (UUID) | Unique identifier for the hotspot cluster. |
| **date** | Date (YYYY-MM-DD) | Date of the satellite observations. |
| **centroid_lat** | Float | Latitude of the spatial centroid. |
| **centroid_lon** | Float | Longitude of the spatial centroid. |
| **area_km2** | Float | Spatial area of the cluster polygon in square kilometers. |
| **mean_hcho** | Float | Average HCHO column density ($\text{mol/m}^2$) inside the cluster. |
| **max_hcho** | Float | Peak HCHO column density ($\text{mol/m}^2$) inside the cluster. |
| **persistence_days**| Integer | Number of consecutive days this cluster has overlapped in space. |

---

## 2. Spatial-Temporal Fire Correlation

To link HCHO enhancements to biomass burning, we correlate hotspots with MODIS/VIIRS active fire data from NASA FIRMS.

### Spatial Buffer Configuration
For each HCHO hotspot centroid, we create concentric circular buffers:
* **$10\text{ km}$ (Local source):** Captures immediate fire emissions.
* **$20\text{ km}$ & $50\text{ km}$ (Plume range):** Captures local transport and oxidation of volatile organic compounds (VOCs).
* **$100\text{ km}$ (Regional scale):** Captures long-range transport effects.

### Temporal Lag Windows
Biomass burning releases precursor VOCs (like ethene and pinene) which photochemically oxidize into HCHO. This chemical aging takes time:
* We compute correlations across **lags of $t=0, -1, -2, \text{ and } -3\text{ days}$** relative to the satellite pass.
* *Justification:* Lag 0 captures direct HCHO emissions; Lags 1–3 capture the transport of longer-lived VOC precursors that oxidize into HCHO downwind.

### Feature Table Schema
This schema serves as the input to the correlation analysis engine:

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| **hotspot_id** | String | Reference to the HCHO hotspot cluster. |
| **fire_count_10k_lag0** | Integer | Total active fire counts within $10\text{ km}$ on the same day. |
| **sum_frp_50k_lag1** | Float | Sum of Fire Radiative Power ($\text{MW}$) within $50\text{ km}$ on the previous day. |
| **correlation_pearson**| Float | Calculated Pearson correlation coefficient between daily HCHO and FRP. |
| **correlation_spearman**| Float | Calculated Spearman rank correlation (to capture non-linear fits). |

---

## 3. Wind Transport Alignment & Source Attribution

Formaldehyde plumes drift downwind. We verify transport using ERA5/IMDAA meteorological wind vectors.

### Physical Model & Formulas
Let $f$ be an active fire source and $h$ be a downwind HCHO hotspot grid cell.
1. **Bearing Angle ($\theta_{f, h}$):** Compute the bearing angle from the fire to the hotspot coordinates:
   $$\theta_{f, h} = \operatorname{atan2}\left(\sin(\Delta \lambda) \cos(\phi_h), \cos(\phi_f)\sin(\phi_h) - \sin(\phi_f)\cos(\phi_h)\cos(\Delta \lambda)\right)$$
2. **Wind Direction ($\phi_{\text{wind}}$):** Derived from the $u$ (zonal) and $v$ (meridional) wind components at 10m altitude:
   $$\phi_{\text{wind}} = \operatorname{atan2}(u, v) \pm 180^\circ \text{ (direction wind is blowing to)}$$
3. **Transport Alignment Score:** We weigh the spatial influence using a distance-decay function and a wind-alignment cosine coefficient:
   $$\text{Transport Score}_{f, h} = \text{FRP}_f \times \exp\left(-\frac{d_{f, h}}{\lambda}\right) \times \max\left(0, \cos(\theta_{f, h} - \phi_{\text{wind}})\right)^2$$
   * Where $d_{f, h}$ is the geodesic distance.
   * $\lambda = 50\text{ km}$ is the **spatial decay constant** (representing the atmospheric residence scale of HCHO precursors).
   * $\cos^2(\cdot)$ focuses on the downwind cone, penalizing lateral dispersion.

---

## 4. Scientific Assumptions & Core Research Questions

### Core Assumptions
1. **HCHO as a Fire Proxy:** Formaldehyde is assumed to be the dominant visible secondary tracer for VOC oxidation plumes from agricultural residue burning.
2. **Linear Wind Advection:** High-resolution 10m wind fields are assumed to represent boundary-layer advection pathways over flat terrains (like the Indo-Gangetic Plain).
3. **QA Threshold Validity:** We assume that filtering out pixels with `qa_value < 0.5` removes cloud interference without introducing significant spatial sampling bias.

### Key Analysis Questions
* *What is the average temporal lag between peak fire activity (FRP) and peak HCHO column density over the Indo-Gangetic Plain?*
* *What percentage of detected HCHO hotspots cannot be attributed to upwind fire emissions (indicating industrial/urban sources)?*
* *How does the correlation strength vary between pre-monsoon (April-May) and post-monsoon (October-November) biomass burning seasons?*
