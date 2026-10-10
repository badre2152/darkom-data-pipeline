"""Regression tests for safe database URLs and schema validation."""

import os
import unittest
from unittest.mock import patch

from sqlalchemy.engine import URL

from src.utils.db import get_engine


class DatabaseConnectionTests(unittest.TestCase):
    @patch("src.utils.db.create_engine")
    def test_special_characters_are_preserved_in_credentials(self, create_engine):
        env = {
            "DB_USER": "name@domain",
            "DB_PASSWORD": "p@ss:/?# space",
            "DB_HOST": "localhost",
            "DB_PORT": "5433",
            "DB_NAME": "darkom_dwh",
        }
        with patch.dict(os.environ, env):
            get_engine("bronze")

        url = create_engine.call_args.args[0]
        self.assertIsInstance(url, URL)
        self.assertEqual(url.username, env["DB_USER"])
        self.assertEqual(url.password, env["DB_PASSWORD"])
        self.assertEqual(url.port, 5433)
        self.assertEqual(
            create_engine.call_args.kwargs["connect_args"]["options"],
            "-csearch_path=bronze",
        )

    @patch("src.utils.db.create_engine")
    def test_unapproved_schema_is_rejected(self, create_engine):
        with self.assertRaises(ValueError):
            get_engine("public;DROP SCHEMA gold")
        create_engine.assert_not_called()


if __name__ == "__main__":
    unittest.main()
