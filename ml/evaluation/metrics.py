"""Evaluation metrics for all credit risk models."""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, brier_score_loss
from scipy.stats import ks_2samp


def evaluate_pd(y_true, y_pred_pd, label=''):
    auc   = roc_auc_score(y_true, 1 - y_pred_pd)
    gini  = 2 * auc - 1
    ks    = ks_2samp(y_pred_pd[y_true == 1], y_pred_pd[y_true == 0]).statistic
    brier = brier_score_loss(y_true, 1 - y_pred_pd)
    m = {'auc': auc, 'gini': gini, 'ks': ks, 'brier': brier}
    if label:
        print(f"\n{'='*45}")
        print(f"  {label} PD Model Performance")
        print(f"{'='*45}")
        print(f"  AUC:         {auc:.4f}  (>0.65 good)")
        print(f"  Gini:        {gini:.4f}  (>0.40 good on OOT)")
        print(f"  KS:          {ks:.4f}  (>0.25 good)")
        print(f"  Brier Score: {brier:.4f}  (<0.10 well-calibrated)")
    return m


def decile_analysis(y_true, pd_scores, label='Test'):
    """Verify monotonic bad rate by score decile."""
    df = pd.DataFrame({'good_bad': y_true, 'score': -pd_scores})
    df['decile'] = pd.qcut(df['score'], q=10, labels=range(1, 11))
    tbl = df.groupby('decile', observed=False).agg(
        n_obs=('good_bad', 'count'),
        n_bad=('good_bad', lambda x: (x == 0).sum()),
        bad_rate=('good_bad', lambda x: (x == 0).mean()),
    ).reset_index()
    tbl['cum_bad_pct'] = tbl['n_bad'].cumsum() / tbl['n_bad'].sum() * 100
    print(f"\nDecile Analysis ({label} Set — Decile 1 = Worst Scores):")
    print(tbl[['decile', 'n_obs', 'n_bad', 'bad_rate', 'cum_bad_pct']].to_string(index=False))
    top3_pct = tbl.loc[tbl['decile'].isin([1, 2, 3]), 'n_bad'].sum() / tbl['n_bad'].sum()
    print(f"\nTop 3 deciles capture {top3_pct:.1%} of all bads (target: >50%)")
    return tbl


def psi(expected, actual, n_buckets=10):
    """Population Stability Index."""
    bp = np.percentile(expected, np.linspace(0, 100, n_buckets + 1))
    bp[0], bp[-1] = -np.inf, np.inf
    psi_val = 0.0
    for i in range(n_buckets):
        e = max(((expected >= bp[i]) & (expected < bp[i + 1])).mean(), 1e-6)
        a = max(((actual   >= bp[i]) & (actual   < bp[i + 1])).mean(), 1e-6)
        psi_val += (a - e) * np.log(a / e)
    status = 'STABLE' if psi_val < 0.10 else ('MONITOR' if psi_val < 0.25 else 'ALERT')
    return psi_val, status
