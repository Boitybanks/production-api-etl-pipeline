"""Offline tests for CoinGecko extraction."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import extract


def fake_response(payload):
    response = Mock()
    response.json.return_value = payload
    return response


class ExtractTests(unittest.TestCase):
    def test_requested_ids_are_valid_coingecko_ids(self):
        self.assertIn("ripple", extract.COIN_IDS)
        self.assertNotIn("xrp", extract.COIN_IDS)

    def test_missing_coin_is_logged_and_rest_returned(self):
        payload = {coin: {"usd": 1} for coin in extract.COIN_IDS if coin != "ripple"}
        with patch.object(requests.Session, "get", return_value=fake_response(payload)):
            with self.assertLogs("extract", level="WARNING") as logs:
                result = extract.get_crypto_prices()
        self.assertEqual(result, payload)
        self.assertIn("ripple", logs.output[0])

    def test_http_error_returns_none_and_logs_reason(self):
        response = Mock()
        response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Too Many Requests")
        with patch.object(requests.Session, "get", return_value=response):
            with self.assertLogs("extract", level="ERROR") as logs:
                self.assertIsNone(extract.get_crypto_prices())
        self.assertIn("429", logs.output[0])

    def test_api_key_is_sent_when_configured(self):
        payload = {coin: {"usd": 1} for coin in extract.COIN_IDS}
        with patch.dict(os.environ, {"COINGECKO_API_KEY": "demo-key"}):
            with patch.object(requests.Session, "get", return_value=fake_response(payload)) as get:
                extract.get_crypto_prices()
        self.assertEqual(get.call_args.kwargs["headers"]["x-cg-demo-api-key"], "demo-key")


if __name__ == "__main__":
    unittest.main()
