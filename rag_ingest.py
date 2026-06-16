"""
RAG Ingestion Script
====================
Run ONCE to build the ChromaDB vector stores for the chat interface.

Usage:
    python rag_ingest.py

Requires:
    pip install langchain langchain-community chromadb sentence-transformers pypdf pandas pyarrow
"""

import os
import pandas as pd
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE         = Path(__file__).parent
DOCS_DIR     = BASE / "docs"
PROCESSED    = BASE / "data" / "processed"
CHROMA_DIR   = BASE / "chroma_db"

# ── Config ────────────────────────────────────────────────────────────────────
EMBED_MODEL    = "all-MiniLM-L6-v2"   # free, runs locally, ~80 MB download
CHUNK_SIZE     = 500
CHUNK_OVERLAP  = 50
PDF_STORE_DIR  = str(CHROMA_DIR / "pdf_store")
DATA_STORE_DIR = str(CHROMA_DIR / "data_store")

# How many loan rows to embed (5 000 is plenty — don't embed all 538k)
DATA_SAMPLE_N  = 5_000


# ══════════════════════════════════════════════════════════════════════════════
# PDF PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def build_pdf_store(embeddings) -> None:
    """Load both research PDFs, chunk them, embed and persist to ChromaDB."""
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import Chroma

    print("── PDF vector store ──")

    pdf_files = [
        DOCS_DIR / "Research_Report.pdf",
        DOCS_DIR / "Research_Report_DE.pdf",
    ]

    all_docs = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )

    for pdf_path in pdf_files:
        if not pdf_path.exists():
            print(f"  ⚠  Not found: {pdf_path.name} — skipping")
            continue
        print(f"  Loading {pdf_path.name} ...", end=" ", flush=True)
        loader = PyPDFLoader(str(pdf_path))
        pages  = loader.load()
        chunks = splitter.split_documents(pages)
        for c in chunks:
            c.metadata["source_file"] = pdf_path.name
        all_docs.extend(chunks)
        print(f"{len(chunks)} chunks")

    if not all_docs:
        print("  ✗  No PDFs loaded.")
        return

    print(f"  Embedding {len(all_docs)} chunks (this takes ~1 min on CPU) ...")
    Chroma.from_documents(all_docs, embeddings, persist_directory=PDF_STORE_DIR)
    print(f"  ✓  Saved → {PDF_STORE_DIR}")


# ══════════════════════════════════════════════════════════════════════════════
# DATA PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def _row_to_text(row: pd.Series, idx: int) -> str:
    """Serialise a DataFrame row to a readable sentence."""
    parts = [f"Loan #{idx}:"]
    for col, val in row.items():
        if pd.isna(val):
            continue
        if isinstance(val, float):
            parts.append(f"{col}={val:.4f}")
        else:
            parts.append(f"{col}={val}")
    return " | ".join(parts)


def _grade_summaries(df: pd.DataFrame, source: str) -> list:
    """Build one summary chunk per grade (A–G) — great for aggregate questions."""
    from langchain_core.documents import Document
    docs = []
    grade_col = next((c for c in ["grade", "sub_grade"] if c in df.columns), None)
    if grade_col is None:
        return docs

    numeric_cols = df.select_dtypes("number").columns.tolist()[:20]

    for grade_val, grp in df.groupby(grade_col):
        lines = [f"Grade {grade_val} aggregate summary ({len(grp):,} loans):"]
        for col in numeric_cols:
            lines.append(
                f"  {col}: mean={grp[col].mean():.4f} | "
                f"median={grp[col].median():.4f} | "
                f"std={grp[col].std():.4f}"
            )
        docs.append(Document(
            page_content="\n".join(lines),
            metadata={"source_file": source, "chunk_type": "grade_summary", "grade": str(grade_val)},
        ))
    return docs


def build_data_store(embeddings) -> None:
    """Load parquet files, convert to text chunks, embed and persist."""
    from langchain_core.documents import Document
    from langchain_community.vectorstores import Chroma

    print("── Data vector store ──")

    all_docs: list[Document] = []

    # ── 1. Expected-loss file (PD, LGD, EAD, EL per loan) ────────────────────
    el_path = PROCESSED / "expected_loss_test.parquet"
    if el_path.exists():
        print(f"  Loading expected_loss_test.parquet ...", end=" ", flush=True)
        df_el = pd.read_parquet(el_path)
        sample = df_el.sample(n=min(DATA_SAMPLE_N, len(df_el)), random_state=42)
        row_docs = [
            Document(
                page_content=_row_to_text(row, i),
                metadata={"source_file": "expected_loss_test.parquet", "row": i},
            )
            for i, (_, row) in enumerate(sample.iterrows())
        ]
        all_docs.extend(row_docs)
        all_docs.extend(_grade_summaries(df_el, "expected_loss_test.parquet"))
        print(f"{len(row_docs)} row chunks + {len(df_el['grade'].unique()) if 'grade' in df_el.columns else 0} grade summaries")
    else:
        print(f"  ⚠  expected_loss_test.parquet not found — skipping")

    # ── 2. IFRS 9 scenario ECL file ───────────────────────────────────────────
    ifrs_path = PROCESSED / "ifrs9_scenario_ecl.parquet"
    if ifrs_path.exists():
        print(f"  Loading ifrs9_scenario_ecl.parquet ...", end=" ", flush=True)
        df_ifrs = pd.read_parquet(ifrs_path)
        sample2 = df_ifrs.sample(n=min(2_000, len(df_ifrs)), random_state=42)
        ifrs_docs = [
            Document(
                page_content=_row_to_text(row, i),
                metadata={"source_file": "ifrs9_scenario_ecl.parquet", "row": i},
            )
            for i, (_, row) in enumerate(sample2.iterrows())
        ]
        all_docs.extend(ifrs_docs)
        all_docs.extend(_grade_summaries(df_ifrs, "ifrs9_scenario_ecl.parquet"))
        print(f"{len(ifrs_docs)} row chunks")
    else:
        print(f"  ⚠  ifrs9_scenario_ecl.parquet not found — skipping")

    # ── 3. PSI results (monitoring) ───────────────────────────────────────────
    psi_path = PROCESSED / "psi_results.csv"
    if psi_path.exists():
        df_psi = pd.read_csv(psi_path)
        psi_text = "PSI monitoring results:\n" + df_psi.to_string(index=False)
        all_docs.append(Document(
            page_content=psi_text,
            metadata={"source_file": "psi_results.csv", "chunk_type": "monitoring"},
        ))

    if not all_docs:
        print("  ✗  No data loaded.")
        return

    print(f"  Embedding {len(all_docs)} total chunks ...")
    Chroma.from_documents(all_docs, embeddings, persist_directory=DATA_STORE_DIR)
    print(f"  ✓  Saved → {DATA_STORE_DIR}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from langchain_huggingface import HuggingFaceEmbeddings

    CHROMA_DIR.mkdir(exist_ok=True)

    print(f"Embedding model : {EMBED_MODEL}")
    print(f"Output directory: {CHROMA_DIR}\n")

    print("Loading embedding model (downloads ~80 MB on first run) ...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    print("  ✓  Model ready\n")

    build_pdf_store(embeddings)
    print()
    build_data_store(embeddings)

    print("\n✅  Both vector stores built.")
    print("Next: add your LLM API key to .env, then run  streamlit run dashboard.py")
