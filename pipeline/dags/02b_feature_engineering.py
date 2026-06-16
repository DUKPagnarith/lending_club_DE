"""
DAG 02b — Feature Engineering: WoE dummy encoding
Input:  staging.loans_cleaned (PostgreSQL) or MinIO parquet backup
Output: data/processed/train_preprocessed.parquet
        data/processed/test_preprocessed.parquet
        data/processed/dummy_cols.json

This is the step that was missing between cleaning and model training.
Applies the identical WoE dummy encoding from L01 notebook so that DAG-03
and DAG-04 receive the correct 56-column feature matrix.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

default_args = {"owner": "credit_risk", "retries": 1, "retry_delay": timedelta(minutes=5)}

DUMMY_COLS = [
    'grade_A','grade_B','grade_C','grade_D','grade_E',
    'home_ownership_OWN','home_ownership_MORTGAGE',
    'verif_Verified','verif_Source_Verified',
    'purpose_debt_consolidation','purpose_credit_card','purpose_home_improvement',
    'purpose_major_purchase','purpose_other',
    'initial_list_w',
    'int_rate_lt_0088','int_rate_088_117','int_rate_117_148','int_rate_148_176','int_rate_176_200',
    'annual_inc_25k_50k','annual_inc_50k_75k','annual_inc_75k_125k','annual_inc_gt125k',
    'fico_600_640','fico_640_680','fico_680_720','fico_720_760','fico_gt760',
    'dti_lt_10','dti_10_20','dti_20_28','dti_28_35',
    'term_36',
    'mths_issue_lt38','mths_issue_38_64','mths_issue_64_95','mths_issue_95_118',
    'cr_line_lt80','cr_line_80_140','cr_line_140_200','cr_line_gt200',
    'delinq_never','delinq_lt24','delinq_24_48','delinq_48_72',
    'revol_util_lt020','revol_util_20_40','revol_util_40_60','revol_util_60_80',
    'inq_0','inq_1','inq_2_3',
    'pct_dlq_gt95','pct_dlq_85_95','pct_dlq_70_85',
]


def encode_woe_dummies(df):
    """Apply WoE coarse-class dummy encoding — identical to L01 notebook cell 36."""
    # Sentinel fill (NaN = "never happened" → treated as its own WoE bin)
    for col in ['mths_since_last_delinq', 'mths_since_last_record',
                'mths_since_last_major_derog', 'mths_since_recent_bc_dlq',
                'mths_since_recent_revol_delinq']:
        if col in df.columns:
            df[col] = df[col].fillna(-1)

    for g in ['A', 'B', 'C', 'D', 'E']:
        df[f'grade_{g}'] = (df['grade'] == g).astype(int)
    df['home_ownership_OWN']          = (df['home_ownership'] == 'OWN').astype(int)
    df['home_ownership_MORTGAGE']     = (df['home_ownership'] == 'MORTGAGE').astype(int)
    df['verif_Verified']              = (df['verification_status'] == 'Verified').astype(int)
    df['verif_Source_Verified']       = (df['verification_status'] == 'Source Verified').astype(int)
    df['purpose_debt_consolidation']  = (df['purpose'] == 'debt_consolidation').astype(int)
    df['purpose_credit_card']         = (df['purpose'] == 'credit_card').astype(int)
    df['purpose_home_improvement']    = (df['purpose'] == 'home_improvement').astype(int)
    df['purpose_major_purchase']      = (df['purpose'] == 'major_purchase').astype(int)
    df['purpose_other'] = df['purpose'].isin([
        'car','medical','moving','vacation','wedding','house',
        'renewable_energy','educational','other']).astype(int)
    df['initial_list_w'] = (df['initial_list_status'] == 'w').astype(int)

    r = df['int_rate']
    df['int_rate_lt_0088'] = (r <= 0.088).astype(int)
    df['int_rate_088_117'] = ((r > 0.088) & (r <= 0.117)).astype(int)
    df['int_rate_117_148'] = ((r > 0.117) & (r <= 0.148)).astype(int)
    df['int_rate_148_176'] = ((r > 0.148) & (r <= 0.176)).astype(int)
    df['int_rate_176_200'] = ((r > 0.176) & (r <= 0.200)).astype(int)

    inc = df['annual_inc'].clip(upper=250000)
    df['annual_inc_25k_50k']  = ((inc > 25000) & (inc <= 50000)).astype(int)
    df['annual_inc_50k_75k']  = ((inc > 50000) & (inc <= 75000)).astype(int)
    df['annual_inc_75k_125k'] = ((inc > 75000) & (inc <= 125000)).astype(int)
    df['annual_inc_gt125k']   = (inc > 125000).astype(int)

    f = df['fico_score']
    df['fico_600_640'] = ((f >= 600) & (f < 640)).astype(int)
    df['fico_640_680'] = ((f >= 640) & (f < 680)).astype(int)
    df['fico_680_720'] = ((f >= 680) & (f < 720)).astype(int)
    df['fico_720_760'] = ((f >= 720) & (f < 760)).astype(int)
    df['fico_gt760']   = (f >= 760).astype(int)

    dti = df['dti']
    df['dti_lt_10'] = (dti <= 10).astype(int)
    df['dti_10_20'] = ((dti > 10) & (dti <= 20)).astype(int)
    df['dti_20_28'] = ((dti > 20) & (dti <= 28)).astype(int)
    df['dti_28_35'] = ((dti > 28) & (dti <= 35)).astype(int)

    df['term_36'] = (df['term_int'] == 36).astype(int)

    m = df['mths_since_issue_d']
    df['mths_issue_lt38']   = (m <= 38).astype(int)
    df['mths_issue_38_64']  = ((m > 38) & (m <= 64)).astype(int)
    df['mths_issue_64_95']  = ((m > 64) & (m <= 95)).astype(int)
    df['mths_issue_95_118'] = ((m > 95) & (m <= 118)).astype(int)

    cr = df['mths_since_earliest_cr_line']
    df['cr_line_lt80']    = (cr <= 80).astype(int)
    df['cr_line_80_140']  = ((cr > 80)  & (cr <= 140)).astype(int)
    df['cr_line_140_200'] = ((cr > 140) & (cr <= 200)).astype(int)
    df['cr_line_gt200']   = (cr > 200).astype(int)

    md = df['mths_since_last_delinq']
    df['delinq_never'] = (md == -1).astype(int)
    df['delinq_lt24']  = ((md >= 0) & (md < 24)).astype(int)
    df['delinq_24_48'] = ((md >= 24) & (md < 48)).astype(int)
    df['delinq_48_72'] = ((md >= 48) & (md < 72)).astype(int)

    ru = df['revol_util']
    df['revol_util_lt020'] = (ru < 0.20).astype(int)
    df['revol_util_20_40'] = ((ru >= 0.20) & (ru < 0.40)).astype(int)
    df['revol_util_40_60'] = ((ru >= 0.40) & (ru < 0.60)).astype(int)
    df['revol_util_60_80'] = ((ru >= 0.60) & (ru < 0.80)).astype(int)

    inq = df['inq_last_6mths']
    df['inq_0']   = (inq == 0).astype(int)
    df['inq_1']   = (inq == 1).astype(int)
    df['inq_2_3'] = ((inq >= 2) & (inq <= 3)).astype(int)

    p = df['pct_tl_nvr_dlq'].fillna(0) if 'pct_tl_nvr_dlq' in df.columns else 0
    df['pct_dlq_gt95']  = (p > 95).astype(int)
    df['pct_dlq_85_95'] = ((p >= 85) & (p <= 95)).astype(int)
    df['pct_dlq_70_85'] = ((p >= 70) & (p < 85)).astype(int)

    return df


def feature_engineering(**ctx):
    import json
    import pandas as pd
    from sqlalchemy import create_engine

    DATA   = "/opt/airflow/data/processed"
    DB_URL = f"postgresql://credit_risk:CreditRisk2026!@postgres/credit_risk"

    print("Loading cleaned loans from staging.loans_cleaned ...")
    engine = create_engine(DB_URL)
    df = pd.read_sql("SELECT * FROM staging.loans_cleaned", engine)
    print(f"  Loaded {len(df):,} rows")

    # Apply WoE dummy encoding
    df = encode_woe_dummies(df)

    avail = [c for c in DUMMY_COLS if c in df.columns]
    missing = set(DUMMY_COLS) - set(avail)
    if missing:
        print(f"  WARNING: {len(missing)} features zero-filled: {missing}")
        for c in missing:
            df[c] = 0

    train = df[df['dataset_split'] == 'train'].copy()
    oot   = df[df['dataset_split'] == 'oot'].copy()

    train_n = len(train); oot_n = len(oot)
    print(f"  Train: {train_n:,} (DR {1-train['good_bad'].mean():.2%})")
    print(f"  OOT:   {oot_n:,}   (DR {1-oot['good_bad'].mean():.2%})")

    train.to_parquet(f"{DATA}/train_preprocessed.parquet", index=False)
    oot.to_parquet(f"{DATA}/test_preprocessed.parquet",    index=False)
    with open(f"{DATA}/dummy_cols.json", 'w') as f:
        json.dump(DUMMY_COLS, f, indent=2)

    print(f"  Saved train_preprocessed.parquet ({train_n:,} rows)")
    print(f"  Saved test_preprocessed.parquet  ({oot_n:,} rows)")
    print(f"  Saved dummy_cols.json ({len(DUMMY_COLS)} features)")


with DAG(
    dag_id="credit_risk_feature_engineering",
    description="WoE dummy encoding → train/test parquets for model training",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["credit_risk", "features"],
) as dag:

    wait_for_cleaning = ExternalTaskSensor(
        task_id="wait_for_cleaning",
        external_dag_id="credit_risk_cleaning",
        external_task_id="spark_clean_loans",
        timeout=3600,
        poke_interval=30,
        mode="reschedule",
    )

    feat_task = PythonOperator(
        task_id="encode_woe_dummies",
        python_callable=feature_engineering,
    )

    wait_for_cleaning >> feat_task
