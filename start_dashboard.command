#!/bin/bash
cd "$(dirname "$0")"
pip install streamlit plotly pandas numpy --break-system-packages -q 2>/dev/null || true
streamlit run dashboard.py
