import unittest
import pandas as pd

from terratrenD.analysis import benjamini_hochberg
from terratrenD.data import annualize_monthly


class TestAnnualization(unittest.TestCase):
    def test_temperature_requires_all_12_months(self):
        frame = pd.DataFrame({
            "year": [2001] * 11,
            "month": list(range(1, 12)),
            "value": [10.0] * 11,
        })
        result = annualize_monthly(frame, "T2M")
        self.assertEqual(len(result), 0)

    def test_temperature_annual_mean(self):
        frame = pd.DataFrame({
            "year": [2001] * 12,
            "month": list(range(1, 13)),
            "value": [10.0] * 12,
        })
        result = annualize_monthly(frame, "T2M")
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result.iloc[0]["value"], 10.0, places=8)

    def test_precipitation_annual_total(self):
        frame = pd.DataFrame({
            "year": [2001] * 12,
            "month": list(range(1, 13)),
            "value": [1.0] * 12,
        })
        result = annualize_monthly(frame, "PRECTOTCORR")
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result.iloc[0]["value"], 365.0, places=8)

    def test_precip_requires_12_months(self):
        frame = pd.DataFrame({
            "year": [2001] * 11,
            "month": list(range(1, 12)),
            "value": [1.0] * 11,
        })
        result = annualize_monthly(frame, "PRECTOTCORR")
        self.assertEqual(len(result), 0)

    def test_bh_adjustment(self):
        p = [0.01, 0.04, 0.03, 0.20]
        q = benjamini_hochberg(p)
        self.assertEqual(len(q), 4)
        self.assertTrue(all(0 <= x <= 1 for x in q))
        self.assertAlmostEqual(q[0], 0.04, places=8)


if __name__ == "__main__":
    unittest.main()
