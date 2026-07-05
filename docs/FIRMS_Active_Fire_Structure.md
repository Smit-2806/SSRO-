# NASA FIRMS Active Fire Data Structure Reference

This reference document defines the file formats, attributes, and quality filters for **NASA FIRMS Active Fire** datasets (MODIS and VIIRS products).

---

## 1. Data Ingestion Formats

Active fire data is ingested in tabular point vector formats:
* **CSV:** Daily near-real-time (NRT) downloads.
* **CRS:** EPSG:4326 (WGS 84 geographic coordinates).

---

## 2. Variables & Attributes Schema

The following table defines the columns present in the FIRMS active fire CSV file:

| Column Name | Data Type | Physical Unit | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`latitude`** | Float64 | Degrees | $-90.0 \text{ to } 90.0$ | Latitude of the center of the fire pixel. |
| **`longitude`** | Float64 | Degrees | $-180.0 \text{ to } 180.0$ | Longitude of the center of the fire pixel. |
| **`frp`** | Float32 | Megawatts ($\text{MW}$) | $0.0 \text{ to } 10000.0$ | Fire Radiative Power. Indicates the rate of heat release and biomass consumption rate. |
| **`brightness`** | Float32 | Kelvin ($\text{K}$) | $250.0 \text{ to } 500.0$ | Brightness temperature (Kelvin) of the fire pixel. |
| **`confidence`** | String / Int | Variable | $0-100\% \text{ or } [L, N, H]$ | Confidence level of detection. MODIS uses $0-100\%$, VIIRS uses $L$ (low), $N$ (nominal), $H$ (high). |
| **`acq_date`** | Date | YYYY-MM-DD | - | Date of acquisition. |
| **`acq_time`** | String | HHMM | - | Time of acquisition in UTC. |
| **`satellite`** | String | Class | `Terra`, `Aqua`, `NPP`, `NOAA20` | Satellite platform that performed the scan. |
| **`instrument`**| String | Class | `MODIS`, `VIIRS` | Sensor instrument. |

---

## 3. Sensor Spatial Footprint Comparison

We must weight fire influence based on the spatial resolution of the detecting instrument to avoid spatial sampling biases:
* **MODIS (Terra/Aqua):**
  * *Spatial Resolution:* $1\text{ km} \times 1\text{ km}$ at nadir.
  * *FRP range:* Typically higher detection threshold ($>10\text{ MW}$).
* **VIIRS (Suomi-NPP/NOAA-20):**
  * *Spatial Resolution:* $375\text{ m} \times 375\text{ m}$ at nadir.
  * *FRP range:* Sensitive to smaller, cooler agricultural fires ($>1\text{ MW}$).
  * *Calibration Rule:* Standardize VIIRS counts and FRP values when combining with MODIS datasets to prevent local density overestimation.

---

## 4. Quality Control & False Alarm Filtering

To avoid non-biomass heat sources (like industrial chimneys, gas flares, and solar reflection), we apply the following filtering logic:

```python
# Python Preprocessing Quality Filter for Fires
import pandas as pd

def clean_active_fires(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Filter out low confidence detections
    # MODIS: confidence > 30%
    # VIIRS: confidence != 'low'
    modis_mask = (df['instrument'] == 'MODIS') & (df['confidence'].astype(float) > 30)
    viirs_mask = (df['instrument'] == 'VIIRS') & (df['confidence'] != 'low')
    
    df_clean = df[modis_mask | viirs_mask].copy()
    
    # 2. Mask known industrial gas flaring zones (e.g., refinery coordinates)
    # Filter by bounding box list if necessary to isolate rural biomass burning
    
    # 3. Combine acquisition date and time into a single UTC datetime object
    df_clean['datetime_utc'] = pd.to_datetime(
        df_clean['acq_date'] + ' ' + 
        df_clean['acq_time'].str.zfill(4), 
        format='%Y-%m-%d %H%M', 
        utc=True
    )
    
    return df_clean
```
* *Justification:* Active fire alerts with low confidence (or under $30\%$) are prone to reflection/solar glint anomalies. Combining date and time columns into a single timezone-aware timestamp is crucial for temporal lag calculations in downstream correlations.
