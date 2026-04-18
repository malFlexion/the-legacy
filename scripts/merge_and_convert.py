"""
Merge LoRA adapter into base model, then optionally convert to GGUF for Ollama
or push to HuggingFace for SageMaker.

Two deployment targets share the merge step, so this script handles both:

  Ollama (local):
    python scripts/merge_and_convert.py --llama-cpp-path /path/to/llama.cpp

  SageMaker (remote):
    python scripts/merge_and_convert.py --push-hf-repo malhl/the-legacy-lora-merged --skip-gguf

  Both at once:
    python scripts/merge_and_convert.py --llama-cpp-path /path/to/llama.cpp \\
        --push-hf-repo malhl/the-legacy-lora-merged

Pipeline steps (each can be skipped with a flag):
  1. Download LoRA adapter from HuggingFace Hub (or use a local path)
  2. Load Llama 3.2 1B Instruct base model
  3. Merge adapter weights into the base via peft.merge_and_unload()
  4. Save merged model as HF format (safetensors)
  5. (optional) Push merged model to HuggingFace Hub
  6. (optional) Convert to GGUF using llama.cpp's convert_hf_to_gguf.py
  7. (optional) Rewrite the repo Modelfile to point at the new .gguf file

Prerequisites:
  - pip install transformers peft torch huggingface_hub accelerate
  - HF login: `huggingface-cli login` (or --hf-token)
  For Ollama path:
  - Ollama installed (https://ollama.com)
  - llama.cpp cloned somewhere locally — pass its path via --llama-cpp-path
  For SageMaker path:
  - HF token with write access (for pushing merged model)

This script runs on CPU. Merging a 1B model takes ~30s and ~4GB of RAM.
GGUF at q4_k_m is about 800MB; the full HF merged model is ~2.5GB.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_BASE_MODEL = "meta-llama/Llama-3.2-1B-Instruct"
DEFAULT_ADAPTER_REPO = "malhl/the-legacy-lora"
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MERGED_DIR = REPO_ROOT / "merged-model"
DEFAULT_GGUF_OUT = REPO_ROOT / "the-legacy.gguf"
MODELFILE_PATH = REPO_ROOT / "Modelfile"


# Llama 3.2 Instruct chat template, as Ollama Go-template syntax.
# Mirrors the tokenizer's chat_template.jinja but rewritten for Ollama.
LLAMA32_TEMPLATE = """{{- if or .System .Tools }}<|start_header_id|>system<|end_header_id|>

{{ if .System }}{{ .System }}
{{- end }}
{{- if .Tools }}You have access to the following tools:
{{ range .Tools }}{{ . }}
{{ end }}
{{- end }}<|eot_id|>
{{- end }}
{{- range .Messages }}
{{- if eq .Role "user" }}<|start_header_id|>user<|end_header_id|>

{{ .Content }}<|eot_id|>
{{- else if eq .Role "assistant" }}<|start_header_id|>assistant<|end_header_id|>

{{ .Content }}{{ if not $last }}<|eot_id|>{{ end }}
{{- end }}
{{- end }}
{{- if not $last }}<|start_header_id|>assistant<|end_header_id|>

{{ end }}"""


SYSTEM_PROMPT = (
    "You are The Legacy, an expert AI assistant for Magic: The Gathering "
    "Legacy format. You help players build decks, understand rules, evaluate "
    "cards, analyze the metagame, and improve their play. You have deep "
    "knowledge of all Legacy archetypes, card interactions, and competitive "
    "strategies."
)


def merge_adapter(
    base_model_id: str,
    adapter_source: str,
    output_dir: Path,
    hf_token: str | None,
) -> None:
    """Load base + adapter, merge, save to output_dir as HF format."""
    print(f"\n=== Step 1: Merge LoRA adapter into base ===")
    print(f"Base model:  {base_model_id}")
    print(f"Adapter:     {adapter_source}")
    print(f"Output:      {output_dir}")

    # Imports are deferred so `--help` works without torch installed
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    if hf_token:
        from huggingface_hub import login
        login(token=hf_token)

    print(f"Loading base model...")
    base = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        torch_dtype=torch.float16,
        device_map="cpu",  # merge works fine on CPU for 1B
        low_cpu_mem_usage=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model_id)

    print(f"Loading adapter and merging...")
    model = PeftModel.from_pretrained(base, adapter_source)
    merged = model.merge_and_unload()

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Saving merged model to {output_dir}...")
    merged.save_pretrained(output_dir, safe_serialization=True)
    tokenizer.save_pretrained(output_dir)
    print(f"Merged model saved. Size on disk:")
    size_mb = sum(p.stat().st_size for p in output_dir.rglob("*")) / (1024 * 1024)
    print(f"  {size_mb:.1f} MB")


def push_merged_to_hf(
    merged_dir: Path,
    repo_id: str,
    private: bool,
    hf_token: str | None,
) -> None:
    """Push the merged HF model to HuggingFace Hub."""
    print(f"\n=== Step 2a: Push merged model to HuggingFace ===")
    print(f"Repo: {repo_id} (private={private})")

    from huggingface_hub import HfApi, login
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if hf_token:
        login(token=hf_token)

    # Use the Transformers push_to_hub method — handles model card generation
    # and LFS tracking for large safetensors automatically.
    model = AutoModelForCausalLM.from_pretrained(merged_dir)
    tokenizer = AutoTokenizer.from_pretrained(merged_dir)

    print(f"Uploading model...")
    model.push_to_hub(repo_id, private=private, commit_message="Merged LoRA model")
    print(f"Uploading tokenizer...")
    tokenizer.push_to_hub(repo_id, private=private, commit_message="Merged LoRA tokenizer")

    print(f"Pushed to https://huggingface.co/{repo_id}")


def convert_to_gguf(
    merged_dir: Path,
    gguf_out: Path,
    llama_cpp_path: Path,
    quant: str,
) -> None:
    """Run llama.cpp's convert_hf_to_gguf.py to produce a GGUF file."""
    print(f"\n=== Step 2: Convert HF model to GGUF ===")
    script = llama_cpp_path / "convert_hf_to_gguf.py"
    if not script.exists():
        raise FileNotFoundError(
            f"convert_hf_to_gguf.py not found at {script}. "
            "Pass --llama-cpp-path pointing to your local llama.cpp clone."
        )

    cmd = [
        sys.executable,
        str(script),
        str(merged_dir),
        "--outtype",
        quant,
        "--outfile",
        str(gguf_out),
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print(f"GGUF written to {gguf_out} ({gguf_out.stat().st_size / (1024 * 1024):.1f} MB)")


def write_modelfile(gguf_path: Path) -> None:
    """Write a Modelfile that points at the GGUF and uses Llama 3.2's template."""
    print(f"\n=== Step 3: Write Modelfile ===")
    # Ollama Modelfile: FROM path is relative to the Modelfile directory by default
    # when loaded via `ollama create -f`. Use a relative path so the file stays portable.
    relative_gguf = os.path.relpath(gguf_path, REPO_ROOT)
    content = f"""FROM ./{relative_gguf}

TEMPLATE \"\"\"{LLAMA32_TEMPLATE}\"\"\"

PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_predict 1024
PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_of_text|>"

SYSTEM \"\"\"{SYSTEM_PROMPT}\"\"\"
"""
    MODELFILE_PATH.write_text(content, encoding="utf-8")
    print(f"Modelfile written at {MODELFILE_PATH}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--llama-cpp-path",
        type=Path,
        help="Path to your local llama.cpp clone (required unless --skip-gguf)",
    )
    parser.add_argument(
        "--base-model",
        default=DEFAULT_BASE_MODEL,
        help=f"Base model ID (default: {DEFAULT_BASE_MODEL})",
    )
    parser.add_argument(
        "--adapter-repo",
        default=DEFAULT_ADAPTER_REPO,
        help=f"HF repo or local path for the LoRA adapter (default: {DEFAULT_ADAPTER_REPO})",
    )
    parser.add_argument(
        "--merged-dir",
        type=Path,
        default=DEFAULT_MERGED_DIR,
        help="Where to save the merged HF model (default: ./merged-model)",
    )
    parser.add_argument(
        "--gguf-out",
        type=Path,
        default=DEFAULT_GGUF_OUT,
        help="Output path for the GGUF file (default: ./the-legacy.gguf)",
    )
    parser.add_argument(
        "--quant",
        default="q4_k_m",
        choices=["f16", "q8_0", "q5_k_m", "q4_k_m", "q4_0", "q3_k_m"],
        help="GGUF quantization level (default: q4_k_m — good quality/size tradeoff)",
    )
    parser.add_argument(
        "--hf-token",
        default=os.environ.get("HF_TOKEN"),
        help="HuggingFace token (also reads from HF_TOKEN env var)",
    )
    parser.add_argument(
        "--push-hf-repo",
        default=None,
        help="If set, push the merged HF model to this repo (e.g. malhl/the-legacy-lora-merged)",
    )
    parser.add_argument(
        "--hf-private",
        action="store_true",
        help="When pushing to HF, create the repo as private (default: public)",
    )
    parser.add_argument(
        "--skip-merge",
        action="store_true",
        help="Skip the merge step and use an existing merged-dir (useful for re-running conversion)",
    )
    parser.add_argument(
        "--skip-gguf",
        action="store_true",
        help="Skip the GGUF conversion step (use with --push-hf-repo for SageMaker deployment only)",
    )
    parser.add_argument(
        "--skip-modelfile",
        action="store_true",
        help="Skip writing the Modelfile",
    )
    parser.add_argument(
        "--keep-merged",
        action="store_true",
        help="Keep the merged HF model after conversion (default: delete to save disk)",
    )
    args = parser.parse_args()

    if not args.skip_gguf and args.llama_cpp_path is None:
        parser.error("--llama-cpp-path is required unless --skip-gguf is set")

    # Step 1: merge (or skip if reusing existing merged-dir)
    if not args.skip_merge:
        merge_adapter(
            base_model_id=args.base_model,
            adapter_source=args.adapter_repo,
            output_dir=args.merged_dir,
            hf_token=args.hf_token,
        )
    else:
        if not args.merged_dir.exists():
            sys.exit(f"--skip-merge set but {args.merged_dir} does not exist")
        print(f"Skipping merge; using existing {args.merged_dir}")

    # Step 2a: optionally push merged model to HF (for SageMaker)
    if args.push_hf_repo:
        push_merged_to_hf(
            merged_dir=args.merged_dir,
            repo_id=args.push_hf_repo,
            private=args.hf_private,
            hf_token=args.hf_token,
        )

    # Step 2b: GGUF conversion (for Ollama)
    if not args.skip_gguf:
        convert_to_gguf(
            merged_dir=args.merged_dir,
            gguf_out=args.gguf_out,
            llama_cpp_path=args.llama_cpp_path,
            quant=args.quant,
        )

        if not args.skip_modelfile:
            write_modelfile(gguf_path=args.gguf_out)

    # Cleanup
    if not args.keep_merged and args.merged_dir.exists():
        print(f"\nCleaning up {args.merged_dir} (use --keep-merged to preserve)")
        shutil.rmtree(args.merged_dir)

    print("\n=== Done ===")
    if args.push_hf_repo:
        print(f"Merged model pushed: https://huggingface.co/{args.push_hf_repo}")
        print(f"  Deploy to SageMaker: python scripts/deploy_sagemaker.py --create")
    if not args.skip_gguf:
        print(f"GGUF written to: {args.gguf_out}")
        print(f"  Register with Ollama: ollama create the-legacy -f {MODELFILE_PATH.name}")
        print(f"  Test: ollama run the-legacy \"What's the best deck in Legacy?\"")


if __name__ == "__main__":
    main()
