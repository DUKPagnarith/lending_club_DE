"""
Spark Job 02 — Clean raw loans, create targets, apply OOT split.
Input:  raw.loan_applications (PostgreSQL)
Output: staging.loans_cleaned (PostgreSQL) + parquet backup to MinIO
"""
import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, FloatType

POSTGRES_URL   = "jdbc:postgresql://postgres:5432/credit_risk"
POSTGRES_PROPS = {"user": os.getenv("POSTGRES_USER","credit_risk"),
                  "password": os.getenv("POSTGRES_PASSWORD",""),
                  "driver": "org.postgresql.Driver"}
TRAIN_CUTOFF   = int(os.getenv("TRAIN_CUTOFF_YEAR", "2015"))

BAD_STATUSES = [
    "Charged Off", "Default",
    "Does not meet the credit policy. Status:Charged Off",
    "Late (31-120 days)"
]
GOOD_STATUSES = [
    "Fully Paid",
    "Does not meet the credit policy. Status:Fully Paid"
]

def clean(df):
    # ── Create targets BEFORE dropping post-origination cols ─────────────
    bad_cond  = F.col("loan_status").isin(BAD_STATUSES)
    good_cond = F.col("loan_status").isin(GOOD_STATUSES)
    df = df.filter(bad_cond | good_cond)
    df = df.withColumn("good_bad", F.when(bad_cond, 0).otherwise(1).cast(IntegerType()))
    df = df.withColumn("recovery_rate",
        F.when(bad_cond,
               (F.col("recoveries") / F.col("funded_amnt")).cast(FloatType()))
        .otherwise(F.lit(None)))
    df = df.withColumn("ccf",
        F.when(bad_cond,
               ((F.col("funded_amnt") - F.col("total_pymnt")) / F.col("funded_amnt"))
               .cast(FloatType()))
        .otherwise(F.lit(None)))

    # ── Format conversions ────────────────────────────────────────────────
    # term: " 36 months" → 36
    df = df.withColumn("term_int",
        F.regexp_extract(F.col("term"), r"(\d+)", 1).cast(IntegerType()))
    # int_rate: 13.99 → 0.1399
    df = df.withColumn("int_rate", (F.col("int_rate") / 100).cast(FloatType()))
    # revol_util: 29.7 → 0.297
    df = df.withColumn("revol_util", (F.col("revol_util") / 100).cast(FloatType()))
    # emp_length → int
    df = df.withColumn("emp_length_int",
        F.regexp_extract(F.coalesce(F.col("emp_length"), F.lit("0")), r"(\d+)", 1)
        .cast(IntegerType()))

    # ── Date features ─────────────────────────────────────────────────────
    df = df.withColumn("issue_d_parsed",
        F.to_timestamp(F.col("issue_d"), "yyyy-MM-dd HH:mm:ss"))
    df = df.withColumn("earliest_cr_line_parsed",
        F.to_date(F.col("earliest_cr_line"), "MMM-yyyy"))
    ref_date = df.agg(F.max("issue_d_parsed")).collect()[0][0]
    df = df.withColumn("mths_since_issue_d",
        F.round(F.months_between(F.lit(ref_date), F.col("issue_d_parsed"))).cast(IntegerType()))
    df = df.withColumn("mths_since_earliest_cr_line",
        F.round(F.months_between(F.lit(ref_date), F.col("earliest_cr_line_parsed"))).cast(IntegerType()))
    df = df.withColumn("issue_year", F.year(F.col("issue_d_parsed")).cast(IntegerType()))
    df = df.withColumn("fico_score",
        ((F.col("fico_range_low") + F.col("fico_range_high")) / 2).cast(FloatType()))

    # ── Missing sentinel for WoE ──────────────────────────────────────────
    for col in ["mths_since_last_delinq", "mths_since_last_record"]:
        df = df.withColumn(col, F.coalesce(F.col(col), F.lit(-1.0)))

    # ── OOT split ─────────────────────────────────────────────────────────
    df = df.withColumn("dataset_split",
        F.when(F.col("issue_year") <= TRAIN_CUTOFF, "train").otherwise("oot"))

    return df

def main():
    spark = SparkSession.builder.appName("CreditRisk_Clean").getOrCreate()
    df = (spark.read.format("jdbc").option("url", POSTGRES_URL)
          .option("dbtable", "raw.loan_applications")
          .option("numPartitions", "20").option("partitionColumn", "id")
          .option("lowerBound", "1").option("upperBound", "3000000")
          .options(**POSTGRES_PROPS).load())
    print(f"Raw rows: {df.count():,}")
    df_clean = clean(df)
    train_n = df_clean.filter(F.col("dataset_split")=="train").count()
    oot_n   = df_clean.filter(F.col("dataset_split")=="oot").count()
    print(f"Train (2007-{TRAIN_CUTOFF}): {train_n:,} | OOT: {oot_n:,}")

    (df_clean.write.format("jdbc").option("url", POSTGRES_URL)
     .option("dbtable", "staging.loans_cleaned")
     .option("batchsize", "50000").option("numPartitions", "20")
     .options(**POSTGRES_PROPS).mode("overwrite").save())

    # Parquet backup to MinIO
    (df_clean.write.mode("overwrite")
     .parquet("s3a://spark-output/staging/loans_cleaned/"))
    print("Cleaning complete ✓")
    spark.stop()

if __name__ == "__main__":
    main()
