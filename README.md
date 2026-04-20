# The Legacy — AI-Powered MTG Legacy Deck Builder

An AI application that helps Magic: The Gathering players design, refine, and test **Legacy format** decks that are unique in the current metagame.

## What It Does

- **Deck Building Chat** — Describe your play style, preferences, and meta goals. The AI curates a 75-card deck through conversation, explaining every card choice.
- **Deck Import & Analysis** — Paste an existing decklist and get a full breakdown: strengths, weaknesses, meta positioning, and suggested improvements.
- **Meta Awareness** — Understands the current Legacy metagame (54+ archetypes), win rates, matchups, and how to position a brew against the field.
- **Board State Analysis** — Describe a game state and get advice on optimal plays, threat assessment, and sequencing.
- **Goldfish Mode** — Solitaire-test your deck: draw hands, mulligan, play out turns, and get statistical consistency reports.
- **Budget Substitutions** — Get budget-friendly alternatives for expensive cards (especially Reserved List dual lands) with honest assessments of the trade-offs.
- **Future Set Consideration** — Evaluate upcoming spoiled cards and how they might slot into your deck or shift the meta.
- **Rules Knowledge** — Deep understanding of the MTG Comprehensive Rules via RAG, with accurate rulings on complex Legacy card interactions.
- **Scryfall Integration** — Every card mentioned comes with full oracle text, images, and legality data pulled live from the Scryfall API.

## What Is Legacy?

Legacy is a **non-rotating, eternal constructed format** in Magic: The Gathering that permits cards from all Magic sets ever printed, subject to a curated ban list. It is one of the oldest and most skill-intensive competitive formats.

### Key Characteristics
- **Card pool**: Every MTG set from Alpha (1993) through the latest release
- **Deck construction**: Minimum 60 cards main, up to 15 sideboard, max 4 copies of any card
- **No rotation**: Cards stay legal forever unless specifically banned
- **Free counterspells**: Force of Will and Daze define the format's interaction model
- **Brainstorm + fetchlands**: The defining card selection engine for blue decks
- **Reserved List**: Dual lands (Underground Sea, Volcanic Island, etc.) cannot be reprinted, giving Legacy a unique and expensive mana base
- **Diverse metagame**: Combo, control, tempo, midrange, and prison strategies are all viable

### Why People Play Legacy
- Access to Magic's entire 30+ year card history
- Highest skill ceiling of any constructed format
- Long-term deck investment — no rotation means your deck keeps working
- Incredibly diverse metagame (~54 distinct competitive archetypes)
- Unique strategic dynamics from free spells and efficient mana denial

### Current Meta Snapshot (April 2026)
| Tier | Top Decks |
|------|-----------|
| Tier 1 | Dimir Tempo (14.6%), Ocelot Pride Midrange (8.5%), Oops! All Spells (8.2%), Sneak and Show (6.7%) |
| Tier 2 | Izzet Delver, Painter, Lands, The EPIC Storm, Eldrazi, Mystic Forge Combo, Mardu Energy, Boros Initiative |
| Tier 3 | Doomsday, Red Stompy, Affinity, Beanstalk Control, Death and Taxes, Stoneblade, Pox, Miracles |

Format health: Considered healthy per March 2026 B&R announcement (no changes). Data covers ~6,433 entries / ~35,000 matches since Entomb ban (November 2025).

### Complete Ban List
~70 individually banned cards plus categorical bans on Conspiracy cards, ante cards, sticker/Attraction cards, and culturally offensive cards. Notable bans include: Black Lotus, Ancestral Recall, the Moxen, Brainstorm's enablers (Gitaxian Probe, Dreadhorde Arcanist), Deathrite Shaman, Sensei's Divining Top, Wrenn and Six, Ragavan, Oko, Grief, Entomb, Nadu, and Psychic Frog.

## Project Structure

```
the_legacy/
  data/
    comprehensive-rules.txt    # Full MTG Comprehensive Rules (Feb 2026, ~943KB)
    scryfall-cards.json         # Scryfall bulk data (508MB, gitignored — download separately)
    mtg-slang.md                # 346-entry MTG slang dictionary (5 categories)
    legacy-deck-history.md      # 54 archetypes + 420 variant index with decklists, history, meta data
    archetype-guide.md          # 32 parent archetypes, 200+ variants with Scryfall links
    legacy-basics.md            # Legacy format guide (ban list, play patterns, glossary)
    deckbuilding-guide.md       # Deckbuilding principles (Reid Duke) with card images
    legacy-analysis.md          # Meta analysis with matchup/hate matrices, meta evolution
    training/                   # LoRA training dataset (1,549 pairs after Bowmasters disambig adds)
      rules_qa.jsonl            #   Rules Q&A (422 pairs)
      card_evaluation.jsonl     #   Card playability assessment (304 pairs)
      deckbuilding_rationale.jsonl  # Deck-building rationale (217 pairs)
      deck_analysis.jsonl       #   Archetype ID, meta positioning (146 pairs)
      board_state_analysis.jsonl #  Opening hands, board states, sequencing (146 pairs)
      conversation_flow.jsonl   #   Deck consultation dialogues (119 pairs)
      budget_substitutions.jsonl #  Budget alternatives, upgrade paths (129 pairs)
      meta_awareness.jsonl      #   Meta %, tiers, matchups (26 pairs, Round 2)
      negative_examples.jsonl   #   Uncertainty and "I don't know" responses (12 pairs, Round 2)
      card_relevance.jsonl      #   Color/strategy-constrained recommendations (9 pairs, Round 2)
      disambiguation.jsonl      #   Card vs mechanic vs archetype (9 pairs, Round 2)
      deck_construction.jsonl   #   Complete 60+15 verified decklists (6 pairs, Round 2)
      uniqueness.jsonl          #   Novel brew concepts (4 pairs, Round 2)
  src/
    server.py                   # FastAPI server (chat, card lookup, RAG, streaming, Ollama/SageMaker, static mount)
    deck_parser.py              # Deck import parser (plain text, Moxfield, MTGGoldfish)
    build_vectordb.py           # Builds ChromaDB vector database (719 chunks)
    card_index.py               # Card name index for fuzzy matching (36,670 cards)
    budget_engine.py            # Curated budget substitution engine with Scryfall prices
    goldfish_engine.py          # Deterministic deck sampling, London Mulligan, aggregate stats
    turn_engine.py              # Turn-by-turn goldfish simulator with combo detection
  docs/                         # Static frontend served by FastAPI at /
    index.html                  # 4-tab UI: Chat / Import & Analyze / Goldfish / Budget
    app.js                      # Vanilla JS, ~500 lines, no build step
    styles.css                  # Dark theme
    config.js                   # window.API_BASE (empty = same-origin)
  scripts/
    deploy_sagemaker.py         # Deploy/manage SageMaker endpoint (--create/--delete/--status/--test)
    merge_and_convert.py        # Merge LoRA + GGUF convert (Ollama) or push to HF (SageMaker)
    test_deployment.py          # Smoke-test Ollama/SageMaker with expect/reject prompt patterns
    audit_training_data.py      # Cross-reference training pairs against Scryfall for factual errors
    fix_training_data.py        # Apply audit fixes (duplicates, banned cards, factual errors)
    gen_round2_data.py          # Generate Round 2 training pairs from project data files
  tests/
    test_card_index.py          # 32 tests for card index
    test_build_vectordb.py      # 47 tests for vector DB builder
    test_budget_engine.py       # 22 tests for budget substitution engine
    test_goldfish_engine.py     # 32 tests for goldfish engine
    test_turn_engine.py         # 21 tests for turn engine (154 total)
  notebooks/
    finetune_legacy.ipynb       # LoRA finetuning notebook (SageMaker)
    deploy_sagemaker.ipynb      # Interactive SageMaker endpoint deployment walkthrough
    eval_report.json            # Evaluation results (Round 2, 61.6% finetuned)
    lora-legacy/                # Checkpoint outputs (gitignored)
  vectordb/                     # ChromaDB vector database (committed, 13MB) — rebuild with src/build_vectordb.py
  Dockerfile                    # Fly.io image (Python 3.11-slim + FastAPI + chromadb + pre-cached embedding model)
  fly.toml                      # Fly.io app config (us-east-1, scale-to-zero, 1GB RAM)
  .github/workflows/
    fly-deploy.yml              # CI: auto-deploy to Fly on push to master
  Modelfile                     # Ollama model config with Llama 3.2 chat template
  notes/
    assignment-00.md ... assignment-11.md   # Course assignment notes
    chapter-01.md ... chapter-12.md         # Book chapter notes
    final-project.md                        # Rubric breakdown
    development/
      progress.md                           # Running dev notes (dataset, training)
      round1-analysis.md                    # Honest analysis of Round 1 results
      ollama-deployment.md                  # Walkthrough: merge → GGUF → ollama serve
      ollama-checklist.md                   # Condensed checkbox list for the Ollama path
      sagemaker-deployment.md               # Walkthrough: merge+push → SageMaker endpoint
      frontend-deployment.md                # Walkthrough: Docker → Fly → continuous deploy on push
  checklist.md                  # Project progress checklist
  final-project-plan.md         # Detailed implementation plan
  README.md                     # This file
```

## Deployment

Three deployment paths, all sharing the same merge step (`scripts/merge_and_convert.py`) and verified with the same smoke test (`scripts/test_deployment.py`).

| Path | What | Cost | Use when |
|---|---|---|---|
| **Ollama** (local GGUF) | Model runs on your laptop | Free | Dev, local demo |
| **Fly.io all-in-one** | Fly machine runs FastAPI **and** Ollama in the same container | ~$0.50/hr while running (always-on, `performance-8x`/16 GB) | **The public demo backend** |
| **SageMaker** (TGI endpoint) | Model runs on A10G GPU in AWS | ~$1.41/hr | Alternative remote backend; set `INFERENCE_BACKEND=sagemaker` |

**Architecture for the public demo (all-in-one Fly + Ollama):**
```
Browser ─HTTPS─> Fly machine ─┬─> FastAPI  (serves docs/, /chat, /health, etc.)
                              ├─> Ollama   (localhost:11434, GGUF on a Fly Volume)
                              └─> ChromaDB (RAG index rebuilt in-container)
```

One container serves the UI (`docs/`), the 14 JSON endpoints, and the model — no cross-service credentials. The entrypoint (`scripts/docker_entrypoint.sh`) starts Ollama, downloads the GGUF from HuggingFace on first boot into `/root/.ollama` (mounted as a Fly Volume so it survives restarts), rebuilds the vector DB, then execs uvicorn. Modelfile and vectordb version markers trigger re-registration / rebuilds when params or schemas change.

### Inference pipeline (what happens on every `/chat` request)

1. **Query card extraction** (`extract_query_cards`) — exact word-boundary names from `card_index.resolve`, then a token-level fuzzy pass where each substantive query word is fuzzy-matched against all ~36k card names (rank 2+ starts-with matches only, Legacy-legal preferred). This catches short partials like "Akroma" → "Akroma, Angel of Wrath". A whole-query fuzzy fallback runs only when nothing else hit, so typos ("Emrakull") still resolve without polluting clean queries.
2. **Card context injection** (`format_card_context`) — resolved card data (name, mana cost, type, P/T, oracle text, keywords) is written into the system prompt with instructions to use the data verbatim. Addresses the generic-embedding-doesn't-know-MTG problem by giving the LLM ground truth before it generates.
3. **RAG retrieval** (`retrieve_context`) — ChromaDB query over ~31k chunks (strategy guides + rules + card data). When card injection fired, the RAG call passes `where={"source": {"$ne": "scryfall-card"}}` so retrieval returns *only* strategy/rules chunks — RAG's job becomes context, card data already has ground truth. `n_results=10` keeps strategy chunks from being crowded out.
4. **Generation** — Ollama streams tokens back; temperature 0.1, `num_predict 256`, `num_ctx 2048` (see Sampling section below).
5. **Card resolution + bracket wrapping** — response is scanned for card names; `auto_bracket_cards` wraps them in `[[Name]]` markup. Frontend renders those as clickable Scryfall links and populates the left-panel card grid in the order they appear in the response.
6. **Filtering** — basic lands and non-Legacy-legal cards are hidden from the panel unless the response is specifically discussing bans.

### Sampling method

Rubric asks for an "appropriate sampling method"; this project uses deterministic-leaning temperature sampling tuned per endpoint. The 1B model hallucinates card stats at higher temperatures, so we trade some creative variation for factual stability.

| Endpoint | Temperature | Rationale |
|---|---|---|
| `/chat` (Modelfile default) | **0.1** | Global anti-hallucination pass — low temperature keeps the model close to the ground-truth card data injected into the system prompt |
| `/build-deck`, `/analyze-deck` | 0.2 ("precise") | Deck construction needs consistent 60+15 structure and Legacy-legal choices |
| `/budget-sub`, `/evaluate-card`, `/evaluate-board` | 0.3–0.4 ("balanced") | Explanatory output where a bit more phrasing variation reads naturally |
| `/goldfish` | 0.5 ("creative") | Keep-or-mull commentary benefits from variety; stats come from the deterministic engine anyway |

Other Modelfile params: `num_predict 256` (chat responses run short to stay on-topic), `num_ctx 2048` (fits the system prompt + card-injection block + RAG block + recent turns). Callers can override `temperature` on any request. Sampling is pure top-k/top-p (Ollama defaults) — no beam search, no constrained decoding. Card validity is enforced *after* generation via the deterministic `card_index.resolve` pass, not by restricting the decoder.

### Comparison against the SageMaker path

The SageMaker path (legacy, kept for parity) runs the same merged LoRA model via TGI on an A10G. It supports identical endpoints via a thin `SAGEMAKER_ENDPOINT`-routed branch in `generate()`. For the public demo we switched away from SageMaker because it doubled operational cost without a quality win at 1B size — the Fly CPU path hits acceptable latency with `performance-8x`, and keeping AWS credentials out of the loop removed a whole class of deploy breakage.

Walkthroughs:
- **Ollama:** [`notes/development/ollama-checklist.md`](notes/development/ollama-checklist.md) (condensed) or [`ollama-deployment.md`](notes/development/ollama-deployment.md)
- **SageMaker:** [`notebooks/deploy_sagemaker.ipynb`](notebooks/deploy_sagemaker.ipynb) (interactive) or [`sagemaker-deployment.md`](notes/development/sagemaker-deployment.md)
- **Fly.io + frontend:** [`notes/development/frontend-deployment.md`](notes/development/frontend-deployment.md)

Verify any deployment with:
```
python scripts/test_deployment.py --ollama      # or --sagemaker or --all
```

**CI/CD:** `.github/workflows/fly-deploy.yml` is manual-only right now (`workflow_dispatch`) — trigger from the Actions tab → Fly Deploy → Run workflow. Push-triggered auto-deploy is commented out at the top of the file; uncomment the `push:` block to re-enable.

### Prerequisites check — before deploying

Before `fly deploy` (or hitting Run workflow) will succeed, you need:

**Fly.io (public demo, all-in-one)** — `flyctl` installed and authenticated, persistent volume attached:
```
flyctl version                                    # install: https://fly.io/docs/hands-on/install-flyctl/
fly auth whoami                                   # confirms you're logged in
fly status -a the-legacy-api                      # confirms the app exists, machine running
fly volumes list -a the-legacy-api                # should show `ollama_data` mounted at /root/.ollama
```
No cloud secrets needed for the all-in-one path — Ollama runs inside the container, GGUF downloads at boot from HuggingFace. Deploy with:
```
fly deploy --strategy immediate -a the-legacy-api
```
`--strategy immediate` replaces the running machine in place (Fly's default blue/green needs two volumes, which costs double). First boot pulls the GGUF (~1.3 GB) from HuggingFace into the volume and rebuilds the vector DB; subsequent boots are fast because both are cached.

**SageMaker (alternative remote backend)** — only if running `INFERENCE_BACKEND=sagemaker`:
```
aws sts get-caller-identity                       # confirms CLI is configured
aws sagemaker describe-endpoint --endpoint-name the-legacy-llm
python scripts/deploy_sagemaker.py --create --role arn:aws:iam::ACCOUNT:role/ROLE
```
Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `SAGEMAKER_ENDPOINT`, and `INFERENCE_BACKEND=sagemaker` as Fly secrets if you want Fly to proxy a SageMaker backend instead of running Ollama in-container. The IAM user needs `sagemaker:InvokeEndpoint` and `sagemaker:DescribeEndpoint`.

**GitHub Actions (only if using push-triggered CD)** — the `FLY_API_TOKEN` secret:
```
fly tokens create deploy -a the-legacy-api
```
Paste into repo Settings → Secrets and variables → Actions → new secret named `FLY_API_TOKEN`.

**End-to-end sanity check after deploying:**
```
curl https://the-legacy-api.fly.dev/health
```
Expected `"status": "ok"`, `"llm": {"reachable": true}`, and `vector_chunks` around 31,000. If `reachable: false`, `detail` tells you what's wrong (Ollama still booting, model not yet registered, etc.).

Note on GGUF quantization: `convert_hf_to_gguf.py` emits f16/bf16/q8_0 directly. Smaller quantizations (q4_k_m, q5_k_m) require compiling llama.cpp and running its `llama-quantize` binary on the f16 output. At 1B size, q8_0 is near-lossless and the size difference doesn't matter.

## Training Results (Round 2)

LoRA finetune of Llama 3.2 1B on 1,546 training pairs (5 epochs, rank 16, loss 1.30).

| Category | Baseline | Finetuned | Change |
|---|---|---|---|
| deck_legality | 100% | 100% | — |
| rules_knowledge | 50% | 83% | **+33%** |
| card_evaluation | 13% | 71% | **+58%** |
| deck_analysis | 0% | 67% | **+67%** |
| card_relevance | 0% | 50% | **+50%** |
| meta_awareness | 17% | 50% | **+33%** |
| board_state | 42% | 42% | — |
| budget_subs | 10% | 20% | +10% |
| **Overall** | **28.9%** | **61.6%** | **+32.7%** |

**Key findings**: Major gains across most categories, especially card evaluation (+58%) and deck analysis (+67%). Board state and budget subs remain weak — RAG and Scryfall card resolution in the inference pipeline are expected to compensate for factual accuracy gaps.

## Technology Stack

- **Model**: Llama 3.2 1B + LoRA adapter (rank 16, 5 epochs, 1,546 training pairs). LoRA trained on SageMaker (Tesla T4), merged and converted to GGUF q8_0 (~1.3 GB) for Ollama serving
- **RAG**: ChromaDB with `sentence-transformers/all-MiniLM-L6-v2` embeddings over ~31k chunks: comprehensive rules, archetype guides, meta analysis, and one chunk per Legacy-legal card. Card chunks are metadata-filtered out of retrieval when the query names specific cards (ground truth already injected)
- **Inference**: Ollama in-container on Fly.io for the public demo (`performance-8x`, 16 GB, persistent machine). Local Ollama and SageMaker TGI remain supported via `INFERENCE_BACKEND`
- **API**: FastAPI — 14 endpoints, SSE streaming on `/chat`, per-request logging, `/health` reports model reachability + card-index size + vector-DB chunk count
- **Frontend**: Vanilla JS (no build step), 4 tabs (Chat / Import & Analyze / Goldfish / Budget), served by FastAPI from the same origin as the API. Inline `[[Name]]` card refs render as clickable Scryfall links; a left-side panel accumulates referenced cards across the session
- **Card Data**: Scryfall bulk data indexed locally (36,670 cards, 30,538 Legacy-legal, earliest-printing preferred). Fuzzy + word-boundary matching via rapidfuzz
- **Deterministic engines**: Budget substitution and goldfish sampling — pure Python modules that provide exact answers instead of relying on the LLM
- **Evaluation**: Custom 22-case eval dataset across 9 categories (baseline 28.9% → finetuned 61.6%, +32.7%)

## API Endpoints

The FastAPI server (`src/server.py`) exposes these endpoints. LLM-backed endpoints route through Ollama or SageMaker based on `INFERENCE_BACKEND` env var.

**Conversational (LLM-backed, RAG-enriched, card resolution):**
- `POST /chat` — main conversation with optional SSE streaming
- `POST /build-deck` — generate a 75-card decklist from a play-style description
- `POST /analyze-deck` — archetype classification, strengths, weaknesses, meta positioning
- `POST /evaluate-board` — advice on optimal plays given a described board state
- `POST /evaluate-card` — Legacy playability assessment for a card
- `POST /goldfish` — LLM-narrated hand evaluation ("this is keepable because...")
- `POST /budget-sub` — LLM explains budget substitutions with trade-offs

**Deterministic (pure Python, no model calls):**
- `POST /budget-sub/lookup` — curated substitution lookup with real prices
- `POST /budget-tiers` — full / mid / budget versions of a decklist with estimated prices
- `POST /goldfish/draw` — shuffled opening hand with London Mulligan, full card data, mana curve
- `POST /goldfish/stats` — N-sample aggregate stats (up to 100k): land distribution, P(color by turn)
- `POST /import-deck` — parse a decklist from plain text, Moxfield URL, or MTGGoldfish URL
- `GET /card/{name}` — Scryfall card data with fuzzy name resolution
- `GET /card/{name}/search` — fuzzy card search returning top N matches
- `GET /health` — service status (model backend, card index, vector DB)

## Testing

```
pytest tests/            # 133 tests across card index, vector DB, budget engine, goldfish
pytest tests/test_goldfish_engine.py -v
```

## Data Sources

| Source | Usage |
|--------|-------|
| [Scryfall API](https://scryfall.com) | Card data, images, oracle text, legality |
| [MTG Comprehensive Rules](https://magic.wizards.com/en/rules) | Rules knowledge via RAG |
| [MTGGoldfish](https://www.mtggoldfish.com/metagame/legacy) | Metagame percentages, staples, tournament results |
| [MTGTop8](https://www.mtgtop8.com/format?f=LE) | Archetype breakdown, tournament results |
| [mtgdecks.net](https://mtgdecks.net/Legacy) | Decklists, win rates, staple analysis |
| [The Source (MTG Salvation)](https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5) | Archetype primers and in-depth discussion |
| [Moxfield](https://www.moxfield.com) | Decklist browsing and visual tools |

## Course Context

This project is the final project for the "LLMs in Production" course by Christopher Brousseau and Matthew Sharp. It applies skills from all 12 assignments: tokenization, data loading, evaluation, GPU training, LoRA finetuning, model serving, RAG, structured output, prompt optimization, and frontend development.
