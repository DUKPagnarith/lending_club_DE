"""
WoE encoder — fitted on training set, applied to both train and OOT.
Matches the methodology from L01 notebook.
"""
import numpy as np
import pandas as pd
import json


class WoEEncoder:
    """Compute WoE/IV for discrete and continuous variables."""

    def __init__(self, target_col='good_bad'):
        self.target_col = target_col
        self.woe_maps = {}       # {col: {category: woe}}
        self.iv_scores = {}      # {col: total_iv}
        self.bin_edges = {}      # {col: bin_edges} for continuous vars

    # ── Discrete WoE ─────────────────────────────────────────────────────
    def fit_discrete(self, df, col):
        d = df[[col, self.target_col]].copy()
        d[col] = d[col].fillna('Missing').astype(str)
        agg = d.groupby(col)[self.target_col].agg(['count','sum']).reset_index()
        agg.columns = [col, 'n_obs', 'n_good']
        agg['n_bad']       = agg['n_obs'] - agg['n_good']
        agg['prop_n_good'] = agg['n_good'] / agg['n_good'].sum()
        agg['prop_n_bad']  = agg['n_bad']  / agg['n_bad'].sum()
        agg['woe']         = np.log(agg['prop_n_good'].clip(1e-6) / agg['prop_n_bad'].clip(1e-6))
        agg['iv']          = (agg['prop_n_good'] - agg['prop_n_bad']) * agg['woe']
        self.woe_maps[col]  = dict(zip(agg[col], agg['woe']))
        self.iv_scores[col] = agg['iv'].sum()
        return agg

    # ── Continuous WoE (fine-class with sentinel for missing=-1) ─────────
    def fit_continuous(self, df, col, n_bins=20):
        d = df[[col, self.target_col]].copy()
        missing = d[d[col] == -1]
        actual  = d[d[col] != -1].dropna()
        try:
            actual['bin'], edges = pd.qcut(actual[col], q=n_bins,
                                           duplicates='drop', retbins=True)
        except Exception:
            actual['bin'], edges = pd.cut(actual[col], bins=n_bins, retbins=True)
        self.bin_edges[col] = edges

        rows = []
        if len(missing) > 0:
            ng = missing[self.target_col].sum()
            nb = len(missing) - ng
            rows.append({'bin': 'Missing(-1)', 'n_obs': len(missing),
                         'n_good': ng, 'n_bad': nb})
        for bin_label, grp in actual.groupby('bin', observed=False):
            ng = grp[self.target_col].sum()
            nb = len(grp) - ng
            rows.append({'bin': str(bin_label), 'n_obs': len(grp),
                         'n_good': ng, 'n_bad': nb})

        agg = pd.DataFrame(rows)
        total_good = agg['n_good'].sum()
        total_bad  = agg['n_bad'].sum()
        agg['prop_n_good'] = agg['n_good'] / total_good
        agg['prop_n_bad']  = agg['n_bad']  / total_bad
        agg['woe']         = np.log(agg['prop_n_good'].clip(1e-6) / agg['prop_n_bad'].clip(1e-6))
        agg['iv']          = (agg['prop_n_good'] - agg['prop_n_bad']) * agg['woe']
        self.iv_scores[col] = agg['iv'].sum()
        return agg

    def iv_summary(self):
        df = pd.DataFrame.from_dict(self.iv_scores, orient='index', columns=['IV'])
        df['Strength'] = df['IV'].apply(lambda x:
            'Useless' if x < 0.02 else 'Weak' if x < 0.10 else
            'Medium'  if x < 0.30 else 'Strong' if x < 0.50 else 'Check!')
        return df.sort_values('IV', ascending=False)

    def save(self, path):
        with open(path, 'w') as f:
            json.dump({'woe_maps': self.woe_maps,
                       'iv_scores': self.iv_scores}, f, indent=2)

    @classmethod
    def load(cls, path):
        obj = cls()
        with open(path) as f:
            d = json.load(f)
        obj.woe_maps  = d['woe_maps']
        obj.iv_scores = d['iv_scores']
        return obj
