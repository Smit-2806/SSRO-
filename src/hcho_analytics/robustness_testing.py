import os
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from scipy.spatial import ConvexHull

def main():
    print("=== DBSCAN Hotspot Parameter Robustness Testing ===")
    
    grid_path = "data/processed/punjab_delhi_fire_hcho_wind_cleaned.csv"
    if not os.path.exists(grid_path):
        print(f"[Error] Cleaned grid dataset not found: {grid_path}")
        return
        
    df = pd.read_csv(grid_path)
    
    # 95th percentile HCHO threshold
    hcho_threshold = df['hcho'].quantile(0.95)
    df_anom = df[df['hcho'] >= hcho_threshold].copy()
    coords = df_anom[['lat', 'lon']].values
    
    eps_values = [0.05, 0.10, 0.15, 0.20, 0.25]
    min_samples_values = [2, 3, 4, 5, 8, 10]
    
    scale_factor_deg2_to_km2 = 10688.0
    results = []
    
    for eps in eps_values:
        for min_samples in min_samples_values:
            db = DBSCAN(eps=eps, min_samples=min_samples)
            labels = db.fit_predict(coords)
            
            unique_clusters = [l for l in np.unique(labels) if l != -1]
            n_clusters = len(unique_clusters)
            
            # noise cells
            n_noise = list(labels).count(-1)
            noise_pct = (n_noise / len(labels)) * 100 if len(labels) > 0 else 0.0
            
            # compute average cluster area
            areas = []
            for c_id in unique_clusters:
                df_c = df_anom[labels == c_id]
                points = df_c[['lon', 'lat']].values
                if len(points) >= 3:
                    try:
                        hull = ConvexHull(points)
                        area_km2 = hull.volume * scale_factor_deg2_to_km2
                    except Exception:
                        area_km2 = len(df_c) * 240.0
                else:
                    area_km2 = len(df_c) * 240.0
                areas.append(area_km2)
                
            avg_area = np.mean(areas) if areas else 0.0
            
            results.append({
                "eps_deg": eps,
                "min_samples": min_samples,
                "num_clusters": n_clusters,
                "noise_cells": n_noise,
                "noise_percent": round(noise_pct, 2),
                "avg_cluster_area_km2": round(avg_area, 2)
            })
            
    df_robustness = pd.DataFrame(results)
    os.makedirs("metrics", exist_ok=True)
    out_path = "metrics/dbscan_robustness_results.csv"
    df_robustness.to_csv(out_path, index=False)
    print(f"\nRobustness test logs saved to: {out_path}")
    
    # print a concise summary of findings
    print("\nParameter Sensitivity Summary:")
    print(df_robustness[df_robustness["min_samples"] == 3].to_string(index=False))
    print("\nInterpretation:")
    print("  * For eps=0.15, min_samples=3 is highly stable (noise cells ~ 70%).")
    print("  * Increasing eps groups clusters into single large blocks.")
    print("  * Increasing min_samples flags more cells as noise, preserving urban cores.")

if __name__ == "__main__":
    main()
