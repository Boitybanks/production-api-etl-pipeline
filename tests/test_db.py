"""Offline tests for database configuration."""

import os
import sys
import traceback
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from db import connect, get_db_config


class DbConfigTests(unittest.TestCase):
    def test_missing_credentials_are_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "DATABASE_URL or DB_PASSWORD"):
                get_db_config()

    def test_empty_secrets_are_rejected(self):
        with patch.dict(os.environ, {"DATABASE_URL": "", "DB_PASSWORD": ""}, clear=True):
            with self.assertRaises(RuntimeError):
                get_db_config()

    def test_empty_optional_secrets_use_defaults(self):
        env = {
            "DB_HOST": "db.example.com",
            "DB_PASSWORD": "secret",
            "DB_PORT": "",
            "DB_NAME": "",
            "DB_USER": "",
        }
        with patch.dict(os.environ, env, clear=True):
            config = get_db_config()
        self.assertEqual(config["host"], "db.example.com")
        self.assertEqual(config["port"], "5432")
        self.assertEqual(config["dbname"], "crypto_etl")
        self.assertEqual(config["user"], "postgres")

    def test_database_url_takes_priority(self):
        env = {"DATABASE_URL": "postgresql://u:p@h/d", "DB_PASSWORD": "other"}
        with patch.dict(os.environ, env, clear=True):
            config = get_db_config()
        self.assertEqual(config["dsn"], "postgresql://u:p@h/d")
        self.assertNotIn("password", config)

    def test_malformed_database_url_does_not_expose_password(self):
        urls = (
            "postgresq://u:FAKESECRET@db.invalid/x",
            "postgresql://u:FAKE%ZZSECRET@db.invalid/x",
            "postgresql://u:FAKE/SECRET@db.invalid:5432/x",
            "postgresql://u:FAKE@SECRET@db.invalid/x",
        )
        for url in urls:
            with self.subTest(url=url):
                with patch.dict(os.environ, {"DATABASE_URL": url}, clear=True):
                    with self.assertRaises(RuntimeError) as caught:
                        connect()
                printed = "".join(traceback.format_exception(caught.exception))
                self.assertNotIn("SECRET", printed)
                self.assertNotIn("FAKE", printed)


if __name__ == "__main__":
    unittest.main()
