"""
LGD & EAD Model Training Script
Run after train_pd.py.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import numpy as np
import pandas as pd
import mlflow

from ml.models.lgd_model import LGDModel, EADModel

DATA_DIR   = "data/processed"
MODEL_DIR  = "data/models"
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
os.makedirs(MODEL_DIR, exist_ok=True)

def main():
    train = pd.read_parquet(f"{DATA_DIR}/train_preprocessed.parquet")
    test  = pd.read_parquet(f"{DATA_DIR}/test_preprocessed.parquet")
    with open(f"{DATA_DIR}/dummy_cols.json") as f:
        dummy_cols = json.load(f)

    # ── Filter defaulted loans only ───────────────────────────────────────
    train_def = train[train['good_bad'] == 0].copy()
    test_def  = test[test['good_bad'] == 0].copy()
    print(f"Defaulted — Train: {len(train_def):,} | OOT: {len(test_def):,}")

    avail = [c for c in dummy_cols if c in train_def.columns]
    X_lgd_train = train_def[avail].fillna(0)
    X_lgd_test  = test_def[avail].fillna(0)
    rr_train    = train_def['recovery_rate'].fillna(0).clip(0, 1)
    rr_test     = test_def['recovery_rate'].fillna(0).clip(0, 1)
    ccf_train   = train_def['ccf'].fillna(train_def['ccf'].median()).clip(0, 1)
    ccf_test    = test_def['ccf'].fillna(test_def['ccf'].median()).clip(0, 1)

    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment("LGD_EAD_Models_2007_2018")

    with mlflow.start_run(run_name="lgd_ead_v1"):
        # ── LGD ──────────────────────────────────────────────────────────
        print("\nTraining LGD two-stage model...")
        lgd = LGDModel()
        lgd.fit(X_lgd_train, rr_train)
        lgd_metrics = lgd.evaluate(X_lgd_test, rr_test)

        print(f"  Stage 1 Gini: {lgd_metrics['stage1_gini']:.4f}")
        print(f"  LGD MAE:      {lgd_metrics['lgd_mae']*100:.2f}%")
        for k, v in lgd_metrics.items():
            mlflow.log_metric(f"lgd_{k}", v)

        lgd.save(f"{MODEL_DIR}/lgd_model.pkl")

        # ── EAD ──────────────────────────────────────────────────────────
        print("\nTraining EAD model...")
        ead = EADModel()
        ead.fit(X_lgd_train, ccf_train)
        ead_metrics = ead.evaluate(X_lgd_test, ccf_test)

        print(f"  EAD MAE: {ead_metrics['ead_mae']*100:.2f}%")
        print(f"  EAD R²:  {ead_metrics['ead_r2']:.4f}")
        for k, v in ead_metrics.items():
            mlflow.log_metric(f"ead_{k}", v)

        ead.save(f"{MODEL_DIR}/ead_model.pkl")

        mlflow.log_artifact(f"{MODEL_DIR}/lgd_model.pkl")
        mlflow.log_artifact(f"{MODEL_DIR}/ead_model.pkl")
        print("\n✓ LGD & EAD models saved")

if __name__ == "__main__":
    main()
