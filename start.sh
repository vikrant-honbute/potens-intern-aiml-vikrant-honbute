#!/usr/bin/env bash
set -euo pipefail

# Start FastAPI backend on port 8000
uvicorn api.main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit on port 7860 (Hugging Face Spaces port)
exec streamlit run app_streamlit.py \
  --server.port 7860 \
  --server.address 0.0.0.0 \
  --logger.level=info
