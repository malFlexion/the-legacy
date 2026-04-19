"""
Deploy the finetuned Legacy model to a SageMaker real-time endpoint.

Prerequisites:
    1. Merge the LoRA adapter and push to HuggingFace:
       python scripts/merge_and_convert.py \\
           --push-hf-repo malFlexion/the-legacy-lora-merged --skip-gguf
    2. AWS credentials configured: `aws configure`
    3. SageMaker execution role with these permissions:
       - AmazonSageMakerFullAccess
       - Access to pull from HuggingFace (public repo — no extra perms)

Usage:
    python scripts/deploy_sagemaker.py --create
    python scripts/deploy_sagemaker.py --status
    python scripts/deploy_sagemaker.py --test "What is the best deck in Legacy?"
    python scripts/deploy_sagemaker.py --delete

    # Custom role / region:
    python scripts/deploy_sagemaker.py --create --role arn:aws:iam::... --region us-west-2

Cost: ml.g5.xlarge runs about $1.41/hour. A deployed endpoint bills
continuously until deleted — don't forget to run --delete when done.
"""

import argparse
import json
import os
import sys

# boto3 is imported lazily inside each command so --help works without it installed.


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ENDPOINT_NAME = "the-legacy-llm"
INSTANCE_TYPE = "ml.g5.xlarge"  # 1x A10G, 24GB VRAM — plenty for 1B model
DEFAULT_HF_MODEL_ID = "malFlexion/the-legacy-lora-merged"  # override with --hf-model-id or HF_MODEL_ID env var
INSTANCE_HOURLY_COST_USD = 1.41  # ml.g5.xlarge on-demand, us-east-1


# ---------------------------------------------------------------------------
# Deploy
# ---------------------------------------------------------------------------


def create_endpoint(role: str | None = None, region: str | None = None, hf_model_id: str | None = None):
    """Create a SageMaker real-time endpoint."""
    import boto3
    import sagemaker
    from sagemaker.huggingface import HuggingFaceModel, get_huggingface_llm_image_uri

    hf_model_id = hf_model_id or os.environ.get("HF_MODEL_ID") or DEFAULT_HF_MODEL_ID

    boto_sess = boto3.Session(region_name=region) if region else boto3.Session()
    sess = sagemaker.Session(boto_session=boto_sess)

    if role is None:
        try:
            role = sagemaker.get_execution_role()
        except Exception as e:
            sys.exit(
                f"Could not auto-detect SageMaker execution role ({e}). "
                "Pass one explicitly: --role arn:aws:iam::ACCOUNT:role/ROLE_NAME"
            )

    print("About to deploy:")
    print(f"  Model:         {hf_model_id}")
    print(f"  Endpoint name: {ENDPOINT_NAME}")
    print(f"  Instance:      {INSTANCE_TYPE} (~${INSTANCE_HOURLY_COST_USD:.2f}/hr)")
    print(f"  Region:        {sess.boto_region_name}")
    print(f"  Role:          {role}")
    print()
    print(f"REMINDER: This endpoint bills continuously once deployed.")
    print(f"  24h = ~${INSTANCE_HOURLY_COST_USD * 24:.2f}")
    print(f"  Run `python scripts/deploy_sagemaker.py --delete` when you're done.")
    print()

    # HuggingFace TGI container for LLM inference
    image_uri = get_huggingface_llm_image_uri("huggingface", version="3.2.3")

    model = HuggingFaceModel(
        image_uri=image_uri,
        role=role,
        env={
            "HF_MODEL_ID": hf_model_id,
            "HF_TASK": "text-generation",
            "MAX_INPUT_LENGTH": "1024",
            "MAX_TOTAL_TOKENS": "2048",
            "SM_NUM_GPUS": "1",
        },
        sagemaker_session=sess,
    )

    print(f"Deploying (this takes 5-10 minutes)...")
    model.deploy(
        initial_instance_count=1,
        instance_type=INSTANCE_TYPE,
        endpoint_name=ENDPOINT_NAME,
        container_startup_health_check_timeout=600,
    )

    print(f"\nEndpoint created: {ENDPOINT_NAME}")
    print()
    print("Set these environment variables for the FastAPI server:")
    print(f"  export INFERENCE_BACKEND=sagemaker")
    print(f"  export SAGEMAKER_ENDPOINT={ENDPOINT_NAME}")
    print(f"  export AWS_REGION={sess.boto_region_name}")


def delete_endpoint(region: str | None = None):
    """Delete the SageMaker endpoint and its config."""
    import boto3
    client = boto3.client("sagemaker", region_name=region) if region else boto3.client("sagemaker")

    print(f"Deleting endpoint: {ENDPOINT_NAME}")
    deleted_something = False

    try:
        client.delete_endpoint(EndpointName=ENDPOINT_NAME)
        print(f"  Endpoint deleted.")
        deleted_something = True
    except client.exceptions.ClientError as e:
        if "Could not find endpoint" in str(e):
            print(f"  Endpoint {ENDPOINT_NAME} not found (already deleted?)")
        else:
            print(f"  Error deleting endpoint: {e}")

    try:
        client.delete_endpoint_config(EndpointConfigName=ENDPOINT_NAME)
        print(f"  Endpoint config deleted.")
        deleted_something = True
    except client.exceptions.ClientError:
        pass  # may not exist

    # Model object — SageMaker creates one automatically with a timestamp in the
    # name, so we list and delete any that match.
    try:
        resp = client.list_models(NameContains="huggingface-pytorch-tgi")
        for m in resp.get("Models", []):
            client.delete_model(ModelName=m["ModelName"])
            print(f"  Model deleted: {m['ModelName']}")
            deleted_something = True
    except Exception as e:
        print(f"  Warning: could not list/delete model objects: {e}")

    if deleted_something:
        print("\nAll SageMaker resources cleaned up. Billing has stopped.")


def status(region: str | None = None):
    """Show endpoint status and metadata."""
    import boto3
    client = boto3.client("sagemaker", region_name=region) if region else boto3.client("sagemaker")

    try:
        resp = client.describe_endpoint(EndpointName=ENDPOINT_NAME)
    except client.exceptions.ClientError as e:
        if "Could not find endpoint" in str(e):
            print(f"Endpoint {ENDPOINT_NAME} does not exist.")
            print(f"Create one with: python scripts/deploy_sagemaker.py --create")
            return
        raise

    print(f"Endpoint:         {ENDPOINT_NAME}")
    print(f"Status:           {resp['EndpointStatus']}")
    print(f"Created:          {resp['CreationTime']}")
    print(f"Last modified:    {resp['LastModifiedTime']}")
    if resp.get("FailureReason"):
        print(f"Failure reason:   {resp['FailureReason']}")

    # Cost estimate — rough: hours since creation * hourly cost
    from datetime import datetime, timezone
    runtime_hours = (datetime.now(timezone.utc) - resp["CreationTime"]).total_seconds() / 3600
    cost_est = runtime_hours * INSTANCE_HOURLY_COST_USD
    print(f"Runtime so far:   ~{runtime_hours:.1f} hours")
    print(f"Approx cost:      ~${cost_est:.2f} (at ${INSTANCE_HOURLY_COST_USD}/hr for {INSTANCE_TYPE})")


def test_endpoint(prompt: str, region: str | None = None):
    """Send a prompt to the deployed endpoint and print the response."""
    import boto3
    runtime = boto3.client("sagemaker-runtime", region_name=region) if region else boto3.client("sagemaker-runtime")

    messages = [
        {
            "role": "system",
            "content": (
                "You are The Legacy, an expert AI assistant for "
                "Magic: The Gathering Legacy format."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    payload = {
        "inputs": format_chat_prompt(messages),
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.3,
            "top_p": 0.9,
            "do_sample": True,
        },
    }

    print(f"Sending: {prompt}\n")

    try:
        response = runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType="application/json",
            Body=json.dumps(payload),
        )
    except runtime.exceptions.ValidationError as e:
        sys.exit(f"Endpoint validation error: {e}")

    result = json.loads(response["Body"].read().decode())
    if isinstance(result, list):
        result = result[0]

    generated = result.get("generated_text", "")
    print(f"Response:\n{generated}")
    return generated


def format_chat_prompt(messages: list[dict]) -> str:
    """Format messages as a Llama 3 chat prompt string for TGI."""
    parts = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        parts.append(f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>")
    parts.append("<|start_header_id|>assistant<|end_header_id|>\n\n")
    return "<|begin_of_text|>" + "".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Manage the SageMaker endpoint for The Legacy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--create", action="store_true", help="Create endpoint (~$1.41/hr)")
    action.add_argument("--delete", action="store_true", help="Delete endpoint (stops billing)")
    action.add_argument("--status", action="store_true", help="Show endpoint status and cost estimate")
    action.add_argument("--test", type=str, metavar="PROMPT", help="Test with a prompt")

    parser.add_argument("--role", type=str, help="SageMaker execution role ARN (auto-detected if omitted)")
    parser.add_argument("--region", type=str, help="AWS region (default: from AWS config)")
    parser.add_argument(
        "--hf-model-id",
        type=str,
        help=f"HuggingFace merged model repo ID (default: {DEFAULT_HF_MODEL_ID}; env: HF_MODEL_ID)",
    )

    args = parser.parse_args()

    if args.create:
        create_endpoint(role=args.role, region=args.region, hf_model_id=args.hf_model_id)
    elif args.delete:
        delete_endpoint(region=args.region)
    elif args.status:
        status(region=args.region)
    elif args.test:
        test_endpoint(args.test, region=args.region)
