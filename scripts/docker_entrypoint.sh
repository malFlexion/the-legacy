#!/bin/bash
# Docker entrypoint for the all-in-one Fly + Ollama container.
#
# Flow:
#  1. Start `ollama serve` in the background.
#  2. Wait for the Ollama API to respond.
#  3. If the-legacy model isn't already registered (fresh volume), download
#     the GGUF from HF to /tmp, register it with `ollama create` (which
#     copies the blob into /root/.ollama — mounted as a Fly Volume so it
#     persists across restarts), then delete the temp GGUF.
#  4. Exec uvicorn as PID 1.
set -e

echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

echo "Waiting for Ollama to be ready..."
for i in $(seq 1 60); do
    if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama is ready."
        break
    fi
    if [ "$i" = "60" ]; then
        echo "FATAL: Ollama didn't come up in 60s." >&2
        kill "$OLLAMA_PID" 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

MODEL_NAME="${MODEL_NAME:-the-legacy}"
GGUF_URL="${GGUF_URL:-https://huggingface.co/malFlexion/the-legacy-gguf/resolve/main/the-legacy.gguf}"
GGUF_TMP="/tmp/the-legacy.gguf"

if ollama list 2>/dev/null | grep -q "^${MODEL_NAME}"; then
    echo "Model '${MODEL_NAME}' already in Ollama cache (volume hit) — skipping download + register."
else
    echo "Model '${MODEL_NAME}' not in cache. Downloading GGUF from HuggingFace (~1.3GB, 1-2 min)..."
    curl -fL --retry 3 -o "${GGUF_TMP}" "${GGUF_URL}"
    echo "Download complete. Registering with Ollama..."

    # Rewrite Modelfile so FROM points at the downloaded temp file
    # (the original Modelfile uses `FROM ./the-legacy.gguf` which assumed
    # the GGUF was alongside it — no longer true since we moved the
    # download to runtime).
    sed "s|FROM ./the-legacy.gguf|FROM ${GGUF_TMP}|" /app/Modelfile > /tmp/Modelfile
    ollama create "${MODEL_NAME}" -f /tmp/Modelfile
    echo "Model registered. Cleaning up temp GGUF (ollama has copied the blob into /root/.ollama)."
    rm -f "${GGUF_TMP}" /tmp/Modelfile
fi

# --- RAG vector DB ---
# The committed vectordb/ was built with a different chromadb version and
# raises KeyError('_type') when read. Rebuild in the container so the
# chromadb version that wrote it matches the version that reads it.
# Persisted to /root/.ollama/vectordb alongside the model — survives
# restarts thanks to the Fly Volume mount.
VECTORDB_PATH="/root/.ollama/vectordb"
export VECTORDB_DIR="${VECTORDB_PATH}"

if [ -f "${VECTORDB_PATH}/chroma.sqlite3" ]; then
    echo "Vector DB already built at ${VECTORDB_PATH} — skipping rebuild."
else
    echo "Building RAG vector DB from source docs (~30-60s)..."
    # build_vectordb.py reads DB_DIR from its module-level constant; override
    # via env and a quick Python invocation rather than editing the file.
    python -c "
import os, src.build_vectordb as bv
bv.DB_DIR = '${VECTORDB_PATH}'
bv.build_database()
"
    echo "Vector DB built at ${VECTORDB_PATH}."
fi

echo "Starting FastAPI server..."
exec uvicorn src.server:app --host 0.0.0.0 --port "${PORT:-8000}"
