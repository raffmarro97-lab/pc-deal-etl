import json
import logging
from datetime import datetime
from pathlib import Path

import duckdb


logger = logging.getLogger(__name__)


DB_PATH = Path("/opt/airflow/data/warehouse/pc_deals.db")


def load_products(input_file):
    """
    Load transformed and scored product data
    from a JSON file into DuckDB.
    """

    input_path = Path(input_file)

    with open(input_path, "r", encoding="utf-8") as file:
        products = json.load(file)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(DB_PATH))

    # -----------------------------
    # 1. Product master table
    # -----------------------------
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS products(
            product_id VARCHAR PRIMARY KEY,
            title VARCHAR,
            brand VARCHAR,
            cpu VARCHAR,
            gpu VARCHAR,
            ram_gb INTEGER,
            storage_gb INTEGER,
            programming_score INTEGER,
            programming_class VARCHAR,
            cpu_score INTEGER,
            ram_score INTEGER,
            storage_score INTEGER,
            gpu_score INTEGER,
            url VARCHAR
        )
        """
    )

    # -----------------------------
    # 2. Price history table
    # -----------------------------
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS price_history(
            product_id VARCHAR,
            price DOUBLE,
            currency VARCHAR,
            rating DOUBLE,
            reviews INTEGER,
            observed_at TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
        """
    )

    observed_at = datetime.now()

    # -----------------------------
    # 3. Upsert products
    #    + append price observations
    # -----------------------------
    for product in products:
        connection.execute(
            """
            INSERT INTO products(
                product_id,
                title,
                brand,
                cpu,
                gpu,
                ram_gb,
                storage_gb,
                programming_score,
                programming_class,
                cpu_score,
                ram_score,
                storage_score,
                gpu_score,
                url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT (product_id)
            DO UPDATE SET
                title = EXCLUDED.title,
                brand = EXCLUDED.brand,
                cpu = EXCLUDED.cpu,
                gpu = EXCLUDED.gpu,
                ram_gb = EXCLUDED.ram_gb,
                storage_gb = EXCLUDED.storage_gb,
                programming_score = EXCLUDED.programming_score,
                programming_class = EXCLUDED.programming_class,
                cpu_score = EXCLUDED.cpu_score,
                ram_score = EXCLUDED.ram_score,
                storage_score = EXCLUDED.storage_score,
                gpu_score = EXCLUDED.gpu_score,
                url = EXCLUDED.url
            """,
            [
                product.get("product_id"),
                product.get("title"),
                product.get("brand"),
                product.get("cpu"),
                product.get("gpu"),
                product.get("ram_gb"),
                product.get("storage_gb"),
                product.get("programming_score"),
                product.get("programming_class"),
                product.get("cpu_score"),
                product.get("ram_score"),
                product.get("storage_score"),
                product.get("gpu_score"),
                product.get("url"),
            ],
        )

        connection.execute(
            """
            INSERT INTO price_history(
                product_id,
                price,
                currency,
                rating,
                reviews,
                observed_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                product.get("product_id"),
                product.get("price"),
                product.get("currency"),
                product.get("rating"),
                product.get("reviews"),
                observed_at,
            ],
        )

    # -----------------------------
    # 4. Warehouse metrics
    # -----------------------------
    products_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM products
        """
    ).fetchone()[0]

    price_history_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM price_history
        """
    ).fetchone()[0]

    connection.close()

    # -----------------------------
    # 5. Logging
    # -----------------------------
    logger.info("LOAD SUMMARY")
    logger.info(
        "Loaded %s products into DuckDB",
        len(products),
    )
    logger.info(
        "Database path: %s",
        DB_PATH,
    )
    logger.info(
        "Total rows in products: %s",
        products_count,
    )
    logger.info(
        "Total rows in price_history: %s",
        price_history_count,
    )

    return str(DB_PATH)