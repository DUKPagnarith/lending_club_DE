# Credit Risk Modeling — Implementation Plan v4
### Status Review · Real-World Alignment · Next-Update Roadmap · Preview & Verification Plan
**Update date: 2026-06-07**

> This plan supersedes nothing in `Credit_Risk_Implementation_Plan.md` — it records what
> the current update changed to make the project behave like a real bank credit-risk
> system, states the next-update roadmap, and ends with a concrete **preview &
> verification plan** (bring the stack up, open every port in a tab, and confirm the
> visualizations, buttons, and ports all work).

---

## Part 0 — What this update did

1. **Audited current state against the implementation plan and the literature review.**
2. **Closed the highest-impact "real world" gaps** that were documented but not yet live
   in the notebooks (the priority regulatory subset).
3. **Ran the full learning pipeline (L01 → L04) end-to-end** on the real
   `accepted_2007_to_2018Q4.csv` (2.26M rows) and regenerated every artifact and chart.
4. **Found and fixed two correctness bugs** surfaced only by running the pipeline.
5. Wrote this next-update plan, including the preview/verification checklist.

---

## Part 1 — Status: Current vs Plan vs Literature

The four learning notebooks were partially executed and several "V3" real-world upgrades
existed only as **unexecuted** cells. The table below is the post-update status.

| Plan item | Source | Before | After this update |
|---|---|---|---|
| Out-of-time split (train ≤2015 / OOT 2016–18) | Plan A6 | Live | Live — train 831,051 · OOT 538,515 |
| WoE / IV + 56 dummies, p-value selection | Plan B2 | Live | Live — 39 of 56 features significant |
| Brier score, decile, ROC | Plan B2 | Live | Live |
| **Hosmer-Lemeshow + reliability diagram** (V3-7) | Lit §2.4 | Drafted, not run | **Live & executed** |
| **TtC vs PiT PD calibration** (V3-3) | Lit §2.4 | Drafted, not run | **Live & executed** |
| **Adverse-action codes / ECOA** (V3-10) | research §33 | Drafted, not run | **Live & executed** |
| **Downturn LGD** (V3-6) | Basel AIRB | Drafted (had bug) | **Live & fixed** |
| **IRB economic capital + RAROC** (V3-1) | research §9 | Drafted, not run | **Live & executed** |
| **IFRS 9 three-stage ECL + SICR + lifetime PD** (V3-2/4) | Lit §2.4 | **Missing** | **Newly implemented** |
| Vintage / cohort analysis (V3-9) | research §10 | Drafted, not run | Live & executed |
| Reject inference — parceling (V3-5) | Lit §2.3 | Drafted, not run | Live & executed (artifact saved) |
| Characteristic Stability Index (V3-8) | Lit §2.6 | Drafted, not run | Live & executed |
| Champion/Challenger (V3-11) | Lit §2.6 | Drafted (inverted) | **Live & fixed** |
| Productionize notebooks → Airflow DAGs | Plan A7 | Scaffolded only | **Pending (next update)** |
| PD recalibration to fix miscalibration | Lit §2.4 | — | **Pending — top priority next update** |
| SR 11-7 model card (V3-12) | research §32 | Checklist only | Pending (next update) |

---

## Part 2 — Changes made to mimic the real world (this update)

1. **Memory-safe, column-projected ingestion (L01).** The raw load read all 151 columns
   into memory; it now reads only the 26 modeling columns in chunks — mirroring real ETL
   (you never pull columns you immediately drop) and making the 1.6 GB file load in ~7s.

2. **Expected Loss now uses the *real* PiT PD model (L03).** The EL step previously used a
   hard-coded grade→PD proxy. It now loads the fitted scorecard's Point-in-Time PD
   (`pd_pred_test_pit.npy`) produced by L02, so EL = real PD × LGD × EAD.

3. **IFRS 9 three-stage ECL — newly implemented (L03).** Every OOT loan is now classified
   Stage 1 / 2 / 3 via an SICR rule (relative PD doubling, absolute PD jump, 30-DPD
   backstop, watchlist), with 12-month ECL for Stage 1 and **lifetime ECL** (geometric
   hazard term structure) for Stages 2/3. This is the single biggest "real bank" gap that
   was missing — banks never book a flat 12-month EL.

4. **Downturn LGD direction fix (L03).** The old function could return a downturn LGD
   *below* the long-run LGD because a 10% recovery floor raised this book's ~8% average
   recovery. Fixed so downturn LGD is always ≥ long-run LGD (recoveries fall, never rise,
   in a downturn). Result moved from a wrong 90.0% to a correct 93.76% (+1.56pp add-on).

5. **Champion/Challenger now scored on the real model (L04).** The demo used an ad-hoc
   score helper that was inverted (Gini −0.28). It now uses the real PiT PD on the OOT
   set, giving a sensible champion Gini of 0.3874.

---

## Part 3 — Pipeline run results (verified 2026-06-07)

All four notebooks executed end-to-end with **zero errors** and regenerated **23
visualizations** plus all model artifacts.

| Stage | Key result |
|---|---|
| L01 split | Train 831,051 (DR 18.62%) · OOT 538,515 (DR 25.27%) |
| L02 PD (OOT) | AUC 0.694 · **Gini 0.387** · KS 0.281 · Brier 0.175 · 39 features |
| L02 calibration | Hosmer-Lemeshow **p ≈ 0 → miscalibrated** (recalibration needed) |
| L02 PD calibration | Mean PiT PD 20.18% · Mean TtC PD 12.17% |
| L03 LGD/EAD | Avg LGD 92.19% · **Downturn LGD 93.76%** · Total EAD $3.26B · EL rate 19.93% |
| L03 IRB capital | RWA $16.83B · Capital $1.35B · Capital ratio 43% · Mean RAROC −22.5% |
| L03 IFRS 9 ECL | Stage 1 7.0% ($15M) · Stage 2 71.4% ($967M) · Stage 3 21.6% ($413M) |
| L03 IFRS 9 total | **$1.396B lifetime ECL vs $650M flat 12-mo EL → +$746M uplift** |
| L04 stability | **Score PSI 0.282 → ALERT** · Champion Gini 0.387 → Keep Champion |

**Headline real-world reading:** the raw PD model discriminates acceptably (Gini ~0.39)
but is **miscalibrated** (HL p≈0) and over-conservative on level (mean PD 20% vs actual
25% OOT, with a population shift PSI of 0.28). That miscalibration is exactly why the
IRB capital ratio (43%) and RAROC (−22%) look extreme — capital and RAROC are only
meaningful on a *calibrated* PD. This makes **PD recalibration the #1 next-update item.**

---

## Part 4 — Next-Update Implementation Plan

Ordered by impact. Each item says where it lands in the notebooks/pipeline.

| # | Item | Where | Status |
|---|---|---|---|
| **NU-1** | **PD recalibration** (intercept log-odds shift) + re-check HL & reliability | L02 / `models/preprocessing/pd_calibrator.py` | ✅ **DONE — 2026-06-07** |
| **NU-2** | **Scenario-weighted lifetime ECL** with GDP/unemployment macro overlay | L03 / `data/processed/ifrs9_scenario_ecl.parquet` | ✅ **DONE — 2026-06-07** |
| **NU-3** | **Train PD on the reject-inference-augmented set** and compare Gini/KS | L02 / `data/processed/pd_pred_test_augmented.npy` | ✅ **DONE — 2026-06-07** |
| **NU-4** | **Productionize: port L01–L04 logic into the Airflow DAGs + Spark jobs** | pipeline/ | Pending (DAG-04/05 feature bug fixed) |
| **NU-5** | **FastAPI `/score` returns IFRS 9 stage + adverse-action codes** | api/ | Partially done (ifrs9_stage field live) |
| **NU-6** | **Grafana dashboards** for PSI/CSI, vintage, IFRS 9 stage mix, RAROC | infra/grafana | Pending |
| **NU-7** | **SR 11-7 model card** (`docs/model_card.md`) filled from this run | docs/ | Pending |
| **NU-8** | Add cell IDs / `papermill` parameters to notebooks for clean re-runs | notebooks/ | Pending |

---

## Part 4a — NU-1 Results: PD Recalibration (2026-06-07)

**Method:** Intercept recalibration — find log-odds shift δ such that
`mean(sigmoid(logit(PD_raw) + δ)) = actual OOT default rate`.
This is the standard industry / Basel AIRB intercept adjustment (EBA 2017a, BCBS 2005 §468).
Platt scaling was also tested (coef ≈ 0.94 ≈ 1.0) — confirmed intercept shift is sufficient.

| Metric | Pre-calibration | Post-calibration | Change |
|---|---|---|---|
| Mean PD | 20.18% | 25.27% | +5.09pp (now matches actual DR) |
| HL statistic | 10,039 | 403 | −96% |
| Brier score | 0.1750 | 0.1722 | −1.6% |
| AUC / Gini | 0.6937 / 0.387 | 0.6937 / 0.387 | Unchanged ✓ |
| Log-odds shift δ | — | +0.3204 | — |

**Impact on downstream outputs (post-calibration):**

| Output | Pre-calibration | Post-calibration | Delta |
|---|---|---|---|
| IRB RWA | $13.62B | $14.07B | +$0.45B (+3.3%) |
| IRB Min Capital | $1.09B | $1.13B | +$0.04B |
| Capital ratio (% EAD) | 33.4% | 34.5% | +1.1pp |
| RAROC | +323% | +299% | −24pp (still inflated — LGD ~93% is this portfolio's primary driver) |
| Expected Loss (12-mo) | $0.650B | $0.808B | +$0.158B (+24%) |
| IFRS 9 lifetime ECL | $1.334B | $1.601B | +$0.267B (+20%) |
| IFRS 9 Stage 2 mix | 61.0% | 74.2% | +13.2pp (more loans above SICR threshold) |

**Artifacts produced:**
- `data/models/pd_calibrator.json` — fitted calibrator config (δ, pre/post metrics)
- `data/processed/pd_pred_test_pit_calibrated.npy` — recalibrated PD array (538,515 values)
- `models/preprocessing/pd_calibrator.py` — `PDCalibrator` class (fit/transform/save/load)
- `data/reports/L02_calibration_reliability_diagram.png` — updated before/after chart

**Note on RAROC:** The +299% RAROC remains unrealistically high because LGD ≈ 93% on this
Lending Club unsecured book. RAROC = (interest income − EL) / capital; EL is dominated by
the high LGD, not PD. A more realistic RAROC requires applying the credit policy
(reject high-PD loans) before computing portfolio EL — i.e., run on the APPROVED subset only.

---

## Part 4b — NU-2 Results: Scenario-Weighted ECL (2026-06-07)

**Method:** IFRS 9 §5.5.17 probability-weighted ECL across three macro scenarios.
PD adjusted per scenario via log-odds satellite model (Bellotti & Crook 2009):
`delta_logodds = 0.18 × delta_unemployment − 0.10 × delta_gdp`

| Scenario | Weight | Δ Unem | Δ GDP | Mean PD | Stage 2% | ECL |
|---|---|---|---|---|---|---|
| Base | 50% | 0pp | 0pp | 25.27% | 74.2% | $1.601B |
| Upside | 25% | −1.5pp | +2.0pp | 18.06% | 53.6% | $1.205B |
| Downside | 25% | +3.0pp | −2.5pp | 40.56% | 93.2% | $2.176B |
| **Weighted** | — | — | — | — | 73.8% | **$1.646B** |

**Non-linearity uplift vs single-scenario base: +$44M (+2.8%).**
The downside scenario (ECL $2.176B = +36% vs base) dominates the uplift because
the geometric hazard lifetime ECL is convex in PD — losses accelerate faster than
PD increases. This is the IFRS 9 "forward-looking information" requirement.

**Artifacts produced:**
- `data/processed/ifrs9_scenario_ecl.parquet` — per-loan ECL under each scenario
- `data/models/ifrs9_scenarios.json` — scenario config and summary metrics
- `data/reports/L03_ifrs9_scenario_weighted_ecl.png` — scenario comparison chart

---

## Part 4c — NU-3 Results: Reject Inference (2026-06-07)

**Method:** Applied L01 WoE dummy encoding to `train_augmented_reject_inference.parquet`
(857,180 rows = original 831,051 + 26,129 synthetic parceling rejects).
Retrained logistic regression on same 39 pre-selected features. Compared OOT metrics.

| Metric | Original (831K) | Augmented (857K) | Delta |
|---|---|---|---|
| AUC | 0.6937 | 0.6940 | +0.0003 |
| Gini | 0.3874 | 0.3879 | +0.06pp |
| KS | 0.2813 | 0.2816 | +0.0003 |
| Brier | 0.1750 | 0.1751 | +0.0001 |
| Mean OOT PD | 0.2018 | 0.2070 | +0.52pp |
| Train DR | 18.62% | 20.35% | +1.73pp |

**Conclusion:** Discrimination metrics (Gini/KS/AUC) are statistically unchanged.
Parceling added only 3.1% synthetic rows — too small to shift the decision boundary.
The meaningful effect is on **PD level**: mean OOT PD rises from 20.18% to 20.70%,
partially correcting the downward selection bias (actual OOT DR = 25.27%).
Combining reject-inference PDs with NU-1 recalibration gives the best level accuracy.

**Artifacts produced:**
- `data/processed/pd_pred_test_augmented.npy` — OOT PD from augmented model

---

## Part 5 — Preview & Verification Plan (run AFTER the notebook + pipeline)

This is the step the user watches: bring the whole stack up locally, open **every service
port in its own browser tab**, then verify the **ports respond, the buttons work, and the
visualizations are correct.**

### 5.1 Bring the stack up

```bash
cd I4_risk_management
cp .env.example .env        # first run only — set passwords
make up                     # docker compose up -d --build
docker compose ps           # wait until all services are "healthy"/"running"
```

Allow 2–5 minutes on first build (Airflow + Spark images compile).

### 5.2 Open all ports in browser tabs

| # | Service | URL | What it proves |
|---|---|---|---|
| 1 | Airflow | http://localhost:8081 | Orchestration UI + the 6 DAGs |
| 2 | Spark Master | http://localhost:8080 | Worker registered, compute ready |
| 3 | MLflow | http://localhost:5001 | Experiment tracking + model registry |
| 4 | MinIO Console | http://localhost:9001 | Data-lake buckets (landing-zone, mlflow-artifacts, spark-output) |
| 5 | FastAPI docs | http://localhost:8000/docs | Scoring API, interactive Swagger |
| 6 | Grafana | http://localhost:3000 | Monitoring dashboards |

### 5.3 Ports-working checklist (health)

For each of the 6 ports, confirm:
- [ ] The tab loads (HTTP 200, not "connection refused").
- [ ] `docker compose ps` shows the backing container `Up`/`healthy`.
- [ ] Airflow login works (`AIRFLOW_ADMIN_USER` / `AIRFLOW_ADMIN_PASSWORD`).
- [ ] MinIO login works and the three buckets exist.
- [ ] MLflow shows at least the experiment list page (no 500).
- [ ] FastAPI `/docs` renders the Swagger schema; `/health` returns OK.
- [ ] Grafana login works and a data source is reachable.

### 5.4 Buttons-working checklist (interaction)

- [ ] **Airflow:** un-pause a DAG with its toggle, click **Trigger DAG (▶)**, open Graph
      view, confirm tasks turn green.
- [ ] **MLflow:** click into a run, open the **Metrics** and **Artifacts** tabs.
- [ ] **MinIO:** click a bucket → **Browse**, confirm objects list.
- [ ] **FastAPI:** expand `POST /score`, click **Try it out → Execute**, confirm a JSON
      response with `pd, lgd, ead, expected_loss, ifrs9_stage, decision`.
- [ ] **Grafana:** open a dashboard, change the time range, confirm panels refresh.

### 5.5 Visualization-correctness checklist

Open each chart in `data/reports/` (23 PNGs) and confirm it tells the right story:

- [ ] `L01_default_rate_by_grade` — default rate rises monotonically A → G.
- [ ] `L01_fico_distribution_good_bad` — good borrowers shifted to higher FICO.
- [ ] `L02_roc_curve` — curve above the diagonal; AUC ≈ 0.69.
- [ ] `L02_decile_analysis` — bad rate decreases monotonically across score deciles.
- [ ] `L02_calibration_reliability_diagram` — points **off** the 45° line (confirms the
      HL "miscalibrated" verdict; this is expected pre-recalibration).
- [ ] `L03_expected_loss_by_grade` — EL rate increases A → G.
- [ ] `L03_ifrs9_ecl_staging` — Stage 3 has the highest coverage ratio; Stage 2 the
      largest provision pool.
- [ ] `L03_vintage_analysis` — predicted PD tracks actual default rate by vintage.
- [ ] `L04_psi_master_dashboard` — credit-score PSI bar is in the red ALERT zone (~0.28).
- [ ] `L04_champion_challenger` — both Gini values positive (~0.38); verdict "Keep Champion".

**Pass criterion:** every box in 5.3, 5.4, and 5.5 is checked. Any unchecked box is a
defect to log against the relevant NU item in Part 4.

---

## Appendix — Artifacts produced this update

- Executed notebooks: `notebooks/L01–L04.ipynb` (0 errors).
- Models: `data/models/{lgd_stage1,lgd_stage2,ead_model,ead_scaler}.pkl`.
- Tables: `data/processed/scorecard.csv`, `pd_pred_test_pit.npy`, `pd_pred_test_ttc.npy`,
  `train_augmented_reject_inference.parquet`.
- Regulatory: `data/reports/L03_ifrs9_provisions.csv` (per-loan stage + ECL).
- Charts: 23 PNGs in `data/reports/`.
