"""
Deploy the finetuned Legacy model to a SageMaker real-time endpoint.

Prerequisites:
    1. Merge the LoRA adapter and push to HuggingFace:
       - Uncomment the merge cell in notebooks/finetune_legacy.ipynb
       - Or run: python scripts/merge_and_push.py
    2. AWS credentials configured (aws configure)
    3. SageMaker execution role with permissions

Usage:
    python scripts/deploy_sagemaker.py --create
    python scripts/deploy_sagemaker.py --delete
    python scripts/deploy_sagemaker.py --test "What is the best deck in Legacy?"
"""

import argparse
import json
import boto3
import sagemaker
from sagemaker.huggingface import HuggingFaceModel, get_huggingface_llm_image_uri


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ENDPOINT_NAME = "the-legacy-llm"
INSTANCE_TYPE = "ml.g5.xlarge"  # 1x A10G, 24GB VRAM — plenty for 1B model
HF_MODEL_ID = "malhl/the-legacy-lora-merged"  # Merged model on HF Hub

# ---------------------------------------------------------------------------
# Deploy
# ---------------------------------------------------------------------------


def create_endpoint(role: str = None):
    """Create a SageMaker real-time endpoint."""
    sess = sagemaker.Session()

    if role is None:
        role = sagemaker.get_execution_role()

    # HuggingFace TGI container for LLM inference
    image_uri = get_huggingface_llm_image_uri("huggingface", version="3.2.3")

    model = HuggingFaceModel(
        image_uri=image_uri,
        role=role,
        env={
            "HF_MODEL_ID": HF_MODEL_ID,
            "HF_TASK": "text-generation",
            "MAX_INPUT_LENGTH": "1024",
            "MAX_TOTAL_TOKENS": "2048",
            "SM_NUM_GPUS": "1",
        },
        sagemaker_session=sess,
    )

    print(f"Deploying {HF_MODEL_ID} to {ENDPOINT_NAME}...")
    print(f"Instance type: {INSTANCE_TYPE}")

    predictor = model.deploy(
        initial_instance_count=1,
        instance_type=INSTANCE_TYPE,
        endpoint_name=ENDPOINT_NAME,
        container_startup_health_check_timeout=600,
    )

    print(f"\nEndpoint created: {ENDPOINT_NAME}")
    print(f"Region: {sess.boto_region_name}")
    print("\nSet these environment variables for the server:")
    print(f"  export INFERENCE_BACKEND=sagemaker")
    print(f"  export SAGEMAKER_ENDPOINT={ENDPOINT_NAME}")
    print(f"  export AWS_REGION={sess.boto_region_name}")

    return predictor


def delete_endpoint():
    """Delete the SageMaker endpoint."""
    sess = sagemaker.Session()
    client = sess.boto_session.client("sagemaker")

    print(f"Deleting endpoint: {ENDPOINT_NAME}")

    try:
        client.delete_endpoint(EndpointName=ENDPOINT_NAME)
        print("Endpoint deleted.")
    except client.exceptions.ClientError as e:
        print(f"Error: {e}")

    # Also delete the endpoint config and model
    try:
        client.delete_endpoint_config(EndpointConfigName=ENDPOINT_NAME)
        print("Endpoint config deleted.")
    except Exception:
        pass


def test_endpoint(prompt: str):
    """Test the deployed endpoint."""
    runtime = boto3.client("sagemaker-runtime")

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

    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/json",
        Body=json.dumps(payload),
    )

    result = json.loads(response["Body"].read().decode())
    if isinstance(result, list):
        result = result[0]

    generated = result.get("generated_text", "")
    print(f"Response:\n{generated}")
    return generated


def format_chat_prompt(messages: list[dict]) -> str:
    """Format messages as a Llama 3 chat prompt string."""
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
    parser = argparse.ArgumentParser(description="Manage SageMaker endpoint")
    parser.add_argument("--create", action="store_true", help="Create endpoint")
    parser.add_argument("--delete", action="store_true", help="Delete endpoint")
    parser.add_argument("--test", type=str, help="Test with a prompt")
    parser.add_argument("--role", type=str, help="SageMaker execution role ARN")

    args = parser.parse_args()

    if args.create:
        create_endpoint(role=args.role)
    elif args.delete:
        delete_endpoint()
    elif args.test:
        test_endpoint(args.test)
    else:
        parser.print_help()
