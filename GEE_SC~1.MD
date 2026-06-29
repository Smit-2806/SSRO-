# Google Earth Engine Scripts

## Setup

Python API:
```bash
pip install earthengine-api
earthengine authenticate
```

JavaScript: Use https://code.earthengine.google.com

---

## TROPOMI Pollutant Extraction (GEE JavaScript)

```javascript
// gee/tropomi_extract.js
// Run in GEE Code Editor — exports monthly mean TROPOMI L3 to Google Drive

var india = ee.Geometry.Rectangle([68.0, 6.5, 97.5, 37.5]);
var scale = 0.1;  // ~11 km resolution

// ---- Product catalogue ----
var PRODUCTS = {
  NO2:  {collection: 'COPERNICUS/S5P/OFFL/L3_NO2',  band: 'tropospheric_NO2_column_number_density', qa_band: 'qa_value'},
  SO2:  {collection: 'COPERNICUS/S5P/OFFL/L3_SO2',  band: 'SO2_column_number_density',              qa_band: 'qa_value'},
  CO:   {collection: 'COPERNICUS/S5P/OFFL/L3_CO',   band: 'CO_column_number_density',               qa_band: 'qa_value'},
  O3:   {collection: 'COPERNICUS/S5P/OFFL/L3_O3',   band: 'O3_column_number_density',               qa_band: 'qa_value'},
  HCHO: {collection: 'COPERNICUS/S5P/OFFL/L3_HCHO', band: 'tropospheric_HCHO_column_number_density',qa_band: 'qa_value'},
};

function exportMonthlyMean(productKey, startDate, endDate) {
  var p = PRODUCTS[productKey];
  var col = ee.ImageCollection(p.collection)
    .filterDate(startDate, endDate)
    .filterBounds(india)
    .filter(ee.Filter.gte(p.qa_band, 0.75))  // quality filter
    .select(p.band);

  var monthly = col.mean().clip(india);

  Export.image.toDrive({
    image: monthly,
    description: 'TROPOMI_' + productKey + '_' + startDate,
    folder: 'GEE_AQI',
    fileNamePrefix: 'tropomi_' + productKey.toLowerCase() + '_' + startDate,
    region: india,
    scale: scale,
    crs: 'EPSG:4326',
    maxPixels: 1e9,
  });
}

// Example: export NO2 for October 2023
exportMonthlyMean('NO2',  '2023-10-01', '2023-10-31');
exportMonthlyMean('HCHO', '2023-10-01', '2023-10-31');
```

---

## INSAT-3D AOD (GEE JavaScript)

INSAT-3D is not natively in GEE. Use the MODIS MAIAC AOD as proxy, or ingest INSAT data
via `ee.Image.loadGeoTIFF()` if you've uploaded it to GEE Assets.

```javascript
// MODIS MAIAC AOD (proxy if INSAT-3D is unavailable in GEE)
var maiac = ee.ImageCollection('MODIS/006/MCD19A2_GRANULES')
  .filterDate('2023-10-01', '2023-10-31')
  .filterBounds(india)
  .select('Optical_Depth_047');

var aod = maiac.mean().multiply(0.001).clip(india);  // scale factor

Export.image.toDrive({
  image: aod,
  description: 'MAIAC_AOD_Oct2023',
  folder: 'GEE_AQI',
  fileNamePrefix: 'aod_maiac_2023_10',
  region: india, scale: 1000, crs: 'EPSG:4326', maxPixels: 1e9
});
```

---

## MODIS/VIIRS Fire Counts (GEE JavaScript)

```javascript
// gee/fire_counts.js
var viirs = ee.ImageCollection('FIRMS')
  .filterDate('2023-10-01', '2023-11-30')
  .filterBounds(india)
  .select('T21');  // brightness temperature

// Count fire pixels per 0.25-degree grid cell
var fireCount = viirs.count().clip(india);

Export.image.toDrive({
  image: fireCount,
  description: 'VIIRS_FireCount_Oct-Nov2023',
  folder: 'GEE_AQI',
  fileNamePrefix: 'fire_count_oct_nov_2023',
  region: india, scale: 25000, crs: 'EPSG:4326', maxPixels: 1e9
});

// Time series at a point (e.g., Punjab IGP region)
var igp_point = ee.Geometry.Point([75.5, 30.5]);
var ts = viirs.map(function(img) {
  var val = img.reduceRegion({reducer: ee.Reducer.count(), geometry: igp_point.buffer(50000), scale: 375});
  return img.set('fire_count', val.get('T21'));
});
print(ts.aggregate_array('fire_count'));
```

---

## ERA5 Wind Fields (GEE Python API)

```python
# Python API — extract ERA5 u/v wind components for transport analysis
import ee
ee.Initialize()

india = ee.Geometry.Rectangle([68.0, 6.5, 97.5, 37.5])

era5 = (ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY")
    .filterDate("2023-10-01", "2023-11-30")
    .filterBounds(india)
    .select(["u_component_of_wind_10m", "v_component_of_wind_10m",
             "surface_pressure", "2m_temperature"]))

# Export daily mean wind
daily = era5.filterDate("2023-10-15", "2023-10-16").mean().clip(india)

task = ee.batch.Export.image.toDrive(
    image=daily,
    description="ERA5_wind_20231015",
    folder="GEE_AQI",
    fileNamePrefix="era5_wind_20231015",
    region=india,
    scale=25000,
    crs="EPSG:4326",
    maxPixels=int(1e9),
)
task.start()
print("Export started:", task.status())
```

---

## Batch Export Loop (Python API)

```python
import ee
from datetime import date, timedelta
ee.Initialize()

def daterange(start: str, end: str):
    d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)
    while d <= end_d:
        yield d.isoformat()
        d += timedelta(days=1)

india = ee.Geometry.Rectangle([68.0, 6.5, 97.5, 37.5])
COLLECTION = "COPERNICUS/S5P/OFFL/L3_HCHO"
BAND = "tropospheric_HCHO_column_number_density"

for day in daterange("2023-10-01", "2023-11-30"):
    next_day = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
    img = (ee.ImageCollection(COLLECTION)
           .filterDate(day, next_day)
           .filterBounds(india)
           .filter(ee.Filter.gte("qa_value", 0.75))
           .select(BAND)
           .mean()
           .clip(india))
    task = ee.batch.Export.image.toDrive(
        image=img,
        description=f"HCHO_{day.replace('-','')}",
        folder="GEE_HCHO",
        fileNamePrefix=f"hcho_{day.replace('-','')}",
        region=india, scale=11000, crs="EPSG:4326", maxPixels=int(1e9),
    )
    task.start()
print("All exports started.")
```
