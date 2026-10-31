"""PostgreSQL connection settings shared by the ETL stages."""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

CONNECT_TIMEOUT_SECONDS = 10


def get_db_config():
    """Build psycopg2 connection arguments from the environment.

    DATABASE_URL takes priority over the individual DB_* variables.

    Returns:
        dict: Keyword arguments for psycopg2.connect.

    Raises:
        RuntimeError: If database credentials are missing.
    """
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return {
            "dsn": database_url,
            "connect_timeout": CONNECT_TIMEOUT_SECONDS,
        }

    password = os.getenv("DB_PASSWORD")

    if not password:
        raise RuntimeError(
            "Database is not configured. "
            "Set DATABASE_URL or DB_PASSWORD before running the ETL pipeline."
        )

    # GitHub Actions expands an unset secret to an empty string, which
    # os.getenv's default would not replace, so fall back with "or".
    return {
        "host": os.getenv("DB_HOST") or "localhost",
        "dbname": os.getenv("DB_NAME") or "crypto_etl",
        "user": os.getenv("DB_USER") or "postgres",
        "password": password,
        "port": os.getenv("DB_PORT") or "5432",
        "connect_timeout": CONNECT_TIMEOUT_SECONDS,
    }


def connect():
    """Open a PostgreSQL connection using the environment configuration.

    Raises:
        RuntimeError: If credentials are missing or DATABASE_URL cannot connect.
        psycopg2.Error: If a connection built from DB_* variables fails.
    """
    config = get_db_config()

    if "dsn" not in config:
        return psycopg2.connect(**config)

    # libpq can repeat parts of a malformed URL, including the password, in
    # its error text, and this repository's Actions logs are public.
    try:
        return psycopg2.connect(**config)
    except psycopg2.Error as error:
        raise RuntimeError(
            f"Could not connect using DATABASE_URL ({type(error).__name__}). "
            "Check the URL format, percent-encode special characters in the "
            "password, and confirm the host and credentials."
        ) from None
