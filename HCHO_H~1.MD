# HCHO Hotspot Detection & Fire Correlation — Objective 2

## 1. Load and Stack TROPOMI HCHO Data

```python
import xarray as xr
import numpy as np
from pathlib import Path

INDIA_BBOX = {"lon_min": 68.0, "lon_max": 97.5, "lat_min": 6.5, "lat_max": 37.5}

def load_hcho_stack(nc_dir: str) -> xr.DataArray:
    """
    Load all daily HCHO NetCDF files into a time-stacked DataArray.
    Files exported from GEE are named: hcho_YYYYMMDD.tif or .nc
    """
    files = sorted(Path(nc_dir).glob("hcho_*.nc"))
    arrays = []
    for f in files:
        da = xr.open_dataarray(f)
        date_str = f.stem.split("_")[1]
        da = da.expand_dims({"time": [np.datetime64(f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}")]})
        arrays.append(da)
    stack = xr.concat(arrays, dim="time")
    # Subset to India
    stack = stack.sel(
        x=slice(INDIA_BBOX["lon_min"], INDIA_BBOX["lon_max"]),
        y=slice(INDIA_BBOX["lat_min"], INDIA_BBOX["lat_max"])
    )
    return stack  # (time, y, x) in mol/m²
```

---

## 2. Identify Biomass Burning Periods Using Fire Counts

```python
import pandas as pd

def extract_burning_periods(firms_csv: str, lat_range=(6.5, 37.5),
                             lon_range=(68, 97.5), min_fires=500) -> pd.DatetimeIndex:
    """
    Return dates where fire counts exceed threshold — these are 'burning periods'.
    Uses FIRMS active fire CSV (https://firms.modaps.eosdis.nasa.gov/).
    """
    df = pd.read_csv(firms_csv, parse_dates=["acq_date"])
    df = df[df["latitude"].between(*lat_range) & df["longitude"].between(*lon_range)]
    df = df[df["confidence"] >= 80]

    daily_fires = df.groupby("acq_date").size().rename("fire_count")
    burning_days = daily_fires[daily_fires >= min_fires].index
    print(f"Found {len(burning_days)} high-fire days (>= {min_fires} fires/day)")
    return pd.DatetimeIndex(burning_days)
```

---

## 3. Hotspot Detection — Two Methods

### Method A: Statistical Threshold (95th percentile)

Simple, interpretable, good for spatial maps:

```python
def detect_hotspots_percentile(
    hcho_stack: xr.DataArray,
    dates: pd.DatetimeIndex = None,
    percentile: float = 95.0
) -> xr.DataArray:
    """
    Flag grid cells where HCHO exceeds the `percentile`th value.
    If `dates` is given, subset to burning-period days first.
    Returns a binary mask (1 = hotspot).
    """
    if dates is not None:
        subset = hcho_stack.sel(time=hcho_stack.time.isin(dates))
    else:
        subset = hcho_stack

    mean_hcho = subset.mean(dim="time")
    threshold = float(np.nanpercentile(mean_hcho.values, percentile))
    hotspot_mask = (mean_hcho >= threshold).astype(int)
    hotspot_mask.attrs["threshold_mol_m2"] = threshold
    return hotspot_mask
```

### Method B: DBSCAN Spatial Clustering

Better for identifying coherent source regions:

```python
from sklearn.cluster import DBSCAN
import geopandas as gpd
from shapely.geometry import Point

def detect_hotspots_dbscan(
    hcho_stack: xr.DataArray,
    dates: pd.DatetimeIndex = None,
    percentile_filter: float = 75.0,
    eps_deg: float = 1.0,
    min_samples: int = 5,
) -> gpd.GeoDataFrame:
    """
    1. Filter to top-percentile pixels
    2. Run DBSCAN to find spatially coherent clusters
    Returns a GeoDataFrame with cluster polygons and mean HCHO.
    """
    if dates is not None:
        data = hcho_stack.sel(time=hcho_stack.time.isin(dates)).mean(dim="time")
    else:
        data = hcho_stack.mean(dim="time")

    hcho_vals = data.values
    lons = data.x.values
    lats = data.y.values
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    # Flatten and filter to top percentile
    flat_hcho = hcho_vals.ravel()
    flat_lon  = lon_grid.ravel()
    flat_lat  = lat_grid.ravel()
    mask = ~np.isnan(flat_hcho)
    threshold = np.nanpercentile(flat_hcho, percentile_filter)
    mask &= (flat_hcho >= threshold)

    coords = np.column_stack([flat_lon[mask], flat_lat[mask]])

    # DBSCAN (eps in degrees ≈ ~110 km per degree)
    labels = DBSCAN(eps=eps_deg, min_samples=min_samples).fit_predict(coords)

    gdf_points = gpd.GeoDataFrame({
        "geometry": [Point(c) for c in coords],
        "hcho": flat_hcho[mask],
        "cluster": labels,
    }, crs="EPSG:4326")

    # Filter out noise (-1) and compute cluster convex hulls
    clusters = []
    for lbl in set(labels):
        if lbl == -1:
            continue
        grp = gdf_points[gdf_points["cluster"] == lbl]
        clusters.append({
            "cluster_id": lbl,
            "n_pixels": len(grp),
            "mean_hcho": grp["hcho"].mean(),
            "centroid_lon": grp.geometry.x.mean(),
            "centroid_lat": grp.geometry.y.mean(),
            "geometry": grp.unary_union.convex_hull,
        })
    return gpd.GeoDataFrame(clusters, crs="EPSG:4326")
```

---

## 4. Fire–HCHO Correlation

```python
import scipy.stats as stats
import matplotlib.pyplot as plt

def fire_hcho_correlation(
    hcho_stack: xr.DataArray,
    firms_csv: str,
    region_bbox: dict = None,   # e.g. {"lon_min":73,"lon_max":82,"lat_min":28,"lat_max":33} for IGP
) -> dict:
    """
    Compute Pearson correlation between daily fire counts and
    spatially averaged HCHO over a region (e.g., Indo-Gangetic Plain).
    """
    # Spatial mean HCHO per day
    if region_bbox:
        sub = hcho_stack.sel(
            x=slice(region_bbox["lon_min"], region_bbox["lon_max"]),
            y=slice(region_bbox["lat_min"], region_bbox["lat_max"])
        )
    else:
        sub = hcho_stack
    hcho_ts = sub.mean(dim=["x", "y"]).to_series().rename("hcho")

    # Daily fire counts
    df_fire = pd.read_csv(firms_csv, parse_dates=["acq_date"])
    if region_bbox:
        df_fire = df_fire[
            df_fire["latitude"].between(region_bbox["lat_min"], region_bbox["lat_max"]) &
            df_fire["longitude"].between(region_bbox["lon_min"], region_bbox["lon_max"])
        ]
    fire_ts = df_fire.groupby("acq_date").size().rename("fire_count")

    # Align time series
    merged = pd.concat([hcho_ts, fire_ts], axis=1).dropna()
    r, p = stats.pearsonr(merged["fire_count"], merged["hcho"])

    # Plot
    fig, ax1 = plt.subplots(figsize=(12, 4))
    ax2 = ax1.twinx()
    ax1.plot(merged.index, merged["hcho"], "b-", label="Mean HCHO (mol/m²)")
    ax2.bar(merged.index, merged["fire_count"], alpha=0.4, color="r", label="Fire count")
    ax1.set_ylabel("HCHO (mol/m²)", color="b")
    ax2.set_ylabel("Fire count", color="r")
    ax1.set_title(f"Fire–HCHO correlation  r={r:.3f}  p={p:.4f}")
    fig.tight_layout()
    plt.savefig("fire_hcho_correlation.png", dpi=150)
    plt.close()

    print(f"Pearson r = {r:.3f}, p-value = {p:.4f}")
    return {"r": r, "p_value": p, "n": len(merged)}
```

---

## 5. Wind Transport Analysis (ERA5)

```python
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

def plot_hcho_with_wind(
    hcho_map: xr.DataArray,
    era5_path: str,
    date: str,
    out_path: str = "hcho_wind_transport.png",
):
    """
    Overlay HCHO concentration with ERA5 850 hPa wind vectors
    to show transport pathways from fire source regions.
    """
    era5 = xr.open_dataset(era5_path)
    u = era5["u_component_of_wind_10m"].sel(time=date, method="nearest")
    v = era5["v_component_of_wind_10m"].sel(time=date, method="nearest")

    fig, ax = plt.subplots(figsize=(12, 10),
                           subplot_kw={"projection": ccrs.PlateCarree()})
    ax.set_extent([68, 97.5, 6.5, 37.5])
    ax.add_feature(cfeature.BORDERS, linewidth=0.8)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.STATES, linewidth=0.3, alpha=0.5)

    # HCHO filled contour
    cf = ax.contourf(hcho_map.x, hcho_map.y, hcho_map.values,
                     levels=20, cmap="YlOrRd", transform=ccrs.PlateCarree())
    plt.colorbar(cf, ax=ax, label="HCHO (mol/m²)", shrink=0.7)

    # Wind vectors (subsample every 5th point)
    skip = 5
    ax.quiver(u.longitude.values[::skip], u.latitude.values[::skip],
              u.values[::skip, ::skip], v.values[::skip, ::skip],
              transform=ccrs.PlateCarree(), scale=200, alpha=0.7, color="navy")

    ax.set_title(f"HCHO + Wind Transport — {date}", fontsize=13)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")
```

---

## 6. Spatio-temporal Animation (bonus)

```python
import matplotlib.animation as animation

def animate_hcho_time_series(hcho_stack: xr.DataArray, out_gif: str = "hcho_anim.gif"):
    """Create an animated GIF of daily HCHO maps over India."""
    vmin = float(np.nanpercentile(hcho_stack.values, 5))
    vmax = float(np.nanpercentile(hcho_stack.values, 99))

    fig, ax = plt.subplots(figsize=(8, 8),
                           subplot_kw={"projection": ccrs.PlateCarree()})
    ax.set_extent([68, 97.5, 6.5, 37.5])
    ax.add_feature(cfeature.BORDERS); ax.add_feature(cfeature.COASTLINE)

    frames = []
    for t in hcho_stack.time.values:
        im = ax.pcolormesh(hcho_stack.x, hcho_stack.y,
                           hcho_stack.sel(time=t).values,
                           vmin=vmin, vmax=vmax, cmap="hot_r",
                           transform=ccrs.PlateCarree())
        title = ax.set_title(str(t)[:10])
        frames.append([im, title])

    ani = animation.ArtistAnimation(fig, frames, interval=300, blit=False)
    ani.save(out_gif, writer="pillow", fps=4)
    plt.close()
    print(f"Animation saved: {out_gif}")
```
