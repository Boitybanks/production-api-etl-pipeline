
"""PostgreSQL loading layer for the cryptocurrency ETL pipeline."""

import logging
import os
from decimal import Decimal, InvalidOperation

import psycopg2
from psycopg2.extras import execute_batch

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
        RuntimeError: If database credentials are missing.
        psycopg2.Error: If a database operation fails.
    """
    password = os.getenv("DB_PASSWORD")

    if not password:
        raise RuntimeError(
            "DB_PASSWORD is not configured. "
            "Set it before running the ETL pipeline."
        )

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

    # Keep credentials out of code and version control.
    db_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "dbname": os.getenv("DB_NAME", "crypto_etl"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": password,
        "port": os.getenv("DB_PORT", "5432"),
        "connect_timeout": 10,
    }

    connection = None

    try:
        connection = psycopg2.connect(**db_config)

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

    except psycopg2.Error:
        logger.exception("PostgreSQL load operation failed.")
        raise

    finally:
        if connection is not None:
            connection.close()
            logger.debug("Database connection closed.")
