# Lending Club Credit Risk — Data Engineering & Machine Learning Pipeline

<img src="data/reports/L02_roc_curve.png" width="800px">

# 1. Project Description

This project builds an **end-to-end, production-grade credit risk modelling platform** on a modern open-source data stack. It applies the full **CRISP-DM** framework — from raw CSV ingestion through to regulatory reporting, real-time scoring, and daily automated monitoring — and is intentionally designed to mirror how a real bank credit risk system is structured and governed.

**What the platform does end-to-end:**
The system ingests 2,260,668 Lending Club loan records through a **PySpark pipeline**, cleans and transforms them into a WoE-encoded feature store in PostgreSQL, and trains three interlinked models covering the three components of **Expected Loss (EL = PD × LGD × EAD)**:

- **PD Model (Probability of Default):** A logistic regression scorecard (300–850 scale) with WoE encoding, iterative p-value feature selection, and intercept log-odds recalibration. The model is calibrated to the OOT observed default rate and produces both a **Point-in-Time (PiT)** PD (used for IFRS 9 provisioning) and a **Through-the-Cycle (TtC)** PD (used for Basel AIRB capital). The full pipeline — from raw feature to calibrated PD to credit score — was executed end-to-end on the real 2.26M-row dataset and verified to produce zero errors across all four notebooks.

- **LGD Model (Loss Given Default):** A two-stage architecture (Stage 1: logistic regression on whether any recovery occurs; Stage 2: linear regression on the recovery amount) applied to charged-off loans only. The model produces a **long-run LGD of 92.19%** and a **Basel AIRB downturn LGD of 93.76%** (applying the 1.25× haircut required under CRE36).

- **EAD Model (Exposure at Default):** Linear regression on the Credit Conversion Factor (CCF), giving a total portfolio EAD of **$3.26 billion**.

**What makes this project different from a standard ML notebook:**

Beyond model training, the project implements the infrastructure and regulatory outputs that distinguish an academic exercise from a production credit risk system:

- **Data engineering layer:** Apache Airflow DAGs orchestrate six pipeline stages (ingestion → cleaning → feature engineering → model training → batch scoring → monitoring). PySpark processes the 1.6 GB raw file in ~7 seconds using column-projected, chunk-safe ingestion. MinIO serves as the S3-compatible data lake; PostgreSQL holds five logical schemas (raw, staging, features, models, risk).

- **Regulatory stack:** IFRS 9 three-stage Expected Credit Loss (ECL) provisioning — with SICR rules (relative PD doubling, absolute PD jump ≥ 5pp, 30-DPD backstop), lifetime ECL via geometric hazard term structure, and three-scenario probability-weighting per §5.5.17 (Base 50%, Upside 25%, Downside 25%) — producing a **weighted lifetime ECL of $1.646 billion** versus a flat 12-month EL of $0.808 billion, a +$838M uplift that reflects the real cost of credit risk across loan lifetimes. Basel III AIRB capital is computed using the retail IRB formula, giving **RWA of $14.07 billion** and a **minimum capital requirement of $1.13 billion**.

- **Reject inference:** A parceling augmentation adds 26,129 synthetic reject rows to the training set, partially correcting the selection bias introduced by training only on funded (accepted) loans.

- **ECOA compliance:** Every rejected loan application returns up to four adverse action reason codes (ECOA Regulation B), derived directly from scorecard contributions — making the decision auditable and legally compliant.

- **Real-time scoring API:** FastAPI service returns PD, LGD, EAD, Expected Loss, IFRS 9 stage, credit score, risk class (AA–F), credit decision, and adverse action codes per loan application.

- **Monitoring:** Prometheus and Grafana track daily PSI and CSI across all model input variables and the score distribution, with automatic alerts when PSI > 0.25. The OOT population (2016–2018) already shows a **Score PSI of 0.282 (ALERT)** versus the 2007–2015 training window — flagging that a model rebuild will be required in the next update.

- **SR 11-7 governance:** The model card (`docs/model_card.md`) documents model purpose, methodology, training data, OOT performance, known limitations, governance roles, and approval status in the format expected by banking regulators.

---

# 2. Business Problem and Objectives

**2.1 What is the Lending Club?**

LendingClub is a **peer-to-peer (P2P) lending platform** that connects individual borrowers seeking personal loans with investors willing to fund them — bypassing traditional banks entirely. Operating as an online marketplace, it originated loans from 2007 through 2018 across grade tiers (A through G) with interest rates ranging from 5.42% to 26%, and loan amounts from a few thousand to $35,000. The accepted loan dataset used in this project covers **2,260,668 applications** spanning that full period.

**2.2 What is the business problem?**

LendingClub faces the fundamental challenge that any lender faces: **maximising returns to investors while controlling credit losses**. Every loan either generates interest income or becomes a default, and the difference between a well-managed and a poorly-managed portfolio is determined by how accurately the platform can predict default risk *before* issuing a loan.

The specific problems this project addresses are:

- **Credit origination decisioning:** Which applicants should be approved, rejected, or flagged for manual review? The PD scorecard and 10-class credit policy (AA → F) provide a systematic, auditable framework for this decision, replacing ad-hoc judgement.
- **Expected loss estimation:** What financial losses should the portfolio expect? EL = PD × LGD × EAD quantifies this per loan, enabling LendingClub to price risk into interest rates and flag loss-making loans before funding them.
- **Regulatory provisioning (IFRS 9):** Financial institutions are required under IFRS 9 to hold provisions against expected credit losses. Stage 1 loans require 12-month ECL; Stage 2 (Significant Increase in Credit Risk) and Stage 3 (credit-impaired) loans require lifetime ECL. The three-stage SICR classification and scenario-weighted lifetime ECL calculation in this project directly address this regulatory obligation.
- **Capital adequacy (Basel III):** Under the Internal Ratings-Based (AIRB) approach, banks must hold minimum capital equal to 8% of Risk-Weighted Assets, where RWA is computed from the IRB formula using PD, LGD, and maturity. This project computes per-loan RWA and minimum capital requirements, producing a portfolio total of **$1.13 billion in required capital**.
- **Model stability and drift:** A model trained on 2007–2015 applicants may no longer be valid for 2016–2018 applicants if the population has shifted. Population Stability Index (PSI) and Characteristic Stability Index (CSI) monitoring detect this drift automatically and trigger a rebuild alert when thresholds are breached.
- **Regulatory transparency (ECOA):** US lending law requires lenders to explain rejections. Adverse action codes, generated from scorecard contributions, ensure every reject decision is traceable and legally defensible.

**2.3 What are the project objectives and benefits?**

1. Build a **memory-safe, production-grade data engineering pipeline** (PySpark + Airflow + PostgreSQL + MinIO) that ingests the 1.6 GB raw CSV using column-projected chunked reads (~7 seconds), cleans and validates data at each stage, and stores outputs in a five-schema data warehouse.

2. Develop a **PD scorecard** (300–850 integer scale, PDO = 20, reference score 600 at 1:1 odds) using statsmodels Logistic Regression with WoE encoding and iterative p-value feature selection, retaining only the **39 of 56 candidates** that are statistically significant at α = 0.05.

3. Apply **PD calibration** (intercept log-odds shift δ = +0.3204) to align mean predicted PD with the OOT observed default rate of 25.27%, and produce both **PiT** and **TtC** PD variants for their respective regulatory uses.

4. Apply **reject inference** via the parceling method (Siddiqi 2006), adding 26,129 synthetic reject rows to partially correct for selection bias in a funded-loans-only dataset.

5. Develop an **LGD two-stage model** and an **EAD CCF regression**, computing Expected Loss on the real calibrated PD rather than grade-proxy approximations.

6. Implement **IFRS 9 three-stage ECL** with SICR classification, geometric hazard lifetime PD, and three-scenario probability-weighted ECL per §5.5.17, generating a portfolio provision of **$1.646 billion**.

7. Implement **Basel III AIRB capital** calculation (retail IRB formula, RWA $14.07B, minimum capital $1.13B) and document the known limitation that RAROC (+299%) is inflated by the high unsecured LGD (~93%) and should be computed on the approved-only subset.

8. Implement a **10-class credit policy** (AA → F) with ROI-based decisioning for middle bands, and generate ECOA-compliant adverse action codes for every rejection.

9. Deploy a **real-time FastAPI scoring service** returning the full credit decision payload, and a **daily Airflow monitoring DAG** computing PSI/CSI with Grafana alerting on breach.

10. Document the model under **SR 11-7 Model Risk Management** guidance, covering conceptual soundness, outcome analysis, limitations, governance roles, and a full validation summary.

**2.4 Important concepts in the context of credit risk**

- **Credit risk** is the probability that a borrower fails to repay, resulting in a loss for the lender. In a P2P context like LendingClub, this loss falls directly on the investor who funded the loan.

- **Probability of Default (PD)** is the estimated likelihood that a borrower defaults within a fixed observation window (here, the loan's resolved status — Charged Off = bad, Fully Paid = good). The PD model is an *application model*, built from data available at the time of loan origination.

- **Loss Given Default (LGD)** is the share of the outstanding balance that cannot be recovered after a default. In this portfolio — unsecured personal loans — recovery rates average only ~8%, giving a long-run LGD of **92.19%** and a Basel downturn LGD of **93.76%**.

- **Exposure at Default (EAD)** is the outstanding loan balance at the moment of default. Modelled via the Credit Conversion Factor: `EAD = CCF × funded amount`.

- **Expected Loss (EL)** is the portfolio's average anticipated loss: `EL = PD × LGD × EAD`. The portfolio-level 12-month EL is **$0.808 billion** (19.93% EL rate).

- **Unexpected Loss and Economic Capital:** Banks hold capital not for expected losses (covered by provisions) but for *unexpected* losses — the tail of the loss distribution. The Basel III AIRB formula converts PD, LGD, and maturity into a capital requirement per loan. Portfolio RWA is **$14.07 billion**; minimum capital is **$1.13 billion (34.5% of EAD)**.

- **IFRS 9 ECL:** Accounting standard requiring financial institutions to recognise forward-looking provisions. Loans are staged: Stage 1 (performing, 12-month ECL), Stage 2 (SICR triggered, lifetime ECL), Stage 3 (credit-impaired, lifetime ECL). Lifetime ECL is computed via a geometric hazard term structure and probability-weighted across three macro scenarios. Portfolio total: **$1.646 billion** — +$838M above a flat 12-month EL.

- **Through-the-Cycle (TtC) vs Point-in-Time (PiT) PD:** TtC PD averages across the full economic cycle and is used for stable Basel capital calculation. PiT PD is sensitive to current conditions and used for IFRS 9 provisioning. The intercept log-odds shift method converts the base logistic model output into both variants.

- **Weight of Evidence (WoE):** A monotonic encoding that captures the log-odds of a good/bad event per feature category. Using WoE-encoded dummies as logistic regression inputs guarantees interpretable, direction-consistent coefficients — a regulatory requirement for scorecard models.

- **Population Stability Index (PSI):** Measures how much the score distribution has shifted between training and monitoring periods. PSI < 0.10 = stable; 0.10–0.25 = monitor; > 0.25 = alert, consider rebuild. The OOT Score PSI in this project is **0.282 (ALERT)** — the 2016–2018 applicant population has shifted measurably from the 2007–2015 training window.

- **ECOA Regulation B (Adverse Action):** US law requiring lenders to provide specific written reasons for any rejection. The scoring API generates up to four adverse action codes per rejection, derived from which scorecard variables contributed most negatively to the applicant's score.

- **SR 11-7:** Federal Reserve guidance on Model Risk Management, requiring banks to document model purpose, methodology, performance, limitations, governance, and validation before any model is used in production for regulatory capital or provisioning decisions.

---

# 3. Solution Pipeline

The solution follows the **CRISP-DM** framework across four sequential learning notebooks (L01–L04) and a parallel production pipeline (six Airflow DAGs). All four notebooks were executed end-to-end on the real `accepted_2007_to_2018Q4.csv` dataset (2.26M rows) with zero errors, regenerating 23 charts and all model artifacts.

**3.1 Business Understanding**

The starting point is defining what "credit risk" means operationally for this project: the goal is not to maximise model accuracy in isolation, but to produce outputs that satisfy three distinct audiences simultaneously — the credit underwriting team (who need an approve/reject decision), the finance team (who need IFRS 9 provisions), and the risk team (who need Basel AIRB capital). Each audience requires a different PD variant (PiT for IFRS 9, TtC for Basel) and a different time horizon (12-month for Stage 1, lifetime for Stage 2/3). The regulatory success criteria are documented explicitly: Gini ≥ 0.40 on OOT, KS ≥ 0.25, Brier ≤ 0.20, Score PSI < 0.25, API p99 latency < 200ms.

**3.2 Data Understanding**

The raw dataset contains 2,260,668 loan applications across 151 columns, covering 2007–2018. Key characteristics discovered during exploration:

- The file is **not sorted chronologically** — an `issue_year` column must be used for the OOT split, not row order.
- The overall default rate (Charged Off status) is approximately **17%** across resolved loans, rising to **25.27%** in the 2016–2018 OOT period — a significant population shift that the monitoring PSI later confirms.
- 15 columns are **100% null** (all `sec_app_*`, `member_id`, `desc`) and are dropped immediately.
- `int_rate` and `revol_util` are stored as percentages (e.g., 13.99) and must be divided by 100 before modelling.
- `mths_since_last_delinq` contains actual NaN (not a sentinel value like −1) and must be treated as a separate WoE category rather than imputed — because missingness signals a specific borrower type, not a data quality problem.
- FICO score (`fico_range_low` and `fico_range_high`) is available in this dataset and is one of the strongest predictors, with expected IV > 0.30.
- Default rate by grade shows a clear monotonic pattern (A ≈ 5% → G > 35%), validating that the WoE approach will find meaningful orderings.

**3.3 Data Preparation (L01 — Preprocessing & Feature Engineering)**

Data preparation runs across the PySpark cleaning Spark job and the L01 notebook, producing the training and OOT parquet files that feed all downstream models.

*Ingestion:* The raw 1.6 GB CSV is read with column projection — only the 26 modelling columns are loaded into memory rather than all 151. This reduces load time to approximately 7 seconds and mirrors real ETL practice (you never pull columns you immediately drop).

*Cleaning:* 57 columns are removed across five categories — 100% null, identifier/constant, joint application (>99% null), hardship/settlement (>97% null), and post-application leakage (variables only known after the loan is issued, such as `total_pymnt`, `recoveries`, `out_prncp`). These leakage columns are used only to construct the target variables before being dropped.

*Target variable creation:*
- `good_bad` — 1 for Fully Paid; 0 for Charged Off / Default / Late 31–120 days.
- `recovery_rate` — `recoveries / funded_amnt`, computed on charged-off loans only; used as the LGD target.
- `ccf` — `(funded_amnt − total_pymnt) / funded_amnt`, on charged-off loans only; used as the EAD target.

*Derived features:* `fico_score` (midpoint of FICO range), `term_int` (integer months from string), `int_rate` (divided by 100), `mths_since_issue_d`, `mths_since_earliest_cr_line`, `emp_length_int`.

*Out-of-time split:*

```
2007–2015  →  Training set:  831,051 loans  |  Default rate: 18.62%
2016–2018  →  OOT Test set:  538,515 loans  |  Default rate: 25.27%
```

This is the gold standard for credit risk models. A random split would allow future statistical patterns to contaminate the training set; the OOT split ensures the model is evaluated exactly as it will be used in production — trained on history, scored on the future.

*WoE encoding:* Weight of Evidence bins are computed on the **training set only** and then applied (without re-fitting) to the OOT set. Missing values are treated as a distinct WoE bin rather than imputed — a borrower with no delinquency record in the dataset is a different credit risk profile from a borrower with a zero-delinquency record. 56 WoE dummy variables are produced from 16 raw predictors.

*Reject inference:* The dataset contains only funded (accepted) loans. Rejected applicants — who would disproportionately be bad borrowers — are unobserved, creating a selection bias that causes the model to underestimate default risk. The parceling method (Siddiqi 2006) adds 26,129 synthetic reject rows (3.1% of training size) with probabilistic `good_bad` labels derived from inflated PD estimates. The augmented training set (857,180 rows) produces a mean OOT PD of 20.70% versus 20.18% on the base set — partially correcting the downward bias before intercept recalibration.

**3.4 Modelling (L02 — PD Scorecard, L03 — LGD / EAD / Expected Loss)**

*PD Model:* Logistic regression estimated with statsmodels (BFGS optimiser), which provides proper Wald-test p-values required for regulatory documentation. Feature selection uses iterative backward elimination: at each step the variable with the highest max p-value across its dummies is removed, until all remaining dummies have p < 0.05. This reduces the feature set from 56 to **39 significant dummies** covering 16 predictors. Coefficients are transformed into a 300–850 integer scorecard using standard scaling formulae (PDO = 20, reference score 600 at odds 1:1).

*PD Calibration:* The raw model produces a mean OOT PD of 20.18% against an actual OOT default rate of 25.27%. An intercept log-odds shift (δ = +0.3204) recalibrates the level, reducing the Hosmer-Lemeshow statistic by 96% and aligning the mean PD to the observed rate. Discrimination metrics (AUC, Gini, KS) are mathematically unaffected by the intercept shift. Two calibrated variants are saved: PiT (for IFRS 9) and TtC (log-odds shifted to the long-run 15% default rate, for Basel capital).

*LGD Model:* Two-stage regression on the charged-off loan subset. Stage 1 (logistic) predicts whether any recovery occurs (P(RR > 0)); Stage 2 (linear) predicts the recovery amount given recovery > 0. Combined LGD = 1 − (Stage 1 × Stage 2). Downturn LGD applies a 1.25× haircut to the recovery rate (floored at the long-run level) per Basel AIRB CRE36, producing a downturn LGD of 93.76%.

*EAD Model:* Linear regression on the Credit Conversion Factor, clipped to [0, 1]. Total portfolio EAD is $3.26 billion.

*Expected Loss:* `EL = calibrated PiT PD × LGD × EAD` — computed using the real model outputs, not grade-proxy approximations. This change (from hard-coded grade→PD proxies to the real scorecard PD) was one of the key real-world corrections made in the v4 update.

*IFRS 9 ECL:* Every OOT loan is classified Stage 1, 2, or 3 via the SICR rule. Stage 1 receives a 12-month ECL; Stages 2 and 3 receive a lifetime ECL computed from a geometric hazard term structure (monthly hazard rate derived from annual PD, 5% discount rate). Three-scenario probability-weighted ECL is then computed using a log-odds macro satellite model (Bellotti & Crook 2009: Δlogodds = 0.18 × Δunemployment − 0.10 × ΔGDP) with Base / Upside / Downside scenarios weighted 50% / 25% / 25%.

**3.5 Validation (L02 validation, L04 — Population Stability Index)**

Validation covers both model performance and population stability, following EBA GL/2017/16 requirements:

*Model performance metrics:*

| Metric | Value | Benchmark | Result |
|---|---|---|---|
| AUC (OOT) | 0.694 | > 0.65 | ✓ |
| Gini (OOT) | 0.387 | ≥ 0.40 preferred | ⚠ Marginally below |
| KS (OOT) | 0.281 | ≥ 0.25 | ✓ |
| Brier Score | 0.172 | ≤ 0.20 | ✓ |
| Hosmer-Lemeshow (pre-calibration) | p ≈ 0 | p ≥ 0.05 | ✗ Miscalibrated — corrected |
| Hosmer-Lemeshow (post-calibration) | HL = 403 | p ≥ 0.05 | ⚠ n = 538K gives near-infinite HL power |
| Decile ordering | Monotonic bad rate | Confirmed | ✓ |
| Score PSI (OOT vs train) | 0.282 | < 0.25 | ✗ ALERT |

*Decile analysis* confirms the scorecard has ordering power: Decile 1 (lowest scores) carries the highest bad rate, and the top three deciles capture more than 50% of all bad borrowers. This monotonic ordering is a mandatory acceptance criterion for scorecard models.

*Population monitoring:* The Score PSI of 0.282 on the 2016–2018 OOT population is a clear ALERT signal. Characteristic Stability Index (CSI) is computed for each of the 39 model input variables to identify which features drove the shift. Vintage analysis plots predicted PD against actual default rate by origination cohort, confirming the model tracks the real default experience across years. Champion/Challenger comparison retains the incumbent logistic scorecard (Gini 0.387) — no challenger outperforms it within the current model class.

**3.6 Deployment**

Deployment covers three components:

*Real-time scoring:* FastAPI service loads model artifacts at startup and returns a full credit decision payload (PD, LGD, EAD, EL, IFRS 9 stage, credit score, risk class, decision, adverse action codes) in under 200ms. Redis caches features for hot applicants.

*Batch pipeline:* Airflow DAG-05 scores the full OOT portfolio overnight using the same model artifacts, writing results to the `risk` schema in PostgreSQL.

*Monitoring:* Airflow DAG-06 (daily, 6am) computes PSI for the score distribution and CSI for each input variable against the training baseline. Results feed a Prometheus metrics endpoint scraped by Grafana, which fires alerts when PSI > 0.25 on any variable.

---

# 4. Technologies and Tools

| Layer | Technology |
|---|---|
| Orchestration | Apache Airflow 2.x |
| Big Data Processing | Apache Spark 3.x (PySpark) |
| Data Lake | MinIO (S3-compatible) |
| Data Warehouse | PostgreSQL 15 |
| ML Tracking | MLflow 2.x |
| Statistical Modelling | Statsmodels, Scikit-learn |
| Model Serving | FastAPI + Redis cache |
| Monitoring | Prometheus + Grafana |
| Containerisation | Docker Compose |
| Language | Python (Pandas, NumPy, Scikit-Learn, Statsmodels) |

---

# 5. Project Structure

```
I4_risk_management/
├── pipeline/                 # End-to-end pipeline code
│   ├── dags/                 # Airflow orchestration DAGs
│   │   ├── 00_master_pipeline.py
│   │   ├── 01_ingestion.py
│   │   ├── 02_cleaning.py
│   │   ├── 02b_feature_engineering.py
│   │   ├── 03_pd_training.py
│   │   ├── 04_lgd_ead_training.py
│   │   ├── 05_batch_scoring.py
│   │   └── 06_monitoring.py
│   └── spark_jobs/           # PySpark transformation jobs
│       ├── 01_ingest.py
│       └── 02_clean.py
│
├── models/                   # All model-related Python code
│   ├── preprocessing/        # WoE encoding & PD calibration
│   │   ├── woe_encoder.py
│   │   └── pd_calibrator.py
│   ├── training/             # Model training scripts
│   │   ├── train_pd.py
│   │   └── train_lgd_ead.py
│   ├── evaluation/           # Metrics and evaluation utilities
│   │   └── metrics.py
│   ├── architectures/        # Model class definitions
│   │   ├── pd_model.py
│   │   └── lgd_model.py
│   └── risk/                 # Business risk logic
│       ├── expected_loss.py
│       └── psi_monitor.py
│
├── api/                      # FastAPI real-time scoring service
│   ├── main.py
│   ├── model_loader.py
│   ├── routers/score.py
│   ├── schemas/score.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── infrastructure/           # Docker service configurations
│   ├── airflow/
│   ├── spark/
│   ├── mlflow/
│   ├── postgres/init.sql
│   └── grafana/dashboards/
│
├── notebooks/                # Learning notebooks (run in order)
│   ├── L01_Preprocessing_Feature_Engineering.ipynb
│   ├── L02_PD_Model_Scorecard.ipynb
│   ├── L03_LGD_EAD_Expected_Loss.ipynb
│   └── L04_Population_Stability_Index.ipynb
│
├── data/                     # ⚠️ gitignored — local only
│   ├── raw/                  #   Lending Club CSV (~1.6 GB)
│   ├── processed/            #   Parquet feature store
│   ├── artifacts/            #   Serialised model .pkl files
│   └── reports/              #   Charts and PSI outputs
│
├── docs/                     # Documentation and research
│   ├── model_card.md         #   SR 11-7 governance document
│   ├── Column_Mapping.md
│   ├── Credit_Risk_Implementation_Plan.md
│   └── Literature_review_V2.md
│
├── docker-compose.yml
├── Makefile
├── .env.example
└── requirements_notebooks.txt
```

---

# 6. Key Business Insights

The Lending Club dataset spans 2007–2018 and contains 2,260,668 loan applications. After removing 57 irrelevant, leaking, or near-null columns, 1,369,566 loans remain for modelling (those with a resolved loan status — Fully Paid or Charged Off).

**6.1 Default rate and loan volume**

<img src="data/reports/L01_loan_volume_default_rate.png">

- The overall default rate across the resolved portfolio is approximately **17%** (Charged Off status).
- Loan volume grew substantially from 2007 to 2015, then again through 2018.

**6.2 Default rate by credit grade**

<img src="data/reports/L01_default_rate_by_grade.png">

- There is a clear monotonic relationship between Lending Club's internal grade and default rate: Grade A borrowers default at roughly 5% while Grade G borrowers default at over 35%.
- This monotonic ordering validates the WoE approach — higher-risk grade bins consistently show lower (more negative) WoE values.

**6.3 FICO score distribution — good vs bad borrowers**

<img src="data/reports/L01_fico_distribution_good_bad.png">

- Good borrowers (non-defaulters) are concentrated at higher FICO scores.
- Bad borrowers (defaulters) are concentrated at the lower end of the FICO range.
- FICO score is one of the strongest predictors of default, with an IV well above 0.30.

**6.4 Conclusion**
- Despite LendingClub presenting a largely conservative portfolio (most borrowers are Grade A–D, employed 2+ years, borrowing for debt consolidation), the default rate is high enough to justify a rigorous credit risk framework. The goal is to reduce the effective default rate and Expected Loss while rejecting as few profitable loans as possible.

---

# 7. Modelling

## 7.1 Data Preparation

**Out-of-time split** — The gold standard for credit risk models. Rather than a random train/test split, data is divided chronologically:

| Split | Years | Rows | Role |
|---|---|---|---|
| Train | 2007–2015 | ~1,369,566 | Fit WoE bins, train all models |
| OOT Test | 2016–2018 | ~960,000 | Evaluate on genuinely future data |

This mirrors real deployment: models trained on past data must generalise to future applicants. A random split allows future statistical patterns to leak into training.

**Reject inference** — The dataset contains only funded (accepted) loans. To partially correct for selection bias, a parceling augmentation adds 26,129 synthetic reject rows to the training set before retraining the PD model.

**Key cleaning steps:**
- Drop 57 columns (100% null, identifier, post-application leakage, near-zero variance).
- Create target variables: `good_bad` (PD), `recovery_rate` (LGD), `ccf` (EAD).
- Treat missing values as a separate WoE bin (not imputed away) — missingness often carries credit risk information.
- Derive: `fico_score`, `term_int`, `int_rate` (/100), `mths_since_issue_d`, `emp_length_int`.

---

## 7.2 PD Model — Probability of Default

The PD model is a Logistic Regression built with **statsmodels**, which provides proper Wald test p-values required for regulatory documentation. All predictors are WoE-encoded dummies.

**Feature selection** — Iterative backward elimination: variables with all dummies at p ≥ 0.05 are dropped, until only statistically significant predictors remain. The final model retains 39 of 56 candidate features.

**Scorecard scaling** — Coefficients are converted to integer score points on a 300–850 scale (PDO = 20, reference score 600 at odds 1:1). Higher score = lower PD = better borrower.

**Calibration** — An intercept log-odds shift (δ = +0.3204) aligns the model's mean predicted PD to the OOT observed default rate (25.27%). Two PD variants are produced:
- **PiT PD** — used for IFRS 9 provisioning (sensitive to current conditions).
- **TtC PD** — shifted to the long-run default rate of 15%, used for Basel AIRB capital.

**PD Model performance (OOT test set — calibrated):**

| Metric | Value | Benchmark | Assessment |
|---|---|---|---|
| AUC | 0.694 | > 0.65 | ✓ Acceptable |
| Gini | 0.387 | > 0.40 preferred | ⚠ Marginally below target |
| KS Statistic | 0.281 | > 0.25 | ✓ Acceptable |
| Brier Score | 0.172 | < 0.20 | ✓ Acceptable |
| Mean PD (calibrated) | 25.27% | Matches actual DR | ✓ Calibrated |
| Score PSI (OOT vs train) | 0.282 | < 0.25 | ✗ Population shift detected |

**Score distribution and decile analysis:**

<img src="data/reports/L02_score_distribution_good_bad.png">

<img src="data/reports/L02_decile_analysis.png">

The decile analysis confirms a **monotonic ordering**: Decile 1 (lowest scores) carries the highest bad rate, and the top three deciles capture more than 50% of all bad borrowers — a standard validation requirement for scorecard acceptance.

**ROC curve:**

<img src="data/reports/L02_roc_curve.png">

**Calibration reliability diagram:**

<img src="data/reports/L02_calibration_reliability_diagram.png">

**Risk class distribution (10 classes: AA → F):**

<img src="data/reports/L02_risk_class_distribution.png">

---

## 7.3 LGD Model — Loss Given Default

The LGD model uses a **two-stage architecture**, applied only to defaulted loans (Charged Off status):

- **Stage 1 — Logistic Regression:** Predicts whether any recovery occurs (Recovery Rate > 0).
- **Stage 2 — Linear Regression:** Predicts the recovery amount conditional on recovery > 0.
- **Combined:** LGD = 1 − (Stage 1 prediction × Stage 2 prediction).

**Recovery rate distribution:**

<img src="data/reports/L03_recovery_rate_distribution.png">

Nearly 50% of charged-off loans show zero recovery, justifying the two-stage design.

**LGD residuals:**

<img src="data/reports/L03_lgd_residuals.png">

| Metric | Value |
|---|---|
| Stage 1 AUC | > 0.60 |
| LGD MAE | ~5% |
| Mean LGD (portfolio) | 92.19% |
| Downturn LGD (Basel AIRB) | 93.76% (1.25× haircut) |

The high mean LGD reflects the unsecured nature of personal loans — recovery rates are low across the portfolio.

---

## 7.4 EAD Model — Exposure at Default

The EAD model regresses a **Credit Conversion Factor (CCF)** — defined as `(funded_amnt − total_pymnt) / funded_amnt` — on loan and borrower characteristics. EAD is then recovered as CCF × funded amount.

**CCF distribution:**

<img src="data/reports/L03_ccf_distribution.png">

**EAD residuals:**

<img src="data/reports/L03_ead_residuals.png">

| Metric | Value |
|---|---|
| CCF MAE | ~14% |
| Total portfolio EAD | $3.26B |

---

## 7.5 Expected Loss, IFRS 9 ECL, and Credit Policy

**Expected Loss** is computed as EL = PD × LGD × EAD across the full portfolio.

**Expected loss by grade:**

<img src="data/reports/L03_expected_loss_by_grade.png">

**IFRS 9 three-stage ECL:**
- **Stage 1 (Performing):** 12-month ECL.
- **Stage 2 (SICR):** Lifetime ECL triggered when PD doubles, rises by ≥ 5pp, or 30-DPD backstop fires.
- **Stage 3 (Credit-impaired):** Lifetime ECL for 90+ DPD loans.

ECL is computed under three macroeconomic scenarios and probability-weighted per IFRS 9 §5.5.17 (Base 50%, Upside 25%, Downside 25%).

<img src="data/reports/L03_ifrs9_ecl_staging.png">

<img src="data/reports/L03_ifrs9_scenario_weighted_ecl.png">

**Portfolio-level outputs (calibrated PD):**

| Metric | Value |
|---|---|
| Total 12-month Expected Loss | $0.808B |
| IFRS 9 lifetime ECL (base scenario) | $1.601B |
| IFRS 9 ECL (§5.5.17 weighted) | $1.646B |
| IRB Risk-Weighted Assets (RWA) | $14.07B |
| Basel III Minimum Capital (8% of RWA) | $1.13B |

**10-class credit policy (AA → F):**
Loans are segmented into 10 risk classes based on credit score bands. Auto-approve for AA/A; auto-reject for F; ROI-based approval for all middle classes (annualised ROI must exceed the US base rate of 2.15%).

**Vintage analysis:**

<img src="data/reports/L03_vintage_analysis.png">

---

## 7.6 Model Monitoring

After deployment, the pipeline monitors whether the current loan applicant population remains consistent with the training population.

**PSI monitoring dashboard:**

<img src="data/reports/L04_psi_master_dashboard.png">

<img src="data/reports/L04_score_psi_distribution.png">

**PSI thresholds:**

| PSI Value | Status | Action |
|---|---|---|
| < 0.10 | STABLE | Continue as-is |
| 0.10 – 0.25 | MONITOR | Investigate root cause |
| > 0.25 | ALERT | Consider model redevelopment |

The score PSI on the 2016–2018 OOT population is **0.282 (ALERT)**, indicating a meaningful shift in applicant characteristics between the 2007–2015 training window and the 2016–2018 monitoring period.

**CSI (Characteristic Stability Index)** is computed for each model input variable to identify which features drove the population shift.

<img src="data/reports/L04_characteristic_stability_index.png">

<img src="data/reports/L04_psi_continuous_variables.png">

<img src="data/reports/L04_psi_discrete_variables.png">

**Champion / Challenger:**

<img src="data/reports/L04_champion_challenger.png">

**Ongoing monitoring plan:**
- **Daily:** Score PSI and input PSI computed by DAG-06; Grafana alert fires if PSI > 0.25.
- **Monthly:** CSI per variable, decile stability, vintage cohort update.
- **Quarterly:** Full model performance review (AUC, Gini, KS, Brier).
- **Annual:** Full recalibration review; retrain if PSI ALERT persists > 2 months or Gini drops > 5pp.

**Next steps:**
- Retrain PD model on the 2016–2018 population using gradient boosting (XGBoost / LightGBM).
- Apply SHAP values for feature importance and individual loan explainability (ECOA Reg B compliance).
- Implement Platt scaling recalibration if Brier Score degrades on live scoring.

---

# 8. FastAPI Scoring Service

The scoring API accepts a loan application and returns a full credit decision in real time:

```json
{
  "loan_id": "LC123456",
  "pd": 0.0421,
  "lgd": 0.62,
  "ead": 12500.00,
  "expected_loss": 326.55,
  "credit_score": 672,
  "risk_class": "BB",
  "annualized_roi": 0.0387,
  "decision": "APPROVE",
  "adverse_action_codes": [],
  "model_version": "2.0"
}
```

Service URLs after stack boot:

| Service | URL |
|---|---|
| Airflow | http://localhost:8081 |
| Spark Master | http://localhost:8080 |
| MLflow | http://localhost:5001 |
| MinIO Console | http://localhost:9001 |
| FastAPI Docs | http://localhost:8000/docs |
| Grafana | http://localhost:3000 |

---

# 9. Obtain the Data

The dataset is the full Lending Club loan file covering 2007–2018Q4.

Download `accepted_2007_to_2018Q4.csv` from Kaggle and place it at `data/raw/accepted_2007_to_2018Q4.csv`:

> https://www.kaggle.com/datasets/wordsforthewise/lending-club

The file is approximately 1.6 GB and is gitignored. All downstream processed outputs (parquet, model pkl files, reports) are also gitignored and will be generated by running the notebooks or pipeline DAGs.

---

# 10. Run this Project on Your Local Machine

**Prerequisites:** Python 3.11, Docker Desktop, Git.

### 1. Clone and configure

```bash
git clone https://github.com/DUKPagnarith/lending_club_DE.git
cd lending_club_DE
cp .env.example .env
# Edit .env — set your PostgreSQL password, MinIO keys, etc.
```

### 2. Download the dataset

Download `accepted_2007_to_2018Q4.csv` from the Kaggle link above and place it at:
```
data/raw/accepted_2007_to_2018Q4.csv
```

### 3. Start the full stack

```bash
make up          # docker compose up -d --build
```

Wait ~60 seconds for all services to initialise, then verify at the URLs in Section 8.

### 4. Run the learning notebooks (recommended first)

Install notebook dependencies and run notebooks L01 → L04 in order:

```bash
pip install -r requirements_notebooks.txt
jupyter notebook notebooks/
```

| Notebook | Topic | Key Outputs |
|---|---|---|
| L01 | Preprocessing & Feature Engineering | Cleaned parquet, WoE bins, dummy variables |
| L02 | PD Model & Scorecard | Scorecard CSV, credit scores, decile analysis |
| L03 | LGD, EAD & Expected Loss | LGD/EAD models, portfolio EL, IFRS 9 ECL |
| L04 | Population Stability Index | PSI/CSI per feature, score PSI, stability verdict |

### 5. Run the production pipeline (Airflow DAGs)

Trigger DAGs individually from the Airflow UI at http://localhost:8081, or use Makefile shortcuts:

```bash
make train-pd    # Run PD model training DAG
make train-lgd   # Run LGD/EAD model training DAG
```

### 6. Shut down

```bash
make down        # docker compose down
```

---

# 11. Model Governance (SR 11-7)

This project follows the Federal Reserve's **SR 11-7 Model Risk Management** guidance. The model card at [`docs/model_card.md`](docs/model_card.md) documents:

- Model purpose, intended use, and prohibited uses.
- Methodology, training data, OOT test setup, and reject inference approach.
- Full performance metrics with benchmarks and assessments.
- Known limitations and compensating controls.
- Governance roles (model owner, validator, business sponsor, technology owner, compliance).
- Approval status and next scheduled review date.

**Key governance thresholds:**

| Checkpoint | Threshold | Status |
|---|---|---|
| PD Gini (OOT) | ≥ 0.40 | ⚠ 0.387 — marginally below |
| PD KS (OOT) | ≥ 0.25 | ✓ 0.281 |
| PD Brier Score | ≤ 0.20 | ✓ 0.172 |
| Decile ordering | Monotonic bad rate | ✓ Confirmed |
| LGD Stage 1 AUC | ≥ 0.60 | ✓ |
| Score PSI | < 0.25 | ✗ 0.282 — ALERT |
| API p99 latency | < 200ms | ✓ |

---

# 12. Contact

- **LinkedIn:** https://www.linkedin.com/in/panharith-duk/
- **GitHub:** https://github.com/DUKPagnarith
- **Email:** panharithduk@gmail.com
