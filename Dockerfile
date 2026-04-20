# FastAPI backend for The Legacy — deployed to Fly.io to proxy browser
# requests into SageMaker.
#
# The container runs src/server.py with the SageMaker backend. Configure at
# runtime via Fly secrets:
#   INFERENCE_BACKEND=sagemaker     (required)
#   SAGEMAKER_ENDPOINT=the-legacy-llm
#   AWS_REGION=us-east-1
#   AWS_ACCESS_KEY_ID=...           (set via `fly secrets set`)
#   AWS_SECRET_ACCESS_KEY=...       (set via `fly secrets set`)
#
# Local build + run:
#   docker build -t the-legacy-api .
#   docker run -p 8000:8000 --env-file .env the-legacy-api
#
# Fly deploy:
#   fly launch --no-deploy    # first time, generates fly.toml (already committed)
#   fly secrets set AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...
#   fly deploy

FROM python:3.11-slim

WORKDIR /app

# System deps. libgomp1 is needed by rapidfuzz and sentence-transformers.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Pin to CPU torch so we don't pull the 2GB CUDA variant.
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch

# Core runtime dependencies.
RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn[standard]==0.31.0 \
    httpx==0.27.2 \
    pydantic==2.9.2 \
    boto3==1.35.33 \
    sagemaker==2.232.2 \
    rapidfuzz==3.10.0 \
    chromadb==0.5.11 \
    sentence-transformers==3.1.1

# Pre-download the RAG embedding model (~80MB) during build so cold starts
# don't re-download it every time the Fly machine wakes from scale-to-zero.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy what the server needs at runtime.
# card_index.pkl powers fuzzy card name resolution.
# vectordb/ is the ChromaDB store built by src/build_vectordb.py — enables
# RAG retrieval over the comprehensive rules, meta analysis, and archetype docs.
# scryfall-cards.json (508MB raw data) is NOT copied — card_index.pkl is the
# compiled form that gets used at runtime.
COPY src/ /app/src/
COPY data/card_index.pkl /app/data/card_index.pkl
COPY vectordb/ /app/vectordb/

# Static frontend served from the same FastAPI process — no separate hosting
COPY docs/ /app/docs/

EXPOSE 8000

# HF Spaces expects the app on port 7860; allow override via PORT env.
ENV PORT=8000

CMD uvicorn src.server:app --host 0.0.0.0 --port ${PORT}
