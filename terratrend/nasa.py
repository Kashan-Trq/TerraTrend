"""NASA POWER connector with explicit provenance and defensive parsing."""

from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd
import requests

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_DOCS = "https://power.larc.nasa.gov/docs/services/api/"


class NASADataError(RuntimeError):
    """Raised when NASA POWER cannot return a usable response."""


def _date_token(value: str | date) -> str:
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    return pd.Timestamp(value).strftime("%Y%m%d")


def fetch_power_daily(
    latitude: float,
    longitude: float,
    parameter: str,
    start: str | date,
    end: str | date,
    timeout: int = 30,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch a daily NASA POWER point series and return date/value/provenance columns."""
    if not (-90 <= float(latitude) <= 90 and -180 <= float(longitude) <= 180):
        raise NASADataError("Latitude must be between -90 and 90 and longitude between -180 and 180.")
    start_token, end_token = _date_token(start), _date_token(end)
    if start_token > end_token:
        raise NASADataError("Start date must be before end date.")
    params = {
        "parameters": parameter,
        "community": "AG",
        "longitude": float(longitude),
        "latitude": float(latitude),
        "start": start_token,
        "end": end_token,
        "format": "JSON",
        "time-standard": "UTC",
    }
    client = session or requests.Session()
    try:
        response = client.get(POWER_URL, params=params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise NASADataError(f"NASA POWER request failed: {exc}") from exc
    try:
        values = payload["properties"]["parameter"][parameter]
    except (KeyError, TypeError) as exc:
        message = payload.get("messages") if isinstance(payload, dict) else None
        raise NASADataError(f"NASA POWER returned no {parameter} series. {message or ''}".strip()) from exc
    rows = []
    for token, raw_value in values.items():
        value = pd.to_numeric(raw_value, errors="coerce")
        if value == -999:
            value = float("nan")
        rows.append({"date": pd.to_datetime(token, format="%Y%m%d"), "value": value})
    frame = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    frame["latitude"] = float(latitude)
    frame["longitude"] = float(longitude)
    frame["parameter"] = parameter
    frame["source"] = "NASA POWER (MERRA-2-derived)"
    frame["source_url"] = POWER_DOCS
    return frame


def fetch_locations(
    locations: Iterable[tuple[str, float, float]], parameter: str, start: str, end: str
) -> pd.DataFrame:
    """Fetch multiple representative points, preserving a location column."""
    frames = []
    for name, lat, lon in locations:
        frame = fetch_power_daily(lat, lon, parameter, start, end)
        frame.insert(0, "location", name)
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)

