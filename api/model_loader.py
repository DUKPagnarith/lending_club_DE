"""
Loads scorecard, LGD, EAD models from disk at startup.
Models are stored in /app/data/models/ (mounted from host).
"""
import os
import json
import joblib
import pandas as pd

_models: dict = {"loaded": False}


def load_models():
    base = os.getenv("MODEL_PATH", "/app/data")
    proc = f"{base}/processed"
    mods = f"{base}/models"

    try:
        scorecard   = pd.read_csv(f"{proc}/scorecard.csv")
        lgd_stage1  = joblib.load(f"{mods}/lgd_stage1.pkl")
        lgd_stage2  = joblib.load(f"{mods}/lgd_stage2.pkl")
        ead_model   = joblib.load(f"{mods}/ead_model.pkl")
        ead_scaler  = joblib.load(f"{mods}/ead_scaler.pkl")

        with open(f"{proc}/dummy_cols.json") as f:
            dummy_cols = json.load(f)

        final_feats = list(scorecard["Feature"])
        n_features  = len(final_feats)

        # Intercept is stored in scorecard metadata row if present, else 0
        intercept_row = scorecard[scorecard["Feature"] == "const"]
        intercept = float(intercept_row["Coefficient"].iloc[0]) if len(intercept_row) else 0.0
        scorecard = scorecard[scorecard["Feature"] != "const"].reset_index(drop=True)

        _models.update({
            "loaded": True,
            "scorecard": scorecard,
            "lgd_stage1": lgd_stage1,
            "lgd_stage2": lgd_stage2,
            "ead_model": ead_model,
            "ead_scaler": ead_scaler,
            "dummy_cols": dummy_cols,
            "final_features": final_feats,
            "n_features": n_features,
            "intercept": intercept,
            "version": "1.0.0",
        })
        print(f"Models loaded: scorecard={len(scorecard)} features, version=1.0.0")
    except Exception as e:
        print(f"WARNING: Could not load models: {e}")
        _models["loaded"] = False


def get_models() -> dict:
    return _models
