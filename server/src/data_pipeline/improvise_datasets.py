import os
import urllib.request
import pandas as pd
import numpy as np
import json
import time

def download_open_firms_fires():
    """Downloads the keyless 7-day active fire CSVs from NASA FIRMS and crops them to India."""
    print("=== Step 1: Downloading open-access 7-day active fires from NASA FIRMS ===")
    
    # Bounding Box of India
    west, south, east, north = 68.0, 6.5, 97.5, 38.5
    
    urls = {
        "MODIS": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_7d.csv",
        "VIIRS_SNPP": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_NPP_VIIRS_C2_Global_7d.csv"
    }
    
    output_dir = "data/raw/fires"
    os.makedirs(output_dir, exist_ok=True)
    all_fires = []
    
    for sensor, url in urls.items():
        print(f"Fetching 7-day {sensor} global data from NASA...")
        try:
            temp_path = os.path.join(output_dir, f"temp_{sensor}.csv")
            urllib.request.urlretrieve(url, temp_path)
            
            # Read and filter spatially for India
            df = pd.read_csv(temp_path)
            df_india = df[
                (df['latitude'] >= south) & (df['latitude'] <= north) &
                (df['longitude'] >= west) & (df['longitude'] <= east)
            ].copy()
            
            df_india['sensor_source'] = sensor
            all_fires.append(df_india)
            print(f"  Found {len(df_india)} active fire points within India bounds.")
            
            # Clean up temp file
            os.remove(temp_path)
        except Exception as e:
            print(f"  [Error] Failed to fetch {sensor} fires: {e}")
            
    if all_fires:
        combined_df = pd.concat(all_fires, ignore_index=True)
        combined_df.sort_values(by=['acq_date', 'acq_time'], inplace=True)
        
        out_path = os.path.join(output_dir, "firms_recent_fires_india_7d.csv")
        combined_df.to_csv(out_path, index=False)
        print(f"Success! Saved combined 7-day active fires ({len(combined_df)} points) to: {out_path}")
    else:
        print("Failed to download any fire data.")

def calculate_relative_humidity(temp_c, dewpoint_c):
    """Calculates relative humidity from temperature and dewpoint using the Magnus-Tetens formula."""
    # Magnus-Tetens constants
    a = 17.625
    b = 243.04
    alpha = ((a * dewpoint_c) / (b + dewpoint_c)) - ((a * temp_c) / (b + temp_c))
    rh = 100.0 * np.exp(alpha)
    return np.clip(rh, 0.0, 100.0)

def fill_weather_gaps_open_meteo():
    """Fetches real historical reanalysis weather from Open-Meteo to fill gaps in CPCB weather columns."""
    print("\n=== Step 2: Imputing weather gaps in CPCB training table using Open-Meteo ===")
    
    local_path = "Input Documents/objective1_full_merged_with_weather_2024.csv"
    if not os.path.exists(local_path):
        print(f"[Error] Local merged CPCB file not found at: {local_path}")
        return
        
    df_cpcb = pd.read_csv(local_path)
    print(f"CPCB table loaded. Rows: {len(df_cpcb)}. Weather null count: {df_cpcb['temp_c'].isnull().sum()}")
    
    # Coordinate mapping for the 5 cities in our dataset
    cities_coords = {
        "Delhi": {"lat": 28.6139, "lon": 77.2090},
        "Mumbai": {"lat": 19.0760, "lon": 72.8777},
        "Chennai": {"lat": 13.0827, "lon": 80.2707},
        "Bangalore": {"lat": 12.9716, "lon": 77.5946},
        "Hyderabad": {"lat": 17.3850, "lon": 78.4867}
    }
    
    # We fetch the full year 2024 weather for each city in one API call
    weather_data_by_city = {}
    for city, coords in cities_coords.items():
        print(f"Querying Open-Meteo ERA5 Reanalysis for {city} (Lat {coords['lat']}, Lon {coords['lon']})...")
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
            df_hourly = pd.DataFrame({
                'datetime': pd.to_datetime(hourly['time']),
                'temp_c': hourly['temperature_2m'],
                'dewpoint_c': hourly['dewpoint_2m'],
                'precip_mm': hourly['precipitation'],
                'pressure_hpa': hourly['pressure_msl'],
                'wind_speed_ms': np.array(hourly['wind_speed_10m']) / 3.6, # Convert km/h to m/s
                'rel_humidity_pct': hourly['relative_humidity_2m']
            })
            
            # Aggregate hourly to daily averages
            df_hourly['date'] = df_hourly['datetime'].dt.strftime('%Y-%m-%d')
            df_daily = df_hourly.groupby('date').agg({
                'temp_c': 'mean',
                'dewpoint_c': 'mean',
                'precip_mm': 'sum', # Precipitation is accumulated
                'pressure_hpa': 'mean',
                'wind_speed_ms': 'mean',
                'rel_humidity_pct': 'mean'
            }).reset_index()
            
            # Map column names for API comparison
            df_daily.rename(columns={
                'temp_c': 'api_temp_c',
                'dewpoint_c': 'api_dewpoint_c',
                'precip_mm': 'api_precip_mm',
                'pressure_hpa': 'api_pressure_hpa',
                'wind_speed_ms': 'api_wind_speed_ms',
                'rel_humidity_pct': 'api_rel_humidity_pct'
            }, inplace=True)
            
            weather_data_by_city[city] = df_daily
            print(f"  Successfully aggregated {len(df_daily)} daily weather records for {city}.")
            time.sleep(1.0) # Polite rate limit pause
        except Exception as e:
            print(f"  [Error] Failed to fetch weather for {city}: {e}")
            
    # Impute missing values in the primary dataframe
    imputed_count = 0
    for idx, row in df_cpcb.iterrows():
        city = row['City']
        date = row['date']
        
        # Check if weather variables are null
        if pd.isnull(row['temp_c']) and city in weather_data_by_city:
            city_weather = weather_data_by_city[city]
            # Match by date
            match = city_weather[city_weather['date'] == date]
            if not match.empty:
                df_cpcb.at[idx, 'temp_c'] = match.iloc[0]['api_temp_c']
                df_cpcb.at[idx, 'dewpoint_c'] = match.iloc[0]['api_dewpoint_c']
                df_cpcb.at[idx, 'wind_speed_ms'] = match.iloc[0]['api_wind_speed_ms']
                df_cpcb.at[idx, 'pressure_hpa'] = match.iloc[0]['api_pressure_hpa']
                df_cpcb.at[idx, 'precip_mm'] = match.iloc[0]['api_precip_mm']
                df_cpcb.at[idx, 'rel_humidity_pct'] = match.iloc[0]['api_rel_humidity_pct']
                imputed_count += 1
                
    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "objective1_imputed_weather_2024.csv")
    df_cpcb.to_csv(out_path, index=False)
    
    print(f"\nSuccess! Imputed {imputed_count} daily weather records.")
    print(f"Final null count for temp_c: {df_cpcb['temp_c'].isnull().sum()}")
    print(f"Saved complete imputed dataset to: {out_path}")

if __name__ == "__main__":
    download_open_firms_fires()
    fill_weather_gaps_open_meteo()
