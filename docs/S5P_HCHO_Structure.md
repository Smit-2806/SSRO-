# Sentinel-5P TROPOMI HCHO Data Structure Reference

This reference document defines the file metadata, variable attributes, and quality thresholds for the **Sentinel-5P TROPOMI Level 3 Formaldehyde** dataset (`COPERNICUS/S5P/OFFL/L3_HCHO`).

---

## 1. Grid Dimensions & Coordinate Reference System (CRS)

* **Dimensions:**
  * `time`: Daily orbital acquisitions.
  * `latitude`: $0.05^\circ$ spacing (approx. $5.5\text{ km}$).
  * `longitude`: $0.05^\circ$ spacing (approx. $5.5\text{ km}$).
* **CRS:** EPSG:4326 (WGS 84 geographic coordinate system).

---

## 2. Variables & Attributes Schema

The following table outlines the NetCDF4 / GEE image bands used in our pipelines:

| Variable Name (NetCDF/GEE Key) | Data Type | Physical Unit | Valid Range | Scale / Offset | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`tropospheric_HCHO_column_number_density`** | Float32 | $\text{mol/m}^2$ | $0.0 \text{ to } 0.0015$ | $1.0 \text{ / } 0.0$ | Main vertical column density of formaldehyde in the troposphere. |
| **`tropospheric_HCHO_column_number_density_amf`** | Float32 | Unitless | $0.3 \text{ to } 5.0$ | $1.0 \text{ / } 0.0$ | Tropospheric Air Mass Factor (AMF) used to convert slant columns to vertical columns. |
| **`qa_value`** | UInt8 | Fraction | $0.0 \text{ to } 1.0$ | $0.01 \text{ / } 0.0$ | Quality Assurance value. 1.0 = clear sky, 0.0 = error/cloud. |
| **`cloud_fraction`** | Float32 | Fraction | $0.0 \text{ to } 1.0$ | $1.0 \text{ / } 0.0$ | Geometrical cloud fraction of the target pixel. |

---

## 3. Scientific Units Conversion

In literature, HCHO vertical columns are often reported in **molecules/$\text{cm}^2$** rather than the SI standard **mol/$\text{m}^2$**.

### Conversion Formula
To convert column density $C$ from $\text{mol/m}^2$ to $\text{molecules/cm}^2$:
$$C_{\text{molecules/cm}^2} = C_{\text{mol/m}^2} \times N_A \times 10^{-4}$$
Where:
* $N_A = 6.02214 \times 10^{23} \text{ mol}^{-1}$ (Avogadro's Constant).
* $10^{-4} \text{ m}^2/\text{cm}^2$ converts square meters to square centimeters.

### Combined Scale Factor
$$\text{Scale Factor} = 6.02214 \times 10^{19} \text{ molecules/mol}$$
* *Example:* A column density of $1.5 \times 10^{-4} \text{ mol/m}^2$ is equal to:
  $$(1.5 \times 10^{-4}) \times (6.02214 \times 10^{19}) \approx 9.03 \times 10^{15} \text{ molecules/cm}^2$$

---

## 4. Quality Control & Masking Protocol

To ensure high-grade data pipelines, the ingestion script must apply the following quality mask:

```python
# Python Preprocessing Quality Mask Template
import xarray as xr

def apply_hcho_quality_mask(ds: xr.Dataset) -> xr.Dataset:
    # 1. Keep pixels with qa_value >= 0.50 (removes cloud-covered scenes, snow, ice)
    qa_mask = ds['qa_value'] >= 0.50
    
    # 2. Keep pixels with cloud_fraction < 0.20 (strict cloud contamination filter)
    cloud_mask = ds['cloud_fraction'] < 0.20
    
    # Combine masks
    valid_mask = qa_mask & cloud_mask
    
    # Apply mask (sets invalid pixels to NaN)
    ds_masked = ds.where(valid_mask)
    return ds_masked
```
* *Justification:* A `qa_value` threshold of $0.5$ is the official recommendation by the Sentinel-5P product team to eliminate erroneous retrievals while keeping enough spatial coverage. Setting `cloud_fraction` $< 0.20$ guarantees that aerosol/trace gas optical paths are not blocked by cloud layers.
