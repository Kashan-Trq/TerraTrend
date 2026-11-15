from __future__ import annotations

import time
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from terratrenD.data import fetch_power_monthly, annualize_monthly, POWER_SOURCE_NOTE
from terratrenD.analysis import analyze_trend, benjamini_hochberg

st.set_page_config(
    page_title="TERRATREND | Earth System Change Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container {padding-top: 1.6rem; padding-bottom: 2.4rem; max-width: 1500px;}
    .hero {padding: 1.45rem 1.6rem; border: 1px solid rgba(80,130,120,.28);
           border-radius: 18px; background: linear-gradient(115deg, rgba(20,90,75,.10), rgba(50,110,150,.06));}
    .eyebrow {font-size:.76rem; letter-spacing:.12em; font-weight:700; color:#23836f;}
    .muted {color: #718096; font-size: .9rem;}
    .small-note {font-size:.82rem; color:#718096;}
    div[data-testid="stMetric"] {background: rgba(120,140,150,.07); border:1px solid rgba(120,140,150,.15);
        padding: 12px 14px; border-radius: 12px;}
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
    .stTabs [data-baseweb="tab"] {height: 44px; white-space: pre-wrap;}
</style>
""", unsafe_allow_html=True)

SITES = {
    "Lahore, Pakistan": (31.5204, 74.3587),
    "Karachi, Pakistan": (24.8607, 67.0011),
    "Islamabad, Pakistan": (33.6844, 73.0479),
    "Quetta, Pakistan": (30.1798, 66.9750),
    "Peshawar, Pakistan": (34.0151, 71.5249),
    "Multan, Pakistan": (30.1575, 71.5249),
    "Skardu, Pakistan": (35.2971, 75.6333),
    "Phoenix, USA": (33.4484, -112.0740),
    "Cairo, Egypt": (30.0444, 31.2357),
    "Manaus, Brazil": (-3.1190, -60.0217),
    "London, UK": (51.5072, -0.1276),
}

PARAMETERS = {
    "T2M": {
        "label": "Mean air temperature at 2 m",
        "unit": "°C",
        "annual": "day-weighted annual mean",
        "description": "Monthly mean 2-m air temperature.",
        "interpretation": "Positive slope means increasing annual mean temperature.",
    },
    "T2M_MAX": {
        "label": "Mean daily maximum temperature",
        "unit": "°C",
        "annual": "day-weighted annual mean of monthly daily maxima",
        "description": "Monthly mean of daily maximum 2-m air temperature.",
        "interpretation": "This is not the single hottest daily maximum in each year.",
    },
    "T2M_MIN": {
        "label": "Mean daily minimum temperature",
        "unit": "°C",
        "annual": "day-weighted annual mean of monthly daily minima",
        "description": "Monthly mean of daily minimum 2-m air temperature.",
        "interpretation": "This is not the single coldest daily minimum in each year.",
    },
    "PRECTOTCORR": {
        "label": "Corrected precipitation",
        "unit": "mm/year",
        "annual": "sum of monthly mean daily rates × days in month",
        "description": "Monthly mean daily precipitation rate, converted to annual accumulation.",
        "interpretation": "Annual totals are only calculated for complete 12-month years.",
    },
    "RH2M": {
        "label": "Relative humidity at 2 m",
        "unit": "%",
        "annual": "day-weighted annual mean",
        "description": "Monthly mean relative humidity at 2 m.",
        "interpretation": "Positive slope means increasing annual mean relative humidity.",
    },
    "WS10M": {
        "label": "Wind speed at 10 m",
        "unit": "m/s",
        "annual": "day-weighted annual mean",
        "description": "Monthly mean wind speed at 10 m.",
        "interpretation": "Positive slope means increasing annual mean 10-m wind speed.",
    },
}

st.markdown("""
<div class="hero">
  <div class="eyebrow">NASA SPACE APPS CHALLENGE 2026 · EARTH SYSTEM TREND DETECTIVE</div>
  <h1 style="margin:.35rem 0 .25rem 0;">🌍 TERRATREND</h1>
  <h3 style="margin:0 0 .55rem 0; font-weight:500;">Earth System Change Intelligence Platform</h3>
  <p style="margin:0; max-width:950px;">
    Explore long-term Earth-system changes using NASA data. Compare locations, estimate the
    magnitude of trends, and test whether observed changes are statistically supported.
  </p>
  <p class="small-note" style="margin:.8rem 0 0 0;">
    Research prototype · v0.1 · NASA POWER monthly meteorological time series
  </p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Analysis configuration")
    selected_sites = st.multiselect(
        "Comparison locations",
        options=list(SITES.keys()),
        default=["Lahore, Pakistan", "Karachi, Pakistan", "Skardu, Pakistan"],
        max_selections=6,
        help="Point-based comparison. NASA POWER returns model/reanalysis grid values for the selected coordinates.",
    )
    with st.expander("Add one custom location"):
        custom_name = st.text_input("Location name", value="Custom site")
        custom_lat = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=30.0, step=0.1, format="%.4f")
        custom_lon = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=70.0, step=0.1, format="%.4f")
        add_custom = st.checkbox("Include custom location", value=False)

    parameter = st.selectbox(
        "Earth-system variable",
        options=list(PARAMETERS.keys()),
        format_func=lambda x: f"{PARAMETERS[x]['label']} ({x})",
        index=0,
    )
    col_a, col_b = st.columns(2)
    with col_a:
        start_year = st.number_input("Start year", min_value=1981, max_value=2025, value=1981, step=1)
    with col_b:
        end_year = st.number_input("End year", min_value=1982, max_value=2025, value=2025, step=1)

    st.caption("NASA POWER meteorological monthly record: 1981 onward. The latest complete year is used as the default end year.")
    run_analysis = st.button("▶ Run NASA analysis", type="primary", use_container_width=True)

    st.divider()
    st.caption("No NASA API key is required for this public POWER endpoint.")
    st.caption("Data requests are cached for 24 hours.")

if start_year >= end_year:
    st.error("The end year must be later than the start year.")
    st.stop()

if not selected_sites and not add_custom:
    st.info("Select at least one comparison location in the sidebar.")
    st.stop()

locations: list[tuple[str, float, float]] = [
    (name, SITES[name][0], SITES[name][1]) for name in selected_sites
]
if add_custom:
    label = custom_name.strip() or "Custom site"
    if label in [x[0] for x in locations]:
        label = f"{label} (custom)"
    locations.append((label, float(custom_lat), float(custom_lon)))

if len(locations) > 6:
    st.warning("For the first version, select no more than six locations.")
    st.stop()

tab_overview, tab_method, tab_data = st.tabs(["📊 Trend explorer", "🧪 Methodology", "🛰️ Data & limitations"])

with tab_overview:
    st.subheader("Earth-system trend explorer")
    meta = PARAMETERS[parameter]
    st.write(f"**Selected variable:** {meta['label']} · **Unit:** {meta['unit']}")
    st.caption(meta["description"])

    if run_analysis:
        all_annual = []
        summary_rows = []
        errors = []
        progress = st.progress(0, text="Connecting to NASA POWER…")
        for i, (name, lat, lon) in enumerate(locations):
            try:
                monthly = fetch_power_monthly(
                    latitude=lat,
                    longitude=lon,
                    parameter=parameter,
                    start_year=int(start_year),
                    end_year=int(end_year),
                )
                annual = annualize_monthly(monthly, parameter)
                annual = annual[(annual["year"] >= int(start_year)) & (annual["year"] <= int(end_year))].copy()
                if annual.empty or len(annual) < 10:
                    raise ValueError(f"Only {len(annual)} valid annual observations; at least 10 are required.")
                result = analyze_trend(annual["year"].to_numpy(), annual["value"].to_numpy())
                annual["location"] = name
                annual["latitude"] = lat
                annual["longitude"] = lon
                all_annual.append(annual)
                summary_rows.append({
                    "Location": name,
                    "Latitude": lat,
                    "Longitude": lon,
                    "Years": f"{int(annual['year'].min())}–{int(annual['year'].max())}",
                    "N years": int(len(annual)),
                    "Sen slope / year": result["slope"],
                    "Sen slope / decade": result["slope"] * 10 if pd.notna(result["slope"]) else float("nan"),
                    "95% slope CI / year (low)": result["slope_ci_low"],
                    "95% slope CI / year (high)": result["slope_ci_high"],
                    "Hamed–Rao p": result["p_value"],
                    "Kendall tau": result["tau"],
                    "Trend": result["trend"],
                    "Method note": result["method_note"],
                })
            except Exception as exc:
                errors.append(f"{name}: {exc}")
            progress.progress((i + 1) / len(locations), text=f"Processed {i+1}/{len(locations)} locations")
        progress.empty()

        if all_annual:
            annual_df = pd.concat(all_annual, ignore_index=True)
            summary_df = pd.DataFrame(summary_rows)
            summary_df["BH-adjusted q"] = benjamini_hochberg(summary_df["Hamed–Rao p"].tolist())
            summary_df["Significant at q<0.05"] = summary_df["BH-adjusted q"] < 0.05
            st.session_state["terratrenD_annual"] = annual_df
            st.session_state["terratrenD_summary"] = summary_df
            st.session_state["terratrenD_parameter"] = parameter
            st.session_state["terratrenD_errors"] = errors
            st.session_state["terratrenD_run_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        else:
            st.error("No locations returned enough valid annual data. Check the coordinates, year range, or NASA POWER service.")
        if errors:
            for err in errors:
                st.warning(err)

    if "terratrenD_annual" in st.session_state and st.session_state.get("terratrenD_parameter") == parameter:
        annual_df = st.session_state["terratrenD_annual"]
        summary_df = st.session_state["terratrenD_summary"]
        errors = st.session_state.get("terratrenD_errors", [])

        sig_count = int(summary_df["Significant at q<0.05"].fillna(False).sum())
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Locations analysed", len(summary_df))
        c2.metric("Annual observations", len(annual_df))
        c3.metric("Significant trends", f"{sig_count}/{len(summary_df)}")
        c4.metric("Analysis period", f"{int(annual_df.year.min())}–{int(annual_df.year.max())}")

        st.markdown("### Annual time series")
        fig = go.Figure()
        palette = px.colors.qualitative.Safe
        for idx, name in enumerate(annual_df["location"].unique()):
            sub = annual_df[annual_df["location"] == name].sort_values("year")
            color = palette[idx % len(palette)]
            fig.add_trace(go.Scatter(
                x=sub["year"], y=sub["value"], mode="lines+markers",
                name=name, line=dict(color=color, width=2), marker=dict(size=5),
                hovertemplate=f"{name}<br>Year: %{{x}}<br>Value: %{{y:.3f}} {meta['unit']}<extra></extra>",
            ))
            row = summary_df[summary_df["Location"] == name]
            if not row.empty and pd.notna(row.iloc[0]["Sen slope / year"]):
                slope = float(row.iloc[0]["Sen slope / year"])
                intercept = float(sub["value"].median() - slope * sub["year"].median())
                xline = [int(sub["year"].min()), int(sub["year"].max())]
                yline = [slope * x + intercept for x in xline]
                fig.add_trace(go.Scatter(
                    x=xline, y=yline, mode="lines", name=f"{name} · Sen trend",
                    line=dict(color=color, width=2, dash="dash"), showlegend=False,
                    hoverinfo="skip",
                ))
        fig.update_layout(
            height=470, template="plotly_white", hovermode="x unified",
            xaxis_title="Year", yaxis_title=f"{meta['label']} ({meta['unit']})",
            legend_title="Location", margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Statistical trend summary")
        display_cols = [
            "Location", "Years", "N years", "Sen slope / decade",
            "95% slope CI / year (low)", "95% slope CI / year (high)",
            "Hamed–Rao p", "BH-adjusted q", "Kendall tau", "Trend", "Significant at q<0.05",
        ]
        view = summary_df[display_cols].copy()
        for col in ["Sen slope / decade", "95% slope CI / year (low)", "95% slope CI / year (high)", "Hamed–Rao p", "BH-adjusted q", "Kendall tau"]:
            view[col] = view[col].map(lambda x: round(float(x), 5) if pd.notna(x) else None)
        st.dataframe(view, use_container_width=True, hide_index=True)

        st.markdown("### Spatial comparison of selected points")
        map_df = summary_df.dropna(subset=["Sen slope / decade"]).copy()
        if not map_df.empty:
            map_fig = px.scatter_geo(
                map_df, lat="Latitude", lon="Longitude", color="Sen slope / decade",
                hover_name="Location",
                hover_data={"Trend": True, "Hamed–Rao p": ":.4f", "BH-adjusted q": ":.4f", "Latitude": ":.3f", "Longitude": ":.3f"},
                color_continuous_scale="RdBu_r", color_continuous_midpoint=0,
                projection="natural earth", size_max=16,
            )
            map_fig.update_traces(marker=dict(size=13, line=dict(width=0.7, color="white")))
            map_fig.update_layout(height=440, template="plotly_white", margin=dict(l=0, r=0, t=10, b=0),
                                  coloraxis_colorbar_title=f"{meta['unit']}/decade")
            st.plotly_chart(map_fig, use_container_width=True)
        else:
            st.info("No valid slopes available to map.")

        st.markdown("### Download results")
        csv = annual_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Download annual time-series CSV",
            data=csv,
            file_name=f"terratrenD_{parameter}_{start_year}_{end_year}.csv",
            mime="text/csv",
        )
        summary_csv = summary_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Download statistical summary CSV",
            data=summary_csv,
            file_name=f"terratrenD_summary_{parameter}.csv",
            mime="text/csv",
        )

        with st.expander("Interpretation and quality notes"):
            st.write(meta["interpretation"])
            st.write(
                "The p-value shown is from the Hamed–Rao modified Mann–Kendall test, which adjusts "
                "the variance for serial correlation. BH-adjusted q-values control the false discovery "
                "rate across the locations included in this run."
            )
            st.write(
                "The Sen slope confidence interval is calculated using scipy's Theil–Sen slope estimator. "
                "The annual aggregation and completeness rules are documented in the Methodology tab."
            )
            st.write(
                "A statistically significant trend is not proof of causation, nor does it establish "
                "that a change is practically important."
            )
        if errors:
            st.warning("Some locations could not be analysed: " + " | ".join(errors))
    else:
        st.info("Choose a variable, locations and period in the sidebar, then select **Run NASA analysis**.")
        st.markdown("#### Suggested first investigation")
        st.write("Compare long-term annual mean temperature across Lahore, Karachi and Skardu from 1981–2025.")
        st.write("Then repeat with corrected precipitation and relative humidity. Treat these as exploratory comparisons, not conclusions.")

with tab_method:
    st.subheader("Scientific methodology")
    st.markdown("""
**1. Data retrieval**

TERRATREND requests monthly point time series from the NASA POWER Temporal Monthly API. The selected parameter is retrieved separately for each coordinate.

**2. Annual aggregation**

- Temperature, relative humidity and wind speed: monthly values are combined into day-weighted annual means. A year is retained only when at least 10 months are available.
- Corrected precipitation: the API monthly mean daily rate (mm/day) is multiplied by the number of days in each month and summed. A precipitation year is retained only when all 12 months are available.

**3. Trend magnitude**

Theil–Sen / Sen slope estimates the median pairwise rate of change. The application reports the slope per year and per decade, with a 95% confidence interval for the slope.

**4. Trend significance**

The Hamed–Rao modified Mann–Kendall test is used to adjust the variance for serial autocorrelation. The p-value is then adjusted across selected locations using the Benjamini–Hochberg false-discovery-rate procedure.

**5. Interpretation**

- Increasing/decreasing describes the estimated monotonic direction.
- Statistical significance is assessed using the adjusted q-value (<0.05).
- Statistical significance does not prove causation.
- A point comparison is not a full gridded spatial analysis.
""")
    st.warning(
        "Prototype limitation: this first version analyses selected coordinate points. "
        "It does not yet calculate regional area-weighted trends from gridded raster data, "
        "perform seasonal Mann–Kendall analysis, or fuse meteorological and vegetation products."
    )

with tab_data:
    st.subheader("NASA data provenance")
    st.markdown(f"""
**Primary source:** NASA Prediction Of Worldwide Energy Resources (POWER), Temporal Monthly Point API.

**Underlying meteorological source:** NASA Global Modeling and Assimilation Office MERRA-2 reanalysis.

{POWER_SOURCE_NOTE}

**API documentation:** https://power.larc.nasa.gov/docs/services/api/temporal/monthly/

**Meteorological data-source documentation:** https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/

**Data access:** no API key is required for the public POWER endpoint.
""")
    st.markdown("### Important limitations")
    st.markdown("""
- NASA POWER meteorological variables are reanalysis/model-derived grid estimates, not direct measurements at the selected address.
- The native MERRA-2 meteorological grid is approximately 0.5° latitude × 0.625° longitude. Nearby coordinates may therefore resolve to the same grid cell.
- Point sampling is not equivalent to regional or watershed averaging.
- Reanalysis products can be revised; record the access date and exact request parameters in any formal research report.
- Precipitation and temperature are different physical variables and require different annual aggregation rules.
- The prototype's statistical analysis is exploratory. For publication-grade work, validate results against an independent dataset and examine structural breaks, seasonality, data homogeneity and spatial dependence.
""")
    st.markdown("### NASA data citation")
    st.code(
        "NASA POWER Project. Prediction Of Worldwide Energy Resources (POWER), "
        "Temporal Monthly Point API. NASA Langley Research Center. "
        "Accessed 2026-11-09. https://power.larc.nasa.gov/",
        language="text",
    )

st.divider()
st.caption("TERRATREND v0.1 · Built for NASA Space Apps Challenge 2026 · Research prototype, not an operational climate-warning service.")
