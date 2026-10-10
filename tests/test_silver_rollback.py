"""Verify failed Silver replacements preserve the previously committed table."""

import os
import unittest
from unittest.mock import patch

import pandas as pd
from sqlalchemy import text

from src.clean.clean_data import _replace_silver_table
from src.utils.db import get_engine
from src.utils.migrations import run_migrations


@unittest.skipUnless(os.getenv("TEST_POSTGRES") == "1", "Requires test PostgreSQL")
class SilverTransactionTests(unittest.TestCase):
    def test_failed_replacement_rolls_back_table_drop(self):
        run_migrations()
        engine = get_engine("silver")
        original = pd.DataFrame({"annonce_id": ["original"], "prix": [1000]})
        _replace_silver_table(original, engine)

        replacement = pd.DataFrame({"annonce_id": ["new"], "prix": [2000]})
        with patch.object(
            replacement, "to_sql", side_effect=RuntimeError("simulated insert error")
        ):
            with self.assertRaisesRegex(RuntimeError, "simulated insert error"):
                _replace_silver_table(replacement, engine)

        with engine.connect() as conn:
            actual = conn.execute(
                text("SELECT annonce_id, prix FROM silver.annonces_clean")
            ).all()
        self.assertEqual(actual, [("original", 1000)])


if __name__ == "__main__":
    unittest.main()
