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

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

INFERENCE_BACKEND = os.environ.get("INFERENCE_BACKEND", "ollama")  # "ollama" or "sagemaker"

# Ollama config
OLLAMA_BASE = os.environ.get("OLLAMA_BASE", "http://localhost:11434")
MODEL_NAME = os.environ.get("MODEL_NAME", "the-legacy")

# SageMaker config
SAGEMAKER_ENDPOINT = os.environ.get("SAGEMAKER_ENDPOINT", "the-legacy-llm")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
VECTORDB_DIR = os.path.join(os.path.dirname(__file__), "..", "vectordb")

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load card index, vector DB, and inference backend at startup."""
    global card_index, chroma_collection, sagemaker_runtime, budget_engine

    # Card index
    card_index = CardIndex()
    try:
        card_index.load()
    except FileNotFoundError:
        print(
            "WARNING: card_index.pkl not found. "
            "Card resolution disabled. Run: python src/card_index.py"
        )
        card_index = None

    # Budget engine (depends on card index for prices)
    if card_index is not None:
        budget_engine = BudgetEngine(card_index)

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
        print(f"Loaded vector DB: {chroma_collection.count()} chunks")
    except Exception as e:
        print(f"WARNING: Vector DB not available ({e}). RAG disabled.")
        chroma_collection = None

    # SageMaker client
    if INFERENCE_BACKEND == "sagemaker":
        import boto3
        sagemaker_runtime = boto3.client(
            "sagemaker-runtime", region_name=AWS_REGION
        )
        print(f"Using SageMaker endpoint: {SAGEMAKER_ENDPOINT} ({AWS_REGION})")
    else:
        print(f"Using Ollama: {OLLAMA_BASE} (model: {MODEL_NAME})")

    yield


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
    return await ollama_generate(
        messages, stream=stream, temperature=temperature,
        top_p=top_p, max_tokens=max_tokens,
    )


async def sagemaker_generate(
    messages: list[dict],
    temperature: float = 0.3,
    top_p: float = 0.9,
    max_tokens: int = 1024,
) -> str:
    """Call SageMaker endpoint for inference."""
    if sagemaker_runtime is None:
        raise HTTPException(status_code=503, detail="SageMaker not configured")

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

    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=SAGEMAKER_ENDPOINT,
        ContentType="application/json",
        Body=json.dumps(payload),
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

    async with httpx.AsyncClient(timeout=120.0) as client:
        if stream:
            return await _stream_response(client, payload)

        resp = await client.post(
            f"{OLLAMA_BASE}/api/chat",
            json=payload,
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Ollama error: {resp.text}",
            )
        data = resp.json()
        return data.get("message", {}).get("content", "")


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
    """Health check."""
    return {
        "status": "ok",
        "backend": INFERENCE_BACKEND,
        "model": MODEL_NAME if INFERENCE_BACKEND == "ollama" else SAGEMAKER_ENDPOINT,
        "card_index": card_index is not None,
        "card_count": len(card_index.cards) if card_index else 0,
        "vector_db": chroma_collection is not None,
        "vector_chunks": chroma_collection.count() if chroma_collection else 0,
    }
