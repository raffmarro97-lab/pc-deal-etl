import json
import logging
import re
from pathlib import Path


logger = logging.getLogger(__name__)


MIN_RAM_GB = 16
MIN_STORAGE_GB = 512

MIN_PRICE = 450
MAX_PRICE = 1000


def extract_brand(title):
    brands = [
        "ASUS",
        "Lenovo",
        "MSI",
        "Acer",
        "Dell",
        "HP",
        "Apple",
        "Samsung",
        "Gigabyte",
        "Razer",
        "Medion",
        "Microsoft",
        "LG",
        "Tivique",
        "Kayoote",
        "Tunhail",
    ]

    title_lower = title.lower()

    for brand in brands:
        if brand.lower() in title_lower:
            return brand

    return "Unknown"


def extract_cpu(title):
    patterns = [
        # -------------------------
        # Intel Core Ultra
        # -------------------------
        r"(Intel\s+Core\s+Ultra\s+[3579]\s+\d{3}[A-Za-z]*)",

        # -------------------------
        # New Intel naming
        # Example: Intel Core 7 Processor 150U
        # -------------------------
        r"(Intel[®™\s]+Core[™\s]+\d\s+(?:Processor\s+)?\d{3}[A-Za-z]*)",
        r"(Intel\s+Core\s+\d\s+(?:Processor\s+)?\d{3}[A-Za-z]*)",

        # -------------------------
        # Intel Core i
        # -------------------------
        r"(Intel\s+Core\s+i[3579]-?\d{4,5}[A-Za-z]*)",
        r"(Core\s+i[3579][-\s]?\d{4,5}[A-Za-z]*)",

        # Older Y-series
        r"(Core\s+i[3579][-\s]?\d[A-Za-z]\d{2})",

        # Intel without "Core"
        r"(Intel\s+i[3579]-?\d{4,5}[A-Za-z]*)",

        # Bare i5-1245U
        r"\b(i[3579]-?\d{4,5}[A-Za-z]*)\b",

        # -------------------------
        # AMD Ryzen
        # -------------------------
        r"(AMD\s+Ryzen\s+[3579]\s+\d{3,5}[A-Za-z]*)",
        r"(Ryzen\s+[3579]\s+\d{3,5}[A-Za-z]*)",

        r"(Ryzen\s+\d{4}[A-Za-z]*)",

        # Generic Ryzen fallback
        r"(AMD\s+Ryzen\s+[3579])",
        r"(Ryzen\s+[3579])",

        # -------------------------
        # Intel Celeron
        # -------------------------
        r"(Intel\s+Celeron\s+[A-Za-z]?\d{3,5})",
        r"(Celeron\s+[A-Za-z]?\d{2,5})",

        # -------------------------
        # Pentium
        # -------------------------
        r"(Intel\s+Pentium\s+(?:Gold\s+)?[A-Za-z0-9-]+)",
        r"(Pentium\s+Gold\s+[A-Za-z0-9-]+)",

        # -------------------------
        # AMD A-series
        # -------------------------
        r"(AMD\s+A\d+)",

        # -------------------------
        # Final Intel fallbacks
        # -------------------------
        r"(Intel\s+Core\s+i[3579])",
        r"(Intel\s+i[3579])",
    ]

    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)

        if match:
            return match.group(0)

    return "Unknown"


def extract_gpu(title):
    patterns = [
        # -------------------------
        # NVIDIA RTX
        # -------------------------
        r"(NVIDIA\s+GeForce\s+RTX\s+\d{4}(?:\s+Ti)?)",
        r"(GeForce\s+RTX\s+\d{4}(?:\s+Ti)?)",
        r"(NVIDIA\s+RTX\s+\d{4}(?:\s+Ti)?)",
        r"(RTX\s+\d{4}(?:\s+Ti)?)",
        r"(RTX\d{4}(?:\s+Ti)?)",

        # -------------------------
        # NVIDIA GTX
        # -------------------------
        r"(NVIDIA\s+GeForce\s+GTX\s+\d{3,4}(?:\s+Ti)?)",
        r"(GeForce\s+GTX\s+\d{3,4}(?:\s+Ti)?)",
        r"(GTX\s+\d{3,4}(?:\s+Ti)?)",

        # -------------------------
        # AMD Radeon RX
        # -------------------------
        r"(AMD\s+Radeon\s+RX\s+\d{4}[A-Za-z]*)",
        r"(Radeon\s+RX\s+\d{4}[A-Za-z]*)",

        # AMD Radeon RX Vega
        r"(AMD\s+Radeon\s+RX\s+Vega\s+\d+)",
        r"(Radeon\s+RX\s+Vega\s+\d+)",

        # AMD Radeon Vega
        r"(AMD\s+Radeon\s+Vega\s+\d+)",
        r"(Radeon\s+Vega\s+\d+)",

        # -------------------------
        # Intel graphics
        # -------------------------
        r"(Intel\s+Iris\s+Xe)",
        r"(Iris\s+Xe)",
        r"(Intel\s+UHD(?:\s+Graphics)?)",
        r"(UHD\s+Graphics)",
        r"(grafica\s+UHD)",

        # -------------------------
        # Intel Arc
        # -------------------------
        r"(Intel\s+Arc\s+[AB]\d{3,4}M?)",
        r"(Arc\s+[AB]\d{3,4}M?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)

        if match:
            return match.group(0)

    return "Unknown"


def extract_ram(title):
    patterns = [
        r"(\d+)\s*GB\s+RAM",
        r"(\d+)\s*GB\s+(?:di\s+)?RAM",
        r"RAM\s*:?\s*(\d+)\s*GB",
        r"RAM\s*:?\s*(\d+)\s*GB",
        r"(\d+)\s*GB\s+DDR[345X]*",
        r"(\d+)\s*GB\s*\+\s*\d+\s*GB\s+SSD",
    ]

    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)

        if match:
            return int(match.group(1))

    return None


def extract_storage(title):
    patterns = [
        (
            r"(\d+(?:[.,]\d+)?)\s*TB"
            r"(?:\s+(?:NVMe|PCIe))?"
            r"\s+SSD",
            "tb",
        ),

        (
            r"SSD"
            r"(?:\s+(?:NVMe|PCIe))?"
            r"\s*(\d+(?:[.,]\d+)?)\s*TB",
            "tb",
        ),

        (
            r"(\d+)\s*GB"
            r"(?:\s+(?:NVMe|PCIe))?"
            r"\s+SSD",
            "gb",
        ),

        (
            r"SSD"
            r"(?:\s+(?:NVMe|PCIe))?"
            r"\s*(\d+)\s*GB",
            "gb",
        ),
    ]

    for pattern, unit in patterns:
        match = re.search(pattern, title, re.IGNORECASE)

        if match:
            value = match.group(1).replace(",", ".")

            if unit == "tb":
                return int(float(value) * 1024)

            return int(value)

    return None


def transform_products(input_file):
    input_path = Path(input_file)

    with open(input_path, "r", encoding="utf-8") as file:
        products = json.load(file)

    transformed_products = []

    stats = {
        "input_products": len(products),
        "price_filtered": 0,
        "ram_missing": 0,
        "ram_below_minimum": 0,
        "storage_missing": 0,
        "storage_below_minimum": 0,
        "cpu_unknown": 0,
        "brand_unknown": 0,
        "gpu_unknown": 0,
    }

    for product in products:
        title = product.get("title", "")

        product["brand"] = extract_brand(title)
        product["cpu"] = extract_cpu(title)
        product["gpu"] = extract_gpu(title)
        product["ram_gb"] = extract_ram(title)
        product["storage_gb"] = extract_storage(title)

        if product["brand"] == "Unknown":
            stats["brand_unknown"] += 1

        if product["cpu"] == "Unknown":
            stats["cpu_unknown"] += 1

        if product["gpu"] == "Unknown":
            stats["gpu_unknown"] += 1

        price = product.get("price")

        if price is None or price < MIN_PRICE or price > MAX_PRICE:
            stats["price_filtered"] += 1
            continue

        if product["ram_gb"] is None:
            stats["ram_missing"] += 1
            continue

        if product["ram_gb"] < MIN_RAM_GB:
            stats["ram_below_minimum"] += 1
            continue

        if product["storage_gb"] is None:
            stats["storage_missing"] += 1
            continue

        if product["storage_gb"] < MIN_STORAGE_GB:
            stats["storage_below_minimum"] += 1
            continue

        transformed_products.append(product)

    output_dir = Path("/opt/airflow/data/staging")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"clean_{input_path.name}"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            transformed_products,
            file,
            indent=4,
            ensure_ascii=False,
        )

    # --------------------------------------------------
    # Transform observability
    # --------------------------------------------------
    logger.info("TRANSFORM SUMMARY")
    logger.info("Input products: %s", stats["input_products"])
    logger.info("Output products: %s", len(transformed_products))
    logger.info("Price filtered: %s", stats["price_filtered"])
    logger.info("RAM missing: %s", stats["ram_missing"])
    logger.info(
        "RAM below minimum: %s",
        stats["ram_below_minimum"],
    )
    logger.info(
        "Storage missing: %s",
        stats["storage_missing"],
    )
    logger.info(
        "Storage below minimum: %s",
        stats["storage_below_minimum"],
    )

    if stats["cpu_unknown"] > 0:
        logger.warning(
            "CPU Unknown: %s",
            stats["cpu_unknown"],
        )
    else:
        logger.info("CPU Unknown: 0")

    if stats["brand_unknown"] > 0:
        logger.warning(
            "Brand Unknown: %s",
            stats["brand_unknown"],
        )
    else:
        logger.info("Brand Unknown: 0")

    # GPU is optional, therefore not treated as a warning.
    logger.info(
        "GPU Unknown: %s (optional field)",
        stats["gpu_unknown"],
    )

    logger.info(
        "Transformed data saved to: %s",
        output_file,
    )

    return str(output_file)