"""TERRATREND Streamlit application."""

from __future__ import annotations

import json
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from terratrend.analysis import analyze_locations
from terratrend.catalogue import VARIABLES, get_variable
from terratrend.nasa import NASADataError, fetch_locations
from terratrend.regions import REGIONS

st.set_page_config(page_title="TERRATREND", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background: #f5f8fa; color: #102a43; }
    [data-testid="stSidebar"] { background: #0b1f33; }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #e7f5f5; }
    /* Keep labels light on the navy sidebar, but keep input values readable
       inside Streamlit's light controls. */
    [data-testid="stSidebar"] [data-baseweb="select"],
    [data-testid="stSidebar"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea { color: #102a43 !important; }
    [data-testid="stSidebar"] [data-baseweb="select"] { background: #ffffff !important; border-radius: 10px; }
    [data-testid="stSidebar"] [data-baseweb="tag"] { background: #0b8f87 !important; color: #ffffff !important; }
    [data-testid="stSidebar"] [data-baseweb="tag"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] [data-testid="stNumberInput"] input { background: #ffffff !important; }
    .hero { background: linear-gradient(135deg,#0b1f33 0%,#123d52 60%,#0d6b70 100%); padding: 2.2rem 2.4rem; border-radius: 18px; color: white; margin-bottom: 1.2rem; }
    .hero h1 { font-size: 2.5rem; margin: 0; letter-spacing: .02em; }
    .hero p { color: #cde9e8; font-size: 1.05rem; margin-bottom: 0; }
    .eyebrow { color: #6ee7d8; text-transform: uppercase; letter-spacing: .15em; font-size: .75rem; font-weight: 700; }
    .finding { border-left: 4px solid #0b8f87; background: white; padding: 1rem 1.2rem; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=86400, show_spinner=False)
def load_data(locations: tuple[tuple[str, float, float], ...], parameter: str, start: str, end: str) -> pd.DataFrame:
    return fetch_locations(locations, parameter, start, end)


def fmt(value, digits=3):
    return "—" if value is None or pd.isna(value) else f"{value:.{digits}f}"


def sidebar_controls():
    st.sidebar.markdown("## TERRATREND")
    st.sidebar.caption("Earth System Change Intelligence Platform")
    st.sidebar.divider()
    variable = st.sidebar.selectbox("Earth-system variable", list(VARIABLES), format_func=lambda x: f"{x} — {VARIABLES[x].name}")
    locations = st.sidebar.multiselect("Study locations", list(REGIONS), default=["Islamabad", "Karachi"])
    st.sidebar.caption("These are NASA POWER representative points, not area-wide averages.")
    with st.sidebar.expander("Add a custom coordinate"):
        add_custom = st.checkbox("Include custom point")
        custom_name = st.text_input("Point name", "Custom point")
        custom_lat = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=30.0, step=0.1)
        custom_lon = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=70.0, step=0.1)
    years = st.sidebar.slider("Analysis period", 1981, date.today().year - 1, (2000, min(2024, date.today().year - 1)))
    run = st.sidebar.button("Run NASA analysis", type="primary", use_container_width=True)
    custom = (custom_name.strip() or "Custom point", float(custom_lat), float(custom_lon)) if add_custom else None
    return variable, locations, years, run, custom


def map_panel(locations, custom=None):
    point_rows = [{"location": n, **REGIONS[n]} for n in locations]
    if custom is not None:
        point_rows.append({"location": custom[0], "lat": custom[1], "lon": custom[2], "description": "User-selected coordinate"})
    points = pd.DataFrame(point_rows)
    if points.empty:
        st.info("Choose at least one study location.")
        return
    fig = px.scatter_geo(points, lat="lat", lon="lon", text="location", hover_name="location", scope="world",
                         projection="natural earth", color_discrete_sequence=["#0b8f87"])
    fig.update_traces(marker={"size": 12, "line": {"width": 1, "color": "white"}}, textposition="top center")
    fig.update_geos(showland=True, landcolor="#e5edf0", showcountries=True, countrycolor="#aab8c2",
                    center={"lat": 30, "lon": 73}, lataxis_range=[20, 40], lonaxis_range=[60, 85])
    fig.update_layout(height=420, margin={"l": 0, "r": 0, "t": 0, "b": 0}, paper_bgcolor="white", geo_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def results_panel(raw, annual, results, variable):
    metadata = get_variable(variable)
    if annual.empty or not results:
        st.warning("NASA returned no usable observations for this selection.")
        return
    result_frame = pd.DataFrame(results)
    st.markdown("### What is changing?")
    cols = st.columns(min(4, len(results)))
    for col, result in zip(cols, results):
        with col:
            direction = "↑" if result["sen_slope_per_decade"] > 0 else "↓"
            st.metric(result["label"], f"{direction} {fmt(result['sen_slope_per_decade'])} {metadata.unit}/decade")
            st.caption(result["classification"])
    fig = px.line(annual, x="year", y="value", color="location", markers=True,
                  labels={"year": "Year", "value": f"{metadata.name} ({metadata.unit})", "location": "Location"})
    for result in results:
        part = annual[annual.location == result["label"]].dropna(subset=["value"])
        if len(part) >= 2:
            x0, x1 = part.year.min(), part.year.max()
            y0 = result["slope_per_year"] * x0 + (part.value.mean() - result["slope_per_year"] * part.year.mean())
            y1 = result["slope_per_year"] * x1 + (part.value.mean() - result["slope_per_year"] * part.year.mean())
            fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines", name=f"{result['label']} trend",
                                     line={"dash": "dash", "width": 2}))
    fig.update_layout(height=470, paper_bgcolor="white", plot_bgcolor="white", legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("### Evidence table")
    display = result_frame[["label", "start_year", "end_year", "n", "missing_pct", "mean_daily_coverage_pct", "sen_slope_per_decade",
                            "sen_low_per_decade", "sen_high_per_decade", "mk_tau", "mk_p_value", "mk_q_value", "classification"]].copy()
    display.columns = ["Location", "From", "To", "Years", "Missing annual %", "Mean daily coverage %", "Sen slope / decade", "CI low", "CI high", "Kendall tau", "MK p", "BH q", "Interpretation"]
    st.dataframe(display, use_container_width=True, hide_index=True)
    if len(results) >= 2:
        ordered = sorted(results, key=lambda item: item["sen_slope_per_decade"])
        low, high = ordered[0], ordered[-1]
        if low["sen_slope_per_decade"] < 0 < high["sen_slope_per_decade"]:
            st.markdown(f'<div class="finding"><b>Trend divergence signal.</b> {low["label"]} has an estimated {low["sen_slope_per_decade"]:.3f} {metadata.unit}/decade trend while {high["label"]} has {high["sen_slope_per_decade"]:.3f} {metadata.unit}/decade. This is a calculated spatial contrast; significance and data limitations should be read alongside it.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="finding"><b>Comparison finding.</b> The largest estimated contrast is between {low["label"]} and {high["label"]}: {low["sen_slope_per_decade"]:.3f} versus {high["sen_slope_per_decade"]:.3f} {metadata.unit}/decade. This comparison does not establish causation.</div>', unsafe_allow_html=True)
    for result in results:
        if result.get("warning"):
            st.caption(f"{result['label']}: {result['warning']}")
    st.markdown("### Reproducible outputs")
    c1, c2, c3 = st.columns(3)
    c1.download_button("Download raw NASA data", raw.to_csv(index=False), "terratrend_raw.csv", "text/csv")
    c2.download_button("Download annual series", annual.to_csv(index=False), "terratrend_annual.csv", "text/csv")
    c3.download_button("Download analysis JSON", json.dumps({"variable": metadata.as_dict(), "results": results}, indent=2, default=str), "terratrend_analysis.json", "application/json")


def main():
    st.markdown('<div class="hero"><div class="eyebrow">NASA Space Apps 2026 · Earth System Trend Detective</div><h1>TERRATREND</h1><p>Discover what is changing on Earth, where it is changing, how fast, and how certain we are.</p></div>', unsafe_allow_html=True)
    variable, selected, years, run, custom = sidebar_controls()
    tabs = st.tabs(["Overview", "Trend Detective", "Variable catalogue", "Methodology"])
    with tabs[0]:
        left, right = st.columns([1.35, 1])
        with left:
            st.markdown("### Investigate a real Earth-system question")
            st.write("TERRATREND combines NASA POWER reanalysis data with robust trend statistics so a user can compare how the same variable changes across different parts of a basin. The initial demonstration uses representative points across Pakistan and the Indus Basin context.")
            st.info("Start with two or more locations. Opposing slopes are a discovery signal—not a causal explanation.")
        with right:
            st.markdown("### Current study map")
            map_panel(selected, custom)
    with tabs[1]:
        st.markdown(f"### {get_variable(variable).name}")
        if not run:
            st.info("Choose a variable, locations, and period in the sidebar, then run the NASA analysis.")
        elif not selected and custom is None:
            st.warning("Select at least one location.")
        else:
            locs = [(name, REGIONS[name]["lat"], REGIONS[name]["lon"]) for name in selected]
            if custom is not None:
                locs.append(custom)
            try:
                with st.spinner("Retrieving NASA POWER daily data and calculating trends…"):
                    raw = load_data(tuple(locs), variable, f"{years[0]}-01-01", f"{years[1]}-12-31")
                    annual, results = analyze_locations(raw, variable)
                results_panel(raw, annual, results, variable)
            except NASADataError as exc:
                st.error(str(exc))
    with tabs[2]:
        st.markdown("### NASA variable catalogue")
        st.caption("Initial TERRATREND variables use NASA POWER's public daily point API. Coverage and resolution are documented as data-product properties, not as local observation density.")
        st.dataframe(pd.DataFrame([v.as_dict() for v in VARIABLES.values()]), use_container_width=True, hide_index=True)
    with tabs[3]:
        st.markdown("### Methods and limitations")
        st.markdown("""
**Data provenance.** NASA POWER provides access to meteorological parameters derived from the MERRA-2 reanalysis. These values are not direct ground-station measurements at every coordinate. TERRATREND labels the initial case study as a representative-point comparison.

**Aggregation.** Temperature, humidity, and wind are annual means. Corrected precipitation is an annual total of valid daily values. Years with less than 90% valid daily coverage are excluded from the trend calculation.

**Trend evidence.** Ordinary least squares is shown as a descriptive line. Magnitude is reported with Theil–Sen slope and a 95% confidence interval. Statistical evidence uses a tie-corrected Mann–Kendall test with a lag-1 autocorrelation variance sensitivity adjustment; Benjamini–Hochberg q-values control false-discovery risk across the selected locations.

**Interpretation.** Statistical significance is not causation. A non-significant trend is not proof of no change. Spatial resolution, model structure, missing observations, and the representative-point design limit local inference.

**Sources.** [NASA POWER API](https://power.larc.nasa.gov/docs/services/api/) · [NASA POWER methodology](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/)
        """)


if __name__ == "__main__":
    main()

