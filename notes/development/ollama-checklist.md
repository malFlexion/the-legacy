# Ollama Setup Checklist

Step-by-step checklist for getting `the-legacy` running locally via Ollama. Full details and troubleshooting are in [ollama-deployment.md](ollama-deployment.md) — this is the condensed action list.

Expected total time: **~15 minutes**

## 1. One-time installs

- [X] **Ollama** — download Windows installer from [ollama.com/download](https://ollama.com/download), run it
- [ ] Verify Ollama works: open a new terminal and run
  ```
  ollama --version
  ```
- [ ] **llama.cpp** — clone it anywhere (no compile needed, just for the conversion script):
  ```
  git clone https://github.com/ggerganov/llama.cpp
  ```
  Note the path — you'll need it in step 3.
- [ ] **Python deps** — transformers stack plus `sentencepiece` (required by llama.cpp's converter for the Llama tokenizer):
  ```
  pip install transformers peft torch huggingface_hub accelerate sentencepiece
  ```
- [ ] **HuggingFace login** — `huggingface_hub` 1.x renamed the CLI to `hf`:
  ```
  hf auth login
  ```
  Read access is sufficient for downloading the adapter.

## 2. Merge + convert the model

From the repo root:

- [ ] Run the merge + GGUF pipeline (replace the path with where you cloned llama.cpp):
  ```
  python scripts/merge_and_convert.py --llama-cpp-path C:/path/to/llama.cpp
  ```
  Expected: ~2 minutes on CPU. Produces `the-legacy.gguf` (~1.3GB at q8_0) and rewrites `Modelfile`.

  **Note:** `convert_hf_to_gguf.py` only supports f32 / f16 / bf16 / q8_0 directly. For smaller quants (q4_k_m, q5_k_m) you'd need to compile llama.cpp and run its `llama-quantize` binary on the f16 output. q8_0 is near-lossless and fine for a 1B model.
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
  Expected: **3-5/5 passed**, latency ~10-15s per response on CPU.

  Some cases can fail on phrasing (e.g. the model says "UB Tempo" instead of "Dimir Tempo") without being factually wrong — use `--verbose` to see the full responses if something fails. Factual hallucinations that do exist (e.g. "Bowmasters has trample") are Round 2 limitations documented in `round1-analysis.md`, not deployment bugs.

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

Hit a problem? See the troubleshooting section of [ollama-deployment.md](ollama-deployment.md). Issues we've actually encountered:

- **`ollama` not found after install** — open a new PowerShell; the existing session has a stale PATH
- **`No module named 'sentencepiece'`** during GGUF conversion — `pip install sentencepiece`
- **`invalid choice: 'q4_k_m'`** on conversion — modern `convert_hf_to_gguf.py` only emits f16/bf16/q8_0 directly; smaller quants need a compiled `llama-quantize`. Use `--quant q8_0` or leave the default.
- **`template error: undefined variable "$last"`** on `ollama create` — old Modelfile syntax, pull latest repo and re-run (fixed in the current Modelfile)
- **Adapter repo not found on HF (404)** — weights may only exist on your SageMaker training instance or locally. Pass `--adapter-repo ./notebooks/lora-legacy/lora-adapter` to use a local path.
- **`convert_hf_to_gguf.py not found`** — the `--llama-cpp-path` value is wrong
- **Model answers like the base Llama** — the merge didn't take, re-run step 2
- **Garbled output / no termination** — Modelfile template issue, re-run `ollama create`
