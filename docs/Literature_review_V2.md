# 2. Literature Review

The study of credit risk has evolved over six decades from simple financial ratio inspection to sophisticated machine-learning pipelines operating under multi-layered regulatory oversight. This review traces that evolution across five thematic arcs: the classical statistical foundations of credit scoring (§2.1); the subsequent wave of machine-learning benchmarking (§2.2); prior empirical work using the Lending Club peer-to-peer dataset that motivates this study (§2.3); the regulatory and accounting frameworks that govern model design in practice (§2.4); the technical methodology of scorecard construction (§2.5); and the engineering discipline of production deployment and model monitoring (§2.6). The section concludes by identifying the gap that remains and stating the specific contributions of this paper (§2.7).

---

## 2.1 Classical Credit Scoring

Classical credit scoring developed through a sequence of methodological shifts that gradually moved banking from simple ratio inspection to statistically estimated scorecards. **Univariate financial ratio analysis** entered the scholarly record with Beaver's landmark study of firm failure, which demonstrated that single accounting ratios—especially cash-flow and profitability measures—could reliably separate failed from non-failed firms up to five years before failure; however, its univariate design treated each indicator in isolation and therefore could not capture the joint effect of multiple predictors (Beaver, 1966). Altman extended this insight by combining several financial ratios through **multiple discriminant analysis (MDA)** into the Z-score, a multivariate bankruptcy model that improved corporate distress prediction significantly over single-ratio approaches; nonetheless, the method depended on assumptions of linear separability and multivariate normality that subsequent researchers found restrictive in practical consumer-credit settings (Altman, 1968).

In consumer lending, Wiginton marked a major transition by applying **logistic regression** to credit behavior, replacing discriminant scoring with a probabilistic binary-response framework better suited to default/non-default outcomes and less dependent on distributional assumptions; though early logit models still offered limited transparency for operational implementation and variable engineering in retail portfolios (Wiginton, 1980). Steenackers and Goovaerts advanced this line in retail banking by deploying logistic regression for personal-loan credit scoring, helping establish the logit model as a workable method for banking decision systems, yet these models still left open the problem of transforming heterogeneous applicant characteristics into stable, interpretable inputs for production scorecards (Steenackers & Goovaerts, 1989).

The academic consolidation of the field came with *Credit Scoring and Its Applications*, which systematized the statistical, operational, and policy foundations of credit scoring and became the standard scholarly textbook linking earlier bankruptcy and consumer-credit models to modern banking practice (Thomas, Edelman, & Crook, 2002). The industry consolidation came with Siddiqi's *Credit Risk Scorecards*, which codified scorecard development around **Weight of Evidence (WoE)** and **Information Value (IV)**, showing how logistic regression could be embedded in an interpretable, governance-friendly scorecard workflow; its practical canonization also highlighted the limits of classical scorecards in handling nonlinear relationships and high-dimensional data, thereby motivating the wave of machine-learning research reviewed in the following subsection (Siddiqi, 2006). Taken together, the literature shows a coherent evolution from univariate ratio analysis, to discriminant analysis, to logistic regression, and finally to operational scorecards that translated statistical prediction into scalable banking practice.

---

## 2.2 Machine Learning in Credit Scoring

Building on the classical scorecard foundations described above, machine-learning research in credit scoring has progressively demonstrated that flexible nonlinear classifiers often outperform logistic regression in predictive accuracy, though adoption in regulated banking remains constrained by explainability, governance, and operational requirements. Early benchmark work by Baesens et al. compared a wide range of classifiers—including neural networks, support vector machines, decision trees, nearest-neighbor methods, naïve Bayes, discriminant analysis, and logistic regression—across eight real-life credit scoring datasets, showing that no single method dominated uniformly, but that several nontraditional classifiers were competitive with or better than logistic regression on rank-ordering measures such as **AUC (Area Under the Receiver Operating Characteristic Curve)**; however, the study was limited by the era's comparatively narrow computational search and limited attention to deployment or interpretability (Baesens et al., 2003). Lessmann et al. then greatly expanded the benchmark universe to 41 classifiers and found that ensemble learners delivered the strongest average discriminatory power, outperforming logistic regression on AUC in a statistically meaningful sense; yet this study also focused exclusively on predictive benchmarking rather than implementation, regulatory acceptability, or policy integration in bank decision processes (Lessmann et al., 2015). Khandani, Kim, and Lo extended machine learning in consumer credit risk by applying nonlinear, nonparametric algorithms to a large proprietary panel combining credit bureau information with customer transaction data from a major commercial bank between 2005 and 2009, finding materially improved out-of-sample prediction of delinquency and reporting economically meaningful estimated loss reductions under credit-line management scenarios; yet the paper emphasized forecasting gains and portfolio analytics more than transparent score construction, institution-wide governance, or supervisory usability (Khandani, Kim, & Lo, 2010).

In the more recent **gradient boosting** literature, XGBoost and LightGBM have repeatedly outperformed logistic regression because boosting captures nonlinearities, interactions, and heterogeneous segment behavior more effectively. Zedda compared XGBoost with logistic regression on 35,535 Italian SME cases across seven sectors and found broadly similar overall capability but meaningful sensitivity to cutoff choice and sectoral heterogeneity, tempering blanket claims of algorithmic superiority (Zedda, 2024). Dong, Xue, and Chen compared XGBoost and LightGBM for loan-default prediction and reported stronger classification performance for both boosting methods in a contemporary credit setting (Dong, Xue, & Chen, 2023), while a parallel LightGBM-based default study published in *BCP Business & Management* similarly confirmed high AUC performance for gradient-boosting architectures (Anonymous, 2022).

Despite these performance gains, the **interpretability-versus-accuracy trade-off** remains decisive: banks often continue to prefer logistic regression because coefficient-based models are easier to document, validate, monitor, explain to supervisors, and embed in scorecards and adverse-action workflows. The European Banking Authority's follow-up report on machine learning in IRB models explicitly highlights interpretability and explainability as obstacles to broader ML adoption, and model-risk guidance stresses documentation, validation, monitoring, and governance requirements that are easier to satisfy with simpler models (EBA, 2023). Taken together, this literature suggests that while machine learning has convincingly improved benchmark discrimination metrics, most studies remain centered on model comparison rather than the harder questions of production deployment, regulatory compliance, and integration with business policy—a gap this paper directly addresses.

---

## 2.3 Prior Work on the Lending Club Dataset

The evidence reviewed above on machine-learning methods has been applied to the **Lending Club** peer-to-peer lending dataset more extensively than to almost any other publicly available credit dataset. The Lending Club dataset became popular in academic credit-risk research primarily because it is publicly accessible—most notably through Kaggle's "All Lending Club loan data" repository covering loans issued between 2007 and 2018, with over one million observations and more than 140 columns spanning borrower demographics, loan terms, credit-bureau data, and repayment outcomes—and is rooted in a real-world lending context (Kaggle, 2018). A cleaned and purpose-built derivative dataset has also been deposited on Zenodo specifically for granting-model research, further lowering the barrier to reproducible experimentation (Zenodo, 2024).

Gupta, Gulati, and Chakrabarty examined which classifiers best distinguish "good" and "bad" loans in Lending Club data, comparing logistic regression, decision trees, random forests, support vector machines, and gradient boosting on metrics including accuracy, precision, recall, and F1, finding that tree-based ensembles offer higher classification performance but at the cost of reduced interpretability and potential overfitting (Gupta et al., 2022). Zhou et al. used Lending Club records jointly with other peer-to-peer datasets to study how feature selection and regularization can improve predictive accuracy in high-dimensional spaces, applying XGBoost, random forests, and penalized logistic regression and reporting AUC and **Kolmogorov–Smirnov (KS)** statistics as primary metrics, showing that gradient-boosting models outperform traditional logistic regression in this setting (Zhou et al., 2019). A complementary study published in *Entropy* compared deep-learning architectures and ensemble methods—neural networks, XGBoost, CatBoost, and LightGBM—against benchmark classifiers on over 140 attributes drawn from Lending Club and similar platforms, finding that gradient-boosting and deep models achieve the highest predictive performance but at the expense of transparency and complex preprocessing pipelines (Zhou, J. et al., 2022). More recently, Demajo et al. built a LightGBM model on a Lending Club dataset of approximately 2.9 million loans using application-time features such as credit score range, annual income, debt-to-income ratio, loan amount, interest rate, and term, complemented by post-hoc SHAP explainability tools; while reporting strong AUC gains over logistic regression, the study noted that model explanations can only partially mitigate interpretability concerns and did not address concrete regulatory-validation processes or bank-specific governance requirements (Demajo et al., 2025).

The dataset's known limitations for academic credit-risk research are increasingly recognized: the peer-to-peer platform context differs from regulated bank portfolios in underwriting standards, borrower mix, and macroeconomic exposure; the platform's eventual shutdown raises questions about survivorship bias and structural breaks in the data; and the raw dataset includes historical artifacts, missing values, and variables that would not be available at application time. The roughly 17% default rate implied by loan-status distributions means that **class imbalance**, while present, is less extreme than in traditional retail-credit portfolios, allowing standard classifiers to achieve reasonable performance without heavy resampling; however, many studies still treat the problem as a binary classification with static labels and do not fully exploit time-to-default information, dynamic covariates, or portfolio-level risk measures. Existing Lending Club studies have largely answered which algorithms best predict default and which input subsets matter most, but most work stops at offline model evaluation, does not design application-time scorecards that account for business constraints, and rarely addresses regulatory compliance, model-risk-management requirements, or deployment issues such as model monitoring and population stability—the combination of deficiencies that this paper addresses.

---

## 2.4 Regulatory Frameworks (Basel II/III, IFRS 9, SR 11-7)

The regulatory context in which credit scoring systems operate has evolved substantially over the past three decades, encompassing capital regulation, accounting standards, and model governance guidance. Together, these three bodies of rules transform credit scoring from a purely internal risk-ranking exercise into a regulated modeling system whose design must support capital calculation, supervisory validation, loss provisioning, and ongoing governance.

### Basel Capital Regulation

**Basel I** introduced the first internationally harmonized capital regime by requiring banks to hold capital equal to at least 8% of **risk-weighted assets (RWA)**; however, its broad risk buckets meant that loans with very different underlying credit quality could attract identical capital charges, giving banks little regulatory incentive to build finely differentiated credit scoring systems beyond internal portfolio management (BCBS, 1988). **Basel II** fundamentally changed this logic through its three-pillar structure—minimum capital requirements, supervisory review, and market discipline—and, most importantly for credit scoring, through the **Internal Ratings-Based (IRB) approach**, which allowed eligible banks to use their own estimates of **probability of default (PD)**, **loss given default (LGD)**, and **exposure at default (EAD)** within supervisory capital formulas, making the **Capital Adequacy Ratio** $CAR = \text{Bank Capital} / \text{RWA}$ directly sensitive to model outputs (BCBS, 2004; European Parliament, 2016). This created a clear competitive incentive to develop more accurate internal models because better-calibrated systems could reduce RWA and economize on scarce capital, while simultaneously triggering requirements for robust documentation, grade design, long-run calibration, and validation evidence acceptable to supervisors.

The 2008 financial crisis revealed that Basel II's risk sensitivity could amplify the credit cycle: when measured risk rose in downturns, required capital also rose, encouraging deleveraging precisely when the system was already under stress. Post-crisis analyses argued that point-in-time modeling, understated tail risk, and overreliance on internal models contributed to systemic fragility (Repullo, Saurina, & Trucharte, 2010; ECB, 2009; IMF, 2008). **Basel III** therefore retained the basic capital framework but added a **capital conservation buffer**, a **countercyclical capital buffer**, a **leverage ratio**, the **Liquidity Coverage Ratio (LCR)**, and the **Net Stable Funding Ratio (NSFR)**, while the 2017 finalization further constrained internal-model variability, reflecting a regulatory shift from pure model sophistication toward resilience and comparability (BCBS, 2010; BCBS, 2017). For banks using the **Advanced IRB (AIRB)** approach, supervisory approval now requires that rating systems be conceptually sound, based on relevant historical data, regularly reviewed, independently validated, and supported by audit trails and margin-of-conservatism adjustments (BCBS, 2022; EBA, 2017a; ECB, n.d.). Academic commentary reinforces these design implications: Repullo et al. demonstrate that Basel II's capital formulas can be materially procyclical unless inputs or outputs are smoothed; Fraisse, Lé, and Thesmar find that higher capital requirements reduce lending at both intensive and extensive margins; Kashyap, Stein, and Hanson argue that heightened capital requirements under Basel III have only modest long-run effects on loan pricing; and IMF cross-country analysis confirms that higher capital requirements can modestly raise lending spreads and reduce loan growth (Fraisse, Lé, & Thesmar, 2017; Kashyap, Stein, & Hanson, 2010; Cosimano & Hakura, 2011).

### IFRS 9 Expected Credit Loss Framework

**IFRS 9** replaced the backward-looking incurred loss model of IAS 39—widely criticized for recognizing credit losses "too little, too late"—with a forward-looking **Expected Credit Loss (ECL)** framework requiring banks to recognize allowances based on current and forecast conditions from initial recognition (IASB, 2014; FSI–BIS, 2015). Under IFRS 9's three-stage impairment model, Stage 1 exposures (performing loans without **Significant Increase in Credit Risk**, or SICR) carry a 12-month ECL; Stage 2 exposures (those with SICR) and Stage 3 exposures (credit-impaired loans) require lifetime ECL, with the full expression $ECL = \sum_{t} PD_{t} \times LGD_{t} \times EAD_{t}$ over the relevant horizon making PD–LGD–EAD modeling central to both accounting provisioning and regulatory capital (Bundesbank, 2019). A key practical challenge is defining the SICR threshold and thus the Stage 1–Stage 2 boundary: the standard deliberately avoids a prescriptive rule, instead requiring consideration of relative changes in lifetime default risk since origination, leading to diverse practices combining internal rating migration, absolute PD thresholds, credit-score movements, and qualitative indicators (AASB, 2014). IFRS 9 also explicitly mandates the incorporation of **forward-looking macroeconomic information**, requiring banks to construct probability-weighted scenario ECLs using GDP, unemployment, and house-price forecasts—in direct contrast to Basel II/III capital PDs, which are typically specified on a through-the-cycle basis and therefore less sensitive to short-run macroeconomic variation (BDO UK, 2024). The IASB's own literature review finds that IFRS 9 accelerates loss recognition relative to IAS 39 but can be procyclical because macro-scenario-driven ECLs rise in downturns, with the degree of procyclicality depending on banks' scenario design and SICR thresholds (IASB Staff, 2023; BCBS, 2021; ESRB, 2019). Empirical studies of European and Chinese banks document that IFRS 9 adoption increased loan-loss allowances and introduced more volatility linked to macroeconomic conditions, highlighting tensions between timely recognition and earnings smoothing (University of Bergamo, n.d.; PMC, 2024). For credit risk modelers, the duality of Basel II/III through-the-cycle capital PDs and IFRS 9 point-in-time accounting PDs—combined with the need to evidence SICR thresholds, scenario methodologies, and governance to auditors and supervisors—pushes the discipline toward greater transparency, robust out-of-time validation, clear documentation of model limitations, and close coordination between risk, finance, and accounting functions.

### SR 11-7 and Model Risk Management

**Model risk management** was formalized in the United States by **SR 11-7**, which defines model risk as the risk of adverse consequences from decisions based on incorrect or misused models and identifies two core sources: model error and inappropriate use (Federal Reserve Board, 2011). The guidance emerged in the aftermath of the 2008 financial crisis and established a comprehensive framework organized around three pillars: robust model development, implementation, and use; effective independent validation; and strong governance, policies, controls, and model inventory management. OCC Bulletin 2011-12 complemented SR 11-7 for national banks, helping standardize model inventories, validation functions, and three-lines-of-defense structures across U.S. banking organizations (OCC, 2011). Subsequent Federal Reserve and interagency guidance extended SR 11-7 explicitly to machine-learning and AI models, emphasizing that even advanced models must remain fit for purpose, support explainability, and be subject to back-testing, benchmarking, and governance controls; the 2021 interagency statement on model risk management for BSA/AML systems reaffirmed that existing MRM principles extend to complex analytics (Federal Reserve Board, 2019; Federal Reserve Board, OCC & FDIC, 2021; Federal Reserve Board, 2021). Academic commentary confirms that model risk in banking has evolved from a niche validation topic into a broad governance literature concerned with transparency, decision impact, and organizational control (Knowledge Mapping, 2023; ML in Banking, 2025), while the BIS Financial Stability Institute observes that banks often prefer models that are not globally most accurate if simpler or post-hoc-explainable alternatives are easier to validate, document, monitor, and defend to supervisors (BIS FSI, 2024; PwC, n.d.). Collectively, Basel II/III, IFRS 9, and SR 11-7 make bank credit scoring not just a predictive exercise but a supervised infrastructure in which interpretability, out-of-time validation, conservative calibration, and full documentation are central design constraints because model outputs affect capital, loan-loss provisioning, lending capacity, and regulatory approval.

---

## 2.5 Scorecard Methodology (WoE, IV, PDO Scaling)

The regulatory emphasis on interpretability described above has reinforced the enduring centrality of **scorecard methodology** in credit risk. WoE and IV occupy a distinctive position because they link the information-theoretic idea of evidence to a highly practical scorecard workflow built around binning, monotonic risk patterns, and transparent logistic modeling. Conceptually, WoE can be traced to Shannon's foundational formulation of information and entropy, which established the mathematical language of information measurement, and to Good's definition of "weight of evidence" as the logarithm of a Bayes factor; in credit scoring, this notion was operationalized as the log ratio of the distribution of goods to bads within a categorical bin (Shannon, 1948; Good, 1950).

In modern scorecard development, WoE for bin $i$ is formally defined as:
$$WoE_i = \ln\!\left(\frac{\%\,Goods_i}{\%\,Bads_i}\right)$$
so a positive WoE indicates that a bin contains a higher proportion of good accounts than bad accounts (lower risk than average), while a negative WoE indicates relatively higher risk; this formulation is canonically codified by Siddiqi (2006) and by Thomas, Edelman, and Crook (2002). Information Value aggregates these bin-level contrasts as:
$$IV = \sum_i \left(\%\,Goods_i - \%\,Bads_i\right) \times WoE_i$$
and the familiar interpretation scale—below 0.02 as useless, 0.02–0.10 as weak, 0.10–0.30 as medium, 0.30–0.50 as strong, and above 0.50 as suspiciously powerful—is generally attributed in industry and software documentation to Siddiqi (2006), making that text the main cited source of the rule-of-thumb scale.

The standard **fine classing and coarse classing** workflow first splits continuous variables into relatively granular bins, then merges adjacent bins to produce coarse classes with distinct and preferably monotonic WoE values, because monotonicity makes transformed predictors more stable, interpretable, and compatible with linear-logit scorecards (Thomas, Edelman, & Crook, 2002). Missing values are commonly treated as a separate WoE bin rather than imputed away, because in credit data missingness can itself be behaviorally informative—missing income or employment information may correlate with risk—and the separate-bin approach preserves this signal while keeping the scorecard transparent (Lund University, 2021).

**PDO (Points to Double the Odds) scaling** extends the WoE-logit framework into an operational score using:
$$Factor = \frac{PDO}{\ln(2)}, \quad Offset = Reference\_Score - Factor \times \ln(Reference\_Odds)$$
thereby mapping raw log-odds to a business-friendly point scale. The historical consumer-credit score range most widely recognized in the United States is the **FICO base-score range** of 300 to 850, as documented by Fair Isaac Corporation, while the convention that a fixed number of points doubles the odds—often 20 points in many scorecard implementations—has become a long-standing industry norm rather than a universal regulatory requirement (myFICO, n.d.; FICO Community, n.d.; World Bank, 2020).

Compared with raw logistic regression on unbinned variables, WoE-based scorecards handle nonlinearity through binning, simplify the treatment of missing values and outliers, produce monotonic partial effects that are easy to explain, and remain highly acceptable in regulated banking because every point assignment can be traced to a bin and a log-odds contribution. Compared with more flexible machine-learning methods, they sacrifice some predictive power and may lose information through discretization, but they gain transparency, stability, and easier validation under model-risk and regulatory frameworks. This trade-off makes scorecard methodology a natural complement to gradient-boosting approaches in a regulated deployment context, as the following subsection addresses.

---

## 2.6 Production ML Systems and Model Monitoring

Notwithstanding the sophistication of the methods reviewed in §2.2 and §2.5, academic credit scoring research typically stops at model comparison on static datasets and rarely addresses the engineering and governance work needed for production deployment. Sculley et al. described how real-world ML systems accrue **"hidden technical debt"** through entanglement, data dependencies, and fragile monitoring, arguing that focusing only on model accuracy while ignoring system-level concerns such as pipeline orchestration, testing, and drift detection is dangerous—a critique that applies directly to the Lending Club studies reviewed in §2.3, which benchmark algorithms without specifying deployment, monitoring, or regulatory integration (Sculley et al., 2015).

**MLOps** has emerged as the discipline that combines ML with DevOps to cover experiment tracking, model registries, CI/CD for models, and production monitoring; in financial services, this must be extended with audit trails, model versioning, and stage gates for regulatory review under frameworks such as SR 11-7 so that each model version, training run, and deployment decision is traceable and challengeable. **MLflow** provides open-source infrastructure for this lifecycle: its tracking API logs parameters, metrics, artifacts, and code, while its model registry manages versions and promotion stages ("Staging" → "Production"), enabling governance and lineage tracking aligned with banking expectations for model inventories and promotion workflows (MLflow, 2026).

Underneath the models, production credit-risk systems depend on robust **data engineering pipelines**. **Apache Airflow** is widely used to orchestrate batch workflows in banking—managing ingestion, transformation, and scoring DAGs with scheduling, dependencies, and logging, thereby providing the traceability and repeatability that auditors expect from regulated institutions (Astronomer, 2021; Gupta, 2025). **Apache Spark** (PySpark) offers a distributed analytics engine for large-scale data processing, making it possible to handle millions of loan records and high-dimensional feature sets in credit portfolios that exceed single-machine memory limits (Apache Spark, 2026). **Great Expectations** adds a data-quality and validation layer, defining testable assertions about data, running validations in pipelines, and automatically producing human-readable "Data Docs" that align closely with regulatory expectations that model inputs be validated and data-quality controls documented as part of model risk management (Great Expectations, 2024).

**Model monitoring** is another area where production practice outpaces the academic credit-scoring literature. The **Population Stability Index (PSI)** has become a standard tool in credit risk for detecting distributional shifts between training and live populations, typically defined as:
$$PSI = \sum_i \left(Observed_i - Expected_i\right) \times \ln\!\left(\frac{Observed_i}{Expected_i}\right)$$
with industry-standard thresholds of PSI < 0.10 indicating little or no shift, 0.10–0.25 indicating moderate shift, and ≥ 0.25 indicating significant shift that may warrant recalibration or retraining; these threshold bands are propagated primarily via practice guides and risk-education resources rather than a single canonical academic source (GARP, 2021; Arthur AI, 2025). Beyond PSI, production systems use **characteristic stability indices (CSI)** for individual features, performance monitoring tracking AUC, Gini, KS, and default rates over time, and shadow or **challenger models** that run in parallel to detect performance degradation—monitoring disciplines rarely treated systematically in credit-scoring research (MathWorks, n.d.). In retail banking and fintech, credit scoring systems often need latency on the order of tens to hundreds of milliseconds, pushing architectures toward API-based scoring services and feature stores such as **Redis** and **Feast** to serve real-time features while maintaining consistency between training and serving data. In regulated banking, MLOps must further integrate with credit-policy logic, IFRS 9 staging decisions, Basel III reporting, and model risk governance—an intersection rarely described in the academic scoring literature, which tends to treat accounting, capital models, and ML pipelines as separate concerns.

---

## 2.7 Research Gap and Contribution of This Paper

The foregoing review reveals a consistent structural gap in the credit risk literature. Academic credit scoring studies demonstrate that machine-learning methods improve discriminatory performance over classical logistic regression and scorecards, yet no published study on the Lending Club dataset—or on peer-to-peer lending data more broadly—integrates these findings into a single, end-to-end, reproducible system that also satisfies the design constraints imposed by Basel II/III, IFRS 9, and SR 11-7. Existing Lending Club studies restrict their scope to algorithmic benchmarking on static snapshots, do not impose the application-time data constraint that would be required in live lending, and address neither the scorecard architecture, credit-policy logic, regulatory reporting, nor the monitoring infrastructure necessary to operate such a model within a governed banking environment. The MLOps toolchain—experiment tracking, pipeline orchestration, data-quality validation, and PSI/CSI monitoring—that turns a trained model into a maintainable production asset is absent from the academic scoring literature almost entirely, and the dual PD challenge (through-the-cycle for capital, point-in-time for IFRS 9 provisioning) has never been demonstrated on a public dataset in a way that is fully reproducible.

This paper makes the following specific contributions to address that gap:

1. **Application-time feature discipline.** All predictors are restricted to information available at the moment of loan application, eliminating target leakage that affects many prior Lending Club studies and making the model deployment-ready by construction.

2. **Regulatory-compliant scorecard development.** A full WoE/IV transformation, PDO-scaled scorecard, and logistic regression pipeline are implemented alongside a gradient-boosting alternative, with both evaluated against Basel III interpretability requirements and SR 11-7 documentation standards.

3. **Credit-policy engine.** Model outputs are operationalized into a rule-based lending decision layer that maps model scores to accept/refer/reject decisions, expected loss estimates, and risk-based pricing, bridging the gap between model evaluation and business implementation that existing benchmarking studies leave open.

4. **IFRS 9 and Basel III reporting alignment.** The paper produces ECL estimates under the three-stage IFRS 9 framework and demonstrates how the same PD model can be calibrated for both regulatory capital (through-the-cycle) and accounting provisioning (point-in-time, forward-looking) purposes on a single public dataset.

5. **Production monitoring infrastructure.** PSI and CSI monitoring, MLflow experiment tracking, Apache Airflow pipeline orchestration, and Great Expectations data validation are implemented end-to-end on the Lending Club dataset, making the full architecture reproducible and inspectable by both researchers and practitioners.

---

## References

Altman, Edward I. (1968). Financial ratios, discriminant analysis and the prediction of corporate bankruptcy. *The Journal of Finance*, *23*(4), 589–609. https://doi.org/10.1111/j.1540-6261.1968.tb00843.x

Anonymous. (2022). Loan default prediction based on machine learning (LightGBM model). *BCP Business & Management*, *25*, 457–468. https://doi.org/10.54691/bcpbm.v25i.1857

Apache Spark. (2026). *Apache Spark™ – Unified engine for large-scale data analytics*. https://spark.apache.org

Arthur AI. (2025). *Population stability index (PSI) metrics – Arthur platform documentation*. https://docs.arthur.ai/docs/population-stability-index-psi-metrics

Astronomer. (2021). *The future of banking: How can Apache Airflow® help?* https://www.astronomer.io/blog/future-of-banking-apache-airflow/

Australian Accounting Standards Board (AASB). (2014). *IFRS 9 financial instruments – Summary (July 2014)*. https://www.aasb.gov.au/admin/file/content102/c3/M140_22.2_IFRS_9_Summary_July_14.pdf

Baesens, B., Van Gestel, T., Viaene, S., Stepanova, M., Suykens, J., & Vanthienen, J. (2003). Benchmarking state-of-the-art classification algorithms for credit scoring. *Journal of the Operational Research Society*, *54*(6), 627–635. https://doi.org/10.1057/palgrave.jors.2601545

Basel Committee on Banking Supervision (BCBS). (1988). *International convergence of capital measurement and capital standards*. Bank for International Settlements. https://www.bis.org/publ/bcbsc111.pdf

Basel Committee on Banking Supervision (BCBS). (2004). *International convergence of capital measurement and capital standards: A revised framework*. Bank for International Settlements. https://www.bis.org/publ/bcbs128.pdf

Basel Committee on Banking Supervision (BCBS). (2010). *Basel III: A global regulatory framework for more resilient banks and banking systems*. Bank for International Settlements. https://www.bis.org/publ/bcbs189.pdf

Basel Committee on Banking Supervision (BCBS). (2017). *High-level summary of Basel III reforms*. Bank for International Settlements. https://www.bis.org/bcbs/publ/d424_hlsummary.pdf

Basel Committee on Banking Supervision (BCBS). (2021). *The procyclicality of loan loss provisions: A literature review* (Working Paper No. 39). Bank for International Settlements. https://www.bis.org/bcbs/publ/wp39.htm

Basel Committee on Banking Supervision (BCBS). (2022). *CRE36 – IRB approach: Minimum requirements to use IRB approach*. Basel Framework, Bank for International Settlements. https://www.bis.org/basel_framework/chapter/CRE/36.htm

Baesens, B., Van Gestel, T., Viaene, S., Stepanova, M., Suykens, J., & Vanthienen, J. (2003). See above.

BDO UK. (2024). *IFRS 9 financial instruments – Expected credit losses guidance*. https://www.bdo.co.uk/en-gb/services/audit-assurance/ifrs/ifrs-9-financial-instruments

Beaver, William H. (1966). Financial ratios as predictors of failure. *Journal of Accounting Research*, *4*(Suppl.), 71–111. https://www.gsb.stanford.edu/faculty-research/publications/financial-ratios-predictors-failure

Bank for International Settlements, Financial Stability Institute (BIS FSI). (2015). *IFRS 9 and expected loss provisioning – Executive summary*. https://www.bis.org/fsi/fsisummaries/ifrs9.pdf

Bank for International Settlements, Financial Stability Institute (BIS FSI). (2024). *Managing explanations: How regulators can address AI explainability*. https://www.bis.org/fsi/fsipapers24.pdf

Board of Governors of the Federal Reserve System. (2011). *Supervisory guidance on model risk management (SR 11-7)*. https://www.federalreserve.gov/frrs/guidance/supervisory-guidance-on-model-risk-management.htm

Board of Governors of the Federal Reserve System. (2019). *Statement on the use of alternative data in credit underwriting*. https://www.federalreserve.gov/newsevents/pressreleases/files/bcreg20191203b1.pdf

Board of Governors of the Federal Reserve System. (2021). Supporting responsible use of AI and equitable outcomes in financial services [Speech by Governor Lael Brainard]. https://www.federalreserve.gov/newsevents/speech/brainard20210112a.htm

Board of Governors of the Federal Reserve System, Office of the Comptroller of the Currency (OCC), & Federal Deposit Insurance Corporation (FDIC). (2021). *Statement on model risk management for bank systems supporting Bank Secrecy Act/Anti-Money Laundering compliance*. https://www.federalreserve.gov/newsevents/pressreleases/files/bcreg20210409a2.pdf

Bundesbank, Deutsche. (2019). IFRS 9 from the perspective of banking supervision. *Monthly Report*, January 2019. https://www.bundesbank.de/resource/blob/773872/71c8cf60bc9784d052a5d5afd810f0d1/mL/2019-01-ifrs9-data.pdf

Cosimano, Thomas F., & Hakura, Dalia S. (2011). *Bank behavior in response to Basel III: A cross-country analysis* (IMF Working Paper No. 11/119). International Monetary Fund. https://www.imf.org/external/pubs/ft/wp/2011/wp11119.pdf

Demajo, L. M., et al. (2025). Explainable AI based LightGBM prediction model to predict default in social lending. *Results in Applied Mathematics*. https://www.sciencedirect.com/science/article/pii/S2667305325000407

Dong, X., Xue, W., & Chen, J. (2023). Analysis and comparison of loan default prediction models based on XGBoost and LightGBM algorithm. *Academic Journal of Computing & Information Science*, *6*(9), 32–37. https://doi.org/10.25236/AJCIS.2023.060905

European Banking Authority (EBA). (2017a). *Guidelines on PD estimation, LGD estimation and the treatment of defaulted exposures (EBA/GL/2017/16)*. https://www.managementsolutions.com/en/publications-and-events/regulatory-notes/technical-notes-on-regulations/guidelines-pd-estimation-lgd-estimation-and-treatment-defaulted-exposures

European Banking Authority (EBA). (2017b). *Guidelines on credit institutions' credit risk management practices and accounting for expected credit losses (EBA/GL/2017/06)*. https://www.eba.europa.eu

European Banking Authority (EBA). (2023). *Follow-up report on the use of machine learning in internal ratings-based models*. https://www.eba.europa.eu/publications-and-media/press-releases/eba-publishes-follow-report-use-machine-learning-internal

European Central Bank (ECB). (2009). Is Basel II pro-cyclical? A selected review of the literature. *Financial Stability Review* (special feature). https://www.ecb.europa.eu/pub/pdf/fsr/art/ecb.fsrart200912_03.en.pdf

European Central Bank (ECB). (n.d.). *Instructions for reporting the validation results of internal models*. https://www.bankingsupervision.europa.eu/activities/internal_models/shared/pdf/instructions_validation_reporting_credit_risk.en.pdf

European Parliament. (2016). *Basel II IRB approach: Review of the regulatory treatment of credit risk* (Study IDAN/2016/587366). https://www.europarl.europa.eu/RegData/etudes/IDAN/2016/587366/IPOL_IDA(2016)587366_EN.pdf

European Systemic Risk Board (ESRB). (2019). *The cyclical behaviour of the ECL model in IFRS 9*. https://www.esrb.europa.eu/pub/pdf/reports/esrb.report190318_reportonthecyclicalbehaviouroftheECLmodel~2347c3b8da.en.pdf

FICO Community. (n.d.). *Score-to-odds relationship example for FICO scores*. https://community.fico.com/s/blog-post/a5Q2E0000008eD9UAI/fico1573

Fraisse, H., Lé, M., & Thesmar, D. (2017). *The real effects of bank capital requirements* (ESRB Working Paper No. 47). European Systemic Risk Board. https://www.esrb.europa.eu/pub/pdf/wp/esrbwp47.en.pdf

Global Association of Risk Professionals (GARP). (2021). Probability of default: Pros and cons of the population stability index. *GARP Risk Intelligence*. https://www.garp.org/risk-intelligence/credit/probability-of-default-pros-and-cons-of-the-population-stability-index

Good, I. J. (1950). *Probability and the weighing of evidence*. Charles Griffin. https://www.cs.tufts.edu/~nr/cs257/archive/jack-good/weight-of-evidence.pdf

Great Expectations. (2024). *GX Core: Open source data quality platform*. https://greatexpectations.io

Gupta, A. (2025). How the banking industry relies on Apache Airflow. *LinkedIn Pulse*. https://www.linkedin.com/pulse/orchestrating-trust-data-how-banking-industry-relies-apache-gupta-ikvsc

Gupta, A., Gulati, P., & Chakrabarty, S. P. (2022). Classification based credit risk analysis: The case of Lending Club. arXiv preprint arXiv:2210.05136; published in *Lecture Notes in Networks and Systems*, *964*, 77–86, 2024. https://arxiv.org/abs/2210.05136

International Accounting Standards Board (IASB). (2014). *IFRS 9 financial instruments*. https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/

IASB Staff. (2023). *Summary of academic literature review on expected credit loss accounting* (Agenda Paper AP27D). https://www.ifrs.org/content/dam/ifrs/meetings/2023/february/iasb/ap27d-summary-of-academic-literature-review.pdf

International Monetary Fund (IMF). (2008). *The procyclical effects of Basel II* [Seminar paper]. https://www.imf.org/external/np/res/seminars/2008/arc/pdf/rs.pdf

Kaggle. (2018). *All Lending Club loan data* [Dataset]. https://www.kaggle.com/datasets/wordsforthewise/lending-club

Kashyap, A. K., Stein, J. C., & Hanson, S. G. (2010). *An analysis of the impact of "substantially heightened" capital requirements on large financial institutions* [Working paper]. Harvard Business School. https://stein.scholars.harvard.edu/file_url/271

Khandani, A. E., Kim, A. J., & Lo, A. W. (2010). Consumer credit-risk models via machine-learning algorithms. *Journal of Banking & Finance*, *34*(11), 2767–2787. https://www.sciencedirect.com/science/article/abs/pii/S0378426610002372

Knowledge Mapping of Model Risk in Banking. (2023). *[Author not stated in source]*. *Journal of Financial Stability* [or related]. https://www.sciencedirect.com/science/article/abs/pii/S1057521923003162

Lessmann, S., Baesens, B., Seow, H.-V., & Thomas, L. C. (2015). Benchmarking state-of-the-art classification algorithms for credit scoring: An update of research. *European Journal of Operational Research*, *247*(1), 124–136. https://doi.org/10.1016/j.ejor.2015.05.030

Lund University. (2021). *Weight of evidence transformation in credit scoring models* [Student thesis]. https://lup.lub.lu.se/student-papers/record/9066332/file/9067075.pdf

MathWorks. (n.d.). *Credit risk modeling: Importance and key components*. https://www.mathworks.com/discovery/credit-risk-modeling.html

ML in Banking Risk Management: Mapping a Decade of Research. (2025). *[Author not stated in source]*. https://www.sciencedirect.com/science/article/pii/S2667096825000060

MLflow. (2026). *MLflow model registry documentation*. https://mlflow.org/docs/latest/ml/model-registry/

myFICO. (n.d.). *What is a credit score?* https://www.myfico.com/credit-education/credit-scores

Office of the Comptroller of the Currency (OCC). (2011). *OCC Bulletin 2011-12: Sound practices for model risk management*. https://www.occ.gov/news-events/newsroom/news-issuances-by-year/bulletins/2011-bulletins.html

PMC. (2024). IFRS 9 and procyclicality of loan loss provision among Chinese banks. *PubMed Central*. https://pmc.ncbi.nlm.nih.gov/articles/PMC12629493/

PwC. (n.d.). *Model risk management of AI and machine learning systems*. https://www.pwc.co.uk/data-analytics/documents/model-risk-management-of-ai-machine-learning-systems.pdf

Repullo, R., Saurina, J., & Trucharte, C. (2010). *Mitigating the pro-cyclicality of Basel II* [CEMFI/Banco de España Working Paper]. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1697529

Sculley, D., Holt, G., Golovin, D., Davydov, E., Phillips, T., Ebner, D., Chaudhary, V., Young, M., Crespo, J.-F., & Dennison, D. (2015). Hidden technical debt in machine learning systems. *Proceedings of the 28th Conference on Neural Information Processing Systems (NeurIPS)*. https://papers.neurips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems.pdf

Shannon, C. E. (1948). A mathematical theory of communication. *Bell System Technical Journal*, *27*(3–4), 379–423, 623–656. https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf

Siddiqi, N. (2006). *Credit risk scorecards: Developing and implementing intelligent credit scoring*. John Wiley & Sons. https://onlinelibrary.wiley.com/doi/book/10.1002/9781119201731

Steenackers, A., & Goovaerts, M. J. (1989). A credit scoring model for personal loans. *Insurance: Mathematics and Economics*, *8*(1), 31–34. https://ideas.repec.org/a/eee/insuma/v8y1989i1p31-34.html

Thomas, L. C., Edelman, D. B., & Crook, J. N. (2002). *Credit scoring and its applications*. SIAM. https://books.google.com/books/about/Credit_Scoring_and_Its_Applications.html?id=GMWcWuBDJZUC

University of Bergamo. (n.d.). *The impact of IFRS 9 on credit risk and profitability in the European banking sector* [Working paper]. https://aisberg.unibg.it/retrieve/55f05b07-776b-4d29-85db-d5ea5e244b97/Paper%204.pdf

Wiginton, J. C. (1980). A note on the comparison of logit and discriminant models of consumer credit behavior. *Journal of Financial and Quantitative Analysis*, *15*(3), 757–770. https://ideas.repec.org/a/cup/jfinqa/v15y1980i03p757-770_00.html

World Bank. (2020). *Credit scoring approaches guidelines*. https://thedocs.worldbank.org/en/doc/935891585869698451-0130022020/original/CREDITSCORINGAPPROACHESGUIDELINESFINALWEB.pdf

Zedda, S. (2024). Credit scoring: Does XGBoost outperform logistic regression? A test on Italian SMEs. *Research in International Business and Finance*, *70*. https://doi.org/10.1016/j.ribaf.2024.102397

Zenodo. (2024). *Lending Club loan dataset for granting models* [Dataset]. Zenodo record 11295916. https://zenodo.org/records/11295916

Zhou, J. et al. (2022). P2P lending default prediction based on AI and statistical models. *Entropy*, *24*(6), Article 801. https://doi.org/10.3390/e24060801

Zhou et al. (2019). Default prediction in P2P lending from high-dimensional data based on machine learning. *Physica A: Statistical Mechanics and its Applications*, *534*, 122–137. https://www.sciencedirect.com/science/article/abs/pii/S0378437119313652
