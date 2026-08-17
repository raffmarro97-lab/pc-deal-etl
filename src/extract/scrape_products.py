import json
import os
from datetime import datetime
from pathlib import Path

import requests

MIN_PRICE = 450
MAX_PRICE = 1000

API_URL = "https://realtime.oxylabs.io/v1/queries"

def normalize_products(data):
    """
    Convert the Oxylabs Amazon Search response
    into the internal schema used by our ETL pipeline.
    """

    normalized_products = []

    results = data.get("results", [])

    if not results:
        return normalize_products

    content = results[0].get("content", {})

    amazon_results = content.get("results", {})

    organic_products = amazon_results.get("organic", [])

    for item in organic_products:
        price = item.get("price")

        # Ignore products without a valid price
        if price is None or price <= 0:
            continue

        # Our budget constraint
        if price < MIN_PRICE or price > MAX_PRICE:
            continue

        relative_url = item.get("url")

        if relative_url:
            product_url = f"https://www.amazon.it{relative_url}"
        else:
            product_url = None

        product = {
            "product_id": item.get("asin"),
            "title": item.get("title"),
            "price": price,
            "currency": item.get("currency"),
            "rating": item.get("rating"),
            "reviews": item.get("reviews_count"),
            "url": product_url, 
        }

        normalized_products.append(product)

    return normalized_products

def extract_products():

    username = os.getenv("OXYLABS_USERNAME")
    password = os.getenv("OXYLABS_PASSWORD")

    if not username or not password:
        raise ValueError(
            "Oxylabs credentials are missing. "
            "Check OXYLABS_USERNAME and OXYLABS_PASSWORD."
        )

    payload = {
        "source": "amazon_search",
        "query": "laptop programming 16GB RAM SSD",
        "domain": "it",
        "parse": True,
    }

    response = requests.post(
        API_URL,
        auth=(username, password),
        json=payload,
        timeout=120
    )

    if not response.ok:
        print("STATUS CODE:", response.status_code)
        print("RESPONSE BODY:")
        print(response.text)

    response.raise_for_status()

    data = response.json()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = Path("/opt/airflow/data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------
    # Save original API response
    # -------------------------

    raw_output_file = output_dir / f"amazon_raw_{timestamp}.json"

    with open(raw_output_file, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
        )

    # -------------------------
    # Normalize products
    # -------------------------

    products = normalize_products(data)

    if not products:
        raise ValueError(
            "No valid products after normalization"
        )

    output_file = (
        output_dir /
        f"products_{timestamp}.json"
    )

    with open(output_file, "w", encoding= "utf-8") as file:
        json.dump(
            products,
            file,
            indent=4,
            ensure_ascii=False,
        )


    print(
        f"Retrieved {len(products)} valid products "
        f"with price between €{MIN_PRICE} and €{MAX_PRICE}"
    )

    print(
        f"Raw Oxylabs response saved to: "
        f"{raw_output_file}"
    )

    print(
        f"Normalized products saved to: "
        f"{output_file}"
    )

    return str(output_file)


if __name__ == "__main__":
    extract_products()