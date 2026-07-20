"""
Extract module for the Production API ETL Pipeline.

This module is responsible for retrieving cryptocurrency market
data from the CoinGecko API.
"""

import logging

import requests

# -----------------------------
# Logging Configuration
# -----------------------------
logging.basicConfig(
    filename="logs/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

# -----------------------------
# API Configuration
# -----------------------------
BASE_URL = "https://api.coingecko.com/api/v3/simple/price"

PARAMS = {
    "ids": "bitcoin,ethereum,solana,xrp,dogecoin,cardano",
    "vs_currencies": "usd",
}


def get_crypto_prices():
    """
    Fetch cryptocurrency prices from the CoinGecko API.

    Returns:
        dict:
            Cryptocurrency price data.

        None:
            If extraction fails.
    """

    logger.info("Starting cryptocurrency extraction.")

    try:

        response = requests.get(
            BASE_URL,
            params=PARAMS,
            timeout=10,
        )

        logger.info("Request sent to CoinGecko API.")

        response.raise_for_status()

        logger.info(
            "Successfully retrieved cryptocurrency prices."
        )

        return response.json()

    except requests.exceptions.Timeout:

        logger.error("Request timed out.")

        return None

    except requests.exceptions.ConnectionError:

        logger.error("Unable to connect to the CoinGecko API.")

        return None

    except requests.exceptions.HTTPError as error:

        logger.error(f"HTTP Error: {error}")

        return None

    except requests.exceptions.RequestException as error:

        logger.error(f"Unexpected Request Error: {error}")

        return None


if __name__ == "__main__":

    logger.info("========== ETL Extraction Started ==========")

    crypto_data = get_crypto_prices()

    if crypto_data:

        logger.info("Extraction completed successfully.")

        print(crypto_data)

    else:

        logger.warning("No data returned from extraction.")

    logger.info("========== ETL Extraction Finished ==========")