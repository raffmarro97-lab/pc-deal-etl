- calculates a Deal Score
- validates warehouse data quality
- exposes the current best deals through an analytical DuckDB view

---

## Business Requirements

The project focuses on laptops suitable for programming with the following requirements:

- Price: €450 – €1000
- RAM: minimum 16 GB
- Storage: minimum 512 GB
- GPU: optional

The goal is not simply to identify the most powerful laptop, but to rank products based on the balance between:

- technical suitability
- price
- historical price behavior
- rating and review confidence

---

## Tech Stack

- Python
- Apache Airflow
- Docker / Docker Compose
- DuckDB
- Oxylabs API
- Amazon Search results
- Pytest
- Regex-based hardware parsing

---

## Architecture

```text
Oxylabs / Amazon
       |
       v
    Extract
       |
       v
    Raw JSON
       |
       v
   Transform
       |
       v
Programming Score
       |
       v
     DuckDB
    /      \
products  price_history
    \      /
     \    /
     Deal Score
         |
         v
    deal_scores
         |
         v
   current_deals
         |
         v
      Top Deals
Apache Airflow orchestrates the complete workflow.
________________________________________
Airflow DAG
The pipeline follows this task dependency:
extract_products
        |
        v
transform_products
        |
        v
score_products
        |
        v
load_products
        |
        v
calculate_deal_scores
        |
        v
validate_warehouse
The DAG is scheduled to run once per day.
Configuration:
•	timezone: Europe/Rome 
•	catchup: disabled 
•	maximum active DAG runs: 1 
•	retries: 2 
•	exponential retry backoff enabled 
________________________________________
Project Structure
pc-deal-etl/
│
├── dags/
│   └── pc_deals_etl_dag.py
│
├── src/
│   ├── extract/
│   │   └── scrape_products.py
│   │
│   ├── transform/
│   │   └── clean_products.py
│   │
│   ├── score/
│   │   ├── programming_score.py
│   │   ├── score_products.py
│   │   └── deal_score.py
│   │
│   ├── load/
│   │   └── load_duckdb.py
│   │
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
________________________________________
Extract
The Extract stage queries Amazon search results through the Oxylabs API.
Example search:
laptop programming 16GB RAM SSD
The API response is stored in the raw layer before normalization.
This preserves the original source data and makes debugging easier.
Normalized fields include:
•	product_id 
•	title 
•	price 
•	currency 
•	rating 
•	reviews 
•	url 
________________________________________
Transform
The transformation stage parses laptop hardware specifications from Amazon product titles using regular expressions.
Extracted attributes include:
•	brand 
•	CPU 
•	GPU 
•	RAM 
•	storage 
Example:
ASUS Laptop Intel Core 7 Processor 150U 16GB RAM 1TB SSD
becomes:
Brand: ASUS
CPU: Intel Core 7 Processor 150U
RAM: 16 GB
Storage: 1024 GB
Products that do not satisfy the minimum requirements are filtered out.
________________________________________
Programming Suitability Score
Each laptop receives a Programming Suitability Score between 0 and 100.
The score is based on:
Component	Maximum Score
CPU	55
RAM	25
Storage	15
GPU	5
Total	100
GPU is treated as an optional bonus rather than a hard requirement.
Programming classes:
Score	Classification
85–100	Excellent
70–84	Good
55–69	Acceptable
< 55	Poor
Important
The Programming Suitability Score is a custom heuristic developed for this project.
It is not an official hardware benchmark and does not replace standardized CPU/GPU benchmark datasets.
The purpose of the score is to provide a transparent and reproducible ranking suitable for the project's programming-focused use case.
________________________________________
DuckDB Warehouse
The warehouse currently contains three main datasets.
products
Stores the current product state:
•	product_id 
•	title 
•	brand 
•	CPU 
•	GPU 
•	RAM 
•	storage 
•	programming score 
•	programming class 
•	component scores 
•	URL 
price_history
Stores one price observation for each pipeline run.
Fields include:
•	product_id 
•	price 
•	currency 
•	rating 
•	reviews 
•	observed_at 
This allows the pipeline to build a historical price dataset over time.
deal_scores
Stores calculated deal metrics including:
•	technical score 
•	value score 
•	historical price score 
•	rating score 
•	final Deal Score 
________________________________________
Deal Score
The Deal Score evaluates whether a laptop represents a good purchase opportunity.
Weights:
Component	Maximum
Programming quality	60
Price / performance	20
Historical price	15
Rating confidence	5
Total	100
The historical component uses a neutral score when insufficient historical observations are available.
This avoids penalizing newly discovered products.
Deal classifications:
Deal Score	Classification
>= 80	Excellent Deal
>= 70	Good Deal
>= 60	Fair Deal
< 60	Weak Deal
________________________________________
Analytics View
The project exposes a DuckDB view called:
current_deals
The view combines:
•	product information 
•	latest price 
•	Programming Score 
•	Deal Score 
•	price history statistics 
Example query:
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
This produces the current Top Deals ranking.
________________________________________
Data Quality
The pipeline includes warehouse validation checks.
Hard failures include:
•	empty products table 
•	NULL product identifiers 
•	duplicate product identifiers 
•	invalid prices 
•	insufficient RAM 
•	insufficient storage 
•	Programming Score outside 0–100 
•	Deal Score outside 0–100 
•	orphan price history rows 
•	orphan Deal Score rows 
Quality warnings include:
•	unknown CPU 
•	unknown brand 
Unknown GPU values are informational because GPU is optional.
________________________________________
Observability
Airflow logs expose execution metrics for each pipeline stage.
Examples include:
Transform
•	input product count 
•	output product count 
•	products filtered by price 
•	missing RAM 
•	missing storage 
•	unknown CPUs 
•	unknown brands 
•	unknown GPUs 
Programming Score
•	products scored 
•	Excellent products 
•	Good products 
•	Acceptable products 
•	Poor products 
Deal Score
•	Excellent Deals 
•	Good Deals 
•	Fair Deals 
•	Weak Deals 
Load
•	number of products loaded 
•	total warehouse product count 
•	price history observation count 
________________________________________
Automated Tests
The project uses Pytest.
Test coverage includes:
•	hardware parsing 
•	CPU parsing 
•	RAM parsing 
•	storage parsing 
•	GPU parsing 
•	Programming Score 
•	Programming classifications 
•	Deal Score components 
•	historical price scoring 
•	regression tests for previously discovered parser issues 
Run all tests with:
docker compose exec airflow-worker bash -c "cd /opt/airflow && pytest tests -v"
________________________________________
Running the Project
1. Configure environment variables
Create a .env file containing:
AIRFLOW_UID=50000
OXYLABS_USERNAME=your_username
OXYLABS_PASSWORD=your_password
Never commit the .env file.
________________________________________
2. Build the Docker image
docker compose build
________________________________________
3. Initialize Airflow
docker compose up airflow-init
________________________________________
4. Start Airflow
docker compose up -d
The Airflow UI is available at:
http://localhost:8080
________________________________________
5. Run the DAG
The DAG is named:
pc_deals_etl
It can be triggered manually through the Airflow UI or executed automatically according to its schedule.
________________________________________
Security
API credentials are provided through environment variables.
The .env file is excluded from version control.
An .env.example file can be committed to document required variables without exposing secrets.
________________________________________
Future Improvements
Possible future improvements include:
•	integrate external CPU benchmark datasets 
•	migrate the warehouse to BigQuery 
•	build a dashboard for Top Deals 
•	send alerts when a significant price drop occurs 
•	improve Amazon product deduplication 
•	expand hardware parsing rules 
•	introduce parser quality thresholds 
•	add GitHub Actions CI 
•	add data lineage and monitoring 
•	support multiple ecommerce sources 
•	separate historical Deal Score snapshots from current serving models 
________________________________________
What This Project Demonstrates
This project demonstrates practical knowledge of:
•	ETL pipeline design 
•	workflow orchestration 
•	containerization 
•	API integration 
•	data normalization 
•	semi-structured data parsing 
•	dimensional separation between current state and history 
•	data quality validation 
•	observability 
•	scoring and analytical modeling 
•	automated testing 
•	reproducible local development 



