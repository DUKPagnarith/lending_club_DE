"""
PD Model Training Script
Loads preprocessed parquet → trains PD model → logs to MLflow → saves artifacts.
Run: python ml/training/train_pd.py
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn

from ml.models.pd_model import PDModel
from ml.evaluation.metrics import evaluate_pd, decile_analysis

# ── Config ───────────────────────────────────────────────────────────────
DATA_DIR    = "data/processed"
MODEL_DIR   = "data/models"
MLFLOW_URI  = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
os.makedirs(MODEL_DIR, exist_ok=True)

def load_data():
    print("Loading preprocessed data...")
    train = pd.read_parquet(f"{DATA_DIR}/train_preprocessed.parquet")
    test  = pd.read_parquet(f"{DATA_DIR}/test_preprocessed.parquet")
    with open(f"{DATA_DIR}/dummy_cols.json") as f:
        dummy_cols = json.load(f)
    print(f"Train: {len(train):,} | OOT: {len(test):,} | Features: {len(dummy_cols)}")
    return train, test, dummy_cols

def main():
    train, test, dummy_cols = load_data()

    X_train = train[dummy_cols].fillna(0)
    y_train = train['good_bad']
    X_test  = test[dummy_cols].fillna(0)
    y_test  = test['good_bad']

    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment("PD_Model_2007_2018")

    with mlflow.start_run(run_name="pd_logistic_v1") as run:
        # ── Feature selection ─────────────────────────────────────────────
        print("\nRunning backward feature selection (p < 0.05)...")
        model = PDModel(p_threshold=0.05)
        model.select_features(X_train, y_train)

        # ── Fit final model ───────────────────────────────────────────────
        print("Fitting final model...")
        model.fit(X_train, y_train)
        mlflow.log_param("n_features_total",   len(dummy_cols))
        mlflow.log_param("n_features_selected", len(model.features))
        mlflow.log_param("p_threshold", 0.05)
        mlflow.log_param("train_years", "2007-2015")
        mlflow.log_param("oot_years",   "2016-2018")

        # ── Evaluate ──────────────────────────────────────────────────────
        pd_train = model.predict_proba(X_train)
        pd_test  = model.predict_proba(X_test)

        train_m = evaluate_pd(y_train.values, pd_train, label="Train")
        test_m  = evaluate_pd(y_test.values,  pd_test,  label="OOT Test")

        for k, v in train_m.items():
            mlflow.log_metric(f"train_{k}", v)
        for k, v in test_m.items():
            mlflow.log_metric(f"test_{k}", v)

        # ── Decile analysis ───────────────────────────────────────────────
        decile_analysis(y_test.values, pd_test, label="OOT")

        # ── Scorecard ─────────────────────────────────────────────────────
        model.scorecard.to_csv(f"{DATA_DIR}/scorecard.csv", index=False)
        mlflow.log_artifact(f"{DATA_DIR}/scorecard.csv")
        print(f"\nScorecard saved ({len(model.scorecard)} features)")

        # ── Credit scores ─────────────────────────────────────────────────
        test_scores = model.compute_scores(X_test)
        print(f"Test score range: {test_scores.min()}–{test_scores.max()} | mean: {test_scores.mean():.0f}")

        # ── Save model ────────────────────────────────────────────────────
        model.save(f"{MODEL_DIR}/pd_model.pkl")
        mlflow.log_artifact(f"{MODEL_DIR}/pd_model.pkl")
        mlflow.register_model(f"runs:/{run.info.run_id}/pd_model",
                              "CreditRisk_PD_Model")

        print(f"\n✓ PD model training complete")
        print(f"  MLflow run: {run.info.run_id}")
        print(f"  Gini (OOT): {test_m['gini']:.4f}")
        print(f"  Model saved: {MODEL_DIR}/pd_model.pkl")

if __name__ == "__main__":
    main()
