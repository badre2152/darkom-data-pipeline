"""Ensure failed Gold rebuilds preserve the previously committed warehouse."""

import os
import unittest
from unittest.mock import patch

import pandas as pd
from sqlalchemy import text

from src.utils.db import get_engine
from src.utils.migrations import run_migrations
from src.warehouse.bi_schema import build_warehouse


@unittest.skipUnless(os.getenv("TEST_POSTGRES") == "1", "Requires test PostgreSQL")
class GoldRollbackTests(unittest.TestCase):
    def test_failed_dimension_insertion_rolls_back_schema_rebuild(self):
        run_migrations()
        engine = get_engine("gold")
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS gold.fact_annonces CASCADE"))
            conn.execute(text("CREATE TABLE gold.fact_annonces (annonce_id TEXT PRIMARY KEY)"))
            conn.execute(text("INSERT INTO gold.fact_annonces VALUES ('original')"))

        source = pd.DataFrame({
            "annonce_id": ["new"],
            "ville": ["rabat"],
            "prix_par_m2": [50.0],
        })
        with patch("src.warehouse.bi_schema.pd.read_sql", return_value=source):
            with patch(
                "src.warehouse.bi_schema.pd.DataFrame.to_sql",
                side_effect=RuntimeError("forced dimension insert failure"),
            ):
                with self.assertRaisesRegex(RuntimeError, "forced dimension insert failure"):
                    build_warehouse()

        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT annonce_id FROM gold.fact_annonces")
            ).scalars().all()
        self.assertEqual(rows, ["original"])


if __name__ == "__main__":
    unittest.main()
