"""Verify Gold property dimension uniqueness and conflicting ages."""

import unittest

import pandas as pd

from src.warehouse.bi_schema import _deduplicate_bien_dimensions


class PropertyDimensionTests(unittest.TestCase):
    def test_identical_dimension_keys_collapse(self):
        rows = pd.DataFrame({
            "type_id": [1, 1, 2],
            "construction_id": [3, 3, 3],
            "caracteristique_id": [4, 4, 4],
            "age_estime": [6, 6, 5],
        })
        result = _deduplicate_bien_dimensions(rows)
        self.assertEqual(len(result), 2)

    def test_conflicting_ages_are_rejected(self):
        rows = pd.DataFrame({
            "type_id": [1, 1],
            "construction_id": [3, 3],
            "caracteristique_id": [4, 4],
            "age_estime": [6, 7],
        })
        with self.assertRaisesRegex(ValueError, "multiple ages"):
            _deduplicate_bien_dimensions(rows)


if __name__ == "__main__":
    unittest.main()
