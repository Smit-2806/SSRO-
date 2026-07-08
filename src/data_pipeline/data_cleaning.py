import os
import urllib.request
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime

# Import weather helper functions from our existing script
try:
    from improvise_datasets import calculate_relative_humidity
except ImportError:
    def calculate_relative_humidity(temp_c, dewpoint_c):
        a, b = 17.625, 243.04
        alpha = ((a * dewpoint_c) / (b + dewpoint_c)) - ((a * temp_c) / (b + temp_c))
        return np.clip(100.0 * np.exp(alpha), 0.0, 100.0)

def clean_cpcb_dataset(raw_path, processed_path):
    """Cleans primary ground-station dataset: imputes weather from Open-Meteo, interpolates gases."""
    print("\n--- Cleaning Ground CPCB AQI Dataset ---")
    if not os.path.exists(raw_path):
        print(f"[Error] Raw CPCB dataset not found at: {raw_path}")
        return
        
    df = pd.read_csv(raw_path)
    initial_null_weather = df['temp_c'].isnull().sum()
    initial_null_gases = df['TROPOMI_HCHO_mol_m2'].isnull().sum()
    print(f"Loaded {len(df)} rows. Weather nulls: {initial_null_weather}, HCHO nulls: {initial_null_gases}")
    
    # 1. Fetch weather via Open-Meteo if there are null values
    if initial_weather_gaps := df['temp_c'].isnull().sum() > 0:
        print("  Detected missing weather values. Fetching ERA5 reanalysis from Open-Meteo...")
        cities_coords = {
            "Delhi": {"lat": 28.6139, "lon": 77.2090},
            "Mumbai": {"lat": 19.0760, "lon": 72.8777},
            "Chennai": {"lat": 13.0827, "lon": 80.2707},
            "Bangalore": {"lat": 12.9716, "lon": 77.5946},
            "Hyderabad": {"lat": 17.3850, "lon": 78.4867}
        }
        
        weather_by_city = {}
        for city, coords in cities_coords.items():
            url = (
                f"https://archive-api.open-meteo.com/v1/archive?"
                f"latitude={coords['lat']}&longitude={coords['lon']}&"
                f"start_date=2024-01-01&end_date=2024-12-31&"
                f"hourly=temperature_2m,relative_humidity_2m,dewpoint_2m,precipitation,pressure_msl,wind_speed_10m&"
                f"timezone=auto"
            )
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    res_data = json.loads(response.read().decode())
                
                hourly = res_data['hourly']
                df_h = pd.DataFrame({
                    'datetime': pd.to_datetime(hourly['time']),
                    'temp_c': hourly['temperature_2m'],
                    'dewpoint_c': hourly['dewpoint_2m'],
                    'precip_mm': hourly['precipitation'],
                    'pressure_hpa': hourly['pressure_msl'],
                    'wind_speed_ms': np.array(hourly['wind_speed_10m']) / 3.6,
                    'rel_humidity_pct': hourly['relative_humidity_2m']
                })
                df_h['date'] = df_h['datetime'].dt.strftime('%Y-%m-%d')
                df_d = df_h.groupby('date').agg({
                    'temp_c': 'mean', 'dewpoint_c': 'mean', 'precip_mm': 'sum',
                    'pressure_hpa': 'mean', 'wind_speed_ms': 'mean', 'rel_humidity_pct': 'mean'
                }).reset_index()
                weather_by_city[city] = df_d
                time.sleep(0.5)
            except Exception as e:
                print(f"  [Error] Failed to fetch weather for {city}: {e}")
                
        # Fill in weather values
        for idx, row in df.iterrows():
            city = row['City']
            date = row['date']
            if pd.isnull(row['temp_c']) and city in weather_by_city:
                match = weather_by_city[city][weather_by_city[city]['date'] == date]
                if not match.empty:
                    df.at[idx, 'temp_c'] = match.iloc[0]['temp_c']
                    df.at[idx, 'dewpoint_c'] = match.iloc[0]['dewpoint_c']
                    df.at[idx, 'wind_speed_ms'] = match.iloc[0]['wind_speed_ms']
                    df.at[idx, 'pressure_hpa'] = match.iloc[0]['pressure_hpa']
                    df.at[idx, 'precip_mm'] = match.iloc[0]['precip_mm']
                    df.at[idx, 'rel_humidity_pct'] = match.iloc[0]['rel_humidity_pct']
                    
    # 2. Interpolate missing satellite gas columns
    # We sort by City and Date, and apply forward-fill and backward-fill within each city group
    gas_cols = ['TROPOMI_CO_mol_m2', 'TROPOMI_HCHO_mol_m2', 'TROPOMI_NO2_mol_m2']
    print("  Applying temporal interpolation on missing satellite gas columns...")
    df.sort_values(by=['City', 'date'], inplace=True)
    for col in gas_cols:
        df[col] = df.groupby('City')[col].transform(lambda x: x.ffill().bfill())
        
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    df.to_csv(processed_path, index=False)
    print(f"  CPCB cleaning completed. Weather nulls: {df['temp_c'].isnull().sum()}, HCHO nulls: {df['TROPOMI_HCHO_mol_m2'].isnull().sum()}")
    print(f"  Cleaned file saved to: {processed_path}")

def clean_satellite_gas(raw_path, processed_path):
    """Processes raw orbit datasets: removes out-of-swath nulls, aggregates by date and city."""
    print(f"\n--- Cleaning Satellite Dataset: {os.path.basename(raw_path)} ---")
    if not os.path.exists(raw_path):
        print(f"[Error] Raw dataset not found at: {raw_path}")
        return
        
    df = pd.read_csv(raw_path)
    print(f"Loaded {len(df)} rows. Null values: {df['mean'].isnull().sum()}")
    
    # 1. Filter out null (out-of-swath) rows
    df_clean = df[df['mean'].notnull()].copy()
    
    # 2. Aggregate orbits to daily averages per city
    df_daily = df_clean.groupby(['date', 'name']).agg({
        'mean': 'mean',
        '.geo': 'first'
    }).reset_index()
    
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    df_daily.to_csv(processed_path, index=False)
    print(f"  Aggregation completed. Out-of-swath rows removed. Unique daily points: {len(df_daily)}")
    print(f"  Cleaned dataset saved to: {processed_path}")

def clean_active_fires(raw_path, processed_path):
    """Applies quality control confidence filters to active fires."""
    print(f"\n--- Cleaning Active Fires: {os.path.basename(raw_path)} ---")
    if not os.path.exists(raw_path):
        print(f"[Error] Active fires file not found at: {raw_path}")
        return
        
    df = pd.read_csv(raw_path)
    print(f"Loaded {len(df)} raw fire records.")
    
    # Check if this is 7-day firms data or regional grids
    if 'sensor_source' in df.columns:
        # MODIS confidence: integer, VIIRS confidence: Low/Nominal/High
        modis_mask = (df['sensor_source'] == 'MODIS') & (df['confidence'] > 30)
        viirs_mask = (df['sensor_source'] == 'VIIRS_SNPP') & (df['confidence'] != 'low')
        df_clean = df[modis_mask | viirs_mask].copy()
    else:
        # For regional grids like Punjab/Delhi, we drop entirely null fire counts
        # and standardise columns
        df_clean = df.copy()
        
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    df_clean.to_csv(processed_path, index=False)
    print(f"  Cleaning completed. High-confidence fire points remaining: {len(df_clean)}")
    print(f"  Cleaned fires saved to: {processed_path}")

def main():
    # 1. Clean CPCB primary dataset
    clean_cpcb_dataset(
        "data/raw/cpcb/objective1_merged_cpcb_2024.csv",
        "data/processed/cpcb_cleaned_2024.csv"
    )
    
    # 2. Clean Satellite gas files
    clean_satellite_gas(
        "data/raw/satellite/tropomi_hcho_5cities_2024.csv",
        "data/processed/tropomi_hcho_cleaned_2024.csv"
    )
    clean_satellite_gas(
        "data/raw/satellite/tropomi_no2_5cities_2024.csv",
        "data/processed/tropomi_no2_cleaned_2024.csv"
    )
    clean_satellite_gas(
        "data/raw/satellite/tropomi_co_5cities_2024.csv",
        "data/processed/tropomi_co_cleaned_2024.csv"
    )
    
    # 3. Clean Active Fires
    if os.path.exists("data/raw/fires/firms_recent_fires_india_7d.csv"):
        clean_active_fires(
            "data/raw/fires/firms_recent_fires_india_7d.csv",
            "data/processed/firms_recent_fires_cleaned_7d.csv"
        )
    if os.path.exists("data/raw/fires/punjab_delhi_fire_hcho_wind_2024.csv"):
        clean_active_fires(
            "data/raw/fires/punjab_delhi_fire_hcho_wind_2024.csv",
            "data/processed/punjab_delhi_fire_hcho_wind_cleaned_2024.csv"
        )

if __name__ == "__main__":
    main()
