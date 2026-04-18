# Ollama Setup Checklist

Step-by-step checklist for getting `the-legacy` running locally via Ollama. Full details and troubleshooting are in [ollama-deployment.md](ollama-deployment.md) — this is the condensed action list.

Expected total time: **~15 minutes**

## 1. One-time installs

- [ ] **Ollama** — download Windows installer from [ollama.com/download](https://ollama.com/download), run it
- [ ] Verify Ollama works: open a new terminal and run
  ```
  ollama --version
  ```
- [ ] **llama.cpp** — clone it anywhere (no compile needed, just for the conversion script):
  ```
  git clone https://github.com/ggerganov/llama.cpp
  ```
  Note the path — you'll need it in step 3.
- [ ] **Python deps**:
  ```
  pip install transformers peft torch huggingface_hub accelerate
  ```
- [ ] **HuggingFace login** (needed to download the LoRA adapter):
  ```
  huggingface-cli login
  ```

## 2. Merge + convert the model

From the repo root:

- [ ] Run the merge + GGUF pipeline (replace the path with where you cloned llama.cpp):
  ```
  python scripts/merge_and_convert.py --llama-cpp-path C:/path/to/llama.cpp
  ```
  Expected: ~2 minutes on CPU. Produces `the-legacy.gguf` (~800MB) and rewrites `Modelfile`.
- [ ] Confirm the file exists:
  ```
  ls the-legacy.gguf
  ```

## 3. Register with Ollama

- [ ] Create the model:
  ```
  ollama create the-legacy -f Modelfile
  ```
  Expected: prints a few hash lines ending with `success`.
- [ ] Verify it's registered:
  ```
  ollama list
  ```
  You should see `the-legacy` in the list.

## 4. Test it

- [ ] Quick manual sanity check:
  ```
  ollama run the-legacy "What is the most played deck in Legacy right now?"
  ```
  Expected: response mentions **Dimir Tempo** (and ideally 14.6%).
- [ ] Run the full smoke test:
  ```
  python scripts/test_deployment.py --ollama
  ```
  Expected: **5/5 passed**, avg latency a few seconds per response.

## 5. (Optional) Point the FastAPI server at it

- [ ] Start the server against Ollama:

  **Bash:**
  ```
  export INFERENCE_BACKEND=ollama
  export MODEL_NAME=the-legacy
  uvicorn src.server:app --reload --port 8000
  ```

  **PowerShell:**
  ```powershell
  $env:INFERENCE_BACKEND = "ollama"
  $env:MODEL_NAME = "the-legacy"
  uvicorn src.server:app --reload --port 8000
  ```

- [ ] Check health: open [http://localhost:8000/health](http://localhost:8000/health) in a browser. Should return JSON with `status: ok` and `model: the-legacy`.

## Done

The model is running locally. No ongoing cost. Responds in 1-3 seconds on most hardware.

Ollama auto-starts on login, so `ollama run the-legacy` will work after a reboot without any extra setup.

## Troubleshooting

Hit a problem? See the troubleshooting section of [ollama-deployment.md](ollama-deployment.md). Common issues:

- **`convert_hf_to_gguf.py not found`** — the `--llama-cpp-path` value is wrong
- **Model answers like the base Llama** — the merge didn't take, re-run step 2
- **Garbled output / no termination** — Modelfile template issue, re-run `ollama create`
