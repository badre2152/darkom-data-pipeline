"""Keep missing neighborhood values distinguishable from real locations."""

import unittest

import pandas as pd

from src.clean.clean_data import _normalize_unknown_neighborhoods


class NeighborhoodQualityTests(unittest.TestCase):
    def test_missing_and_blank_names_remain_unknown(self):
        values = pd.Series(["Agdal", None, " ", "Hay Riad"])
        actual = _normalize_unknown_neighborhoods(values)
        self.assertEqual(actual.tolist(), ["Agdal", "unknown", "unknown", "Hay Riad"])

    def test_neighborhood_name_is_not_borrowed_from_another_listing(self):
        values = pd.Series(["Maarif", None, "Maarif"])
        actual = _normalize_unknown_neighborhoods(values)
        self.assertEqual(actual.iloc[1], "unknown")


if __name__ == "__main__":
    unittest.main()
