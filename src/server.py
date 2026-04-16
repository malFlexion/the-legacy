"""
The Legacy — FastAPI server.

Serves the finetuned Llama model via Ollama with RAG retrieval
and Scryfall card resolution. Every card name in model output is
resolved to full card data (oracle text, mana cost, legality, image).

Usage:
    uvicorn src.server:app --reload --port 8000

Requires:
    - Ollama running with the-legacy model loaded
    - data/card_index.pkl (built from Scryfall bulk data)
    - vectordb/ (built by build_vectordb.py)
"""

import os
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import httpx
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from .card_index import CardIndex

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OLLAMA_BASE = os.environ.get("OLLAMA_BASE", "http://localhost:11434")
MODEL_NAME = os.environ.get("MODEL_NAME", "the-legacy")
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load card index and vector DB once at startup."""
    global card_index, chroma_collection

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

    yield


app = FastAPI(
    title="The Legacy",
    description="AI-powered MTG Legacy deck builder",
    lifespan=lifespan,
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
# Ollama interaction
# ---------------------------------------------------------------------------


def build_messages(
    messages: list[ChatMessage], rag_context: str = ""
) -> list[dict]:
    """Build the message list for Ollama, injecting system prompt and RAG."""
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

    async def generate():
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

    return StreamingResponse(generate(), media_type="text/event-stream")


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

    # Stream mode
    if req.stream:
        return await ollama_generate(
            messages,
            stream=True,
            temperature=req.temperature,
            top_p=req.top_p,
            max_tokens=req.max_tokens,
        )

    # Non-stream: generate, resolve cards, return
    content = await ollama_generate(
        messages,
        stream=False,
        temperature=req.temperature,
        top_p=req.top_p,
        max_tokens=req.max_tokens,
    )

    cards = resolve_cards(content)

    return ChatResponse(content=content, cards=cards)


@app.get("/card/{name}")
async def get_card(name: str):
    """Look up a card by name (fuzzy matched)."""
    if card_index is None:
        raise HTTPException(status_code=503, detail="Card index not loaded")

    # Try exact match first
    card = card_index.get(name)
    if card:
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

    # Fuzzy search
    results = card_index.search(name, limit=1, legacy_only=False)
    if not results:
        raise HTTPException(status_code=404, detail=f"Card not found: {name}")

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
        "model": MODEL_NAME,
        "card_index": card_index is not None,
        "card_count": len(card_index.cards) if card_index else 0,
        "vector_db": chroma_collection is not None,
        "vector_chunks": chroma_collection.count() if chroma_collection else 0,
    }
