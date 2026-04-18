# Ollama Deployment Walkthrough

End-to-end steps to take the finetuned LoRA adapter on HuggingFace Hub and serve it locally via Ollama. The repo already wires `INFERENCE_BACKEND=ollama` in `src/server.py`, so once Ollama is serving `the-legacy`, the API just works.

## Prerequisites

**Install these first (one-time setup):**

1. **Ollama** — [ollama.com/download](https://ollama.com/download). Windows installer. After install, `ollama` should be on PATH. Test with `ollama --version`.

2. **llama.cpp** — clone anywhere:
   ```
   git clone https://github.com/ggerganov/llama.cpp
   ```
   No compile needed for conversion — we only use `convert_hf_to_gguf.py`.

3. **Python deps** for the merge script:
   ```
   pip install transformers peft torch huggingface_hub accelerate
   ```

4. **HuggingFace login** (the adapter lives at `malhl/the-legacy-lora` — may require auth):
   ```
   huggingface-cli login
   ```

## Run it

From the repo root:

```
python scripts/merge_and_convert.py --llama-cpp-path /path/to/llama.cpp
```

That does everything end-to-end:

1. Downloads the LoRA adapter from `malhl/the-legacy-lora`
2. Loads Llama 3.2 1B Instruct base from HF
3. Merges adapter weights via `peft.merge_and_unload()` → `./merged-model/`
4. Runs `convert_hf_to_gguf.py --outtype q4_k_m` → `./the-legacy.gguf`
5. Rewrites `Modelfile` to point at the new GGUF with the Llama 3.2 chat template
6. Deletes `./merged-model/` (saves ~2.5GB) unless you pass `--keep-merged`

**Runtime:** ~2 minutes on CPU (1B model is small). RAM peak ~4GB.
**Output size:** the-legacy.gguf at q4_k_m is ~800MB.

Then register with Ollama:

```
ollama create the-legacy -f Modelfile
ollama run the-legacy "What is the most played deck in Legacy right now?"
```

## Verify the model is working

Run a few eval questions against it — the Round 2 eval topics where the model should be strong:

```
ollama run the-legacy "Is Counterspell good in Legacy?"
ollama run the-legacy "What is a budget replacement for Underground Sea?"
ollama run the-legacy "Identify this deck: 4 Show and Tell, 4 Sneak Attack, 3 Emrakul, 3 Atraxa, 4 Force of Will"
```

Expected: correct card stats (UU not 1UU for Counterspell), Watery Grave as the budget sub, and Sneak and Show as the archetype.

## Point the API at it

Once `ollama serve` is running (auto-starts on Windows), the existing FastAPI server works out of the box:

```
uvicorn src.server:app --reload --port 8000
```

The server defaults to `INFERENCE_BACKEND=ollama` and `MODEL_NAME=the-legacy` — both are overridable via env vars.

## Troubleshooting

### `convert_hf_to_gguf.py not found`
The script expects llama.cpp cloned somewhere. Pass the path explicitly: `--llama-cpp-path C:/src/llama.cpp`.

### Adapter download fails
Try `huggingface-cli login` first. If the adapter is private, you need a token with read access. Or point at a local path with `--adapter-repo ./notebooks/lora-legacy/lora-adapter`.

### Ollama can't find the GGUF
The Modelfile uses `FROM ./the-legacy.gguf` (relative to Modelfile location). Run `ollama create` from the repo root so the relative path resolves.

### Model responses look garbled / no `<|eot_id|>` termination
The `PARAMETER stop "<|eot_id|>"` line in the Modelfile handles this. If you're seeing it, the Modelfile didn't apply — check with `ollama show the-legacy --modelfile` and re-run `ollama create`.

### Out of memory during merge
The script uses CPU and float16 which peaks around 4GB RAM. If that's tight, add `--quant q3_k_m` (smaller GGUF) after merging succeeds, or run the merge on a machine with more RAM and copy the merged folder back.

## Different quantizations

| Quant    | Size   | Quality | When to use |
|----------|--------|---------|-------------|
| `f16`    | ~2.5GB | Perfect | Benchmarking / research |
| `q8_0`   | ~1.3GB | Nearly perfect | Best quality for local use |
| `q5_k_m` | ~900MB | Very good | Good middle ground |
| `q4_k_m` | ~800MB | Good (default) | Recommended for everyday use |
| `q4_0`   | ~770MB | OK | Slightly faster, slightly worse |
| `q3_k_m` | ~600MB | Degraded | Only if RAM-constrained |

Pass with `--quant q5_k_m` etc.

## What to commit

- ✅ `Modelfile` — committed, references the GGUF filename
- ✅ `scripts/merge_and_convert.py` — committed
- ❌ `the-legacy.gguf` — gitignored (too large, regenerate from adapter)
- ❌ `merged-model/` — gitignored, deleted after conversion anyway

The adapter weights live on HF Hub; anyone can rebuild the GGUF locally by running the script.
