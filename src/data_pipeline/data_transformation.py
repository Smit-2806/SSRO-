import os
import pandas as pd
import numpy as np

def create_lag_features(processed_path, features_path, max_lags=3):
    """Generates temporal sliding-window lag features for training recurrent networks."""
    print("\n--- Engineering Temporal Lag Features ---")
    if not os.path.exists(processed_path):
        print(f"[Error] Processed dataset not found at: {processed_path}")
        return
        
    df = pd.read_csv(processed_path)
    df.sort_values(by=['City', 'date'], inplace=True)
    
    # Columns to lag
    lag_cols = [
        'CPCB_AQI', 'CPCB_PM25', 'CPCB_PM10', 
        'TROPOMI_HCHO_mol_m2', 'TROPOMI_NO2_mol_m2', 
        'temp_c', 'wind_speed_ms'
    ]
    
    # Create copy to append features
    df_features = df.copy()
    
    for col in lag_cols:
        for lag in range(1, max_lags + 1):
            col_name = f"{col}_lag{lag}"
            # Shift within each city group to avoid cross-boundary leaks
            df_features[col_name] = df_features.groupby('City')[col].shift(lag)
            
    # Drop rows that have NaN values due to lagging (the first 3 days of each city)
    df_features.dropna(subset=[f"{col}_lag{max_lags}" for col in lag_cols], inplace=True)
    
    os.makedirs(os.path.dirname(features_path), exist_ok=True)
    df_features.to_csv(features_path, index=False)
    print(f"  Temporal lag feature engineering completed. Shape: {df_features.shape}")
    print(f"  Features saved to: {features_path}")

def calculate_geodesic_distance(lat1, lon1, lat2, lon2):
    """Computes approximate geodesic distance in km using the Haversine formula."""
    r = 6371.0 # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return r * c

def calculate_bearing_angle(lat1, lon1, lat2, lon2):
    """Calculates the bearing angle (in radians) from point 1 to point 2."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    y = np.sin(dlon) * np.cos(lat2)
    x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
    return np.atan2(y, x)

def compute_wind_transport_influence(grid_path, features_path, decay_rate_km=50.0):
    """Computes wind-advected active fire plume score at each HCHO grid cell."""
    print("\n--- Engineering Wind Transport & Plume Advection Features ---")
    if not os.path.exists(grid_path):
        print(f"[Error] Gridded fire/wind dataset not found at: {grid_path}")
        return
        
    df = pd.read_csv(grid_path)
    
    # We identify active fires: cells where fire temperature (fire_nov or fire_oct) is active
    # For this dataset, the values denote brightness temperature (Kelvin), e.g., > 300K
    # Let's extract cells with valid fire readings
    has_nov_fire = df['fire_nov'].notnull() & (df['fire_nov'] > 0)
    has_oct_fire = df['fire_oct'].notnull() & (df['fire_oct'] > 0)
    
    fire_cells_nov = df[has_nov_fire].copy()
    fire_cells_oct = df[has_oct_fire].copy()
    
    # Pre-calculate wind speed and direction (in radians) for all cells
    df['wind_speed'] = np.sqrt(df['u_component_of_wind_10m']**2 + df['v_component_of_wind_10m']**2)
    # Wind direction (direction wind is blowing TO, in radians)
    df['wind_dir_rad'] = np.atan2(df['u_component_of_wind_10m'], df['v_component_of_wind_10m'])
    
    plume_scores_nov = []
    plume_scores_oct = []
    
    # Compute plume advection score for each cell
    for idx, row in df.iterrows():
        lat, lon = row['lat'], row['lon']
        u, v = row['u_component_of_wind_10m'], row['v_component_of_wind_10m']
        wind_dir = row['wind_dir_rad']
        
        # November Plume Score
        score_nov = 0.0
        for f_idx, f_row in fire_cells_nov.iterrows():
            f_lat, f_lon = f_row['lat'], f_row['lon']
            f_val = f_row['fire_nov'] - 300.0 # Use temperature excess as intensity proxy
            
            # Geodesic distance
            d = calculate_geodesic_distance(f_lat, f_lon, lat, lon)
            if d <= 100.0 and d > 0: # within 100km
                # Bearing from fire to current cell
                theta = calculate_bearing_angle(f_lat, f_lon, lat, lon)
                # Wind alignment coefficient
                align = np.max([0.0, np.cos(theta - wind_dir)])**2
                # Plume decay score
                score_nov += f_val * np.exp(-d / decay_rate_km) * align
        plume_scores_nov.append(score_nov)
        
        # October Plume Score
        score_oct = 0.0
        for f_idx, f_row in fire_cells_oct.iterrows():
            f_lat, f_lon = f_row['lat'], f_row['lon']
            f_val = f_row['fire_oct'] - 300.0
            
            d = calculate_geodesic_distance(f_lat, f_lon, lat, lon)
            if d <= 100.0 and d > 0:
                theta = calculate_bearing_angle(f_lat, f_lon, lat, lon)
                align = np.max([0.0, np.cos(theta - wind_dir)])**2
                score_oct += f_val * np.exp(-d / decay_rate_km) * align
        plume_scores_oct.append(score_oct)
        
    df['plume_score_nov'] = plume_scores_nov
    df['plume_score_oct'] = plume_scores_oct
    
    os.makedirs(os.path.dirname(features_path), exist_ok=True)
    df.to_csv(features_path, index=False)
    print(f"  Wind advection plume feature engineering completed. Shape: {df.shape}")
    print(f"  Features saved to: {features_path}")

def main():
    # 1. Generate lag features for AQI model
    create_lag_features(
        "data/processed/cpcb_cleaned_2024.csv",
        "data/features/aqi_features_lags.csv"
    )
    
    # 2. Compute plume transport scores for HCHO
    if os.path.exists("data/processed/punjab_delhi_fire_hcho_wind_cleaned_2024.csv"):
        compute_wind_transport_influence(
            "data/processed/punjab_delhi_fire_hcho_wind_cleaned_2024.csv",
            "data/features/hcho_fire_wind_features.csv"
        )

if __name__ == "__main__":
    main()
