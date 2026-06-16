#!/bin/bash
# ── Credit Risk Project — Full Stack Startup ──────────────────────────────────
cd "$(dirname "$0")"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║     Credit Risk Project — Starting Full Stack        ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── 1. Docker services ────────────────────────────────────────────────────────
echo "▶  Starting Docker services..."
if ! docker info > /dev/null 2>&1; then
  echo "   ⚠  Docker is not running. Please open Docker Desktop first, then re-run this script."
  read -p "   Press Enter to exit..."
  exit 1
fi

docker compose up -d --remove-orphans 2>&1 | grep -E "(Starting|Creating|Running|error|Error)" || true

echo ""
echo "   Waiting for services to be healthy..."
sleep 5

echo ""
echo "   ✓  Docker services:"
echo "      Airflow    → http://localhost:8081  (admin / Airflow2026!)"
echo "      MLflow     → http://localhost:5001"
echo "      FastAPI    → http://localhost:8000/docs"
echo "      MinIO      → http://localhost:9001  (minioadmin / MinIO2026secure!)"
echo "      Grafana    → http://localhost:3000  (admin / Grafana2026!)"
echo "      Spark      → http://localhost:8085"
echo ""

# ── 2. Python deps (silent, skip if already installed) ───────────────────────
echo "▶  Checking Python dependencies..."
pip install streamlit plotly pandas numpy python-dotenv \
    langchain langchain-community langchain-core \
    langchain-text-splitters langchain-huggingface \
    chromadb sentence-transformers openai \
    --break-system-packages -q 2>/dev/null || true
echo "   ✓  Dependencies ready"
echo ""

# ── 3. RAG vector stores (skip if already built) ─────────────────────────────
if [ ! -d "chroma_db/pdf_store" ]; then
  echo "▶  Building RAG vector stores (first time only, ~5 min)..."
  python3 rag_ingest.py
  echo ""
else
  echo "▶  RAG vector stores already built — skipping ingestion"
  echo ""
fi

# ── 4. Streamlit dashboard ────────────────────────────────────────────────────
echo "▶  Starting Streamlit dashboard..."
echo "   Dashboard → http://localhost:8501"
echo ""
echo "   DeepSeek settings (auto-loaded from .env):"
echo "   API Key : sk-31b3e347e7694c9f991f08825b5984a2"
echo "   Base URL: https://api.deepseek.com/v1"
echo "   Model   : deepseek-v4-flash"
echo ""
echo "══════════════════════════════════════════════════════"
echo "   Opening browser in 3 seconds..."
sleep 3
open http://localhost:8501

streamlit run dashboard.py
