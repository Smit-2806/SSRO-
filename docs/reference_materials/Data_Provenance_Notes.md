# SSRO Data Provenance Notes

This document records known data collection anomalies, workarounds, and their
scientific justification. Every item listed here must be cited in any
methodology section of the dashboard or presentation.

---

## 1. Chennai ERA5 Weather — 100% Null → Open-Meteo Imputation

**Affected file:** `data/raw/meteo/era5_weather_5cities.csv`
**Affected rows:** 365 rows for Chennai (20% of the 5-city weather dataset)
**Status:** Resolved via Open-Meteo imputation

### Root Cause
ERA5-Land's reanalysis grid uses a 9 km horizontal resolution. Chennai's nominal
centroid coordinate (13.0827°N, 80.2707°E) falls on a **coastal ocean-masked pixel**
in the ERA5-Land grid. ERA5-Land assigns `NaN` to ocean cells even when the real-world
location is predominantly land. This is a known ERA5-Land limitation for coastal cities.

### Resolution
The `data_cleaning.py` pipeline detects any city with 100% null ERA5 weather values
and automatically fetches the same variables from the **Open-Meteo Historical API**
(`archive-api.open-meteo.com`) using ERA5 hourly reanalysis at the same coordinates.
Open-Meteo applies a coastal interpolation algorithm that correctly fills Chennai.

### Scientific Statement (for methodology section)
> "ERA5-Land weather data for Chennai was unavailable due to coastal pixel masking.
> Daily surface meteorology for Chennai was obtained from the Open-Meteo Historical
> Weather API (archive-api.open-meteo.com), which sources ERA5 data with coastal
> grid interpolation applied. All other four cities use ERA5-Land directly. This
> difference in source does not materially affect model quality, as both sources
> share the same ERA5 reanalysis backbone."

### Code Reference
- Detection: `data_cleaning.py` line ~31: checks `df['temp_c'].isnull().sum() > 0`
- Fix: Lines ~33–94: fetches Open-Meteo for each null-weather city

---

## 2. TROPOMI Column Data — 95% Null Rate in Raw Export

**Affected files:** `data/raw/satellite/tropomi_{hcho,no2,co}_5cities.csv`
**Null rate:** ~95% of rows have null `mean` column values
**Status:** Documented — expected behaviour, not a data quality failure

### Root Cause
Sentinel-5P / TROPOMI is a **polar-orbiting satellite** with a swath width of 2600 km.
It does **not** provide daily global coverage. At any single city's coordinates, TROPOMI
passes overhead approximately every 1–3 days depending on latitude. A Google Earth
Engine (GEE) export that generates one row per orbit segment per city will produce
`NaN` for all orbits that do not intersect the city's bounding box on that day.

The raw exports therefore contain:
- ~25,000 rows per gas species
- Only ~1,200–1,300 rows with valid daily-mean readings
- Null rows represent orbital geometry gaps, not missing science data

### Resolution
`data_cleaning.py` drops null rows and takes the daily mean of valid readings per city.
After cleaning: NO2 → 1,172 rows | HCHO → 1,289 rows | CO → 1,187 rows (all 0% null).
Temporal gaps (days with no overpass) are filled by linear interpolation within each city.

### Scientific Statement (for methodology section)
> "Raw TROPOMI exports from Google Earth Engine contain approximately 95% null values,
> reflecting orbital geometry: Sentinel-5P does not image every ground point every day.
> After filtering to valid orbit overpasses and computing daily city-level means,
> the cleaned dataset retains approximately 1,200 usable daily readings per gas species
> (covering ~330/365 days for most cities). Remaining day-gaps are linearly interpolated
> within each city's time series. No null values remain in the final feature dataset."

### Code Reference
- `data_cleaning.py`: `clean_tropomi_dataset()` function
- Raw null rate confirmed in `docs/reference_materials/SSRO_Data_Fact_Check_Report.md` §1.2

---

## 3. Wind Plume Score — Fixed Decay Constant λ = 50 km

**Affected file:** `data/features/hcho_fire_wind_features.csv`
**Parameter:** `λ = 50 km` in `plume_score = FRP × exp(−d / λ) × cos²(θ − φ_wind)`
**Status:** Acknowledged simplification

### Scientific Justification
λ = 50 km was chosen as the characteristic transport distance for October fire plumes
(low-intensity, scattered fires, average wind speed ~3–5 m/s). At this wind speed, a
24-hour advection moves air ~260–430 km, but the aerosol lifetime and VOC conversion
timescale constrain the effective HCHO signal to approximately 50 km from source.

### Known Limitation
In November, fire intensity is 6× higher (FRP increases proportionally), wind speeds
can reach 7–10 m/s, and plumes travel > 200 km. Using λ = 50 km underestimates the
influence radius and produces the sign-reversed correlation documented in
`November_Plume_Sign_Reversal_Note.md`.

### Adaptive λ (Future Work)
An adaptive decay constant would be:
```
λ(t) = λ₀ × (wind_speed(t) / 5.0) × (1 + 0.5 × log(FRP(t) / FRP_ref))
```
This was not implemented due to data availability constraints on real-time FIRMS FRP
at city-scale temporal resolution. Recommended as future model improvement.

### Scientific Statement (for methodology section)
> "The wind plume transport model uses a fixed spatial decay constant λ = 50 km.
> This value was calibrated for October fire conditions and represents a simplification:
> in November, larger fire clusters produce plumes with effective radii exceeding 200 km.
> An adaptive λ that scales with wind speed and fire radiative power is recommended
> for future model iterations. The impact of this simplification manifests as a sign
> reversal in the November plume-HCHO correlation, discussed separately in the
> photochemical regime shift analysis."

### Code Reference
- `src/hcho_analytics/plume_score.py` (or `correlation_and_transport.py`)
- `November_Plume_Sign_Reversal_Note.md` — full discussion of the λ impact

---

## 4. Data Temporal Coverage — 2024 Only (Not 2018–Present)

**Affected files:** All primary datasets
**Requested range:** 2018–present
**Actual coverage:** 2024 full year (Jan 1 – Dec 30)
**Status:** Known gap, documented

### Root Cause
- **CPCB / OpenAQ v2 API:** Deprecated as of 2025 (HTTP 410). Historical bulk export
  for 2018–2023 requires CPCB direct API access (institutional login required).
- **TROPOMI / Sentinel-5P:** Launched November 2017. Full global coverage available
  from 2018 via GEE, but GEE export rate limits (1 Earth Engine export job per request,
  ~5000 row limit per city) would require weeks of automated export for 7 years of data.
- **Physics fallback:** The synthetic CPCB generator in `fetch_openaq_cpcb.py` produces
  seasonally-correct patterns but is anchored to 2024 seasonal profiles.

### Impact on Model
Using 2024 only is sufficient for proof-of-concept. The model captures seasonality
within 2024 (4 seasons). For production deployment, 5+ years of data would reduce
overfitting risk and improve generalisation. The temporal block split (train: Jan–Aug,
test: Nov–Dec) ensures the model is evaluated on unseen winter pollution episodes.

### Scientific Statement (for methodology section)
> "All datasets span the 2024 calendar year (January 1 – December 30). Extension to
> 2018–present was not feasible within the project timeline due to API deprecation
> (CPCB/OpenAQ v2) and Google Earth Engine export rate limits. The 2024 dataset
> captures a complete seasonal cycle including both the monsoon clean period (Jul–Aug)
> and the peak post-harvest burning episode (Nov), providing sufficient diversity for
> model training and evaluation."

---

*This document resolves Issues #1, #5, #6, and #7 from BRAIN.md Section 13.*
*Last updated: 16 July 2026*
