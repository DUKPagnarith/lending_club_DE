"""
DAG 06 — Daily PSI monitoring: compare current score distribution vs training baseline
Writes results to risk.population_stability and alerts if PSI > 0.25
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {"owner": "credit_risk", "retries": 1, "retry_delay": timedelta(minutes=5)}


def compute_psi(**ctx):
    import os, json, joblib
    import numpy as np
    import pandas as pd
    from sqlalchemy import create_engine

    DATA   = "/opt/airflow/data/processed"
    MODELS = "/opt/airflow/data/models"
    DB_URL = os.getenv("DATABASE_URL",
             "postgresql://credit_risk:CreditRisk2026!@postgres/credit_risk")

    scorecard = pd.read_csv(f"{DATA}/scorecard.csv")
    FACTOR    = 20 / np.log(2)
    OFFSET    = 600.0
    score_map = dict(zip(scorecard["Feature"], scorecard["Score"]))
    final_feats = list(scorecard["Feature"])

    def compute_scores(df):
        s = pd.Series(OFFSET, index=df.index)
        for feat in final_feats:
            if feat in df.columns:
                s += df[feat].fillna(0).astype(float) * score_map.get(feat, 0)
        return s.round().clip(300, 850).astype(int)

    train = pd.read_parquet(f"{DATA}/train_preprocessed.parquet")
    test  = pd.read_parquet(f"{DATA}/test_preprocessed.parquet")

    train_scores = compute_scores(train)
    test_scores  = compute_scores(test)

    bins = np.arange(300, 860, 50)

    def psi(expected, actual, bins):
        exp_pct = np.histogram(expected, bins=bins)[0] / len(expected)
        act_pct = np.histogram(actual,   bins=bins)[0] / len(actual)
        exp_pct = np.clip(exp_pct, 1e-6, None)
        act_pct = np.clip(act_pct, 1e-6, None)
        return float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))

    psi_val    = psi(train_scores, test_scores, bins)
    psi_status = "STABLE" if psi_val < 0.1 else ("WARNING" if psi_val < 0.25 else "ALERT")

    result = pd.DataFrame([{
        "variable_name":   "credit_score",
        "psi_value":       round(psi_val, 6),
        "psi_status":      psi_status,
        "reference_date":  "2007-2015",
        "monitoring_date": ctx["ds"],
    }])

    result.to_csv(f"{DATA}/psi_results.csv", index=False)

    try:
        engine = create_engine(DB_URL)
        result.to_sql("population_stability", schema="risk", con=engine,
                      if_exists="append", index=False)
    except Exception as e:
        print(f"DB write skipped: {e}")

    print(f"PSI={psi_val:.4f} [{psi_status}]")
    if psi_status == "ALERT":
        raise ValueError(f"PSI ALERT: score distribution drift PSI={psi_val:.4f} > 0.25")


with DAG(
    dag_id="credit_risk_monitoring",
    description="Daily PSI monitoring — score distribution drift",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="0 6 * * *",  # 6am daily
    catchup=False,
    tags=["credit_risk", "monitoring", "psi"],
) as dag:

    psi_task = PythonOperator(task_id="compute_psi", python_callable=compute_psi)
