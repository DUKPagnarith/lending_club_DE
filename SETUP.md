# Credit Risk System — Full Setup Guide
**Lending Club 2007–2018 | 2.26M rows | 151 columns**

---

## Project Structure

```
I4_risk_management/
├── data/
│   ├── raw/accepted_2007_to_2018Q4.csv   ← YOUR DATASET (already here)
│   ├── processed/                          ← L01 outputs (parquet files)
│   └── models/                             ← saved model pkl files
├── notebooks/
│   ├── L01_Preprocessing_Feature_Engineering.ipynb
│   ├── L02_PD_Model_Scorecard.ipynb
│   ├── L03_LGD_EAD_Expected_Loss.ipynb
│   └── L04_Population_Stability_Index.ipynb
├── spark_jobs/                             ← Production PySpark scripts
├── dags/                                   ← Airflow DAGs
├── ml/                                     ← Model training modules
├── api/                                    ← FastAPI scoring service
├── risk/                                   ← Risk management scripts
├── infrastructure/                         ← Docker service configs
├── docker-compose.yml                      ← All services
├── .env                                    ← Your secrets (copy from .env.example)
├── Makefile                                ← Quick commands
├── requirements_notebooks.txt             ← Notebook dependencies
└── requirements_pipeline.txt              ← Full pipeline dependencies
```

---

## TRACK 1 — Run Learning Notebooks (Start Here)

### Step 1 — Create conda environment

```bash
cd "/Users/dukpagnarith/Documents/Obsidian Vault/project 2026/I4_risk_management"

conda create -n credit_risk python=3.11 -y
conda activate credit_risk

pip install -r requirements_notebooks.txt
```

### Step 2 — Launch Jupyter

```bash
conda activate credit_risk
cd "/Users/dukpagnarith/Documents/Obsidian Vault/project 2026/I4_risk_management"
jupyter notebook
```

### Step 3 — Run notebooks in order

| Order | Notebook | Runtime | Output |
|-------|---------|---------|--------|
| 1st | `L01_Preprocessing_Feature_Engineering.ipynb` | ~10 min | `data/processed/train_preprocessed.parquet` |
| 2nd | `L02_PD_Model_Scorecard.ipynb` | ~5 min | `data/processed/scorecard.csv` |
| 3rd | `L03_LGD_EAD_Expected_Loss.ipynb` | ~5 min | `data/models/lgd_stage1.pkl` |
| 4th | `L04_Population_Stability_Index.ipynb` | ~3 min | `data/processed/psi_results.csv` |

> **Important:** L01 loads 2.26M rows — it will take a few minutes. The parquet outputs are much faster to reload in subsequent notebooks.

---

## TRACK 2 — Docker Pipeline (Production)

### Prerequisites

```bash
# 1. Install Docker Desktop for Mac
# https://docs.docker.com/desktop/install/mac-install/

# 2. Verify Docker is running
docker --version
docker-compose --version
```

### Step 1 — Configure environment

```bash
cd "/Users/dukpagnarith/Documents/Obsidian Vault/project 2026/I4_risk_management"

# Copy env template
cp .env.example .env

# Edit .env with your passwords (open in any text editor)
# Minimum required: POSTGRES_PASSWORD, MINIO_PASSWORD, AIRFLOW_FERNET_KEY
```

Generate a Fernet key for Airflow:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Step 2 — Start all services

```bash
make up
# OR manually:
docker-compose up -d
```

This starts:
| Service | URL | Purpose |
|---------|-----|---------|
| PostgreSQL | localhost:5432 | Data warehouse (5 schemas) |
| MinIO | localhost:9001 | Data lake (S3-compatible) |
| Spark Master | localhost:8080 | Big data processing |
| Airflow | localhost:8081 | Pipeline orchestration |
| MLflow | localhost:5000 | Model tracking & registry |
| FastAPI | localhost:8000 | Real-time scoring |
| Grafana | localhost:3000 | Dashboards & monitoring |
| Prometheus | localhost:9090 | Metrics collection |

### Step 3 — Initialize database

```bash
make init-db
# Creates all schemas: raw, staging, features, models, risk, audit
```

### Step 4 — Upload data to MinIO

```bash
make upload-data
# Copies accepted_2007_to_2018Q4.csv → MinIO landing-zone bucket
```

### Step 5 — Trigger the pipeline

Open Airflow at http://localhost:8081 (user: admin, pass: from .env)

Enable and trigger DAGs in order:
1. `credit_risk_ingestion`
2. `credit_risk_cleaning`
3. `credit_risk_features`
4. `credit_risk_pd_training`
5. `credit_risk_lgd_ead_training`
6. `credit_risk_batch_scoring`
7. `credit_risk_monitoring` (runs daily automatically)

### Step 6 — Test the scoring API

```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "loan_amnt": 15000,
    "term_int": 36,
    "int_rate": 0.1199,
    "grade": "B",
    "emp_length_int": 5,
    "home_ownership": "MORTGAGE",
    "annual_inc": 75000,
    "purpose": "debt_consolidation",
    "dti": 18.5,
    "fico_score": 710,
    "inq_last_6mths": 1,
    "revol_util": 0.42
  }'
```

Expected response:
```json
{
  "pd": 0.0821,
  "lgd": 0.5934,
  "ead": 14250.00,
  "expected_loss": 693.45,
  "credit_score": 648,
  "risk_class": "B",
  "decision": "APPROVE",
  "annualized_roi": 0.0412
}
```

---

## Common Commands (Makefile)

```bash
make up          # Start all Docker services
make down        # Stop all services
make restart     # Restart all services
make logs        # Tail all logs
make init-db     # Initialize PostgreSQL schemas
make upload-data # Upload CSV to MinIO
make test        # Run unit tests
make clean       # Remove all containers + volumes (⚠️ deletes data)
make status      # Show service health
```

---

## Troubleshooting

**Airflow fails to start:**
```bash
docker-compose run --rm airflow-webserver airflow db init
docker-compose run --rm airflow-webserver airflow users create \
  --username admin --password admin \
  --firstname Admin --lastname Admin \
  --role Admin --email admin@bank.com
```

**Spark out of memory:**
```bash
# In docker-compose.yml, increase:
SPARK_WORKER_MEMORY=8G   # default: 4G
```

**MLflow can't connect to MinIO:**
```bash
# Verify MinIO is up:
docker-compose ps minio
# Check MINIO_ROOT_USER and MINIO_ROOT_PASSWORD in .env match
```

**PostgreSQL connection refused:**
```bash
docker-compose logs postgres
# Wait for "database system is ready to accept connections"
```
