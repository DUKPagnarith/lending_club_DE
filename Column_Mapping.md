# Column Mapping — Lending Club 2007–2018
**Full dataset:** `data/raw/accepted_2007_to_2018Q4.csv` | 151 columns | ~2.26M rows

---

## Quick Answers

| Question | Answer |
|----------|--------|
| Total raw columns | 151 |
| Columns to DROP | 57 |
| Columns to KEEP for modeling | 46 |
| NEW columns to CREATE (targets + derived) | 9 |
| NEW WoE dummy columns (final model input) | ~50–60 |
| **Final feature count going into logistic regression** | **~50–60 dummies** |

---

## ⚠️ Format Differences vs GitHub Projects

The raw CSV is **NOT the same format** as the clean sample. These conversions are required in L01:

| Column | Raw Format | Needs |
|--------|-----------|-------|
| `term` | `" 36 months"` (string with space) | Strip + convert to int |
| `int_rate` | `13.99` (percentage) | Divide by 100 → `0.1399` |
| `revol_util` | `29.7` (percentage) | Divide by 100 → `0.297` |
| `emp_length` | `"10+ years"` (string) | Strip + convert to int |
| `earliest_cr_line` | `"Aug-2003"` (MMM-YYYY) | Parse → months elapsed |
| `issue_d` | `"2015-12-01 00:00:00"` | Already datetime-parseable |
| `mths_since_last_delinq` | `NaN` (actual null) | Fill NaN → sentinel for WoE |
| `mths_since_last_record` | `NaN` (actual null) | Fill NaN → sentinel for WoE |

---

## Category 1 — DROP (100% Null — Immediate Drop)
*15 columns — all `sec_app_*` and structural empties*

| Column | Reason |
|--------|--------|
| `member_id` | 100% null |
| `desc` | 100% null (free text anyway) |
| `revol_bal_joint` | 100% null |
| `sec_app_fico_range_low` | 100% null |
| `sec_app_fico_range_high` | 100% null |
| `sec_app_earliest_cr_line` | 100% null |
| `sec_app_inq_last_6mths` | 100% null |
| `sec_app_mort_acc` | 100% null |
| `sec_app_open_acc` | 100% null |
| `sec_app_revol_util` | 100% null |
| `sec_app_open_act_il` | 100% null |
| `sec_app_num_rev_accts` | 100% null |
| `sec_app_chargeoff_within_12_mths` | 100% null |
| `sec_app_collections_12_mths_ex_med` | 100% null |
| `sec_app_mths_since_last_major_derog` | 100% null |

---

## Category 2 — DROP (Identifiers & Irrelevant)
*8 columns*

| Column | Reason |
|--------|--------|
| `id` | Loan identifier, no predictive value |
| `url` | URL link, no predictive value |
| `title` | Free text description of purpose (use `purpose` instead) |
| `zip_code` | Too granular, high cardinality (use `addr_state`) |
| `pymnt_plan` | Constant = `n` for all loans |
| `policy_code` | Constant = `1.0` for all loans |
| `funded_amnt_inv` | Near-duplicate of `funded_amnt` |
| `disbursement_method` | Always "Cash" for this dataset |

---

## Category 3 — DROP (Joint Application, >99% Null)
*3 columns — almost all loans are individual*

| Column | Null Rate | Reason |
|--------|-----------|--------|
| `annual_inc_joint` | 99.5% | Joint apps only |
| `dti_joint` | 99.5% | Joint apps only |
| `verification_status_joint` | 99.5% | Joint apps only |

> **Note:** Keep `application_type` (Individual/Joint) as a binary feature — it has 0% null.

---

## Category 4 — DROP (Hardship Program, >99% Null)
*12 columns — hardship program started in 2017–2018, mostly empty*

`hardship_type`, `hardship_reason`, `hardship_status`, `deferral_term`,
`hardship_amount`, `hardship_start_date`, `hardship_end_date`,
`payment_plan_start_date`, `hardship_length`, `hardship_dpd`,
`hardship_loan_status`, `orig_projected_additional_accrued_interest`,
`hardship_payoff_balance_amount`, `hardship_last_payment_amount`

> **Note:** Keep `hardship_flag` (0% null) — could signal stress.

---

## Category 5 — DROP (Debt Settlement, >97% Null)
*6 columns*

`debt_settlement_flag_date`, `settlement_status`, `settlement_date`,
`settlement_amount`, `settlement_percentage`, `settlement_term`

> **Note:** Keep `debt_settlement_flag` (0% null).

---

## Category 6 — DROP (Post-Application Leakage for PD)
*15 columns — only known AFTER loan is issued/defaulted*

> ⚠️ **CRITICAL:** These columns cause data leakage for PD. However, `recoveries` and `total_pymnt` are needed to **create** the LGD and EAD targets BEFORE dropping them.

| Column | Reason |
|--------|--------|
| `out_prncp` | Known only after payments |
| `out_prncp_inv` | Post-origination |
| `total_pymnt` | Post-origination *(use to compute CCF for EAD target first)* |
| `total_pymnt_inv` | Post-origination |
| `total_rec_prncp` | Post-origination |
| `total_rec_int` | Post-origination |
| `total_rec_late_fee` | Post-origination |
| `recoveries` | Post-origination *(use to compute recovery_rate for LGD target first)* |
| `collection_recovery_fee` | Post-origination |
| `last_pymnt_d` | Post-origination |
| `last_pymnt_amnt` | Post-origination |
| `next_pymnt_d` | Future payment date |
| `last_credit_pull_d` | Post-origination behavior |
| `last_fico_range_high` | Post-origination FICO (use application-time FICO instead) |
| `last_fico_range_low` | Post-origination FICO |

---

## Category 7 — DROP (Near-Zero Variance)
*7 columns — >99% of values are 0, no discriminatory power*

`collections_12_mths_ex_med`, `chargeoff_within_12_mths`, `delinq_amnt`,
`tax_liens`, `acc_now_delinq`, `num_tl_30dpd`, `num_tl_90g_dpd_24m`

---

## Category 8 — KEEP + CONVERT (Need Format Fix)
*6 columns that need preprocessing before use*

| Column | Raw Format | Conversion | New Name |
|--------|-----------|------------|----------|
| `term` | `" 36 months"` | Strip → int | `term_int` |
| `int_rate` | `13.99` | `/100` | `int_rate` (overwrite) |
| `revol_util` | `29.7` | `/100` | `revol_util` (overwrite) |
| `emp_length` | `"10+ years"` | Strip → int | `emp_length_int` |
| `issue_d` | `"2015-12-01"` | `pd.to_datetime()` | → derive features below |
| `earliest_cr_line` | `"Aug-2003"` | Parse MMM-YYYY | → derive feature below |

---

## Category 9 — KEEP (Categorical Features for WoE Encoding)
*11 columns — discrete variables → WoE dummies*

| Column | Categories | Notes |
|--------|-----------|-------|
| `grade` | A, B, C, D, E, F, G | Strong predictor (IV > 0.5) |
| `sub_grade` | A1–G5 (35 cats) | More granular than grade |
| `home_ownership` | RENT, OWN, MORTGAGE, OTHER | |
| `verification_status` | Not Verified, Verified, Source Verified | |
| `purpose` | debt_consolidation, credit_card, home_improvement, etc. | |
| `addr_state` | 50 US states | May need grouping by WoE |
| `initial_list_status` | w, f | Binary |
| `application_type` | Individual, Joint | Binary |
| `hardship_flag` | N, Y | Binary, mostly N |
| `debt_settlement_flag` | N, Y | Binary, mostly N |
| `emp_length` | after → `emp_length_int` | 0–10 |

---

## Category 10 — KEEP (Numeric Features for WoE Fine/Coarse Classing)
*29 columns — continuous variables → fine class → coarse class → dummies*

### Core variables (matching GitHub format exactly):
| Column | Notes |
|--------|-------|
| `loan_amnt` | Requested amount |
| `funded_amnt` | Actual funded amount |
| `installment` | Monthly payment |
| `annual_inc` | Right-skewed, cap at 99th percentile |
| `dti` | Debt-to-income ratio |
| `delinq_2yrs` | Delinquencies last 2 years |
| `inq_last_6mths` | Credit inquiries last 6 months |
| `open_acc` | Open credit accounts |
| `pub_rec` | Public records (bankruptcies, liens) |
| `revol_bal` | Total revolving credit balance |
| `total_acc` | Total credit accounts |
| `fico_range_low` | FICO score lower bound |
| `fico_range_high` | FICO score upper bound |

### Additional credit bureau variables (richer than GitHub — our advantage):
| Column | Null Rate | Notes |
|--------|-----------|-------|
| `acc_open_past_24mths` | 0% | Accounts opened last 24 months |
| `avg_cur_bal` | 0% | Average current balance across accounts |
| `bc_open_to_buy` | 0.9% | Bankcard available credit |
| `bc_util` | 1.0% | Bankcard utilization ratio |
| `mo_sin_old_il_acct` | 2.7% | Months since oldest installment account |
| `mo_sin_old_rev_tl_op` | 0% | Months since oldest revolving account |
| `mort_acc` | 0% | Number of mortgage accounts |
| `mths_since_recent_bc` | 0.9% | Months since most recent bankcard opened |
| `mths_since_recent_inq` | 10.5% | Months since most recent inquiry |
| `num_accts_ever_120_pd` | 0% | Accounts ever 120+ days past due |
| `num_actv_bc_tl` | 0% | Active bankcard tradelines |
| `num_actv_rev_tl` | 0% | Active revolving tradelines |
| `num_bc_tl` | 0% | Total bankcard tradelines |
| `num_il_tl` | 0% | Installment tradelines |
| `num_rev_accts` | 0% | Revolving accounts |
| `pct_tl_nvr_dlq` | 0% | % accounts never delinquent |
| `percent_bc_gt_75` | 1.0% | % bankcards > 75% utilization |
| `pub_rec_bankruptcies` | 0% | Public record bankruptcies |
| `tot_cur_bal` | 0% | Total current balance all accounts |
| `tot_hi_cred_lim` | 0% | Total high credit limit |
| `total_bc_limit` | 0% | Total bankcard credit limit |
| `total_il_high_credit_limit` | 0% | Total installment high credit limit |
| `total_rev_hi_lim` | 0% | Total revolving high credit limit |

### High-null variables — treat missing AS A WoE CATEGORY (don't drop):
| Column | Null Rate | What null means |
|--------|-----------|----------------|
| `mths_since_last_delinq` | 48% | Never been delinquent → own WoE bin |
| `mths_since_last_major_derog` | 70% | Never had major derogatory → own WoE bin |
| `mths_since_recent_bc_dlq` | 74% | Never had bankcard delinquency → own WoE bin |
| `mths_since_recent_revol_delinq` | 64% | Never had revolving delinquency → own WoE bin |
| `mths_since_last_record` | 82% | No public record → own WoE bin |

### Partially available (57–63% null — use if IV is strong enough):
`open_acc_6m`, `open_act_il`, `open_il_12m`, `open_il_24m`, `mths_since_rcnt_il`,
`total_bal_il`, `il_util`, `open_rv_12m`, `open_rv_24m`, `max_bal_bc`,
`all_util`, `inq_fi`, `total_cu_tl`, `inq_last_12m`

> These are only available for loans after 2012. Check IV — include only if > 0.02.

---

## Category 11 — CREATE NEW (Derived Features)
*9 new columns created during preprocessing*

| New Column | Source | Formula | Purpose |
|-----------|--------|---------|---------|
| `good_bad` | `loan_status` | 0 if Charged Off/Default/Late 31-120d, 1 if Fully Paid | **PD target** |
| `recovery_rate` | `recoveries`, `funded_amnt` | `recoveries / funded_amnt` (defaulted only) | **LGD target** |
| `ccf` | `total_pymnt`, `funded_amnt` | `(funded_amnt - total_pymnt) / funded_amnt` (defaulted only) | **EAD target** |
| `term_int` | `term` | Strip " months" → int | PD feature |
| `emp_length_int` | `emp_length` | Strip "years/+" → int | PD feature |
| `mths_since_issue_d` | `issue_d` | Months from issue_d to dataset max date | PD feature |
| `mths_since_earliest_cr_line` | `earliest_cr_line` | Months from earliest_cr_line to dataset max date | PD feature |
| `issue_year` | `issue_d` | `issue_d.dt.year` | **OOT split key** |
| `fico_score` | `fico_range_low`, `fico_range_high` | `(low + high) / 2` | PD feature |

---

## Category 12 — WoE DUMMY VARIABLES (Final Model Input)
*Created during feature engineering — ~50–60 total*

Each variable gets 3–7 dummy columns after coarse classing. The **reference category** (highest risk / lowest WoE) is NOT created as a dummy.

| Variable | Approx. Dummies | Reference Category |
|---------|----------------|-------------------|
| `grade` | 5 | F and G |
| `home_ownership` | 2 | RENT |
| `verification_status` | 2 | Not Verified |
| `purpose` | 5–6 | small_business |
| `initial_list_status` | 1 | f |
| `application_type` | 1 | Joint |
| `term_int` | 1 | 60 months |
| `int_rate` | 5 | >20% |
| `funded_amnt` | 4 | lowest bracket |
| `annual_inc` | 4 | <$25k |
| `dti` | 4 | >35% |
| `emp_length_int` | 3–4 | 0 years |
| `fico_score` | 5 | <600 |
| `mths_since_issue_d` | 4 | most recent (least data) |
| `mths_since_earliest_cr_line` | 4 | shortest history |
| `inq_last_6mths` | 3 | highest inquiries |
| `mths_since_last_delinq` | 4 | recent delinquency |
| `revol_util` | 4 | >80% |
| `bc_util` | 3 | >80% |
| `pct_tl_nvr_dlq` | 3 | lowest % |
| `mort_acc` | 2 | 0 mortgages |
| **TOTAL** | **~50–60** | |

---

## Summary: Column Journey

```
151 raw columns
   - 15  (100% null)
   - 8   (identifiers/constants)
   - 3   (joint application, >99% null)
   - 14  (hardship/settlement, >97% null)
   - 15  (post-application leakage for PD)
   - 7   (near-zero variance)
   ─────────────────────────────────────
   ≈ 89  columns remaining after cleaning

   Of these 89:
   → 6   need format conversion
   → 11  are categorical → WoE encode
   → 29  are numeric → fine class → WoE → dummies
   → 9   are NEW derived columns (targets + engineered)
   ─────────────────────────────────────
   → ~50–60 final WoE dummy columns fed into logistic regression
```

---

## Out-of-Time Split (2007–2018 Dataset)

| Split | Years | Approx. Rows | Purpose |
|-------|-------|-------------|---------|
| **Train** | 2007–2015 | ~1.3M | Fit WoE bins, train all models |
| **OOT Test** | 2016–2018 | ~960K | Evaluate on future unseen data |

> The train/OOT boundary is at `issue_year <= 2015` vs `issue_year >= 2016`.
> This gives 3 years of out-of-time validation — more robust than the 1-year window in the course.

---

## Matching the GitHub Projects

| Feature | levist7 project | allmeidaapedro project | Our project |
|---------|----------------|----------------------|-------------|
| Grade | `grade` | `sub_grade` | Both `grade` + `sub_grade` (choose by IV) |
| FICO | ❌ Not used | ✅ `fico_range_low/high` | ✅ `fico_score` derived |
| Credit bureau vars | ❌ Few | ✅ Some | ✅ Full set (richer dataset) |
| OOT split | 2007–14 / 2015 | Chronological | 2007–15 / 2016–18 |
| Missing as WoE cat | ✅ | ✅ | ✅ |
| Scorecard scale | 300–850 | 300–850 | 300–850 |
| LGD model | 2-stage | 2-stage + beta note | 2-stage + beta note |
