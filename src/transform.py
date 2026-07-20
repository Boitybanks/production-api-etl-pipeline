"""
Transform module for the Production API ETL Pipeline.

This module converts raw API JSON into a clean,
database-ready structure.
"""


def transform_crypto_data(raw_data):
    """
    Transform raw cryptocurrency JSON into a list of records.

    Args:
        raw_data (dict):
            Raw JSON returned from CoinGecko.

    Returns:
        list:
            Clean records ready for loading.
    """

    transformed_data = []

    for coin, values in raw_data.items():

        record = {
            "coin": coin,
            "currency": "USD",
            "price": values["usd"],
        }

        transformed_data.append(record)

    return transformed_data