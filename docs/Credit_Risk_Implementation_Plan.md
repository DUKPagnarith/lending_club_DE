# Credit Risk Modeling — Full Implementation Plan (v2)
### Lending Club Dataset · Data Engineering · Machine Learning · Risk Management

> **Version 2 — Updated after reviewing:**  
> - [levist7/Credit_Risk_Modelling](https://github.com/levist7/Credit_Risk_Modelling)  
> - [allmeidaapedro/Lending-Club-Credit-Scoring](https://github.com/allmeidaapedro/Lending-Club-Credit-Scoring)  
>  
> Key improvements incorporated: out-of-time split, separate data cleaning phase, business EDA, statsmodels p-values, Brier Score, decile analysis, 10 risk classes, ROI-based credit policy, beta regression consideration for LGD, SHAP/LIME future steps.

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Technology Stack & Rationale](#2-technology-stack--rationale)
3. [Project Repository Structure](#3-project-repository-structure)
4. [Learning Notebooks Path (L01–L04)](#4-learning-notebooks-path-l01l04)
5. [Part A — Data Engineering](#part-a--data-engineering)
6. [Part B — Machine Learning](#part-b--machine-learning)
7. [Part C — Risk Management](#part-c--risk-management)
8. [End-to-End Data Flow](#8-end-to-end-data-flow)
9. [Implementation Roadmap](#9-implementation-roadmap)
10. [Key Improvements vs Original Plan](#10-key-improvements-vs-original-plan)

---

## 1. System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        INGESTION LAYER                               │
│   Lending Club CSV (2.5M+ rows) → MinIO Data Lake (raw zone)        │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│                       PROCESSING LAYER                               │
│   Apache Spark (PySpark) — large-scale transformation & feature eng  │
│   Great Expectations — data quality validation at each stage         │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│                        STORAGE LAYER                                 │
│   PostgreSQL — raw / staging / features / models / risk schemas      │
│   MinIO — parquet files for Spark intermediate outputs               │
│   Redis — feature cache for real-time scoring                        │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│                     ML & SERVING LAYER                               │
│   MLflow — experiment tracking + model registry (SR 11-7 compliant) │
│   FastAPI — REST API for real-time PD/LGD/EAD scoring                │
│   Scikit-learn / Statsmodels / PySpark MLlib — model training        │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│                    ORCHESTRATION & MONITORING                        │
│   Apache Airflow — DAG scheduling for all pipelines                  │
│   Prometheus + Grafana — metrics, dashboards, alerting               │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack & Rationale

| Layer | Tool | Why Banks Use It |
|-------|------|-----------------|
| **Orchestration** | Apache Airflow | Industry-standard workflow scheduler; auditable DAG runs, SLA tracking |
| **Big Data Processing** | Apache Spark (PySpark) | Handles 100M+ rows; used by JPMorgan, HSBC, Barclays for batch credit scoring |
| **Relational Database** | PostgreSQL | ACID-compliant; widely used operational data store in mid-size banks |
| **Data Lake** | MinIO | S3-compatible on-premise object store for data sovereignty |
| **Data Transformation** | dbt | SQL-based lineage and testing; adopted rapidly in banking analytics |
| **Data Quality** | Great Expectations | Statistical validation at each stage; meets audit requirements |
| **ML Tracking** | MLflow | Model registry with stage gates (Staging → Production); SR 11-7 compliant |
| **Statistical Modeling** | Statsmodels | Proper p-values, confidence intervals; required for regulatory interpretability |
| **ML Modeling** | Scikit-learn | Industry-standard for logistic/linear regression; explainable |
| **Future: Explainability** | SHAP / LIME | Explainability tools for next model iteration when boosting is used |
| **Model Serving** | FastAPI | Async, high-performance Python API for scoring microservices |
| **Containerization** | Docker + Docker Compose | Reproducible environments; standard in bank DevOps |
| **Feature Cache** | Redis | Sub-millisecond feature retrieval for real-time lending decisions |
| **Monitoring** | Prometheus + Grafana | Time-series metrics; alerts on PSI breach, Gini drop, API latency |

---

## 3. Project Repository Structure

```
credit-risk-system/
│
├── docker-compose.yml
├── .env.example
├── Makefile
│
├── notebooks/                      # LEARNING PHASE (L01–L04)
│   ├── L01_Preprocessing_Feature_Engineering.ipynb
│   ├── L02_PD_Model_Scorecard.ipynb
│   ├── L03_LGD_EAD_Expected_Loss.ipynb
│   └── L04_Population_Stability_Index.ipynb
│
├── infrastructure/
│   ├── postgres/init.sql
│   ├── airflow/Dockerfile
│   ├── spark/Dockerfile
│   ├── mlflow/Dockerfile
│   └── grafana/dashboards/
│
├── dags/
│   ├── ingestion_dag.py
│   ├── cleaning_dag.py             # NEW: separate cleaning DAG
│   ├── preprocessing_dag.py
│   ├── feature_engineering_dag.py
│   ├── pd_model_training_dag.py
│   ├── lgd_ead_model_training_dag.py
│   ├── batch_scoring_dag.py
│   └── monitoring_dag.py
│
├── spark_jobs/
│   ├── ingest_raw.py
│   ├── clean_loans.py              # NEW: dedicated cleaning job
│   ├── eda_insights.py             # NEW: business EDA job
│   ├── compute_woe.py
│   ├── create_dummies.py
│   └── batch_score.py
│
├── dbt/
│   ├── models/staging/
│   ├── models/features/
│   └── models/risk/
│
├── ml/
│   ├── preprocessing/
│   │   ├── woe_encoder.py
│   │   ├── fine_classer.py         # NEW: fine classing for continuous vars
│   │   └── feature_pipeline.py
│   ├── models/
│   │   ├── pd_model.py             # Updated: uses statsmodels for p-values
│   │   ├── lgd_model.py
│   │   └── ead_model.py
│   ├── evaluation/
│   │   ├── metrics.py              # Updated: +Brier Score, +decile analysis
│   │   └── scorecard.py
│   └── training/
│       ├── train_pd.py
│       ├── train_lgd.py
│       └── train_ead.py
│
├── api/
│   ├── Dockerfile
│   ├── main.py
│   ├── routers/score.py
│   └── schemas/loan_application.py
│
├── risk/
│   ├── expected_loss.py
│   ├── credit_policy.py            # NEW: ROI-based credit policy, risk classes
│   ├── psi_monitor.py
│   └── regulatory_report.py
│
├── data_quality/
│   ├── raw_suite.json
│   ├── staging_suite.json
│   └── features_suite.json
│
└── tests/
    ├── unit/
    ├── integration/
    └── model/
```

---

## 4. Learning Notebooks Path (L01–L04)

Before building the production pipeline, these four notebooks teach the full credit risk workflow on the actual Lending Club dataset. Run them in order.

| Notebook | Topic | Dataset Phase | Key Outputs |
|----------|-------|---------------|-------------|
| **L01** | Preprocessing & Feature Engineering | 2007–2014 raw | Cleaned data (parquet), WoE bins, dummy variables |
| **L02** | PD Model & Scorecard | 2007–2014 processed | Logistic model, scorecard CSV, credit scores, cut-off analysis |
| **L03** | LGD, EAD & Expected Loss | 2007–2014 defaulted loans | LGD model (2-stage), EAD model, portfolio EL, credit policy |
| **L04** | Population Stability Index | 2015 monitoring data | PSI per feature, score PSI, stability verdict |

### Data Split Strategy (Improvement #1 — Out-of-Time Split)

Unlike a random train/test split, this project uses an **out-of-time (OOT) split**, which is the gold standard for credit risk models:

```
2007–2014 data  →  Training set  (fit WoE bins, train all models)
2015 data       →  Test / OOT set (evaluate model on future data)
```

This mirrors how models are actually used in production: they are trained on past data and must generalize to future applicants. A random split would allow information from the future to leak into the training set through shared statistical patterns.

---

## Part A — Data Engineering

---

### A1. Infrastructure Setup (Docker)

```yaml
# docker-compose.yml — key services
services:
  postgres:        # Data warehouse
  minio:           # Data lake (S3-compatible)
  spark-master:    # Big data processing
  spark-worker:
  airflow-webserver:
  airflow-scheduler:
  mlflow:          # ML tracking & registry
  api:             # FastAPI scoring service
  redis:           # Feature cache
  prometheus:      # Metrics collection
  grafana:         # Dashboards & alerting
```

---

### A2. Database Design — Five Schemas

```sql
CREATE SCHEMA raw;        -- Bronze: untouched CSVs loaded as-is
CREATE SCHEMA staging;    -- Silver: cleaned, validated, type-corrected
CREATE SCHEMA features;   -- Gold: WoE bins, dummy variables, feature store
CREATE SCHEMA models;     -- Predictions: PD scores, LGD, EAD outputs
CREATE SCHEMA risk;       -- EL calculations, PSI, regulatory reports
CREATE SCHEMA audit;      -- Pipeline run logs, data lineage
```

Key tables added in v2:
- `staging.loans_cleaned` — now includes `dataset_split = 'train'|'oot'` (out-of-time flag)
- `staging.business_insights` — summary EDA statistics for reporting
- `features.woe_bins` — WoE bins fitted on training set ONLY
- `risk.credit_policy_decisions` — NEW: stores risk class, ROI, decision per loan
- `risk.risk_classes` — NEW: 10-class rating scale (AA → F)

---

### A3. Data Ingestion Pipeline

PySpark reads multiple annual CSV files from MinIO and loads them into `raw.loan_applications`. The key addition in v2 is tracking the `year` of each loan for the out-of-time split.

---

### A4. NEW — Data Cleaning Phase (Improvement #2)

A dedicated cleaning job runs before any feature engineering. This mirrors what both reference projects do — raw data is never used directly for modeling.

**Cleaning steps:**
1. **Remove high-missing features** — drop columns with >50% missing values
2. **Remove irrelevant features** — loan IDs, URLs, free-text fields, policy codes
3. **Remove data leakage features** — variables only known after loan issuance (total_pymnt, recoveries, etc. are excluded from PD model inputs)
4. **Fix data types** — parse dates, convert strings to numeric (emp_length, term, int_rate)
5. **Create derived features** — months since issue date, months since earliest credit line
6. **Create target variables** — good_bad (PD), recovery_rate (LGD), ccf (EAD)
7. **Handle outliers** — cap extreme values in annual_inc, dti
8. **Memory optimization** — downcast numeric types, save to parquet

```python
# spark_jobs/clean_loans.py
def clean_lending_club_data(df):
    # 1. Drop high-missing columns (>50% null)
    missing_rates = df.select([
        (F.count(F.when(F.col(c).isNull(), c)) / F.count('*')).alias(c)
        for c in df.columns
    ]).collect()[0].asDict()
    cols_to_drop = [c for c, rate in missing_rates.items() if rate > 0.5]
    df = df.drop(*cols_to_drop)

    # 2. Drop leakage / irrelevant columns
    leakage_cols = ['total_pymnt', 'total_rec_prncp', 'total_rec_int',
                    'recoveries', 'collection_recovery_fee', 'last_pymnt_d',
                    'out_prncp', 'out_prncp_inv']  # known only post-default
    df = df.drop(*[c for c in leakage_cols if c in df.columns])

    # 3. Parse employment length
    df = df.withColumn('emp_length_int',
        F.regexp_extract('emp_length', r'(\d+)', 1).cast('int'))

    # 4. Parse term
    df = df.withColumn('term_int',
        F.regexp_extract('term', r'(\d+)', 1).cast('int'))

    # 5. Compute months since issue date
    df = df.withColumn('mths_since_issue_d',
        F.months_between(F.current_date(),
                         F.to_date('issue_d', 'MMM-yyyy')).cast('int'))

    # 6. Create good_bad target (1=good, 0=bad/defaulted)
    bad_statuses = ['Charged Off', 'Default',
                    'Does not meet the credit policy. Status:Charged Off',
                    'Late (31-120 days)']
    df = df.withColumn('good_bad',
        F.when(F.col('loan_status').isin(bad_statuses), 0).otherwise(1))

    # 7. Create recovery_rate for LGD (only on charged-off loans)
    df = df.withColumn('recovery_rate',
        F.when(F.col('loan_status') == 'Charged Off',
               F.col('recoveries') / F.col('funded_amnt')).otherwise(F.lit(None)))

    # 8. Create CCF for EAD
    df = df.withColumn('ccf',
        F.when(F.col('loan_status') == 'Charged Off',
               (F.col('funded_amnt') - F.col('total_pymnt')) / F.col('funded_amnt')
               ).otherwise(F.lit(None)))

    # 9. Out-of-time split flag
    df = df.withColumn('year',
        F.year(F.to_date('issue_d', 'MMM-yyyy')))
    df = df.withColumn('dataset_split',
        F.when(F.col('year') <= 2014, 'train').otherwise('oot'))

    return df
```

---

### A5. Business EDA Phase (Improvement #3)

A dedicated EDA job computes business insights before feature engineering. Results are stored in `staging.business_insights` and surfaced in Grafana dashboards.

**Key EDA metrics computed:**
- Default rate overall and by grade, purpose, term, state
- Distribution of funded amounts, interest rates, DTI, annual income
- Monotonicity check: default rate vs each variable (validates WoE approach)
- Time trend of loan volume and default rate by year

---

### A6. Feature Engineering Pipeline

All WoE computation and dummy variable creation runs only on the **training set** (`dataset_split = 'train'`). The fitted bins are then stored and applied to the OOT set — no re-fitting on test data.

**New in v2 — Missing values as a WoE category (Improvement #4):**

```python
# Missing values are not dropped or imputed — they are treated as
# a separate category in WoE analysis. This is because missing values
# often signal a specific borrower behavior (e.g., no delinquency record
# may mean the borrower is new, not that they are clean).
df = df.fillna({'mths_since_last_delinq': -999,
                'mths_since_last_record': -999})
# -999 becomes its own WoE bin in fine classing
```

---

### A7. Airflow DAG Orchestration

```
ingestion_dag
    └──► cleaning_dag          (NEW in v2)
              └──► eda_dag     (NEW in v2)
                    └──► feature_engineering_dag
                              ├──► pd_model_training_dag
                              └──► lgd_ead_model_training_dag
                                          └──► batch_scoring_dag
                                                      └──► monitoring_dag
```

---

## Part B — Machine Learning

---

### B1. ML Infrastructure (MLflow)

All experiments logged to MLflow. Promotion requires passing all governance checkpoints before any model moves to Production.

```
Experiment Run → [Staging] → Risk Committee Review → [Production]
```

---

### B2. PD Model Pipeline (Updated)

#### Key change: Statsmodels for p-values (Improvement #5)

Instead of approximating p-values from sklearn's logistic regression, we use **statsmodels** directly, which provides proper Wald test p-values and confidence intervals — required for regulatory documentation.

```python
import statsmodels.api as sm

# Add constant for intercept
X_train_const = sm.add_constant(X_train[features])

# Fit with statsmodels
logit_model = sm.Logit(y_train, X_train_const)
result = logit_model.fit(method='bfgs', maxiter=300)

# P-values are directly available
print(result.summary())
# result.pvalues gives proper Wald test p-values
# result.conf_int() gives 95% confidence intervals

# Select features where p-value < 0.05
significant_features = result.pvalues[result.pvalues < 0.05].index.tolist()
significant_features = [f for f in significant_features if f != 'const']
```

#### Feature selection loop

```python
# Iteratively remove least significant variable until all p-values < 0.05
while True:
    X_const = sm.add_constant(X_train[features])
    result = sm.Logit(y_train, X_const).fit(disp=0)
    max_pval = result.pvalues.drop('const').max()
    if max_pval < 0.05:
        break
    # Remove the variable with highest p-value
    worst_var = result.pvalues.drop('const').idxmax()
    features.remove(worst_var)
```

#### Updated Evaluation Metrics (Improvement #6)

```python
from sklearn.metrics import roc_auc_score, brier_score_loss
from scipy.stats import ks_2samp

def evaluate_pd_model(y_true, y_pred_proba):
    auc   = roc_auc_score(y_true, y_pred_proba)
    gini  = 2 * auc - 1
    ks    = ks_2samp(y_pred_proba[y_true==1], y_pred_proba[y_true==0]).statistic
    brier = brier_score_loss(y_true, y_pred_proba)  # NEW: calibration check

    return {"auc": auc, "gini": gini, "ks": ks, "brier": brier}

# Interpretation:
# Brier score: lower is better. < 0.1 = well-calibrated model
# Gini > 0.4 on OOT set = satisfactory for retail credit
# KS > 0.3 = good separation between good and bad borrowers
```

#### Decile Analysis (Improvement #7)

```python
# Split predictions into 10 equal-sized buckets (deciles)
# Verify that bad rate decreases monotonically from decile 1 to 10
df_eval['decile'] = pd.qcut(df_eval['pd_score'], q=10,
                             labels=range(10, 0, -1))

decile_table = df_eval.groupby('decile').agg(
    n_obs=('good_bad', 'count'),
    n_bad=('good_bad', lambda x: (x == 0).sum()),
    bad_rate=('good_bad', lambda x: (x == 0).mean()),
    avg_score=('pd_score', 'mean')
).reset_index()

# A valid model shows: decile 1 (worst scores) has highest bad rate
# Top 3 deciles should capture >50% of all bad borrowers
```

#### Scorecard & Credit Score

```python
# Scorecard scaling: min=300, max=850 (industry-standard range)
# ref_score=600 at odds of 1:1 (equal good/bad)
# pdo=20 (20 points to double the odds of being good)

factor = 20 / np.log(2)   # ≈ 28.85
offset = 600 - factor * np.log(1)  # = 600

# For each dummy variable:
# Score contribution = -(coefficient × factor)
# Higher score = lower PD = better borrower
```

#### 10 Risk Classes & ROI Credit Policy (Improvement #8)

```python
# 10 risk classes based on credit score bands
risk_classes = {
    'AA': (780, 850),   # Lowest PD → auto-approve
    'A':  (740, 779),   # Very low PD → auto-approve
    'AB': (700, 739),   # Low PD → approve if ROI > base rate
    'BB': (660, 699),   # Moderate PD → approve if ROI > base rate
    'B':  (620, 659),   # Moderate-high PD → approve if ROI > base rate
    'BC': (580, 619),   # High PD → approve if ROI > base rate
    'C':  (540, 579),   # High PD → approve if ROI > base rate
    'CD': (500, 539),   # Very high PD → approve if ROI > base rate
    'DD': (460, 499),   # Very high PD → manual review
    'F':  (300, 459),   # Highest PD → auto-reject
}

# ROI-based credit policy
def compute_annualized_roi(int_rate, term_months, pd, lgd, funded_amnt):
    """
    Expected ROI = Interest income − Expected Loss
    Annualized to compare against the risk-free rate
    """
    expected_interest = funded_amnt * int_rate * (term_months / 12)
    expected_loss     = pd * lgd * funded_amnt
    net_return        = expected_interest - expected_loss
    roi               = net_return / funded_amnt / (term_months / 12)
    return roi

US_BASE_RATE = 0.0215  # US Fed rate at time of data

def credit_decision(risk_class, annualized_roi):
    if risk_class in ('AA', 'A'):
        return 'AUTO_APPROVE'
    elif risk_class == 'F':
        return 'AUTO_REJECT'
    elif annualized_roi > US_BASE_RATE:
        return 'APPROVE'
    else:
        return 'REJECT'
```

---

### B3. LGD Model Pipeline (Updated)

#### Beta Regression consideration (Improvement #9)

```python
# Recovery Rate and CCF are both bounded in [0, 1] — beta distribution
# Beta regression is theoretically more appropriate than linear regression.
# However, in practice, linear regression achieves similar results and
# avoids the need to handle exact 0 and 1 values (which require adjustments
# like replacing with 0.0001/0.9999).
# This project uses linear regression for simplicity and replicability,
# but a beta regression is documented here for completeness.

# Beta regression alternative (using statsmodels):
# from statsmodels.othermod.betareg import BetaModel
# beta_model = BetaModel(y_stage2, X_stage2).fit()

# Decision: proceed with linear regression (same MAE, simpler pipeline)
```

The two-stage LGD model remains:
- **Stage 1** — Logistic regression: P(Recovery Rate > 0)
- **Stage 2** — Linear regression: E[Recovery Rate | RR > 0]
- **Combined** — LGD = 1 − (Stage1 × Stage2)

---

### B4. EAD Model Pipeline

Linear regression on Credit Conversion Factor (CCF). Predictions clipped to [0, 1].

---

### B5. Model Serving API

FastAPI service returns full scoring response per loan application:

```json
{
  "loan_id": "LC123456",
  "pd": 0.0421,
  "lgd": 0.6200,
  "ead": 12500.00,
  "expected_loss": 326.55,
  "credit_score": 672,
  "risk_class": "BB",
  "annualized_roi": 0.0387,
  "decision": "APPROVE",
  "model_version": "2.0"
}
```

---

### B6. Future Model Improvements (Improvement #10)

When the PD model's Gini degrades or PSI signals population drift, the next iteration should:

1. **Use gradient boosting** (XGBoost or LightGBM) for higher predictive power
2. **Apply SHAP values** for feature importance and model explainability
3. **Apply LIME** for individual loan decision explanations
4. **Re-calibrate with Platt scaling** if Brier Score degrades
5. **Retrain on expanded dataset** incorporating new population characteristics

```python
# Future: SHAP explainability
import shap
explainer = shap.LinearExplainer(model, X_train)
shap_values = explainer.shap_values(X_test)
shap.summary_plot(shap_values, X_test)

# Individual loan explanation
shap.force_plot(explainer.expected_value, shap_values[0], X_test.iloc[0])
```

---

## Part C — Risk Management

---

### C1. Expected Loss Calculation

```python
# EL = PD × LGD × EAD
expected_loss = pd_predicted * lgd_predicted * ead_predicted

# Portfolio summary
portfolio_el_rate = expected_loss.sum() / ead_predicted.sum()
```

---

### C2. 10 Risk Classes & Credit Policy

Portfolio segmented into 10 risk bands. Credit decisions combine:
- Score-based auto-approve/reject (AA/A = approve; F = reject)
- ROI-based approval for middle bands (ROI > US base rate)

Result from reference project applying this policy:
- Default rate reduced from 6.71% → 5.65%
- Expected Loss rate reduced from 6.91% → 5.77%
- Achieved by rejecting only 11% of loans (F class + negative ROI)

---

### C3. Model Monitoring & PSI

PSI computed daily for each model input variable and for credit scores:

| PSI Value | Status | Action |
|-----------|--------|--------|
| < 0.10 | STABLE | Continue as-is |
| 0.10–0.25 | MONITOR | Investigate root cause |
| > 0.25 | ALERT | Consider model redevelopment |

Score PSI is particularly important — if the score distribution shifts significantly (PSI > 0.19 as seen in the reference project), it may indicate the model needs to be rebuilt.

---

### C4. IFRS 9 & Basel III Regulatory Reporting

- **Stage 1:** 12-month ECL (PD < 0.02)
- **Stage 2:** Lifetime ECL (0.02 ≤ PD < 0.15)
- **Stage 3:** Lifetime ECL, already defaulted (PD ≥ 0.15)
- **Capital requirement:** RWA × 8% minimum under Basel III AIRB

---

## 8. End-to-End Data Flow

```
Lending Club Dataset (CSV — 2007–2015, 2.5M rows)
         │
         ▼  ingestion_dag
  MinIO: s3a://landing-zone/lending_club/raw/*.csv
         │
         ▼  cleaning_dag (NEW)
  PostgreSQL: staging.loans_cleaned
  • Type fixes, leakage removal, target creation
  • Out-of-time split: train=2007–2014 / oot=2015
  • Parquet backup to MinIO for Spark
         │
         ▼  eda_dag (NEW)
  PostgreSQL: staging.business_insights
  • Default rate by grade, purpose, term
  • Distribution summaries for reporting
         │
         ▼  feature_engineering_dag
  PostgreSQL: features.woe_bins (train only)
  PostgreSQL: features.information_values
  PostgreSQL: features.loan_features_encoded
  • WoE/IV computed on training set
  • Missing values → separate WoE category
  • Same bins applied to OOT set
         │
         ├──► pd_model_training_dag
         │    MLflow: PD Logistic Regression (statsmodels)
         │    • Iterative p-value feature selection
         │    • AUC, Gini, KS, Brier Score logged
         │    • Decile analysis
         │    • Scorecard (300–850 scale)
         │    • 10 risk classes
         │
         └──► lgd_ead_model_training_dag
              MLflow: LGD Stage1 (Logistic) + Stage2 (Linear)
              MLflow: EAD Linear Regression
              • MAE, R² logged
              • Beta regression documented as alternative
         │
         ▼  MLflow Model Registry
  Staging → Risk Committee Review → Production
         │
         ▼  FastAPI /score endpoint
  Real-time scoring: PD + LGD + EAD + EL + risk_class + decision + ROI
         │
         ▼  risk/expected_loss.py
  risk.expected_loss — per-loan EL
  risk.credit_policy_decisions — decision audit trail
  risk.ifrs9_provisions — regulatory reporting
         │
         ▼  monitoring_dag (daily)
  risk.population_stability — PSI per feature + score
  Prometheus → Grafana alerts on PSI > 0.25
```

---

## 9. Implementation Roadmap

| Sprint | Duration | Deliverable |
|--------|----------|-------------|
| **Sprint 0** | 1 week | Run L01–L04 notebooks on Lending Club data; understand full flow |
| **Sprint 1** | 2 weeks | Docker environment; PostgreSQL schemas; MinIO buckets; Airflow DAGs scaffolded |
| **Sprint 2** | 2 weeks | PySpark ingestion + cleaning DAG; parquet output; Great Expectations on raw data |
| **Sprint 3** | 2 weeks | EDA DAG; business insights to database; out-of-time split confirmed |
| **Sprint 4** | 3 weeks | WoE/IV pipeline (missing-as-category); coarse classes; dummy variables in feature store |
| **Sprint 5** | 2 weeks | PD model (statsmodels); feature selection; Gini > 0.40 on OOT; scorecard; 10 risk classes |
| **Sprint 6** | 2 weeks | LGD two-stage model; EAD model; ROI credit policy; all models in MLflow |
| **Sprint 7** | 2 weeks | FastAPI scoring service; Redis cache; real-time endpoint with full credit decision |
| **Sprint 8** | 2 weeks | EL calculation; IFRS 9 staging; Basel III capital report |
| **Sprint 9** | 2 weeks | PSI monitoring DAG; Grafana dashboards; score PSI alert |
| **Sprint 10** | 1 week | Documentation; SR 11-7 model governance report; integration tests |

**Total: ~21 weeks**

---

## 10. Key Improvements vs Original Plan

| # | Improvement | Source | Impact |
|---|------------|--------|--------|
| 1 | **Out-of-time split** (2007–14 train / 2015 OOT) | Both repos | Prevents look-ahead bias; models test on truly future data |
| 2 | **Separate data cleaning phase** | allmeidaapedro | Cleaner pipeline; parquet memory optimization |
| 3 | **Business EDA** with insights before modeling | allmeidaapedro | Better feature understanding; regulatory documentation |
| 4 | **Missing values as WoE category** | allmeidaapedro | Higher accuracy; captures behavioral signal in missings |
| 5 | **Statsmodels** for p-values | allmeidaapedro | Proper Wald test; confidence intervals for regulators |
| 6 | **Brier Score** added to metrics | allmeidaapedro | Checks probability calibration, not just discrimination |
| 7 | **Decile analysis** for score validation | allmeidaapedro | Validates score ordering; required for scorecard acceptance |
| 8 | **10 risk classes + ROI credit policy** | allmeidaapedro | More nuanced credit decisions; quantified business impact |
| 9 | **Beta regression** documented for LGD/EAD | allmeidaapedro | Theoretically correct; documented as alternative |
| 10 | **SHAP/LIME** as next-iteration steps | allmeidaapedro | Future explainability for boosting models |

---

## Key Model Governance Checkpoints

| Checkpoint | Threshold | Owner |
|-----------|-----------|-------|
| PD model Gini (OOT set) | ≥ 0.40 | Model Validation |
| PD model KS (OOT set) | ≥ 0.25 | Model Validation |
| PD model Brier Score | ≤ 0.10 | Model Validation |
| Decile ordering check | Monotonic bad rate | Model Validation |
| LGD Stage 1 AUC | ≥ 0.60 | Model Validation |
| LGD Stage 2 MAE | ≤ 0.10 | Model Validation |
| EAD MAE | ≤ 0.15 | Model Validation |
| PSI all features | < 0.25 | Risk Management |
| Score PSI | < 0.19 | Risk Management |
| Data quality pass rate | 100% | Data Engineering |
| API p99 latency | < 200ms | Engineering |
| Documentation | SR 11-7 complete | Risk Officer |

---

# APPENDIX — Dataset-Specific Updates (v3)
**Based on actual dataset audit: `accepted_2007_to_2018Q4.csv`**

---

## Confirmed Dataset Facts

| Property | Value |
|----------|-------|
| File | `data/raw/accepted_2007_to_2018Q4.csv` |
| Total rows | ~2,260,701 |
| Total columns | 151 |
| Date range | 2007–2018 (file NOT sorted chronologically — use `issue_year` to filter) |
| Default rate | ~17% (Charged Off) |
| `term` format | `" 36 months"` string → needs strip + int conversion |
| `int_rate` format | `13.99` (percent) → needs divide by 100 |
| `revol_util` format | `29.7` (percent) → needs divide by 100 |
| `earliest_cr_line` format | `"Aug-2003"` (MMM-YYYY) → needs `pd.to_datetime(format='%b-%Y')` |
| `mths_since_last_delinq` | Actual `NaN` (not -1 sentinel) → fill with -1 before WoE |
| `mths_since_last_record` | 82% null → fill with -1 before WoE |
| 100% null columns | 15 (all `sec_app_*`, `member_id`, `desc`, `revol_bal_joint`) |

---

## Column Summary

| Category | Count | Action |
|----------|-------|--------|
| 100% null | 15 | Drop immediately |
| Identifiers/constants | 8 | Drop |
| Joint application (>99% null) | 3 | Drop |
| Hardship/settlement (>97% null) | 18 | Drop |
| Post-application leakage (PD) | 15 | Create targets first, then drop |
| Near-zero variance | 7 | Drop |
| **Total dropped** | **~57** | |
| Kept for modeling | ~46 | Keep + convert |
| NEW target variables | 3 | `good_bad`, `recovery_rate`, `ccf` |
| NEW derived features | 6 | `term_int`, `emp_length_int`, `int_rate` (/100), `mths_since_issue_d`, `mths_since_earliest_cr_line`, `fico_score` |
| **Final WoE dummy columns** | **~50–60** | Input to logistic regression |

---

## Out-of-Time Split (Updated for 2007–2018)

```python
# CORRECT split for 2007-2018 dataset
# NOTE: file is NOT sorted by date — always filter by issue_year
train = df[df['issue_year'] <= 2015]   # ~1.3M rows  (2007–2015)
test  = df[df['issue_year'] >= 2016]   # ~960K rows  (2016–2018)
```

| Split | Years | Approx. Rows | Role |
|-------|-------|-------------|------|
| **Train** | 2007–2015 | ~1.3M | Fit WoE bins, train all models |
| **OOT Test** | 2016–2018 | ~960K | Evaluate on future unseen data |

> 3 years of OOT validation vs. 1 year in the original course — more robust.

---

## Key Preprocessing Differences vs GitHub Projects

```python
# GitHub clean sample (NOT needed for our raw CSV):
# df['term_int'] = pd.to_numeric(df['term'].str.replace(' months',''))  ← SAME

# Our raw CSV — additional steps:
df['int_rate']   = df['int_rate']   / 100        # 13.99 → 0.1399
df['revol_util'] = df['revol_util'] / 100        # 29.7  → 0.297

# Date parsing — different format than course dataset
df['earliest_cr_line'] = pd.to_datetime(df['earliest_cr_line'],
                                         format='%b-%Y')  # "Aug-2003"

# Missing sentinel — must fill NaN (NOT -1 like in clean sample)
df['mths_since_last_delinq'] = df['mths_since_last_delinq'].fillna(-1)
df['mths_since_last_record']  = df['mths_since_last_record'].fillna(-1)

# FICO score — available in this dataset (advantage over GitHub)
df['fico_score'] = (df['fico_range_low'] + df['fico_range_high']) / 2
```

---

## Additional Variables Not in GitHub Projects

These are in our dataset but not used in levist7 or allmeidaapedro:

| Variable | Why it helps |
|----------|-------------|
| `fico_score` | FICO is one of the strongest default predictors (expected IV > 0.30) |
| `bc_util` | Bankcard utilization — captures credit stress beyond `revol_util` |
| `pct_tl_nvr_dlq` | % accounts never delinquent — strong behavioral signal |
| `mort_acc` | Homeowners with mortgages tend to be more stable |
| `num_accts_ever_120_pd` | Serious delinquency history — very predictive |
| `acc_open_past_24mths` | Recent credit-seeking behavior |
| `tot_cur_bal` | Total debt burden across all accounts |

---

## Pipeline DAG Update for 2007–2018

```
accepted_2007_to_2018Q4.csv (151 cols, 2.26M rows)
    ↓ ingestion_dag (PySpark)
    raw.loan_applications (PostgreSQL)
    ↓ cleaning_dag — targets first, then drop 57 cols
    staging.loans_cleaned (94 cols)
    ↓ feature_engineering_dag — OOT split at 2015
    features.woe_bins (fitted on 2007–2015 only)
    features.loan_features_encoded (~50 WoE dummies)
    ↓ pd_model_training_dag (statsmodels logistic regression)
    models.pd_predictions + scorecard.csv
    ↓ lgd_ead_model_training_dag
    models.lgd_predictions + models.ead_predictions
    ↓ batch_scoring_dag
    risk.expected_loss (per loan: PD × LGD × EAD)
    ↓ monitoring_dag (daily, using OOT data)
    risk.population_stability (PSI per variable + score PSI)
```

---

# APPENDIX — Version 3 Improvements
**Sourced from: `research.md` deep-dives + `Literature_review_V2.md` gap analysis**

> These additions close the gap between offline model benchmarking (where most Lending Club papers stop) and a production-grade, regulatory-compliant credit risk system. Each improvement is mapped to the plan section it extends.

---

## V3-1. Unexpected Loss, Economic Capital & RAROC  *(extends C1)*

**Gap:** The plan covers Expected Loss (EL = PD × LGD × EAD) but stops there. Banks also hold capital against *Unexpected Loss* and measure risk-adjusted performance via RAROC. The `research.md` EL/UL section (§9) covers this in detail; nothing equivalent exists in the plan.

**What to add — `risk/economic_capital.py`:**

```python
from scipy.stats import norm
import numpy as np

def irb_capital_requirement(pd, lgd, ead, rho=None, maturity=1.0):
    """
    Basel III AIRB retail IRB formula.
    rho (asset correlation) for retail = 0.03 + 0.16*(1 - exp(-35*pd)) / (1 - exp(-35))
    Returns K (capital per unit EAD) and RWA.
    """
    if rho is None:
        # Retail revolving asset correlation formula
        rho = 0.03 + 0.16 * (1 - np.exp(-35 * pd)) / (1 - np.exp(-35))

    g_pd  = norm.ppf(pd)
    g_999 = norm.ppf(0.999)
    worst_case_pd = norm.cdf((g_pd + np.sqrt(rho) * g_999) / np.sqrt(1 - rho))
    K   = lgd * (worst_case_pd - pd)          # unexpected loss per unit EAD
    rwa = K * 12.5 * ead                       # 12.5 = 1 / 8% minimum CAR
    return {"K": K, "rwa": rwa, "capital": K * ead}

def raroc(net_revenue, expected_loss, economic_capital):
    """
    Risk-Adjusted Return on Capital.
    RAROC = (Net Revenue - EL) / Economic Capital
    Target: RAROC > cost-of-equity (typically 10–15%)
    """
    return (net_revenue - expected_loss) / economic_capital
```

**New database table:** `risk.economic_capital` — per-loan K, RWA, capital, RAROC.

**New governance checkpoint:**

| Metric | Threshold | Owner |
|--------|-----------|-------|
| Portfolio RAROC | > 10% (cost of equity) | Risk Management |
| Average RWA density | Plausible vs Standardized Approach | Model Validation |

---

## V3-2. IFRS 9 SICR Rule — Replace Hardcoded PD Thresholds  *(extends C4)*

**Gap:** The current plan uses fixed PD bands (Stage 1: PD < 0.02, Stage 2: 0.02–0.15, Stage 3: PD ≥ 0.15). The `research.md` IFRS 9 section (§28) explicitly states:

> *"IFRS 9 does not fix a hard PD threshold; it's based on SICR, not a specific number."*

SICR must combine **relative PD change since origination** + **30 DPD backstop** + **qualitative watchlist flags**. The PD bands in C4 should be documented as internal policy approximations, not IFRS 9 requirements.

**What to add — `risk/ifrs9_staging.py`:**

```python
def classify_stage(pd_current, pd_at_origination, days_past_due,
                   watchlist_flag=False,
                   pd_relative_threshold=2.0,   # 2× increase = SICR
                   pd_absolute_threshold=0.02,   # absolute floor for SICR
                   dpd_backstop=30):
    """
    Three-stage IFRS 9 classification per EBA/GL/2017/06.

    Stage 3 — credit-impaired (objective evidence of default):
        90+ DPD OR charge-off/restructuring event
    Stage 2 — SICR (Significant Increase in Credit Risk):
        - Relative PD has doubled OR
        - Absolute PD rose by > 2pp since origination OR
        - 30 DPD backstop (rebuttable presumption) OR
        - Watchlist / forbearance flag
    Stage 1 — performing:
        No SICR, no impairment
    """
    # Stage 3: credit-impaired
    if days_past_due >= 90:
        return 3, "90+ DPD"

    # Stage 2: SICR triggers
    pd_ratio   = pd_current / pd_at_origination if pd_at_origination > 0 else 1
    pd_change  = pd_current - pd_at_origination

    sicr_relative = pd_ratio   >= pd_relative_threshold
    sicr_absolute = pd_change  >= pd_absolute_threshold
    sicr_backstop = days_past_due >= dpd_backstop
    sicr_watchlist = watchlist_flag

    if any([sicr_relative, sicr_absolute, sicr_backstop, sicr_watchlist]):
        reason = (f"ratio={pd_ratio:.1f}x" if sicr_relative else
                  f"abs_change={pd_change:.3f}" if sicr_absolute else
                  f"DPD={days_past_due}" if sicr_backstop else "watchlist")
        return 2, reason

    return 1, "performing"
```

**Staging audit trail:** Every stage assignment stored in `risk.ifrs9_provisions` with the trigger reason — required for auditor review.

---

## V3-3. Through-the-Cycle vs Point-in-Time PD Calibration  *(extends B2 + C4)*

**Gap:** The plan trains one logistic regression model and uses its output probability directly for both Basel capital (C4) and IFRS 9 provisioning (C4). These require *different* PD calibrations:

| Use | Calibration | Horizon | Sensitivity |
|-----|------------|---------|-------------|
| **Basel AIRB capital** | Through-the-Cycle (TtC) | Long-run average | Low (stable across cycles) |
| **IFRS 9 ECL Stage 1** | Point-in-Time (PiT) | 12-month forward | High (moves with economy) |
| **IFRS 9 ECL Stage 2/3** | PiT + macro-adjusted | Lifetime | Very high |

**What to add — `ml/models/pd_calibration.py`:**

```python
def calibrate_ttc(pd_pit, long_run_default_rate, sample_default_rate):
    """
    Shift PiT PD toward long-run average for Basel TtC capital PD.
    Simple Platt scaling / intercept shift approach.
    """
    shift = np.log(long_run_default_rate / (1 - long_run_default_rate)) - \
            np.log(sample_default_rate  / (1 - sample_default_rate))
    log_odds_ttc = np.log(pd_pit / (1 - pd_pit)) + shift
    return 1 / (1 + np.exp(-log_odds_ttc))

def apply_macro_overlay(pd_pit, gdp_growth_forecast, unemployment_forecast,
                        gdp_sensitivity=-0.8, unemp_sensitivity=0.5):
    """
    Forward-looking macro adjustment for IFRS 9 ECL.
    Sensitivities calibrated from historical PD vs macro regressions.
    """
    macro_adj = gdp_sensitivity * gdp_growth_forecast + \
                unemp_sensitivity * unemployment_forecast
    log_odds_adj = np.log(pd_pit / (1 - pd_pit)) + macro_adj
    return 1 / (1 + np.exp(-log_odds_adj))
```

**New MLflow parameters to log:** `pd_calibration_type` = `"PiT"` | `"TtC"` | `"PiT_macro"`.

---

## V3-4. Lifetime PD & IFRS 9 Scenario-Weighted ECL  *(extends C4)*

**Gap:** IFRS 9 Stages 2 and 3 require **lifetime ECL**, but the plan only computes 12-month ECL. The literature review (§2.4) notes this duality is never demonstrated on a public dataset.

**What to add — `risk/lifetime_pd.py`:**

```python
def term_structure_pd(pd_1yr, num_years, survival_decay=0.85):
    """
    Approximate lifetime PD term structure using survival analysis.
    P(default in year t) = (1 - pd_1yr)^(t-1) * pd_1yr  [geometric hazard]
    Lifetime PD = 1 - prod(1 - pd_t) for t = 1..T
    survival_decay: accounts for PD declining for surviving good borrowers.
    """
    conditional_pds = [pd_1yr * (survival_decay ** (t - 1)) for t in range(1, num_years + 1)]
    survival = 1.0
    lifetime_pd = 0.0
    for cpd in conditional_pds:
        marginal = survival * cpd
        lifetime_pd += marginal
        survival *= (1 - cpd)
    return lifetime_pd

def scenario_weighted_ecl(pd_base, pd_up, pd_down, lgd, ead, loan_term_years,
                           w_base=0.50, w_up=0.30, w_down=0.20):
    """
    Probability-weighted ECL across three macroeconomic scenarios.
    Required by IFRS 9 paragraph 5.5.17.
    """
    ecl_base = term_structure_pd(pd_base, loan_term_years) * lgd * ead
    ecl_up   = term_structure_pd(pd_up,   loan_term_years) * lgd * ead
    ecl_down = term_structure_pd(pd_down, loan_term_years) * lgd * ead
    return w_base * ecl_base + w_up * ecl_up + w_down * ecl_down
```

**New Airflow DAG:** `scenario_ecl_dag` — runs quarterly using updated macro forecasts.

---

## V3-5. Reject Inference  *(extends A4 + B2)*

**Gap:** The Lending Club dataset contains only **funded (accepted) loans** — rejected applicants are not observed. A model trained on accepted loans only learns from a biased sample (selection bias). The literature review (§2.3) identifies this as a known limitation; no prior Lending Club paper addresses it. The `research.md` covers this implicitly through its selection bias discussion.

**What to add — `ml/preprocessing/reject_inference.py`:**

```python
def parceling_augmentation(df_accepted, pd_model, reject_pd_threshold=0.30,
                            reject_bad_rate_multiplier=2.0):
    """
    Parceling method (Siddiqi 2006, Chapter 8):
    1. Score accepted applications with the initial PD model.
    2. Infer rejected applications would have been scored ~2× worse.
    3. Assign probabilistic good/bad labels to synthetic rejects.
    4. Retrain model on accepted + augmented rejects.

    This reduces the optimistic bias from training on accepts only.
    """
    df = df_accepted.copy()

    # Step 1: score all accepted loans
    df['pd_initial'] = pd_model.predict_proba(df[features])[:, 1]

    # Step 2: create synthetic rejects (higher PD, assume never funded)
    df_rejects = df[df['pd_initial'] > reject_pd_threshold].copy()
    df_rejects['pd_adjusted'] = (df_rejects['pd_initial'] *
                                  reject_bad_rate_multiplier).clip(0, 1)

    # Step 3: assign probabilistic target
    np.random.seed(42)
    df_rejects['good_bad'] = np.random.binomial(
        1, 1 - df_rejects['pd_adjusted'])

    # Step 4: combine and retrain
    df_combined = pd.concat([df_accepted, df_rejects], ignore_index=True)
    return df_combined
```

**Document limitation:** Add a note in the SR 11-7 model documentation that PD estimates may be optimistically biased due to truncated sample, and that reject inference was applied using the parceling method.

---

## V3-6. Downturn LGD Adjustment  *(extends B3 + C4)*

**Gap:** Basel AIRB requires banks to estimate **downturn LGD** — recovery rates during economic downturns are lower than long-run averages. The plan uses simple average LGD with no downturn adjustment.

**What to add — `ml/models/lgd_model.py` (addition):**

```python
def downturn_lgd(lgd_long_run, recovery_rate_floor=0.10,
                 downturn_haircut=1.25):
    """
    Basel III CRE36 requirement: LGD must reflect economic downturn conditions.
    Conservative approach: scale up LGD by downturn haircut, floor the recovery rate.
    EBA GL/2019/03 allows adding a margin of conservatism (MoC) overlay.
    """
    # Downturn: recovery rates are compressed
    recovery_long_run = 1 - lgd_long_run
    recovery_downturn = max(recovery_long_run / downturn_haircut, recovery_rate_floor)
    lgd_downturn = 1 - recovery_downturn
    return lgd_downturn

# Log both to MLflow:
# mlflow.log_metric("lgd_long_run", lgd_avg)
# mlflow.log_metric("lgd_downturn", downturn_lgd(lgd_avg))
```

**Basel reporting:** Capital RWA uses `lgd_downturn`; IFRS 9 ECL uses `lgd_long_run` (or PiT LGD).

---

## V3-7. Hosmer-Lemeshow Test + Calibration Plot  *(extends B2 evaluation)*

**Gap:** The plan adds Brier Score (good) but stops there. The research.md Brier Score section (§22) and Basel model validation guidance both require an explicit **calibration test** and **reliability diagram** before AIRB approval. A Brier Score alone doesn't show *where* miscalibration occurs.

**What to add — `ml/evaluation/metrics.py` (addition):**

```python
from scipy.stats import chi2
import matplotlib.pyplot as plt

def hosmer_lemeshow_test(y_true, y_pred_proba, n_groups=10):
    """
    Hosmer-Lemeshow goodness-of-fit test for logistic regression.
    H0: model is well-calibrated.
    p-value < 0.05 → reject H0 → model is miscalibrated.
    Required by EBA GL/2017/16 for PD model validation.
    """
    df = pd.DataFrame({'y': y_true, 'p': y_pred_proba})
    df['group'] = pd.qcut(df['p'], q=n_groups, labels=False, duplicates='drop')

    obs_bad  = df.groupby('group')['y'].apply(lambda x: (x == 0).sum())
    obs_good = df.groupby('group')['y'].apply(lambda x: (x == 1).sum())
    exp_bad  = df.groupby('group')['p'].sum()
    exp_good = df.groupby('group').apply(lambda g: (1 - g['p']).sum())

    hl_stat = ((obs_bad - exp_bad)**2 / exp_bad +
               (obs_good - exp_good)**2 / exp_good).sum()
    p_value = 1 - chi2.cdf(hl_stat, df=n_groups - 2)
    return {"hl_stat": hl_stat, "p_value": p_value,
            "calibrated": p_value >= 0.05}

def reliability_diagram(y_true, y_pred_proba, n_bins=10, save_path=None):
    """
    Plot predicted PD vs actual default rate by score decile.
    A well-calibrated model produces points on the 45° diagonal.
    """
    from sklearn.calibration import calibration_curve
    fraction_of_positives, mean_predicted = calibration_curve(
        y_true, y_pred_proba, n_bins=n_bins, strategy='quantile')

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, 1], [0, 1], 'k--', label='Perfect calibration')
    ax.plot(mean_predicted, fraction_of_positives, 's-', label='Model')
    ax.set_xlabel('Mean Predicted PD')
    ax.set_ylabel('Actual Default Rate')
    ax.set_title('Reliability Diagram (Calibration Plot)')
    ax.legend()
    if save_path:
        fig.savefig(save_path)
    return fig
```

**New governance checkpoint:**

| Metric | Threshold | Owner |
|--------|-----------|-------|
| Hosmer-Lemeshow p-value | ≥ 0.05 (calibrated) | Model Validation |
| Reliability diagram | Points within ±1pp of diagonal | Model Validation |

---

## V3-8. Characteristic Stability Index (CSI)  *(extends C3 monitoring)*

**Gap:** The plan monitors PSI at the score and portfolio level. The literature review (§2.6) and GARP/Arthur AI sources both mention **CSI** (per-variable stability) as the companion metric. PSI alone detects that something changed; CSI identifies *which input variable* drove the shift, enabling faster root-cause analysis.

**What to add — `risk/psi_monitor.py` (addition):**

```python
def characteristic_stability_index(train_series, live_series, n_bins=10):
    """
    CSI = PSI applied to a single input variable (before WoE transformation).
    Same thresholds as PSI: <0.10 stable, 0.10-0.25 monitor, >0.25 alert.
    Run for every model input variable in the monitoring_dag.
    """
    bins = pd.qcut(train_series, q=n_bins, duplicates='drop', retbins=True)[1]
    bins[0], bins[-1] = -np.inf, np.inf  # open-ended edges

    train_counts = pd.cut(train_series, bins=bins).value_counts(normalize=True).sort_index()
    live_counts  = pd.cut(live_series,  bins=bins).value_counts(normalize=True).sort_index()

    # Avoid division by zero / log(0)
    train_counts = train_counts.clip(lower=1e-6)
    live_counts  = live_counts.clip(lower=1e-6)

    csi = ((live_counts - train_counts) * np.log(live_counts / train_counts)).sum()
    return csi

# In monitoring_dag: compute CSI for all ~46 model input variables.
# Store results in risk.characteristic_stability with timestamp + alert flag.
```

**Updated monitoring table:**

| Metric | PSI/CSI < 0.10 | 0.10–0.25 | > 0.25 |
|--------|---------------|-----------|--------|
| Score PSI | STABLE | MONITOR | **ALERT: consider rebuild** |
| Feature CSI (each var) | STABLE | MONITOR | **ALERT: investigate drift** |
| AUC on live data | ≥ baseline | Investigate | **ALERT: retrain** |

---

## V3-9. Vintage / Cohort Analysis  *(extends C3 monitoring)*

**Gap:** The OOT split validates the model on one fixed future window (2016–2018). Banks additionally run **vintage analysis** — tracking bad rates by origination cohort over time — to detect portfolio-level deterioration and validate that WoE bins remain stable across origination years.

**What to add — `risk/vintage_analysis.py`:**

```python
def vintage_analysis(df, score_col='credit_score', target_col='good_bad',
                     vintage_col='issue_year', performance_months=12):
    """
    For each origination year (vintage), compute:
    - Default rate at 12 months on book
    - Average credit score at origination
    - Score band distribution
    Enables detection of underwriting drift and score shift over time.
    """
    summary = df.groupby(vintage_col).agg(
        n_loans=(target_col, 'count'),
        default_rate=(target_col, lambda x: (x == 0).mean()),
        avg_score=(score_col, 'mean'),
        pct_AA=(score_col, lambda x: (x >= 780).mean()),
        pct_F=(score_col, lambda x: (x < 460).mean())
    ).reset_index()
    return summary
```

**New Airflow DAG:** `vintage_dag` — runs quarterly, computes vintage table for every origination year, surfaces in Grafana.

**New Sprint:** Add to Sprint 9 (monitoring) alongside PSI.

---

## V3-10. Adverse Action Codes  *(extends B5 API + C2 credit policy)*

**Gap:** When the credit-policy engine returns `REJECT`, US lending law (Equal Credit Opportunity Act / ECOA Regulation B) requires the lender to provide up to four specific **adverse action reason codes** explaining the rejection. The plan has no mechanism to generate these from the scorecard.

**What to add — `risk/credit_policy.py` (addition):**

```python
def adverse_action_codes(scorecard_contributions, n_reasons=4):
    """
    Generate top-N adverse action reason codes from scorecard.
    Each code = the variable that hurt the applicant's score most.
    Required by ECOA Reg B (12 CFR 202.9) for any adverse action.

    scorecard_contributions: dict {variable_name: score_points_contributed}
    Negative points = variables hurting the score (adverse factors).
    """
    adverse = {k: v for k, v in scorecard_contributions.items() if v < 0}
    sorted_adverse = sorted(adverse.items(), key=lambda x: x[1])  # most negative first
    top_reasons = sorted_adverse[:n_reasons]

    # Map variable names to human-readable ECOA codes
    code_map = {
        'fico_score_woe':        'AA01 — Derogatory credit history',
        'dti_woe':               'AA02 — Debt-to-income ratio too high',
        'revol_util_woe':        'AA03 — Proportion of balances to credit limits too high',
        'emp_length_int_woe':    'AA04 — Insufficient length of employment',
        'annual_inc_woe':        'AA05 — Insufficient income',
        'inq_last_6mths_woe':    'AA06 — Too many recent credit inquiries',
        'num_accts_ever_120_pd_woe': 'AA07 — Serious delinquency history',
        'open_acc_woe':          'AA08 — Too few open accounts',
    }
    return [code_map.get(var, f'AA99 — {var}') for var, _ in top_reasons]
```

**Updated API response:**

```json
{
  "loan_id": "LC123456",
  "pd": 0.2150,
  "credit_score": 430,
  "risk_class": "F",
  "decision": "AUTO_REJECT",
  "adverse_action_codes": [
    "AA01 — Derogatory credit history",
    "AA02 — Debt-to-income ratio too high",
    "AA07 — Serious delinquency history",
    "AA06 — Too many recent credit inquiries"
  ]
}
```

---

## V3-11. Champion / Challenger Model Framework  *(extends B6)*

**Gap:** B6 describes gradient boosting as a "future improvement" in isolation. Production model risk management requires a formal **champion/challenger** framework — the current model (champion) runs alongside a candidate model (challenger) on live traffic, and the challenger promotes only when it statistically outperforms the champion.

**What to add — `ml/training/champion_challenger.py`:**

```python
from scipy.stats import mannwhitneyu

def champion_challenger_test(y_true, champion_proba, challenger_proba,
                              alpha=0.05, min_gini_delta=0.02):
    """
    Promote challenger to champion only if:
    1. Challenger Gini is meaningfully higher (> min_gini_delta)
    2. Difference is statistically significant (Mann-Whitney U, p < alpha)
    3. Hosmer-Lemeshow p-value ≥ 0.05 (still calibrated)
    """
    from sklearn.metrics import roc_auc_score

    auc_champ = roc_auc_score(y_true, champion_proba)
    auc_chal  = roc_auc_score(y_true, challenger_proba)
    gini_delta = 2 * (auc_chal - auc_champ)

    stat, p_value = mannwhitneyu(challenger_proba[y_true == 0],
                                  challenger_proba[y_true == 1],
                                  alternative='greater')

    promote = (gini_delta > min_gini_delta) and (p_value < alpha)
    return {
        "gini_champion": round(2 * auc_champ - 1, 4),
        "gini_challenger": round(2 * auc_chal - 1, 4),
        "gini_delta": round(gini_delta, 4),
        "p_value": round(p_value, 4),
        "promote_challenger": promote
    }
```

**MLflow integration:** Both champion and challenger are registered in the MLflow model registry. The `monitoring_dag` runs champion-challenger test monthly and flags results in Grafana for Risk Committee review before promotion.

---

## V3-12. SR 11-7 Model Documentation Checklist  *(extends Sprint 10)*

**Gap:** Sprint 10 says "SR 11-7 model governance report" but provides no structure. SR 11-7 has specific documentation requirements; auditors and supervisors expect all of these to be present before a model is used in production.

**Minimum documentation required per SR 11-7 (`docs/model_card.md`):**

```markdown
## Model Documentation — PD Scorecard v2.0

### 1. Purpose & Intended Use
- [ ] Business problem the model solves
- [ ] Decisions the model output feeds into (credit approval, IFRS 9 staging, capital RWA)
- [ ] Approved user population (retail unsecured personal loans only)
- [ ] Prohibited uses (corporate lending, fraud detection, pricing outside approved bands)

### 2. Methodology
- [ ] Target variable definition (good/bad, observation window, performance window)
- [ ] Feature list with WoE bins and IV values
- [ ] Model type (statsmodels Logit, version, hyperparameters)
- [ ] Training dataset (Lending Club 2007–2015, n=1.3M rows, 17% default rate)
- [ ] OOT test dataset (2016–2018, n=960K rows)
- [ ] Reject inference methodology (parceling, Siddiqi 2006)

### 3. Performance (Training + OOT)
- [ ] AUC / Gini (OOT ≥ 0.40)
- [ ] KS statistic (OOT ≥ 0.25)
- [ ] Brier Score (≤ 0.10)
- [ ] Hosmer-Lemeshow p-value (≥ 0.05)
- [ ] Reliability diagram (attached)
- [ ] Decile analysis table (monotonic bad rate confirmed)

### 4. Assumptions & Limitations
- [ ] Selection bias: trained on accepted loans only (reject inference applied)
- [ ] P2P platform context: Lending Club ≠ traditional bank portfolio
- [ ] Platform shutdown: no post-2018 data; structural break possible
- [ ] No macroeconomic linkage in base PD model (macro overlay applied separately)

### 5. Model Risk Assessment
- [ ] Inherent risk rating (Low / Medium / High)
- [ ] Materiality: feeds IFRS 9 provisions and Basel RWA → HIGH materiality
- [ ] Compensating controls: OOT validation, PSI/CSI monitoring, HL test

### 6. Validation Evidence
- [ ] Independent validation performed by: [name / team]
- [ ] Validation date:
- [ ] Findings and management responses:
- [ ] Outstanding issues (if any):

### 7. Governance
- [ ] Model owner:
- [ ] Model developer:
- [ ] Risk Committee approval date:
- [ ] Next scheduled review:
- [ ] MLflow experiment URL:
- [ ] MLflow model version:
```

---

## Summary of V3 Improvements

| # | Improvement | Plan Section | Gap Source |
|---|-------------|-------------|------------|
| V3-1 | Unexpected Loss, Economic Capital, RAROC | C1 | research.md §9 |
| V3-2 | IFRS 9 SICR rule (replace hardcoded PD thresholds) | C4 | research.md §28, Lit Review §2.4 |
| V3-3 | Through-the-Cycle vs Point-in-Time PD calibration | B2, C4 | Lit Review §2.4 |
| V3-4 | Lifetime PD + scenario-weighted ECL | C4 | research.md §28, Lit Review §2.4 |
| V3-5 | Reject inference (parceling method) | A4, B2 | Lit Review §2.3 |
| V3-6 | Downturn LGD adjustment | B3, C4 | research.md §29 (Basel AIRB) |
| V3-7 | Hosmer-Lemeshow test + reliability diagram | B2 | research.md §22 |
| V3-8 | Characteristic Stability Index (CSI) | C3 | Lit Review §2.6 |
| V3-9 | Vintage / cohort analysis | C3 | research.md §10 |
| V3-10 | Adverse action codes (ECOA compliance) | B5, C2 | research.md §33 |
| V3-11 | Champion / challenger model framework | B6 | Lit Review §2.6 |
| V3-12 | SR 11-7 model documentation checklist | Sprint 10 | research.md §32, Lit Review §2.4 |

**Total new sprint effort: ~3 additional weeks** — spread across existing sprints rather than new dedicated sprints (most items slot into Sprint 5–10 as additions).
