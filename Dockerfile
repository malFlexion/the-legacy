# FastAPI backend for The Legacy — single-container deploy on Fly.io running
# the finetuned GGUF locally via llama-cpp-python. No external model service.
#
# Configure at runtime via Fly secrets / env:
#   INFERENCE_BACKEND=llamacpp      (picked up by src/server.py)
#   LLAMACPP_MODEL_PATH=./the-legacy.gguf   (default)
#   LLAMACPP_N_THREADS=2            (match VM dedicated cores)
#   LLAMACPP_N_CTX=2048             (context window)
#
# Local build + run:
#   docker build -t the-legacy-api .
#   docker run -p 8000:8000 -e INFERENCE_BACKEND=llamacpp the-legacy-api
#
# Fly deploy (first time):
#   fly launch --no-deploy
#   fly secrets set INFERENCE_BACKEND=llamacpp
#   fly deploy

FROM python:3.11-slim

WORKDIR /app

# System deps. libgomp1 is needed by rapidfuzz and sentence-transformers.
# build-essential + cmake are needed for llama-cpp-python's from-source build
# (there are no pre-built CPU wheels for every Python minor version).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    build-essential \
    cmake \
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
    rapidfuzz==3.10.0 \
    chromadb==0.5.11 \
    sentence-transformers==3.1.1

# llama-cpp-python for in-process GGUF inference. Built from source (~2-3
# minutes); the compiled extension is ~10MB so it doesn't bloat the image.
RUN pip install --no-cache-dir llama-cpp-python==0.3.2

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

# GGUF model for in-process inference. 1.3GB at Q8_0 — dominates the image
# size but avoids needing an external model service at runtime.
COPY the-legacy.gguf /app/the-legacy.gguf

# Static frontend served from the same FastAPI process — no separate hosting
COPY docs/ /app/docs/

EXPOSE 8000

# HF Spaces expects the app on port 7860; allow override via PORT env.
ENV PORT=8000

CMD uvicorn src.server:app --host 0.0.0.0 --port ${PORT}
