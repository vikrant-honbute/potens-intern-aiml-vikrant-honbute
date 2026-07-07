#!/usr/bin/env bash
set -euo pipefail

uvicorn api.main:app --host 0.0.0.0 --port 8000 &
exec streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 7860
