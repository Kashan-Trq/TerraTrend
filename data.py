from __future__ import annotations

import calendar
import math
import re
from typing import Any

import pandas as pd
import requests
import streamlit as st

NASA_POWER_MONTHLY_POINT = "https://power.larc.nasa.gov/api/temporal/monthly/point"

POWER_SOURCE_NOTE = (
    "NASA POWER meteorological parameters are derived from the MERRA-2 assimilation "
    "system. NASA documents the meteorological record from January 1981 onward, with "
    "a native source grid of approximately 0.5° latitude × 0.625° longitude. "
    "The exact temporal coverage available depends on the parameter and access date."
)

@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def fetch_power_monthly(
    latitude: float,
    longitude: float,
    parameter: str,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """Fetch a monthly NASA POWER point time series and return date/value columns."""
    params = {
        "parameters": parameter,
        "community": "AG",
        "longitude": f"{longitude:.5f}",
        "latitude": f"{latitude:.5f}",
        "start": str(start_year),
        "end": str(end_year),
        "format": "JSON",
    }
    response = requests.get(NASA_POWER_MONTHLY_POINT, params=params, timeout=(15, 90))
    if response.status_code != 200:
        detail = response.text[:500].replace("\n", " ")
        raise RuntimeError(f"NASA POWER returned HTTP {response.status_code}: {detail}")
    payload: dict[str, Any] = response.json()

    try:
        values = payload["properties"]["parameter"][parameter]
    except (KeyError, TypeError) as exc:
        messages = payload.get("messages", [])
        raise RuntimeError(f"Unexpected NASA POWER response. Messages: {messages}") from exc

    rows = []
    for key, raw_value in values.items():
        key = str(key)
        if not re.fullmatch(r"\d{6}", key):
            continue
        year, month = int(key[:4]), int(key[4:])
        if not 1 <= month <= 12:
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(value) or value <= -900:
            continue
        rows.append({"date": pd.Timestamp(year=year, month=month, day=1), "year": year,
                     "month": month, "value": value})

    if not rows:
        raise RuntimeError("NASA POWER returned no valid monthly observations for this request.")
    frame = pd.DataFrame(rows).sort_values("date").drop_duplicates("date")
    return frame.reset_index(drop=True)


def annualize_monthly(monthly: pd.DataFrame, parameter: str) -> pd.DataFrame:
    """
    Convert monthly NASA POWER values to annual values.

    PRECTOTCORR is treated as a monthly mean daily rate (mm/day) and integrated
    over each month's calendar days. A precipitation year requires 12 valid months.
    Other listed variables are monthly means and are day-weighted; at least 10
    valid months are required.
    """
    if monthly.empty:
        return pd.DataFrame(columns=["year", "value", "months_present"])

    frame = monthly.copy()
    frame["days"] = frame.apply(
        lambda row: calendar.monthrange(int(row["year"]), int(row["month"]))[1], axis=1
    )
    rows = []
    for year, group in frame.groupby("year"):
        n_months = int(group["month"].nunique())
        # Require all 12 months for every annual statistic. This avoids
        # seasonal bias from a missing month in a day-weighted annual mean.
        if n_months != 12:
            continue
        if parameter == "PRECTOTCORR":
            # POWER monthly PRECTOTCORR is a mean daily rate (mm/day).
            annual_value = float((group["value"] * group["days"]).sum())
        else:
            annual_value = float((group["value"] * group["days"]).sum() / group["days"].sum())
        rows.append({"year": int(year), "value": annual_value, "months_present": n_months})

    if not rows:
        return pd.DataFrame(columns=["year", "value", "months_present"])
    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
