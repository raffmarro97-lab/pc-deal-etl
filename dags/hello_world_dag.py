from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator


def print_hello():
    print("Hello from PythonOperator!")
    print("Our PC Deal ETL project is working.")


with DAG(
    dag_id="hello_world_dag",
    description="First test DAG for the PC Deal ETL project",
    start_date=datetime(2026, 8, 1),
    schedule="*/5 * * * *",
    catchup=False,
    tags=["pc-deal-etl", "learning"],
) as dag:

    bash_task = BashOperator(
        task_id="hello_from_bash",
        bash_command='echo "Hello from BashOperator!"',
    )

    python_task = PythonOperator(
        task_id="hello_from_python",
        python_callable=print_hello,
    )

    bash_task >> python_task