"""Offline loader boundary checks; transaction behaviour is tested with PostgreSQL."""

import os
import sys
import traceback
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import load


class LoadValidationTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"DB_PASSWORD": "test-only"}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_invalid_record_rejects_whole_batch_before_connecting(self):
        valid = {"coin": "bitcoin", "currency": "usd", "price": "1.25"}
        invalid = [None, {}, {**valid, "coin": None}, {**valid, "currency": 123},
                   {**valid, "coin": " "}, {**valid, "price": True},
                   {**valid, "price": "NaN"}, {**valid, "price": -1}]
        for record in invalid:
            with self.subTest(record=record), patch.object(load, "connect") as connect:
                with self.assertRaisesRegex(ValueError, "index 1"):
                    load.load_crypto_data([valid, record])
                connect.assert_not_called()

    def test_empty_batch_does_not_connect(self):
        with patch.object(load, "connect") as connect:
            self.assertEqual(load.load_crypto_data([]), 0)
            connect.assert_not_called()

    def test_connection_error_does_not_expose_diagnostics(self):
        records = [{"coin": "bitcoin", "currency": "USD", "price": 1}]
        with patch.object(load, "connect", side_effect=load.psycopg2.OperationalError("FAKE_SECRET")):
            with self.assertLogs("load", level="ERROR") as logs:
                with self.assertRaisesRegex(RuntimeError, "OperationalError") as caught:
                    load.load_crypto_data(records)
        self.assertNotIn("FAKE_SECRET", "\n".join(logs.output))
        self.assertNotIn("FAKE_SECRET", "".join(traceback.format_exception(caught.exception)))


if __name__ == "__main__":
    unittest.main()
