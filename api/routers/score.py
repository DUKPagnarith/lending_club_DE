import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from schemas.score import ScoreRequest, ScoreResponse
from model_loader import get_models

router = APIRouter()

RISK_CLASS_BINS   = [300, 460, 500, 540, 580, 620, 660, 700, 740, 780, 851]
RISK_CLASS_LABELS = ['F', 'DD', 'CD', 'C', 'BC', 'B', 'BB', 'AB', 'A', 'AA']
US_BASE_RATE      = 0.0215
FACTOR = 20 / np.log(2)
OFFSET = 600.0


def _build_dummies(req: ScoreRequest) -> pd.DataFrame:
    r = req
    row = {}

    for g in ['A', 'B', 'C', 'D', 'E']:
        row[f'grade_{g}'] = int(r.grade.upper() == g)
    row['home_ownership_OWN']      = int(r.home_ownership.upper() == 'OWN')
    row['home_ownership_MORTGAGE'] = int(r.home_ownership.upper() == 'MORTGAGE')
    row['verif_Verified']        = int(r.verification_status == 'Verified')
    row['verif_Source_Verified'] = int(r.verification_status == 'Source Verified')

    purposes = ['debt_consolidation', 'credit_card', 'home_improvement', 'major_purchase']
    for p in purposes:
        row[f'purpose_{p}'] = int(r.purpose == p)
    row['purpose_other'] = int(r.purpose not in purposes + ['small_business'])
    row['initial_list_w'] = int(r.initial_list_status == 'w')

    ir = r.int_rate
    row['int_rate_lt_0088'] = int(ir <= 0.088)
    row['int_rate_088_117'] = int(0.088 < ir <= 0.117)
    row['int_rate_117_148'] = int(0.117 < ir <= 0.148)
    row['int_rate_148_176'] = int(0.148 < ir <= 0.176)
    row['int_rate_176_200'] = int(0.176 < ir <= 0.200)

    inc = min(r.annual_inc, 250000)
    row['annual_inc_25k_50k']  = int(25000 < inc <= 50000)
    row['annual_inc_50k_75k']  = int(50000 < inc <= 75000)
    row['annual_inc_75k_125k'] = int(75000 < inc <= 125000)
    row['annual_inc_gt125k']   = int(inc > 125000)

    f = r.fico_score
    row['fico_600_640'] = int(600 <= f < 640)
    row['fico_640_680'] = int(640 <= f < 680)
    row['fico_680_720'] = int(680 <= f < 720)
    row['fico_720_760'] = int(720 <= f < 760)
    row['fico_gt760']   = int(f >= 760)

    d = r.dti
    row['dti_lt_10']  = int(d <= 10)
    row['dti_10_20']  = int(10 < d <= 20)
    row['dti_20_28']  = int(20 < d <= 28)
    row['dti_28_35']  = int(28 < d <= 35)

    row['term_36'] = int(r.term_int == 36)

    m = r.mths_since_issue_d or 60
    row['mths_issue_lt38']   = int(m <= 38)
    row['mths_issue_38_64']  = int(38 < m <= 64)
    row['mths_issue_64_95']  = int(64 < m <= 95)
    row['mths_issue_95_118'] = int(95 < m <= 118)

    cr = r.mths_since_earliest_cr_line or 120
    row['cr_line_lt80']    = int(cr <= 80)
    row['cr_line_80_140']  = int(80 < cr <= 140)
    row['cr_line_140_200'] = int(140 < cr <= 200)
    row['cr_line_gt200']   = int(cr > 200)

    delinq = r.mths_since_last_delinq if r.mths_since_last_delinq is not None else -1
    row['delinq_never']  = int(delinq == -1)
    row['delinq_lt24']   = int(0 <= delinq < 24)
    row['delinq_24_48']  = int(24 <= delinq < 48)
    row['delinq_48_72']  = int(48 <= delinq < 72)

    ru = r.revol_util
    row['revol_util_lt020'] = int(ru < 0.20)
    row['revol_util_20_40'] = int(0.20 <= ru < 0.40)
    row['revol_util_40_60'] = int(0.40 <= ru < 0.60)
    row['revol_util_60_80'] = int(0.60 <= ru < 0.80)

    inq = r.inq_last_6mths
    row['inq_0']   = int(inq == 0)
    row['inq_1']   = int(inq == 1)
    row['inq_2_3'] = int(2 <= inq <= 3)

    row['pct_dlq_gt95'] = 0
    row['pct_dlq_85_95'] = 0
    row['pct_dlq_70_85'] = 0

    return pd.DataFrame([row])


@router.post("/score", response_model=ScoreResponse)
def score_loan(req: ScoreRequest):
    models = get_models()
    if not models["loaded"]:
        raise HTTPException(status_code=503, detail="Models not loaded yet")

    scorecard   = models["scorecard"]
    lgd_stage1  = models["lgd_stage1"]
    lgd_stage2  = models["lgd_stage2"]
    ead_model   = models["ead_model"]
    ead_scaler  = models["ead_scaler"]
    final_feats = models["final_features"]
    n_features  = models["n_features"]
    intercept   = models["intercept"]

    X = _build_dummies(req)

    # ── Credit score from scorecard ──────────────────────────────────────
    score_map = dict(zip(scorecard["Feature"], scorecard["Score"]))
    credit_score = OFFSET + FACTOR * (intercept / n_features)
    for feat in final_feats:
        if feat in X.columns and feat in score_map:
            credit_score += float(X[feat].iloc[0]) * score_map[feat]
    credit_score = int(round(credit_score))
    credit_score = max(300, min(850, credit_score))

    # ── PD from score ────────────────────────────────────────────────────
    log_odds = (credit_score - OFFSET) / FACTOR
    p_good   = np.exp(log_odds) / (1 + np.exp(log_odds))
    pd_prob  = float(1 - p_good)

    # ── LGD (two-stage) ──────────────────────────────────────────────────
    lgd_features = ['funded_amnt', 'term_int', 'int_rate', 'dti', 'fico_score',
                    'annual_inc', 'revol_util', 'inq_last_6mths']
    lgd_X = pd.DataFrame([{
        'funded_amnt': req.funded_amnt, 'term_int': req.term_int,
        'int_rate': req.int_rate, 'dti': req.dti, 'fico_score': req.fico_score,
        'annual_inc': req.annual_inc, 'revol_util': req.revol_util,
        'inq_last_6mths': req.inq_last_6mths,
    }])
    available = [c for c in lgd_features if c in lgd_X.columns]
    lgd_X = lgd_X[available].fillna(0)

    try:
        recovery_prob = float(lgd_stage1.predict_proba(lgd_X)[0][1])
        recovery_amt  = float(max(0, lgd_stage2.predict(lgd_X)[0]))
        lgd = float(1 - recovery_prob * recovery_amt)
        lgd = max(0.0, min(1.0, lgd))
    except Exception:
        lgd = 0.45  # fallback industry average

    # ── EAD ─────────────────────────────────────────────────────────────
    try:
        ead_X_scaled = ead_scaler.transform(lgd_X)
        ccf = float(max(0, min(1, ead_model.predict(ead_X_scaled)[0])))
        ead = float(req.funded_amnt * ccf)
    except Exception:
        ead = float(req.funded_amnt)

    # ── Expected Loss ────────────────────────────────────────────────────
    el = pd_prob * lgd * ead

    # ── Risk class ───────────────────────────────────────────────────────
    risk_class = RISK_CLASS_LABELS[-1]
    for i, (lo, hi) in enumerate(zip(RISK_CLASS_BINS[:-1], RISK_CLASS_BINS[1:])):
        if lo <= credit_score < hi:
            risk_class = RISK_CLASS_LABELS[i]
            break

    # ── ROI & Decision ───────────────────────────────────────────────────
    interest_income = req.funded_amnt * req.int_rate * (req.term_int / 12)
    net_return      = interest_income - el
    annualized_roi  = float((net_return / req.funded_amnt) / (req.term_int / 12))

    if risk_class in ('AA', 'A'):
        decision = 'AUTO_APPROVE'
    elif risk_class == 'F':
        decision = 'AUTO_REJECT'
    elif annualized_roi > US_BASE_RATE:
        decision = 'APPROVE'
    else:
        decision = 'REJECT'

    return ScoreResponse(
        pd=round(pd_prob, 6),
        lgd=round(lgd, 6),
        ead=round(ead, 2),
        expected_loss=round(el, 2),
        credit_score=credit_score,
        risk_class=risk_class,
        decision=decision,
        annualized_roi=round(annualized_roi, 6),
        model_version=models["version"],
    )
