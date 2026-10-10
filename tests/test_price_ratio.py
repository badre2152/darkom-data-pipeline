"""Check derived rental price per square meter for invalid surfaces."""

import unittest
import numpy as np
import pandas as pd
from src.clean.clean_data import _calculate_price_per_square_meter


class PriceRatioTests(unittest.TestCase):
    def test_zero_and_negative_surfaces_are_not_divided(self):
        records = pd.DataFrame({
            "prix": [1000.0, 2000.0, 100.0, np.nan],
            "surface": [20.0, 0.0, -10.0, 40.0],
        })
        result = _calculate_price_per_square_meter(records)
        self.assertEqual(result.iloc[0], 50.0)
        self.assertTrue(result.iloc[1:].isna().all())

    def test_zero_price_has_defined_ratio(self):
        records = pd.DataFrame({"prix": [0], "surface": [30]})
        self.assertEqual(_calculate_price_per_square_meter(records).iloc[0], 0.0)


if __name__ == "__main__":
    unittest.main()
