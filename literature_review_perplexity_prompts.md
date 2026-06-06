# Perplexity Prompts — Literature Review
## For: "A Production-Grade Credit Risk Modeling System on the Lending Club Dataset"

> **How to use**
> - Paste each prompt **exactly as written** into Perplexity AI
> - Every prompt instructs Perplexity to write in **Markdown** and list all source URLs
> - Copy the full Markdown output into your notes file
> - Run all 8 prompts in order — they build on each other
> - After collecting all 8 outputs, combine them into Section 2 of your paper

---

---

## PROMPT 1 — Classical Credit Scoring (Foundation)

```
Write a literature review paragraph in academic English about the history
and development of classical credit scoring models in banking. Cover the
following works in chronological order:

- Beaver (1966): univariate financial ratio analysis for predicting firm
  failure
- Altman (1968): the Z-score model for corporate bankruptcy prediction
- Wiginton (1980): first application of logistic regression to consumer
  credit scoring
- Steenackers & Goovaerts (1989): logistic regression for credit scoring
  in retail banking
- Siddiqi (2006): "Credit Risk Scorecards" as the canonical industry
  reference for scorecard development using Weight of Evidence (WoE) and
  Information Value (IV)
- Thomas, Edelman & Crook (2002): "Credit Scoring and Its Applications"
  as the standard academic textbook

For each work, explain: (1) what it contributed, (2) its key methodology,
and (3) its limitation that motivated later research. Connect the works
into a coherent narrative showing how the field evolved from univariate
analysis → discriminant analysis → logistic regression → scorecards.

Write the output in Markdown format with proper academic citation style
(Author, Year) inline. At the end, list all sources with full titles,
authors, year, journal/publisher, and URL or DOI where available.
```

---

---

## PROMPT 2 — Machine Learning in Credit Scoring

```
Write a literature review paragraph in academic English about the
application of machine learning methods to credit scoring and default
prediction. Cover the following research areas:

1. Early ML benchmarks in credit scoring:
   - Baesens et al. (2003) "Benchmarking State-of-the-Art Classification
     Algorithms for Credit Scoring" — Journal of the Operational Research
     Society — compared neural networks, SVMs, logistic regression across
     credit datasets

2. Comprehensive benchmarking study:
   - Lessmann et al. (2015) "Benchmarking State-of-the-Art Classification
     Algorithms for Credit Scoring: An Update of Research" — European
     Journal of Operational Research — 41 classifiers, key finding that
     ensemble methods outperform logistic regression in AUC

3. Consumer credit risk with ML:
   - Khandani, Kim & Lo (2010) "Consumer Credit-Risk Models via
     Machine-Learning Algorithms" — Journal of Banking & Finance

4. Gradient boosting in credit:
   - Research showing XGBoost and LightGBM outperforming logistic
     regression for credit default prediction (cite 2–3 relevant papers
     from 2017–2023)

5. The interpretability vs accuracy trade-off:
   - Why banks still prefer logistic regression despite lower accuracy
   - Regulatory interpretability requirements as a constraint on ML adoption

For each work explain: (1) what classifiers were compared, (2) key findings
on performance metrics (AUC, Gini), (3) datasets used, and (4) limitations.
End the paragraph by identifying the gap: most studies stop at model
evaluation and do not address production deployment, regulatory compliance,
or business policy integration.

Write the output in Markdown format with (Author, Year) inline citations.
At the end, list all sources with full title, authors, year, journal, and
URL or DOI.
```

---

---

## PROMPT 3 — Studies Using the Lending Club Dataset

```
Write a literature review paragraph in academic English specifically about
academic research that has used the Lending Club peer-to-peer lending
dataset for credit risk modeling. I need you to find and discuss at least
5 published papers or preprints that used this dataset.

For each paper cover:
1. Full citation (authors, year, title, journal or conference)
2. Research question the paper addressed
3. Which features or subsets of the 151 columns they used
4. Machine learning methods or statistical models applied
5. Evaluation metrics reported (AUC, Gini, KS, accuracy, F1)
6. Key results and findings
7. Limitations of the study

Also address:
- Why the Lending Club dataset became popular in academic credit risk
  research (availability, size, real-world lending context)
- What the dataset's known limitations are for research purposes
  (P2P lending context vs traditional bank, platform shutdown, data quality)
- What the ~17% default rate implies for class imbalance in modeling

Connect the papers to show what has already been done and where gaps remain.
Conclude by stating what this project adds that prior Lending Club studies
have not addressed.

Write the output in Markdown format with (Author, Year) inline citations.
At the end, list every source with full title, authors, year, venue, and
direct URL or DOI. Also include the direct URL to the Lending Club dataset
on Kaggle.
```

---

---

## PROMPT 4 — Basel II, Basel III & Regulatory Capital Framework

```
Write a literature review paragraph in academic English about the Basel II
and Basel III regulatory frameworks for credit risk and their impact on
credit scoring model development in banks.

Cover the following in this order:

1. Basel I (1988): original capital accord — flat 8% requirement,
   limitation of not differentiating risk levels

2. Basel II (2004): three pillars, introduction of the Internal
   Ratings-Based (IRB) approach, how it allowed banks to use their own
   PD/LGD/EAD models for capital calculation, Capital Adequacy Ratio
   formula (CAR = Bank Capital / RWA), the competitive advantage of
   better internal models

3. The 2008 financial crisis: how Basel II's procyclicality and model
   failures contributed to systemic risk, as documented in academic
   and regulatory post-mortems

4. Basel III (2010, finalized 2017): what it added — capital conservation
   buffer, countercyclical buffer, leverage ratio, liquidity coverage ratio
   (LCR), Net Stable Funding Ratio (NSFR)

5. Advanced IRB (AIRB) approach: what validation regulators require before
   approving internal models

6. Academic commentary on Basel II/III — cite 3–4 academic papers that
   analyzed the regulatory framework's effect on bank lending or model risk

For each regulatory document and academic paper, explain what it requires
or found, and how it directly shapes the design choices in a credit risk
modeling system (interpretability, OOT validation, documentation).

Write the output in Markdown format with (Author/Institution, Year) inline
citations. At the end, list all sources including:
- Direct BIS document URLs (bis.org)
- Academic paper DOIs or URLs
- Any central bank guidance URLs
```

---

---

## PROMPT 5 — IFRS 9 Expected Credit Loss Framework

```
Write a literature review paragraph in academic English about the IFRS 9
Expected Credit Loss (ECL) accounting standard and its implications for
credit risk modeling in banks.

Cover the following:

1. Background: IAS 39 incurred loss model — the "too little, too late"
   criticism exposed by the 2008 financial crisis

2. IFRS 9 (IASB, 2014): the three-stage ECL framework
   - Stage 1: 12-month ECL for performing loans
   - Stage 2: lifetime ECL for loans with significant increase in credit risk
   - Stage 3: lifetime ECL for credit-impaired loans
   How PD × LGD × EAD feeds into each stage

3. "Significant increase in credit risk" (SICR): how banks determine when
   a loan moves from Stage 1 to Stage 2 — the challenges of defining this
   threshold in practice

4. Forward-looking information requirement: how IFRS 9 requires
   macroeconomic scenarios to be incorporated into ECL estimates
   (unlike Basel II PD which is through-the-cycle)

5. Academic and industry research on IFRS 9 implementation challenges:
   - Data requirements
   - Model complexity vs Basel II PD models
   - Procyclicality concerns
   - EBA and BCBS guidance papers
   Cite at least 3–4 academic papers or regulatory impact studies

6. Comparison: Basel II capital PD (through-the-cycle, point-in-time)
   vs IFRS 9 ECL PD (point-in-time, forward-looking)

Write in Markdown format with (Author/Institution, Year) inline citations.
At the end, list all sources with:
- IFRS 9 standard URL (ifrs.org)
- EBA guidelines URLs (eba.europa.eu)
- BCBS guidance URLs (bis.org)
- Academic paper DOIs or URLs
```

---

---

## PROMPT 6 — SR 11-7 & Model Risk Management

```
Write a literature review paragraph in academic English about model risk
management in banking, focused on the Federal Reserve's SR 11-7 guidance
and its implications for machine learning model governance.

Cover the following in order:

1. What is model risk? Definition from SR 11-7: risk of adverse consequences
   from decisions based on incorrect or misused models. Two sources: model
   error and incorrect use.

2. SR 11-7 (Federal Reserve Board & OCC, April 2011):
   - What triggered it (post-2008 model failures)
   - The three components: model development & implementation, model
     validation, model governance & inventory
   - Documentation requirements: purpose, data, assumptions, validation
     results, limitations
   - Independent validation requirement: who validates and what they check

3. OCC Bulletin 2011-12: complementary guidance for national banks

4. Extension to ML/AI models: how SR 11-7 is being applied to models that
   go beyond traditional statistics — challenges of interpretability,
   explainability requirements, black-box concerns
   - Cite Federal Reserve or OCC guidance specifically addressing ML models
     (2019–2023 guidance if available)

5. Academic commentary on model risk management:
   - Papers on model risk in banking (cite 3–4)
   - Papers on the tension between ML accuracy and regulatory interpretability

6. Industry surveys: what percentage of banks have a formal Model Risk
   Management function? How has this changed post-SR 11-7?

Write in Markdown format with (Author/Institution, Year) inline citations.
At the end, list all sources with direct URLs including:
- SR 11-7 full text URL (federalreserve.gov)
- OCC Bulletin 2011-12 URL (occ.gov)
- Any Fed/OCC follow-up guidance on AI/ML
- Academic paper DOIs or URLs
```

---

---

## PROMPT 7 — Weight of Evidence, Information Value & Scorecard Methodology

```
Write a literature review paragraph in academic English about the Weight
of Evidence (WoE) and Information Value (IV) methodology used in credit
risk scorecard development.

Cover the following:

1. Origins of WoE in credit scoring: when and where this methodology was
   first formalized — trace it from information theory (Shannon entropy)
   to its application in credit scoring

2. WoE formula and interpretation:
   WoE_i = ln(% Goods_i / % Bads_i)
   Positive WoE = lower risk, negative WoE = higher risk
   Cite the academic or industry source that established this formula

3. Information Value (IV):
   IV = Σ (% Goods_i - % Bads_i) × WoE_i
   The interpretation table (< 0.02 useless, 0.02–0.10 weak, etc.)
   Where does this interpretation scale come from? Cite the original source.

4. Fine classing and coarse classing methodology: how continuous variables
   are binned and then merged based on WoE monotonicity

5. Missing value treatment as a separate WoE bin: academic justification
   for this approach vs imputation

6. PDO (Points to Double the Odds) scaling:
   Factor = PDO / ln(2), Offset = Reference_Score - Factor × ln(Reference_Odds)
   Historical origin of the 300–850 FICO score range and the 20 PDO
   convention — cite Fair Isaac Corporation or academic sources

7. Comparison of WoE-based scorecards vs raw logistic regression vs ML:
   advantages (interpretability, monotonicity, regulatory acceptance) and
   disadvantages (information loss from binning)

Write in Markdown format with (Author, Year) inline citations. At the end,
list all sources with full titles, authors, year, publisher/journal, and
URL or DOI. Include:
- Siddiqi (2006) "Credit Risk Scorecards" (Wiley)
- Thomas, Edelman & Crook (2002)
- Fair Isaac Corporation / FICO documentation URLs
- Any academic papers specifically on WoE methodology
```

---

---

## PROMPT 8 — Production ML Systems, MLOps & Data Engineering for Credit

```
Write a literature review paragraph in academic English about the gap
between academic credit scoring research and production-ready ML systems
in banking — covering MLOps, data engineering pipelines, and model
monitoring for credit risk applications.

Cover the following:

1. The research-to-production gap in ML:
   - Academic papers typically evaluate models on static datasets without
     addressing deployment, monitoring, or regulatory integration
   - Cite papers or industry reports that document this gap in financial ML
     (e.g., Sculley et al. 2015 "Hidden Technical Debt in Machine Learning
     Systems" — NeurIPS — as a foundational reference)

2. MLOps for financial services:
   - Definition of MLOps (ML + DevOps): experiment tracking, model
     registry, CI/CD for models, monitoring
   - Unique requirements in banking: audit trail, model versioning, stage
     gates for regulatory review
   - MLflow as an experiment tracking and registry tool: cite documentation
     and any published use cases in finance

3. Data engineering pipelines for credit:
   - Apache Airflow for pipeline orchestration in financial services:
     cite use cases or engineering blog posts from banks
   - Apache Spark (PySpark) for large-scale credit data processing:
     why distributed processing is needed for millions of loan records
   - Great Expectations for data quality validation: regulatory requirement
     for validated model inputs under SR 11-7

4. Population Stability Index (PSI) and model monitoring:
   - Academic or industry references that formalized PSI for credit model
     monitoring (find the original paper or textbook that introduced PSI)
   - The PSI thresholds (< 0.10, 0.10–0.25, > 0.25) — where do these
     specific numbers come from? Find the original source.
   - Model drift detection methods beyond PSI: characteristic stability
     index (CSI), performance monitoring, shadow models

5. Real-time model serving for credit decisions:
   - Latency requirements in retail banking credit scoring
   - Feature stores (Redis, Feast) for real-time feature retrieval
   - API-based credit scoring architectures in fintech

Conclude by identifying what this paper contributes that existing literature
does not: a fully integrated system combining data engineering, model
training with regulatory-compliant feature selection, a credit policy engine,
IFRS 9 and Basel III reporting, and production monitoring — all on a single
publicly available dataset.

Write in Markdown format with (Author/Institution, Year) inline citations.
At the end, list ALL sources with full title, authors, year, venue/publisher,
and direct URL or DOI. Include:
- Sculley et al. 2015 NeurIPS URL
- MLflow documentation URL
- Apache Airflow documentation URL
- Apache Spark documentation URL
- Great Expectations documentation URL
- Any academic papers on ML monitoring or model drift detection
- Any banking engineering blog posts cited (with URLs)
```

---

---

## AFTER COLLECTING ALL 8 OUTPUTS — ASSEMBLY PROMPT

Once you have run all 8 prompts and saved the outputs, paste this final
prompt into Perplexity to generate the complete assembled literature review:

```
I have eight literature review sections written in Markdown about credit
risk modeling. I will paste them below. Please do the following:

1. Combine them into a single cohesive Section 2 "Literature Review" for
   an academic research paper, with the following subsections:
   - 2.1 Classical Credit Scoring
   - 2.2 Machine Learning in Credit Scoring
   - 2.3 Prior Work on the Lending Club Dataset
   - 2.4 Regulatory Frameworks (Basel II/III, IFRS 9, SR 11-7)
   - 2.5 Scorecard Methodology (WoE, IV, PDO Scaling)
   - 2.6 Production ML Systems and Model Monitoring
   - 2.7 Research Gap and Contribution of This Paper

2. Remove any repeated citations — cite each work only once in the main
   text, then list it once in the consolidated reference list at the end.

3. Add smooth transition sentences between subsections so it reads as one
   coherent narrative, not eight disconnected blocks.

4. Section 2.7 should explicitly state the research gap in 3–4 sentences
   and then list this paper's specific contributions in a numbered list.

5. Keep the output in Markdown format. Use ## for subsection headings,
   bold for key terms on first use, and (Author, Year) inline citations.

6. At the very end, produce a consolidated References section listing
   every cited work alphabetically by first author, with full title,
   authors, year, journal/publisher, and URL or DOI.

Here are my eight sections:
[PASTE SECTION 1 OUTPUT HERE]
[PASTE SECTION 2 OUTPUT HERE]
[PASTE SECTION 3 OUTPUT HERE]
[PASTE SECTION 4 OUTPUT HERE]
[PASTE SECTION 5 OUTPUT HERE]
[PASTE SECTION 6 OUTPUT HERE]
[PASTE SECTION 7 OUTPUT HERE]
[PASTE SECTION 8 OUTPUT HERE]
```

---

---

## QUICK REFERENCE — TARGET SOURCES PER PROMPT

| Prompt | Must-Have Sources | Target Journals / Institutions |
|--------|------------------|-------------------------------|
| 1 | Altman 1968, Siddiqi 2006, Thomas 2002 | Journal of Finance, Wiley |
| 2 | Baesens 2003, Lessmann 2015, Khandani 2010 | EJOR, J. Banking & Finance |
| 3 | 5+ Lending Club papers | SSRN, arXiv, IEEE, ACM |
| 4 | BIS 2004, BIS 2010, BIS 2017 | bis.org |
| 5 | IASB 2014, EBA guidelines | ifrs.org, eba.europa.eu |
| 6 | SR 11-7 (2011), OCC 2011-12 | federalreserve.gov, occ.gov |
| 7 | Siddiqi 2006, FICO docs | Wiley, myfico.com |
| 8 | Sculley 2015, MLflow, Airflow docs | NeurIPS, mlflow.org |

---

## CITATION FORMAT TO REQUEST (add to any prompt if needed)

If Perplexity does not cite sources automatically, add this line:

```
For every claim you make, add an inline citation in the format (Author, Year).
At the end of your response, list every source as:
[Number] Author(s). "Title." Journal/Publisher, Year. URL: [direct link]
```

---

*8 research prompts + 1 assembly prompt · Covers all of Section 2 of the paper*
