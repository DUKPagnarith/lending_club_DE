"""
DAG 02 — Clean raw loans → staging.loans_cleaned
Runs: after ingestion completes
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {"owner": "credit_risk", "retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="credit_risk_cleaning",
    description="Clean raw loans, create targets, OOT split",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["credit_risk", "cleaning"],
) as dag:

    clean = BashOperator(
        task_id="spark_clean_loans",
        bash_command=(
            "spark-submit "
            "--master spark://spark-master:7077 "
            "--packages org.apache.hadoop:hadoop-aws:3.3.4,org.postgresql:postgresql:42.6.0 "
            "/opt/airflow/spark_jobs/02_clean.py"
        ),
    )
