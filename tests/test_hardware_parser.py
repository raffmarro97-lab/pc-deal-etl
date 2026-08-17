import sys

sys.path.append("/opt/airflow/src")

from transform.clean_products import (
    extract_brand,
    extract_cpu,
    extract_gpu,
    extract_ram,
    extract_storage,
)


TEST_CASES = [
    {
        "title": "ASUS TUF Gaming A15 AMD Ryzen 7 7735HS 16GB RAM NVIDIA GeForce RTX 4060 8GB 512GB SSD",
        "brand": "ASUS",
        "cpu": "AMD Ryzen 7 7735HS",
        "gpu": "NVIDIA GeForce RTX 4060",
        "ram_gb": 16,
        "storage_gb": 512,
    },
    {
        "title": "Lenovo LOQ Intel Core i7-13620H 16GB RAM RTX 4060 Laptop GPU 1TB SSD",
        "brand": "Lenovo",
        "cpu": "Intel Core i7-13620H",
        "gpu": "RTX 4060",
        "ram_gb": 16,
        "storage_gb": 1024,
    },
    {
        "title": "Acer Nitro V Intel Core i5-13420H 16GB DDR5 GeForce RTX 4050 512GB NVMe SSD",
        "brand": "Acer",
        "cpu": "Intel Core i5-13420H",
        "gpu": "GeForce RTX 4050",
        "ram_gb": 16,
        "storage_gb": 512,
    },
    {
        "title": "HP Gaming Laptop AMD Ryzen 5 7535HS 16GB RAM Radeon RX 7600S 1TB SSD",
        "brand": "HP",
        "cpu": "AMD Ryzen 5 7535HS",
        "gpu": "Radeon RX 7600S",
        "ram_gb": 16,
        "storage_gb": 1024,
    },
    {
        "title": "MSI Laptop Intel Core Ultra 7 155H 32GB RAM RTX 4070 1TB SSD",
        "brand": "MSI",
        "cpu": "Intel Core Ultra 7 155H",
        "gpu": "RTX 4070",
        "ram_gb": 32,
        "storage_gb": 1024,
    },
]


def run_tests():

    for i, case in enumerate(TEST_CASES, start=1):

        title = case["title"]

        actual = {
            "brand": extract_brand(title),
            "cpu": extract_cpu(title),
            "gpu": extract_gpu(title),
            "ram_gb": extract_ram(title),
            "storage_gb": extract_storage(title),
        }

        print(f"\nTEST {i}")
        print(title)

        for field, expected in case.items():

            if field == "title":
                continue

            result = actual[field]

            status = "PASS" if result == expected else "FAIL"

            print(
                f"{field}: "
                f"expected={expected!r}, "
                f"actual={result!r} "
                f"[{status}]"
            )


if __name__ == "__main__":
    run_tests()