import os
import sys
import time
import requests
import argparse
import pandas as pd
from datetime import datetime, timedelta

def get_date_chunks(start_date: datetime, end_date: datetime, step_days: int = 10):
    """Splits a date range into sub-ranges of step_days length to satisfy FIRMS API limits."""
    curr = start_date
    while curr <= end_date:
        chunk_end = min(curr + timedelta(days=step_days - 1), end_date)
        yield curr, chunk_end
        curr += timedelta(days=step_days)

def download_firms_fires(map_key: str, start_date_str: str, end_date_str: str, bbox: str, output_dir: str):
    """
    Downloads active fire data from NASA FIRMS API for MODIS and VIIRS sensors.
    Applies rate-limit retries and saves output as a unified CSV.
    """
    # Parse boundaries and dates
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    # Sensors to download
    # MODIS_C61 = MODIS Standard, VIIRS_SNPP_NRT = Suomi NPP near-real-time, VIIRS_NOAA20_NRT = NOAA-20 near-real-time
    sensors = {
        "MODIS": "MODIS_SP",
        "VIIRS_SNPP": "VIIRS_SNPP_NRT",
        "VIIRS_NOAA20": "VIIRS_NOAA20_NRT"
    }
    
    os.makedirs(output_dir, exist_ok=True)
    all_data = []
    
    # Loop over date chunks (max 10 days per chunk)
    for s_date, e_date in get_date_chunks(start_date, end_date, step_days=10):
        days_range = (e_date - s_date).days + 1
        date_query = s_date.strftime("%Y-%m-%d")
        
        for sensor_name, sensor_code in sensors.items():
            print(f"Fetching {sensor_name} fires for {s_date.strftime('%Y-%m-%d')} to {e_date.strftime('%Y-%m-%d')}...")
            
            # API URL for Area Query (CSV format)
            url = f"https://firms.modaps.eosdis.nasa.gov/api/v1/area/csv/{map_key}/{sensor_code}/{bbox}/{days_range}/{date_query}"
            
            # Request with retries
            retries = 3
            backoff = 2
            success = False
            
            for attempt in range(retries):
                try:
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        # Parse CSV output
                        data_str = response.text
                        if len(data_str.strip()) > 0 and not data_str.startswith("No active fires"):
                            from io import StringIO
                            df = pd.read_csv(StringIO(data_str))
                            df['sensor_source'] = sensor_name
                            all_data.append(df)
                        success = True
                        break
                    elif response.status_code == 429:
                        # Rate limit reached
                        print(f"  [429] Rate limit reached. Backing off for {backoff}s...")
                        time.sleep(backoff)
                        backoff *= 2
                    else:
                        print(f"  [Error] HTTP {response.status_code} on attempt {attempt+1}.")
                        time.sleep(backoff)
                        backoff *= 2
                except Exception as e:
                    print(f"  [Exception] {e} on attempt {attempt+1}.")
                    time.sleep(backoff)
                    backoff *= 2
                    
            if not success:
                print(f"  Failed to retrieve data for {sensor_name} in range {s_date.date()} - {e_date.date()}")
            
            # Polite pause to respect API limits
            time.sleep(1.0)
            
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        # Sort by date and coordinates
        combined_df.sort_values(by=['acq_date', 'acq_time'], inplace=True)
        
        # Save output file
        filename = f"firms_active_fires_{start_date_str}_{end_date_str}.csv"
        out_path = os.path.join(output_dir, filename)
        combined_df.to_csv(out_path, index=False)
        print(f"\nSuccess! Downloaded {len(combined_df)} active fire records.")
        print(f"File saved to: {out_path}")
    else:
        print("\nNo active fire records found in the specified spatial-temporal window.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Programmatic downloader for NASA FIRMS Active Fire data over India.")
    parser.add_argument("--map_key", type=str, default=os.getenv("FIRMS_MAP_KEY"), help="Your NASA FIRMS Map Key.")
    parser.add_argument("--start_date", type=str, required=True, help="Start Date in YYYY-MM-DD format.")
    parser.add_argument("--end_date", type=str, required=True, help="End Date in YYYY-MM-DD format.")
    parser.add_argument("--bbox", type=str, default="68.0,6.5,97.5,38.5", help="Bounding box coordinates: WEST,SOUTH,EAST,NORTH.")
    parser.add_argument("--output_dir", type=str, default="data/raw/fires", help="Directory where raw files are saved.")
    
    args = parser.parse_args()
    
    if not args.map_key:
        print("[Error] NASA FIRMS Map Key not specified. Please provide via --map_key or set FIRMS_MAP_KEY environment variable.")
        sys.exit(1)
        
    download_firms_fires(args.map_key, args.start_date, args.end_date, args.bbox, args.output_dir)
