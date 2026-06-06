"""
DAG 03 — Train PD model from processed parquet, register in MLflow
Runs: manually triggered after cleaning
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {"owner": "credit_risk", "retries": 1, "retry_delay": timedelta(minutes=5)}


def train_pd(**ctx):
    import sys, json
    import numpy as np
    import pandas as pd
    import statsmodels.api as sm
    import mlflow
    import mlflow.sklearn
    from sklearn.metrics import roc_auc_score
    from scipy.stats import ks_2samp

    DATA = "/opt/airflow/data/processed"
    MODELS = "/opt/airflow/data/models"

    train = pd.read_parquet(f"{DATA}/train_preprocessed.parquet")
    test  = pd.read_parquet(f"{DATA}/test_preprocessed.parquet")
    with open(f"{DATA}/dummy_cols.json") as f:
        DUMMY_COLS = json.load(f)

    X_train = train[DUMMY_COLS].astype(float)
    y_train = train["good_bad"].astype(float)

    mlflow.set_experiment("credit_risk_pd")
    with mlflow.start_run(run_name=f"pd_model_{ctx['ds_nodash']}"):
        features = DUMMY_COLS.copy()
        while True:
            X_c = sm.add_constant(train[features].astype(float), has_constant="add")
            res = sm.Logit(y_train, X_c).fit(method="newton", maxiter=100, disp=False)
            pvals = res.pvalues.drop("const").fillna(1.0)
            if pvals.max() < 0.05:
                break
            features.remove(pvals.idxmax())

        X_final = sm.add_constant(train[features].astype(float), has_constant="add")
        final   = sm.Logit(y_train, X_final).fit(method="newton", maxiter=100, disp=False)

        X_test  = sm.add_constant(test[features].astype(float), has_constant="add")
        y_pred  = 1 - final.predict(X_test)
        y_true  = test["good_bad"].values
        auc  = roc_auc_score(y_true, 1 - y_pred)
        gini = 2 * auc - 1
        ks   = ks_2samp(y_pred[y_true==1], y_pred[y_true==0]).statistic

        mlflow.log_metrics({"auc": auc, "gini": gini, "ks": ks, "n_features": len(features)})
        mlflow.log_param("optimizer", "newton")

        scorecard = pd.DataFrame({
            "Feature": features,
            "Coefficient": [final.params[f] for f in features],
            "Score": [round(-final.params[f] * (20 / np.log(2))) for f in features],
            "PValue": [final.pvalues[f] for f in features],
        })
        scorecard.to_csv(f"{DATA}/scorecard.csv", index=False)
        mlflow.log_artifact(f"{DATA}/scorecard.csv")

        print(f"PD model: {len(features)} features | AUC={auc:.4f} | Gini={gini:.4f} | KS={ks:.4f}")


with DAG(
    dag_id="credit_risk_pd_training",
    description="Train logistic PD model, register metrics in MLflow",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["credit_risk", "ml", "pd"],
) as dag:

    train_task = PythonOperator(task_id="train_pd_model", python_callable=train_pd)
