"""Create the crypto_prices table if it does not exist yet.

Run: python src/init_db.py
"""

from pathlib import Path

from db import connect

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


def init_db():
    """Apply the idempotent schema in one transaction."""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    connection = connect(direct=True)

    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(schema)
    finally:
        connection.close()


if __name__ == "__main__":
    init_db()
    print("Database schema is ready.")
