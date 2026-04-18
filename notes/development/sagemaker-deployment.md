# SageMaker Deployment Walkthrough

End-to-end steps to deploy the finetuned model to a SageMaker real-time endpoint. Use this for the remote demo path — the endpoint is internet-accessible, so you can serve the FastAPI app from a lightweight CPU instance (or even locally) while the model runs on a GPU in AWS.

## Cost reality check

**ml.g5.xlarge costs ~$1.41/hour, billed continuously once the endpoint is up.**

| Duration | Cost |
|----------|------|
| 1 hour   | ~$1.41 |
| 24 hours | ~$34 |
| 1 week   | ~$237 |
| 1 month  | ~$1,015 |

**Remember to `--delete` when you're done.** `--status` shows an estimate of how much the current endpoint has cost so far. The create command itself prints the reminder too.

## Prerequisites

**One-time setup:**

1. **AWS account** with SageMaker and IAM access
2. **AWS CLI configured** — `aws configure` (access key, secret, default region, default output)
3. **SageMaker execution role** — if you've used SageMaker before, you probably have one. Otherwise create `AmazonSageMaker-ExecutionRole` with `AmazonSageMakerFullAccess`. Note its ARN.
4. **Python deps** — `pip install boto3 sagemaker transformers peft torch huggingface_hub accelerate`
5. **HuggingFace login with write access** — `huggingface-cli login` using a token with "Write" permission (needed to push the merged model)

## One-time: push the merged model to HF

SageMaker's TGI container pulls the model from HuggingFace. The LoRA adapter alone isn't enough — you need the fully merged model on HF Hub.

```
python scripts/merge_and_convert.py \
    --push-hf-repo malhl/the-legacy-lora-merged \
    --skip-gguf
```

This downloads the LoRA adapter, merges it into Llama 3.2 1B, and pushes the merged model to `https://huggingface.co/malhl/the-legacy-lora-merged`. `--skip-gguf` skips the Ollama conversion step since we don't need GGUF for SageMaker.

Add `--hf-private` if you want the merged repo private (SageMaker's HF pull will need a token in that case).

Takes ~3-5 minutes depending on upload bandwidth. Merged model is ~2.5GB.

## Deploy

```
python scripts/deploy_sagemaker.py --create
```

Behind the scenes:
- Uses the HuggingFace TGI 3.2.3 image for LLM inference
- Deploys to `ml.g5.xlarge` (1x A10G GPU, 24GB VRAM — 1B model uses a tiny fraction)
- Endpoint name: `the-legacy-llm`
- Config: MAX_INPUT_LENGTH=1024, MAX_TOTAL_TOKENS=2048

Takes 5-10 minutes — the container has to download the model from HF on cold start.

Pass `--role arn:aws:iam::ACCOUNT:role/ROLE` if auto-detection fails (it usually does outside of SageMaker notebook environments). Pass `--region us-west-2` to override the default region.

## Verify

```
python scripts/deploy_sagemaker.py --status
```

Wait for `Status: InService`, then:

```
python scripts/deploy_sagemaker.py --test "What is the most played deck in Legacy?"
```

Expected output: something referencing Dimir Tempo at 14.6%. If it sounds like the base model (generic, hedging), the merged model on HF may not be the right one — double-check the push step worked.

## Point the FastAPI server at it

Two options:

**Local server, remote inference (recommended for demo):**
```
export INFERENCE_BACKEND=sagemaker
export SAGEMAKER_ENDPOINT=the-legacy-llm
export AWS_REGION=us-east-1  # or wherever you deployed

uvicorn src.server:app --reload --port 8000
```

Your API (including RAG, card resolution, goldfish, budget tiers) runs locally. Only model calls go to SageMaker.

**PowerShell syntax:**
```powershell
$env:INFERENCE_BACKEND = "sagemaker"
$env:SAGEMAKER_ENDPOINT = "the-legacy-llm"
$env:AWS_REGION = "us-east-1"
uvicorn src.server:app --reload --port 8000
```

## Tear down

**Critically important** — don't forget this.

```
python scripts/deploy_sagemaker.py --delete
```

Deletes the endpoint, the endpoint config, and any associated model objects. Billing stops immediately after the endpoint deletion completes (which takes ~30 seconds).

You can verify with `--status` — it should report the endpoint doesn't exist.

## Troubleshooting

### `Could not auto-detect SageMaker execution role`
You're running outside a SageMaker notebook. Pass `--role` explicitly:
```
python scripts/deploy_sagemaker.py --create \
    --role arn:aws:iam::123456789012:role/service-role/AmazonSageMaker-ExecutionRole-20240101
```
Find the ARN in the AWS console under IAM → Roles.

### Container startup health check timeout
The TGI container needs to download ~2.5GB from HuggingFace on cold start. The script sets a 10-minute timeout, but slow regions or throttled HF downloads can push past this. If it happens, delete and retry — HF caches aggressively and the second attempt is usually faster.

### Endpoint creation fails with `ResourceLimitExceeded`
Your account doesn't have quota for `ml.g5.xlarge`. Request an increase via AWS Service Quotas. Meanwhile, you can try smaller/older instance types like `ml.g4dn.xlarge` (T4 GPU) — edit `INSTANCE_TYPE` in `deploy_sagemaker.py`. The 1B model runs fine on a T4.

### API returns 503 "SageMaker not configured"
The FastAPI server imports `boto3` lazily. Make sure `INFERENCE_BACKEND=sagemaker` is set in the server's environment and `pip install boto3` is satisfied.

### Response looks like the base model, not the finetuned one
Check that the HF repo (`malhl/the-legacy-lora-merged`) actually contains the merged weights — browse to https://huggingface.co/malhl/the-legacy-lora-merged and verify you see `model.safetensors` (~2.5GB). If the repo has only the LoRA adapter files (`adapter_model.safetensors`, ~30MB), you pushed the wrong thing. Re-run `merge_and_convert.py --push-hf-repo`.

## Alternative: serverless / scale-to-zero

If cost is the main concern, SageMaker Serverless Inference scales to zero when idle. It's slower on cold starts (10-20 seconds) but free when not in use. To try it, replace `model.deploy(...)` in the create_endpoint function with `model.deploy(serverless_inference_config=ServerlessInferenceConfig(...))`.

Not worth it for active demos (cold start ruins the first user's experience) but perfect for rare invocations.
