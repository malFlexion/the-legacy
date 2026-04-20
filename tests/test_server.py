"""Tests for src/server.py — the FastAPI API surface.

Strategy:
- Module-scoped TestClient that runs the real lifespan (loads card_index
  and the vector DB from disk — they exist locally and in CI artifacts).
- INFERENCE_BACKEND forced to "ollama" so SageMaker setup is skipped.
  The Ollama connectivity probe during lifespan will fail, log, and
  continue — that's the designed graceful-degrade path.
- LLM-backed endpoints (/chat, /build-deck, /analyze-deck, etc.) are
  tested by monkey-patching `src.server.generate` to return a canned
  response. That exercises the endpoint plumbing (request shape, RAG
  retrieval, card resolution, response model) without needing a real
  backend.
- Deterministic endpoints (goldfish, budget, card lookup, import-deck)
  hit the real engine logic end-to-end.
"""

import os

import pytest

# Skip the whole module if FastAPI isn't installed in this Python env
# (e.g. running tests from system Python without the server deps).
pytest.importorskip("fastapi", reason="fastapi not installed — skipping server tests")
pytest.importorskip("chromadb", reason="chromadb not installed — skipping server tests")

from fastapi.testclient import TestClient  # noqa: E402


# Force Ollama backend so the lifespan skips boto3/SageMaker setup.
# Must be set BEFORE importing src.server so module-level config
# captures it.
os.environ["INFERENCE_BACKEND"] = "ollama"


@pytest.fixture(scope="module")
def client():
    from src.server import app

    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

def test_health_returns_expected_shape(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    # Required fields regardless of backend state
    for field in ("status", "backend", "model", "llm", "card_index", "card_count",
                   "vector_db", "vector_chunks"):
        assert field in body, f"Missing {field} in /health response"
    assert body["llm"].keys() >= {"reachable", "detail"}


def test_health_card_index_loaded(client):
    """card_index.pkl is committed and should load; card_count > 0."""
    body = client.get("/health").json()
    assert body["card_index"] is True
    assert body["card_count"] > 10_000


def test_health_reports_llm_state(client):
    """Whether Ollama is running locally or not, /health should report a
    consistent llm.reachable boolean and an explanatory detail string."""
    body = client.get("/health").json()
    assert isinstance(body["llm"]["reachable"], bool)
    assert isinstance(body["llm"]["detail"], str) and body["llm"]["detail"]
    # status mirrors llm.reachable
    if body["llm"]["reachable"]:
        assert body["status"] == "ok"
    else:
        assert body["status"] == "degraded"


# ---------------------------------------------------------------------------
# Card lookup
# ---------------------------------------------------------------------------

def test_card_lookup_exact(client):
    r = client.get("/card/Brainstorm")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Brainstorm"
    assert body["mana_cost"] == "{U}"
    assert body["type_line"].startswith("Instant")


def test_card_lookup_fuzzy(client):
    # Typo should still resolve via fuzzy match
    r = client.get("/card/Brainstrm")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Brainstorm"


def test_card_lookup_garbage_input_does_not_crash(client):
    """The endpoint fuzzy-matches with a similarity threshold. Very weird
    input may match a low-scoring candidate (200) or fall off the threshold
    (404) — either is fine. We just assert no 500 crash."""
    r = client.get("/card/Xyzzy Zzzblorb Qquux Grblgr")
    assert r.status_code in (200, 404)


def test_card_search_returns_ranked(client):
    r = client.get("/card/Force/search?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) > 0
    assert len(body) <= 5
    # Every entry has a name and score
    for entry in body:
        assert "name" in entry and "score" in entry


# ---------------------------------------------------------------------------
# Budget endpoints (deterministic, no LLM)
# ---------------------------------------------------------------------------

def test_budget_sub_lookup_known_card(client):
    r = client.post("/budget-sub/lookup", json={"card": "Underground Sea"})
    assert r.status_code == 200
    body = r.json()
    assert body["card"] == "Underground Sea"
    assert body["irreplaceable"] is False
    assert len(body["substitutions"]) >= 1
    # First substitution should be Watery Grave per our curated list
    assert body["substitutions"][0]["replacement"] == "Watery Grave"
    assert body["substitutions"][0]["tradeoffs"]  # non-empty


def test_budget_sub_lookup_unknown_card(client):
    r = client.post("/budget-sub/lookup", json={"card": "No Such Card"})
    assert r.status_code == 200
    body = r.json()
    assert body["substitutions"] == []


def test_budget_sub_lookup_irreplaceable(client):
    r = client.post("/budget-sub/lookup", json={"card": "Lion's Eye Diamond"})
    assert r.status_code == 200
    body = r.json()
    assert body["irreplaceable"] is True


def test_budget_tiers_basic(client):
    decklist = {
        "Underground Sea": 4,
        "Brainstorm": 4,
        "Ponder": 4,
        "Island": 10,
    }
    r = client.post("/budget-tiers", json={"decklist": decklist})
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"full", "mid", "budget"}
    # Budget should be cheaper than full
    assert body["budget"]["estimated_price_usd"] <= body["full"]["estimated_price_usd"]
    # Mid should have subbed out the Reserved List card
    assert ("Underground Sea" in [pair[0] for pair in body["mid"]["substitutions_applied"]])


# ---------------------------------------------------------------------------
# Goldfish endpoints (deterministic)
# ---------------------------------------------------------------------------

DIMIR_SMOKE = {
    "Brainstorm": 4, "Ponder": 4, "Force of Will": 4, "Daze": 4,
    "Thoughtseize": 4, "Orcish Bowmasters": 4, "Murktide Regent": 4,
    "Underground Sea": 4, "Polluted Delta": 4, "Misty Rainforest": 4,
    "Wasteland": 4, "Island": 8, "Swamp": 8,
}


def test_goldfish_draw_returns_seven_cards(client):
    r = client.post("/goldfish/draw", json={"decklist": DIMIR_SMOKE, "keep_count": 7, "seed": 42})
    assert r.status_code == 200
    body = r.json()
    assert len(body["cards"]) == 7
    assert body["land_count"] + body["spell_count"] == 7


def test_goldfish_draw_mulligan_to_5(client):
    r = client.post("/goldfish/draw", json={"decklist": DIMIR_SMOKE, "keep_count": 5, "seed": 42})
    assert r.status_code == 200
    assert len(r.json()["cards"]) == 5


def test_goldfish_draw_is_reproducible(client):
    """Same seed → same hand."""
    req = {"decklist": DIMIR_SMOKE, "keep_count": 7, "seed": 99}
    a = client.post("/goldfish/draw", json=req).json()
    b = client.post("/goldfish/draw", json=req).json()
    assert [c["name"] for c in a["cards"]] == [c["name"] for c in b["cards"]]


def test_goldfish_stats_basic(client):
    r = client.post("/goldfish/stats", json={"decklist": DIMIR_SMOKE, "n_samples": 200, "seed": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["n_samples"] == 200
    assert 0 < body["avg_land_count"] < 7
    assert 0 <= body["keepable_rate"] <= 1


def test_goldfish_stats_rejects_excessive_n(client):
    r = client.post("/goldfish/stats", json={"decklist": DIMIR_SMOKE, "n_samples": 999_999})
    assert r.status_code == 400


def test_goldfish_simulate_turn_log(client):
    r = client.post("/goldfish/simulate", json={"decklist": DIMIR_SMOKE, "turns": 5, "seed": 7})
    assert r.status_code == 200
    body = r.json()
    assert body["turns_played"] == 5
    assert len(body["turns"]) == 5


def test_goldfish_simulate_many(client):
    r = client.post(
        "/goldfish/simulate-many",
        json={"decklist": DIMIR_SMOKE, "n_games": 50, "turns": 4, "seed": 1},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["n_games"] == 50
    assert 0 <= body["avg_mana_efficiency"] <= 1


def test_goldfish_simulate_rejects_bad_turns(client):
    r = client.post("/goldfish/simulate", json={"decklist": DIMIR_SMOKE, "turns": 99})
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Deck import
# ---------------------------------------------------------------------------

def test_import_deck_plain_text(client):
    r = client.post("/import-deck", json={"text": "4 Brainstorm\n4 Ponder\n"})
    assert r.status_code == 200
    body = r.json()
    main_names = [e["name"] for e in body["main"]]
    assert "Brainstorm" in main_names
    assert "Ponder" in main_names


def test_import_deck_resolves_card_data(client):
    """Parsed entries should include resolved Scryfall data."""
    r = client.post("/import-deck", json={"text": "4 Brainstorm"})
    body = r.json()
    entry = body["main"][0]
    assert entry["card"] is not None
    assert entry["card"]["mana_cost"] == "{U}"


def test_import_deck_empty_body_400(client):
    r = client.post("/import-deck", json={})
    assert r.status_code == 400


def test_import_deck_empty_text_400(client):
    r = client.post("/import-deck", json={"text": "   \n\n"})
    # Either 400 (no cards found) or 200 with empty main — both are acceptable
    # behaviors. Pin current behavior:
    assert r.status_code in (200, 400)


# ---------------------------------------------------------------------------
# LLM-backed endpoints — mock generate() so we don't hit Ollama/SageMaker
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_generate(monkeypatch):
    """Replace generate() with a canned-response stub."""
    async def fake_generate(messages, **kwargs):
        # Return a response that references a real card so resolve_cards can
        # attach image data — exercises the post-generation pipeline too.
        return "Dimir Tempo plays Brainstorm and Force of Will as staples."

    import src.server as server
    monkeypatch.setattr(server, "generate", fake_generate)
    return fake_generate


def test_chat_endpoint(client, mock_generate):
    r = client.post("/chat", json={
        "messages": [{"role": "user", "content": "What's the best deck in Legacy?"}],
        "temperature": 0.3,
    })
    assert r.status_code == 200
    body = r.json()
    assert "content" in body
    assert "Dimir Tempo" in body["content"]


def test_chat_resolves_mentioned_cards(client, mock_generate):
    r = client.post("/chat", json={
        "messages": [{"role": "user", "content": "anything"}],
    })
    body = r.json()
    # Response mentions Brainstorm + Force of Will — server should
    # resolve both via card_index and attach them to `cards`
    names = {c["name"] for c in body.get("cards", [])}
    assert "Brainstorm" in names
    assert "Force of Will" in names


def test_build_deck_endpoint(client, mock_generate):
    r = client.post("/build-deck", json={
        "messages": [{"role": "user", "content": "Build me tempo"}],
    })
    assert r.status_code == 200


def test_analyze_deck_endpoint(client, mock_generate):
    r = client.post("/analyze-deck", json={
        "messages": [{"role": "user", "content": "4 Brainstorm, 4 Ponder"}],
    })
    assert r.status_code == 200


def test_evaluate_board_endpoint(client, mock_generate):
    r = client.post("/evaluate-board", json={
        "messages": [{"role": "user", "content": "Opp has Blood Moon"}],
    })
    assert r.status_code == 200


def test_evaluate_card_endpoint(client, mock_generate):
    r = client.post("/evaluate-card", json={
        "messages": [{"role": "user", "content": "Is Counterspell good?"}],
    })
    assert r.status_code == 200


def test_goldfish_llm_endpoint(client, mock_generate):
    r = client.post("/goldfish", json={
        "messages": [{"role": "user", "content": "Goldfish my deck"}],
    })
    assert r.status_code == 200


def test_budget_sub_llm_endpoint(client, mock_generate):
    r = client.post("/budget-sub", json={
        "messages": [{"role": "user", "content": "Underground Sea alternative"}],
    })
    assert r.status_code == 200
