"""
DAG 04 — Train LGD (two-stage) and EAD models, register in MLflow
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {"owner": "credit_risk", "retries": 1, "retry_delay": timedelta(minutes=5)}

FEATURES = ["funded_amnt", "term_int", "int_rate", "dti", "fico_score",
            "annual_inc", "revol_util", "inq_last_6mths"]


def train_lgd_ead(**ctx):
    import joblib
    import numpy as np
    import pandas as pd
    import mlflow
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import roc_auc_score, r2_score

    DATA   = "/opt/airflow/data/processed"
    MODELS = "/opt/airflow/data/artifacts"

    train = pd.read_parquet(f"{DATA}/train_preprocessed.parquet")
    defaults = train[train["good_bad"] == 0].copy()
    feats = [c for c in FEATURES if c in defaults.columns]
    X_def = defaults[feats].fillna(defaults[feats].median())

    mlflow.set_experiment("credit_risk_lgd_ead")
    with mlflow.start_run(run_name=f"lgd_ead_{ctx['ds_nodash']}"):
        # Stage 1: Recovery probability > 0
        y_s1 = (defaults["recovery_rate"] > 0).astype(int)
        lgd1 = LogisticRegression(max_iter=500, C=1.0)
        lgd1.fit(X_def, y_s1)
        auc_s1 = roc_auc_score(y_s1, lgd1.predict_proba(X_def)[:, 1])

        # Stage 2: Recovery amount (given recovery > 0)
        mask  = defaults["recovery_rate"] > 0
        X_s2  = X_def[mask]
        y_s2  = defaults.loc[mask, "recovery_rate"].clip(0, 1)
        lgd2  = Ridge(alpha=1.0)
        lgd2.fit(X_s2, y_s2)
        r2_s2 = r2_score(y_s2, lgd2.predict(X_s2))

        # EAD model (CCF)
        y_ccf   = defaults["ccf"].clip(0, 1).fillna(0)
        scaler  = StandardScaler()
        X_scaled = scaler.fit_transform(X_def)
        ead_m   = Ridge(alpha=1.0)
        ead_m.fit(X_scaled, y_ccf)
        r2_ead  = r2_score(y_ccf, ead_m.predict(X_scaled))

        joblib.dump(lgd1,   f"{MODELS}/lgd_stage1.pkl")
        joblib.dump(lgd2,   f"{MODELS}/lgd_stage2.pkl")
        joblib.dump(ead_m,  f"{MODELS}/ead_model.pkl")
        joblib.dump(scaler, f"{MODELS}/ead_scaler.pkl")

        mlflow.log_metrics({"lgd_stage1_auc": auc_s1, "lgd_stage2_r2": r2_s2, "ead_r2": r2_ead})
        for name in ["lgd_stage1.pkl", "lgd_stage2.pkl", "ead_model.pkl", "ead_scaler.pkl"]:
            mlflow.log_artifact(f"{MODELS}/{name}")

        print(f"LGD Stage1 AUC={auc_s1:.4f} | Stage2 R²={r2_s2:.4f} | EAD R²={r2_ead:.4f}")


with DAG(
    dag_id="credit_risk_lgd_ead_training",
    description="Train LGD two-stage model and EAD model",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["credit_risk", "ml", "lgd", "ead"],
) as dag:

    train_task = PythonOperator(task_id="train_lgd_ead", python_callable=train_lgd_ead)
