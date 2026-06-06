"""
LGD Two-Stage Model:
  Stage 1: Logistic Regression — P(Recovery Rate > 0)
  Stage 2: Linear Regression  — E[Recovery Rate | RR > 0]
  Combined: LGD = 1 - (Stage1 × Stage2)
"""
import numpy as np
import pickle
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import roc_auc_score, mean_absolute_error, r2_score


class LGDModel:
    def __init__(self, C=1.0):
        self.stage1   = LogisticRegression(C=C, max_iter=1000, solver='lbfgs')
        self.stage2   = LinearRegression()
        self.features = None

    def fit(self, X, recovery_rate):
        self.features = list(X.columns)
        y1 = (recovery_rate > 0).astype(int)
        self.stage1.fit(X, y1)

        mask = recovery_rate > 0
        self.stage2.fit(X[mask], recovery_rate[mask])
        return self

    def predict_recovery_rate(self, X):
        p_rr_gt0  = self.stage1.predict_proba(X[self.features])[:, 1]
        rr_given  = self.stage2.predict(X[self.features]).clip(0, 1)
        return p_rr_gt0 * rr_given

    def predict_lgd(self, X):
        return 1 - self.predict_recovery_rate(X)

    def evaluate(self, X, recovery_rate):
        y1       = (recovery_rate > 0).astype(int)
        s1_prob  = self.stage1.predict_proba(X[self.features])[:, 1]
        rr_pred  = self.predict_recovery_rate(X)
        lgd_pred = 1 - rr_pred
        lgd_act  = 1 - recovery_rate
        return {
            'stage1_auc':  roc_auc_score(y1, s1_prob),
            'stage1_gini': 2 * roc_auc_score(y1, s1_prob) - 1,
            'lgd_mae':     mean_absolute_error(lgd_act, lgd_pred),
        }

    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path):
        with open(path, 'rb') as f:
            return pickle.load(f)


class EADModel:
    """Linear regression on Credit Conversion Factor (CCF)."""
    def __init__(self):
        self.model    = LinearRegression()
        self.features = None

    def fit(self, X, ccf):
        self.features = list(X.columns)
        self.model.fit(X, ccf)
        return self

    def predict_ccf(self, X):
        return self.model.predict(X[self.features]).clip(0, 1)

    def predict_ead(self, X, funded_amnt):
        return self.predict_ccf(X) * funded_amnt

    def evaluate(self, X, ccf_actual):
        pred = self.predict_ccf(X)
        return {
            'ead_mae': mean_absolute_error(ccf_actual, pred),
            'ead_r2':  r2_score(ccf_actual, pred),
        }

    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path):
        with open(path, 'rb') as f:
            return pickle.load(f)
