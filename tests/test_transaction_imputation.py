"""Regression tests for missing real estate transaction labels."""

import unittest

import pandas as pd

from src.clean.clean_data import _infer_missing_transactions


class TransactionInferenceTests(unittest.TestCase):
    def test_missing_labels_with_both_reference_categories(self):
        records = pd.DataFrame({
            "transaction": ["vente", "location", None, None, None],
            "prix": [200000, 1000, 200, 500000, 30000],
        })
        actual = _infer_missing_transactions(records)
        self.assertEqual(actual.iloc[2], "location")
        self.assertEqual(actual.iloc[3], "vente")
        self.assertTrue(pd.isna(actual.iloc[4]))

    def test_no_known_categories_keeps_values_missing(self):
        records = pd.DataFrame({
            "transaction": [None, None],
            "prix": [500, 200000],
        })
        actual = _infer_missing_transactions(records)
        self.assertTrue(actual.isna().all())

    def test_one_reference_category_does_not_infer_other_from_nan(self):
        records = pd.DataFrame({
            "transaction": ["location", None],
            "prix": [1000, 100],
        })
        actual = _infer_missing_transactions(records)
        self.assertEqual(actual.iloc[1], "location")


if __name__ == "__main__":
    unittest.main()
