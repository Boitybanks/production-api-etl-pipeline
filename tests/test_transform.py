"""Offline regression tests for CoinGecko transformation."""

import unittest
from decimal import Decimal

from src.transform import transform_crypto_data


class TransformTests(unittest.TestCase):
    def test_valid_prices_become_decimal_records(self):
        result = transform_crypto_data({
            "bitcoin": {"usd": 65046.25},
            "ethereum": {"usd": 0},
        })
        self.assertEqual(result, [
            {"coin": "bitcoin", "currency": "USD", "price": Decimal("65046.25")},
            {"coin": "ethereum", "currency": "USD", "price": Decimal("0")},
        ])

    def test_empty_payload_is_rejected(self):
        with self.assertRaises(ValueError):
            transform_crypto_data({})

    def test_missing_usd_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing USD price"):
            transform_crypto_data({"bitcoin": {"eur": 42}})

    def test_invalid_prices_are_rejected(self):
        for price in (-1, "NaN", "Infinity", None, True, "not-a-number"):
            with self.subTest(price=price):
                with self.assertRaises(ValueError):
                    transform_crypto_data({"bitcoin": {"usd": price}})

    def test_invalid_coin_identifier_is_rejected(self):
        with self.assertRaises(ValueError):
            transform_crypto_data({"": {"usd": 1}})


if __name__ == "__main__":
    unittest.main()
