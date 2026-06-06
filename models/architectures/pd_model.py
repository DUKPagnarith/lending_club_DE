"""
PD Model — Logistic Regression with statsmodels for p-values.
Includes: feature selection, scorecard creation, risk class assignment.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import pickle


class PDModel:
    # Scorecard scaling params (industry standard)
    REF_SCORE = 600
    REF_ODDS  = 1
    PDO       = 20
    FACTOR    = PDO / np.log(2)       # ≈ 28.85
    OFFSET    = REF_SCORE             # at odds 1:1

    RISK_CLASSES = {
        'AA': (780, 851), 'A':  (740, 780), 'AB': (700, 740),
        'BB': (660, 700), 'B':  (620, 660), 'BC': (580, 620),
        'C':  (540, 580), 'CD': (500, 540), 'DD': (460, 500),
        'F':  (300, 460),
    }

    def __init__(self, p_threshold=0.05):
        self.p_threshold = p_threshold
        self.result      = None
        self.features    = []
        self.scorecard   = None
        self.intercept   = None

    def select_features(self, X_train, y_train):
        """Backward elimination — remove highest p-value until all < threshold."""
        features = list(X_train.columns)
        iteration = 0
        while True:
            Xc = sm.add_constant(X_train[features])
            res = sm.Logit(y_train, Xc).fit(method='bfgs', maxiter=500, disp=False)
            pvals = res.pvalues.drop('const')
            if pvals.max() < self.p_threshold:
                break
            worst = pvals.idxmax()
            features.remove(worst)
            iteration += 1
            if iteration % 5 == 0:
                print(f"  Iter {iteration}: removed '{worst}' | {len(features)} remaining")
        self.features = features
        print(f"Feature selection done: {len(features)} significant features")
        return features

    def fit(self, X_train, y_train):
        Xc = sm.add_constant(X_train[self.features])
        self.result    = sm.Logit(y_train, Xc).fit(method='bfgs', maxiter=500, disp=False)
        self.intercept = self.result.params['const']
        self._build_scorecard()
        return self

    def _build_scorecard(self):
        n = len(self.features)
        intercept_contrib = self.OFFSET + self.FACTOR * (self.intercept / n)
        rows = []
        for feat in self.features:
            coef  = self.result.params[feat]
            score = round(-coef * self.FACTOR + intercept_contrib / n)
            rows.append({'feature': feat, 'coefficient': coef,
                         'score': score, 'p_value': self.result.pvalues[feat]})
        self.scorecard = pd.DataFrame(rows).sort_values('score', ascending=False)

    def predict_proba(self, X):
        """Returns probability of DEFAULT (bad=0)."""
        Xc = sm.add_constant(X[self.features], has_constant='add')
        p_good = self.result.predict(Xc)
        return 1 - p_good   # PD

    def compute_scores(self, X):
        score_map = dict(zip(self.scorecard['feature'], self.scorecard['score']))
        scores = pd.Series(0.0, index=X.index)
        for feat, sc in score_map.items():
            if feat in X.columns:
                scores += X[feat] * sc
        scores += self.OFFSET
        return scores.clip(300, 850).round().astype(int)

    def assign_risk_class(self, scores):
        classes = pd.Series('F', index=scores.index)
        for cls, (lo, hi) in self.RISK_CLASSES.items():
            classes[scores.between(lo, hi - 1)] = cls
        return classes

    def score_to_pd(self, score):
        log_odds = (score - self.OFFSET) / self.FACTOR
        p_good   = np.exp(log_odds) / (1 + np.exp(log_odds))
        return 1 - p_good

    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path):
        with open(path, 'rb') as f:
            return pickle.load(f)
