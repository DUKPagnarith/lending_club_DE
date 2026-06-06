.PHONY: up down restart logs status init-db upload-data test clean help

BASE_DIR := $(shell pwd)
DATA_FILE := data/raw/accepted_2007_to_2018Q4.csv

help:
	@echo "Credit Risk System — Available Commands"
	@echo "======================================="
	@echo "  make up           Start all Docker services"
	@echo "  make down         Stop all services"
	@echo "  make restart      Restart all services"
	@echo "  make logs         Tail all container logs"
	@echo "  make status       Show service health"
	@echo "  make init-db      Initialize PostgreSQL schemas"
	@echo "  make upload-data  Upload CSV to MinIO data lake"
	@echo "  make test         Run unit tests"
	@echo "  make clean        Remove all containers + volumes (⚠️ deletes data)"
	@echo ""
	@echo "  make notebook     Launch Jupyter for L01-L04"
	@echo "  make train-pd     Run PD model training script"
	@echo "  make train-lgd    Run LGD/EAD model training script"
	@echo "  make score-test   Test the scoring API endpoint"

up:
	docker-compose up -d
	@echo "Services starting... Check status with: make status"
	@echo "Airflow UI:  http://localhost:8081"
	@echo "MLflow UI:   http://localhost:5000"
	@echo "MinIO UI:    http://localhost:9001"
	@echo "Grafana UI:  http://localhost:3000"
	@echo "Spark UI:    http://localhost:8080"
	@echo "API:         http://localhost:8000"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f --tail=100

status:
	docker-compose ps

init-db:
	docker-compose exec postgres psql -U $${POSTGRES_USER:-credit_risk} -d credit_risk -f /docker-entrypoint-initdb.d/01_init.sql
	@echo "Database schemas initialized ✓"

upload-data:
	@echo "Uploading $(DATA_FILE) to MinIO..."
	docker-compose run --rm minio-init sh -c "\
		mc alias set local http://minio:9000 $${MINIO_USER} $${MINIO_PASSWORD} && \
		mc cp /data/$(DATA_FILE) local/landing-zone/"
	@echo "Data uploaded ✓"

notebook:
	conda run -n credit_risk jupyter notebook notebooks/

train-pd:
	conda run -n credit_risk python models/training/train_pd.py

train-lgd:
	conda run -n credit_risk python models/training/train_lgd_ead.py

score-test:
	curl -s -X POST http://localhost:8000/score \
		-H "Content-Type: application/json" \
		-d '{"loan_amnt":15000,"term_int":36,"int_rate":0.1199,"grade":"B","emp_length_int":5,"home_ownership":"MORTGAGE","annual_inc":75000,"purpose":"debt_consolidation","dti":18.5,"fico_score":710,"inq_last_6mths":1,"revol_util":0.42}' \
		| python3 -m json.tool

test:
	conda run -n credit_risk python -m pytest tests/ -v

clean:
	@echo "⚠️  This will delete ALL data. Continue? [y/N]" && read ans && [ $${ans:-N} = y ]
	docker-compose down -v --remove-orphans
	@echo "All containers and volumes removed."
