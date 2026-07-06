import os
import sys
import argparse
from datetime import datetime

def check_cds_credentials():
    """Checks if CDS API configuration is set up in env or home directory."""
    home_rc = os.path.expanduser("~/.cdsapirc")
    if not os.path.exists(home_rc) and not (os.getenv("CDSAPI_URL") and os.getenv("CDSAPI_KEY")):
        print("\n[Warning] Copernicus CDS API configuration not found.")
        print("Please create a '~/.cdsapirc' file containing:")
        print("  url: https://cds.climate.copernicus.eu/api/v2")
        print("  key: <your-personal-api-uid>:<your-personal-api-key>")
        print("You can get your credentials by registering at: https://cds.climate.copernicus.eu\n")
        return False
    return True

def download_era5_data(variables: list, years: list, months: list, bbox: list, output_path: str):
    """
    Downloads ERA5 reanalysis single levels data using the Copernicus cdsapi library.
    Crops spatially to bounding box and saves output as NetCDF.
    """
    if not check_cds_credentials():
        print("[Error] CDS API credentials missing. Exiting.")
        sys.exit(1)
        
    try:
        import cdsapi
    except ImportError:
        print("[Error] 'cdsapi' Python package is not installed. Run: pip install cdsapi")
        sys.exit(1)
        
    c = cdsapi.Client()
    
    # Format dates to string
    years_str = [str(y) for y in years]
    months_str = [str(m).zfill(2) for m in months]
    
    # Days (always pull full month for complete daily time series)
    days_str = [str(d).zfill(2) for d in range(1, 32)]
    
    # Standard times (6-hourly intervals for robust daily mean and wind profile representation)
    times_str = ["00:00", "06:00", "12:00", "18:00"]
    
    # CDS API request payload
    request_params = {
        'product_type': 'reanalysis',
        'variable': variables,
        'year': years_str,
        'month': months_str,
        'day': days_str,
        'time': times_str,
        # Spatially crop: North, West, South, East
        'area': bbox,
        'format': 'netcdf',
    }
    
    print(f"Submitting retrieval request to Copernicus Climate Data Store...")
    print(f"Target variables: {variables}")
    print(f"Target years: {years_str}, months: {months_str}")
    print(f"Spatial boundaries (N, W, S, E): {bbox}")
    print(f"Output destination: {output_path}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        c.retrieve('reanalysis-era5-single-levels', request_params, output_path)
        print(f"\nSuccess! Meteorological data saved to: {output_path}")
    except Exception as e:
        print(f"\n[Error] Retrieval failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Programmatic downloader for ERA5 Single Levels Meteorological data over India.")
    
    # Default variables cover: 10m Wind vectors (u,v), 2m Temperatures (dewpoint, air), surface pressure, boundary layer height, precip
    default_vars = [
        '10m_u_component_of_wind', '10m_v_component_of_wind',
        '2m_dewpoint_temperature', '2m_temperature',
        'boundary_layer_height', 'surface_pressure',
        'total_precipitation'
    ]
    
    parser.add_argument("--variables", type=str, default=",".join(default_vars), help="Comma-separated list of ERA5 variables.")
    parser.add_argument("--years", type=str, required=True, help="Comma-separated list of years (e.g. 2023,2024).")
    parser.add_argument("--months", type=str, default="1,2,3,4,5,6,7,8,9,10,11,12", help="Comma-separated list of months (1-12).")
    parser.add_argument("--bbox", type=str, default="38.5,68.0,6.5,97.5", help="Bounding box coords: North,West,South,East.")
    parser.add_argument("--output_path", type=str, default="data/raw/meteo/era5_meteo_raw.nc", help="Output file path (.nc).")
    
    args = parser.parse_args()
    
    vars_list = [v.strip() for v in args.variables.split(",")]
    years_list = [int(y.strip()) for y in args.years.split(",")]
    months_list = [int(m.strip()) for m in args.months.split(",")]
    bbox_list = [float(coord.strip()) for coord in args.bbox.split(",")]
    
    download_era5_data(vars_list, years_list, months_list, bbox_list, args.output_path)
