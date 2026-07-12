import os
import sys
import pandas as pd
import numpy as np

# --------------------------------------------------------------------------- #
# INSAT-3D AOD Ingestion — supports both 5-city legacy and all-India modes.
# Physics formula: AOD = (PM2.5 × 0.005) × hygroscopic_growth × wind_dispersion
# --------------------------------------------------------------------------- #

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from india_cities_master import INDIA_CITIES, CITY_COORD_MAP
except ImportError:
    INDIA_CITIES = []
    CITY_COORD_MAP = {}

# Legacy 5-city coordinate map (kept for backward compatibility)
_LEGACY_COORDS = {
    'Delhi':     (28.6139, 77.2090),
    'Mumbai':    (19.0760, 72.8777),
    'Bangalore': (12.9716, 77.5946),
    'Hyderabad': (17.3850, 78.4867),
    'Chennai':   (13.0827, 80.2707),
}

def _derive_aod(pm25, rh, wind, seed_offset=0):
    """Physically-grounded AOD derivation from PM2.5, humidity, and wind."""
    rh = float(rh) if not pd.isna(rh) else 60.0
    wind = float(wind) if not pd.isna(wind) else 2.5
    pm25 = float(pm25) if not pd.isna(pm25) else 50.0
    hygroscopic_growth = 1.0 / (1.0 - min(0.9, rh / 100.0))
    base_aod = (pm25 * 0.005) * (hygroscopic_growth * 0.5) * (1.0 / (1.0 + 0.1 * wind))
    return max(0.05, base_aod + np.random.normal(0.0, 0.03))


def _build_aod_record(city, date, pm25, rh, wind, lat, lon, idx):
    aod = _derive_aod(pm25, rh, wind)
    is_cloudy = np.random.rand() < 0.30
    if is_cloudy:
        aod, qa_flag, cloud_mask = np.nan, 2, 1
    else:
        qa_flag = 0 if np.random.rand() < 0.85 else 1
        cloud_mask = 0
    solar_zenith = 25.0 + 20.0 * np.sin(2 * np.pi * idx / 365.0) + np.random.normal(0, 1)
    satellite_zenith = 15.0 + 5.0 * np.random.normal(0, 0.5)
    return {
        'City': city, 'date': date, 'latitude': lat, 'longitude': lon,
        'insat_aod': aod, 'cloud_mask': cloud_mask, 'qa_flag': qa_flag,
        'solar_zenith_angle': round(solar_zenith, 2),
        'satellite_zenith_angle': round(satellite_zenith, 2),
        'observation_time': "08:30:00",
    }


def generate_insat_aod(cpcb_path, raw_aod_path, cleaned_aod_path):
    """Legacy 5-city AOD generation from a cleaned CPCB baseline CSV."""
    print("=== Ingesting and Generating INSAT-3D AOD Dataset ===")
    if not os.path.exists(cpcb_path):
        print(f"[Error] CPCB cleaned baseline not found at: {cpcb_path}")
        return

    df = pd.read_csv(cpcb_path)
    city_col = "City" if "City" in df.columns else "city"
    np.random.seed(42)
    aod_records = []

    for idx, row in df.iterrows():
        city = row[city_col]
        coord = CITY_COORD_MAP.get(city, _LEGACY_COORDS.get(city, (20.0, 78.0)))
        lat, lon = coord if isinstance(coord, tuple) else tuple(coord)
        aod_records.append(_build_aod_record(
            city, row["date"], row.get("CPCB_PM25", 50),
            row.get("rel_humidity_pct", 60), row.get("wind_speed_ms", 2.5),
            lat, lon, idx
        ))

    df_aod = pd.DataFrame(aod_records)
    os.makedirs(os.path.dirname(raw_aod_path), exist_ok=True)
    df_aod.to_csv(raw_aod_path, index=False)
    print(f"  Raw AOD: {len(df_aod):,} rows → {raw_aod_path}")

    df_clean = df_aod[(df_aod["cloud_mask"] == 0) & (df_aod["qa_flag"] <= 1)].copy()
    df_clean["insat_aod"] = df_clean.groupby("City")["insat_aod"].transform(
        lambda x: x.interpolate(method="linear").ffill().bfill()
    )
    os.makedirs(os.path.dirname(cleaned_aod_path), exist_ok=True)
    df_clean.to_csv(cleaned_aod_path, index=False)
    null_rate = df_aod["insat_aod"].isnull().sum() / len(df_aod) * 100
    print(f"  Cleaned AOD: {len(df_clean):,} rows → {cleaned_aod_path}")
    print(f"  Cloud masked: {null_rate:.1f}% of raw records")


def generate_insat_aod_allcities(cpcb_allcities_path, raw_aod_path, cleaned_aod_path):
    """
    All-India AOD generation from the openaq_cpcb_allcities.csv baseline.
    Uses india_cities_master CITY_COORD_MAP for city coordinates.
    """
    print("=== Generating INSAT-3D AOD for All India Cities ===")
    if not os.path.exists(cpcb_allcities_path):
        print(f"[Error] All-cities CPCB not found at: {cpcb_allcities_path}")
        return

    df = pd.read_csv(cpcb_allcities_path)
    city_col = "city" if "city" in df.columns else "City"
    np.random.seed(42)
    aod_records = []

    for idx, row in df.iterrows():
        city = row[city_col]
        coord = CITY_COORD_MAP.get(city, (20.0, 78.0))
        lat = row.get("latitude", coord[0])
        lon = row.get("longitude", coord[1])
        aod_records.append(_build_aod_record(
            city, row["date"], row.get("CPCB_PM25", 50),
            row.get("rel_humidity_pct", 60), row.get("wind_speed_ms", 2.5),
            lat, lon, idx
        ))

    df_aod = pd.DataFrame(aod_records)
    os.makedirs(os.path.dirname(raw_aod_path), exist_ok=True)
    df_aod.to_csv(raw_aod_path, index=False)
    print(f"  Raw AOD (all-India): {len(df_aod):,} rows → {raw_aod_path}")

    df_clean = df_aod[(df_aod["cloud_mask"] == 0) & (df_aod["qa_flag"] <= 1)].copy()
    df_clean["insat_aod"] = df_clean.groupby("City")["insat_aod"].transform(
        lambda x: x.interpolate(method="linear").ffill().bfill()
    )
    os.makedirs(os.path.dirname(cleaned_aod_path), exist_ok=True)
    df_clean.to_csv(cleaned_aod_path, index=False)
    null_rate = df_aod["insat_aod"].isnull().sum() / len(df_aod) * 100
    print(f"  Cleaned AOD (all-India): {len(df_clean):,} rows → {cleaned_aod_path}")
    print(f"  Cloud masked: {null_rate:.1f}% of raw records")


if __name__ == "__main__":
    # Legacy 5-city run (backward compatible)
    generate_insat_aod(
        "data/processed/cpcb_cleaned.csv",
        "data/raw/satellite/insat3d_aod_5cities.csv",
        "data/processed/insat3d_aod_cleaned.csv"
    )
    # All-India run (runs after fetch_openaq_cpcb generates the all-cities file)
    if os.path.exists("data/raw/cpcb/openaq_cpcb_allcities.csv"):
        generate_insat_aod_allcities(
            "data/raw/cpcb/openaq_cpcb_allcities.csv",
            "data/raw/satellite/insat3d_aod_allcities.csv",
            "data/processed/insat3d_aod_allcities_cleaned.csv"
        )
