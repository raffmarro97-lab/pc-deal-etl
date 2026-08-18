# 💻 PC Deal ETL Pipeline — Airflow Data Engineering Project

[![Python](https://img.shields.io/badge/Python-3.13-green)](https://www.python.org/)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-3.3.1-blue)](https://airflow.apache.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://www.docker.com/)
[![DuckDB](https://img.shields.io/badge/DuckDB-Analytical%20Warehouse-yellow)](https://duckdb.org/)
[![Pytest](https://img.shields.io/badge/Pytest-Automated%20Tests-orange)](https://docs.pytest.org/)
[![Oxylabs](https://img.shields.io/badge/Oxylabs-Amazon%20Search-purple)](https://oxylabs.io/)

## 🎯 Overview

This project implements an end-to-end **Data Engineering ETL pipeline** that collects laptop listings from Amazon through Oxylabs, parses hardware specifications, evaluates programming suitability, tracks historical prices, and ranks the best laptop deals.

The pipeline is orchestrated with **Apache Airflow**, runs inside **Docker containers**, and uses **DuckDB** as the analytical warehouse.

The project focuses on laptops suitable for programming and applies the following minimum requirements:

- price between **€450 and €1000**;
- at least **16 GB RAM**;
- at least **512 GB storage**;
- GPU is optional.

The goal is not simply to identify the most powerful laptop, but to rank products based on the balance between:

- technical suitability;
- price;
- historical price behavior;
- rating and review confidence.

---

## 📐 Overall Architecture

```text
Oxylabs / Amazon
       │
       ▼
    Extract
       │
       ▼
    Raw JSON
       │
       ▼
   Transform
       │
       ▼
Programming Score
       │
       ▼
     DuckDB
    /      \
products  price_history
    \      /
     \    /
     Deal Score
         │
         ▼
    deal_scores
         │
         ▼
   current_deals
         │
         ▼
      Top Deals
```

Apache Airflow orchestrates the complete workflow from extraction to warehouse validation.

---

## ⚙️ Airflow DAG

The pipeline follows this task dependency:

```text
extract_products
        │
        ▼
transform_products
        │
        ▼
score_products
        │
        ▼
load_products
        │
        ▼
calculate_deal_scores
        │
        ▼
validate_warehouse
```

The DAG is scheduled to run once per day.

### DAG configuration

| Setting | Value |
|---|---|
| Timezone | `Europe/Rome` |
| Catchup | Disabled |
| Maximum active DAG runs | `1` |
| Retries | `2` |
| Retry strategy | Exponential backoff |

---

## 🧱 Repository Structure

```text
pc-deal-etl/
│
├── dags/
│   └── pc_deals_etl_dag.py
│
├── src/
│   ├── extract/
│   │   └── scrape_products.py
│   ├── transform/
│   │   └── clean_products.py
│   ├── score/
│   │   ├── programming_score.py
│   │   ├── score_products.py
│   │   └── deal_score.py
│   ├── load/
│   │   └── load_duckdb.py
│   └── validate/
│       ├── validate_warehouse.py
│       └── validate_parser_quality.py
│
├── tests/
│   ├── conftest.py
│   ├── test_hardware_parser.py
│   ├── test_programming_score.py
│   └── test_deal_score.py
│
├── data/
│   ├── raw/
│   ├── staging/
│   └── warehouse/
│
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

---

# 📥 Extract — Amazon Search Data via Oxylabs

The Extract stage queries Amazon search results through the **Oxylabs API**.

Example search:

```text
laptop programming 16GB RAM SSD
```

The API response is stored in the raw layer before normalization.

This preserves the original source data and makes debugging and parser-quality analysis easier.

## Normalized fields

| Field | Description |
|---|---|
| `product_id` | Amazon product identifier |
| `title` | Product title |
| `price` | Current product price |
| `currency` | Price currency |
| `rating` | Amazon rating |
| `reviews` | Number of reviews |
| `url` | Product URL |

---

# 🔧 Transform — Hardware Parsing and Filtering

The transformation stage parses laptop hardware specifications from Amazon product titles using regular expressions.

Extracted attributes include:

- brand;
- CPU;
- GPU;
- RAM;
- storage.

Example:

```text
ASUS Laptop Intel Core 7 Processor 150U 16GB RAM 1TB SSD
```

becomes:

```text
Brand: ASUS
CPU: Intel Core 7 Processor 150U
RAM: 16 GB
Storage: 1024 GB
```

## Business filters

| Rule | Requirement |
|---|---:|
| Minimum price | €450 |
| Maximum price | €1000 |
| Minimum RAM | 16 GB |
| Minimum storage | 512 GB |
| GPU | Optional |

CPU and brand parsing issues are monitored as data-quality warnings.

An unknown GPU does not invalidate a product because a dedicated GPU is not a hard requirement for the programming-focused use case.

---

# 🧠 Programming Suitability Score

Each laptop receives a **Programming Suitability Score** between `0` and `100`.

## Score weights

| Component | Maximum Score |
|---|---:|
| CPU | 55 |
| RAM | 25 |
| Storage | 15 |
| GPU | 5 |
| **Total** | **100** |

GPU contributes only a small optional bonus.

## Programming classes

| Score | Classification |
|---|---|
| 85–100 | Excellent |
| 70–84 | Good |
| 55–69 | Acceptable |
| < 55 | Poor |

> **Important:** the Programming Suitability Score is a custom heuristic developed for this project. It is not an official hardware benchmark and does not replace standardized CPU or GPU benchmark datasets.

---

# 🗄️ DuckDB Warehouse

The warehouse separates current product state from historical observations and analytical scoring.

## `products`

Stores the latest known product characteristics, including product identity, parsed hardware specifications, Programming Suitability Score, component scores, and product URL.

## `price_history`

Stores one price observation for every product loaded during a pipeline run.

Fields include:

- `product_id`;
- `price`;
- `currency`;
- `rating`;
- `reviews`;
- `observed_at`.

## `deal_scores`

Stores calculated deal metrics, including:

- technical score;
- value score;
- historical price score;
- rating score;
- final Deal Score;
- price-history statistics;
- calculation timestamp.

---

# 💰 Deal Score

The **Deal Score** evaluates whether a laptop represents a good purchase opportunity.

## Score weights

| Component | Maximum |
|---|---:|
| Programming quality | 60 |
| Price / performance | 20 |
| Historical price | 15 |
| Rating confidence | 5 |
| **Total** | **100** |

When there are not enough historical observations, the historical component receives a neutral score.

## Deal classifications

| Deal Score | Classification |
|---|---|
| >= 80 | Excellent Deal |
| >= 70 | Good Deal |
| >= 60 | Fair Deal |
| < 60 | Weak Deal |

---

# 📊 Analytics View — `current_deals`

The project exposes an analytical DuckDB view called `current_deals`.

The view combines:

- product information;
- latest price;
- Programming Suitability Score;
- Deal Score;
- historical price statistics;
- deal classification.

Example query:

```sql
SELECT
    brand,
    cpu,
    ram_gb,
    storage_gb,
    current_price,
    programming_score,
    deal_score,
    deal_class
FROM current_deals
ORDER BY deal_score DESC
LIMIT 5;
```

This produces the current **Top Deals** ranking.

---

# ✅ Data Quality Validation

The final Airflow task validates warehouse consistency and business rules.

## Hard failures

The pipeline fails when it detects:

- an empty `products` table;
- NULL product identifiers;
- duplicate product identifiers;
- invalid prices;
- RAM below the minimum requirement;
- storage below the minimum requirement;
- Programming Scores outside the `0–100` range;
- Deal Scores outside the `0–100` range;
- orphan `price_history` rows;
- orphan `deal_scores` rows.

## Quality warnings

The pipeline reports warnings for:

- unknown CPU;
- unknown brand;
- low product volume.

Unknown GPU values are informational because GPU is optional.

---

# 📈 Observability and Logging

The pipeline uses structured Python logging so that execution metrics are visible directly in Airflow task logs.

### Transform

- input product count;
- output product count;
- products filtered by price;
- missing RAM;
- RAM below minimum;
- missing storage;
- storage below minimum;
- unknown CPUs;
- unknown brands;
- unknown GPUs.

### Programming Score

- products scored;
- Excellent products;
- Good products;
- Acceptable products;
- Poor products.

### Load

- products processed during the run;
- total rows in `products`;
- total observations in `price_history`;
- DuckDB database path.

### Deal Score

- products scored;
- Excellent Deals;
- Good Deals;
- Fair Deals;
- Weak Deals.

---

# 🧪 Testing Strategy

The project uses **Pytest** to validate the most important parts of the pipeline independently from Airflow.

```text
Hardware parsing
      │
      ├── CPU
      ├── RAM
      ├── Storage
      └── GPU

Programming Score
      │
      ├── component scores
      ├── final score
      └── classification

Deal Score
      │
      ├── rating confidence
      └── historical price score
```

Test coverage includes:

- hardware parsing;
- Programming Suitability Score;
- programming classifications;
- Deal Score components;
- historical price scoring;
- regression tests for previously discovered parser issues.

Run all tests with:

```bash
docker compose exec airflow-worker bash -c "cd /opt/airflow && pytest tests -v"
```

---

# 🐳 Running the Project

## 1. Configure environment variables

Create a `.env` file:

```env
AIRFLOW_UID=50000
OXYLABS_USERNAME=your_username
OXYLABS_PASSWORD=your_password
```

Never commit the real `.env` file.

A safe `.env.example` can be committed instead:

```env
AIRFLOW_UID=50000
OXYLABS_USERNAME=your_oxylabs_username
OXYLABS_PASSWORD=your_oxylabs_password
```

## 2. Build the Docker image

```bash
docker compose build
```

## 3. Initialize Airflow

```bash
docker compose up airflow-init
```

## 4. Start the services

```bash
docker compose up -d
```

Airflow UI:

```text
http://localhost:8080
```

## 5. Run the DAG

The DAG is named:

```text
pc_deals_etl
```

It can be triggered manually through the Airflow UI or executed automatically according to its daily schedule.

---

# 🔐 Security

API credentials are provided through environment variables.

The `.env` file is excluded from version control.

Only `.env.example`, containing placeholder values, should be committed.

Generated raw, staging, and warehouse data should also remain outside version control unless intentionally added for demonstration purposes.

---

# 🛠️ Tech Stack

| Technology | Usage |
|---|---|
| Python | ETL logic, parsing, scoring, validation |
| Apache Airflow | Workflow orchestration and scheduling |
| Docker | Reproducible containerized environment |
| Docker Compose | Multi-container Airflow environment |
| DuckDB | Local analytical warehouse |
| Oxylabs API | Amazon search data extraction |
| Amazon Search | Laptop product source |
| Pytest | Automated testing |
| Regular Expressions | Hardware specification parsing |
| Git / GitHub | Version control and project publication |

---

# 🚀 Future Improvements

Possible future improvements include:

- integrate external CPU benchmark datasets;
- migrate the warehouse to BigQuery;
- build a dashboard for Top Deals;
- send alerts when significant price drops occur;
- improve Amazon product deduplication;
- expand hardware parsing rules;
- introduce parser-quality thresholds;
- add GitHub Actions CI;
- add data lineage and more advanced monitoring;
- support multiple ecommerce sources;
- separate historical Deal Score snapshots from current serving models.

---

# 📌 Project Outcomes

This project demonstrates practical knowledge of:

- ETL pipeline design;
- workflow orchestration;
- containerization;
- API integration;
- raw-data preservation;
- data normalization;
- semi-structured text parsing;
- current-state and historical data modelling;
- incremental price-history collection;
- custom analytical scoring;
- data-quality validation;
- observability and structured logging;
- automated testing;
- reproducible local development;
- Git-based project organization.

The final output is an automated pipeline capable of producing a ranked analytical view of laptop deals for programming-oriented users.

# 👨‍💻 Author

**Raffaele Marro**  
Data Engineer | ETL Pipelines | Apache Airflow | Python | Docker | DuckDB

[LinkedIn](https://www.linkedin.com/in/raffaele-marro-6b1681282/)