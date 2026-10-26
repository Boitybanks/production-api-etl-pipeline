"""Validate and transform CoinGecko simple-price API responses."""

from decimal import Decimal, InvalidOperation


def transform_crypto_data(raw_data):
    """Convert a simple-price response into validated database records.

    Raises:
        ValueError: When the response or any coin price is malformed.
    """
    if not isinstance(raw_data, dict) or not raw_data:
        raise ValueError("CoinGecko response must be a non-empty mapping")

    records = []
    for coin, values in raw_data.items():
        if not isinstance(coin, str) or not coin.strip():
            raise ValueError("Coin identifiers must be non-empty strings")
        if not isinstance(values, dict) or "usd" not in values:
            raise ValueError(f"Missing USD price for {coin}")

        raw_price = values["usd"]
        if isinstance(raw_price, bool) or not isinstance(raw_price, (int, float, str, Decimal)):
            raise ValueError(f"Invalid USD price for {coin}")
        try:
            price = Decimal(str(raw_price))
        except InvalidOperation as error:
            raise ValueError(f"Invalid USD price for {coin}") from error
        if not price.is_finite() or price < 0:
            raise ValueError(f"USD price must be finite and non-negative for {coin}")

        records.append({
            "coin": coin.strip(),
            "currency": "USD",
            "price": price,
        })
    return records
