"""Regression tests for sparse numeric values in Silver records."""

import unittest

import numpy as np
import pandas as pd

from src.clean.clean_data import _impute_required_integers


class RequiredNumericTests(unittest.TestCase):
    def test_group_and_global_fallback(self):
        records = pd.DataFrame({
            "ville": ["rabat", "rabat", "fes"],
            "type_bien": ["villa", "villa", "appartement"],
            "nb_chambres": [2.0, np.nan, np.nan],
            "nb_salles_bain": [1.0, np.nan, np.nan],
            "etage": [1.0, np.nan, np.nan],
            "annee_construction": [2020.0, np.nan, np.nan],
        })
        actual = _impute_required_integers(records)
        self.assertEqual(len(actual), 3)
        self.assertFalse(actual[["nb_chambres", "nb_salles_bain", "etage", "annee_construction"]].isna().any().any())
        self.assertEqual(int(actual.loc[2, "nb_chambres"]), 2)
        self.assertEqual(int(actual.loc[2, "annee_construction"]), 2020)

    def test_unresolvable_values_fail_without_invalid_int_cast(self):
        records = pd.DataFrame({
            "ville": ["rabat"],
            "type_bien": ["villa"],
            "nb_chambres": [np.nan],
            "nb_salles_bain": [np.nan],
            "etage": [np.nan],
            "annee_construction": [np.nan],
        })
        with self.assertRaisesRegex(ValueError, "No records"):
            _impute_required_integers(records)


if __name__ == "__main__":
    unittest.main()
