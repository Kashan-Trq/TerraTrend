import numpy as np
import pandas as pd

from terratrend.statistics import analyze_series, benjamini_hochberg, finalize_results, mann_kendall, prepare_annual_series


def annual(values):
    return pd.DataFrame({"year": np.arange(2000, 2000 + len(values)), "value": values, "usable": True})


def test_positive_trend_is_detected():
    result = analyze_series(annual(np.arange(10, dtype=float)), "positive")
    result = finalize_results([result])[0]
    assert result["sen_slope_per_decade"] > 0
    assert result["classification"] == "Significant increasing trend"


def test_negative_trend_is_detected():
    result = finalize_results([analyze_series(annual(-np.arange(10, dtype=float)), "negative")])[0]
    assert result["sen_slope_per_decade"] < 0
    assert result["classification"] == "Significant decreasing trend"


def test_constant_series_has_no_direction():
    result = finalize_results([analyze_series(annual(np.ones(10)), "constant")])[0]
    assert result["mk_tau"] == 0
    assert result["classification"] == "No statistically detectable trend"


def test_missing_daily_coverage_is_flagged():
    dates = pd.date_range("2020-01-01", "2021-12-31", freq="D")
    frame = pd.DataFrame({"date": dates, "value": 1.0})
    frame = frame.iloc[:-100]
    prepared = prepare_annual_series(frame)
    assert prepared["coverage"].min() < 0.9
    assert not prepared["usable"].all()


def test_bh_is_monotonic_and_preserves_order():
    q = benjamini_hochberg([0.001, 0.02, 0.5, np.nan])
    assert q[0] <= q[1] <= q[2]
    assert np.isnan(q[3])


def test_seasonal_like_series_has_finite_mk_result():
    x = np.arange(24)
    values = np.sin(2 * np.pi * x / 4) + x * 0.05
    result = mann_kendall(values)
    assert np.isfinite(result["p_value"])

