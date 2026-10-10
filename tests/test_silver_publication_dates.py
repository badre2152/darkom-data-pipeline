"""Ensure missing dates never inherit values from unrelated listings."""

import unittest

import pandas as pd

from src.clean.clean_data import _remove_missing_publication_dates


class PublicationDateTests(unittest.TestCase):
    def test_undated_listing_is_removed_without_changing_other_dates(self):
        records = pd.DataFrame({
            "annonce_id": ["a", "b", "c"],
            "date_publication": pd.to_datetime(["2026-01-01", None, "2026-03-01"]),
        })
        actual = _remove_missing_publication_dates(records)
        self.assertEqual(actual["annonce_id"].tolist(), ["a", "c"])
        self.assertEqual(actual["date_publication"].dt.strftime("%Y-%m-%d").tolist(),
                         ["2026-01-01", "2026-03-01"])

    def test_all_missing_dates_raise(self):
        records = pd.DataFrame({
            "date_publication": pd.to_datetime([None, None]),
        })
        with self.assertRaisesRegex(ValueError, "No listings"):
            _remove_missing_publication_dates(records)


if __name__ == "__main__":
    unittest.main()
