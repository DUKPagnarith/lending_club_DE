-- ============================================================
-- Credit Risk System — PostgreSQL Schema
-- Run automatically on first container start
-- ============================================================

-- Create airflow database
CREATE DATABASE airflow;

-- ── Schemas (Bronze → Silver → Gold → Output) ────────────────
\c credit_risk;
CREATE SCHEMA IF NOT EXISTS raw;        -- Bronze: untouched CSV data
CREATE SCHEMA IF NOT EXISTS staging;   -- Silver: cleaned & validated
CREATE SCHEMA IF NOT EXISTS features;  -- Gold: WoE-encoded feature store
CREATE SCHEMA IF NOT EXISTS models;    -- Model predictions & scores
CREATE SCHEMA IF NOT EXISTS risk;      -- EL, PSI, regulatory outputs
CREATE SCHEMA IF NOT EXISTS audit;     -- Pipeline run logs

-- ── RAW LAYER ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS raw.loan_applications (
    id                          BIGINT,
    loan_amnt                   NUMERIC(12,2),
    funded_amnt                 NUMERIC(12,2),
    term                        VARCHAR(20),
    int_rate                    NUMERIC(8,4),
    installment                 NUMERIC(10,2),
    grade                       VARCHAR(5),
    sub_grade                   VARCHAR(5),
    emp_length                  VARCHAR(20),
    home_ownership              VARCHAR(20),
    annual_inc                  NUMERIC(14,2),
    verification_status         VARCHAR(50),
    issue_d                     VARCHAR(30),
    loan_status                 VARCHAR(100),
    purpose                     VARCHAR(50),
    addr_state                  VARCHAR(5),
    dti                         NUMERIC(8,4),
    delinq_2yrs                 INTEGER,
    earliest_cr_line            VARCHAR(20),
    fico_range_low              NUMERIC(6,1),
    fico_range_high             NUMERIC(6,1),
    inq_last_6mths              INTEGER,
    mths_since_last_delinq      NUMERIC(8,2),
    mths_since_last_record      NUMERIC(8,2),
    open_acc                    INTEGER,
    pub_rec                     INTEGER,
    revol_bal                   NUMERIC(14,2),
    revol_util                  NUMERIC(8,4),
    total_acc                   INTEGER,
    initial_list_status         VARCHAR(5),
    application_type            VARCHAR(20),
    bc_util                     NUMERIC(8,4),
    pct_tl_nvr_dlq              NUMERIC(8,4),
    mort_acc                    INTEGER,
    num_accts_ever_120_pd       INTEGER,
    acc_open_past_24mths        INTEGER,
    tot_cur_bal                 NUMERIC(14,2),
    source_file                 VARCHAR(200),
    ingested_at                 TIMESTAMP DEFAULT NOW()
);

-- ── STAGING LAYER ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS staging.loans_cleaned (
    loan_id                     BIGINT PRIMARY KEY,
    funded_amnt                 NUMERIC(12,2),
    term_int                    INTEGER,
    int_rate                    NUMERIC(8,6),
    grade                       VARCHAR(5),
    sub_grade                   VARCHAR(5),
    emp_length_int              INTEGER,
    home_ownership              VARCHAR(20),
    annual_inc                  NUMERIC(14,2),
    verification_status         VARCHAR(50),
    purpose                     VARCHAR(50),
    addr_state                  VARCHAR(5),
    dti                         NUMERIC(8,4),
    delinq_2yrs                 INTEGER,
    fico_score                  NUMERIC(6,1),
    inq_last_6mths              INTEGER,
    mths_since_last_delinq      NUMERIC(8,2),
    mths_since_last_record      NUMERIC(8,2),
    open_acc                    INTEGER,
    pub_rec                     INTEGER,
    revol_bal                   NUMERIC(14,2),
    revol_util                  NUMERIC(8,6),
    total_acc                   INTEGER,
    initial_list_status         VARCHAR(5),
    application_type            VARCHAR(20),
    bc_util                     NUMERIC(8,4),
    pct_tl_nvr_dlq              NUMERIC(8,4),
    mort_acc                    INTEGER,
    num_accts_ever_120_pd       INTEGER,
    acc_open_past_24mths        INTEGER,
    tot_cur_bal                 NUMERIC(14,2),
    mths_since_issue_d          INTEGER,
    mths_since_earliest_cr_line INTEGER,
    issue_year                  INTEGER,
    -- Target variables
    good_bad                    SMALLINT,
    recovery_rate               NUMERIC(8,6),
    ccf                         NUMERIC(8,6),
    dataset_split               VARCHAR(10),   -- 'train' | 'oot'
    cleaned_at                  TIMESTAMP DEFAULT NOW()
);

-- ── FEATURES LAYER ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS features.woe_bins (
    bin_id          BIGSERIAL PRIMARY KEY,
    variable_name   VARCHAR(100) NOT NULL,
    bin_label       VARCHAR(200) NOT NULL,
    n_obs           INTEGER,
    n_good          INTEGER,
    n_bad           INTEGER,
    prop_n_good     NUMERIC(10,8),
    prop_n_bad      NUMERIC(10,8),
    woe             NUMERIC(10,6),
    iv_contribution NUMERIC(10,8),
    total_iv        NUMERIC(10,8),
    model_version   VARCHAR(50),
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS features.information_values (
    variable_name   VARCHAR(100) PRIMARY KEY,
    total_iv        NUMERIC(10,8),
    recommendation  VARCHAR(20),
    model_version   VARCHAR(50),
    computed_at     TIMESTAMP DEFAULT NOW()
);

-- ── MODELS LAYER ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS models.pd_predictions (
    prediction_id   BIGSERIAL PRIMARY KEY,
    loan_id         BIGINT,
    pd_probability  NUMERIC(8,6),
    credit_score    INTEGER,
    score_band      VARCHAR(10),
    decision        VARCHAR(15),
    annualized_roi  NUMERIC(8,6),
    model_version   VARCHAR(50),
    predicted_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS models.lgd_predictions (
    prediction_id       BIGSERIAL PRIMARY KEY,
    loan_id             BIGINT,
    recovery_prob_gt0   NUMERIC(8,6),
    recovery_rate_cond  NUMERIC(8,6),
    recovery_rate_final NUMERIC(8,6),
    lgd_predicted       NUMERIC(8,6),
    model_version       VARCHAR(50),
    predicted_at        TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS models.ead_predictions (
    prediction_id   BIGSERIAL PRIMARY KEY,
    loan_id         BIGINT,
    ccf_predicted   NUMERIC(8,6),
    ead_amount      NUMERIC(12,2),
    model_version   VARCHAR(50),
    predicted_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS models.scorecard (
    feature         VARCHAR(100) PRIMARY KEY,
    coefficient     NUMERIC(10,6),
    score           INTEGER,
    p_value         NUMERIC(10,8),
    model_version   VARCHAR(50),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ── RISK LAYER ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS risk.expected_loss (
    el_id           BIGSERIAL PRIMARY KEY,
    loan_id         BIGINT,
    pd              NUMERIC(8,6),
    lgd             NUMERIC(8,6),
    ead             NUMERIC(12,2),
    expected_loss   NUMERIC(12,2),
    el_rate         NUMERIC(8,6),
    risk_class      VARCHAR(10),
    calc_date       DATE DEFAULT CURRENT_DATE,
    model_run_id    VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS risk.population_stability (
    psi_id          BIGSERIAL PRIMARY KEY,
    variable_name   VARCHAR(100),
    psi_value       NUMERIC(10,6),
    psi_status      VARCHAR(10),
    reference_date  VARCHAR(20),
    monitoring_date VARCHAR(20),
    computed_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk.model_performance_log (
    log_id          BIGSERIAL PRIMARY KEY,
    model_name      VARCHAR(50),
    model_version   VARCHAR(50),
    eval_dataset    VARCHAR(20),
    auc             NUMERIC(8,6),
    gini            NUMERIC(8,6),
    ks_stat         NUMERIC(8,6),
    brier_score     NUMERIC(8,6),
    r_squared       NUMERIC(8,6),
    n_observations  INTEGER,
    evaluated_at    TIMESTAMP DEFAULT NOW()
);

-- ── AUDIT LAYER ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit.pipeline_runs (
    run_id          BIGSERIAL PRIMARY KEY,
    dag_id          VARCHAR(100),
    task_id         VARCHAR(100),
    run_date        DATE,
    rows_processed  BIGINT,
    rows_rejected   BIGINT,
    status          VARCHAR(20),
    error_message   TEXT,
    duration_secs   NUMERIC(10,2),
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP
);

-- ── INDEXES ──────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_pd_loan_id     ON models.pd_predictions(loan_id);
CREATE INDEX IF NOT EXISTS idx_el_calc_date   ON risk.expected_loss(calc_date);
CREATE INDEX IF NOT EXISTS idx_psi_date       ON risk.population_stability(monitoring_date);
CREATE INDEX IF NOT EXISTS idx_loans_split    ON staging.loans_cleaned(dataset_split);
CREATE INDEX IF NOT EXISTS idx_loans_year     ON staging.loans_cleaned(issue_year);
CREATE INDEX IF NOT EXISTS idx_woe_variable   ON features.woe_bins(variable_name, model_version);

-- ── PERMISSIONS ──────────────────────────────────────────────
GRANT ALL ON ALL TABLES IN SCHEMA raw      TO credit_risk;
GRANT ALL ON ALL TABLES IN SCHEMA staging  TO credit_risk;
GRANT ALL ON ALL TABLES IN SCHEMA features TO credit_risk;
GRANT ALL ON ALL TABLES IN SCHEMA models   TO credit_risk;
GRANT ALL ON ALL TABLES IN SCHEMA risk     TO credit_risk;
GRANT ALL ON ALL TABLES IN SCHEMA audit    TO credit_risk;

SELECT 'Database schema initialized successfully' AS status;
