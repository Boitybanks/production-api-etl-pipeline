"""Real PostgreSQL tests, isolated in a unique schema per test.

Set TEST_DATABASE_URL explicitly to a disposable database. Never fall back to
DATABASE_URL: a developer's normal connection may point at production.
"""

import os
import sys
import unittest
import uuid
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import load


@unittest.skipUnless(os.getenv("TEST_DATABASE_URL"), "Set TEST_DATABASE_URL for PostgreSQL tests")
class LoadIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.dsn = os.environ["TEST_DATABASE_URL"]
        self.schema = "etl_test_" + uuid.uuid4().hex
        self.admin = psycopg2.connect(self.dsn)
        self.admin.autocommit = True
        self.addCleanup(self.admin.close)
        with self.admin.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.schema)))
        self.addCleanup(self.drop_schema)
        with self.admin.cursor() as cursor:
            cursor.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(self.schema)))
            cursor.execute((ROOT / "sql/schema.sql").read_text())
        self.connections = []

    def drop_schema(self):
        with self.admin.cursor() as cursor:
            cursor.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(self.schema)))

    def open_connection(self):
        connection = psycopg2.connect(self.dsn)
        # Scope all loader writes to this test's schema without changing the loader.
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(self.schema)))
        self.connections.append(connection)
        self.addCleanup(connection.close)
        return connection

    def run_load(self, records):
        with patch.object(load, "get_db_config", return_value={}), \
             patch.object(load, "connect", side_effect=self.open_connection):
            return load.load_crypto_data(records)

    def rows(self):
        # A separate connection proves writes were committed, not just visible locally.
        with self.admin.cursor() as cursor:
            cursor.execute("SELECT coin, currency, price FROM crypto_prices ORDER BY id")
            return cursor.fetchall()

    def test_commits_exact_decimal_values_and_closes_connection(self):
        records = [{"coin": " bitcoin ", "currency": "usd", "price": "0.1234567890123456789"},
                   {"coin": "ethereum", "currency": "USD", "price": 0}]
        self.assertEqual(self.run_load(records), 2)
        self.assertEqual(self.rows(), [("bitcoin", "USD", Decimal("0.1234567890123456789")),
                                       ("ethereum", "USD", Decimal(0))])
        self.assertTrue(self.connections[-1].closed)

    def test_failure_on_second_page_rolls_back_and_retry_has_no_partial_duplicates(self):
        # execute_batch sends 100 rows per page. Force page two to fail at the DB,
        # after page one succeeded, to exercise the actual transaction boundary.
        records = [{"coin": f"coin-{i}", "currency": "USD", "price": i} for i in range(101)]
        self.run_load([{"coin": "existing", "currency": "USD", "price": 42}])
        with self.admin.cursor() as cursor:
            cursor.execute("ALTER TABLE crypto_prices ADD CONSTRAINT reject_last CHECK (coin <> 'coin-100')")
        with self.assertLogs("load", level="ERROR") as logs:
            with self.assertRaisesRegex(RuntimeError, "CheckViolation"):
                self.run_load(records)
        self.assertNotIn("coin-100", "\n".join(logs.output))
        self.assertTrue(self.connections[-1].closed)
        self.assertEqual(self.rows(), [("existing", "USD", Decimal(42))])
        with self.admin.cursor() as cursor:
            cursor.execute("ALTER TABLE crypto_prices DROP CONSTRAINT reject_last")
        self.assertEqual(self.run_load(records), 101)
        rows = self.rows()
        self.assertEqual(len(rows), 102)
        self.assertEqual(len({row[0] for row in rows}), 102)

    def test_sql_like_identifier_is_stored_as_data(self):
        coin = "x'); DROP TABLE crypto_prices; --"
        self.assertEqual(self.run_load([{"coin": coin, "currency": "USD", "price": 5}]), 1)
        self.assertEqual(self.rows(), [(coin, "USD", Decimal(5))])

    def test_successful_reruns_are_separate_snapshots(self):
        # Unchanged prices at different collection times are legitimate history.
        # This API does not promise idempotency after an uncertain commit result.
        records = [{"coin": "bitcoin", "currency": "USD", "price": 10}]
        self.run_load(records)
        self.run_load(records)
        self.assertEqual(len(self.rows()), 2)


if __name__ == "__main__":
    unittest.main()
