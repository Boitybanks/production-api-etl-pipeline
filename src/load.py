import logging
import psycopg2


logger = logging.getLogger(__name__)


def load_crypto_data(records):
    """
    Load transformed cryptocurrency records into PostgreSQL.
    """

    try:
        connection = psycopg2.connect(
            host="localhost",
            database="crypto_etl",
            user="postgres",
            password="Boity1239!",
            port=5432,
        )

        cursor = connection.cursor()

        insert_query = """
        INSERT INTO crypto_prices
        (coin, currency, price)
        VALUES (%s, %s, %s)
        """

        for record in records:
            cursor.execute(
                insert_query,
                (
                    record["coin"],
                    record["currency"],
                    record["price"],
                ),
            )

        connection.commit()

        logger.info("%s records inserted.", len(records))

    except Exception as error:
        logger.error(error)

    finally:
        if "cursor" in locals():
            cursor.close()

        if "connection" in locals():
            connection.close()

        logger.info("Database connection closed.")