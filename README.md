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
├── pipeline/                 # End-to-end pipeline code
│   ├── dags/                 # Airflow orchestration DAGs
│   │   ├── 01_ingestion.py
│   │   ├── 02_cleaning.py
│   │   ├── 03_pd_training.py
│   │   ├── 04_lgd_ead_training.py
│   │   ├── 05_batch_scoring.py
│   │   └── 06_monitoring.py
│   └── spark_jobs/           # PySpark transformation jobs
│       ├── 01_ingest.py
│       └── 02_clean.py
│
├── models/                   # All model-related Python code
│   ├── preprocessing/        # Feature engineering & WoE encoding
│   │   └── woe_encoder.py
│   ├── training/             # Model training scripts
│   │   ├── train_pd.py
│   │   └── train_lgd_ead.py
│   ├── evaluation/           # Metrics & evaluation utilities
│   │   └── metrics.py
│   ├── architectures/        # Model class definitions
│   │   ├── pd_model.py
│   │   └── lgd_model.py
│   └── risk/                 # Business risk logic
│       ├── expected_loss.py
│       └── psi_monitor.py
│
├── api/                      # FastAPI scoring service
│   ├── main.py
│   ├── model_loader.py
│   ├── routers/
│   ├── schemas/
│   ├── requirements.txt
│   └── Dockerfile
│
├── infrastructure/           # Docker service configurations
│   ├── airflow/
│   ├── spark/
│   ├── mlflow/
│   ├── postgres/
│   └── grafana/
│
├── notebooks/                # Jupyter analysis notebooks
│   ├── L01_Preprocessing_Feature_Engineering.ipynb
│   ├── L02_PD_Model_Scorecard.ipynb
│   ├── L03_LGD_EAD_Expected_Loss.ipynb
│   └── L04_Population_Stability_Index.ipynb
│
├── docs/                     # Documentation & research
│   ├── Column_Mapping.md
│   ├── Credit_Risk_Implementation_Plan.md
│   ├── Literature_review_V1.md
│   ├── Literature_review_V2.md
│   └── research.md
│
├── scripts/                  # Utility & dev scripts
│   └── build_presentation.py
│
├── data/                     # ⚠️ gitignored — local only
│   ├── raw/                  #   Lending Club CSV (~1.6 GB)
│   ├── processed/            #   Parquet feature store
│   ├── artifacts/            #   Serialised model .pkl files
│   └── reports/              #   PSI / scorecard outputs
│
├── tests/                    # Unit & integration tests
│
├── docker-compose.yml        # Full stack compose file
├── Makefile                  # Developer shortcuts
├── .env.example              # Environment template (copy → .env)
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
Trigger DAGs individually from the Airflow UI, or use:
```bash
make train-pd    # Run PD model training
make train-lgd   # Run LGD/EAD model training
```

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
- [`docs/Column_Mapping.md`](docs/Column_Mapping.md) — feature descriptions & mappings
- [`docs/Credit_Risk_Implementation_Plan.md`](docs/Credit_Risk_Implementation_Plan.md) — full technical design doc
- [`docs/Literature_review_V2.md`](docs/Literature_review_V2.md) — literature review

## 🔒 Security

- Never commit `.env` — use `.env.example` as a template
- Secrets are injected via Docker env_file at runtime
- All default passwords in `.env.example` **must** be changed before production

---

## 📄 License

Academic / research use. Dataset subject to [Lending Club Terms of Service](https://www.lendingclub.com/legal/terms-of-service).
