"""
Extract module for the Production API ETL Pipeline.

This module is responsible for retrieving cryptocurrency market
data from the CoinGecko API.
"""

import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

# -----------------------------
# Logging Configuration
# -----------------------------
# Resolve from this file so the pipeline runs from any working directory.
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def configure_logging():
    """Log to the file and console; CI runners discard the file after each job."""
    LOG_DIR.mkdir(exist_ok=True)

    logging.basicConfig(
        handlers=[
            logging.FileHandler(LOG_DIR / "pipeline.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


logger = logging.getLogger(__name__)

# -----------------------------
# API Configuration
# -----------------------------
BASE_URL = "https://api.coingecko.com/api/v3/simple/price"

COIN_IDS = ("bitcoin", "ethereum", "solana", "ripple", "dogecoin", "cardano")

PARAMS = {
    "ids": ",".join(COIN_IDS),
    "vs_currencies": "usd",
}

# Shared CI runner IPs are often rate limited, so back off and retry.
RETRY_POLICY = Retry(
    total=3,
    backoff_factor=5,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=("GET",),
    raise_on_status=False,
    retry_after_max=60,
)


def build_session():
    """Create an HTTP session that retries transient failures."""
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=RETRY_POLICY))

    return session


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

    api_key = os.getenv("COINGECKO_API_KEY")
    headers = {"x-cg-demo-api-key": api_key} if api_key else {}

    try:

        response = build_session().get(
            BASE_URL,
            params=PARAMS,
            headers=headers,
            timeout=10,
        )

        logger.info("Request sent to CoinGecko API.")

        response.raise_for_status()

        logger.info(
            "Successfully retrieved cryptocurrency prices."
        )

        data = response.json()

        # CoinGecko omits unknown IDs instead of returning an error.
        if isinstance(data, dict):
            missing = [coin for coin in COIN_IDS if coin not in data]

            if missing:
                logger.warning(
                    "CoinGecko returned no price for: %s",
                    ", ".join(missing),
                )

        return data

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

    configure_logging()

    logger.info("========== ETL Extraction Started ==========")

    crypto_data = get_crypto_prices()

    if crypto_data:

        logger.info("Extraction completed successfully.")

        print(crypto_data)

    else:

        logger.warning("No data returned from extraction.")

    logger.info("========== ETL Extraction Finished ==========")