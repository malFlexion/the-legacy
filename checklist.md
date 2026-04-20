# The Legacy — Project Checklist

## Phase 1: Data Foundation

- [x] Download MTG Comprehensive Rules → `data/comprehensive-rules.txt`
- [x] Download Scryfall bulk card data → `data/scryfall-cards.json`
- [x] Build MTG slang dictionary → `data/mtg-slang.md`
- [x] Build Legacy deck history + variant index → `data/legacy-deck-history.md`
- [x] Build archetype guide → `data/archetype-guide.md`
- [x] Write Legacy basics guide → `data/legacy-basics.md`
- [x] Write deckbuilding guide → `data/deckbuilding-guide.md`
- [x] Write meta analysis → `data/legacy-analysis.md`
- [x] Chunk comprehensive rules by section and embed into vector DB
- [x] Build card name index from Scryfall data for fuzzy matching
- [x] Index meta data, deck history, and strategy content into vector DB

## Phase 2: Model

- [x] Build LoRA training dataset (1,549 pairs across 13 files after Round 2 + post-deploy fixes)
  - [x] Q&A pairs from comprehensive rules (422 pairs)
  - [x] Deck-building rationale (217 pairs)
  - [x] Card evaluation in Legacy context (304 pairs after Round 2 + Bowmasters disambig pairs)
  - [x] Deck analysis examples (146 pairs)
  - [x] Budget substitution examples (129 pairs after Round 2 additions)
  - [x] Conversation flow examples (119 pairs)
  - [x] Board state analysis examples (146 pairs after Round 2 additions)
  - [x] Round 2 new categories: meta_awareness (26), negative_examples (12), card_relevance (9), disambiguation (9), deck_construction (6), uniqueness (4)
- [ ] Hand-review curated subset (~200-300 examples) for accuracy
- [x] Build evaluation dataset (22 test cases across 9 categories)
  - [x] Deck legality (60 main + 15 side, all Legacy-legal)
  - [x] Card relevance (recommended cards match stated strategy)
  - [x] Meta awareness (correctly identifies top decks and weaknesses)
  - [x] Rules knowledge (correct rulings on card interactions)
  - [x] Board state analysis (identifies correct play given a board)
  - [x] Uniqueness (deck is meaningfully different from known lists)
  - [x] Deck analysis (correctly classifies archetype, strengths, weaknesses)
  - [x] Budget substitutions (functional replacements with honest trade-offs)
  - [x] Card evaluation (correctly assesses Legacy playability)
- [x] Run baseline eval against un-finetuned model (28.9%)
- [x] LoRA finetune on training set (1,546 pairs, 5 epochs, loss 1.30)
- [x] Run eval against finetuned model, compare results (61.6%, +32.7%)
- [x] Document honest analysis of improvements and remaining weaknesses
- [ ] Round 2: Fix regressions and weak categories
  - [x] Add meta_awareness pairs (26 pairs from real meta data)
  - [x] Add board_state pairs (16 pairs with correct rulings incl. Blood Moon, Chalice, Karakas)
  - [x] Add budget_subs pairs (8 pairs with real prices and honest trade-offs)
  - [x] Add card_evaluation pairs (10 pairs with correct Scryfall stats)
  - [x] Add negative examples (12 pairs teaching uncertainty and "I don't know")
  - [x] Add card_relevance pairs with color/strategy constraints (9 pairs, color-locked)
  - [x] Add structured deck construction examples (6 complete 60+15 decklists)
  - [x] Add disambiguation pairs (9 pairs — card vs mechanic vs archetype)
  - [x] Add uniqueness/brew pairs (4 novel deck concepts)
  - [x] Fix factual errors in existing training data (audit + fix: Grief/Psychic Frog ban updates, Counterspell MV fix, Blood Moon fix, Containment Priest fix, Entomb ban notes, removed 3 duplicates)
  - [x] Re-run finetune and eval (54.8% → 61.6%, +6.8%)

## Phase 3: Infrastructure

- [x] Set up Ollama locally serving finetuned model (GGUF quantized, q8_0)
  - [x] `scripts/merge_and_convert.py` — end-to-end merge + GGUF + Modelfile generation
  - [x] Modelfile with correct Llama 3.2 chat template (dropped `$last` — Ollama runtime doesn't support it)
  - [x] Deployment walkthrough at `notes/development/ollama-deployment.md`
  - [x] Condensed setup checklist at `notes/development/ollama-checklist.md`
  - [x] Smoke-test script `scripts/test_deployment.py --ollama` (5 prompts with expect/reject patterns)
  - [x] Ollama + llama.cpp installed locally
  - [x] Merge + GGUF conversion completed (`the-legacy.gguf` at q8_0, ~1.3GB)
  - [x] `ollama create the-legacy -f Modelfile` succeeded; model reachable via `ollama run`
  - [x] Smoke test: 3/5 passed (phrasing-strict failures on 2; model produces sensible domain-aware responses — see round1-analysis for expected Round 2 eval behavior)
- [ ] Deploy SageMaker endpoint for remote demo
  - [x] `scripts/merge_and_convert.py --push-hf-repo ...` pushes merged model to HF
  - [x] `scripts/deploy_sagemaker.py` with --create/--delete/--status/--test actions
  - [x] Cost warning in --create, ongoing cost estimate in --status
  - [x] Walkthrough at `notes/development/sagemaker-deployment.md`
  - [x] Interactive deployment notebook at `notebooks/deploy_sagemaker.ipynb`
  - [x] Smoke-test script `scripts/test_deployment.py --sagemaker` (5 prompts with expect/reject patterns)
  - [ ] External: AWS account, `aws configure`, SageMaker execution role
  - [ ] Getting AWS access key + secret (needed for Fly secrets and local `$env:AWS_*`):
    - **If already configured**: `Get-Content $env:USERPROFILE\.aws\credentials` — both values live under `[default]` as `aws_access_key_id` and `aws_secret_access_key`
    - **If new user / fresh pair**: AWS Console → IAM → Users → your user → Security credentials → Create access key → "Application running outside AWS". Secret is shown **only once** — copy it immediately. Attach `AmazonSageMakerFullAccess` policy to the user if missing.
    - **Shortcut**: if `aws sts get-caller-identity` already works, boto3 picks up creds from `~/.aws/credentials` automatically — no `$env:AWS_*` needed locally. Only Fly.io (`fly secrets set`) needs them explicitly since the container has no `~/.aws`.
  - [x] Run merge + push to HF, then `scripts/deploy_sagemaker.py --create`
  - [x] Verify with `scripts/deploy_sagemaker.py --test`
  - [x] `scripts/deploy_sagemaker.py --delete` when done (stops billing!)
- [x] Build FastAPI layer (`src/server.py`)
  - [x] `POST /chat` — main conversation, streaming + non-streaming
  - [x] `POST /build-deck` — generate 75-card decklist
  - [x] `POST /analyze-deck` — import + analyze a decklist
  - [x] `POST /evaluate-board` — board state analysis
  - [x] `POST /goldfish` — run N goldfish hands
  - [x] `POST /budget-sub` — budget substitutions
  - [x] `POST /evaluate-card` — card Legacy playability
  - [x] `GET /card/{name}` — Scryfall proxy with fuzzy match
  - [x] `GET /card/{name}/search` — fuzzy card search
  - [x] `GET /health` — health check (model, card index, vector DB status)
- [x] Integrate RAG retrieval into chat pipeline
- [x] Integrate deterministic Scryfall card resolution
  - [x] Parse card names from model output (exact match via card_index.resolve)
  - [x] Resolve to Scryfall data (oracle text, mana cost, type, legality, image)
  - [x] Attach as structured metadata to response
  - [x] Flag invalid/non-Legacy-legal cards (legacy_legal field on each card)
- [x] Build deck import parser (`src/deck_parser.py` + `POST /import-deck`)
  - [x] Plain text decklist (one-per-line, comma-separated, markdown bullets)
  - [x] Moxfield URL (via API: `api2.moxfield.com/v3/decks/all/{id}`)
  - [x] MTGGoldfish URL (via download endpoint)
- [x] Build budget substitution engine (`src/budget_engine.py` + 22 tests)
  - [x] Card-to-card replacement mappings (curated, 20+ expensive Legacy staples)
  - [x] Trade-off scoring (power_loss 0-10 + explicit tradeoff strings + notes)
  - [x] Budget tier generation (full / mid / budget via `/budget-tiers` endpoint)
  - [x] Price data from Scryfall (via card_index, supports USD + EUR fallback)
- [x] Implement streaming on /chat (SSE via Ollama backend)
- [x] Implement sampling presets (per-endpoint temperature tuning)
  - [x] Precise (temp 0.2) — /build-deck, /analyze-deck
  - [x] Balanced (temp 0.3-0.4) — /chat, /budget-sub, /evaluate-card, /evaluate-board
  - [x] Creative (temp 0.5) — /goldfish
  - [x] Manual override via `temperature` field on all requests

## Phase 4: Goldfish Engine

### Tier 1 (MVP — must ship)
- [x] Deck representation (`src/goldfish_engine.Deck` from decklist via card_index)
- [x] Draw opening hand (`POST /goldfish/draw` returns full card data + stats)
- [x] London Mulligan (`keep_count` param, 7=no mull, draw 7 put back 7-keep_count)
- [x] Basic stats over N sample hands (`POST /goldfish/stats`, 32 tests)
  - [x] Land count distribution
  - [x] Mana curve of opening hand
  - [x] Color availability by turn (handles fetchlands via FETCH_LAND_COLORS map)
- [x] LLM commentary on hand (existing `POST /goldfish` endpoint)

### Tier 2 (Target — if time allows)
- [x] Simplified turn engine (untap, draw, play land, cast spells) — `src/turn_engine.py`
- [x] Track mana available, cards in hand, permanents on board, graveyard, exile, life
- [x] Play out N turns (default 6; configurable up to 15)
- [x] Stats: avg turn first cast per card, cast rate, mana efficiency per turn

### Tier 3 (Stretch — nice to have)
- [x] Mana ability resolution
  - [x] Fetchlands (sacrifice, search library for preferred dual/basic, shuffle)
  - [x] Dual lands, shocklands, basics via `color_identity`
  - [x] Colorless utility lands (Wasteland, Ancient Tomb with 2 life cost)
  - [x] Fast mana (Lotus Petal, Chrome Mox, Mox Diamond, LED, City of Traitors)
- [x] Spell sequencing heuristics
  - [x] Cantrips / rituals / tutors cast before committing threats
  - [x] Reactive cards (Force of Will, Daze, removal) skipped — they sit in hand
- [x] Combo detection: `COMBOS` map with Marit Lage (Dark Depths + Thespian's Stage), Painter + Grindstone, Helm + Leyline, Thopter+Sword, Food Chain, Ideal+Dovescape
- [x] Full statistical summary over N games: `POST /goldfish/simulate-many` (up to 10,000 games) with combo assembly rates, per-card cast rates, and avg mana efficiency
- [x] Two new endpoints: `POST /goldfish/simulate` (single game log), `POST /goldfish/simulate-many` (aggregate)
- [x] 21 tests in `tests/test_turn_engine.py` (see Testing section below for the full suite)

## Phase 5: Frontend (static files served by FastAPI on Fly.io → SageMaker)

Architecture: single Fly.io deployment serves both the JSON API and the static frontend (`docs/`). FastAPI mounts `docs/` at `/` via `StaticFiles(html=True)` after all API routes, so `GET /` returns the UI and `POST /chat` etc. hit the API. One URL, no CORS. No Gradio — vanilla JS, no build step.

- [x] Chat tab
  - [x] Conversation with deck-building bot (POST /chat)
  - [x] Card images rendered inline from Scryfall metadata in response
  - [x] Chat history maintained in-session
- [x] Import & Analyze tab (supersedes separate Decklist tab)
  - [x] Paste decklist text or Moxfield/MTGGoldfish URL (POST /import-deck)
  - [x] Visual card grid with counts, Scryfall hover links
  - [x] Mana curve bar chart
  - [x] Archetype classification + full analysis via POST /analyze-deck
  - [x] Card click/hover opens full Scryfall page
- [x] Goldfish tab
  - [x] Opening hand display with card images (POST /goldfish/draw)
  - [x] London Mulligan button (keep_count -= 1)
  - [x] Single-game simulation (POST /goldfish/simulate) with turn log
  - [x] 1000-game aggregate stats (POST /goldfish/simulate-many)
- [x] Budget Tiers tab
  - [x] Full/Mid/Budget three-column view (POST /budget-tiers)
  - [x] Per-tier price + applied substitutions list + irreplaceables
  - [x] Total savings shown
- [x] Connect all tabs to API (centralized `api()` helper in app.js)
- [x] API health check in header (calls /health on load)

Deployment infrastructure:
- [x] `Dockerfile` + `.dockerignore` for Fly.io build (copies `src/`, `data/card_index.pkl`, `docs/`, `vectordb/`)
- [x] Docker warm-up: pre-downloads `all-MiniLM-L6-v2` during build so cold starts don't re-fetch it (~80MB)
- [x] `fly.toml` with scale-to-zero, us-east-1 region, 1GB RAM (512MB OOM-killed once chromadb + embeddings loaded)
- [x] Fly `[env] PORT` matches `[http_service] internal_port` (both 8000) — earlier mismatch caused "refused connection" errors
- [x] Static mount at `/` in `src/server.py` via `StaticFiles(html=True)` — same process serves UI + API
- [x] `config.js` set to empty `API_BASE` for same-origin fetches (no CORS needed)
- [x] Walkthrough at `notes/development/frontend-deployment.md`
- [x] `vectordb/` committed to repo (13MB) so CD builds have RAG data available
- [x] `.github/workflows/fly-deploy.yml` — auto-deploys on push to master, triggers scoped to code paths that affect the image (skips doc-only commits)
- [ ] Generate Fly deploy token (`fly tokens create deploy`) and add as `FLY_API_TOKEN` GitHub secret to activate CD

## Testing

- [x] **219 tests passing · 86% line coverage** (`pytest tests/ --cov=src`)
- [x] Per-module coverage breakdown:
  - `deck_parser.py` — **100%** (28 tests)
  - `goldfish_engine.py` — **98%** (32 tests)
  - `build_vectordb.py` — **95%** (53 tests: chunking + build pipeline + Chroma queries)
  - `budget_engine.py` — **93%** (22 tests)
  - `turn_engine.py` — **91%** (21 tests)
  - `card_index.py` — **84%** (32 tests)
  - `server.py` — **73%** (31 tests — all 14 FastAPI endpoints via TestClient with mocked LLM)
- [x] Test isolation: `pytest.importorskip` guards on fastapi/chromadb so the suite gracefully degrades if deps aren't installed in the active Python
- [x] URL imports (Moxfield / MTGGoldfish) tested with a monkey-patched `httpx.AsyncClient` — no network calls in CI
- [x] LLM endpoints tested with `monkeypatch.setattr(server, "generate", ...)` — no model dependency in CI
- [x] End-to-end build: synthetic data-dir fixture exercises the whole `build_database()` pipeline including Chroma delete+recreate idempotency
- [x] `.coverage` and `.pytest_cache/` gitignored

## Phase 6: Documentation & Demo

- [ ] Technical documentation
  - [ ] Architecture overview with diagram
  - [x] Training data sources and preparation process (`notes/development/progress.md`, `round1-analysis.md`)
  - [x] LoRA training process and hyperparameters (documented in `finetune_legacy.ipynb`)
  - [x] API reference (in README: 14 endpoints, LLM-backed vs deterministic)
  - [x] Deployment instructions — reproducible
    - [x] Ollama walkthrough (`notes/development/ollama-deployment.md`)
    - [x] SageMaker walkthrough (`notes/development/sagemaker-deployment.md`)
  - [x] Sampling method explanation (temperature presets documented inline in `src/server.py`)
  - [x] Evaluation results and analysis (`round1-analysis.md` covers Round 1; Round 2 numbers in README + `eval_report.json`)
- [ ] Demo presentation
  - [ ] Live walkthrough: play style → deck → view → goldfish
  - [ ] Show meta awareness and rules knowledge
  - [ ] Show deck import and analysis
  - [ ] Explain architectural decisions and trade-offs
  - [ ] Pre-record backup video in case of live issues
- [ ] Final eval run with polished model
