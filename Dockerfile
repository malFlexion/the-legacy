# All-in-one Fly GPU container: Ollama + FastAPI + static frontend.
#
# At runtime the container starts `ollama serve` in the background, loads the
# finetuned `the-legacy` model into the local Ollama registry (the GGUF is
# baked into the image and copied into /root/.ollama on first boot — that
# path is mounted as a Fly Volume so subsequent boots hit the cache), then
# starts uvicorn. One container, one URL.
#
# Deploy:
#   fly volumes create ollama_data --size 10 -r iad   # one time
#   fly deploy
#
# Scale down to stop billing:
#   fly scale count 0 -a the-legacy-api
# Scale back up (takes ~60-90s first time while volume warms):
#   fly scale count 1 -a the-legacy-api

FROM python:3.11-slim

WORKDIR /app

# System deps:
#  - libgomp1: used by rapidfuzz / sentence-transformers (OpenMP)
#  - curl: fetches the Ollama install script and health-checks Ollama at boot
#  - ca-certificates: HTTPS trust store (Ollama install + pip occasionally need it)
#  - zstd: Ollama's installer uses zstd-compressed tarballs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    ca-certificates \
    zstd \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama. The install script detects linux-amd64 and drops
# /usr/bin/ollama. It also tries to set up a systemd service, which is a
# no-op in Docker — harmless.
RUN curl -fsSL https://ollama.com/install.sh | sh

# CPU-only torch so sentence-transformers embeddings don't pull the 2GB
# CUDA variant (we use Ollama for LLM inference on GPU; embeddings stay
# on CPU).
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch

RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn[standard]==0.31.0 \
    httpx==0.27.2 \
    pydantic==2.9.2 \
    rapidfuzz==3.10.0 \
    chromadb==0.5.11 \
    sentence-transformers==3.1.1

# Pre-cache the RAG embedding model (~80MB) so the FastAPI server doesn't
# download it on every cold start.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# App code + deterministic runtime assets.
COPY src/ /app/src/
COPY data/card_index.pkl /app/data/card_index.pkl
COPY vectordb/ /app/vectordb/
COPY docs/ /app/docs/

# Ollama model artifacts.
#
# The GGUF is too big for git (1.3GB vs GitHub's 100MB per-file limit),
# so we fetch it from HuggingFace Hub during build. HF's CDN is fast and
# supports resumable LFS — more reliable than GitHub Releases for large
# model files. Both local (`fly deploy`) and CI (`workflow_dispatch`)
# deploys use this same URL.
#
# Override the repo at build time if needed:
#   fly deploy --build-arg MODEL_URL=https://huggingface.co/.../resolve/main/the-legacy.gguf
ARG MODEL_URL=https://huggingface.co/malFlexion/the-legacy-gguf/resolve/main/the-legacy.gguf
ADD ${MODEL_URL} /app/the-legacy.gguf

# Modelfile lives in the repo — references ./the-legacy.gguf, so we
# cd to /app before `ollama create` in the entrypoint script.
COPY Modelfile /app/Modelfile

# Startup orchestration: boot Ollama, register model (once), exec uvicorn.
COPY scripts/docker_entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
ENV PORT=8000

CMD ["/app/entrypoint.sh"]
