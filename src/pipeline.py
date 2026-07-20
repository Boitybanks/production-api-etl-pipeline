"""
Main ETL Pipeline

Coordinates the Extract, Transform,
and (later) Load stages.
"""

from extract import get_crypto_prices
from transform import transform_crypto_data


def run_pipeline():
    """
    Run the ETL pipeline.
    """

    print("Starting ETL Pipeline...\n")

    # Extract
    raw_data = get_crypto_prices()

    if raw_data is None:
        print("Extraction failed.")
        return

    print("Extraction successful.\n")

    # Transform
    clean_data = transform_crypto_data(raw_data)

    print("Transformation successful.\n")

    print("Clean Records:\n")

    for record in clean_data:
        print(record)


if __name__ == "__main__":
    run_pipeline()