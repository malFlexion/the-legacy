"""
The Legacy — FastAPI server.

Serves the finetuned Llama model with RAG retrieval and Scryfall card
resolution. Supports two inference backends:
  - Ollama (local): set INFERENCE_BACKEND=ollama (default)
  - SageMaker endpoint: set INFERENCE_BACKEND=sagemaker

Every card name in model output is resolved to full card data
(oracle text, mana cost, legality, image).

Usage:
    # Local with Ollama
    uvicorn src.server:app --reload --port 8000

    # With SageMaker endpoint
    INFERENCE_BACKEND=sagemaker SAGEMAKER_ENDPOINT=the-legacy-llm \
        uvicorn src.server:app --reload --port 8000

Requires:
    - data/card_index.pkl (built from Scryfall bulk data)
    - vectordb/ (built by build_vectordb.py)
"""

import os
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import httpx
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from .card_index import CardIndex
from .deck_parser import parse_decklist, import_from_url, Decklist
from .budget_engine import BudgetEngine
from .goldfish_engine import Deck, aggregate_stats, london_mulligan, sample_hands
from .turn_engine import aggregate_game_stats, simulate_game

# ---------------------------------------------------------------------------
# Logging — configured at import time so startup banners appear in Fly logs.
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("the-legacy")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

INFERENCE_BACKEND = os.environ.get("INFERENCE_BACKEND", "ollama")  # "ollama", "sagemaker", or "llamacpp"

# Ollama config
OLLAMA_BASE = os.environ.get("OLLAMA_BASE", "http://localhost:11434")
MODEL_NAME = os.environ.get("MODEL_NAME", "the-legacy")

# SageMaker config
SAGEMAKER_ENDPOINT = os.environ.get("SAGEMAKER_ENDPOINT", "the-legacy-llm")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# llama-cpp-python config — loads a GGUF file in-process (no external service).
# This is the "run everything in one Fly container" path.
LLAMACPP_MODEL_PATH = os.environ.get("LLAMACPP_MODEL_PATH", "./the-legacy.gguf")
LLAMACPP_N_THREADS = int(os.environ.get("LLAMACPP_N_THREADS", "2"))
LLAMACPP_N_CTX = int(os.environ.get("LLAMACPP_N_CTX", "2048"))

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
# VECTORDB_DIR defaults to repo-relative ./vectordb; the Fly entrypoint
# overrides to /root/.ollama/vectordb so the rebuilt DB persists on the
# mounted Fly Volume alongside the Ollama model cache.
VECTORDB_DIR = os.environ.get(
    "VECTORDB_DIR",
    os.path.join(os.path.dirname(__file__), "..", "vectordb"),
)

SYSTEM_PROMPT = (
    "You are The Legacy, an expert AI assistant for Magic: The Gathering "
    "Legacy format. You help players build decks, understand rules, evaluate "
    "cards, analyze the metagame, and improve their play. You have deep "
    "knowledge of all Legacy archetypes, card interactions, and competitive "
    "strategies."
)

# ---------------------------------------------------------------------------
# Shared state loaded at startup
# ---------------------------------------------------------------------------

card_index: CardIndex | None = None
chroma_collection = None
sagemaker_runtime = None
budget_engine: BudgetEngine | None = None
llamacpp_model = None  # populated only when INFERENCE_BACKEND == "llamacpp"


def _validate_config() -> list[str]:
    """Check required environment variables for the chosen backend.

    Returns a list of human-readable warnings. Empty list = all good.
    Does not raise — the server should start even with config issues so
    that /health can report what's wrong to the frontend.
    """
    warnings: list[str] = []

    if INFERENCE_BACKEND not in ("ollama", "sagemaker", "llamacpp"):
        warnings.append(
            f"INFERENCE_BACKEND='{INFERENCE_BACKEND}' is not recognized "
            f"(expected 'ollama', 'sagemaker', or 'llamacpp'). Defaulting to Ollama path."
        )

    if INFERENCE_BACKEND == "sagemaker":
        # boto3 reads credentials from env, shared config, or instance role.
        # We only check the obvious env-var path here; missing creds from
        # the chain will surface as a clear error on the first invoke.
        if not os.environ.get("AWS_ACCESS_KEY_ID") and not os.environ.get("AWS_PROFILE"):
            warnings.append(
                "Neither AWS_ACCESS_KEY_ID nor AWS_PROFILE is set. "
                "boto3 will try other sources (instance role, ~/.aws/credentials). "
                "If running on Fly, set AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY "
                "via `fly secrets set`."
            )
        if SAGEMAKER_ENDPOINT == "the-legacy-llm":
            log.debug("SAGEMAKER_ENDPOINT using default name 'the-legacy-llm'")
        if not AWS_REGION:
            warnings.append("AWS_REGION is empty — SageMaker calls will fail.")

    if INFERENCE_BACKEND == "ollama":
        if not OLLAMA_BASE.startswith(("http://", "https://")):
            warnings.append(
                f"OLLAMA_BASE='{OLLAMA_BASE}' must include the scheme (http:// or https://)"
            )

    if INFERENCE_BACKEND == "llamacpp":
        if not os.path.exists(LLAMACPP_MODEL_PATH):
            warnings.append(
                f"LLAMACPP_MODEL_PATH='{LLAMACPP_MODEL_PATH}' does not exist. "
                "Generate a GGUF via scripts/merge_and_convert.py and place it at "
                "this path, or set LLAMACPP_MODEL_PATH env var."
            )

    return warnings


def _log_banner(title: str) -> None:
    log.info("=" * 60)
    log.info(title)
    log.info("=" * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load card index, vector DB, and inference backend at startup.

    Emits a structured startup report so any config problem is obvious
    in the Fly logs / local console before the first request arrives.
    """
    global card_index, chroma_collection, sagemaker_runtime, budget_engine

    _log_banner("The Legacy — startup")
    log.info("INFERENCE_BACKEND = %s", INFERENCE_BACKEND)
    if INFERENCE_BACKEND == "sagemaker":
        log.info("SAGEMAKER_ENDPOINT = %s", SAGEMAKER_ENDPOINT)
        log.info("AWS_REGION        = %s", AWS_REGION)
        log.info("AWS_ACCESS_KEY_ID = %s", "set" if os.environ.get("AWS_ACCESS_KEY_ID") else "NOT SET")
    elif INFERENCE_BACKEND == "llamacpp":
        log.info("LLAMACPP_MODEL_PATH = %s", LLAMACPP_MODEL_PATH)
        log.info("LLAMACPP_N_THREADS  = %d", LLAMACPP_N_THREADS)
        log.info("LLAMACPP_N_CTX      = %d", LLAMACPP_N_CTX)
    else:
        log.info("OLLAMA_BASE = %s", OLLAMA_BASE)
        log.info("MODEL_NAME  = %s", MODEL_NAME)

    # Config validation — log but don't fail startup
    for warning in _validate_config():
        log.warning("CONFIG: %s", warning)

    # Card index
    card_index = CardIndex()
    try:
        card_index.load()
        log.info("✓ Card index loaded (%d cards)", len(card_index.cards))
    except FileNotFoundError:
        log.warning(
            "✗ card_index.pkl not found at %s — card resolution disabled. "
            "Rebuild with: python src/card_index.py",
            os.path.join(DATA_DIR, "card_index.pkl"),
        )
        card_index = None
    except Exception:
        log.exception("✗ Unexpected error loading card index — disabling")
        card_index = None

    # Budget engine (depends on card index for prices)
    if card_index is not None:
        budget_engine = BudgetEngine(card_index)
        log.info("✓ Budget engine ready")

    # Vector DB
    try:
        embed_fn = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        client = chromadb.PersistentClient(path=VECTORDB_DIR)
        chroma_collection = client.get_collection(
            name="legacy_knowledge",
            embedding_function=embed_fn,
        )
        log.info("✓ Vector DB loaded (%d chunks) — RAG enabled", chroma_collection.count())
    except Exception as e:
        log.warning("✗ Vector DB unavailable (%s: %s) — RAG disabled", type(e).__name__, e)
        chroma_collection = None

    # Inference backend setup + connectivity check
    if INFERENCE_BACKEND == "llamacpp":
        if not os.path.exists(LLAMACPP_MODEL_PATH):
            log.error(
                "✗ GGUF not found at %s — inference will return 503. "
                "Build one with scripts/merge_and_convert.py or set LLAMACPP_MODEL_PATH.",
                LLAMACPP_MODEL_PATH,
            )
        else:
            try:
                from llama_cpp import Llama
                log.info(
                    "Loading GGUF (this takes 30-60s on cold start)... path=%s, threads=%d, ctx=%d",
                    LLAMACPP_MODEL_PATH, LLAMACPP_N_THREADS, LLAMACPP_N_CTX,
                )
                llamacpp_model = Llama(
                    model_path=LLAMACPP_MODEL_PATH,
                    n_ctx=LLAMACPP_N_CTX,
                    n_threads=LLAMACPP_N_THREADS,
                    n_batch=512,
                    use_mlock=True,
                    verbose=False,
                )
                log.info("✓ llama-cpp model loaded")
            except Exception:
                log.exception("✗ Failed to load GGUF via llama-cpp-python")
                llamacpp_model = None
    elif INFERENCE_BACKEND == "sagemaker":
        try:
            import boto3
            sagemaker_runtime = boto3.client("sagemaker-runtime", region_name=AWS_REGION)
            # Active connectivity + auth check via the control plane
            sm = boto3.client("sagemaker", region_name=AWS_REGION)
            resp = sm.describe_endpoint(EndpointName=SAGEMAKER_ENDPOINT)
            status = resp["EndpointStatus"]
            if status == "InService":
                log.info("✓ SageMaker endpoint '%s' is InService", SAGEMAKER_ENDPOINT)
            else:
                log.warning(
                    "✗ SageMaker endpoint '%s' status: %s — chat requests will fail "
                    "until it's InService", SAGEMAKER_ENDPOINT, status,
                )
        except Exception as e:
            # Most common: NoCredentialsError, AccessDenied, endpoint not found,
            # region typo. Keep the message actionable.
            log.error(
                "✗ Cannot reach SageMaker (%s: %s). Check AWS creds, region, and "
                "that endpoint '%s' exists. Run: aws sagemaker describe-endpoint "
                "--endpoint-name %s --region %s",
                type(e).__name__, str(e)[:200], SAGEMAKER_ENDPOINT,
                SAGEMAKER_ENDPOINT, AWS_REGION,
            )
            sagemaker_runtime = None
    else:
        # Ollama connectivity check
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{OLLAMA_BASE}/api/tags")
            if r.status_code == 200:
                names = [m.get("name", "").split(":")[0] for m in r.json().get("models", [])]
                if MODEL_NAME in names:
                    log.info("✓ Ollama reachable at %s — model '%s' is registered", OLLAMA_BASE, MODEL_NAME)
                else:
                    log.warning(
                        "✗ Ollama reachable but model '%s' is not registered. "
                        "Available: %s. Register with: ollama create %s -f Modelfile",
                        MODEL_NAME, names or "(none)", MODEL_NAME,
                    )
            else:
                log.warning("✗ Ollama at %s returned HTTP %d", OLLAMA_BASE, r.status_code)
        except Exception as e:
            log.error(
                "✗ Cannot reach Ollama at %s (%s: %s). Is `ollama serve` running?",
                OLLAMA_BASE, type(e).__name__, str(e)[:200],
            )

    _log_banner("Startup complete")
    yield
    log.info("Shutting down")


app = FastAPI(
    title="The Legacy",
    description="AI-powered MTG Legacy deck builder",
    lifespan=lifespan,
)

# Allow CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float = 0.3
    top_p: float = 0.9
    max_tokens: int = 1024


class CardData(BaseModel):
    name: str
    mana_cost: str = ""
    cmc: float = 0
    type_line: str = ""
    oracle_text: str = ""
    colors: list[str] = []
    power: str | None = None
    toughness: str | None = None
    legacy_legal: bool = True
    image_url: str | None = None
    scryfall_uri: str = ""
    prices: dict = {}


class ChatResponse(BaseModel):
    content: str
    cards: list[CardData] = []


class CardSearchRequest(BaseModel):
    query: str
    limit: int = 5
    legacy_only: bool = True


# ---------------------------------------------------------------------------
# RAG retrieval
# ---------------------------------------------------------------------------


def retrieve_context(query: str, n_results: int = 5) -> str:
    """Query the vector DB for relevant context chunks."""
    if chroma_collection is None:
        return ""

    results = chroma_collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    if not results["documents"] or not results["documents"][0]:
        return ""

    chunks = results["documents"][0]
    sources = results["metadatas"][0] if results["metadatas"] else [{}] * len(chunks)

    context_parts = []
    for chunk, meta in zip(chunks, sources):
        source = meta.get("source", "unknown")
        section = meta.get("title", meta.get("section", ""))
        header = f"[{source}: {section}]" if section else f"[{source}]"
        context_parts.append(f"{header}\n{chunk}")

    return "\n\n---\n\n".join(context_parts)


# ---------------------------------------------------------------------------
# Card resolution
# ---------------------------------------------------------------------------


def resolve_cards(text: str) -> list[CardData]:
    """Find and resolve all card names in model output."""
    if card_index is None:
        return []

    raw_cards = card_index.resolve(text, legacy_only=False)

    resolved = []
    for card in raw_cards:
        name = card["name"]
        resolved.append(
            CardData(
                name=name,
                mana_cost=card.get("mana_cost", ""),
                cmc=card.get("cmc", 0),
                type_line=card.get("type_line", ""),
                oracle_text=card.get("oracle_text", ""),
                colors=card.get("colors", []),
                power=card.get("power"),
                toughness=card.get("toughness"),
                legacy_legal=card_index.is_legacy_legal(name),
                image_url=card_index.scryfall_image_url(name),
                scryfall_uri=card.get("scryfall_uri", ""),
                prices=card.get("prices", {}),
            )
        )

    return resolved


# ---------------------------------------------------------------------------
# Message formatting
# ---------------------------------------------------------------------------


def build_messages(
    messages: list[ChatMessage], rag_context: str = ""
) -> list[dict]:
    """Build the message list, injecting system prompt and RAG context."""
    system_content = SYSTEM_PROMPT
    if rag_context:
        system_content += (
            "\n\nUse the following reference material to inform your answer. "
            "Only use information from these sources if relevant — do not "
            "force-fit unrelated context.\n\n" + rag_context
        )

    result = [{"role": "system", "content": system_content}]
    for msg in messages:
        result.append({"role": msg.role, "content": msg.content})

    return result


def format_llama_prompt(messages: list[dict]) -> str:
    """Format messages as a Llama 3 chat prompt string (for SageMaker TGI)."""
    parts = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        parts.append(
            f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>"
        )
    parts.append("<|start_header_id|>assistant<|end_header_id|>\n\n")
    return "<|begin_of_text|>" + "".join(parts)


# ---------------------------------------------------------------------------
# Inference backends
# ---------------------------------------------------------------------------


async def generate(
    messages: list[dict],
    stream: bool = False,
    temperature: float = 0.3,
    top_p: float = 0.9,
    max_tokens: int = 1024,
) -> str | StreamingResponse:
    """Route to the configured inference backend."""
    if INFERENCE_BACKEND == "sagemaker":
        return await sagemaker_generate(
            messages, temperature=temperature, top_p=top_p, max_tokens=max_tokens
        )
    if INFERENCE_BACKEND == "llamacpp":
        return await llamacpp_generate(
            messages, temperature=temperature, top_p=top_p, max_tokens=max_tokens
        )
    return await ollama_generate(
        messages, stream=stream, temperature=temperature,
        top_p=top_p, max_tokens=max_tokens,
    )


async def llamacpp_generate(
    messages: list[dict],
    temperature: float = 0.3,
    top_p: float = 0.9,
    max_tokens: int = 512,
) -> str:
    """In-process inference via llama-cpp-python on the Fly container itself.

    No external service — the GGUF is loaded once at startup and each request
    calls create_chat_completion. Because llama-cpp-python is synchronous,
    we offload to a worker thread so we don't block the event loop.
    """
    import asyncio

    if llamacpp_model is None:
        log.error("llamacpp_generate called but model is not loaded — check startup logs")
        raise HTTPException(
            status_code=503,
            detail="llama-cpp model not loaded — check server startup logs",
        )

    try:
        resp = await asyncio.to_thread(
            llamacpp_model.create_chat_completion,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
    except Exception as e:
        log.error(
            "llama-cpp inference failed: %s: %s",
            type(e).__name__, str(e)[:300],
        )
        raise HTTPException(
            status_code=502,
            detail=f"llama-cpp inference failed ({type(e).__name__}): {str(e)[:200]}",
        )

    return resp["choices"][0]["message"]["content"]


async def sagemaker_generate(
    messages: list[dict],
    temperature: float = 0.3,
    top_p: float = 0.9,
    max_tokens: int = 1024,
) -> str:
    """Call SageMaker endpoint for inference."""
    if sagemaker_runtime is None:
        log.error("sagemaker_generate called but sagemaker_runtime is None — startup failed to initialize it")
        raise HTTPException(
            status_code=503,
            detail="SageMaker client not initialized — check server startup logs for config errors",
        )

    prompt = format_llama_prompt(messages)

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "do_sample": True,
        },
    }

    try:
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT,
            ContentType="application/json",
            Body=json.dumps(payload),
        )
    except Exception as e:
        # Common error classes: EndpointNotInServiceException, ValidationError,
        # AccessDeniedException, ThrottlingException, ModelError. Include
        # the error class + message so Fly logs tell us exactly what broke.
        log.error(
            "SageMaker invoke failed: %s: %s (endpoint=%s, region=%s)",
            type(e).__name__, str(e)[:300], SAGEMAKER_ENDPOINT, AWS_REGION,
        )
        raise HTTPException(
            status_code=502,
            detail=f"SageMaker invoke failed ({type(e).__name__}): {str(e)[:200]}",
        )

    result = json.loads(response["Body"].read().decode())
    if isinstance(result, list):
        result = result[0]

    generated = result.get("generated_text", "")

    # TGI returns the full prompt + response — strip the prompt
    if generated.startswith(prompt):
        generated = generated[len(prompt):]

    # Strip any trailing special tokens
    for token in ["<|eot_id|>", "<|end_of_text|>"]:
        generated = generated.split(token)[0]

    return generated.strip()


async def ollama_generate(
    messages: list[dict],
    stream: bool = False,
    temperature: float = 0.3,
    top_p: float = 0.9,
    max_tokens: int = 1024,
) -> str | StreamingResponse:
    """Call Ollama chat API."""
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": stream,
        "options": {
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_tokens,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            if stream:
                return await _stream_response(client, payload)

            resp = await client.post(
                f"{OLLAMA_BASE}/api/chat",
                json=payload,
            )
            if resp.status_code != 200:
                log.error(
                    "Ollama returned HTTP %d for model '%s': %s",
                    resp.status_code, MODEL_NAME, resp.text[:300],
                )
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Ollama error: {resp.text}",
                )
            data = resp.json()
            return data.get("message", {}).get("content", "")
    except httpx.ConnectError as e:
        log.error("Cannot connect to Ollama at %s: %s", OLLAMA_BASE, e)
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to Ollama at {OLLAMA_BASE} — is `ollama serve` running?",
        )
    except httpx.TimeoutException:
        log.error("Ollama request timed out after 120s (model=%s)", MODEL_NAME)
        raise HTTPException(status_code=504, detail="Ollama request timed out")


async def _stream_response(client: httpx.AsyncClient, payload: dict):
    """Stream Ollama response as SSE."""

    async def event_generator():
        async with client.stream(
            "POST", f"{OLLAMA_BASE}/api/chat", json=payload
        ) as resp:
            async for line in resp.aiter_lines():
                if line:
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield f"data: {json.dumps({'content': content})}\n\n"
                    if chunk.get("done"):
                        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Main chat endpoint with RAG retrieval and card resolution."""
    # Get the latest user message for RAG query
    user_msg = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_msg = msg.content
            break

    # Retrieve context
    rag_context = retrieve_context(user_msg)

    # Build messages with system prompt + RAG
    messages = build_messages(req.messages, rag_context)

    # Stream mode (Ollama only)
    if req.stream and INFERENCE_BACKEND == "ollama":
        return await generate(
            messages,
            stream=True,
            temperature=req.temperature,
            top_p=req.top_p,
            max_tokens=req.max_tokens,
        )

    # Non-stream: generate, resolve cards, return
    content = await generate(
        messages,
        stream=False,
        temperature=req.temperature,
        top_p=req.top_p,
        max_tokens=req.max_tokens,
    )

    cards = resolve_cards(content)

    return ChatResponse(content=content, cards=cards)


@app.post("/build-deck", response_model=ChatResponse)
async def build_deck(req: ChatRequest):
    """Generate a 75-card Legacy decklist from a description."""
    deck_prompt = (
        "Build a complete Legacy-legal decklist with exactly 60 cards in the "
        "main deck and 15 cards in the sideboard. List every card with its "
        "quantity. Explain your key card choices and the deck's game plan."
    )

    user_msg = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_msg = msg.content
            break

    rag_context = retrieve_context(user_msg)
    enriched = list(req.messages) + [
        ChatMessage(role="system", content=deck_prompt)
    ]
    messages = build_messages(enriched, rag_context)

    content = await generate(
        messages, temperature=0.2, top_p=0.9, max_tokens=req.max_tokens,
    )
    return ChatResponse(content=content, cards=resolve_cards(content))


@app.post("/analyze-deck", response_model=ChatResponse)
async def analyze_deck(req: ChatRequest):
    """Import and analyze a decklist."""
    analysis_prompt = (
        "Analyze this decklist. Identify the archetype, explain its game plan, "
        "assess the mana base, evaluate sideboard choices, identify strengths "
        "and weaknesses in the current metagame, and suggest improvements."
    )

    user_msg = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_msg = msg.content
            break

    rag_context = retrieve_context(user_msg)
    enriched = list(req.messages) + [
        ChatMessage(role="system", content=analysis_prompt)
    ]
    messages = build_messages(enriched, rag_context)

    content = await generate(
        messages, temperature=0.2, top_p=0.9, max_tokens=req.max_tokens,
    )
    return ChatResponse(content=content, cards=resolve_cards(content))


@app.post("/evaluate-board", response_model=ChatResponse)
async def evaluate_board(req: ChatRequest):
    """Analyze a board state and recommend plays."""
    board_prompt = (
        "Analyze this board state. Identify the correct play, explain threat "
        "assessment, spell sequencing, and resource management. Consider what "
        "the opponent might have and how to play around it."
    )

    user_msg = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_msg = msg.content
            break

    rag_context = retrieve_context(user_msg)
    enriched = list(req.messages) + [
        ChatMessage(role="system", content=board_prompt)
    ]
    messages = build_messages(enriched, rag_context)

    content = await generate(
        messages, temperature=0.4, top_p=0.9, max_tokens=req.max_tokens,
    )
    return ChatResponse(content=content, cards=resolve_cards(content))


@app.post("/goldfish", response_model=ChatResponse)
async def goldfish(req: ChatRequest):
    """Run goldfish hands — draw and evaluate opening hands."""
    goldfish_prompt = (
        "Simulate drawing an opening hand of 7 cards from this decklist. "
        "Show the hand, evaluate whether to keep or mulligan, and explain "
        "the ideal first few turns of play. Consider mana development, "
        "threat deployment, and interaction timing."
    )

    user_msg = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_msg = msg.content
            break

    rag_context = retrieve_context(user_msg)
    enriched = list(req.messages) + [
        ChatMessage(role="system", content=goldfish_prompt)
    ]
    messages = build_messages(enriched, rag_context)

    content = await generate(
        messages, temperature=0.5, top_p=0.9, max_tokens=req.max_tokens,
    )
    return ChatResponse(content=content, cards=resolve_cards(content))


class GoldfishDrawRequest(BaseModel):
    decklist: dict[str, int]  # card_name -> count
    keep_count: int = 7  # London Mulligan: 7 = no mull, 6 = mull to 6, etc.
    seed: int | None = None


class GoldfishHandResponse(BaseModel):
    cards: list[CardData]
    land_count: int
    spell_count: int
    mana_curve: dict[int, int]
    colors_by_turn: dict[int, list[str]]


@app.post("/goldfish/draw", response_model=GoldfishHandResponse)
async def goldfish_draw(req: GoldfishDrawRequest):
    """Deterministic opening hand draw with London Mulligan support.

    Returns the drawn cards (with full Scryfall data), land/spell counts,
    mana curve, and which colors are available on turns 1-4.
    """
    if card_index is None:
        raise HTTPException(status_code=503, detail="Card index not loaded")

    try:
        deck = Deck.from_decklist(req.decklist, card_index)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        hand = london_mulligan(deck, keep_count=req.keep_count, seed=req.seed)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Resolve full card data for each drawn card
    card_data_list: list[CardData] = []
    for card in hand.cards:
        data = card_index.cards.get(card.name) if card_index else None
        if data:
            card_data_list.append(CardData(
                name=data.get("name", card.name),
                mana_cost=data.get("mana_cost", ""),
                cmc=data.get("cmc", 0) or 0,
                type_line=data.get("type_line", ""),
                oracle_text=data.get("oracle_text", ""),
                colors=data.get("colors") or [],
                power=data.get("power"),
                toughness=data.get("toughness"),
                legacy_legal=(data.get("legalities", {}).get("legacy") in ("legal", "restricted")),
                image_url=(data.get("image_uris") or {}).get("normal"),
                scryfall_uri=data.get("scryfall_uri", ""),
                prices=data.get("prices") or {},
            ))
        else:
            card_data_list.append(CardData(name=card.name))

    colors_by_turn = hand.colors_available_by_turn(max_turn=4)

    return GoldfishHandResponse(
        cards=card_data_list,
        land_count=hand.land_count,
        spell_count=hand.spell_count,
        mana_curve=dict(hand.mana_curve),
        colors_by_turn={t: sorted(colors) for t, colors in colors_by_turn.items()},
    )


class GoldfishStatsRequest(BaseModel):
    decklist: dict[str, int]
    n_samples: int = 10_000
    mulligan_to: int = 7
    seed: int | None = None


class GoldfishStatsResponse(BaseModel):
    n_samples: int
    avg_land_count: float
    land_count_distribution: dict[int, int]
    mana_curve_avg: dict[int, float]
    color_by_turn: dict[int, dict[str, float]]
    keepable_rate: float


@app.post("/goldfish/stats", response_model=GoldfishStatsResponse)
async def goldfish_stats(req: GoldfishStatsRequest):
    """Run N goldfish samples and return aggregate statistics.

    Stats:
      - land_count_distribution: histogram of land count in opening hands
      - avg_land_count: mean lands in a 7-card hand
      - mana_curve_avg: avg # of cards at each CMC in an opening hand
      - color_by_turn: P(color X available by turn Y) for each WUBRG and turns 1-4
      - keepable_rate: P(2 <= lands <= 5) — rough heuristic for "keepable"
    """
    if card_index is None:
        raise HTTPException(status_code=503, detail="Card index not loaded")
    if req.n_samples < 1 or req.n_samples > 100_000:
        raise HTTPException(
            status_code=400,
            detail="n_samples must be between 1 and 100000",
        )

    try:
        deck = Deck.from_decklist(req.decklist, card_index)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    hands = sample_hands(
        deck,
        n=req.n_samples,
        mulligan_to=req.mulligan_to,
        seed=req.seed,
    )
    stats = aggregate_stats(hands)

    return GoldfishStatsResponse(
        n_samples=stats.n_samples,
        avg_land_count=round(stats.avg_land_count, 3),
        land_count_distribution=stats.land_count_distribution,
        mana_curve_avg={k: round(v, 3) for k, v in stats.mana_curve_avg.items()},
        color_by_turn={
            t: {c: round(p, 4) for c, p in colors.items()}
            for t, colors in stats.color_by_turn.items()
        },
        keepable_rate=round(stats.keepable_rate(), 3),
    )


class GoldfishSimulateRequest(BaseModel):
    decklist: dict[str, int]
    turns: int = 6  # how many turns to play out
    seed: int | None = None


class GoldfishSimulateResponse(BaseModel):
    turns_played: int
    life_final: int
    turns: list[dict]  # per-turn snapshots
    assembled_combos: dict[str, int]
    threats_deployed: dict[str, int]


@app.post("/goldfish/simulate", response_model=GoldfishSimulateResponse)
async def goldfish_simulate(req: GoldfishSimulateRequest):
    """Play out a single goldfish game turn-by-turn.

    Returns a per-turn log (lands played, spells cast, mana used vs. available,
    combos assembled) plus aggregate end-of-game info (final life, threat
    deployment turns). See notes on what the turn engine does and doesn't
    model in src/turn_engine.py.
    """
    if card_index is None:
        raise HTTPException(status_code=503, detail="Card index not loaded")
    if req.turns < 1 or req.turns > 15:
        raise HTTPException(status_code=400, detail="turns must be between 1 and 15")

    try:
        deck = Deck.from_decklist(req.decklist, card_index)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    game = simulate_game(deck, turns=req.turns, seed=req.seed)
    summary = game.to_summary()

    return GoldfishSimulateResponse(
        turns_played=summary["turns_played"],
        life_final=summary["life_final"],
        turns=summary["turns"],
        assembled_combos=summary["assembled_combos"],
        threats_deployed=summary["threats_deployed"],
    )


class GoldfishSimulateManyRequest(BaseModel):
    decklist: dict[str, int]
    n_games: int = 1000
    turns: int = 6
    seed: int | None = None


class GoldfishGameStatsResponse(BaseModel):
    n_games: int
    avg_life_final: float
    avg_mana_efficiency: float
    combo_assembly: dict[str, dict]
    avg_turn_first_cast: dict[str, float]
    cast_rate: dict[str, float]


@app.post("/goldfish/simulate-many", response_model=GoldfishGameStatsResponse)
async def goldfish_simulate_many(req: GoldfishSimulateManyRequest):
    """Run N goldfish games and return aggregate stats:
      - avg_mana_efficiency: fraction of available mana actually spent each turn
      - combo_assembly: rate and average turn for each known combo
      - avg_turn_first_cast / cast_rate: for each card, when/how often it's cast

    Useful for comparing two deck variants, measuring consistency, or picking
    a good mulligan floor.
    """
    if card_index is None:
        raise HTTPException(status_code=503, detail="Card index not loaded")
    if req.n_games < 1 or req.n_games > 10_000:
        raise HTTPException(status_code=400, detail="n_games must be between 1 and 10000")
    if req.turns < 1 or req.turns > 15:
        raise HTTPException(status_code=400, detail="turns must be between 1 and 15")

    try:
        deck = Deck.from_decklist(req.decklist, card_index)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    import random as _random
    rng = _random.Random(req.seed)
    results = []
    for _ in range(req.n_games):
        results.append(simulate_game(deck, turns=req.turns, seed=rng.randint(0, 2**31 - 1)))
    stats = aggregate_game_stats(results)
    summary = stats.to_summary()

    return GoldfishGameStatsResponse(
        n_games=summary["n_games"],
        avg_life_final=summary["avg_life_final"],
        avg_mana_efficiency=summary["avg_mana_efficiency"],
        combo_assembly=summary["combo_assembly"],
        avg_turn_first_cast=summary["avg_turn_first_cast"],
        cast_rate=summary["cast_rate"],
    )


@app.post("/budget-sub", response_model=ChatResponse)
async def budget_sub(req: ChatRequest):
    """Suggest budget substitutions for expensive cards."""
    budget_prompt = (
        "Suggest budget-friendly replacements for the specified cards. For "
        "each substitution, explain what the budget card does similarly, what "
        "you lose compared to the original, and approximate price savings. "
        "Be honest about trade-offs."
    )

    user_msg = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_msg = msg.content
            break

    rag_context = retrieve_context(user_msg)
    enriched = list(req.messages) + [
        ChatMessage(role="system", content=budget_prompt)
    ]
    messages = build_messages(enriched, rag_context)

    content = await generate(
        messages, temperature=0.3, top_p=0.9, max_tokens=req.max_tokens,
    )
    return ChatResponse(content=content, cards=resolve_cards(content))


class SubstitutionRequest(BaseModel):
    card: str


class SubstitutionEntry(BaseModel):
    replacement: str
    tradeoffs: list[str]
    power_loss: int
    notes: str
    original_price_usd: float | None
    replacement_price_usd: float | None
    savings_usd: float | None


class SubstitutionResponse(BaseModel):
    card: str
    price_usd: float | None
    irreplaceable: bool
    substitutions: list[SubstitutionEntry]


@app.post("/budget-sub/lookup", response_model=SubstitutionResponse)
async def budget_sub_lookup(req: SubstitutionRequest):
    """Deterministic budget substitution lookup (no LLM).

    Returns curated substitutions with real prices and honest trade-offs.
    For the conversational version with LLM narration, use POST /budget-sub.
    """
    if budget_engine is None:
        raise HTTPException(status_code=503, detail="Budget engine unavailable (card index not loaded)")

    price = budget_engine.get_price(req.card)
    subs = budget_engine.get_substitutions(req.card)

    entries = []
    for sub in subs:
        repl_price = budget_engine.get_price(sub.replacement)
        savings = (price - repl_price) if (price is not None and repl_price is not None) else None
        entries.append(SubstitutionEntry(
            replacement=sub.replacement,
            tradeoffs=sub.tradeoffs,
            power_loss=sub.power_loss,
            notes=sub.notes,
            original_price_usd=price,
            replacement_price_usd=repl_price,
            savings_usd=savings,
        ))

    return SubstitutionResponse(
        card=req.card,
        price_usd=price,
        irreplaceable=budget_engine.is_irreplaceable(req.card),
        substitutions=entries,
    )


class BudgetTiersRequest(BaseModel):
    decklist: dict[str, int]  # card_name -> count


class TierSummary(BaseModel):
    decklist: dict[str, int]
    estimated_price_usd: float
    substitutions_applied: list[list[str]]  # list of [original, replacement] pairs
    irreplaceable: list[str]


class BudgetTiersResponse(BaseModel):
    full: TierSummary
    mid: TierSummary
    budget: TierSummary


@app.post("/budget-tiers", response_model=BudgetTiersResponse)
async def budget_tiers(req: BudgetTiersRequest):
    """Generate full/mid/budget tiers of a decklist.

    - full: original list
    - mid: Reserved-List-and-above cards swapped for shocks/fast lands
    - budget: every card above $30 swapped for its best budget alternative

    Each tier reports its estimated paper price, which substitutions were
    applied, and which cards are irreplaceable (you'll need to buy them
    or play a different deck).
    """
    if budget_engine is None:
        raise HTTPException(status_code=503, detail="Budget engine unavailable (card index not loaded)")

    tiers = budget_engine.generate_tiers(req.decklist)

    def summarize(tier):
        return TierSummary(
            decklist=tier.decklist,
            estimated_price_usd=round(tier.estimated_price_usd, 2),
            substitutions_applied=[list(s) for s in tier.substitutions_applied],
            irreplaceable=tier.irreplaceable,
        )

    return BudgetTiersResponse(
        full=summarize(tiers["full"]),
        mid=summarize(tiers["mid"]),
        budget=summarize(tiers["budget"]),
    )


@app.post("/evaluate-card", response_model=ChatResponse)
async def evaluate_card(req: ChatRequest):
    """Evaluate a card's Legacy playability."""
    eval_prompt = (
        "Evaluate this card for Legacy playability. Cover: mana efficiency, "
        "what decks would play it, how it compares to existing options in "
        "the format, relevant interactions, and an overall verdict on whether "
        "it is Legacy-playable."
    )

    user_msg = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_msg = msg.content
            break

    # Enrich with card data if available
    card_context = ""
    if card_index:
        results = card_index.search(user_msg, limit=1, legacy_only=False)
        if results:
            card = card_index.get(results[0][0])
            if card:
                card_context = (
                    f"\nCard data: {card['name']} {card.get('mana_cost', '')} "
                    f"— {card.get('type_line', '')} — {card.get('oracle_text', '')}"
                )

    rag_context = retrieve_context(user_msg) + card_context
    enriched = list(req.messages) + [
        ChatMessage(role="system", content=eval_prompt)
    ]
    messages = build_messages(enriched, rag_context)

    content = await generate(
        messages, temperature=0.3, top_p=0.9, max_tokens=req.max_tokens,
    )
    return ChatResponse(content=content, cards=resolve_cards(content))


class ImportRequest(BaseModel):
    text: str | None = None
    url: str | None = None


@app.post("/import-deck")
async def import_deck(req: ImportRequest):
    """Import a decklist from plain text, Moxfield URL, or MTGGoldfish URL."""
    if req.url:
        try:
            deck = await import_from_url(req.url)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif req.text:
        deck = parse_decklist(req.text)
    else:
        raise HTTPException(
            status_code=400, detail="Provide either 'text' or 'url'"
        )

    if deck.main_count == 0:
        raise HTTPException(
            status_code=400, detail="No cards found in decklist"
        )

    # Resolve card data for each entry
    resolved_main = []
    resolved_side = []

    for entry in deck.main:
        card_data = None
        if card_index:
            card_data = card_index.get(entry.name)
            if not card_data:
                results = card_index.search(entry.name, limit=1, legacy_only=False)
                if results:
                    card_data = card_index.get(results[0][0])

        resolved_main.append({
            "quantity": entry.quantity,
            "name": card_data["name"] if card_data else entry.name,
            "card": CardData(
                name=card_data["name"],
                mana_cost=card_data.get("mana_cost", ""),
                cmc=card_data.get("cmc", 0),
                type_line=card_data.get("type_line", ""),
                oracle_text=card_data.get("oracle_text", ""),
                colors=card_data.get("colors", []),
                power=card_data.get("power"),
                toughness=card_data.get("toughness"),
                legacy_legal=card_index.is_legacy_legal(card_data["name"]),
                image_url=card_index.scryfall_image_url(card_data["name"]),
                scryfall_uri=card_data.get("scryfall_uri", ""),
                prices=card_data.get("prices", {}),
            ) if card_data and card_index else None,
        })

    for entry in deck.sideboard:
        card_data = None
        if card_index:
            card_data = card_index.get(entry.name)
            if not card_data:
                results = card_index.search(entry.name, limit=1, legacy_only=False)
                if results:
                    card_data = card_index.get(results[0][0])

        resolved_side.append({
            "quantity": entry.quantity,
            "name": card_data["name"] if card_data else entry.name,
            "card": CardData(
                name=card_data["name"],
                mana_cost=card_data.get("mana_cost", ""),
                cmc=card_data.get("cmc", 0),
                type_line=card_data.get("type_line", ""),
                oracle_text=card_data.get("oracle_text", ""),
                colors=card_data.get("colors", []),
                power=card_data.get("power"),
                toughness=card_data.get("toughness"),
                legacy_legal=card_index.is_legacy_legal(card_data["name"]),
                image_url=card_index.scryfall_image_url(card_data["name"]),
                scryfall_uri=card_data.get("scryfall_uri", ""),
                prices=card_data.get("prices", {}),
            ) if card_data and card_index else None,
        })

    return {
        "main": resolved_main,
        "sideboard": resolved_side,
        "main_count": deck.main_count,
        "side_count": deck.side_count,
    }


@app.get("/card/{name}")
async def get_card(name: str):
    """Look up a card by name (fuzzy matched)."""
    if card_index is None:
        raise HTTPException(status_code=503, detail="Card index not loaded")

    # Try exact match first
    card = card_index.get(name)
    if not card:
        # Fuzzy search
        results = card_index.search(name, limit=1, legacy_only=False)
        if not results:
            raise HTTPException(
                status_code=404, detail=f"Card not found: {name}"
            )
        matched_name, score = results[0]
        card = card_index.get(matched_name)

    return CardData(
        name=card["name"],
        mana_cost=card.get("mana_cost", ""),
        cmc=card.get("cmc", 0),
        type_line=card.get("type_line", ""),
        oracle_text=card.get("oracle_text", ""),
        colors=card.get("colors", []),
        power=card.get("power"),
        toughness=card.get("toughness"),
        legacy_legal=card_index.is_legacy_legal(card["name"]),
        image_url=card_index.scryfall_image_url(card["name"]),
        scryfall_uri=card.get("scryfall_uri", ""),
        prices=card.get("prices", {}),
    )


@app.get("/card/{name}/search")
async def search_cards(name: str, limit: int = 5, legacy_only: bool = True):
    """Fuzzy search for cards by name."""
    if card_index is None:
        raise HTTPException(status_code=503, detail="Card index not loaded")

    results = card_index.search(name, limit=limit, legacy_only=legacy_only)
    return [{"name": n, "score": s} for n, s in results]


@app.get("/health")
async def health():
    """Health check.

    Also reports the status of the LLM backend (Ollama model presence or
    SageMaker endpoint state) so the frontend can distinguish "proxy is up
    but the model isn't" from "everything is good."
    """
    llm = {"reachable": False, "detail": "unknown"}

    try:
        if INFERENCE_BACKEND == "llamacpp":
            llm = {
                "reachable": llamacpp_model is not None,
                "detail": "loaded" if llamacpp_model else "GGUF not loaded — check startup logs",
            }
        elif INFERENCE_BACKEND == "sagemaker":
            # Free control-plane call to describe_endpoint — reports InService,
            # OutOfService, Updating, Creating, etc.
            import boto3
            sm = boto3.client("sagemaker", region_name=AWS_REGION)
            resp = sm.describe_endpoint(EndpointName=SAGEMAKER_ENDPOINT)
            llm = {
                "reachable": resp["EndpointStatus"] == "InService",
                "detail": resp["EndpointStatus"],
            }
        else:
            # Ollama — GET /api/tags and check our model is registered
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{OLLAMA_BASE}/api/tags")
            if r.status_code == 200:
                names = [m.get("name", "").split(":")[0] for m in r.json().get("models", [])]
                llm = {
                    "reachable": MODEL_NAME in names,
                    "detail": f"registered ({len(names)} models)" if MODEL_NAME in names else "model not registered",
                }
            else:
                llm = {"reachable": False, "detail": f"ollama responded {r.status_code}"}
    except Exception as e:
        llm = {"reachable": False, "detail": str(e)[:120]}

    if INFERENCE_BACKEND == "ollama":
        model_label = MODEL_NAME
    elif INFERENCE_BACKEND == "sagemaker":
        model_label = SAGEMAKER_ENDPOINT
    elif INFERENCE_BACKEND == "llamacpp":
        model_label = os.path.basename(LLAMACPP_MODEL_PATH)
    else:
        model_label = INFERENCE_BACKEND

    return {
        "status": "ok" if llm["reachable"] else "degraded",
        "backend": INFERENCE_BACKEND,
        "model": model_label,
        "llm": llm,
        "card_index": card_index is not None,
        "card_count": len(card_index.cards) if card_index else 0,
        "vector_db": chroma_collection is not None,
        "vector_chunks": chroma_collection.count() if chroma_collection else 0,
    }


# ---------------------------------------------------------------------------
# Static frontend (mount LAST so API routes above take precedence)
# ---------------------------------------------------------------------------

from fastapi.staticfiles import StaticFiles

_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
if os.path.isdir(_DOCS_DIR):
    # html=True serves index.html on GET / and 404s fall back to it too
    app.mount("/", StaticFiles(directory=_DOCS_DIR, html=True), name="frontend")
