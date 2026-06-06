"""
PSI Monitor — computes Population Stability Index for all model inputs and credit scores.
Compares reference population (train) vs monitoring population (OOT/new data).
"""
import os, sys, json, pickle
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

DATA_DIR = "data/processed"
MODEL_DIR = "data/models"
DB_URL   = os.getenv("DATABASE_URL",
           "postgresql://credit_risk:changeme_postgres@localhost:5432/credit_risk")

PSI_THRESHOLDS = {
    (0.00, 0.10): 'STABLE',
    (0.10, 0.25): 'MONITOR',
    (0.25, 9.99): 'ALERT',
}

def psi_status(val):
    for (lo, hi), status in PSI_THRESHOLDS.items():
        if lo <= val < hi:
            return status
    return 'ALERT'

def compute_psi_continuous(ref, actual, n_buckets=10):
    ref    = pd.Series(ref).dropna()
    actual = pd.Series(actual).dropna()
    bp     = np.percentile(ref, np.linspace(0, 100, n_buckets + 1))
    bp[0], bp[-1] = -np.inf, np.inf
    total  = 0.0
    for i in range(n_buckets):
        e = max(((ref >= bp[i]) & (ref < bp[i+1])).mean(), 1e-6)
        a = max(((actual >= bp[i]) & (actual < bp[i+1])).mean(), 1e-6)
        total += (a - e) * np.log(a / e)
    return total

def compute_psi_discrete(ref, actual):
    cats  = set(ref.dropna().unique()) | set(actual.dropna().unique())
    total = 0.0
    for cat in cats:
        e = max((ref == cat).mean(), 1e-6)
        a = max((actual == cat).mean(), 1e-6)
        total += (a - e) * np.log(a / e)
    return total

def run_psi_suite(reference_date="2007-2015", monitoring_date="2016-2018"):
    print(f"Running PSI: reference={reference_date} vs monitoring={monitoring_date}")

    ref  = pd.read_parquet(f"{DATA_DIR}/train_preprocessed.parquet")
    act  = pd.read_parquet(f"{DATA_DIR}/test_preprocessed.parquet")

    with open(f"{DATA_DIR}/dummy_cols.json") as f:
        dummy_cols = json.load(f)

    # ── Input variable PSI ────────────────────────────────────────────────
    results = []

    discrete_vars = ['grade','home_ownership','verification_status',
                     'purpose','initial_list_status','application_type']
    for var in discrete_vars:
        if var in ref.columns:
            psi_val = compute_psi_discrete(ref[var], act[var])
            results.append({'variable': var, 'type': 'Discrete',
                            'psi': psi_val, 'status': psi_status(psi_val)})

    continuous_vars = ['int_rate','annual_inc','dti','fico_score','revol_util',
                       'inq_last_6mths','mths_since_issue_d',
                       'mths_since_earliest_cr_line','bc_util','pct_tl_nvr_dlq']
    for var in continuous_vars:
        if var in ref.columns:
            psi_val = compute_psi_continuous(ref[var].values, act[var].values)
            results.append({'variable': var, 'type': 'Continuous',
                            'psi': psi_val, 'status': psi_status(psi_val)})

    # ── Score PSI ─────────────────────────────────────────────────────────
    try:
        with open(f"{MODEL_DIR}/pd_model.pkl", 'rb') as f:
            pd_model = pickle.load(f)
        avail     = [c for c in dummy_cols if c in ref.columns]
        ref_scores = pd_model.compute_scores(ref[avail].fillna(0))
        act_scores = pd_model.compute_scores(act[avail].fillna(0))
        score_psi  = compute_psi_continuous(ref_scores.values, act_scores.values)
        results.append({'variable': 'credit_score (★)', 'type': 'Score',
                        'psi': score_psi, 'status': psi_status(score_psi)})
    except Exception as e:
        print(f"  Score PSI skipped: {e}")

    psi_df = pd.DataFrame(results).sort_values('psi', ascending=False)
    psi_df['reference_date']  = reference_date
    psi_df['monitoring_date'] = monitoring_date

    # ── Print report ──────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  PSI MONITORING REPORT  |  Ref: {reference_date}  →  Mon: {monitoring_date}")
    print(f"{'='*65}")
    print(f"  {'Variable':<40} {'PSI':>8}  Status")
    print(f"  {'-'*60}")
    for _, row in psi_df.iterrows():
        flag = '🔴' if row['status']=='ALERT' else ('🟡' if row['status']=='MONITOR' else '🟢')
        print(f"  {flag} {row['variable']:<38} {row['psi']:>8.4f}  {row['status']}")

    # ── Save ──────────────────────────────────────────────────────────────
    psi_df.to_csv(f"{DATA_DIR}/psi_results.csv", index=False)
    print(f"\n  Saved: {DATA_DIR}/psi_results.csv ✓")

    try:
        engine = create_engine(DB_URL)
        psi_df.rename(columns={'variable':'variable_name','psi':'psi_value'},
                      inplace=True)
        psi_df.to_sql('population_stability', engine, schema='risk',
                      if_exists='append', index=False)
        print(f"  → Written to risk.population_stability ✓")
    except Exception as e:
        print(f"  DB write skipped: {e}")

    return psi_df

if __name__ == "__main__":
    run_psi_suite()
