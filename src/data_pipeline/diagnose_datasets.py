import os
import glob
import pandas as pd
import numpy as np

def diagnose_file(file_path):
    print(f"\n==================================================")
    print(f"DIAGNOSTIC FOR: {os.path.basename(file_path)}")
    print(f"Path: {file_path}")
    print(f"Size: {os.path.getsize(file_path)/1024:.2f} KB")
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.csv':
        try:
            df = pd.read_csv(file_path)
            print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Print columns, dtypes, and null rates
            print("\n--- Column Attributes ---")
            nulls = df.isnull().sum()
            dtypes = df.dtypes
            for col in df.columns:
                print(f" * {col:<28} ({dtypes[col]}): {nulls[col]} nulls ({nulls[col]/len(df)*100:.1f}%)")
            
            # Print numerical statistics
            num_cols = df.select_dtypes(include=[np.number]).columns
            if len(num_cols) > 0:
                print("\n--- Summary Statistics ---")
                stats = df[num_cols].describe().loc[['min', 'mean', 'max', 'std']]
                print(stats.to_string())
                
            # Print geographic boundaries
            lat_cols = [c for c in df.columns if 'lat' in c.lower()]
            lon_cols = [c for c in df.columns if 'lon' in c.lower()]
            if lat_cols and lon_cols:
                print(f"\n--- Geographic Bounds ---")
                print(f"  Latitude : {df[lat_cols[0]].min()} to {df[lat_cols[0]].max()}")
                print(f"  Longitude: {df[lon_cols[0]].min()} to {df[lon_cols[0]].max()}")
                
            # Print date/time span
            date_cols = [c for c in df.columns if any(k in c.lower() for k in ['date', 'time', 'year', 'month'])]
            if date_cols:
                print(f"\n--- Temporal Span ---")
                for dc in date_cols[:2]:
                    try:
                        converted = pd.to_datetime(df[dc], errors='coerce')
                        print(f"  \"{dc}\" range: {converted.min().date()} to {converted.max().date()} ({converted.nunique()} unique days)")
                    except:
                        pass
        except Exception as e:
            print(f"[Error] Failed to read CSV: {e}")
            
    elif ext == '.nc':
        # NetCDF file diagnosis
        try:
            import xarray as xr
            ds = xr.open_dataset(file_path)
            print(f"Format: NetCDF Dataset")
            print(f"Dimensions: {dict(ds.dims)}")
            print("\n--- Variables & Coordinates ---")
            for var in ds.data_vars:
                print(f" * {var:<28}: {ds[var].dims} {ds[var].dtype}")
            print("\n--- Geographic & Temporal Bounds ---")
            if 'lat' in ds.coords or 'latitude' in ds.coords:
                lat_key = 'lat' if 'lat' in ds.coords else 'latitude'
                print(f"  Latitude : {float(ds[lat_key].min())} to {float(ds[lat_key].max())}")
            if 'lon' in ds.coords or 'longitude' in ds.coords:
                lon_key = 'lon' if 'lon' in ds.coords else 'longitude'
                print(f"  Longitude: {float(ds[lon_key].min())} to {float(ds[lon_key].max())}")
            if 'time' in ds.coords:
                times = pd.to_datetime(ds['time'].values)
                print(f"  Time span: {times.min().date()} to {times.max().date()} ({len(times)} timepoints)")
        except ImportError:
            print("[Warning] 'xarray' or 'netcdf4' not installed. Cannot parse NetCDF headers.")
        except Exception as e:
            print(f"[Error] Failed to read NetCDF: {e}")
    else:
        print(f"Unsupported file format: {ext}")

def main():
    # Scan raw and processed directories
    target_dirs = ['data/raw', 'data/processed', 'Input Documents']
    found_files = []
    for d in target_dirs:
        if os.path.exists(d):
            found_files.extend(glob.glob(os.path.join(d, '**/*.csv'), recursive=True))
            found_files.extend(glob.glob(os.path.join(d, '**/*.nc'), recursive=True))
            
    # Remove duplicates
    unique_files = list(set([os.path.abspath(f) for f in found_files]))
    print(f"Found {len(unique_files)} datasets to diagnose.")
    
    for f in sorted(unique_files):
        diagnose_file(f)

if __name__ == "__main__":
    main()
