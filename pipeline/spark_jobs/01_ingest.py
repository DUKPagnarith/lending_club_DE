"""
Spark Job 01 — Ingest raw CSV from MinIO into PostgreSQL raw schema.
Handles: 2.26M rows, 151 columns, accepted_2007_to_2018Q4.csv
"""
import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

def get_spark():
    return (SparkSession.builder
        .appName("CreditRisk_Ingest")
        .config("spark.sql.shuffle.partitions", "200")
        .config("spark.jars.packages",
                "org.apache.hadoop:hadoop-aws:3.3.4,"
                "org.postgresql:postgresql:42.6.0")
        .config("spark.hadoop.fs.s3a.endpoint", os.getenv("MINIO_URL","http://minio:9000"))
        .config("spark.hadoop.fs.s3a.access.key", os.getenv("MINIO_USER","minioadmin"))
        .config("spark.hadoop.fs.s3a.secret.key", os.getenv("MINIO_PASSWORD",""))
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .getOrCreate())

POSTGRES_URL  = f"jdbc:postgresql://postgres:5432/credit_risk"
POSTGRES_PROPS = {
    "user":     os.getenv("POSTGRES_USER","credit_risk"),
    "password": os.getenv("POSTGRES_PASSWORD",""),
    "driver":   "org.postgresql.Driver",
}

# Only the columns we need for modeling
KEEP_COLS = [
    "id","loan_amnt","funded_amnt","term","int_rate","installment",
    "grade","sub_grade","emp_length","home_ownership","annual_inc",
    "verification_status","issue_d","loan_status","purpose","addr_state",
    "dti","delinq_2yrs","earliest_cr_line","fico_range_low","fico_range_high",
    "inq_last_6mths","mths_since_last_delinq","mths_since_last_record",
    "open_acc","pub_rec","revol_bal","revol_util","total_acc",
    "initial_list_status","application_type","hardship_flag",
    "debt_settlement_flag","bc_util","pct_tl_nvr_dlq","mort_acc",
    "num_accts_ever_120_pd","acc_open_past_24mths","tot_cur_bal",
    # Post-origination — needed to create targets BEFORE dropping
    "recoveries","total_pymnt",
]

def main():
    spark = get_spark()
    source = "s3a://landing-zone/accepted_2007_to_2018Q4.csv"
    print(f"Reading: {source}")

    df = (spark.read
          .option("header", "true")
          .option("inferSchema", "true")
          .csv(source))

    print(f"Raw shape: {df.count():,} rows x {len(df.columns)} cols")

    # Keep only needed cols that exist
    existing = set(df.columns)
    cols = [c for c in KEEP_COLS if c in existing]
    df = df.select(cols)
    df = df.withColumn("source_file", F.lit("accepted_2007_to_2018Q4.csv"))
    df = df.withColumn("ingested_at", F.current_timestamp())

    (df.write.format("jdbc")
       .option("url", POSTGRES_URL)
       .option("dbtable", "raw.loan_applications")
       .option("batchsize", "50000")
       .option("numPartitions", "20")
       .options(**POSTGRES_PROPS)
       .mode("overwrite")
       .save())

    print(f"Ingested {df.count():,} rows → raw.loan_applications ✓")
    spark.stop()

if __name__ == "__main__":
    main()
