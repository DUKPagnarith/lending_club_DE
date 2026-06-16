"""
Credit Risk Modelling Dashboard
================================
Lending Club Credit Risk System — Interactive Dashboard
Run: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import pickle
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─── Path setup ───────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
DATA  = BASE / "data"
REPORTS = DATA / "reports"
MODELS  = DATA / "models"
PROCESSED = DATA / "processed"

st.set_page_config(
    page_title="Credit Risk Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Colour palette ────────────────────────────────────────────────────────────
ITC_BLUE  = "#003366"
ITC_GOLD  = "#CC9900"
RED       = "#B41E1E"
GREEN     = "#1E8240"
AMBER     = "#CC7700"

# ─── Shared CSS ───────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    .main-header {{font-size:2rem;font-weight:700;color:{ITC_BLUE};margin-bottom:0.2rem}}
    .sub-header  {{font-size:1rem;color:#555;margin-bottom:1.5rem}}
    .metric-card {{background:{ITC_BLUE};color:white;padding:1rem 1.2rem;border-radius:8px;text-align:center}}
    .metric-val  {{font-size:1.8rem;font-weight:700}}
    .metric-lbl  {{font-size:0.8rem;opacity:0.85}}
    .green-badge {{background:#e6f4ea;color:{GREEN};padding:2px 10px;border-radius:12px;font-weight:600}}
    .red-badge   {{background:#fde8e8;color:{RED};padding:2px 10px;border-radius:12px;font-weight:600}}
    .amber-badge {{background:#fff3e0;color:{AMBER};padding:2px 10px;border-radius:12px;font-weight:600}}
    .section-divider {{border-top:2px solid {ITC_BLUE};margin:1.5rem 0 1rem 0}}
    .stAlert {{border-radius:8px}}
</style>""", unsafe_allow_html=True)

# ─── Data loading (cached) ─────────────────────────────────────────────────────
@st.cache_data
def load_scorecard():
    return pd.read_csv(PROCESSED / "scorecard.csv")

@st.cache_data
def load_psi():
    return pd.read_csv(PROCESSED / "psi_results.csv")

@st.cache_data
def load_calibrator():
    with open(MODELS / "pd_calibrator.json") as f:
        return json.load(f)

@st.cache_data
def load_ifrs9_config():
    with open(MODELS / "ifrs9_scenarios.json") as f:
        return json.load(f)

@st.cache_data
def load_dummy_cols():
    with open(PROCESSED / "dummy_cols.json") as f:
        return json.load(f)

@st.cache_data
def load_test_sample(n=5000):
    test = pd.read_parquet(PROCESSED / "test_preprocessed.parquet")
    pd_cal = np.load(PROCESSED / "pd_pred_test_pit_calibrated.npy")
    test = test.copy()
    test["pd_calibrated"] = pd_cal
    return test.sample(n=n, random_state=42).reset_index(drop=True)

@st.cache_data
def load_el_summary():
    """Load a summary of the EL output (fast stats only)."""
    pd_cal = np.load(PROCESSED / "pd_pred_test_pit_calibrated.npy")
    test   = pd.read_parquet(PROCESSED / "test_preprocessed.parquet")
    sc     = pd.read_csv(PROCESSED / "scorecard.csv")
    factor = 20 / np.log(2)
    coeff  = {r["Feature"]: -r["Score"] / factor for _, r in sc.iterrows()}
    feats  = [f for f in coeff if f in test.columns]
    fc     = test[feats].fillna(0).dot(pd.Series({f: coeff[f] for f in feats}))
    intercept = -1.259202
    scores = (600 + factor * (intercept + fc.values)).clip(300, 850)
    return pd_cal, scores, test["funded_amnt"].values

@st.cache_resource
def load_lgd_models():
    with open(MODELS / "lgd_stage1.pkl", "rb") as f: s1 = pickle.load(f)
    with open(MODELS / "lgd_stage2.pkl", "rb") as f: s2 = pickle.load(f)
    return s1, s2

# ─── Scoring helpers ───────────────────────────────────────────────────────────
DELTA     = 0.320382
FACTOR    = 20 / np.log(2)
INTERCEPT = -1.259202

RISK_BANDS = [
    ("AA", 740, 850, GREEN),  ("A",  720, 739, GREEN),
    ("AB", 700, 719, "#2e7d32"), ("BB", 680, 699, "#558b2f"),
    ("B",  660, 679, "#f9a825"), ("BC", 640, 659, AMBER),
    ("C",  620, 639, "#e65100"), ("CD", 600, 619, "#bf360c"),
    ("DD", 580, 599, RED),   ("F",  300, 579, "#7b0000"),
]

def get_risk_class(score: float) -> tuple[str, str]:
    for name, lo, hi, col in RISK_BANDS:
        if lo <= score <= hi:
            return name, col
    return "F", "#7b0000"

def compute_score_pd(dummies: dict, funded_amnt: float = 10000) -> dict:
    sc = load_scorecard()
    score_map = dict(zip(sc["Feature"], sc["Score"]))
    coeff_map = {k: -v / FACTOR for k, v in score_map.items()}

    fc = sum(coeff_map.get(f, 0) * v for f, v in dummies.items())
    logit = INTERCEPT + fc
    credit_score = float(np.clip(600 + FACTOR * logit, 300, 850))
    pd_calibrated = float(1 / (1 + np.exp(logit - DELTA)))

    risk_name, risk_color = get_risk_class(credit_score)

    # LGD from model
    s1, s2 = load_lgd_models()
    feat_order = list(s1.feature_names_in_)
    feat_vec = np.array([[dummies.get(f, 0) for f in feat_order]])
    p_recovery = s1.predict_proba(feat_vec)[0][1]
    rr_given_recovery = float(np.clip(s2.predict(feat_vec)[0], 0, 1))
    lgd = float(np.clip(1 - p_recovery * rr_given_recovery, 0, 1))

    ead = funded_amnt * 0.85  # simple CCF proxy for demo

    el = pd_calibrated * lgd * ead
    el_rate = pd_calibrated * lgd

    # IFRS9 stage
    if pd_calibrated >= 0.5:
        stage, stage_label = 3, "Stage 3 — Credit Impaired (Lifetime ECL)"
    elif pd_calibrated >= 0.15:
        stage, stage_label = 2, "Stage 2 — SICR Triggered (Lifetime ECL)"
    else:
        stage, stage_label = 1, "Stage 1 — Performing (12-month ECL)"

    # Scorecard breakdown
    breakdown = []
    for feat, val in dummies.items():
        if val == 1 and feat in score_map:
            breakdown.append({"Feature": feat, "Score": score_map[feat]})
    breakdown_df = pd.DataFrame(breakdown).sort_values("Score")

    return {
        "credit_score": round(credit_score),
        "pd_calibrated": pd_calibrated,
        "lgd": lgd,
        "ead": ead,
        "el": el,
        "el_rate": el_rate,
        "risk_class": risk_name,
        "risk_color": risk_color,
        "ifrs9_stage": stage,
        "ifrs9_label": stage_label,
        "breakdown": breakdown_df,
    }

def build_dummies(
    grade, home_ownership, verification_status, purpose,
    initial_list_status, int_rate, annual_inc, fico_score,
    dti, term, mths_since_issue, mths_since_cr_line,
    mths_since_delinq, revol_util, inq_6mths, pct_tl_nvr_dlq
) -> dict:
    d = {}
    for g in ["A", "B", "C", "D", "E"]:
        d[f"grade_{g}"] = 1 if grade == g else 0
    d["home_ownership_OWN"]      = 1 if home_ownership == "OWN" else 0
    d["home_ownership_MORTGAGE"] = 1 if home_ownership == "MORTGAGE" else 0
    d["verif_Verified"]          = 1 if verification_status == "Verified" else 0
    d["verif_Source_Verified"]   = 1 if verification_status == "Source Verified" else 0
    for p in ["debt_consolidation","credit_card","home_improvement","major_purchase","other"]:
        d[f"purpose_{p}"] = 1 if purpose == p else 0
    d["initial_list_w"]          = 1 if initial_list_status == "w" else 0

    d["int_rate_lt_0088"]  = 1 if int_rate < 0.088 else 0
    d["int_rate_088_117"]  = 1 if 0.088 <= int_rate < 0.117 else 0
    d["int_rate_117_148"]  = 1 if 0.117 <= int_rate < 0.148 else 0
    d["int_rate_148_176"]  = 1 if 0.148 <= int_rate < 0.176 else 0
    d["int_rate_176_200"]  = 1 if 0.176 <= int_rate < 0.200 else 0

    d["annual_inc_25k_50k"]  = 1 if 25000 <= annual_inc < 50000 else 0
    d["annual_inc_50k_75k"]  = 1 if 50000 <= annual_inc < 75000 else 0
    d["annual_inc_75k_125k"] = 1 if 75000 <= annual_inc < 125000 else 0
    d["annual_inc_gt125k"]   = 1 if annual_inc >= 125000 else 0

    d["fico_600_640"] = 1 if 600 <= fico_score < 640 else 0
    d["fico_640_680"] = 1 if 640 <= fico_score < 680 else 0
    d["fico_680_720"] = 1 if 680 <= fico_score < 720 else 0
    d["fico_720_760"] = 1 if 720 <= fico_score < 760 else 0
    d["fico_gt760"]   = 1 if fico_score >= 760 else 0

    d["dti_lt_10"]  = 1 if dti < 10 else 0
    d["dti_10_20"]  = 1 if 10 <= dti < 20 else 0
    d["dti_20_28"]  = 1 if 20 <= dti < 28 else 0
    d["dti_28_35"]  = 1 if 28 <= dti < 35 else 0

    d["term_36"] = 1 if term == 36 else 0

    d["mths_issue_lt38"]   = 1 if mths_since_issue < 38 else 0
    d["mths_issue_38_64"]  = 1 if 38 <= mths_since_issue < 64 else 0
    d["mths_issue_64_95"]  = 1 if 64 <= mths_since_issue < 95 else 0
    d["mths_issue_95_118"] = 1 if 95 <= mths_since_issue < 118 else 0

    d["cr_line_lt80"]    = 1 if mths_since_cr_line < 80 else 0
    d["cr_line_80_140"]  = 1 if 80 <= mths_since_cr_line < 140 else 0
    d["cr_line_140_200"] = 1 if 140 <= mths_since_cr_line < 200 else 0
    d["cr_line_gt200"]   = 1 if mths_since_cr_line >= 200 else 0

    d["delinq_never"] = 1 if mths_since_delinq < 0 else 0
    d["delinq_lt24"]  = 1 if 0 <= mths_since_delinq < 24 else 0
    d["delinq_24_48"] = 1 if 24 <= mths_since_delinq < 48 else 0
    d["delinq_48_72"] = 1 if 48 <= mths_since_delinq < 72 else 0

    d["revol_util_lt020"] = 1 if revol_util < 0.20 else 0
    d["revol_util_20_40"] = 1 if 0.20 <= revol_util < 0.40 else 0
    d["revol_util_40_60"] = 1 if 0.40 <= revol_util < 0.60 else 0
    d["revol_util_60_80"] = 1 if 0.60 <= revol_util < 0.80 else 0

    d["inq_0"]   = 1 if inq_6mths == 0 else 0
    d["inq_1"]   = 1 if inq_6mths == 1 else 0
    d["inq_2_3"] = 1 if inq_6mths in [2, 3] else 0

    d["pct_dlq_gt95"]  = 1 if pct_tl_nvr_dlq > 95 else 0
    d["pct_dlq_85_95"] = 1 if 85 < pct_tl_nvr_dlq <= 95 else 0
    d["pct_dlq_70_85"] = 1 if 70 <= pct_tl_nvr_dlq <= 85 else 0

    return d

# ─── Sidebar navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<div style='text-align:center;padding:0.5rem 0'>"
                f"<span style='font-size:2rem'>🏦</span><br>"
                f"<b style='color:{ITC_BLUE};font-size:1.1rem'>Credit Risk Dashboard</b><br>"
                f"<small style='color:#888'>Lending Club · ITC 2025–2026</small></div>",
                unsafe_allow_html=True)
    st.divider()

    page = st.radio(
        "Navigation",
        [
            "🏠 Overview",
            "📊 EDA & Data Understanding",
            "🎯 PD Model & Scorecard",
            "📉 LGD, EAD & Expected Loss",
            "⚖️ Risk Management",
            "📡 Model Monitoring",
            "🔍 Credit Scorecard Calculator",
            "💬 Chat with Reports & Data",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Group: Rachana · Soklang · Pagnarith · Devid")
    st.caption("Supervised by Lecturer TOEM TOUCH")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Overview":
    st.markdown("<div class='main-header'>🏦 Credit Risk Modelling & Data Engineering Pipeline</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>End-to-end production credit risk system on 2.26M Lending Club loans</div>",
                unsafe_allow_html=True)

    # KPI row
    cal = load_calibrator()
    ifrs = load_ifrs9_config()
    c1, c2, c3, c4, c5 = st.columns(5)
    for col, val, lbl in [
        (c1, "2,260,668", "Loan Records"),
        (c2, f"{cal['auc']:.3f}", "AUC (OOT)"),
        (c3, "$1.646B", "IFRS 9 ECL (Weighted)"),
        (c4, "$14.07B", "Basel III RWA"),
        (c5, "0.282 ⚠", "Score PSI"),
    ]:
        col.markdown(f"<div class='metric-card'>"
                     f"<div class='metric-val'>{val}</div>"
                     f"<div class='metric-lbl'>{lbl}</div></div>",
                     unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Pipeline flow
    st.subheader("Pipeline Architecture")
    flow_cols = st.columns(6)
    stages = [
        ("1️⃣", "Ingestion", "PySpark reads 1.6 GB CSV from MinIO in ~7s using column projection"),
        ("2️⃣", "Cleaning", "57 leaking/null columns removed. 3 targets created. OOT split flagged"),
        ("3️⃣", "Feature Eng.", "WoE encoding on training set only. 56 dummies from 16 predictors"),
        ("4️⃣", "Modelling", "PD scorecard + calibration. LGD two-stage. EAD regression"),
        ("5️⃣", "Risk Outputs", "Expected Loss · IFRS 9 ECL · Basel III RWA · Credit policy"),
        ("6️⃣", "Monitoring", "Daily PSI/CSI via Airflow. Grafana alerts. Champion/Challenger"),
    ]
    for col, (icon, title, desc) in zip(flow_cols, stages):
        col.markdown(f"<div style='background:#f0f4ff;border-left:4px solid {ITC_BLUE};"
                     f"padding:0.8rem;border-radius:6px;height:150px'>"
                     f"<b style='color:{ITC_BLUE}'>{icon} {title}</b><br>"
                     f"<small style='color:#444'>{desc}</small></div>",
                     unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Model Performance Summary")
        perf = {
            "Metric": ["AUC", "Gini", "KS Statistic", "Brier Score", "Mean PD (calibrated)", "Score PSI"],
            "Value": [f"{cal['auc']:.3f}", f"{2*cal['auc']-1:.3f}", "0.281", f"{cal['brier_post']:.3f}", f"{cal['post_mean_pd']:.1%}", "0.282"],
            "Benchmark": ["> 0.65", "≥ 0.40", "> 0.25", "≤ 0.20", "Matches DR", "< 0.25"],
            "Status": ["✅ Pass", "⚠️ Near", "✅ Pass", "✅ Pass", "✅ Pass", "🚨 Alert"],
        }
        st.dataframe(pd.DataFrame(perf), use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Portfolio Risk Stack")
        risk = {
            "Output": ["Total EAD", "Mean LGD (long-run)", "Downturn LGD (Basel)", "12-month EL", "EL Rate",
                       "IFRS 9 ECL (Base)", "IFRS 9 ECL (Weighted)", "Lifetime vs 12m uplift",
                       "IRB RWA", "Min Capital (8%)"],
            "Value": ["$3.26B", "92.19%", "93.76%", "$0.808B", "19.93%",
                      "$1.601B", "$1.646B", "+$838M (+104%)", "$14.07B", "$1.13B"],
        }
        st.dataframe(pd.DataFrame(risk), use_container_width=True, hide_index=True)

    st.subheader("Regulatory Framework")
    r1, r2, r3 = st.columns(3)
    for col, title, body, colour in [
        (r1, "Basel II/III AIRB", "Banks use own PD, LGD, EAD to compute capital. CAR ≥ 8% of RWA. Through-the-Cycle PD for stability.", ITC_BLUE),
        (r2, "IFRS 9 ECL", "Forward-looking 3-stage impairment. Stage 1: 12-month ECL. Stage 2/3: Lifetime ECL. Point-in-Time PD with macro scenarios.", ITC_GOLD),
        (r3, "SR 11-7 Governance", "Model development, independent validation, governance & inventory. All experiments tracked in MLflow.", GREEN),
    ]:
        col.markdown(f"<div style='border:2px solid {colour};border-radius:8px;padding:1rem'>"
                     f"<b style='color:{colour}'>{title}</b><br><small>{body}</small></div>",
                     unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — EDA
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 EDA & Data Understanding":
    st.markdown("<div class='main-header'>📊 EDA & Data Understanding (L01)</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>2,260,668 Lending Club loans · 2007–2018 · 151 columns</div>", unsafe_allow_html=True)

    st.subheader("Dataset Overview")
    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1, "2,260,668", "Total Loans"),
        (c2, "1.6 GB", "Raw File Size"),
        (c3, "151", "Original Columns"),
        (c4, "~17%", "Overall Default Rate"),
    ]:
        col.metric(lbl, val)

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Loan Volume & Default Rate Over Time")
        st.image(str(REPORTS / "L01_loan_volume_default_rate.png"), use_container_width=True)
        st.caption("Loan originations grew steadily through 2015. Default rate jumped from 18.6% (train) "
                   "to 25.3% (OOT), a +6.7pp shift — first signal of population drift confirmed later by PSI = 0.282.")

    with c2:
        st.subheader("Default Rate by Credit Grade")
        st.image(str(REPORTS / "L01_default_rate_by_grade.png"), use_container_width=True)
        st.caption("Strict monotonic increase from Grade A (~5%) to Grade G (>35%). "
                   "This validates the WoE binning approach and the 10-class credit policy design.")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("FICO Score Distribution: Good vs Bad")
        st.image(str(REPORTS / "L01_fico_distribution_good_bad.png"), use_container_width=True)
        st.caption("Good borrowers cluster at higher FICO scores. The overlap at 640–720 is where the "
                   "credit policy adds the most value. FICO achieves IV > 0.30 — strongest single predictor.")

    with c2:
        st.subheader("Data Cleaning Summary")
        cleaning = pd.DataFrame({
            "Category": ["100% null columns", "Identifier / constant", "Joint application", "Hardship / settlement", "Post-application leakage", "Total removed"],
            "Count": [15, 8, 3, 18, 15, 57],
            "Examples": ["sec_app_*, member_id", "id, url, policy_code", "sec_app_* (>99% null)", "hardship_* (>97% null)", "total_pymnt, recoveries", "—"],
        })
        st.dataframe(cleaning, use_container_width=True, hide_index=True)

        st.markdown("**6 derived features created:**")
        st.code("""fico_score           = (fico_range_low + fico_range_high) / 2
term_int             = int(term.replace(' months',''))
int_rate             = int_rate_raw / 100
mths_since_issue_d   = months_between(today, issue_date)
mths_since_cr_line   = months_between(today, earliest_cr_line)
emp_length_int       = int(emp_length.extract_digits())""")

    st.subheader("Out-of-Time Split")
    oot_df = pd.DataFrame({
        "Split": ["Training", "OOT Test"],
        "Years": ["2007–2015", "2016–2018"],
        "Rows": ["831,051", "538,515"],
        "Default Rate": ["18.62%", "25.27%"],
        "Role": ["Fit WoE bins + train all models", "Evaluate on genuinely future data"],
    })
    st.dataframe(oot_df, use_container_width=True, hide_index=True)
    st.info("**Why OOT?** A random split leaks future patterns into training. OOT mirrors real deployment: "
            "models trained on history must generalise to future applicants. The +6.65pp default rate jump "
            "between periods is itself evidence that the population shifted.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — PD MODEL
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎯 PD Model & Scorecard":
    st.markdown("<div class='main-header'>🎯 PD Model & Scorecard (L02)</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>WoE logistic regression · 39 features · PDO 20 · Scale 300–850</div>", unsafe_allow_html=True)

    cal = load_calibrator()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AUC (OOT)", f"{cal['auc']:.3f}", "Benchmark > 0.65 ✅")
    c2.metric("Gini", f"{2*cal['auc']-1:.3f}", "Benchmark ≥ 0.40")
    c3.metric("Brier Score", f"{cal['brier_post']:.3f}", f"Pre-calib: {cal['brier_pre']:.3f}")
    c4.metric("PD Calibration δ", f"+{cal['delta']:.4f}", f"HL: {cal['hl_pre']:,} → {cal['hl_post']:,}")
    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("ROC Curve")
        st.image(str(REPORTS / "L02_roc_curve.png"), use_container_width=True)
        st.caption(f"AUC = {cal['auc']:.3f}, Gini = {2*cal['auc']-1:.3f}. "
                   "Curve lies above the diagonal across all thresholds — confirmed discriminatory power.")

    with c2:
        st.subheader("Decile Analysis")
        st.image(str(REPORTS / "L02_decile_analysis.png"), use_container_width=True)
        st.caption("Bad rate decreases strictly Decile 1→10. Zero monotonicity violations. "
                   "Top 3 deciles capture >50% of all bad borrowers. Mandatory scorecard acceptance criterion.")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Calibration Reliability Diagram")
        st.image(str(REPORTS / "L02_calibration_reliability_diagram.png"), use_container_width=True)
        st.caption("Pre-calibration: all points below the 45° diagonal (mean PD 20.2% vs actual 25.3%). "
                   "Post-calibration (δ=+0.3204): points align with diagonal. HL statistic dropped 96%.")

    with c2:
        st.subheader("Score Distribution: Good vs Bad")
        st.image(str(REPORTS / "L02_score_distribution_good_bad.png"), use_container_width=True)
        st.caption("Good borrowers cluster at higher scores; bad at lower. "
                   "The 500–650 overlap band is where the ROI-based credit policy adds the most value.")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Model Coefficients (39 WoE Dummies)")
        st.image(str(REPORTS / "L02_pd_model_coefficients.png"), use_container_width=True)
        st.caption("All 39 dummies are statistically significant (p < 0.05, Wald test). "
                   "Positive coefficients → lower default risk. Direction is consistent with credit intuition.")

    with c2:
        st.subheader("Risk Class Distribution")
        st.image(str(REPORTS / "L02_risk_class_distribution.png"), use_container_width=True)
        st.caption("Portfolio concentrates in BB–C middle bands. Auto-approve (AA/A) and auto-reject (F) "
                   "cover tail extremes. Most decisions use the ROI threshold rule.")

    st.subheader("Score-to-PD Conversion")
    st.image(str(REPORTS / "L02_score_pd_conversion.png"), use_container_width=True)
    st.caption("Monotonically decreasing: every 20-point score increase halves predicted default odds (PDO=20). "
               "Reference: score 600 at 1:1 odds. This smooth mapping enables IFRS 9 SICR classification and ECOA adverse action codes.")

    st.subheader("Calibration Impact on Regulatory Outputs")
    impact = pd.DataFrame({
        "Output": ["Mean PD", "H-L Statistic", "IRB RWA", "IRB Min Capital", "12-month EL", "IFRS 9 ECL", "Stage 2 Mix"],
        "Pre-calibration": ["20.18%", "10,039", "$13.62B", "$1.09B", "$0.650B", "$1.334B", "61.0%"],
        "Post-calibration": ["25.27%", "403", "$14.07B", "$1.13B", "$0.808B", "$1.601B", "74.2%"],
        "Delta": ["+5.09pp", "−96%", "+$0.45B", "+$0.04B", "+$0.158B (+24%)", "+$0.267B (+20%)", "+13.2pp"],
    })
    st.dataframe(impact, use_container_width=True, hide_index=True)
    st.warning("PD calibration is **financially material** — not cosmetic. Without it, IFRS 9 ECL is under-stated by $267M (20%).")

    sc = load_scorecard()
    with st.expander("📋 Full Scorecard Table (49 features)"):
        st.dataframe(sc.round(4), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — LGD, EAD, EL
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📉 LGD, EAD & Expected Loss":
    st.markdown("<div class='main-header'>📉 LGD, EAD & Expected Loss (L03)</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Two-stage LGD · CCF regression · EL = PD × LGD × EAD</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mean LGD (long-run)", "92.19%", "~8% recovery")
    c2.metric("Downturn LGD (Basel)", "93.76%", "+1.57pp haircut")
    c3.metric("LGD MAE", "~5%", "Two-stage model")
    c4.metric("EAD MAE", "~14%", "CCF regression")
    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Recovery Rate Distribution")
        st.image(str(REPORTS / "L03_recovery_rate_distribution.png"), use_container_width=True)
        st.caption("~50% zero recovery justifies two-stage LGD architecture. "
                   "Stage 1 (logistic) predicts P(RR>0); Stage 2 (linear) predicts the recovery amount.")

    with c2:
        st.subheader("LGD Model Architecture")
        st.markdown("""
        | Stage | Model | Target |
        |---|---|---|
        | **Stage 1** | Logistic Regression | P(Recovery Rate > 0) |
        | **Stage 2** | Linear Regression | E[Recovery Rate \| RR > 0] |
        | **Combined** | LGD = 1 − (P₁ × RR₂) | Loss Given Default |
        """)
        st.markdown("""
        **Downturn LGD (Basel AIRB CRE36):**
        The downturn LGD applies a 1.25× haircut to the recovery rate under stressed economic conditions.
        This is always constrained to be ≥ long-run LGD (recoveries fall, never rise, in a downturn).
        """)
        st.info("**Why LGD is ~92%?** Lending Club loans are **unsecured personal loans** — no collateral to seize. "
                "Average recovery rate is only ~8% of the outstanding balance.")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("LGD Residuals")
        st.image(str(REPORTS / "L03_lgd_residuals.png"), use_container_width=True)
        st.caption("Centred around zero. Slight negative skew: model conservatively underestimates large "
                   "recoveries. MAE ≈ 5% — acceptable for portfolio-level provisioning.")

    with c2:
        st.subheader("CCF Distribution (EAD)")
        st.image(str(REPORTS / "L03_ccf_distribution.png"), use_container_width=True)
        st.caption("Right-skewed with mass near 1.0. Most defaults occur early before significant repayment. "
                   "Median CCF > 0.8 means EAD typically exceeds 80% of funded amount.")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("EAD Residuals")
        st.image(str(REPORTS / "L03_ead_residuals.png"), use_container_width=True)
        st.caption("MAE ≈ 14%. Symmetric — no directional bias. Higher spread than LGD because predicting "
                   "when within the loan lifecycle default occurs is inherently uncertain.")

    with c2:
        st.subheader("Expected Loss by Grade")
        st.image(str(REPORTS / "L03_expected_loss_by_grade.png"), use_container_width=True)
        st.caption("EL rate rises monotonically A→G. Steeper than default rate alone because lower-grade "
                   "borrowers also have higher EAD (fewer repayments before default).")

    st.subheader("Vintage Analysis")
    st.image(str(REPORTS / "L03_vintage_analysis.png"), use_container_width=True)
    st.caption("Predicted PD tracks actual default rate across origination cohorts. "
               "The widening gap in 2016+ cohorts is the quantitative signal for a model rebuild (PSI = 0.282 ALERT).")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — RISK MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚖️ Risk Management":
    st.markdown("<div class='main-header'>⚖️ Risk Management & Regulatory Outputs</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>IFRS 9 ECL · Basel III AIRB · Credit Policy · Portfolio Summary</div>",
                unsafe_allow_html=True)

    ifrs = load_ifrs9_config()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("12-month EL", "$0.808B", "19.93% of EAD")
    c2.metric("IFRS 9 ECL (Weighted)", "$1.646B", "+$838M vs 12m (+104%)")
    c3.metric("Basel III RWA", "$14.07B", "Capital $1.13B")
    c4.metric("Capital / EAD", "34.5%", "LGD ~93% driver")
    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("IFRS 9: Three-Stage ECL Staging")
        st.image(str(REPORTS / "L03_ifrs9_ecl_staging.png"), use_container_width=True)
        st.caption("Stage 2 dominates at 71.4% ($967M). The calibrated PiT PD of 25.3% causes many OOT "
                   "loans to trigger the 'PD doubling' SICR rule → lifetime ECL treatment.")

    with c2:
        st.subheader("IFRS 9: SICR Classification Rules")
        st.markdown("""
        | Stage | Trigger | ECL Horizon |
        |---|---|---|
        | **Stage 1** | No SICR | 12-month |
        | **Stage 2** | PD ≥ 2× origination PD **or** ΔPD ≥ 5pp **or** 30-DPD backstop | Lifetime |
        | **Stage 3** | 90+ DPD or Charged Off | Lifetime |
        """)
        st.markdown("**Lifetime ECL formula:**")
        st.latex(r"ECL^{life} = \sum_{t=1}^{T} \frac{h \cdot (1-h)^{t-1} \cdot LGD \cdot EAD}{(1+r)^t}")
        st.caption("h = monthly hazard rate, r = 5% annual discount rate")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("IFRS 9: Scenario-Weighted ECL (§5.5.17)")
        st.image(str(REPORTS / "L03_ifrs9_scenario_weighted_ecl.png"), use_container_width=True)

    with c2:
        st.subheader("Macro Scenario Results")
        scen = ifrs.get("scenarios", {})
        rows = []
        for name, cfg in scen.items():
            rows.append({
                "Scenario": name,
                "Weight": ifrs["weights"].get(name, ""),
                "Δ Unemployment": f"{cfg.get('delta_unem', 0):+.1f}pp",
                "Δ GDP": f"{cfg.get('delta_gdp', 0):+.1f}pp",
                "Mean PD": f"{cfg.get('mean_pd', 0):.1%}",
                "ECL": f"${ifrs.get(f'ecl_{name.lower()}_B', 0):.3f}B",
            })
        rows.append({
            "Scenario": "**Weighted Total**", "Weight": "—",
            "Δ Unemployment": "—", "Δ GDP": "—", "Mean PD": "—",
            "ECL": f"**${ifrs['ecl_weighted_B']:.3f}B**",
        })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption("Non-linearity uplift +$44M. Downside scenario is +36% above base. "
                   "Lifetime ECL is convex in PD — losses accelerate faster than PD increases.")

    st.subheader("Basel III AIRB Capital Formula")
    col1, col2 = st.columns(2)
    with col1:
        st.latex(r"\rho = 0.03 + 0.16 \cdot \frac{1-e^{-35 \cdot PD}}{1-e^{-35}}")
        st.latex(r"PD_{WC} = \Phi\!\left(\frac{\Phi^{-1}(PD)+\sqrt{\rho}\,\Phi^{-1}(0.999)}{\sqrt{1-\rho}}\right)")
        st.latex(r"K = LGD_{DT}(PD_{WC}-PD), \quad RWA = 12.5 \cdot K \cdot EAD")
    with col2:
        capital_df = pd.DataFrame({
            "Metric": ["Total EAD", "IRB RWA", "Minimum Capital (8%)", "Capital / EAD", "Downturn LGD"],
            "Value": ["$3.26B", "$14.07B", "$1.13B", "34.5%", "93.76%"],
        })
        st.dataframe(capital_df, use_container_width=True, hide_index=True)
        st.warning("Capital ratio of 34.5% is high because capital scales with LGD through the AIRB formula. "
                   "Unsecured portfolios need fundamentally more capital than secured lending.")

    st.subheader("10-Class Credit Policy")
    policy_df = pd.DataFrame(RISK_BANDS, columns=["Class", "Score Min", "Score Max", "Colour"])
    policy_df["Decision"] = policy_df["Class"].map({
        "AA": "✅ Auto-Approve", "A": "✅ Auto-Approve",
        "AB": "📊 Approve if ROI > 2.15%", "BB": "📊 Approve if ROI > 2.15%",
        "B": "📊 Approve if ROI > 2.15%",  "BC": "📊 Approve if ROI > 2.15%",
        "C": "📊 Approve if ROI > 2.15%",  "CD": "📊 Approve if ROI > 2.15%",
        "DD": "🔎 Manual Review", "F": "❌ Auto-Reject",
    })
    st.dataframe(policy_df[["Class", "Score Min", "Score Max", "Decision"]],
                 use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — MONITORING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📡 Model Monitoring":
    st.markdown("<div class='main-header'>📡 Model Monitoring (L04)</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Population Stability Index · CSI · Champion/Challenger · Daily Airflow DAG</div>",
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Score PSI", "0.282", "🚨 ALERT (> 0.25)")
    c2.metric("Champion Gini", "0.387", "Keep Champion ✅")
    c3.metric("Monitoring Frequency", "Daily", "Airflow DAG-06")
    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("PSI Master Dashboard")
        st.image(str(REPORTS / "L04_psi_master_dashboard.png"), use_container_width=True)
        st.caption("Score PSI = 0.282 in the red ALERT zone. Several input variable CSI bars also elevated. "
                   "Provides root-cause signals for which features are driving the drift.")

    with c2:
        st.subheader("PSI Thresholds")
        psi_thr = pd.DataFrame({
            "PSI Range": ["< 0.10", "0.10 – 0.25", "> 0.25"],
            "Status": ["🟢 Stable", "🟡 Monitor", "🔴 Alert"],
            "Action": ["Continue as-is", "Investigate root cause", "Consider model rebuild"],
        })
        st.dataframe(psi_thr, use_container_width=True, hide_index=True)
        st.markdown("**PSI Formula:**")
        st.latex(r"PSI = \sum_i (O_i - E_i) \ln\!\left(\frac{O_i}{E_i}\right)")
        st.caption("O_i = OOT bin proportion, E_i = Training bin proportion")
        st.error("**Score PSI = 0.282 (ALERT).** The 2016–2018 applicant population has shifted "
                 "materially from the 2007–2015 training window. Model rebuild is recommended.")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Score Distribution Shift")
        st.image(str(REPORTS / "L04_score_psi_distribution.png"), use_container_width=True)
        st.caption("OOT population (2016–2018) shifted to lower scores. Consistent with jump in default rate "
                   "from 18.6% to 25.3% between periods.")

    with c2:
        st.subheader("Characteristic Stability Index")
        st.image(str(REPORTS / "L04_characteristic_stability_index.png"), use_container_width=True)
        st.caption("CSI ranked across all 39 model inputs. High-IV predictors (greatest scorecard contribution) "
                   "are also the most unstable — flagged for re-binning.")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("CSI — Continuous Variables")
        st.image(str(REPORTS / "L04_psi_continuous_variables.png"), use_container_width=True)
    with c2:
        st.subheader("CSI — Discrete Variables")
        st.image(str(REPORTS / "L04_psi_discrete_variables.png"), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Champion / Challenger")
        st.image(str(REPORTS / "L04_champion_challenger.png"), use_container_width=True)
        st.success("**Verdict: Keep Champion.** Challenger Gini ≈ 0.387 — identical. "
                   "Mann-Whitney U not significant. Next challenger: XGBoost/LightGBM.")

    with c2:
        st.subheader("Monitoring Schedule")
        schedule_df = pd.DataFrame({
            "Frequency": ["Daily", "Monthly", "Quarterly", "Annual"],
            "Activity": [
                "PSI + CSI for all variables; Grafana alert if PSI > 0.25",
                "Decile stability, vintage update, CSI per variable",
                "Full model performance review (AUC, Gini, KS, Brier)",
                "Full recalibration review; SR 11-7 §4 revalidation",
            ],
            "Trigger": ["PSI > 0.25", "CSI > 0.25 on any input", "Gini drop > 5pp", "PSI ALERT > 2 months"],
        })
        st.dataframe(schedule_df, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 7 — CREDIT SCORECARD CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Credit Scorecard Calculator":
    st.markdown("<div class='main-header'>🔍 Credit Scorecard Calculator</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Enter loan application details to compute credit score, PD, LGD, EAD, EL, and IFRS 9 stage</div>",
                unsafe_allow_html=True)

    with st.form("scorecard_form"):
        st.subheader("Borrower & Loan Information")
        c1, c2, c3 = st.columns(3)
        with c1:
            grade           = st.selectbox("Lending Club Grade", ["A","B","C","D","E","F","G"], index=1,
                                           help="Internal Lending Club grade A (best) to G (worst)")
            home_ownership  = st.selectbox("Home Ownership", ["RENT","MORTGAGE","OWN","OTHER"], index=0)
            verification    = st.selectbox("Income Verification", ["Not Verified","Verified","Source Verified"], index=0)
            purpose         = st.selectbox("Loan Purpose",
                                           ["debt_consolidation","credit_card","home_improvement",
                                            "major_purchase","other","house","car","small_business"], index=0)
            initial_list    = st.selectbox("Initial List Status", ["w","f"], index=0,
                                           help="w = whole, f = fractional listing")

        with c2:
            funded_amnt     = st.number_input("Funded Amount ($)", 1000, 40000, 10000, step=500)
            term            = st.selectbox("Loan Term (months)", [36, 60], index=0)
            int_rate        = st.slider("Interest Rate (%)", 5.0, 30.0, 12.0, step=0.1) / 100
            annual_inc      = st.number_input("Annual Income ($)", 10000, 500000, 60000, step=5000)
            dti             = st.slider("Debt-to-Income Ratio (%)", 0.0, 45.0, 15.0, step=0.5)

        with c3:
            fico_score      = st.slider("FICO Score", 580, 850, 700, step=5)
            revol_util      = st.slider("Revolving Utilisation (%)", 0.0, 100.0, 35.0, step=1.0) / 100
            inq_6mths       = st.selectbox("Inquiries (last 6 months)", [0, 1, 2, 3, 4, 5], index=0)
            mths_delinq     = st.number_input("Months Since Last Delinquency (−1 = never)", -1, 200, -1,
                                              help="Enter −1 if borrower has never been delinquent")
            pct_tl_nvr_dlq  = st.slider("% Accounts Never Delinquent", 50.0, 100.0, 95.0, step=0.5)

        st.subheader("Credit History")
        c1, c2 = st.columns(2)
        with c1:
            mths_since_issue  = st.slider("Months Since Loan Issued", 1, 200, 48,
                                          help="How long ago this loan was issued (for monitoring context)")
        with c2:
            mths_since_cr_line = st.slider("Months Since Earliest Credit Line", 10, 400, 120)

        submitted = st.form_submit_button("🔍 Calculate Credit Score & Risk", use_container_width=True)

    if submitted:
        dummies = build_dummies(
            grade, home_ownership, verification, purpose, initial_list,
            int_rate, annual_inc, fico_score, dti, term,
            mths_since_issue, mths_since_cr_line, mths_delinq,
            revol_util, inq_6mths, pct_tl_nvr_dlq
        )
        result = compute_score_pd(dummies, funded_amnt)

        st.divider()
        st.subheader("📋 Assessment Results")

        # Credit score gauge
        score = result["credit_score"]
        rclass = result["risk_class"]
        rcolor = result["risk_color"]

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": f"Credit Score — <b>{rclass}</b>", "font": {"size": 20}},
            gauge={
                "axis": {"range": [300, 850], "tickwidth": 1},
                "bar": {"color": rcolor, "thickness": 0.3},
                "bgcolor": "white",
                "steps": [
                    {"range": [300, 459], "color": "#ffebee"},
                    {"range": [460, 579], "color": "#fff3e0"},
                    {"range": [580, 659], "color": "#fffde7"},
                    {"range": [660, 719], "color": "#e8f5e9"},
                    {"range": [720, 850], "color": "#e3f2fd"},
                ],
                "threshold": {"line": {"color": rcolor, "width": 4}, "thickness": 0.75, "value": score},
            }
        ))
        fig_gauge.update_layout(height=280, margin=dict(t=40, b=10, l=20, r=20))

        col1, col2 = st.columns([1, 1])
        with col1:
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col2:
            st.markdown(f"### Risk Class: <span style='color:{rcolor}'><b>{rclass}</b></span>",
                        unsafe_allow_html=True)
            st.markdown(f"**Credit Score:** {score} / 850")

            pd_val = result['pd_calibrated']
            if pd_val < 0.15:
                pd_badge = f"<span class='green-badge'>Low Risk {pd_val:.1%}</span>"
            elif pd_val < 0.35:
                pd_badge = f"<span class='amber-badge'>Moderate Risk {pd_val:.1%}</span>"
            else:
                pd_badge = f"<span class='red-badge'>High Risk {pd_val:.1%}</span>"

            stage = result['ifrs9_stage']
            if stage == 1:
                stage_badge = f"<span class='green-badge'>{result['ifrs9_label']}</span>"
            elif stage == 2:
                stage_badge = f"<span class='amber-badge'>{result['ifrs9_label']}</span>"
            else:
                stage_badge = f"<span class='red-badge'>{result['ifrs9_label']}</span>"

            st.markdown(f"**Probability of Default:** {pd_badge}", unsafe_allow_html=True)
            st.markdown(f"**IFRS 9 Stage:** {stage_badge}", unsafe_allow_html=True)

        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PD (calibrated)", f"{result['pd_calibrated']:.2%}")
        c2.metric("LGD (estimated)", f"{result['lgd']:.2%}")
        c3.metric("EAD (approx.)", f"${result['ead']:,.0f}")
        c4.metric("Expected Loss", f"${result['el']:,.0f} ({result['el_rate']:.1%})")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Score Breakdown by Feature")
            bd = result["breakdown"]
            if not bd.empty:
                bd_sorted = bd.sort_values("Score")
                colors = [RED if s > 0 else GREEN for s in bd_sorted["Score"]]
                fig_bar = go.Figure(go.Bar(
                    x=bd_sorted["Score"],
                    y=bd_sorted["Feature"],
                    orientation="h",
                    marker_color=colors,
                    text=bd_sorted["Score"],
                    textposition="outside",
                ))
                fig_bar.update_layout(
                    title="Score Contributions (negative = worse, positive = better for score)",
                    xaxis_title="Score Points",
                    height=max(300, len(bd_sorted) * 24),
                    margin=dict(l=200, r=40, t=50, b=40),
                    plot_bgcolor="white",
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No active scorecard features for this combination.")

        with col2:
            st.subheader("Risk Summary")
            summary = {
                "Credit Score": [score],
                "Risk Class": [rclass],
                "PD (calibrated)": [f"{result['pd_calibrated']:.2%}"],
                "LGD": [f"{result['lgd']:.2%}"],
                "EAD": [f"${result['ead']:,.0f}"],
                "Expected Loss": [f"${result['el']:,.0f}"],
                "EL Rate": [f"{result['el_rate']:.2%}"],
                "IFRS 9 Stage": [stage],
                "ECL Type": ["12-month" if stage == 1 else "Lifetime"],
            }
            st.dataframe(pd.DataFrame(summary).T.rename(columns={0: "Value"}),
                         use_container_width=True)

            # Credit decision
            roi_approx = (int_rate * funded_amnt * (term / 12) - result['el']) / funded_amnt / (term / 12)
            rf = 0.0215
            if rclass in ["AA", "A"]:
                decision, dec_color = "✅ AUTO-APPROVE", GREEN
                reason = "Lowest risk class — automatic approval."
            elif rclass == "F":
                decision, dec_color = "❌ AUTO-REJECT", RED
                reason = "Highest risk class — automatic rejection."
            elif roi_approx > rf:
                decision, dec_color = "✅ APPROVE (ROI)", GREEN
                reason = f"Annualised ROI {roi_approx:.2%} > base rate {rf:.2%}."
            else:
                decision, dec_color = "❌ REJECT (ROI)", RED
                reason = f"Annualised ROI {roi_approx:.2%} < base rate {rf:.2%}."

            st.markdown(f"<div style='background:{dec_color}20;border:2px solid {dec_color};"
                        f"border-radius:8px;padding:1rem;margin-top:0.5rem'>"
                        f"<b style='color:{dec_color};font-size:1.2rem'>{decision}</b><br>"
                        f"<small>{reason}<br>Approx. annualised ROI: {roi_approx:.2%}</small></div>",
                        unsafe_allow_html=True)

            if result["pd_calibrated"] >= 0.35:
                st.markdown("**Adverse Action Codes (ECOA Reg B):**")
                codes = []
                bd_sorted_adv = result["breakdown"].sort_values("Score", ascending=False)
                reason_map = {
                    "grade": "AA01 — Derogatory internal credit grade",
                    "fico": "AA02 — Insufficient credit score",
                    "dti": "AA03 — Debt-to-income ratio too high",
                    "int_rate": "AA04 — High interest rate indicative of risk",
                    "revol_util": "AA05 — Revolving balance utilisation too high",
                    "inq": "AA06 — Too many recent credit inquiries",
                    "delinq": "AA07 — Recent delinquency history",
                    "annual_inc": "AA08 — Insufficient income",
                }
                for _, row in bd_sorted_adv.head(4).iterrows():
                    feat = row["Feature"].lower()
                    for key, code in reason_map.items():
                        if key in feat:
                            codes.append(f"• {code}")
                            break
                for c in codes[:4]:
                    st.markdown(c)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 8 — CHAT WITH REPORTS & DATA
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💬 Chat with Reports & Data":
    st.markdown("<div class='main-header'>💬 Chat with Reports & Data</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Ask anything about the credit risk reports or loan portfolio data</div>",
                unsafe_allow_html=True)

    # ── Lazy imports (only loaded when this page is opened) ───────────────────
    try:
        from langchain_community.vectorstores import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings
        from openai import OpenAI
        _rag_available = True
    except ImportError as _e:
        _rag_available = False
        st.error(
            f"Missing packages: {_e}\n\n"
            "Run this in your terminal first:\n\n"
            "```\npip install langchain langchain-community chromadb "
            "sentence-transformers pypdf openai\n```"
        )

    CHROMA_DIR   = BASE / "chroma_db"
    PDF_STORE    = str(CHROMA_DIR / "pdf_store")
    DATA_STORE   = str(CHROMA_DIR / "data_store")
    EMBED_MODEL  = "all-MiniLM-L6-v2"
    TOP_K        = 5

    if _rag_available:

        # ── Check vector stores exist ─────────────────────────────────────────
        pdf_ready  = (CHROMA_DIR / "pdf_store").exists()
        data_ready = (CHROMA_DIR / "data_store").exists()

        col_status1, col_status2 = st.columns(2)
        col_status1.markdown(
            f"{'✅' if pdf_ready  else '❌'} **PDF store** "
            f"{'ready' if pdf_ready  else '— run `python rag_ingest.py` first'}"
        )
        col_status2.markdown(
            f"{'✅' if data_ready else '❌'} **Data store** "
            f"{'ready' if data_ready else '— run `python rag_ingest.py` first'}"
        )

        if not pdf_ready and not data_ready:
            st.warning(
                "No vector stores found. Run the ingestion script once:\n"
                "```\npython rag_ingest.py\n```"
            )
            st.stop()

        # ── LLM config (sidebar widget just for this page) ────────────────────
        with st.sidebar:
            st.divider()
            st.markdown("### 🤖 LLM Settings")
            llm_api_key = st.text_input(
                "API Key",
                value=os.getenv("LLM_API_KEY", ""),
                type="password",
            )
            llm_base_url = st.text_input(
                "API Base URL",
                value=os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1"),
            )
            llm_model = st.text_input(
                "Model",
                value=os.getenv("LLM_MODEL", "deepseek-v4-flash"),
            )
            source_choice = st.multiselect(
                "Search in",
                ["📄 PDF Reports", "📊 Loan Data"],
                default=["📄 PDF Reports", "📊 Loan Data"],
            )

        # ── Cached resources ──────────────────────────────────────────────────
        @st.cache_resource(show_spinner="Loading embedding model …")
        def _load_embeddings():
            return HuggingFaceEmbeddings(model_name=EMBED_MODEL)

        @st.cache_resource(show_spinner="Loading PDF vector store …")
        def _load_pdf_store(_emb):
            return Chroma(persist_directory=PDF_STORE, embedding_function=_emb)

        @st.cache_resource(show_spinner="Loading data vector store …")
        def _load_data_store(_emb):
            return Chroma(persist_directory=DATA_STORE, embedding_function=_emb)

        emb = _load_embeddings()
        stores = []
        if "📄 PDF Reports" in source_choice and pdf_ready:
            stores.append(("📄 PDF", _load_pdf_store(emb)))
        if "📊 Loan Data" in source_choice and data_ready:
            stores.append(("📊 Data", _load_data_store(emb)))

        # ── Retrieve context for a query ──────────────────────────────────────
        def retrieve_context(query: str) -> tuple[str, list[str]]:
            all_chunks, sources = [], []
            for label, store in stores:
                docs = store.similarity_search(query, k=TOP_K)
                for d in docs:
                    all_chunks.append(d.page_content)
                    src = d.metadata.get("source_file", label)
                    sources.append(src)
            context = "\n\n---\n\n".join(all_chunks)
            return context, list(dict.fromkeys(sources))  # deduplicated

        # ── LLM call (streaming) ──────────────────────────────────────────────
        SYSTEM_PROMPT = (
            "You are an expert credit risk analyst assistant for the ITC Lending Club project. "
            "Answer questions based ONLY on the provided context from research reports and loan data. "
            "Be precise, cite specific numbers and figures when available. "
            "If the answer is not in the context, say so clearly."
        )

        def stream_answer(question: str, context: str):
            if not llm_api_key:
                yield "⚠️ Please enter your API key in the sidebar."
                return
            try:
                client = OpenAI(api_key=llm_api_key, base_url=llm_base_url)
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
                ]
                for chunk in client.chat.completions.create(
                    model=llm_model,
                    messages=messages,
                    stream=True,
                    max_tokens=1200,
                    temperature=0.2,
                ):
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
            except Exception as e:
                yield f"❌ LLM error: {e}"

        # ── Chat UI ───────────────────────────────────────────────────────────
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []

        # Render history
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("sources"):
                    st.caption("Sources: " + " · ".join(msg["sources"]))

        # New question
        question = st.chat_input("Ask about the reports or loan data …")
        if question:
            # Show user message
            st.session_state.chat_messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            # Retrieve + stream answer
            with st.chat_message("assistant"):
                if not stores:
                    st.warning("No vector stores selected or available.")
                else:
                    context, sources = retrieve_context(question)
                    answer_placeholder = st.empty()
                    full_answer = ""
                    for token in stream_answer(question, context):
                        full_answer += token
                        answer_placeholder.markdown(full_answer + "▌")
                    answer_placeholder.markdown(full_answer)
                    if sources:
                        st.caption("Sources: " + " · ".join(sources))
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": full_answer,
                        "sources": sources,
                    })

        # Clear button
        if st.session_state.chat_messages:
            if st.button("🗑 Clear conversation"):
                st.session_state.chat_messages = []
                st.rerun()
