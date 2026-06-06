# 🏦 Lending Club Credit Risk — Data Engineering Pipeline

> End-to-end credit risk modelling platform built on a modern open-source data stack.  
> Covers raw ingestion → feature engineering → PD / LGD / EAD model training → batch scoring → monitoring, all orchestrated by Apache Airflow and tracked with MLflow.

---

## 📐 Architecture

```
Raw CSV (MinIO)
     │
     ▼
Apache Spark ──► PostgreSQL DWH
     │                 │
     ▼                 ▼
ML Training       FastAPI Scoring
(MLflow)          Service
     │                 │
     └────────┬────────┘
              ▼
     Grafana / Prometheus
          (Monitoring)
```

## 🗂️ Project Structure

```
.
├── api/                  # FastAPI scoring service
│   ├── main.py
│   ├── model_loader.py
│   ├── routers/
│   ├── schemas/
│   ├── requirements.txt
│   └── Dockerfile
│
├── dags/                 # Airflow DAGs (pipeline orchestration)
│   ├── 01_ingestion.py
│   ├── 02_cleaning.py
│   ├── 03_pd_training.py
│   ├── 04_lgd_ead_training.py
│   ├── 05_batch_scoring.py
│   └── 06_monitoring.py
│
├── spark_jobs/           # PySpark transformation jobs
│   ├── 01_ingest.py
│   └── 02_clean.py
│
├── ml/                   # Model training & evaluation modules
│   ├── preprocessing/
│   ├── training/
│   ├── evaluation/
│   └── models/
│
├── risk/                 # Risk-specific business logic
│   ├── expected_loss.py
│   └── psi_monitor.py
│
├── notebooks/            # Exploratory & presentation notebooks
│   ├── L01_Preprocessing_Feature_Engineering.ipynb
│   ├── L02_PD_Model_Scorecard.ipynb
│   ├── L03_LGD_EAD_Expected_Loss.ipynb
│   └── L04_Population_Stability_Index.ipynb
│
├── infrastructure/       # Docker service configs
│   ├── airflow/
│   ├── spark/
│   ├── mlflow/
│   ├── postgres/
│   └── grafana/
│
├── tests/                # Unit & integration tests
│
├── data/                 # ⚠️ gitignored — not committed
│   ├── raw/              #   Lending Club CSV (~1.6 GB)
│   ├── processed/        #   Parquet feature store
│   ├── models/           #   Serialised model artefacts
│   └── reports/          #   PSI / scorecard outputs
│
├── docker-compose.yml    # Full stack compose file
├── Makefile              # Developer shortcuts
├── .env.example          # Environment template (copy → .env)
├── requirements_notebooks.txt
└── SETUP.md
```

## 🚀 Quick Start

### 1. Clone & configure environment
```bash
git clone https://github.com/DUKPagnarith/lending_club_DE.git
cd lending_club_DE
cp .env.example .env
# Edit .env with your passwords / keys
```

### 2. Download the dataset
Download `accepted_2007_to_2018Q4.csv` from [Kaggle — Lending Club Loan Data](https://www.kaggle.com/datasets/wordsforthewise/lending-club) and place it at:
```
data/raw/accepted_2007_to_2018Q4.csv
```

### 3. Start the stack
```bash
make up          # docker compose up -d --build
```

Service URLs after boot:

| Service | URL |
|---|---|
| Airflow | http://localhost:8081 |
| Spark Master | http://localhost:8080 |
| MLflow | http://localhost:5001 |
| MinIO Console | http://localhost:9001 |
| FastAPI | http://localhost:8000/docs |
| Grafana | http://localhost:3000 |

### 4. Run the pipeline
```bash
make pipeline    # triggers all 6 Airflow DAGs in order
```
Or trigger DAGs individually from the Airflow UI.

---

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | Apache Airflow 2.x |
| Compute | Apache Spark 3.x |
| Storage | MinIO (S3-compatible) |
| DWH | PostgreSQL 15 |
| ML Tracking | MLflow 2.x |
| Model Serving | FastAPI + Redis cache |
| Monitoring | Prometheus + Grafana |
| Containerisation | Docker Compose |

## 📊 Models

| Model | Target | Algorithm |
|---|---|---|
| PD (Probability of Default) | Binary classification | Logistic Regression / Scorecard |
| LGD (Loss Given Default) | Two-stage regression | Stage-1: classifier, Stage-2: regressor |
| EAD (Exposure at Default) | Regression | Linear Regression + Scaler |
| Expected Loss | Derived | `EL = PD × LGD × EAD` |

## 📖 Documentation

- [`SETUP.md`](SETUP.md) — detailed environment setup guide
- [`Column_Mapping.md`](Column_Mapping.md) — feature descriptions & mappings
- [`Credit_Risk_Implementation_Plan.md`](Credit_Risk_Implementation_Plan.md) — full technical design doc

## 🔒 Security

- Never commit `.env` — use `.env.example` as a template
- Secrets are injected via Docker env_file at runtime
- All default passwords in `.env.example` **must** be changed before production

---

## 📄 License

Academic / research use. Dataset subject to [Lending Club Terms of Service](https://www.lendingclub.com/legal/terms-of-service).
