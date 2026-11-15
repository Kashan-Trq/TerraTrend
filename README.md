# TERRATREND

**Earth System Change Intelligence Platform**

TERRATREND is a NASA Space Apps 2026 prototype for the challenge **Be An Earth System Trend Detective!** It helps users discover what is changing, where it is changing, how fast, and how certain we are.

The first working slice uses the public NASA POWER daily point API and compares representative locations in Pakistan / the Indus Basin context. It computes annual aggregates, ordinary least-squares descriptive slopes, Theil–Sen slopes with confidence intervals, a tie-corrected Mann–Kendall test, an autocorrelation sensitivity warning, and Benjamini–Hochberg adjusted q-values across selected locations.

## Run locally

```powershell
cd work\terratrend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

The same commands work from the published `outputs\terratrend` folder. A project-local virtual environment keeps the runtime reproducible and avoids global Python permission issues.

Run tests:

```powershell
python -m pytest -q
```

The release suite includes six synthetic trend tests and a mocked NASA POWER connector test. It does not require live network access.

## Scientific integrity

NASA POWER meteorological values are reanalysis-derived estimates, not direct measurements at each point. The application therefore calls the initial comparison **representative-point analysis** and exposes coverage, uncertainty, data provenance, and methodological limitations.

Sources: [NASA POWER API](https://power.larc.nasa.gov/docs/services/api/) and [NASA POWER meteorology methodology](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/).

## Current scope

Implemented: live NASA retrieval, variable catalogue, selectable Pakistan locations, annual aggregation, trend statistics, q-value correction, interactive map and charts, raw/processed/JSON downloads, and synthetic validation tests.

Next high-value extensions: gridded regional aggregation, seasonal Mann–Kendall for monthly data, MODIS NDVI/EVI connector, a generated research report, and a polished demo narrative based only on live calculated results.

