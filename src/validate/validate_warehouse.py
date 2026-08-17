import logging

import duckdb


logger = logging.getLogger(__name__)


MIN_PRICE = 450
MAX_PRICE = 1000

MIN_RAM_GB = 16
MIN_STORAGE_GB = 512

MIN_PRODUCTS_EXPECTED = 3


def validate_warehouse(db_path):
    """
    Validate data quality and referential integrity
    in the DuckDB warehouse.
    """

    connection = duckdb.connect(db_path)

    # --------------------------------------------------
    # 1. Products count
    # --------------------------------------------------
    products_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM products
        """
    ).fetchone()[0]

    if products_count == 0:
        connection.close()
        raise ValueError(
            "No products found in the warehouse: table is empty."
        )

    if products_count < MIN_PRODUCTS_EXPECTED:
        logger.warning(
            "Only %s products found in warehouse. "
            "Expected at least %s.",
            products_count,
            MIN_PRODUCTS_EXPECTED,
        )

    # --------------------------------------------------
    # 2. NULL product IDs
    # --------------------------------------------------
    null_product_ids = connection.execute(
        """
        SELECT COUNT(*)
        FROM products
        WHERE product_id IS NULL
        """
    ).fetchone()[0]

    if null_product_ids > 0:
        connection.close()
        raise ValueError(
            f"Validation failed: "
            f"{null_product_ids} products with NULL product_id found."
        )

    # --------------------------------------------------
    # 3. Duplicate product IDs
    # --------------------------------------------------
    duplicate_products_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT
                product_id
            FROM products
            GROUP BY product_id
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    if duplicate_products_count > 0:
        connection.close()
        raise ValueError(
            f"Validation failed: "
            f"{duplicate_products_count} duplicate product IDs found."
        )

    # --------------------------------------------------
    # 4. Invalid prices
    # --------------------------------------------------
    invalid_prices = connection.execute(
        """
        SELECT COUNT(*)
        FROM price_history
        WHERE price IS NULL
           OR price < ?
           OR price > ?
        """,
        [MIN_PRICE, MAX_PRICE],
    ).fetchone()[0]

    if invalid_prices > 0:
        connection.close()
        raise ValueError(
            f"Validation failed: "
            f"{invalid_prices} price history rows outside the accepted "
            f"range €{MIN_PRICE} - €{MAX_PRICE}."
        )

    # --------------------------------------------------
    # 5. Invalid hardware specifications
    # --------------------------------------------------
    invalid_specs = connection.execute(
        """
        SELECT COUNT(*)
        FROM products
        WHERE ram_gb IS NULL
           OR storage_gb IS NULL
           OR ram_gb < ?
           OR storage_gb < ?
        """,
        [MIN_RAM_GB, MIN_STORAGE_GB],
    ).fetchone()[0]

    if invalid_specs > 0:
        connection.close()
        raise ValueError(
            f"Validation failed: "
            f"{invalid_specs} products with invalid hardware "
            f"specifications found."
        )

    # --------------------------------------------------
    # 6. Orphan price history rows
    # --------------------------------------------------
    orphan_history_rows = connection.execute(
        """
        SELECT COUNT(*)
        FROM price_history ph
        LEFT JOIN products p
            ON ph.product_id = p.product_id
        WHERE p.product_id IS NULL
        """
    ).fetchone()[0]

    if orphan_history_rows > 0:
        connection.close()
        raise ValueError(
            f"Validation failed: "
            f"{orphan_history_rows} orphan price history rows found."
        )

    # --------------------------------------------------
    # 7. Programming score range
    # --------------------------------------------------
    invalid_programming_scores = connection.execute(
        """
        SELECT COUNT(*)
        FROM products
        WHERE programming_score IS NOT NULL
          AND (
                programming_score < 0
                OR programming_score > 100
              )
        """
    ).fetchone()[0]

    if invalid_programming_scores > 0:
        connection.close()
        raise ValueError(
            f"Validation failed: "
            f"{invalid_programming_scores} invalid programming scores."
        )

    # --------------------------------------------------
    # 8. Deal score range
    # --------------------------------------------------
    invalid_deal_scores = connection.execute(
        """
        SELECT COUNT(*)
        FROM deal_scores
        WHERE deal_score IS NULL
           OR deal_score < 0
           OR deal_score > 100
        """
    ).fetchone()[0]

    if invalid_deal_scores > 0:
        connection.close()
        raise ValueError(
            f"Validation failed: "
            f"{invalid_deal_scores} invalid deal scores."
        )

    # --------------------------------------------------
    # 9. Orphan deal score rows
    # --------------------------------------------------
    orphan_deal_scores = connection.execute(
        """
        SELECT COUNT(*)
        FROM deal_scores ds
        LEFT JOIN products p
            ON ds.product_id = p.product_id
        WHERE p.product_id IS NULL
        """
    ).fetchone()[0]

    if orphan_deal_scores > 0:
        connection.close()
        raise ValueError(
            f"Validation failed: "
            f"{orphan_deal_scores} orphan deal score rows found."
        )

    # --------------------------------------------------
    # 10. Quality warnings - not hard failures
    # --------------------------------------------------
    unknown_cpu_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM products
        WHERE cpu IS NULL
           OR cpu = 'Unknown'
        """
    ).fetchone()[0]

    unknown_brand_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM products
        WHERE brand IS NULL
           OR brand = 'Unknown'
        """
    ).fetchone()[0]

    unknown_gpu_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM products
        WHERE gpu IS NULL
           OR gpu = 'Unknown'
        """
    ).fetchone()[0]

    # --------------------------------------------------
    # 11. Price history row count
    # --------------------------------------------------
    history_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM price_history
        """
    ).fetchone()[0]

    connection.close()

    # --------------------------------------------------
    # Validation summary
    # --------------------------------------------------
    logger.info("WAREHOUSE VALIDATION PASSED")
    logger.info("Products: %s", products_count)
    logger.info(
        "Price history observations: %s",
        history_count,
    )
    logger.info(
        "Accepted price range: €%s - €%s",
        MIN_PRICE,
        MAX_PRICE,
    )
    logger.info(
        "Minimum hardware: %s GB RAM / %s GB storage",
        MIN_RAM_GB,
        MIN_STORAGE_GB,
    )

    # --------------------------------------------------
    # Data quality warnings
    # --------------------------------------------------
    if unknown_cpu_count > 0:
        logger.warning(
            "Products with Unknown CPU: %s",
            unknown_cpu_count,
        )
    else:
        logger.info("Products with Unknown CPU: 0")

    if unknown_brand_count > 0:
        logger.warning(
            "Products with Unknown brand: %s",
            unknown_brand_count,
        )
    else:
        logger.info("Products with Unknown brand: 0")

    # GPU is optional, so this is informational.
    logger.info(
        "Products with Unknown GPU: %s (optional field)",
        unknown_gpu_count,
    )

    return True