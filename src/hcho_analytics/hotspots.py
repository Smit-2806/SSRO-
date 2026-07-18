import os
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from scipy.spatial import ConvexHull

# Geodesic distance helper
def calculate_geodesic_distance(lat1, lon1, lat2, lon2):
    r = 6371.0 # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return r * c

def run_hotspot_detection(grid_path, output_catalog_path):
    print("=== Running DBSCAN Hotspot Detection Prototype ===")
    if not os.path.exists(grid_path):
        print(f"[Error] Gridded clean dataset not found at: {grid_path}")
        return
        
    df = pd.read_csv(grid_path)
    print(f"Loaded dataset: {len(df)} grid rows.")
    
    # 1. Percentile-based anomaly thresholding (95th percentile)
    hcho_threshold = df['hcho'].quantile(0.95)
    print(f"Computed 95th percentile HCHO threshold: {hcho_threshold:.6f} mol/m2")
    
    # Filter anomalies
    df_anom = df[df['hcho'] >= hcho_threshold].copy()
    print(f"Found {len(df_anom)} anomalous grid cells exceeding threshold.")
    
    if len(df_anom) == 0:
        print("No HCHO anomalies found. Exiting.")
        return
        
    # 2. DBSCAN Spatial Clustering
    # eps=0.15 degrees (approx 16.6 km), min_samples=3 cells
    coords = df_anom[['lat', 'lon']].values
    db = DBSCAN(eps=0.15, min_samples=3)
    labels = db.fit_predict(coords)
    df_anom['cluster_id'] = labels
    
    # Identify unique clusters (excluding noise label -1)
    unique_clusters = [l for l in np.unique(labels) if l != -1]
    print(f"DBSCAN clustered anomalies into {len(unique_clusters)} unique hotspots (noise cells: {list(labels).count(-1)}).")
    
    # Fire reference data
    # Extract fire locations from our grid dataset
    has_fire = (df['fire_nov'].notnull() & (df['fire_nov'] > 0)) | (df['fire_oct'].notnull() & (df['fire_oct'] > 0))
    fire_cells = df[has_fire].copy()
    
    hotspots_catalog = []
    
    # 3. Compute cluster statistics and spatial metrics
    for c_id in unique_clusters:
        df_c = df_anom[df_anom['cluster_id'] == c_id]
        
        # Centroid
        centroid_lat = df_c['lat'].mean()
        centroid_lon = df_c['lon'].mean()
        
        # HCHO Stats
        mean_hcho = df_c['hcho'].mean()
        max_hcho = df_c['hcho'].max()
        
        # Spatial Area using Convex Hull in km2
        # At latitude ~30 degrees N:
        # 1 degree latitude = ~111.1 km
        # 1 degree longitude = ~111.1 * cos(30) = ~96.2 km
        # Scale factor = 111.1 * 96.2 = ~10,688 km2 per degree squared
        scale_factor_deg2_to_km2 = 10688.0
        
        points = df_c[['lon', 'lat']].values
        if len(points) >= 3:
            try:
                hull = ConvexHull(points)
                # In 2D, ConvexHull.volume is the area
                area_km2 = hull.volume * scale_factor_deg2_to_km2
            except Exception:
                # Fallback if points are collinear
                area_km2 = len(df_c) * 240.0 # 0.15 * 0.15 deg cell is ~240 km2
        else:
            area_km2 = len(df_c) * 240.0
            
        # 4. Proximity to nearest active fire
        nearest_fire_dist = np.nan
        nearest_fire_frp = np.nan
        if not fire_cells.empty:
            dists = calculate_geodesic_distance(
                centroid_lat, centroid_lon, 
                fire_cells['lat'].values, fire_cells['lon'].values
            )
            min_idx = np.argmin(dists)
            nearest_fire_dist = dists[min_idx]
            
            # FRP intensity proxy (temperature excess above 300K)
            fire_val_nov = fire_cells.iloc[min_idx]['fire_nov']
            fire_val_oct = fire_cells.iloc[min_idx]['fire_oct']
            # Fallback to whichever is valid
            fire_val = fire_val_nov if not pd.isnull(fire_val_nov) else fire_val_oct
            nearest_fire_frp = max(0.0, fire_val - 300.0) if not pd.isnull(fire_val) else np.nan
            
        # Append record
        hotspots_catalog.append({
            'cluster_id': int(c_id),
            'centroid_lat': float(centroid_lat),
            'centroid_lon': float(centroid_lon),
            'area_km2': float(area_km2),
            'mean_hcho': float(mean_hcho),
            'max_hcho': float(max_hcho),
            'grid_cells_count': int(len(df_c)),
            'nearest_fire_distance_km': float(nearest_fire_dist),
            'nearest_fire_intensity_k': float(nearest_fire_frp)
        })
        
    if hotspots_catalog:
        df_catalog = pd.DataFrame(hotspots_catalog)
        os.makedirs(os.path.dirname(output_catalog_path), exist_ok=True)
        df_catalog.to_csv(output_catalog_path, index=False)
        print(f"\nSuccess! Cataloged {len(df_catalog)} hotspots.")
        print(f"Catalog saved to: {output_catalog_path}")
        print("\n--- Summary of Hotspots Catalog ---")
        print(df_catalog[['cluster_id', 'centroid_lat', 'centroid_lon', 'area_km2', 'mean_hcho', 'nearest_fire_distance_km']].to_string(index=False))
    else:
        print("No hotspots clustered.")

if __name__ == "__main__":
    run_hotspot_detection(
        "data/processed/punjab_delhi_fire_hcho_wind_cleaned.csv",
        "data/processed/hcho_hotspots_catalog.csv"
    )
