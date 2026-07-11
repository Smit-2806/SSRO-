# INSAT-3D AOD Ingestion & Missingness Report (6 July Task)

This report documents the acquisition, structure, and missingness audit of the INSAT-3D Aerosol Optical Depth (AOD) data product ingested for the 2024 pilot period across 5 Indian cities.

---

## 1. Dataset Properties

The raw dataset contains spatial coordinate mappings and geometry parameters matching the imager configurations:

* **File Location:** `data/raw/satellite/insat3d_aod_5cities_2024.csv`
* **Spatio-Temporal Bounds:**
  * **Temporal:** 1 January 2024 – 30 December 2024.
  * **Spatial Bounding Envelope:** 5 Cities (Delhi, Mumbai, Chennai, Hyderabad, Bangalore).
  * **Latitude Limits:** $12.97^\circ\text{ N to }28.61^\circ\text{ N}$
  * **Longitude Limits:** $72.87^\circ\text{ E to }80.27^\circ\text{ E}$

---

## 2. Missingness & Quality Audit

Satellite retrievals suffer from cloud-contamination and solar-glint masks. The raw dataset was audited for data availability and quality flags:

| City | Total Days | Valid AOD Days | Cloudy / Masked Days | Missingness Rate |
| :--- | :---: | :---: | :---: | :---: |
| **Delhi** | 296 | 196 | 100 | 33.78% |
| **Mumbai** | 296 | 195 | 101 | 34.12% |
| **Bangalore** | 296 | 211 | 85 | 28.72% |
| **Hyderabad** | 296 | 200 | 96 | 32.43% |
| **Chennai** | 289 | 189 | 100 | 34.60% |
| **Total Grid** | **1,473** | **991** | **482** | **32.72%** |

### Data Quality Assurance (QA) Flags
* **High Quality (QA = 0):** 83.2% of valid retrievals.
* **Medium Quality (QA = 1):** 16.8% of valid retrievals.
* **Low / Cloud-Masked (QA = 2):** 32.72% of total days (discarded from direct modeling).

---

## 3. Physical Geometry Checks

Validation of orbital geometries was conducted to verify consistency with sun-sensor paths:
* **Solar Zenith Angle:** Bounded between $5.0^\circ$ and $45.0^\circ$, peaking cyclically in summer months (expected physical seasonality).
* **Observation Time:** Fixed morning pass at `08:30:00` Local Solar Time.

---

## 4. Gap Imputation Strategy (July 7 Preview)

To provide the CNN-LSTM model with a continuous temporal matrix:
1. All cloudy days (`qa_flag == 2` or `cloud_mask == 1`) are masked.
2. Missing values are filled using a **temporal linear interpolation** grouped by city:
   $$\text{AOD}_t = \text{Interpolate}(\text{AOD}_{t-1}, \text{AOD}_{t+1})$$
3. Edge boundaries are resolved via forward-fill (`ffill`) and backward-fill (`bfill`).
4. **Cleaned Output File:** `data/processed/insat3d_aod_cleaned_2024.csv` (100% complete, 0.00% missingness).
