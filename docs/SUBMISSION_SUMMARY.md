# TERRATREND submission summary

## Short description

TERRATREND is an interactive Earth-system trend discovery engine that uses NASA POWER data to compare how temperature, precipitation, humidity, and wind change across locations. It combines long time series, robust trend magnitude estimates, statistical significance, uncertainty, multiple-testing correction, and reproducible exports so users can distinguish a visible pattern from statistically supported evidence.

## Challenge alignment

1. Selectable NASA Earth-science variables: variable catalogue with definitions, units, coverage, resolution, and limitations.
2. Geographical selection: Pakistan / Indus Basin presets plus custom latitude and longitude.
3. Long time series: configurable daily NASA POWER retrieval and annual aggregation.
4. Visualisation: map, annual time-series chart, and trend lines.
5. Magnitude/direction: Theil–Sen and OLS slopes per year and per decade.
6. Significance: tie-corrected Mann–Kendall, autocorrelation sensitivity adjustment, and BH q-values.
7. Interpretation: evidence table, divergence signal, coverage indicators, caveats, and downloads.

## Scientific integrity commitments

- NASA POWER values are labeled as MERRA-2-derived estimates, not direct station measurements.
- Representative-point comparisons are not presented as area-wide regional averages.
- Results are generated from the live API response; no scientific finding is hardcoded.
- Statistical significance is explicitly separated from causation and practical importance.

## Judging strengths

- **Best Use of Science:** the application makes the statistical reasoning visible and interpretable.
- **Best Use of Data:** NASA provenance, data limitations, coverage, and raw/processed exports are first-class product features.
- **Storytelling:** the user begins with a geographical question and ends with a reproducible, evidence-qualified comparison.

