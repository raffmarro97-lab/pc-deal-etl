import logging

import duckdb


logger = logging.getLogger(__name__)


def calculate_rating_score(rating, reviews):
    """
    Returns a score from 0 to 5.

    Rating gives the base score.
    Number of reviews determines confidence.
    """

    if rating is None or rating <= 0:
        return 0

    rating_component = min(rating / 5, 1.0)

    if reviews is None or reviews <= 0:
        confidence = 0.3
    elif reviews < 10:
        confidence = 0.5
    elif reviews < 50:
        confidence = 0.7
    elif reviews < 200:
        confidence = 0.85
    else:
        confidence = 1.0

    return round(
        rating_component * confidence * 5,
        2,
    )


def calculate_history_score(
    current_price,
    avg_price,
    observations,
):
    """
    Returns a score from 0 to 15.

    With insufficient history, give a neutral score.
    """

    if observations is None or observations < 2:
        return 7.5

    if avg_price is None or avg_price <= 0:
        return 7.5

    discount_pct = (
        (avg_price - current_price)
        / avg_price
    ) * 100

    if discount_pct <= 0:
        return max(
            0,
            round(
                7.5 + discount_pct * 0.5,
                2,
            ),
        )

    return min(
        15,
        round(
            7.5 + discount_pct * 0.5,
            2,
        ),
    )


def calculate_deal_scores(db_path):
    connection = duckdb.connect(db_path)

    rows = connection.execute(
        """
        WITH latest_prices AS (
            SELECT
                product_id,
                price AS current_price,
                rating,
                reviews,
                observed_at,
                ROW_NUMBER() OVER (
                    PARTITION BY product_id
                    ORDER BY observed_at DESC
                ) AS rn
            FROM price_history
        ),

        history AS (
            SELECT
                product_id,
                COUNT(*) AS observations,
                AVG(price) AS avg_price,
                MIN(price) AS min_price,
                MAX(price) AS max_price
            FROM price_history
            GROUP BY product_id
        )

        SELECT
            p.product_id,
            p.programming_score,
            lp.current_price,
            lp.rating,
            lp.reviews,
            lp.observed_at,
            h.observations,
            h.avg_price,
            h.min_price,
            h.max_price

        FROM products p

        JOIN latest_prices lp
            ON p.product_id = lp.product_id
           AND lp.rn = 1

        JOIN history h
            ON p.product_id = h.product_id

        WHERE p.programming_score IS NOT NULL
        """
    ).fetchall()

    if not rows:
        connection.close()
        raise ValueError(
            "No scored products found for deal calculation."
        )

    ratios = []

    for row in rows:
        programming_score = row[1]
        current_price = row[2]

        if (
            programming_score is not None
            and current_price is not None
            and current_price > 0
        ):
            ratios.append(
                programming_score / current_price
            )

    if not ratios:
        connection.close()
        raise ValueError(
            "No valid price/performance ratios found."
        )

    min_ratio = min(ratios)
    max_ratio = max(ratios)

    results = []

    for row in rows:
        (
            product_id,
            programming_score,
            current_price,
            rating,
            reviews,
            observed_at,
            observations,
            avg_price,
            min_price,
            max_price,
        ) = row

        # ----------------------------------------------
        # 1. Technical score: maximum 60
        # ----------------------------------------------
        technical_score = round(
            programming_score * 0.60,
            2,
        )

        # ----------------------------------------------
        # 2. Price / performance: maximum 20
        # ----------------------------------------------
        ratio = programming_score / current_price

        if max_ratio == min_ratio:
            value_score = 10.0
        else:
            normalized_ratio = (
                (ratio - min_ratio)
                / (max_ratio - min_ratio)
            )

            value_score = round(
                normalized_ratio * 20,
                2,
            )

        # ----------------------------------------------
        # 3. Historical price: maximum 15
        # ----------------------------------------------
        history_score = calculate_history_score(
            current_price=current_price,
            avg_price=avg_price,
            observations=observations,
        )

        # ----------------------------------------------
        # 4. Rating confidence: maximum 5
        # ----------------------------------------------
        rating_score = calculate_rating_score(
            rating=rating,
            reviews=reviews,
        )

        deal_score = round(
            technical_score
            + value_score
            + history_score
            + rating_score,
            2,
        )

        results.append(
            {
                "product_id": product_id,
                "current_price": current_price,
                "programming_score": programming_score,
                "technical_score": technical_score,
                "value_score": value_score,
                "history_score": history_score,
                "rating_score": rating_score,
                "deal_score": deal_score,
                "observations": observations,
                "avg_price": avg_price,
                "min_price": min_price,
                "max_price": max_price,
                "calculated_at": observed_at,
            }
        )

    connection.close()

    return results


def save_deal_scores(db_path, results):
    connection = duckdb.connect(db_path)

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS deal_scores (
            product_id VARCHAR,
            current_price DOUBLE,
            programming_score INTEGER,
            technical_score DOUBLE,
            value_score DOUBLE,
            history_score DOUBLE,
            rating_score DOUBLE,
            deal_score DOUBLE,
            observations INTEGER,
            avg_price DOUBLE,
            min_price DOUBLE,
            max_price DOUBLE,
            calculated_at TIMESTAMP
        )
        """
    )

    for result in results:
        connection.execute(
            """
            INSERT INTO deal_scores (
                product_id,
                current_price,
                programming_score,
                technical_score,
                value_score,
                history_score,
                rating_score,
                deal_score,
                observations,
                avg_price,
                min_price,
                max_price,
                calculated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                result["product_id"],
                result["current_price"],
                result["programming_score"],
                result["technical_score"],
                result["value_score"],
                result["history_score"],
                result["rating_score"],
                result["deal_score"],
                result["observations"],
                result["avg_price"],
                result["min_price"],
                result["max_price"],
                result["calculated_at"],
            ],
        )

    connection.close()

    logger.info(
        "Saved %s deal scores",
        len(results),
    )


def calculate_and_save_deal_scores(db_path):
    results = calculate_deal_scores(db_path)

    save_deal_scores(
        db_path=db_path,
        results=results,
    )

    excellent_deals = sum(
        1
        for result in results
        if result["deal_score"] >= 80
    )

    good_deals = sum(
        1
        for result in results
        if 70 <= result["deal_score"] < 80
    )

    fair_deals = sum(
        1
        for result in results
        if 60 <= result["deal_score"] < 70
    )

    weak_deals = sum(
        1
        for result in results
        if result["deal_score"] < 60
    )

    logger.info("DEAL SCORE SUMMARY")
    logger.info(
        "Products scored: %s",
        len(results),
    )
    logger.info(
        "Excellent deals: %s",
        excellent_deals,
    )
    logger.info(
        "Good deals: %s",
        good_deals,
    )
    logger.info(
        "Fair deals: %s",
        fair_deals,
    )
    logger.info(
        "Weak deals: %s",
        weak_deals,
    )

    if weak_deals > 0:
        logger.warning(
            "%s products classified as Weak Deal",
            weak_deals,
        )

    return db_path