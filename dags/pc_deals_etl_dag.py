from datetime import datetime, timedelta
import sys
import pendulum

from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator


sys.path.append("/opt/airflow/src")

from extract.scrape_products import extract_products
from transform.clean_products import transform_products
from score.score_products import score_products
from load.load_duckdb import load_products
from validate.validate_warehouse import validate_warehouse
from score.deal_score import calculate_and_save_deal_scores

default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}


with DAG(
    dag_id="pc_deals_etl",
    description="ETL pipeline for PC price and performance analysis",
    start_date= pendulum.datetime(2026, 8, 16, tz ="Europe/Rome"),
    schedule="0 8 * * *",
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["pc-deals", "etl", "portfolio"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract_products",
        python_callable=extract_products,
    )

    transform_task = PythonOperator(
        task_id = "transform_products",
        python_callable=transform_products,
        op_args = [extract_task.output],  # Nuovo modo per passare il file estratto come argomento alla funzione di trasformazione in Airflow 3
        #op_args = ["{{ ti.xcom_pull(task_ids='extract_products') }}"], #versione equivalente tramite stringa Jinja per passare il file estratto come argomento alla funzione di trasformazione   
    )

    score_task = PythonOperator(
        task_id="score_products",
        python_callable=score_products,
        op_args=[transform_task.output]
    )

    load_task = PythonOperator(
        task_id="load_products",
        python_callable=load_products,
        op_args=[score_task.output],  # Nuovo modo per passare il file trasformato come argomento alla funzione di caricamento in Airflow 3
        #op_args=["{{ ti.xcom_pull(task_ids='transform_products') }}"], #versione equivalente tramite stringa Jinja per passare il file trasformato come argomento alla funzione di caricamento
    )

    deal_score_task = PythonOperator(
    task_id="calculate_deal_scores",
    python_callable=calculate_and_save_deal_scores,
    op_args=[load_task.output],
    )

    validate_task = PythonOperator(
    task_id="validate_warehouse",
    python_callable=validate_warehouse,
    op_args=[load_task.output],
    )

    extract_task >> transform_task >> score_task >> load_task >> deal_score_task >> validate_task