# Research Plan — Credit Risk Modeling in Banking
## Perplexity Research Prompts (with Citation Requirements)

> **How to use this document**
> - Paste each prompt directly into Perplexity AI (perplexity.ai)
> - Every prompt ends with an explicit instruction to cite sources
> - Copy the answer + all cited URLs into your notes before moving on
> - Prompts are grouped by slide section so each person can run only their assigned block
> - Estimated total: **42 prompts** covering all 91 sections

---

## ASSIGNMENT MAP

| Person | Prompt Block | Sections Covered |
|--------|-------------|-----------------|
| **Person 1** | Block 1–3 (Prompts 1–15) | F1–F5, L1–L25 |
| **Person 2** | Block 4–6 (Prompts 16–28) | L26–L44, P1–P14 |
| **Person 3** | Block 7–9 (Prompts 29–42) | P15–P38, Back Matter |

---

---

# BLOCK 1 — FOUNDATIONS OF CREDIT (Person 1)
*Covers: F1–F5, L1–L5*

---

### Prompt 1 — Definition of Credit & Banking Fundamentals

```
What is the formal definition of credit in banking? Explain the roles of the
creditor (lender) and debtor (borrower), how interest works as compensation
for lending risk, and how credit differs from a cash transaction. Include the
legal and economic basis for credit relationships in commercial banking.
Also briefly describe the three main categories of credit products used by
retail banks: credit cards (revolving unsecured), home loans (secured
fixed-term), and asset financing (secured business loans). Explain what
collateral is and why it matters.

Please cite all sources including URLs.
```

---

### Prompt 2 — Definition of Credit Risk & the 2008 Financial Crisis

```
What is the formal definition of credit risk in banking? Explain what a
lender loses when a borrower defaults (principal, interest, collection costs).
Then explain how the 2008 global financial crisis was caused or worsened by
poor credit risk estimation — specifically the role of subprime mortgages,
CDOs, and inadequate default probability models. What did banks fail to
measure correctly? What were the real-world consequences (bank failures,
unemployment, bailouts)?

Please cite all sources including URLs, preferably from academic papers,
BIS publications, Federal Reserve reports, or reputable financial news.
```

---

### Prompt 3 — How Banks Protect Against Credit Risk

```
What are the three main mechanisms banks use to protect themselves from
credit risk? Specifically explain:
1. Collateral requirements — how they work, legal process on default, types
   of collateral accepted
2. Risk-based pricing — how banks charge higher interest rates to riskier
   borrowers, and how this is calculated
3. Credit scoring — how statistical models predict default probability before
   a loan is approved

Which of these is most widely used in modern retail banking, and why?
Cite academic sources, bank regulatory guidelines, or industry reports.
Please include all source URLs.
```

---

### Prompt 4 — What Is Default? Banking Definition & Triggers

```
What is the legal and regulatory definition of loan default in retail
banking? Explain the "90 days past due" rule — where does it come from,
which regulatory framework mandates it, and how do banks apply it in
practice? Also explain these other default triggers used by banks:
- Charge-off (when a bank writes off a loan as uncollectable)
- Bankruptcy (personal and corporate)
- Loan fraud
- Loan restructuring under financial distress (how this differs from
  voluntary refinancing)

Cite Basel II or Basel III documents, IFRS 9, or central bank guidelines
where relevant. Please include all source URLs.
```

---

---

# BLOCK 2 — EXPECTED LOSS FORMULA: PD, LGD, EAD (Person 1)
*Covers: L6–L13*

---

### Prompt 5 — The Expected Loss Formula (EL = PD × LGD × EAD)

```
Explain the Expected Loss formula used in banking credit risk: EL = PD × LGD × EAD.
What does each component represent? Why do banks need to calculate Expected Loss —
how does it drive (1) loan pricing / interest rates, (2) loan loss provisions
held on the balance sheet, and (3) regulatory capital requirements under Basel II?

Who originally formalized this formula in the regulatory context? Is it from
Basel II documentation, academic research, or both? Provide the historical
origin of this framework.

Please cite all sources including URLs (prefer BIS, Federal Reserve, academic
journals, or bank risk management textbooks).
```

---

### Prompt 6 — Probability of Default (PD): Definition & Industry Practice

```
What is Probability of Default (PD) in credit risk modeling? Explain:
- The formal definition and units (percentage, time horizon)
- Why the industry standard time horizon is 12 months
- How PD is estimated from historical loan data in practice
- The difference between PD at origination vs lifetime PD
- How PD varies across borrower risk grades (e.g., investment grade vs
  subprime)
- Real-world PD ranges: what PD % is considered low risk, medium, and
  high risk in retail banking?

Cite Basel II/III documentation, academic papers on credit risk, or
industry reports from rating agencies (Moody's, S&P, Fitch).
Please include all source URLs.
```

---

### Prompt 7 — Loss Given Default (LGD): Definition & Industry Practice

```
What is Loss Given Default (LGD) in credit risk? Explain:
- The formal definition: proportion of the loan that cannot be recovered
- The range (0% to 100%) and what each extreme means
- What drives recovery rates: collateral type (real estate, equipment,
  unsecured), legal process speed, jurisdiction differences
- How LGD differs across loan types (mortgages, credit cards, corporate loans)
- Typical LGD values used in the industry for different asset classes
- The two-stage statistical model approach for estimating LGD (logistic +
  linear regression)
- How IFRS 9 and Basel II treat LGD estimation differently

Cite BIS documents, academic papers (e.g., from Journal of Banking & Finance),
or banking regulatory guidance. Include all source URLs.
```

---

### Prompt 8 — Exposure at Default (EAD) & Credit Conversion Factor (CCF)

```
What is Exposure at Default (EAD) in credit risk modeling? Explain:
- The definition: total outstanding balance owed at the moment of default
- How EAD is straightforward for fixed-term loans (mortgages, installment
  loans) vs complex for revolving credit (credit cards, credit lines)
- What the Credit Conversion Factor (CCF) is — why borrowers draw more
  credit before defaulting on revolving facilities
- How CCF is estimated using historical data and linear regression
- The regulatory requirement to clip CCF predictions to [0, 1]
- EAD treatment under Basel II Internal Ratings-Based (IRB) approach

Cite BIS Basel II documentation, academic papers, or industry risk
management textbooks. Please include all source URLs.
```

---

### Prompt 9 — Basel II & Capital Adequacy Ratio (CAR)

```
Explain the Basel II Accord in detail:
- Why was Basel II created? What problem did Basel I fail to solve?
- What are the three pillars of Basel II?
- How does Basel II define the Capital Adequacy Ratio (CAR)?
  Formula: CAR = Bank Capital / Risk-Weighted Assets (RWA)
- What does "risk-weighted" mean — how is RWA calculated?
- What is the minimum CAR required (8%)?
- What is the Internal Ratings-Based (IRB) approach and how does it allow
  banks to use their own PD/LGD/EAD models?
- What competitive advantage does a better PD model give a bank under IRB?
- How does Basel II differ from Basel III in terms of capital requirements?

Cite the official BIS Basel II document (2004), Basel III (2010/2017),
and academic commentary. Include all source URLs.
```

---

### Prompt 10 — Three Types of Loss: Expected, Unexpected, Exceptional

```
In bank credit risk management, what is the difference between:
1. Expected Loss (EL) — how is it covered? (interest rate pricing)
2. Unexpected Loss (UL) — how is it covered? (capital reserves)
   What statistical measure is used to define UL? (Value at Risk / CVaR?)
3. Exceptional / Catastrophic Loss — how is it assessed? (stress testing)

How do these three relate to Basel II's three pillars? What does "economic
capital" mean in this context? How do banks run stress tests for exceptional
loss scenarios?

Cite BIS publications, Federal Reserve guidance, academic papers in risk
management journals, or books by Hull, McNeil, or Bluhm on credit risk.
Please include all source URLs.
```

---

---

# BLOCK 3 — PD MODEL METHODOLOGY (Person 1)
*Covers: L14–L25*

---

### Prompt 11 — The PD Model Pipeline: From Data to Scorecard

```
Describe the standard 6-step pipeline used by banks to build a Probability
of Default (PD) model for retail credit:
1. Define Good/Bad borrowers (binary target variable)
2. Data preparation (fine classing, dummy encoding)
3. Feature selection using Weight of Evidence (WoE) and Information Value (IV)
4. Logistic regression model estimation
5. Model evaluation (AUC, Gini, KS)
6. Scorecard construction

Why is logistic regression the regulatory standard for PD models rather than
more complex ML models? What do Basel II and SR 11-7 say about model
interpretability? Cite bank modeling guidelines, BIS papers, SR 11-7
Federal Reserve guidance, and any academic papers on credit scoring pipelines.
Please include all source URLs.
```

---

### Prompt 12 — Weight of Evidence (WoE) and Information Value (IV)

```
What is Weight of Evidence (WoE) in credit risk modeling? Explain:
- The mathematical formula: WoE_i = ln(% Goods_i / % Bads_i)
- How to interpret positive, zero, and negative WoE values
- How WoE enables comparison of all variable categories on a single scale
- What "coarse classing" is and how WoE is used to merge bins
- Why missing values should be treated as their own WoE category rather
  than dropped or imputed

What is Information Value (IV)?
- The formula: IV = Σ (% Goods_i - % Bads_i) × WoE_i
- The IV interpretation table: < 0.02 useless, 0.02–0.10 weak, 0.10–0.30
  medium, 0.30–0.50 strong, > 0.50 suspicious (possible leakage)
- How IV is used for variable pre-selection before logistic regression

Cite textbooks or papers on credit scoring, banking industry references
(e.g., Siddiqi's "Credit Risk Scorecards"), or academic sources.
Please include all source URLs.
```

---

### Prompt 13 — Why Logistic Regression for Credit Risk?

```
Why is logistic regression the industry and regulatory standard for building
Probability of Default (PD) models in retail banking? Explain:
- Why linear regression fails for predicting probabilities (values outside [0,1])
- How the logistic (sigmoid) function solves this: bounded between 0 and 1
- The mathematical formulation: log-odds = β₀ + β₁X₁ + ... + βₙXₙ
- How to convert log-odds to a default probability
- How to interpret coefficients: positive β = lower default risk, negative
  β = higher default risk
- Why interpretability is a regulatory requirement (Basel II, SR 11-7)
- Why banks prefer logistic regression over neural networks or random forests
  for regulated models

Cite Basel II documentation, SR 11-7 Federal Reserve guidance (2011),
academic papers on logistic regression in credit scoring, and Hosmer &
Lemeshow (or equivalent statistics textbook). Include all source URLs.
```

---

### Prompt 14 — Fine Classing, Dummy Variables & Missing Values in Credit Modeling

```
In building credit risk models, explain these three data preparation steps:

1. Fine Classing for continuous variables: Why can't income or loan amount
   be used directly in logistic regression? How does binning into 50+ narrow
   intervals work before WoE transformation? What is coarse classing?

2. Dummy variable encoding: How does converting categorical variables
   (like credit grade or loan purpose) into binary 0/1 columns work?
   Why must one category always be dropped as a reference? What is
   the dummy variable trap / multicollinearity issue?

3. Handling missing data as a separate WoE bin: Why is this better than
   imputing or dropping? What behavioral information does missingness contain
   in credit data?

Cite credit scoring textbooks (Siddiqi, Thomas et al.), academic papers on
credit model feature engineering, or banking regulatory papers.
Please include all source URLs.
```

---

### Prompt 15 — Out-of-Time (OOT) Train/Test Split in Credit Models

```
Why do banks use Out-of-Time (OOT) splitting instead of random splitting
when validating credit risk models?

Explain:
- What OOT splitting means: train on earlier years, test on later years
- Why random splitting fails for time-series credit data (look-ahead bias,
  shared macroeconomic environment leaking between train and test)
- The typical OOT window used in retail credit: how many years of OOT
  data is considered sufficient?
- What is "data leakage" in this context and why is it dangerous?
- How WoE bins fitted on the training set must be applied unchanged to
  the OOT set

What do regulators (Basel II, SR 11-7) require for model validation periods?
Cite bank model validation guidance, academic papers on time-series
cross-validation in finance, or SR 11-7. Please include all source URLs.
```

---

---

# BLOCK 4 — SCORING, CUT-OFF & EVALUATION (Person 2)
*Covers: L26–L37*

---

### Prompt 16 — Credit Scorecard: Construction & Industry Standard Scaling

```
What is a credit scorecard in retail banking? Explain:
- How a logistic regression PD model is converted into a point-based scorecard
- The scaling formula: Score_i = -(β_i × Factor) + Offset
- What PDO (Points to Double the Odds) means — why 20 PDO is the industry
  standard, and the Factor = PDO / ln(2) ≈ 28.85 formula
- Why the reference score is often set at 600 (FICO convention)
- How the final credit score is calculated: sum of all category points
- How the FICO score relates to this methodology
- Why scorecards are preferred over raw probability output by loan officers
  and regulators

Cite Siddiqi's "Credit Risk Scorecards", FICO documentation, Fair Isaac
Corporation history, or academic papers on scorecard development.
Please include all source URLs.
```

---

### Prompt 17 — Credit Score Ranges, Cut-off Setting & Business Trade-offs

```
How do banks set lending cut-offs using credit scores or PD thresholds?
Explain:
- What a cut-off is: the score or PD threshold that separates approve from
  reject
- How cut-off setting is a business decision, not purely statistical
- The business trade-off: lower cut-off = more volume + more defaults;
  higher cut-off = less volume + better quality
- How ROC curves are used to choose the optimal cut-off
- Real-world examples of cut-off ranges used by banks (e.g., what credit
  score qualifies for a mortgage in the US?)
- How risk appetite and regulatory environment influence cut-off decisions
- What "reject inference" is: how banks handle the fact that they only
  observe outcomes on approved loans

Cite Fair Isaac (FICO), Consumer Financial Protection Bureau (CFPB),
academic papers on optimal cut-off selection, or banking industry reports.
Please include all source URLs.
```

---

### Prompt 18 — Classification Errors: False Positives & False Negatives in Credit

```
In credit risk, explain False Positives and False Negatives from the
bank's perspective:
- False Negative (Type II error): model predicted GOOD, borrower defaulted
  → direct financial loss
- False Positive (Type I error): model predicted BAD, borrower would have
  repaid → lost revenue / opportunity cost

How does the bank quantify the cost of each type of error? What is the
cost matrix approach to asymmetric misclassification costs in credit models?
How do banks balance these two errors? What is the role of the ROC curve
in this trade-off?

Also explain the confusion matrix: TP, TN, FP, FN in the credit context.
Why is accuracy alone a misleading metric when 90%+ of borrowers are good
(class imbalance)?

Cite academic papers on cost-sensitive classification, credit scoring
literature, or banking model validation frameworks. Include all source URLs.
```

---

### Prompt 19 — AUC, Gini Coefficient & KS Statistic for Credit Models

```
Explain the three main discrimination metrics used to evaluate credit
scoring models:

1. AUC (Area Under the ROC Curve): What does it measure? How is the ROC
   curve constructed? What does AUC = 0.5 mean vs 0.7 vs 0.9? What is
   the industry minimum acceptable AUC for retail credit models?

2. Gini Coefficient: How does Gini relate to AUC (Gini = 2×AUC - 1)?
   What is the Lorenz curve? What Gini values are considered acceptable
   (industry threshold: ≥ 0.40)?

3. Kolmogorov-Smirnov (KS) Statistic: How is KS calculated for credit
   models? What does it measure (maximum separation between good and bad
   score distributions)? What KS threshold is acceptable (typically ≥ 0.25)?

Why are all three needed together rather than just one metric?
Cite academic papers on credit model validation, bank model risk guidance,
or Basel II validation requirements. Please include all source URLs.
```

---

### Prompt 20 — Brier Score & Probability Calibration in Credit Models

```
What is the Brier Score and why is it used alongside AUC/Gini in credit
risk model evaluation?

Explain:
- The Brier Score formula: BS = (1/N) Σ (predicted_PD_i - actual_outcome_i)²
- What it measures: calibration — how close predicted probabilities are to
  actual observed default rates
- Interpretation: Brier Score of 0 = perfect, 0.25 = uninformative (equivalent
  to random), below 0.10 = well-calibrated in credit context
- Why a model can have high AUC but poor calibration (discrimination ≠ calibration)
- Platt scaling and isotonic regression as methods to re-calibrate a model
- Why IFRS 9 especially requires well-calibrated PD estimates (lifetime ECL)

Cite academic papers on probability calibration, IFRS 9 documentation,
or bank model validation literature. Please include all source URLs.
```

---

### Prompt 21 — Population Stability Index (PSI) & Model Monitoring

```
What is the Population Stability Index (PSI) in credit risk model monitoring?
Explain:
- The PSI formula: PSI = Σ (% New_i - % Original_i) × ln(% New_i / % Original_i)
- The standard interpretation table:
  PSI < 0.10 → stable (no action)
  0.10–0.25 → minor shift (investigate)
  > 0.25 → significant shift (redevelop)
- Why the credit score PSI is the most critical single metric to monitor
  (more important than individual feature PSIs)
- Why models become outdated: economic cycles, demographic shifts, marketing
  channel changes, regulatory changes
- Typical monitoring schedule in practice (every 6–12 months or per N
  applications)
- What triggers a full model rebuild vs recalibration?

Cite SR 11-7 (Federal Reserve model risk guidance), OCC/Basel guidelines
on model validation, or academic papers on credit model monitoring.
Please include all source URLs.
```

---

### Prompt 22 — LGD Two-Stage Model & EAD Model Methodology

```
Explain the two-stage modeling approach for Loss Given Default (LGD):
- Stage 1 (Logistic Regression): predicting whether any recovery will occur
  at all (binary: yes/no)
- Stage 2 (Linear Regression): predicting how much is recovered, given that
  some recovery occurs
- Combined formula: LGD = 1 - (Stage1_probability × Stage2_recovery_rate)
- What data is used (charged-off accounts with observation time for full
  recovery)
- Why beta regression is theoretically preferable to linear regression for
  recovery rates bounded in [0,1], and why linear regression is used in
  practice

Also explain EAD modeling:
- Linear regression on the Credit Conversion Factor (CCF)
- What CCF = Outstanding / Limit means
- Why predictions are clipped to [0, 1]

Cite Basel II/III IRB documentation, academic papers on LGD and EAD
modeling, or BIS working papers. Include all source URLs.
```

---

---

# BLOCK 5 — PROJECT ARCHITECTURE & DATA ENGINEERING (Person 2)
*Covers: P1–P14*

---

### Prompt 23 — Lending Club Dataset: Background & Industry Context

```
What is the Lending Club peer-to-peer lending dataset (2007–2018)?
Explain:
- What Lending Club was as a company: peer-to-peer lending, how it worked,
  its rise and regulatory challenges
- Why this dataset is commonly used for credit risk modeling research and
  education
- The dataset's key statistics: ~2.26M loans, 151 features, ~17% default rate
- What "Charged Off" status means in this dataset vs "Fully Paid"
- Why the dataset covers 2007–2018 and why this period is particularly
  interesting (includes the 2008 financial crisis recovery and 2016–2018
  period)
- What Out-of-Time (OOT) splitting means for this dataset

Please also provide the Kaggle or original source URL for the dataset, and
cite any academic papers that have used this dataset for credit risk research.
Include all source URLs.
```

---

### Prompt 24 — Apache Airflow in Bank Data Engineering

```
What is Apache Airflow and why is it used in bank data engineering pipelines
for credit risk?

Explain:
- What a DAG (Directed Acyclic Graph) is in the context of Airflow
- Why banks require auditable pipeline runs (regulatory requirement)
- How Airflow handles scheduling, retry logic, and SLA monitoring
- Which major banks or financial institutions use Airflow in production?
  (JPMorgan, Barclays, or other reported uses)
- How Airflow compares to alternatives (Luigi, Prefect, Dagster) for
  regulated banking workflows
- What "data lineage" means in a bank context and how Airflow supports it

Cite Airflow documentation, banking industry use cases, or engineering
blog posts from financial institutions. Please include all source URLs.
```

---

### Prompt 25 — PySpark & Big Data Processing in Banking

```
Why do banks use Apache Spark (PySpark) for credit risk data processing?
Explain:
- What PySpark is and how it enables distributed data processing
- Scale challenges in retail banking: how many loan records does a large
  bank process daily? (e.g., millions of records)
- Why PySpark is preferred over pandas for production credit pipelines
  (scale, fault tolerance, cluster deployment)
- How PySpark integrates with data lakes (HDFS, S3/MinIO) and data
  warehouses (PostgreSQL, Hive)
- Which banks or financial institutions are known to use Spark in production?

Also briefly explain:
- What Great Expectations is and why data quality validation is a regulatory
  requirement for model inputs under SR 11-7
- What dbt (data build tool) is and why banks use it for SQL transformations

Cite Apache Spark documentation, banking engineering blogs, or industry
reports. Please include all source URLs.
```

---

### Prompt 26 — MLflow & Model Governance in Banking

```
What is MLflow and why is it used for credit risk model governance in banks?
Explain:
- What MLflow tracks: experiments, parameters, metrics, artifacts, models
- The model lifecycle in banking: Experiment → Staging → Production with
  risk committee review gates
- How MLflow's model registry satisfies SR 11-7 model documentation
  requirements
- What the SR 11-7 guidance (Federal Reserve 2011) requires for model risk
  management: documentation, validation, ongoing monitoring
- What "model risk" means in banking regulation and why it became a major
  focus after the 2008 crisis
- How MLflow compares to alternatives (Weights & Biases, Neptune, DVC) for
  regulated environments

Cite SR 11-7 Federal Reserve / OCC guidance (April 2011), MLflow
documentation, and banking technology adoption reports.
Please include all source URLs.
```

---

### Prompt 27 — Data Leakage in Credit Risk Models: Types & Prevention

```
What is data leakage in machine learning, and why is it a critical problem
in credit risk model building?

Explain specifically in the credit risk context:
- Target leakage: using variables that are only known after the loan outcome
  (e.g., total_pymnt, recoveries, last_pymnt_d in the Lending Club dataset)
- Train-test contamination: fitting WoE bins, imputers, or scalers on the
  full dataset including test data
- Time-based leakage: why random splits fail for time-series credit data

What are the consequences of deploying a model with data leakage?
What real-world examples exist of models failing in production due to leakage?

Cite academic papers on data leakage in ML (Kaufman et al. 2012 is a key
reference), credit model risk guidance (SR 11-7), and practical credit
scoring literature. Please include all source URLs.
```

---

### Prompt 28 — Decile Analysis & Scorecard Validation

```
What is decile analysis in credit scoring model validation?
Explain:
- How the borrower population is divided into 10 equal-size score buckets
  (deciles), from highest risk (Decile 1) to lowest risk (Decile 10)
- What "monotonic bad rate" means and why it is required for a valid scorecard
- The "top 3 deciles should capture > 50% of all defaulters" rule — where
  does this come from?
- How decile analysis complements AUC/Gini and KS as a validation tool
- What the Kolmogorov-Smirnov (KS) point on a decile chart corresponds to
- How decile lift charts are used to compare model vs random selection

Cite credit scoring literature (Siddiqi, Thomas), academic validation
papers, or bank model validation frameworks. Please include all source URLs.
```

---

---

# BLOCK 6 — MACHINE LEARNING IMPLEMENTATION (Person 3)
*Covers: P15–P26*

---

### Prompt 29 — Statsmodels vs Scikit-learn for Regulatory Credit Models

```
Why do bank credit risk modelers use Python's statsmodels library instead
of scikit-learn for logistic regression in regulated environments?

Explain:
- What Wald test p-values are and why they are required for regulatory
  model submissions (Basel II, SR 11-7)
- How statsmodels.api.Logit provides proper p-values and confidence intervals
  vs sklearn's LogisticRegression which does not
- What the Wald test formula is: (β / SE)² follows a chi-squared distribution
- How confidence intervals on coefficients are used in bank model documentation
- What "statistical significance" (p < 0.05) means in the context of feature
  selection for credit models
- Why retaining statistically insignificant features is problematic for
  interpretability and regulator approval

Cite statsmodels documentation, SR 11-7 (Federal Reserve 2011), academic
papers on logistic regression in credit scoring. Please include all source URLs.
```

---

### Prompt 30 — Iterative Feature Selection Using p-values

```
Explain the iterative backward feature selection method used in bank PD
models based on p-values:
- Start with all IV-selected candidate features
- Fit logistic regression
- Remove the variable with the highest p-value if it exceeds 0.05
- Repeat until all remaining features have p < 0.05

Why is p < 0.05 the standard threshold? What does it mean statistically?
How does this relate to Type I error rate?

How does this compare to other feature selection methods:
- LASSO regularization (L1 penalty)
- Recursive Feature Elimination (RFE)
- Stepwise AIC/BIC selection

Why does the banking regulatory environment favor the manual p-value loop
over LASSO or automated methods?

Cite academic papers on feature selection in logistic regression, credit
scoring literature (Siddiqi), and model validation guidance. Include all source URLs.
```

---

### Prompt 31 — Credit Scorecard PDO Scaling (Points to Double the Odds)

```
Explain the industry standard credit scorecard scaling methodology:
- What PDO (Points to Double the Odds) means mathematically
- Why 20 PDO is the standard (where does this convention come from?)
- The Factor formula: Factor = PDO / ln(2) ≈ 28.85 when PDO = 20
- The Offset formula: Offset = Reference_Score - Factor × ln(Reference_Odds)
- Why the reference score is typically set at 600 (corresponding to 50:1
  good-to-bad odds in FICO convention)
- How individual dummy variable score contributions are calculated:
  Contribution_i = -(β_i × Factor)

What is the historical origin of the 300–850 FICO score range? When was it
introduced and why these specific bounds?

Cite Fair Isaac Corporation (FICO) documentation, Siddiqi's
"Credit Risk Scorecards", or academic papers on scorecard scaling.
Please include all source URLs.
```

---

### Prompt 32 — Risk-Based Loan Pricing Using Expected Loss

```
How do banks use Expected Loss (EL = PD × LGD × EAD) to price loans?
Explain the economic logic of risk-based pricing:
- How the interest rate must cover: cost of funds + operating costs +
  expected loss + profit margin
- The formula: Minimum Rate = Cost_of_Funds + OpEx + (EL / Loan_Amount) + Profit_Margin
- How this differs from flat-rate pricing (charging everyone the same rate)
- What "risk-adjusted return on capital" (RAROC) means in lending decisions
- How ROI-based credit policy works: approve if (Interest_Income - EL) /
  Loan_Amount > hurdle rate
- Real-world evidence: does risk-based pricing reduce portfolio default rates?
  By how much?

Cite academic papers on risk-based pricing in lending, Federal Reserve
consumer credit reports, or banking economics papers.
Please include all source URLs.
```

---

### Prompt 33 — FastAPI & Real-Time Credit Scoring API Architecture

```
How do banks serve machine learning models in real time for credit scoring?
Explain:
- The architecture of a real-time credit scoring API: request → feature
  retrieval → model inference → decision → response
- Why FastAPI is used for ML model serving: async support, Pydantic
  validation, automatic OpenAPI docs
- What latency requirements exist in retail credit scoring: what p99 latency
  is acceptable (200ms? 500ms?) and why
- The role of Redis as a feature store / cache for sub-millisecond feature
  retrieval in real-time scoring
- What a typical JSON response from a credit scoring API contains: PD, LGD,
  EAD, EL, credit score, risk class, decision, model version
- How model versioning in the API enables A/B testing and rollback

Cite FastAPI documentation, ML serving architecture blogs (e.g., from
fintech engineering teams), or MLOps industry reports.
Please include all source URLs.
```

---

### Prompt 34 — SHAP, LIME & Explainability for Credit Models

```
What are SHAP values and LIME, and why are they important for credit risk
models?

Explain:
- What SHAP (SHapley Additive exPlanations) is: game-theoretic feature
  attribution, how it decomposes individual predictions
- What LIME (Local Interpretable Model-agnostic Explanations) is: local
  linear approximation of black-box models
- Why explainability is required by regulation: GDPR "right to explanation",
  ECOA / Equal Credit Opportunity Act (adverse action notices in US lending),
  EU AI Act (high-risk AI systems)
- How banks currently satisfy adverse action notice requirements for ML models
- Why boosting models (XGBoost, LightGBM) outperform logistic regression
  in discrimination but require SHAP/LIME for regulatory compliance
- Platt scaling: how to re-calibrate probability estimates from gradient
  boosting models

Cite GDPR Article 22, ECOA Regulation B, academic papers on SHAP
(Lundberg & Lee 2017), LIME (Ribeiro et al. 2016), and EU AI Act.
Please include all source URLs.
```

---

---

# BLOCK 7 — RISK MANAGEMENT & REGULATION (Person 3)
*Covers: P27–P32*

---

### Prompt 35 — IFRS 9 Expected Credit Loss Framework

```
Explain the IFRS 9 Expected Credit Loss (ECL) framework in detail:
- What IFRS 9 replaced (IAS 39) and why — the "too little, too late"
  problem exposed by the 2008 financial crisis
- The three-stage classification system:
  Stage 1 (12-month ECL): performing loans, PD < ~2%
  Stage 2 (Lifetime ECL): significant increase in credit risk, PD 2–15%
  Stage 3 (Lifetime ECL): credit-impaired / in default, PD ≥ 15%
- How banks determine "significant increase in credit risk" for Stage 2
  transfer
- The difference between 12-month ECL and lifetime ECL calculations
- How PD × LGD × EAD feeds into IFRS 9 provisions
- Implementation challenges: forward-looking information, macroeconomic
  scenarios, data requirements
- IFRS 9 effective date and which jurisdictions adopted it

Cite IASB IFRS 9 standard (2014), BCBS guidance on credit risk and
accounting, EBA guidelines on ECL. Please include all source URLs.
```

---

### Prompt 36 — Basel III Capital Requirements & AIRB Approach

```
Explain the Basel III capital requirements for credit risk, specifically
the Advanced Internal Ratings-Based (AIRB) approach:
- How AIRB differs from the Standardized Approach: banks use their own
  PD, LGD, and EAD models
- The RWA formula under AIRB (the IRB formula from Basel II/III)
- The capital requirement: Capital = RWA × 8% (minimum Tier 1 + Tier 2)
- The capital conservation buffer (additional 2.5% under Basel III)
- What "regulatory capital" vs "economic capital" means
- How more accurate internal models give a bank a competitive advantage
  (lower RWA → lower capital → more loans can be issued with same capital)
- What validation requirements exist before a bank can use AIRB?
  (regulators must approve the internal models)
- How Basel III tightened Basel II: leverage ratio, liquidity coverage ratio,
  NSFR, stress testing requirements

Cite BIS Basel III documentation (2010, 2017 finalization), EBA guidelines,
Federal Reserve capital rule guidance. Include all source URLs.
```

---

### Prompt 37 — PSI Monitoring & Model Drift in Production

```
How do banks monitor credit risk models in production for population drift
and performance degradation?

Explain:
- What Population Stability Index (PSI) is and how to interpret it (< 0.10
  stable, 0.10–0.25 monitor, > 0.25 redevelop)
- Why the credit score PSI is the most important single monitor (vs
  individual feature PSIs)
- The typical monitoring cadence: monthly, quarterly, or per-application-volume
  triggers
- Characteristic Stability Index (CSI) — how it differs from PSI
- Gini drift monitoring: how model discrimination degrades over time
- What triggers a model recalibration vs a full rebuild?
- The "Model Risk Inventory" concept — how banks catalog, version, and
  periodically review all models in use (required by SR 11-7)

Cite SR 11-7 (Federal Reserve 2011), OCC Bulletin 2011-12, academic papers
on credit model monitoring, or model risk management frameworks.
Please include all source URLs.
```

---

### Prompt 38 — Credit Policy Engine & Automated Lending Decisions

```
How do banks implement automated credit policy engines that convert model
outputs into lending decisions?

Explain:
- How risk classes (e.g., AA through F, or similar tiered frameworks) are
  built from credit score ranges
- The three-tier decision structure: auto-approve, manual review, auto-reject
- How banks document lending criteria to comply with fair lending laws
  (Equal Credit Opportunity Act, Fair Housing Act in the US)
- The concept of "adverse action notices" — required when a credit application
  is denied
- The role of the credit policy committee in setting and reviewing cut-offs
  and risk class boundaries
- How ROI-based policy overlays work on top of credit score classes

Cite ECOA Regulation B (12 CFR Part 202), CFPB fair lending guidance,
banking industry credit policy frameworks, or academic papers on
automated credit decisions. Please include all source URLs.
```

---

### Prompt 39 — Grafana, Prometheus & ML Monitoring Infrastructure

```
How do financial institutions monitor machine learning models and data
pipelines using Prometheus and Grafana?

Explain:
- What Prometheus is: time-series metrics collection, scraping, alerting
- What Grafana is: visualization and dashboard layer on top of Prometheus
- What metrics are tracked in a bank ML monitoring setup:
  API latency (p50, p95, p99), data quality pass rates, PSI per feature,
  Gini drift, prediction distribution shifts, volume anomalies
- How alert thresholds are configured (e.g., alert when PSI > 0.25)
- What an on-call model risk workflow looks like when an alert fires
- How this monitoring infrastructure satisfies SR 11-7 ongoing monitoring
  requirements

Cite Prometheus documentation, Grafana documentation, MLOps industry
reports (e.g., from Evidently AI, WhyLabs, or similar monitoring platforms).
Please include all source URLs.
```

---

---

# BLOCK 8 — IMPLEMENTATION & GOVERNANCE (Person 3)
*Covers: P33–P38*

---

### Prompt 40 — SR 11-7 Model Risk Management Framework

```
Explain the Federal Reserve's SR 11-7 Guidance on Model Risk Management
(April 2011) in detail:

- What is "model risk" as defined by SR 11-7?
- The three elements of model risk: model error, incorrect use, model
  limitations not understood by users
- What documentation SR 11-7 requires: model purpose, data inputs,
  assumptions, mathematical detail, validation results, performance metrics,
  limitations
- The Model Risk Management (MRM) framework: model development, independent
  validation, ongoing monitoring, model inventory
- What "independent model validation" means: who validates and what they check
- What qualifies as a "model" under SR 11-7? (scoring models, stress testing
  models, valuation models)
- How SR 11-7 applies to machine learning / AI models (extended guidance)

Cite SR 11-7 itself (Federal Reserve Board / OCC, April 4, 2011), OCC
Bulletin 2011-12, subsequent Fed/OCC guidance on ML models.
Please include all source URLs.
```

---

### Prompt 41 — Agile Sprint Planning for ML Projects in Banking

```
How do banks and fintech companies organize machine learning project
delivery using Agile/Scrum methodology?

Explain:
- How a credit risk modeling project is broken into sprints (typically
  2-week sprints)
- What deliverables are expected per sprint in an ML context:
  Sprint 0 (exploration notebooks), Sprint 1 (infrastructure), Sprint 2
  (data pipeline), Sprint 3 (EDA), Sprint 4 (features), Sprint 5 (model),
  etc.
- How Model Governance Review gates are integrated into sprint delivery
  (not just at the end)
- The "Definition of Done" for an ML sprint: code tested, documented,
  peer-reviewed, metrics logged in MLflow
- How MLOps practices (CI/CD for ML, automated testing, model registry
  promotion) integrate with Agile delivery

Cite Scrum Guide, State of MLOps reports, banking technology project
management case studies, or engineering blogs from fintech firms.
Please include all source URLs.
```

---

### Prompt 42 — XGBoost, LightGBM & Future of Credit Scoring

```
What is the current state of machine learning in bank credit scoring —
are banks moving beyond logistic regression?

Explain:
- How gradient boosting models (XGBoost, LightGBM, CatBoost) compare to
  logistic regression for credit default prediction in academic studies
  (typical Gini improvement: 0.40 → 0.55+?)
- What prevents banks from deploying these models today: interpretability
  requirements, SR 11-7, regulatory approval, adverse action notice
  constraints
- How SHAP values are now being accepted by some regulators as a substitute
  for coefficient interpretability
- Which banks have publicly disclosed using ML beyond logistic regression
  for credit decisions?
- What the EU AI Act (2024) means for high-risk AI in credit scoring
- What the CFPB's recent guidance (2022–2024) on AI in credit decisions says

Cite academic benchmarking papers (e.g., papers comparing ML vs logistic
regression on Lending Club data), EU AI Act text, CFPB guidance, and
banking industry survey reports. Please include all source URLs.
```

---

---

## RESEARCH TIPS

### Citation Format to Request
Add this to the end of any prompt if Perplexity doesn't automatically cite well:
```
Please format your answer with numbered citations and provide the full URL
for every source you reference. Include: author/organization, title,
year, and direct URL.
```

### High-Quality Source Targets by Topic

| Topic | Target Sources |
|-------|---------------|
| Expected Loss, PD, LGD, EAD | BIS (bis.org), Journal of Banking & Finance |
| Basel II / Basel III | BIS official documents (bis.org/publ/) |
| IFRS 9 | IASB (ifrs.org), EBA (eba.europa.eu) |
| SR 11-7 | Federal Reserve (federalreserve.gov), OCC (occ.gov) |
| WoE / IV / Scorecard | Siddiqi "Credit Risk Scorecards" (Wiley), Thomas et al. |
| FICO Scores | myFICO.com, Fair Isaac Corp filings |
| AUC / Gini / KS | Hand & Till (2001), academic ML literature |
| PSI / Model Monitoring | SR 11-7, credit risk management textbooks |
| PySpark / Airflow | Apache documentation, engineering blogs |
| MLflow | MLflow.org, Databricks documentation |
| SHAP | Lundberg & Lee (2017) NeurIPS paper |
| LIME | Ribeiro et al. (2016) KDD paper |
| GDPR / ECOA / EU AI Act | EUR-Lex, CFPB.gov, regulations.gov |
| Lending Club Dataset | Kaggle, academic papers using the dataset |

---

*Total: 42 prompts · 9 blocks · Mapped to all 91 slide sections*
