# Data Pipeline Reference

## 1. TROPOMI / Sentinel-5P (via DLR GeoService or GEE)

### Direct download (Python + requests)
```python
import requests, os
from pathlib import Path

BASE_URL = "https://download.geoservice.dlr.de/S5P_TROPOMI/files/L3/"
PRODUCTS = {
    "NO2":  "L3__NO2___",
    "SO2":  "L3__SO2___",
    "CO":   "L3__CO____",
    "O3":   "L3__O3____",
    "HCHO": "L3__HCHO__",
    "AER":  "L3__AER_AI",
}

def download_tropomi(product: str, year: int, month: int, out_dir: Path):
    """Download TROPOMI L3 NetCDF files for a given product/month."""
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = PRODUCTS[product]
    url = f"{BASE_URL}{tag}/{year}/{month:02d}/"
    r = requests.get(url)
    # parse file list and download each .nc file
    ...
```

### Loading and subsetting to India
```python
import xarray as xr
import numpy as np

INDIA_BBOX = {"lon_min": 68.0, "lon_max": 97.5, "lat_min": 6.5, "lat_max": 37.5}

def load_tropomi_nc(path: str, variable: str) -> xr.DataArray:
    ds = xr.open_dataset(path)
    da = ds[variable]
    da = da.sel(
        longitude=slice(INDIA_BBOX["lon_min"], INDIA_BBOX["lon_max"]),
        latitude=slice(INDIA_BBOX["lat_min"], INDIA_BBOX["lat_max"])
    )
    # Apply QA flag (keep qa_value >= 0.75)
    if "qa_value" in ds:
        da = da.where(ds["qa_value"] >= 0.75)
    return da
```

---

## 2. INSAT-3D AOD (MOSDAC)

INSAT-3D AOD is available at https://www.mosdac.gov.in/insat-3d-data-products in HDF5 format.

```python
import h5py
import numpy as np

def load_insat3d_aod(hdf5_path: str) -> dict:
    """Load INSAT-3D AOD data from MOSDAC HDF5 file."""
    with h5py.File(hdf5_path, "r") as f:
        aod = f["AOD_550nm"][:]          # shape: (lat, lon)
        lat = f["Latitude"][:]
        lon = f["Longitude"][:]
        qc  = f["QC_flag"][:]
    # Mask bad retrievals
    aod = np.where(qc == 0, aod, np.nan)
    return {"aod": aod, "lat": lat, "lon": lon}

# Convert AOD → PM2.5 (simple empirical, replace with ML prediction)
# PM2.5 (µg/m³) ≈ AOD * scale_factor (region/season specific, ~50–120)
```

---

## 3. CPCB Ground Station Data

Download from: https://airquality.cpcb.gov.in/ccr/#/caaqm-dashboard-all/caaqm-landing/caaqm-data-repository

```python
import pandas as pd
from pathlib import Path

POLLUTANTS = ["PM2.5", "PM10", "NO2", "SO2", "CO", "Ozone"]

def load_cpcb_station(csv_path: str) -> pd.DataFrame:
    """
    Expected CPCB CSV columns:
    From Date, To Date, PM2.5 (µg/m³), PM10 (µg/m³), NO2 (µg/m³), ...
    """
    df = pd.read_csv(csv_path, parse_dates=["From Date"])
    df = df.rename(columns={"From Date": "datetime"})
    df = df.set_index("datetime")
    # Replace missing/invalid values
    df = df.replace({"None": np.nan, "---": np.nan}).astype(float)
    # Resample to daily mean
    df_daily = df.resample("D").mean()
    return df_daily

def build_station_dataset(station_dir: Path) -> pd.DataFrame:
    """Merge all station CSVs into a single multi-index DataFrame."""
    frames = []
    for csv in station_dir.glob("*.csv"):
        df = load_cpcb_station(str(csv))
        df["station"] = csv.stem
        frames.append(df)
    return pd.concat(frames).reset_index()
```

Station metadata CSV columns needed: `station_id, name, city, state, lat, lon, elevation_m`

---

## 4. ERA5 Reanalysis Meteorology (CDS API)

```python
import cdsapi

c = cdsapi.Client()

METEO_VARS = [
    "2m_temperature", "2m_dewpoint_temperature",
    "surface_pressure", "boundary_layer_height",
    "u_component_of_wind", "v_component_of_wind",  # 10m
    "total_precipitation", "total_column_water_vapour",
]

def download_era5_india(year: int, month: int, out_path: str):
    c.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": "reanalysis",
            "variable": METEO_VARS,
            "year": str(year),
            "month": f"{month:02d}",
            "day": [f"{d:02d}" for d in range(1, 32)],
            "time": ["00:00", "06:00", "12:00", "18:00"],
            "area": [37.5, 68.0, 6.5, 97.5],  # N, W, S, E
            "format": "netcdf",
        },
        out_path,
    )
```

---

## 5. MODIS/VIIRS Fire Counts (NASA FIRMS)

Download from: https://firms.modaps.eosdis.nasa.gov/active_fire/

```python
import pandas as pd

def load_firms_fire(csv_path: str) -> pd.DataFrame:
    """
    FIRMS CSV columns: latitude, longitude, brightness, scan, track,
    acq_date, acq_time, satellite, instrument, confidence, frp, daynight
    """
    df = pd.read_csv(csv_path, parse_dates=["acq_date"])
    # Filter to India bbox
    df = df[
        (df["latitude"].between(6.5, 37.5)) &
        (df["longitude"].between(68.0, 97.5))
    ]
    # Keep only high-confidence fires
    df = df[df["confidence"] >= 80]
    return df
```

---

## 6. Collocation: Satellite ↔ Ground Station

The CNN-LSTM training requires paired (satellite + meteo input) ↔ (surface measurement) samples.

```python
def collocate_satellite_station(
    tropomi_da: xr.DataArray,
    stations_df: pd.DataFrame,
    radius_deg: float = 0.1
) -> pd.DataFrame:
    """
    For each station and date, extract the mean satellite value
    within `radius_deg` degrees of the station coordinates.
    """
    records = []
    for _, row in stations_df.iterrows():
        lat, lon = row["lat"], row["lon"]
        local = tropomi_da.sel(
            latitude=slice(lat - radius_deg, lat + radius_deg),
            longitude=slice(lon - radius_deg, lon + radius_deg),
        )
        val = float(local.mean())
        records.append({
            "station": row["station_id"],
            "date": pd.Timestamp(tropomi_da.time.values),
            "sat_value": val,
            "lat": lat, "lon": lon,
        })
    return pd.DataFrame(records)
```

---

## 7. Normalisation & Sequence Building for CNN-LSTM

```python
import numpy as np
from sklearn.preprocessing import StandardScaler

def build_sequences(df: pd.DataFrame, feature_cols: list, target_col: str,
                    seq_len: int = 7) -> tuple:
    """
    Build sliding-window sequences for LSTM input.
    Returns X: (N, seq_len, n_features), y: (N,)
    """
    scaler_X = StandardScaler()
    scaler_y = StandardScaler()

    X_scaled = scaler_X.fit_transform(df[feature_cols].values)
    y_scaled = scaler_y.fit_transform(df[[target_col]].values).ravel()

    X_seqs, y_seqs = [], []
    for i in range(seq_len, len(df)):
        X_seqs.append(X_scaled[i - seq_len:i])
        y_seqs.append(y_scaled[i])

    return np.array(X_seqs), np.array(y_seqs), scaler_X, scaler_y
```

**Feature columns** (typical set for Objective 1):
- Satellite: `no2_col`, `so2_col`, `co_col`, `o3_col`, `aod_550`, `hcho_col`
- Meteorology: `temp_2m`, `dewpoint_2m`, `blh`, `sp`, `u10`, `v10`, `precip`, `tcwv`
- Temporal: `doy_sin`, `doy_cos` (day-of-year encoded as sine/cosine)
- Spatial: `lat`, `lon` (station coordinates)
