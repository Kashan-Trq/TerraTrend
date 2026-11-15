# TERRATREND demo script

## 90-second story

**Opening (0–15s).** “Climate change is not one line moving in one direction. The same Earth-system variable can behave differently in different places. TERRATREND helps us test that with NASA data and tells us how strong the evidence is.”

**Question (15–30s).** Open the Pakistan / Indus Basin map. Select `T2M`, choose Islamabad and Karachi, and set a long period such as 2000–2024. Explain that these are representative NASA POWER points, not ground stations or area-wide averages.

**Evidence (30–55s).** Run the analysis. Point to the annual time series, dashed descriptive lines, Theil–Sen rate per decade, 95% confidence interval, Kendall tau, Mann–Kendall p-value, and BH-adjusted q-value. Say the exact values shown by the live run; never pre-script a scientific conclusion.

**Discovery (55–72s).** Show the comparison finding. If the calculated slopes have opposite signs, call it a “trend divergence signal.” If they do not, explain the largest calculated contrast without implying causation. If q-values are not significant, say “no statistically detectable trend” plainly.

**Reproducibility (72–84s).** Download raw NASA data, the annual processed series, and the JSON analysis configuration/results. Open the Methodology tab to show data provenance, coverage rules, autocorrelation warning, and limitations.

**Close (84–90s).** “TERRATREND does not manufacture a dramatic answer. It makes Earth-system change inspectable: what changed, where, how fast, and how certain the evidence is.”

## Backup sequence

If the live endpoint is slow, use a shorter period first to prove the workflow, then rerun the long period. If a request fails, show the clear NASA error state and use the exported/reproducible workflow once connectivity returns. Do not substitute invented data.

