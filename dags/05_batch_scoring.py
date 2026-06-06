"""
DAG 05 — Batch score OOT test set → risk.expected_loss table in PostgreSQL
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {"owner": "credit_risk", "retries": 1, "retry_delay": timedelta(minutes=5)}

FEATURES = ["funded_amnt", "term_int", "int_rate", "dti", "fico_score",
            "annual_inc", "revol_util", "inq_last_6mths"]


def batch_score(**ctx):
    import os, json, joblib
    import numpy as np
    import pandas as pd
    from sqlalchemy import create_engine

    DATA   = "/opt/airflow/data/processed"
    MODELS = "/opt/airflow/data/models"
    DB_URL = os.getenv("DATABASE_URL",
             "postgresql://credit_risk:CreditRisk2026!@postgres/credit_risk")

    scorecard  = pd.read_csv(f"{DATA}/scorecard.csv")
    lgd_stage1 = joblib.load(f"{MODELS}/lgd_stage1.pkl")
    lgd_stage2 = joblib.load(f"{MODELS}/lgd_stage2.pkl")
    ead_model  = joblib.load(f"{MODELS}/ead_model.pkl")
    ead_scaler = joblib.load(f"{MODELS}/ead_scaler.pkl")
    with open(f"{DATA}/dummy_cols.json") as f:
        dummy_cols = json.load(f)

    test = pd.read_parquet(f"{DATA}/test_preprocessed.parquet")

    # Credit scores
    FACTOR = 20 / np.log(2)
    OFFSET = 600.0
    score_map = dict(zip(scorecard["Feature"], scorecard["Score"]))
    final_feats = list(scorecard["Feature"])
    scores = pd.Series(OFFSET, index=test.index)
    for feat in final_feats:
        if feat in test.columns:
            scores += test[feat].fillna(0).astype(float) * score_map.get(feat, 0)
    scores = scores.round().clip(300, 850).astype(int)

    # PD
    log_odds = (scores - OFFSET) / FACTOR
    p_good   = np.exp(log_odds) / (1 + np.exp(log_odds))
    pd_vals  = 1 - p_good

    # LGD & EAD
    feats   = [c for c in FEATURES if c in test.columns]
    X_risk  = test[feats].fillna(test[feats].median())
    recovery_prob = lgd_stage1.predict_proba(X_risk)[:, 1]
    recovery_amt  = lgd_stage2.predict(X_risk).clip(0, 1)
    lgd_vals      = (1 - recovery_prob * recovery_amt).clip(0, 1)
    X_scaled      = ead_scaler.transform(X_risk)
    ccf_vals      = ead_model.predict(X_scaled).clip(0, 1)
    ead_vals      = test["funded_amnt"].fillna(0) * ccf_vals

    el_df = pd.DataFrame({
        "loan_id":       test.index,
        "pd":            pd_vals.round(6),
        "lgd":           lgd_vals.round(6),
        "ead":           ead_vals.round(2),
        "expected_loss": (pd_vals * lgd_vals * ead_vals).round(2),
        "el_rate":       (pd_vals * lgd_vals).round(6),
        "risk_class":    pd.cut(scores,
                               bins=[300,460,500,540,580,620,660,700,740,780,851],
                               labels=['F','DD','CD','C','BC','B','BB','AB','A','AA'],
                               right=False).astype(str),
        "calc_date":     ctx["ds"],
        "model_run_id":  ctx["run_id"],
    })

    engine = create_engine(DB_URL)
    el_df.to_sql("expected_loss", schema="risk", con=engine,
                 if_exists="replace", index=False)
    el_df.to_parquet(f"{DATA}/expected_loss_test.parquet", index=False)

    print(f"Scored {len(el_df):,} loans | Mean EL={el_df['expected_loss'].mean():.2f}")


with DAG(
    dag_id="credit_risk_batch_scoring",
    description="Batch score OOT test → risk.expected_loss",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["credit_risk", "scoring"],
) as dag:

    score_task = PythonOperator(task_id="batch_score_loans", python_callable=batch_score)
