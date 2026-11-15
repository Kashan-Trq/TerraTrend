"""High-level preparation and comparison helpers."""

from __future__ import annotations

import pandas as pd

from .catalogue import get_variable
from .statistics import analyze_series, finalize_results, prepare_annual_series


def annualize_daily(frame: pd.DataFrame, parameter: str) -> pd.DataFrame:
    variable = get_variable(parameter)
    return prepare_annual_series(frame, aggregation="sum" if variable.aggregation == "annual total" else "mean")


def analyze_locations(frame: pd.DataFrame, parameter: str) -> tuple[pd.DataFrame, list[dict]]:
    """Prepare and analyze each location, with BH correction across the comparison."""
    rows, results = [], []
    for label, part in frame.groupby("location"):
        annual = annualize_daily(part, parameter)
        annual.insert(0, "location", label)
        rows.append(annual)
        results.append(analyze_series(annual, label=label))
    return (pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(), finalize_results(results))

