import json
import logging
from pathlib import Path

from score.programming_score import calculate_programming_score


logger = logging.getLogger(__name__)


def score_products(input_file):
    input_path = Path(input_file)

    with open(input_path, "r", encoding="utf-8") as file:
        products = json.load(file)

    scored_products = []

    class_counts = {
        "Excellent": 0,
        "Good": 0,
        "Acceptable": 0,
        "Poor": 0,
    }

    for product in products:
        score_data = calculate_programming_score(product)

        product.update(score_data)

        scored_products.append(product)

    output_dir = Path("/opt/airflow/data/staging")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"scored_{input_path.name}"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            scored_products,
            file,
            indent=4,
            ensure_ascii=False,
        )

    for product in scored_products:
        programming_class = product.get("programming_class")

        if programming_class in class_counts:
            class_counts[programming_class] += 1

    logger.info("PROGRAMMING SCORE SUMMARY")
    logger.info("Scored products: %s", len(scored_products))
    logger.info("Excellent: %s", class_counts["Excellent"])
    logger.info("Good: %s", class_counts["Good"])
    logger.info("Acceptable: %s", class_counts["Acceptable"])
    logger.info("Poor: %s", class_counts["Poor"])

    if class_counts["Poor"] > 0:
        logger.warning(
            "%s products classified as Poor",
            class_counts["Poor"],
        )

    logger.info(
        "Scored data saved to: %s",
        output_file,
    )

    return str(output_file)