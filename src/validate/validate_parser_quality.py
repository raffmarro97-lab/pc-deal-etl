import json
from pathlib import Path

from transform.clean_products import (
    extract_brand,
    extract_cpu,
    extract_gpu,
    extract_ram,
    extract_storage,
)


def parser_quality_report(input_file):
    input_path = Path(input_file)

    with open(input_path, "r", encoding="utf-8") as file:
        products = json.load(file)

    total_products = len(products)

    if total_products == 0:
        raise ValueError("No products found in input file.")

    issues = []

    stats = {
        "brand_unknown": 0,
        "cpu_unknown": 0,
        "gpu_unknown": 0,
        "ram_missing": 0,
        "storage_missing": 0,
    }

    print("\n" + "=" * 80)
    print("REAL DATA PARSER QUALITY REPORT")
    print("=" * 80)

    for product in products:
        title = product.get("title", "")
        product_id = product.get("product_id")

        brand = extract_brand(title)
        cpu = extract_cpu(title)
        gpu = extract_gpu(title)
        ram_gb = extract_ram(title)
        storage_gb = extract_storage(title)

        product_issues = []

        if brand == "Unknown":
            stats["brand_unknown"] += 1
            product_issues.append("brand")

        if cpu == "Unknown":
            stats["cpu_unknown"] += 1
            product_issues.append("cpu")

        if gpu == "Unknown":
            stats["gpu_unknown"] += 1
            #product_issues.append("gpu")

        if ram_gb is None:
            stats["ram_missing"] += 1
            product_issues.append("ram")

        if storage_gb is None:
            stats["storage_missing"] += 1
            product_issues.append("storage")

        if product_issues:
            issues.append(
                {
                    "product_id": product_id,
                    "title": title,
                    "issues": product_issues,
                    "parsed": {
                        "brand": brand,
                        "cpu": cpu,
                        "gpu": gpu,
                        "ram_gb": ram_gb,
                        "storage_gb": storage_gb,
                    },
                }
            )

    print(f"\nTotal products analysed: {total_products}")

    print("\nMissing / Unknown values:")
    print(f"Brand Unknown:   {stats['brand_unknown']}")
    print(f"CPU Unknown:     {stats['cpu_unknown']}")
    print(
        f"GPU Unknown:     {stats['gpu_unknown']} "
        "(optional field - accepted)"
    )
    print(f"RAM missing:     {stats['ram_missing']}")
    print(f"Storage missing: {stats['storage_missing']}")

    print("\nRecognition rates:")

    required_fields = {
        "brand_unknown": stats["brand_unknown"],
        "cpu_unknown": stats["cpu_unknown"],
        "ram_missing": stats["ram_missing"],
        "storage_missing": stats["storage_missing"],
    }

    for field, missing in stats.items():
        recognized = total_products - missing
        percentage = (recognized / total_products) * 100

        print(
            f"{field:<18} "
            f"{recognized}/{total_products} "
            f"({percentage:.1f}%)"
        )

    gpu_recognized = total_products - stats["gpu_unknown"]

    print(
        f"{'gpu_optional':<18} "
        f"{gpu_recognized}/{total_products} "
        f"(optional)"
    )


    print("\n" + "=" * 80)
    print("PRODUCTS WITH PARSER ISSUES")
    print("=" * 80)

    if not issues:
        print("\nNo parser issues found.")
    else:
        for issue in issues:
            print(f"\nProduct ID: {issue['product_id']}")
            print(f"Problems: {', '.join(issue['issues'])}")
            print(f"Title: {issue['title']}")

            print("Parsed:")
            print(f"  Brand:   {issue['parsed']['brand']}")
            print(f"  CPU:     {issue['parsed']['cpu']}")
            print(f"  GPU:     {issue['parsed']['gpu']}")
            print(f"  RAM:     {issue['parsed']['ram_gb']}")
            print(f"  Storage: {issue['parsed']['storage_gb']}")

    print("\n" + "=" * 80)

    return stats


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise ValueError(
            "Usage: python validate_parser_quality.py "
            "<products_json_file>"
        )

    parser_quality_report(sys.argv[1])