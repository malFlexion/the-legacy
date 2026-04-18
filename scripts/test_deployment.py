"""
Smoke-test Ollama and/or SageMaker deployments of The Legacy model.

Runs a few Legacy-specific prompts where we know what the correct answer
looks like (mostly drawn from the Round 2 eval set) and verifies that the
responses:
  - contain the expected content (PASS)
  - avoid known hallucinations from pre-Round-2 behavior (REJECT)
  - include bonus details that indicate the finetune really worked

This is reachability + sanity, not a full eval. For full eval numbers,
run the notebook.

Usage:
    # Check Ollama (default: http://localhost:11434, model "the-legacy")
    python scripts/test_deployment.py --ollama

    # Check SageMaker (default endpoint "the-legacy-llm")
    python scripts/test_deployment.py --sagemaker

    # Both, with full response output
    python scripts/test_deployment.py --all --verbose

    # Override defaults
    python scripts/test_deployment.py --ollama \\
        --ollama-host http://192.168.1.10:11434 \\
        --ollama-model the-legacy

Exit code: 0 if every selected backend passes all required assertions,
           1 otherwise. Suitable for CI or post-deploy verification.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


SYSTEM_PROMPT = (
    "You are The Legacy, an expert AI assistant for Magic: The Gathering "
    "Legacy format. You help players build decks, understand rules, evaluate "
    "cards, analyze the metagame, and improve their play."
)


@dataclass
class TestCase:
    """A single prompt with expectations about the response.

    - expect: phrases that MUST appear (required — failure if any missing)
    - bonus:  phrases that SHOULD appear (partial credit)
    - reject: phrases that MUST NOT appear (known hallucinations from
              pre-Round-2 behavior — failure if any present)
    """
    name: str
    prompt: str
    expect: list[str]
    bonus: list[str] = field(default_factory=list)
    reject: list[str] = field(default_factory=list)


# Chosen from the Round 2 eval topics where we have specific correct answers.
# Each test surfaces a different category of finetune gain.
TEST_CASES: list[TestCase] = [
    TestCase(
        name="meta_awareness",
        prompt="What is the most played deck in Legacy right now?",
        expect=["Dimir Tempo"],
        bonus=["14.6", "tempo", "Bowmasters", "Thoughtseize"],
        # These decks don't exist — the pre-Round-2 model hallucinated them
        reject=["Orc & Giant Stompy", "Orc Stompy"],
    ),
    TestCase(
        name="card_evaluation",
        prompt="Is Counterspell good in Legacy? What does it cost?",
        expect=["Counterspell"],
        # Correct answer references UU mana cost, not "1UU"
        bonus=["UU", "two mana", "2 mana"],
        # Pre-Round-2 model said "costs 1UU" and "counters a spell with mana value 2 or less"
        reject=[
            "1UU",
            "costs 1 U U",
            "mana value 2 or less",
            "mana value two or less",
        ],
    ),
    TestCase(
        name="budget_subs",
        prompt="What is a budget replacement for Underground Sea?",
        expect=["Underground Sea"],
        # Correct budget answer: Watery Grave (shockland), not expensive moxen
        bonus=["Watery Grave", "2 life", "Darkslick Shores", "shock"],
        # Pre-Round-2 model recommended expensive cards as "budget"
        reject=["Mox Diamond", "Mox Opal"],
    ),
    TestCase(
        name="card_stats_accuracy",
        prompt="What are Orcish Bowmasters' stats and mana cost?",
        expect=["Bowmasters"],
        # Correct: 1/1 for 1B, Flash, triggers on opponent drawing cards
        bonus=["1/1", "1B", "Flash", "opponent draws"],
        # Pre-Round-2 model said "1/1 trample for 1GG" and "triggers on spells of MV 3 or less"
        reject=[
            "trample",
            "1GG",
            "1 G G",
            "mana value 3 or less",
        ],
    ),
    TestCase(
        name="rules_knowledge",
        prompt=(
            "My opponent has Blood Moon in play. I have a Polluted Delta in "
            "hand. Can I play Polluted Delta and sacrifice it to find an Island?"
        ),
        expect=[],  # language varies; rely on bonus + reject
        bonus=["Mountain", "basic", "nonbasic", "no"],
        # Pre-Round-2 model made up a rule about exiling lands from graveyards
        reject=[
            "exile it instead",
            "exiles it",
            "exile from the graveyard",
        ],
    ),
]


# --- Terminal formatting (works without color libs) ---

def _supports_color() -> bool:
    return sys.stdout.isatty() and sys.platform != "win32" or "ANSICON" in __import__("os").environ


_GREEN = "\033[32m" if _supports_color() else ""
_RED = "\033[31m" if _supports_color() else ""
_YELLOW = "\033[33m" if _supports_color() else ""
_BOLD = "\033[1m" if _supports_color() else ""
_RESET = "\033[0m" if _supports_color() else ""


def _pass(msg: str) -> str:
    return f"{_GREEN}PASS{_RESET} {msg}"


def _fail(msg: str) -> str:
    return f"{_RED}FAIL{_RESET} {msg}"


def _warn(msg: str) -> str:
    return f"{_YELLOW}WARN{_RESET} {msg}"


# --- Test evaluation ---

@dataclass
class CaseResult:
    case: TestCase
    response: str
    latency_s: float
    missing_expect: list[str]
    present_reject: list[str]
    bonus_hits: list[str]

    @property
    def passed(self) -> bool:
        return not self.missing_expect and not self.present_reject


def evaluate_response(case: TestCase, response: str, latency_s: float) -> CaseResult:
    lower = response.lower()
    missing_expect = [p for p in case.expect if p.lower() not in lower]
    present_reject = [p for p in case.reject if p.lower() in lower]
    bonus_hits = [p for p in case.bonus if p.lower() in lower]
    return CaseResult(
        case=case,
        response=response,
        latency_s=latency_s,
        missing_expect=missing_expect,
        present_reject=present_reject,
        bonus_hits=bonus_hits,
    )


def print_case_result(result: CaseResult, verbose: bool) -> None:
    case = result.case
    header = f"  [{case.name}]  ({result.latency_s:.2f}s)"
    if result.passed:
        print(_pass(header))
    else:
        print(_fail(header))

    if result.missing_expect:
        print(f"    Missing required: {result.missing_expect}")
    if result.present_reject:
        print(f"    Hit reject pattern(s): {result.present_reject}")
    if result.bonus_hits:
        print(f"    Bonus signals ({len(result.bonus_hits)}/{len(case.bonus)}): {result.bonus_hits}")
    elif case.bonus:
        print(f"    No bonus signals ({len(case.bonus)} expected — weaker response)")

    if verbose:
        preview = result.response[:500].replace("\n", " ")
        print(f"    Response: {preview}{'...' if len(result.response) > 500 else ''}")


# --- Ollama backend ---

def ollama_list_models(host: str) -> list[str]:
    url = host.rstrip("/") + "/api/tags"
    with urllib.request.urlopen(url, timeout=5) as resp:
        data = json.loads(resp.read().decode())
    return [m.get("name", "") for m in data.get("models", [])]


def ollama_generate(host: str, model: str, prompt: str) -> str:
    url = host.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": 0.3, "top_p": 0.9, "num_predict": 512},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    return data.get("message", {}).get("content", "")


def test_ollama(host: str, model: str, verbose: bool) -> bool:
    print(f"\n{_BOLD}=== Ollama ==={_RESET}  host={host}  model={model}")

    # Reachability
    try:
        models = ollama_list_models(host)
    except urllib.error.URLError as e:
        print(_fail(f"  Cannot reach Ollama at {host}: {e.reason}"))
        print("  Is `ollama serve` running? On Windows it starts automatically after install.")
        return False

    if model not in [m.split(":")[0] for m in models]:
        print(_fail(f"  Model '{model}' not registered. Available: {models or '(none)'}"))
        print(f"  Register it with: ollama create {model} -f Modelfile")
        return False
    print(_pass(f"  Reachable, model '{model}' registered"))

    # Run test cases
    results: list[CaseResult] = []
    for case in TEST_CASES:
        t0 = time.monotonic()
        try:
            response = ollama_generate(host, model, case.prompt)
        except Exception as e:
            print(_fail(f"  [{case.name}] Request failed: {e}"))
            return False
        results.append(evaluate_response(case, response, time.monotonic() - t0))

    for r in results:
        print_case_result(r, verbose)

    passed = sum(r.passed for r in results)
    total = len(results)
    avg_latency = sum(r.latency_s for r in results) / total if results else 0
    print(f"\n  Summary: {passed}/{total} passed, avg latency {avg_latency:.2f}s")
    return passed == total


# --- SageMaker backend ---

def format_chat_prompt(messages: list[dict]) -> str:
    """Llama 3 chat template for TGI."""
    parts = []
    for msg in messages:
        parts.append(
            f"<|start_header_id|>{msg['role']}<|end_header_id|>\n\n"
            f"{msg['content']}<|eot_id|>"
        )
    parts.append("<|start_header_id|>assistant<|end_header_id|>\n\n")
    return "<|begin_of_text|>" + "".join(parts)


def test_sagemaker(endpoint: str, region: str | None, verbose: bool) -> bool:
    print(f"\n{_BOLD}=== SageMaker ==={_RESET}  endpoint={endpoint}  region={region or '(default)'}")

    try:
        import boto3
    except ImportError:
        print(_fail("  boto3 not installed. Run: pip install boto3 sagemaker"))
        return False

    sm = boto3.client("sagemaker", region_name=region) if region else boto3.client("sagemaker")
    runtime = boto3.client("sagemaker-runtime", region_name=region) if region else boto3.client("sagemaker-runtime")

    # Reachability — endpoint must exist and be InService
    try:
        resp = sm.describe_endpoint(EndpointName=endpoint)
    except sm.exceptions.ClientError as e:
        print(_fail(f"  Cannot describe endpoint '{endpoint}': {e}"))
        print(f"  Create one with: python scripts/deploy_sagemaker.py --create")
        return False

    status = resp["EndpointStatus"]
    if status != "InService":
        print(_fail(f"  Endpoint status is '{status}' (need 'InService')"))
        if resp.get("FailureReason"):
            print(f"  Failure reason: {resp['FailureReason']}")
        return False
    print(_pass(f"  Endpoint InService"))

    # Run test cases
    results: list[CaseResult] = []
    for case in TEST_CASES:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": case.prompt},
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

        t0 = time.monotonic()
        try:
            resp = runtime.invoke_endpoint(
                EndpointName=endpoint,
                ContentType="application/json",
                Body=json.dumps(payload),
            )
        except Exception as e:
            print(_fail(f"  [{case.name}] invoke_endpoint failed: {e}"))
            return False

        result_body = json.loads(resp["Body"].read().decode())
        if isinstance(result_body, list):
            result_body = result_body[0]
        response = result_body.get("generated_text", "")
        results.append(evaluate_response(case, response, time.monotonic() - t0))

    for r in results:
        print_case_result(r, verbose)

    passed = sum(r.passed for r in results)
    total = len(results)
    avg_latency = sum(r.latency_s for r in results) / total if results else 0
    print(f"\n  Summary: {passed}/{total} passed, avg latency {avg_latency:.2f}s")
    return passed == total


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="Smoke-test The Legacy model deployments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    target = parser.add_argument_group("targets")
    target.add_argument("--ollama", action="store_true", help="Test the Ollama deployment")
    target.add_argument("--sagemaker", action="store_true", help="Test the SageMaker endpoint")
    target.add_argument("--all", action="store_true", help="Test both Ollama and SageMaker")

    parser.add_argument("--ollama-host", default="http://localhost:11434")
    parser.add_argument("--ollama-model", default="the-legacy")
    parser.add_argument("--sagemaker-endpoint", default="the-legacy-llm")
    parser.add_argument("--region", default=None, help="AWS region (default: from AWS config)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show the full model response for each case")

    args = parser.parse_args()

    run_ollama = args.ollama or args.all
    run_sagemaker = args.sagemaker or args.all

    if not (run_ollama or run_sagemaker):
        parser.error("Specify at least one of --ollama, --sagemaker, or --all")

    all_passed = True

    if run_ollama:
        ok = test_ollama(args.ollama_host, args.ollama_model, args.verbose)
        all_passed = all_passed and ok

    if run_sagemaker:
        ok = test_sagemaker(args.sagemaker_endpoint, args.region, args.verbose)
        all_passed = all_passed and ok

    print()
    if all_passed:
        print(_pass(f"{_BOLD}All tests passed.{_RESET}"))
        sys.exit(0)
    else:
        print(_fail(f"{_BOLD}One or more tests failed.{_RESET}"))
        sys.exit(1)


if __name__ == "__main__":
    main()
