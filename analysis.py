from __future__ import annotations

import numpy as np
import pymannkendall as mk
from scipy.stats import theilslopes


def analyze_trend(years, values) -> dict:
    """Estimate Sen slope and Hamed-Rao modified Mann-Kendall significance."""
    x = np.asarray(years, dtype=float)
    y = np.asarray(values, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]

    if len(y) < 10:
        raise ValueError("At least 10 valid annual observations are required for this prototype.")
    if np.nanmax(y) == np.nanmin(y):
        return {
            "trend": "no variation",
            "slope": 0.0,
            "slope_ci_low": 0.0,
            "slope_ci_high": 0.0,
            "p_value": 1.0,
            "tau": 0.0,
            "method_note": "Constant series; no trend can be estimated.",
        }

    sen = theilslopes(y, x=x, alpha=0.95)
    slope = float(sen.slope)
    ci_low = float(sen.low_slope)
    ci_high = float(sen.high_slope)

    try:
        result = mk.hamed_rao_modification_test(y, alpha=0.05)
        p_value = float(result.p)
        tau = float(result.Tau)
        trend = str(result.trend)
        method_note = "Hamed–Rao modified Mann–Kendall test"
    except Exception as exc:
        # Do not silently substitute an uncorrected test: surface the problem.
        raise RuntimeError(f"Hamed–Rao Mann–Kendall calculation failed: {exc}") from exc

    if not np.isfinite(p_value):
        p_value = float("nan")

    return {
        "trend": trend,
        "slope": slope,
        "slope_ci_low": ci_low,
        "slope_ci_high": ci_high,
        "p_value": p_value,
        "tau": tau,
        "method_note": method_note,
    }


def benjamini_hochberg(p_values) -> list[float]:
    """Benjamini-Hochberg adjusted p-values (q-values), preserving input order."""
    p = np.asarray(p_values, dtype=float)
    q = np.full(p.shape, np.nan, dtype=float)
    valid = np.isfinite(p)
    pv = p[valid]
    m = len(pv)
    if m == 0:
        return q.tolist()

    order = np.argsort(pv)
    ranked = pv[order]
    adjusted = ranked * m / np.arange(1, m + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)

    q_valid = np.empty(m, dtype=float)
    q_valid[order] = adjusted
    q[valid] = q_valid
    return q.tolist()
