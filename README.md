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
    training/                   # LoRA training dataset (1,546 pairs, Round 2)
      rules_qa.jsonl            #   Rules Q&A (422 pairs)
      card_evaluation.jsonl     #   Card playability assessment (301 pairs)
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
    server.py                   # FastAPI server (chat, card lookup, RAG, streaming, Ollama/SageMaker)
    deck_parser.py              # Deck import parser (plain text, Moxfield, MTGGoldfish)
    build_vectordb.py           # Builds ChromaDB vector database (719 chunks)
    card_index.py               # Card name index for fuzzy matching (36,670 cards)
    budget_engine.py            # Curated budget substitution engine with Scryfall prices
    goldfish_engine.py          # Deterministic deck sampling, London Mulligan, aggregate stats
  scripts/
    deploy_sagemaker.py         # Deploy/manage SageMaker endpoint (--create/--delete/--status/--test)
    merge_and_convert.py        # Merge LoRA + GGUF convert (Ollama) or push to HF (SageMaker)
    audit_training_data.py      # Cross-reference training pairs against Scryfall for factual errors
    fix_training_data.py        # Apply audit fixes (duplicates, banned cards, factual errors)
    gen_round2_data.py          # Generate Round 2 training pairs from project data files
  tests/
    test_card_index.py          # 32 tests for card index
    test_build_vectordb.py      # 47 tests for vector DB builder
    test_budget_engine.py       # 22 tests for budget substitution engine
    test_goldfish_engine.py     # 32 tests for goldfish engine (133 tests total)
  notebooks/
    finetune_legacy.ipynb       # LoRA finetuning notebook (SageMaker)
    eval_report.json            # Evaluation results (Round 2, 61.6% finetuned)
    lora-legacy/                # Checkpoint outputs (gitignored)
  Modelfile                     # Ollama model config with Llama 3.2 chat template
  notes/
    assignment-00.md ... assignment-11.md   # Course assignment notes
    chapter-01.md ... chapter-12.md         # Book chapter notes
    final-project.md                        # Rubric breakdown
    development/
      progress.md                           # Running dev notes (dataset, training)
      round1-analysis.md                    # Honest analysis of Round 1 results
      ollama-deployment.md                  # Walkthrough: merge → GGUF → ollama serve
      sagemaker-deployment.md               # Walkthrough: merge+push → SageMaker endpoint
  vectordb/                     # ChromaDB vector database (gitignored, rebuild with src/build_vectordb.py)
  checklist.md                  # Project progress checklist
  final-project-plan.md         # Detailed implementation plan
  README.md                     # This file
```

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

- **Model**: Llama 3.2 1B + LoRA adapter finetuned on 1,546 MTG domain pairs (SageMaker, Tesla T4)
- **RAG**: Vector DB (Chroma) over comprehensive rules, meta data, and strategy content
- **Inference**: Ollama (local GGUF) or SageMaker endpoint (TGI on ml.g5.xlarge)
- **API**: FastAPI server with RAG retrieval, streaming, and deterministic card resolution
- **Frontend**: Gradio with chat, decklist display, and goldfish simulator tabs (planned)
- **Card Data**: Scryfall bulk data indexed locally (36,670 cards with fuzzy matching)
- **Deterministic engines**: Budget substitution and goldfish sampling — pure Python modules that provide exact answers instead of relying on the LLM
- **Evaluation**: Custom 22-case eval dataset across 9 categories

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
