# TERRATREND — Earth System Change Intelligence Platform

**NASA Space Apps Challenge 2026 · “Be An Earth System Trend Detective!”**

TERRATREND is an early research prototype for exploring long-term Earth-system changes using NASA POWER monthly meteorological data. It compares selected point locations, annualizes monthly observations, estimates trend magnitude with the Theil–Sen estimator, tests monotonic trend significance with the Hamed–Rao modified Mann–Kendall test, and applies Benjamini–Hochberg correction across the selected locations.

> **Status:** MVP v0.1. This is a point-based exploratory analysis tool, not a validated regional climate assessment or operational warning system.

## Features in v0.1

- NASA POWER monthly point API integration (no API key required).
- Variables: T2M, T2M_MAX, T2M_MIN, PRECTOTCORR, RH2M, WS10M.
- Built-in Pakistan and international comparison locations, plus one custom point.
- Annual aggregation with explicit completeness rules.
- Theil–Sen slope and 95% slope confidence interval.
- Hamed–Rao modified Mann–Kendall trend test.
- Benjamini–Hochberg q-values across selected locations.
- Interactive annual time-series plot and geographic point comparison.
- CSV downloads for annual observations and statistical summaries.
- Methodology and data limitations included in the application.

## Run locally

Python 3.11 is recommended.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit, normally `http://localhost:8501`.

## NASA data source

TERRATREND v0.1 uses the NASA POWER Temporal Monthly Point API:

- API: https://power.larc.nasa.gov/api/temporal/monthly/point
- Documentation: https://power.larc.nasa.gov/docs/services/api/temporal/monthly/
- Meteorological data sources: https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/

NASA POWER meteorological variables are derived from NASA GMAO MERRA-2 reanalysis. NASA documents a native meteorological grid of approximately 0.5° latitude × 0.625° longitude and a record beginning in January 1981. These are grid/model estimates, not station observations at the selected address.

## Annual aggregation rules

- Temperature, relative humidity and wind speed: day-weighted annual mean of monthly means; all 12 valid months required.
- PRECTOTCORR: monthly mean daily rate in mm/day is multiplied by the number of calendar days in that month and summed; all 12 months are required for an annual total.

The API parameter units and aggregation rules must be checked against the current NASA POWER parameter dictionary before expanding this prototype.

## Statistical method

1. Theil–Sen slope estimates the median pairwise rate of change.
2. Hamed–Rao modified Mann–Kendall test adjusts the variance for serial autocorrelation when assessing a monotonic trend.
3. Benjamini–Hochberg adjustment controls false discovery rate across the selected locations in one run.
4. A q-value below 0.05 is used as the exploratory significance threshold.

A statistically significant trend does not prove causation or practical importance. The slope confidence interval is the Theil–Sen slope interval returned by SciPy; it is not a confidence interval for the full climate system.

## Current limitations — do not hide these

- v0.1 analyses coordinate points, not area-weighted regional raster grids.
- It does not yet calculate seasonal Mann–Kendall tests or explicitly model structural breaks.
- It does not yet combine MODIS NDVI/EVI with meteorological variables.
- It does not establish causal relationships.
- Reanalysis estimates should be checked against independent station or gridded products before publication-grade claims.
- Nearby coordinates may map to the same underlying MERRA-2 grid cell.
- Data access date, API parameters, data completeness and processing version should be recorded for reproducibility.

## Planned next stages

- Regional/gridded analysis and area-weighted summaries.
- Seasonal trend analysis and sensitivity to selected time windows.
- MODIS MOD13Q1 vegetation index integration (NDVI/EVI).
- Spatial multiple-testing strategy and maps of trend significance.
- Independent comparison with another suitable dataset.
- Reproducible export of analysis configuration and provenance.

## Project structure

```text
TERRATREND_MVP/
├── app.py
├── requirements.txt
├── README.md
├── RUN_ON_WINDOWS.md
├── .gitignore
├── .streamlit/
│   └── config.toml
├── terratrenD/
│   ├── __init__.py
│   ├── analysis.py
│   └── data.py
├── scripts/
│   └── verify_nasa_power.py
└── tests/
    └── test_analysis.py
```

## Acknowledgement

This prototype uses publicly accessible NASA POWER data. NASA is not responsible for the interpretation or conclusions of this project and does not endorse this application.
