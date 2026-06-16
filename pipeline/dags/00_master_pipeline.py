"""
DAG 00 — Master Pipeline Orchestrator
Triggers the full credit-risk pipeline in sequence:
  01_ingestion → 02_cleaning → 02b_feature_engineering
  → 03_pd_training → 04_lgd_ead_training → 05_batch_scoring → 06_monitoring

Run this DAG to kick off the entire pipeline from scratch.
Individual DAGs can still be triggered independently for partial re-runs.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sensors.external_task import ExternalTaskSensor

default_args = {"owner": "credit_risk", "retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="credit_risk_master_pipeline",
    description="End-to-end pipeline: ingest → clean → features → PD → LGD/EAD → score → monitor",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["credit_risk", "master"],
) as dag:

    trigger_ingest = TriggerDagRunOperator(
        task_id="trigger_01_ingestion",
        trigger_dag_id="credit_risk_ingestion",
        wait_for_completion=True,
        poke_interval=30,
    )

    trigger_clean = TriggerDagRunOperator(
        task_id="trigger_02_cleaning",
        trigger_dag_id="credit_risk_cleaning",
        wait_for_completion=True,
        poke_interval=30,
    )

    trigger_features = TriggerDagRunOperator(
        task_id="trigger_02b_feature_engineering",
        trigger_dag_id="credit_risk_feature_engineering",
        wait_for_completion=True,
        poke_interval=30,
    )

    trigger_pd = TriggerDagRunOperator(
        task_id="trigger_03_pd_training",
        trigger_dag_id="credit_risk_pd_training",
        wait_for_completion=True,
        poke_interval=60,
    )

    trigger_lgd = TriggerDagRunOperator(
        task_id="trigger_04_lgd_ead",
        trigger_dag_id="credit_risk_lgd_ead_training",
        wait_for_completion=True,
        poke_interval=30,
    )

    trigger_score = TriggerDagRunOperator(
        task_id="trigger_05_batch_scoring",
        trigger_dag_id="credit_risk_batch_scoring",
        wait_for_completion=True,
        poke_interval=30,
    )

    trigger_monitor = TriggerDagRunOperator(
        task_id="trigger_06_monitoring",
        trigger_dag_id="credit_risk_monitoring",
        wait_for_completion=True,
        poke_interval=30,
    )

    (trigger_ingest >> trigger_clean >> trigger_features
     >> trigger_pd >> trigger_lgd >> trigger_score >> trigger_monitor)
