# AQI Model Pipeline Design & Validation Strategy

This document serves as the technical specification and data contract for the Surface AQI Estimation deep learning pipeline (Objective 1).

---

## 1. Target Variables & Input Schema

The goal is to estimate ground-level air quality across India. The model predicts:
* **Primary Target:** `CPCB_AQI` (dimensionless index, 0 to 500)
* **Secondary Targets (Optional/Auxiliary):** `CPCB_PM25` ($\mu\text{g/m}^3$) and `CPCB_PM10` ($\mu\text{g/m}^3$)

### Input Feature Schema
The model uses a fused spatio-temporal feature vector $\mathbf{x}(t)$ consisting of:

| Feature Category | Variable Name | Source | Description |
| :--- | :--- | :---: | :--- |
| **Ground baseline** | `CPCB_NO2_surface`, `CPCB_SO2`, `CPCB_CO_surface`, `CPCB_O3` | CPCB | Surface-level criteria gaseous pollutants. |
| **Satellite Gas Columns** | `TROPOMI_HCHO_mol_m2`, `TROPOMI_NO2_mol_m2`, `TROPOMI_CO_mol_m2` | Sentinel-5P | Columnar tropospheric concentrations. |
| **Aerosol Indicators** | `Aerosol_Index` / `AOD` | Satellite | Column aerosol loading. *Note: If INSAT-3D AOD is not available locally, TROPOMI UV Aerosol Index will be used as a proxy.* |
| **Meteorology** | `temp_c`, `dewpoint_c`, `wind_speed_ms`, `pressure_hpa`, `precip_mm`, `rel_humidity_pct` | ERA5 / Open-Meteo | Atmospheric physical properties governing dispersion and boundary layer height. |
| **Temporal Lags** | $\mathbf{x}(t-1)$, $\mathbf{x}(t-2)$, $\mathbf{x}(t-3)$ | Engineered | Historical sliding windows of 1, 2, and 3 days. |

---

## 2. Spatio-Temporal Data Layout & Artifact Conventions

To maintain project integration, the pipeline uses structured folders to manage raw data, models, and outputs:

```text
ISRO Hackathon/
├── data/
│   ├── raw/                      # Raw local datasets (Gitignored)
│   ├── processed/                # Standardised, QA-masked, and gap-filled tables
│   ├── features/                 # Model-ready lags and wind transport vectors
│   └── predictions/              # Output grids for dashboard display
├── models/                       # Stored model weights (.pth, .pkl)
│   └── checkpoints/              # Epoch-wise training checkpoints
├── metrics/                      # Model performance metrics (CSV/JSON summaries)
└── src/
    └── aqi_model/                # Model code directory
        ├── dataset.py            # Sliding window dataset loader
        ├── model.py              # CNN-LSTM + Attention neural network architecture
        └── train.py              # Training loop, loss functions, and logging
```

---

## 3. Deep Learning Model Architecture (CNN-LSTM + Attention)

To capture both spatial structures and temporal persistence, we design a hybrid network:

```
                  +--------------------------------+
                  |  Input Tensor: (Batch, Seq, F)  |
                  +----------------+---------------+
                                   |
                                   v
                  +--------------------------------+
                  |    1D CNN Layer (Spatial)      |
                  +----------------+---------------+
                                   |
                                   v
                  +--------------------------------+
                  |      LSTM Layer (Temporal)     |
                  +----------------+---------------+
                                   |
                                   v
                  +--------------------------------+
                  |     Self-Attention Layer       |
                  +----------------+---------------+
                                   |
                                   v
                  +--------------------------------+
                  |   Dense Regressor (Surface AQI) |
                  +--------------------------------+
```

1. **1D CNN Block:** Convolves along the feature dimension to capture high-order interactions between meteorological variables and satellite column densities.
2. **LSTM Block:** Recurrent layers that ingest the temporal window sequence (Lags $t-3 \to t$) to model atmospheric persistence.
3. **Attention Layer:** Learns dynamically which lag steps (e.g., yesterday's vs. 3 days ago) are most predictive under varying weather conditions.

---

## 4. Evaluation and Validation Strategy

To evaluate the model's true generalization capacity and prevent temporal/spatial data leakage, we establish a **double-blind validation strategy**:

### A. Temporal Block Split (Within-City Validation)
Since consecutive days are highly correlated ($r = 0.914$ in Delhi), standard random K-fold splits will leak temporal information. We implement **blocked time splits**:
* **Training Set:** January 1 – August 31, 2024
* **Validation Set:** September 1 – October 31, 2024
* **Holdout Test Set:** November 1 – December 31, 2024 (covers the peak stubble-burning episode).

### B. Spatial Holdout Validation (Cross-City Generalization)
To verify if the model can estimate AQI at unmonitored locations, we evaluate the model using **Leave-One-City-Out (LOCO) cross-validation**:
* Train on 4 cities (e.g., Bangalore, Chennai, Hyderabad, Mumbai).
* Evaluate on the 5th city (e.g., Delhi).
* Calculate performance metrics globally and per city.

### C. Performance Metrics
We measure prediction quality using the following standard statistical indicators:
* **Root Mean Squared Error (RMSE):**
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2}$$
* **Mean Absolute Error (MAE):**
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} |y_i - \hat{y}_i|$$
* **Coefficient of Determination ($R^2$):**
  $$R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$$
* **Pearson Correlation Coefficient ($r$):** Measures the linear alignment between predictions and ground CPCB AQI.
