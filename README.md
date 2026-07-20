# Production API ETL Pipeline

A production-style ETL (Extract, Transform, Load) pipeline built with Python and PostgreSQL.

This project extracts live cryptocurrency prices from the CoinGecko API, transforms the raw API response into a clean structured format, and loads historical price snapshots into a PostgreSQL database.

---

## Project Architecture

```
                CoinGecko API
                       │
                Extract (Python)
                       │
                       ▼
              Raw JSON Response
                       │
                Transform (Python)
                       │
                       ▼
             Clean Python Records
                       │
                  Load (psycopg2)
                       │
                       ▼
                 PostgreSQL Database
                       │
                       ▼
                SQL Analytics
```

---

## Features

- Extract live cryptocurrency prices
- Transform raw JSON into clean records
- Load records into PostgreSQL
- Preserve historical snapshots
- Query data using SQL
- Modular ETL architecture
- Logging support
- Git version controlled

---

## Tech Stack

- Python 3.13
- PostgreSQL 18
- psycopg2
- requests
- pgAdmin 4
- SQL
- Git
- VS Code

---

## Project Structure

```
production-api-etl-pipeline/

│
├── config/
├── docs/
├── logs/
│   └── pipeline.log
│
├── src/
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   ├── pipeline.py
│   └── __init__.py
│
├── tests/
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ETL Workflow

### 1. Extract

Retrieve live cryptocurrency prices from the CoinGecko API.

Example response:

```json
{
  "bitcoin": {
    "usd": 65046
  }
}
```

---

### 2. Transform

Convert the nested JSON into clean Python dictionaries.

Example:

```python
{
    "coin": "bitcoin",
    "currency": "USD",
    "price": 65046
}
```

---

### 3. Load

Insert transformed records into PostgreSQL using parameterized SQL queries.

Example:

```python
cursor.execute(
    """
    INSERT INTO crypto_prices
    (coin, currency, price)
    VALUES (%s, %s, %s)
    """,
    (
        record["coin"],
        record["currency"],
        record["price"]
    )
)
```

---

## PostgreSQL Table

```sql
CREATE TABLE crypto_prices (

    id SERIAL PRIMARY KEY,

    coin VARCHAR(50),

    currency VARCHAR(10),

    price NUMERIC,

    created_at TIMESTAMP
    DEFAULT CURRENT_TIMESTAMP

);
```

---

## Running the Pipeline

Create a virtual environment

```bash
python -m venv .venv
```

Activate

Windows

```bash
.venv\Scripts\activate
```

Install packages

```bash
pip install -r requirements.txt
```

Run

```bash
python src/pipeline.py
```

---

## Example SQL Queries

View all records

```sql
SELECT *
FROM crypto_prices;
```

Find Bitcoin prices

```sql
SELECT *
FROM crypto_prices
WHERE coin='bitcoin';
```

Only coin and price

```sql
SELECT coin, price
FROM crypto_prices;
```

Count rows

```sql
SELECT COUNT(*)
FROM crypto_prices;
```

Highest prices

```sql
SELECT *
FROM crypto_prices
ORDER BY price DESC;
```

---

## Sample Output

| id | coin | currency | price | created_at |
|----|------|----------|-------|----------------------------|
| 1 | bitcoin | USD | 64320 | 2026-07-20 16:50 |
| 2 | cardano | USD | 0.162568 | 2026-07-20 16:50 |
| 3 | dogecoin | USD | 0.072317 | 2026-07-20 16:50 |

Each pipeline execution stores a new historical snapshot instead of overwriting previous records.

---

## Skills Demonstrated

- ETL Development
- Python Programming
- PostgreSQL
- SQL
- API Integration
- Data Transformation
- Database Design
- Logging
- Git
- Version Control

---

## Future Improvements

- Dockerize the application
- Environment variables (.env)
- Scheduler (cron / Windows Task Scheduler)
- Apache Airflow orchestration
- Unit tests
- Data validation
- CI/CD with GitHub Actions
- Cloud deployment (AWS)

---

## Author

**Boitumelo Banks**

Junior Software Engineer | Aspiring Data Engineer

GitHub:
https://github.com/Boitybanks