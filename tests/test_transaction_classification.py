"""Ensure unclassified listings are not assigned a majority transaction label."""

import unittest

import pandas as pd

from src.clean.clean_data import (
    _infer_missing_transactions,
    _retain_supported_transactions,
)


class TransactionClassificationTests(unittest.TestCase):
    def test_unresolved_labels_are_not_converted_to_majority_class(self):
        source = pd.DataFrame({
            "transaction": ["vente", "vente", "location", None],
            "prix": [250000, 300000, 1000, 20000],
        })
        inferred = _infer_missing_transactions(source)
        source.loc[source["transaction"].isna(), "transaction"] = inferred
        retained = _retain_supported_transactions(source)
        self.assertEqual(retained["transaction"].tolist(), ["vente", "vente", "location"])

    def test_no_supported_records_raises_clear_error(self):
        with self.assertRaisesRegex(ValueError, "No listings"):
            _retain_supported_transactions(pd.DataFrame({"transaction": [None, "autre"]}))


if __name__ == "__main__":
    unittest.main()
