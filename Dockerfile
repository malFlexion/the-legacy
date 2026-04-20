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
# Source docs for RAG vector DB rebuild on first boot. The committed
# vectordb/ is skipped because it was built with a chromadb version that
# differs from the one in this image — reading it raises KeyError('_type').
# Rebuilding at startup from the source docs guarantees version match.
COPY data/comprehensive-rules.txt /app/data/comprehensive-rules.txt
COPY data/legacy-basics.md /app/data/legacy-basics.md
COPY data/deckbuilding-guide.md /app/data/deckbuilding-guide.md
COPY data/legacy-analysis.md /app/data/legacy-analysis.md
COPY data/archetype-guide.md /app/data/archetype-guide.md
COPY data/legacy-deck-history.md /app/data/legacy-deck-history.md
COPY data/mtg-slang.md /app/data/mtg-slang.md
COPY docs/ /app/docs/

# The 1.3GB GGUF is NOT baked into the image — it would push us past
# Fly's 8GB uncompressed image limit. Instead the entrypoint script
# downloads it on first boot and hands it to `ollama create`, which
# copies the blob into /root/.ollama (mounted as a Fly Volume). Subsequent
# boots find the cached model and skip the download entirely.
ENV GGUF_URL=https://huggingface.co/malFlexion/the-legacy-gguf/resolve/main/the-legacy.gguf

# Modelfile references /tmp/the-legacy.gguf at register time (see entrypoint).
COPY Modelfile /app/Modelfile

# Startup orchestration: boot Ollama, register model (once), exec uvicorn.
COPY scripts/docker_entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
ENV PORT=8000

CMD ["/app/entrypoint.sh"]
