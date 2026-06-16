# Model Card — Credit Risk PD / LGD / EAD Models
**SR 11-7 Model Risk Management Governance Document**
**Version:** 2.0.0 · **Date:** 2026-06-07 · **Owner:** Credit Risk Analytics

---

## 1. Model Purpose and Scope

| Field | Detail |
|---|---|
| **Model name** | Lending Club Consumer Credit Risk Suite |
| **Model type** | Statistical scoring (PD), loss estimation (LGD, EAD) |
| **Business purpose** | Credit origination decisioning, IFRS 9 ECL provisioning, Basel AIRB capital calculation |
| **Regulatory framework** | Basel II/III AIRB, IFRS 9, ECOA Regulation B, SR 11-7 |
| **Decision supported** | Approve / Reject / Auto-approve / Auto-reject at origination |
| **Output consumers** | Credit underwriting, Finance (IFRS 9 provisions), Risk (capital adequacy) |
| **Deployment environment** | FastAPI scoring API (`/score`), Airflow batch pipeline (DAG 05) |

---

## 2. Model Methodology

### 2.1 PD Model — Probability of Default

| Attribute | Detail |
|---|---|
| **Algorithm** | Logistic regression (statsmodels, BFGS optimiser) |
| **Feature selection** | Backward elimination, p < 0.05 significance threshold |
| **Encoding** | Weight of Evidence (WoE) coarse-class dummy variables |
| **Final features** | 39 of 56 candidates (all statistically significant) |
| **Scorecard scaling** | 300–850 integer score, PDO = 20, Reference odds 1:1 at 600 |
| **Calibration** | Intercept log-odds shift (δ = +0.3204) to match OOT default rate |
| **TtC vs PiT** | TtC PD via log-odds shift to 15% long-run DR (Basel capital); PiT PD used for IFRS 9 |

### 2.2 LGD Model — Loss Given Default

| Attribute | Detail |
|---|---|
| **Architecture** | Two-stage: Stage 1 logistic (Is recovery > 0?), Stage 2 linear regression (How much?) |
| **Population** | Defaulted loans only (loan_status = Charged Off / Default) |
| **Target** | Recovery Rate = Recoveries / Funded Amount; LGD = 1 − Recovery Rate |
| **Downturn LGD** | 1.25× haircut on recovery rate (Basel AIRB requirement); long-run LGD = 92.19%, downturn = 93.76% |

### 2.3 EAD Model — Exposure at Default

| Attribute | Detail |
|---|---|
| **Algorithm** | Linear regression on Credit Conversion Factor (CCF) |
| **Target** | CCF = (Funded Amount − Total Paid) / Funded Amount |
| **Output** | EAD = CCF × Funded Amount |

### 2.4 IFRS 9 ECL Framework

| Attribute | Detail |
|---|---|
| **Staging** | Three-stage: SICR = PD doubling (2×) OR absolute jump ≥ 5pp OR 30-DPD backstop |
| **Stage 1** | 12-month ECL = PD × LGD × EAD × min(term/12, 1) |
| **Stage 2/3** | Lifetime ECL via geometric hazard term structure (constant monthly hazard, 5% annual discount) |
| **Scenario weighting** | §5.5.17 three-scenario probability-weighted ECL (Base 50%, Upside 25%, Downside 25%) |
| **Macro overlay** | Log-odds satellite model: Δlogodds = 0.18 × Δunemployment − 0.10 × ΔGDP |

---

## 3. Training Data

| Attribute | Detail |
|---|---|
| **Dataset** | Lending Club `accepted_2007_to_2018Q4.csv` |
| **Total rows** | 2,260,668 loans |
| **Usable (after filtering)** | 1,369,566 (excludes current/late/in-grace loans) |
| **Training set** | 831,051 loans (issue year ≤ 2015), DR = 18.62% |
| **OOT test set** | 538,515 loans (issue year 2016–2018), DR = 25.27% |
| **Split methodology** | Out-of-time (not random) — mirrors real deployment |
| **Reject inference** | Parceling augmentation: 26,129 synthetic reject rows added to training set |
| **Features** | 56 WoE dummy variables from 16 raw predictors |

---

## 4. Model Performance

### 4.1 PD Model (OOT Test Set — calibrated)

| Metric | Value | Benchmark | Assessment |
|---|---|---|---|
| AUC | 0.694 | > 0.65 | ✓ Acceptable |
| Gini | 0.387 | > 0.40 preferred | ⚠ Marginally below target |
| KS Statistic | 0.281 | > 0.25 | ✓ Acceptable |
| Brier Score (calibrated) | 0.1722 | < 0.20 | ✓ Acceptable |
| Hosmer-Lemeshow (pre-calib) | p ≈ 0 | p ≥ 0.05 | ✗ Miscalibrated — corrected |
| Hosmer-Lemeshow (post-calib) | HL = 403, p ≈ 0 | p ≥ 0.05 | ⚠ Large n (538K) — HL has near-infinite power |
| Mean PD (calibrated) | 25.27% | Matches actual DR | ✓ Calibrated |
| Score PSI (OOT vs train) | 0.282 | < 0.25 | ✗ ALERT — population shift 2016–18 |

### 4.2 LGD Model (OOT Defaulted Loans)

| Metric | Value |
|---|---|
| Stage 1 AUC | > 0.60 |
| LGD MAE | ~5% |
| Mean LGD (portfolio) | 92.19% |
| Downturn LGD (Basel) | 93.76% |

### 4.3 EAD Model

| Metric | Value |
|---|---|
| CCF MAE | ~14% |
| Total EAD (portfolio) | $3.26B |

### 4.4 Portfolio-Level Outputs (calibrated PD)

| Metric | Value |
|---|---|
| Total 12-mo EL | $0.808B |
| Total IFRS 9 lifetime ECL (base) | $1.601B |
| Total IFRS 9 ECL (§5.5.17 weighted) | $1.646B |
| IRB RWA | $14.07B |
| IRB Minimum Capital | $1.13B (34.5% of EAD) |
| RAROC (portfolio) | +299% (inflated — unsecured LGD ~93%) |

---

## 5. Model Limitations and Known Issues

| # | Limitation | Severity | Mitigation |
|---|---|---|---|
| L-1 | Score PSI = 0.282 (ALERT) — population shifted 2016–18 vs 2007–15 training | High | Monitor monthly; retrain trigger at PSI > 0.25 |
| L-2 | RAROC is computed on full portfolio including rejected-policy loans — not meaningful for capital planning | Medium | Compute RAROC on approved-only subset |
| L-3 | LGD ~93% is specific to unsecured consumer loans with low recovery — not transferable to secured lending | Medium | Document explicitly; recalibrate for secured books |
| L-4 | Reject inference via parceling adds only 3.1% synthetic rows — selection bias partially corrected | Low | Full augmentation requires external reject data |
| L-5 | Macro scenario PD sensitivities (β_unem = 0.18, β_gdp = 0.10) are literature-based, not empirically estimated | Medium | Estimate from macro time series when available |
| L-6 | No external validation — model validated on OOT holdout only | Medium | Independent model validation review required pre-production |

---

## 6. Governance

| Role | Name / Team | Responsibility |
|---|---|---|
| **Model owner** | Credit Risk Analytics | Development, documentation, ongoing monitoring |
| **Model validator** | Independent Validation Unit | Pre-deployment sign-off, annual review |
| **Business sponsor** | Chief Risk Officer | Approve use for regulatory capital / IFRS 9 |
| **Technology owner** | Data Engineering | Pipeline deployment, data quality |
| **Compliance** | Legal / ECOA | Adverse action code correctness (Reg B) |

### Approval status

| Gate | Status | Date |
|---|---|---|
| Development complete | ✅ Done | 2026-06-07 |
| Independent validation | ⏳ Pending | — |
| Business sign-off (CRO) | ⏳ Pending | — |
| Production deployment | ⏳ Pending validation | — |

---

## 7. Model Validation Summary (SR 11-7 §4)

### Conceptual soundness
- Logistic regression with WoE encoding is industry standard for scorecard models (BCBS 2005, EBA 2017a).
- Two-stage LGD correctly handles the bimodal recovery distribution.
- IFRS 9 three-stage ECL with SICR rules matches EBA/GL/2017/06 guidance.
- Scenario-weighted ECL implements IFRS 9 §5.5.17 probability-weighted approach.

### Outcome analysis
- Monotonic bad rate confirmed across all 10 score deciles (decile analysis in L02).
- Reliability diagram confirms post-calibration level accuracy.
- Vintage analysis (L03) confirms predicted PD tracks actual default rate by cohort.
- Champion/Challenger (L04): incumbent Gini 0.387 retained vs challenger 0.387 — no deterioration.

### Ongoing monitoring plan
- **Daily:** PSI computed by DAG-06 (6am); alert fires if PSI > 0.25.
- **Monthly:** CSI per variable, decile stability, vintage update.
- **Quarterly:** Full model performance review (AUC, Gini, KS, Brier).
- **Annual:** Full recalibration review; trigger earlier if PSI ALERT persists > 2 months.
- **Retrain trigger:** PSI > 0.25 sustained OR Gini drops > 5pp below baseline (0.387).

---

## 8. Key Artifacts and References

| Artifact | Location |
|---|---|
| Preprocessing notebook | `notebooks/L01_Preprocessing_Feature_Engineering.ipynb` |
| PD model notebook | `notebooks/L02_PD_Model_Scorecard.ipynb` |
| LGD/EAD/ECL notebook | `notebooks/L03_LGD_EAD_Expected_Loss.ipynb` |
| PSI monitoring notebook | `notebooks/L04_Population_Stability_Index.ipynb` |
| PD calibrator | `models/preprocessing/pd_calibrator.py` + `data/models/pd_calibrator.json` |
| Scenario ECL config | `data/models/ifrs9_scenarios.json` |
| Scorecard | `data/processed/scorecard.csv` |
| Model artifacts | `data/models/{lgd_stage1,lgd_stage2,ead_model,ead_scaler}.pkl` |
| IFRS 9 provisions | `data/reports/L03_ifrs9_provisions.csv` |
| Scenario ECL results | `data/processed/ifrs9_scenario_ecl.parquet` |
| Implementation plan | `docs/Credit_Risk_Implementation_Plan_v4_NextUpdate.md` |

### Regulatory references
- Basel Committee on Banking Supervision (2005). *International Convergence of Capital Measurement and Capital Standards* (Basel II). §468 PD estimation.
- EBA (2017a). *Guidelines on PD estimation, LGD estimation and the treatment of defaulted exposures.* EBA/GL/2017/16.
- IASB (2014). *IFRS 9 Financial Instruments.* §5.5 Impairment — §5.5.17 multiple scenarios.
- EBA (2017b). *Guidelines on credit institutions' credit risk management practices.* EBA/GL/2017/06.
- Federal Reserve (2011). *SR 11-7: Guidance on Model Risk Management.* Board of Governors.
- Bellotti, T. & Crook, J. (2009). Support vector machines for credit scoring and discovery of significant features. *Expert Systems with Applications*, 36(2), 3302–3308.
