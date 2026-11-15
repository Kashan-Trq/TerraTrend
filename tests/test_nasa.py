import pandas as pd

from terratrend.nasa import fetch_power_daily


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"properties": {"parameter": {"T2M": {"20200101": 8.98, "20200102": -999}}}}


class FakeSession:
    def get(self, url, params, timeout):
        assert "T2M" == params["parameters"]
        assert params["latitude"] == 33.6844
        assert params["longitude"] == 73.0479
        assert timeout == 30
        return FakeResponse()


def test_power_parser_preserves_provenance_and_masks_power_missing_value():
    frame = fetch_power_daily(33.6844, 73.0479, "T2M", "2020-01-01", "2020-01-02", session=FakeSession())
    assert list(frame["date"]) == list(pd.to_datetime(["2020-01-01", "2020-01-02"]))
    assert frame.loc[0, "value"] == 8.98
    assert pd.isna(frame.loc[1, "value"])
    assert frame.loc[0, "source"] == "NASA POWER (MERRA-2-derived)"

