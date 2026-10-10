"""Guard against missing or duplicated Gold fact records."""

import unittest

import pandas as pd

from src.warehouse.bi_schema import _validate_fact_rows


class GoldIntegrityTests(unittest.TestCase):
    def test_exact_one_fact_per_source_listing(self):
        source = pd.DataFrame({"annonce_id": ["a", "b"]})
        fact = pd.DataFrame({"annonce_id": ["a", "b"]})
        _validate_fact_rows(source, fact)

    def test_empty_source_rejected(self):
        empty = pd.DataFrame({"annonce_id": pd.Series(dtype=str)})
        with self.assertRaisesRegex(ValueError, "empty"):
            _validate_fact_rows(empty, empty)

    def test_inner_join_loss_is_rejected(self):
        source = pd.DataFrame({"annonce_id": ["a", "b"]})
        fact = pd.DataFrame({"annonce_id": ["a"]})
        with self.assertRaisesRegex(ValueError, "expected 2 fact rows"):
            _validate_fact_rows(source, fact)

    def test_duplicate_fact_rows_are_rejected(self):
        source = pd.DataFrame({"annonce_id": ["a", "b"]})
        fact = pd.DataFrame({"annonce_id": ["a", "a"]})
        with self.assertRaisesRegex(ValueError, "duplicate fact IDs"):
            _validate_fact_rows(source, fact)

    def test_duplicate_source_ids_are_rejected(self):
        source = pd.DataFrame({"annonce_id": ["a", "a"]})
        with self.assertRaisesRegex(ValueError, "duplicate annonce_id"):
            _validate_fact_rows(source, source)


if __name__ == "__main__":
    unittest.main()
