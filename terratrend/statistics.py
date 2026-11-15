"""Transparent, tested trend statistics for annual Earth-system series."""

from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, linregress, theilslopes


def prepare_annual_series(
    frame: pd.DataFrame,
    value_col: str = "value",
    date_col: str = "date",
    aggregation: str = "mean",
    min_coverage: float = 0.9,
) -> pd.DataFrame:
    """Aggregate valid daily observations to annual values and flag incomplete years."""
    if frame.empty:
        return pd.DataFrame(columns=["year", "value", "n_valid", "n_expected", "coverage"])
    data = frame[[date_col, value_col]].copy()
    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
    data[value_col] = pd.to_numeric(data[value_col], errors="coerce")
    data = data.dropna(subset=[date_col]).drop_duplicates(subset=[date_col])
    data = data.dropna(subset=[value_col])
    data["year"] = data[date_col].dt.year
    grouped = []
    for year, part in data.groupby("year"):
        expected = 366 if pd.Timestamp(year=year, month=12, day=31).is_leap_year else 365
        agg = part[value_col].sum() if aggregation == "sum" else part[value_col].mean()
        grouped.append({"year": int(year), "value": float(agg), "n_valid": int(len(part)),
                        "n_expected": expected, "coverage": float(len(part) / expected)})
    result = pd.DataFrame(grouped).sort_values("year").reset_index(drop=True)
    result["usable"] = result["coverage"] >= min_coverage
    return result


def _normal_two_sided_p(z: float) -> float:
    return float(2 * NormalDist().cdf(-abs(z)))


def mann_kendall(values: np.ndarray, modified: bool = False) -> dict:
    """Mann-Kendall test with tie correction and optional lag-1 adjustment.

    The modified result is a conservative Hamed-Rao-style effective sample-size
    correction using the observed lag-1 autocorrelation. It is reported as a
    warning-bearing sensitivity result, not as a replacement for a full seasonal MK.
    """
    y = np.asarray(values, dtype=float)
    y = y[np.isfinite(y)]
    n = len(y)
    if n < 4:
        return {"n": n, "s": 0, "tau": np.nan, "z": np.nan, "p_value": np.nan, "autocorrelation": np.nan}
    diffs = y[np.newaxis, :] - y[:, np.newaxis]
    s = int(np.sign(np.triu(diffs, 1)).sum())
    _, counts = np.unique(y, return_counts=True)
    tie_term = sum(int(t) * (int(t) - 1) * (2 * int(t) + 5) for t in counts if t > 1)
    variance = (n * (n - 1) * (2 * n + 5) - tie_term) / 18
    # Estimate serial dependence from detrended residuals. Raw trend values are
    # naturally autocorrelated; treating that deterministic trend as noise would
    # over-correct the significance test and hide genuine monotonic signals.
    x = np.arange(n, dtype=float)
    residuals = y - np.polyval(np.polyfit(x, y, 1), x)
    residual_scale = float(np.std(residuals))
    acf1 = (float(pd.Series(residuals).autocorr(lag=1))
            if n > 2 and residual_scale > 1e-10 * max(1.0, float(np.std(y))) else np.nan)
    effective_n = float(n)
    if modified and np.isfinite(acf1) and acf1 > 0:
        effective_n = max(2.0, n * (1 - acf1) / (1 + acf1))
        variance *= n / effective_n
    if s > 0:
        z = (s - 1) / math.sqrt(variance)
    elif s < 0:
        z = (s + 1) / math.sqrt(variance)
    else:
        z = 0.0
    tau_value = kendalltau(np.arange(n), y, nan_policy="omit").statistic
    tau = 0.0 if not np.isfinite(tau_value) and np.all(y == y[0]) else float(tau_value)
    return {"n": n, "s": s, "tau": tau, "z": float(z), "p_value": _normal_two_sided_p(float(z)),
            "autocorrelation": acf1, "effective_n": effective_n}


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    """Return BH-adjusted q-values in original order, preserving NaNs."""
    result = np.full(len(p_values), np.nan, dtype=float)
    valid = [(i, float(p)) for i, p in enumerate(p_values) if np.isfinite(p)]
    m = len(valid)
    if not m:
        return result.tolist()
    ordered = sorted(valid, key=lambda item: item[1])
    running = 1.0
    for rank in range(m, 0, -1):
        index, p = ordered[rank - 1]
        running = min(running, p * m / rank)
        result[index] = min(1.0, running)
    return result.tolist()


def analyze_series(
    annual: pd.DataFrame,
    label: str = "Location",
    alpha: float = 0.05,
    modified_mk: bool = True,
) -> dict:
    """Estimate descriptive and non-parametric trends from a prepared annual series."""
    if annual.empty:
        usable = annual.copy()
    elif "usable" in annual.columns:
        usable = annual[annual["usable"]].copy()
    else:
        usable = annual.copy()
    usable = usable.dropna(subset=["year", "value"])
    n = len(usable)
    base = {"label": label, "n": n, "start_year": None, "end_year": None, "missing_pct": None,
            "mean_daily_coverage_pct": None,
            "slope_per_year": np.nan, "slope_per_decade": np.nan, "sen_slope_per_year": np.nan,
            "sen_slope_per_decade": np.nan, "sen_low_per_decade": np.nan, "sen_high_per_decade": np.nan,
            "ols_p_value": np.nan, "mk_p_value": np.nan, "mk_q_value": np.nan, "mk_tau": np.nan,
            "autocorrelation": np.nan, "classification": "Insufficient data", "warning": None}
    if n < 5:
        return base
    years, values = usable["year"].to_numpy(float), usable["value"].to_numpy(float)
    slope, intercept, r_value, ols_p, std_err = linregress(years, values)
    # scipy.stats.theilslopes returns (slope, intercept, low_slope, high_slope).
    sen, _sen_intercept, low, high = theilslopes(values, years, alpha=1 - alpha)
    mk = mann_kendall(values, modified=modified_mk)
    base.update({"start_year": int(years.min()), "end_year": int(years.max()),
                 "missing_pct": float(100 * (1 - n / max(1, int(years.max() - years.min() + 1)))),
                 "mean_daily_coverage_pct": float(100 * usable["coverage"].mean()) if "coverage" in usable else None,
                 "slope_per_year": float(slope), "slope_per_decade": float(slope * 10),
                 "sen_slope_per_year": float(sen), "sen_slope_per_decade": float(sen * 10),
                 "sen_low_per_decade": float(low * 10), "sen_high_per_decade": float(high * 10),
                 "ols_p_value": float(ols_p), "mk_p_value": float(mk["p_value"]),
                 "mk_tau": float(mk["tau"]), "autocorrelation": float(mk["autocorrelation"]),
                 "warning": "Positive lag-1 autocorrelation detected; modified MK variance adjustment applied."
                 if modified_mk and np.isfinite(mk["autocorrelation"]) and mk["autocorrelation"] > 0.1 else None})
    return base


def classify(result: dict, q_value: float | None = None, alpha: float = 0.05) -> str:
    q = result.get("mk_q_value") if q_value is None else q_value
    if result.get("n", 0) < 5 or not np.isfinite(result.get("sen_slope_per_decade", np.nan)):
        return "Insufficient data"
    if not np.isfinite(q):
        return "Uncertain result"
    slope = result["sen_slope_per_decade"]
    if q <= alpha and slope > 0:
        return "Significant increasing trend"
    if q <= alpha and slope < 0:
        return "Significant decreasing trend"
    return "No statistically detectable trend"


def finalize_results(results: list[dict], alpha: float = 0.05) -> list[dict]:
    qs = benjamini_hochberg([r.get("mk_p_value", np.nan) for r in results])
    final = []
    for result, q in zip(results, qs):
        updated = dict(result)
        updated["mk_q_value"] = q
        updated["classification"] = classify(updated, q, alpha)
        final.append(updated)
    return final

