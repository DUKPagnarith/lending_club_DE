"""
DAG 01 — Ingest raw CSV from MinIO → PostgreSQL raw.loan_applications
Runs: manually triggered (one-time or on new data drop)
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "credit_risk",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="credit_risk_ingestion",
    description="Ingest raw Lending Club CSV from MinIO into PostgreSQL",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["credit_risk", "ingestion"],
) as dag:

    ingest = BashOperator(
        task_id="spark_ingest_csv",
        bash_command=(
            "spark-submit "
            "--master spark://spark-master:7077 "
            "--packages org.apache.hadoop:hadoop-aws:3.3.4,org.postgresql:postgresql:42.6.0 "
            "/opt/airflow/spark_jobs/01_ingest.py"
        ),
        env={
            "MINIO_URL": "http://minio:9000",
            "MINIO_USER": "{{ var.value.get('MINIO_USER', 'minioadmin') }}",
            "MINIO_PASSWORD": "{{ var.value.get('MINIO_PASSWORD', '') }}",
            "POSTGRES_USER": "{{ var.value.get('POSTGRES_USER', 'credit_risk') }}",
            "POSTGRES_PASSWORD": "{{ var.value.get('POSTGRES_PASSWORD', '') }}",
        },
    )
