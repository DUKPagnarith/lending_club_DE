"""
Expected Loss Calculator: EL = PD × LGD × EAD
Applies all three models to the full portfolio and writes to risk.expected_loss.
Run standalone or called by Airflow batch scoring DAG.
"""
import os, sys, json, pickle
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

DATA_DIR  = "data/processed"
MODEL_DIR = "data/models"
DB_URL    = os.getenv("DATABASE_URL",
            f"postgresql://credit_risk:changeme_postgres@localhost:5432/credit_risk")

US_BASE_RATE = 0.0215  # benchmark for ROI credit policy

RISK_CLASSES = {
    'AA':(780,851),'A':(740,780),'AB':(700,740),'BB':(660,700),
    'B':(620,660),'BC':(580,620),'C':(540,580),'CD':(500,540),
    'DD':(460,500),'F':(300,460),
}

def assign_risk_class(score):
    for cls,(lo,hi) in RISK_CLASSES.items():
        if lo <= score < hi:
            return cls
    return 'F'

def credit_decision(risk_class, annualized_roi):
    if risk_class in ('AA','A'):       return 'AUTO_APPROVE'
    elif risk_class == 'F':            return 'AUTO_REJECT'
    elif annualized_roi > US_BASE_RATE: return 'APPROVE'
    else:                              return 'REJECT'

def compute_portfolio_el(run_date: str = None):
    import datetime
    run_date = run_date or datetime.date.today().isoformat()

    print(f"Loading models for EL calculation ({run_date})...")
    with open(f"{MODEL_DIR}/pd_model.pkl",  'rb') as f: pd_model  = pickle.load(f)
    with open(f"{MODEL_DIR}/lgd_model.pkl", 'rb') as f: lgd_model = pickle.load(f)
    with open(f"{MODEL_DIR}/ead_model.pkl", 'rb') as f: ead_model = pickle.load(f)

    test = pd.read_parquet(f"{DATA_DIR}/test_preprocessed.parquet")
    with open(f"{DATA_DIR}/dummy_cols.json") as f:
        dummy_cols = json.load(f)

    avail  = [c for c in dummy_cols if c in test.columns]
    X_test = test[avail].fillna(0)

    # ── PD ────────────────────────────────────────────────────────────────
    pd_pred  = pd_model.predict_proba(X_test)
    scores   = pd_model.compute_scores(X_test)

    # ── LGD ───────────────────────────────────────────────────────────────
    lgd_pred = lgd_model.predict_lgd(X_test)

    # ── EAD ───────────────────────────────────────────────────────────────
    ead_pred = ead_model.predict_ead(X_test, test['funded_amnt'].values)

    # ── Expected Loss ─────────────────────────────────────────────────────
    el = pd_pred * lgd_pred * ead_pred

    # ── ROI ───────────────────────────────────────────────────────────────
    interest_income = test['int_rate'].values * test['funded_amnt'].values * (test['term_int'].values / 12)
    roi = (interest_income - el) / test['funded_amnt'].values / (test['term_int'].values / 12)

    # ── Assemble results ──────────────────────────────────────────────────
    el_df = pd.DataFrame({
        'loan_id':       test.index,
        'pd':            pd_pred,
        'lgd':           lgd_pred,
        'ead':           ead_pred,
        'expected_loss': el,
        'el_rate':       pd_pred * lgd_pred,
        'credit_score':  scores.values,
        'risk_class':    [assign_risk_class(s) for s in scores],
        'annualized_roi':roi,
        'calc_date':     run_date,
        'model_run_id':  f"manual_{run_date}",
    })
    el_df['decision'] = el_df.apply(
        lambda r: credit_decision(r['risk_class'], r['annualized_roi']), axis=1)

    # ── Portfolio summary ─────────────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"  PORTFOLIO EXPECTED LOSS REPORT ({run_date})")
    print(f"{'='*50}")
    print(f"  Total loans:          {len(el_df):,}")
    print(f"  Total EAD:            ${ead_pred.sum():,.0f}")
    print(f"  Total Expected Loss:  ${el.sum():,.0f}")
    print(f"  Portfolio EL Rate:    {el.sum()/ead_pred.sum()*100:.2f}%")
    print(f"  Mean PD:              {pd_pred.mean()*100:.2f}%")
    print(f"  Mean LGD:             {lgd_pred.mean()*100:.2f}%")
    print(f"  Approved loans:       {el_df['decision'].isin(['AUTO_APPROVE','APPROVE']).sum():,}")
    print(f"  Rejected loans:       {el_df['decision'].isin(['AUTO_REJECT','REJECT']).sum():,}")

    # ── Write to DB ───────────────────────────────────────────────────────
    try:
        engine = create_engine(DB_URL)
        el_df.to_sql('expected_loss', engine, schema='risk',
                     if_exists='append', index=False, method='multi', chunksize=10000)
        print(f"  → Written to risk.expected_loss ✓")
    except Exception as e:
        print(f"  DB write skipped (run locally): {e}")

    el_df.to_parquet(f"{DATA_DIR}/expected_loss_results.parquet", index=False)
    print(f"  → Saved: {DATA_DIR}/expected_loss_results.parquet ✓")
    return el_df

if __name__ == "__main__":
    compute_portfolio_el()
