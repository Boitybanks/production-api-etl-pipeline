
"""PostgreSQL loading layer for the cryptocurrency ETL pipeline."""

import logging
from decimal import Decimal, InvalidOperation

import psycopg2
from psycopg2.extras import execute_batch

from db import connect, get_db_config

logger = logging.getLogger(__name__)

INSERT_QUERY = """
    INSERT INTO crypto_prices (coin, currency, price)
    VALUES (%s, %s, %s)
"""


def load_crypto_data(records):
    """Validate and insert cryptocurrency prices in one transaction.

    Args:
        records: Transformed cryptocurrency records containing
            coin, currency, and price.

    Returns:
        int: Number of records successfully inserted.

    Raises:
        ValueError: If a record contains invalid data.
        RuntimeError: If credentials are missing or DATABASE_URL cannot connect.
        psycopg2.Error: If a database operation fails.
    """
    # Fail on missing credentials before doing any other work.
    get_db_config()

    # Validate everything before opening a database connection.
    validated_records = []

    for index, record in enumerate(records):
        try:
            coin = str(record["coin"]).strip()
            currency = str(record["currency"]).strip().upper()
            price = Decimal(str(record["price"]))

            if not coin or not currency:
                raise ValueError("Coin and currency cannot be empty")

            if not price.is_finite() or price < 0:
                raise ValueError("Price must be finite and non-negative")

        except (KeyError, TypeError, InvalidOperation, ValueError) as error:
            raise ValueError(
                f"Invalid cryptocurrency record at index {index}"
            ) from error

        validated_records.append((coin, currency, price))

    if not validated_records:
        logger.info("No records to load.")
        return 0

    connection = None

    try:
        connection = connect()

        # Connection context commits on success and rolls back
        # automatically when an exception is raised.
        with connection:
            with connection.cursor() as cursor:
                execute_batch(
                    cursor,
                    INSERT_QUERY,
                    validated_records,
                    page_size=100,
                )

        logger.info(
            "Successfully loaded %d cryptocurrency records.",
            len(validated_records),
        )

        return len(validated_records)

    except (psycopg2.Error, RuntimeError):
        logger.exception("PostgreSQL load operation failed.")
        raise

    finally:
        if connection is not None:
            connection.close()
            logger.debug("Database connection closed.")
