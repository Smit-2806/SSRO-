import os
import pandas as pd
import numpy as np

def run_source_attribution(catalog_path, output_path):
    print("=== Running HCHO Source Attribution & Ranking Engine ===")
    if not os.path.exists(catalog_path):
        print(f"[Error] Hotspots catalog not found at: {catalog_path}")
        return
        
    df = pd.read_csv(catalog_path)
    print(f"Loaded {len(df)} hotspots from catalog.")
    
    attributed_list = []
    
    for idx, row in df.iterrows():
        c_id = row['cluster_id']
        lat, lon = row['centroid_lat'], row['centroid_lon']
        mean_hcho = row['mean_hcho']
        fire_dist = row['nearest_fire_distance_km']
        fire_frp = row['nearest_fire_intensity_k']
        
        # 1. Compute Attribution / Intensity Score
        # Formula: mean_hcho * (1 + fire_frp / (fire_dist + 1))
        # Handle cases where fire data is missing
        if pd.isnull(fire_dist) or pd.isnull(fire_frp):
            attribution_score = mean_hcho
        else:
            attribution_score = mean_hcho * (1.0 + (fire_frp / (fire_dist + 1.0)))
            
        # 2. Apply Classification Logic Rules
        if not pd.isnull(fire_dist) and fire_dist <= 50.0 and fire_frp > 10.0:
            source_type = "Biomass Burning Dominated"
            evidence = f"Strong spatial proximity to active agricultural burns ({fire_dist:.1f} km) and high thermal fire intensity ({fire_frp:.1f} K excess)."
        elif pd.isnull(fire_dist) or fire_dist > 100.0 or fire_frp <= 2.0:
            source_type = "Industrial / Urban Dominated"
            evidence = f"No active fire sources within regional transport radius (nearest: {fire_dist:.1f} km) or negligible thermal signatures."
        else:
            source_type = "Mixed Influence (Urban + Biomass Transport)"
            evidence = f"Affected by downwind transport of biomass burning precursors (nearest fire: {fire_dist:.1f} km) combined with local urban baseline chemistry."
            
        attributed_list.append({
            'cluster_id': int(c_id),
            'centroid_lat': float(lat),
            'centroid_lon': float(lon),
            'area_km2': float(row['area_km2']),
            'mean_hcho': float(mean_hcho),
            'nearest_fire_distance_km': float(fire_dist) if not pd.isnull(fire_dist) else np.nan,
            'nearest_fire_intensity_k': float(fire_frp) if not pd.isnull(fire_frp) else np.nan,
            'attribution_score': float(attribution_score),
            'source_type': source_type,
            'evidence_log': evidence
        })
        
    df_attributed = pd.DataFrame(attributed_list)
    
    # 3. Sort by Attribution Score in descending order and Assign Ranks
    df_attributed.sort_values(by='attribution_score', ascending=False, inplace=True)
    df_attributed['rank'] = range(1, len(df_attributed) + 1)
    
    # Reorder columns for professional layout
    cols_order = [
        'rank', 'cluster_id', 'source_type', 'attribution_score', 'mean_hcho',
        'centroid_lat', 'centroid_lon', 'area_km2', 'nearest_fire_distance_km',
        'nearest_fire_intensity_k', 'evidence_log'
    ]
    df_attributed = df_attributed[cols_order]
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_attributed.to_csv(output_path, index=False)
    print(f"\nSuccess! Attributed and ranked {len(df_attributed)} HCHO hotspots.")
    print(f"Source catalog saved to: {output_path}")
    print("\n--- Ranked Source Attribution Summary ---")
    print(df_attributed[['rank', 'cluster_id', 'source_type', 'attribution_score', 'nearest_fire_distance_km']].to_string(index=False))

if __name__ == "__main__":
    run_source_attribution(
        "data/processed/hcho_hotspots_catalog.csv",
        "data/processed/source_attribution_catalog.csv"
    )
