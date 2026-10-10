"""Verify staging replacement rolls back on insertion errors."""

import os
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import text

from src.staging.load_staging import load_staging
from src.utils.db import get_engine
from src.utils.migrations import run_migrations


@unittest.skipUnless(os.getenv("TEST_POSTGRES") == "1", "Requires test PostgreSQL")
class StagingRollbackTests(unittest.TestCase):
    def test_previous_staging_rows_survive_bad_import(self):
        run_migrations()
        engine = get_engine("bronze")
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.csv"
            bad = Path(tmp) / "bad.csv"
            good.write_text(
                "annonce_id,titre,ville\nabc,Original,Casa\n",
                encoding="utf-8",
            )
            bad.write_text(
                "annonce_id,column_not_in_staging\nxyz,Unexpected\n",
                encoding="utf-8",
            )
            self.assertEqual(load_staging(str(good)), 1)
            with self.assertRaises(Exception):
                load_staging(str(bad))
            with engine.connect() as conn:
                rows = conn.execute(
                    text("SELECT annonce_id FROM bronze.stg_annonces")
                ).scalars().all()
        self.assertEqual(rows, ["abc"])


if __name__ == "__main__":
    unittest.main()
