#!/bin/bash
# Docker entrypoint for the all-in-one Fly GPU + Ollama container.
#
# Starts Ollama in the background, waits for it to be ready, ensures the
# finetuned `the-legacy` model is registered (copying the GGUF into
# Ollama's cache on first boot — afterwards the Fly Volume at
# /root/.ollama has the cached blob, so subsequent boots skip the step),
# then execs uvicorn as PID 1.
set -e

echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to answer /api/tags (up to 60s).
echo "Waiting for Ollama to be ready..."
for i in $(seq 1 60); do
    if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama is ready."
        break
    fi
    if [ "$i" = "60" ]; then
        echo "FATAL: Ollama didn't come up in 60s. Dumping logs and exiting." >&2
        kill "$OLLAMA_PID" 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Register the model if it's not already in the Ollama cache.
# On first boot with a fresh volume this copies the 1.3GB blob from
# /app/the-legacy.gguf into /root/.ollama/models/blobs — takes ~30-60s.
# On subsequent boots the volume-mounted cache already has the blob
# and `ollama list` returns quickly, so we skip.
MODEL_NAME="${MODEL_NAME:-the-legacy}"
if ollama list 2>/dev/null | grep -q "^${MODEL_NAME}"; then
    echo "Model '${MODEL_NAME}' already registered in Ollama cache — skipping create."
else
    echo "Registering '${MODEL_NAME}' in Ollama (copying GGUF into cache, ~30-60s)..."
    cd /app && ollama create "${MODEL_NAME}" -f /app/Modelfile
    echo "Model registered."
fi

echo "Starting FastAPI server..."
exec uvicorn src.server:app --host 0.0.0.0 --port "${PORT:-8000}"
