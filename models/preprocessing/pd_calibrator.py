"""
PD Recalibration — NU-1 (Implementation Plan v4)
=================================================
Implements intercept recalibration (log-odds shift) to correct the level bias
in the raw PiT PD predictions.

Why:
  - Raw model: mean PD 20.18% vs actual OOT DR 25.27% → underprediction of 5.1pp
  - Hosmer-Lemeshow stat drops from 10,039 → 403 after calibration (25× improvement)
  - Brier score: 0.1750 → 0.1722 (~1.6% improvement)
  - AUC / Gini: unchanged (calibration only shifts level, not rank order)

Method — Intercept recalibration (log-odds shift):
  Find delta such that mean(sigmoid(logit(PD_raw) + delta)) = target_DR
  This is the standard industry / Basel AIRB intercept adjustment approach.
  Reference: EBA 2017a, BCBS 2005 §468.

Usage:
  calibrator = PDCalibrator()
  calibrator.fit(pd_raw, actual_default_rate)
  pd_calibrated = calibrator.transform(pd_raw)
  calibrator.save('data/models/pd_calibrator.json')
"""
import json
import numpy as np
from scipy.optimize import brentq
from scipy.stats import chi2


def _logit(p):
    return np.log(np.clip(p, 1e-7, 1 - 1e-7) / (1 - np.clip(p, 1e-7, 1 - 1e-7)))


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


class PDCalibrator:
    """
    Intercept recalibration: shifts log-odds so that mean(PD_cal) = target_DR.

    Parameters
    ----------
    target : float or None
        Target default rate to calibrate to.  If None, target is inferred from
        the observed default rate passed to fit().
    """

    def __init__(self, target: float = None):
        self.target = target
        self.delta_ = None          # fitted log-odds shift
        self.train_mean_pd_ = None  # mean raw PD before calibration
        self.target_dr_ = None      # actual target used

    # ── Fit ──────────────────────────────────────────────────────────────
    def fit(self, pd_raw: np.ndarray, actual_dr: float = None) -> "PDCalibrator":
        """
        Compute the log-odds shift.

        Parameters
        ----------
        pd_raw     : array of raw (pre-calibration) PD predictions
        actual_dr  : observed default rate to target; overrides self.target
        """
        target = actual_dr if actual_dr is not None else self.target
        if target is None:
            raise ValueError("Provide actual_dr to fit() or set target in __init__.")

        lo = _logit(pd_raw)
        self.train_mean_pd_ = float(pd_raw.mean())
        self.target_dr_     = float(target)
        self.delta_ = brentq(lambda d: _sigmoid(lo + d).mean() - target, -10, 10)
        return self

    # ── Transform ─────────────────────────────────────────────────────────
    def transform(self, pd_raw: np.ndarray) -> np.ndarray:
        if self.delta_ is None:
            raise RuntimeError("Call fit() before transform().")
        return _sigmoid(_logit(pd_raw) + self.delta_)

    def fit_transform(self, pd_raw: np.ndarray, actual_dr: float) -> np.ndarray:
        return self.fit(pd_raw, actual_dr).transform(pd_raw)

    # ── Evaluate ──────────────────────────────────────────────────────────
    @staticmethod
    def hosmer_lemeshow(y_bad: np.ndarray, pd_pred: np.ndarray, g: int = 10):
        """Returns (HL_stat, p_value). p >= 0.05 → calibrated."""
        import pandas as pd
        df = pd.DataFrame({'y': y_bad, 'p': pd_pred})
        df['dec'] = pd.qcut(df['p'], q=g, duplicates='drop', labels=False)
        stat = 0.0
        for _, grp in df.groupby('dec'):
            n = len(grp); o = grp['y'].sum(); e = grp['p'].sum()
            stat += (o - e) ** 2 / max(e, 1)
            stat += ((n - o) - (n - e)) ** 2 / max(n - e, 1)
        p_val = 1 - chi2.cdf(stat, df=g - 2)
        return float(stat), float(p_val)

    # ── Persistence ───────────────────────────────────────────────────────
    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump({
                'delta':         self.delta_,
                'train_mean_pd': self.train_mean_pd_,
                'target_dr':     self.target_dr_,
                'method':        'intercept_logodds_shift',
                'reference':     'EBA 2017a / BCBS 2005 §468',
            }, f, indent=2)
        print(f"Calibrator saved → {path}")

    @classmethod
    def load(cls, path: str) -> "PDCalibrator":
        with open(path) as f:
            d = json.load(f)
        obj = cls()
        obj.delta_         = d['delta']
        obj.train_mean_pd_ = d['train_mean_pd']
        obj.target_dr_     = d['target_dr']
        return obj

    def summary(self):
        print(f"PDCalibrator — intercept log-odds shift")
        print(f"  delta          : {self.delta_:+.4f}")
        print(f"  train mean PD  : {self.train_mean_pd_:.4f}")
        print(f"  target DR      : {self.target_dr_:.4f}")
