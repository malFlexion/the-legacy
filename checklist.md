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

- [x] Build LoRA training dataset (1,449 pairs across 7 categories)
  - [x] Q&A pairs from comprehensive rules (422 pairs)
  - [x] Deck-building rationale (217 pairs)
  - [x] Card evaluation in Legacy context (294 pairs)
  - [x] Deck analysis examples (146 pairs)
  - [x] Budget substitution examples (121 pairs)
  - [x] Conversation flow examples (119 pairs)
  - [x] Board state analysis examples (130 pairs)
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
  - [ ] Re-run finetune and eval

## Phase 3: Infrastructure

- [ ] Set up Ollama locally serving finetuned model (GGUF quantized)
  - [ ] Merge LoRA into base model (uncomment notebook merge cell)
  - [ ] Convert to GGUF: `python llama.cpp/convert_hf_to_gguf.py merged-model --outtype q4_0`
  - [ ] Create Ollama model: `ollama create the-legacy -f Modelfile`
- [ ] Deploy SageMaker endpoint for remote demo
  - [ ] Merge LoRA adapter into base model and push to HF
  - [ ] Run `scripts/deploy_sagemaker.py --create`
  - [ ] Verify with `scripts/deploy_sagemaker.py --test`
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
- [ ] Build budget substitution engine
  - [ ] Card-to-card replacement mappings
  - [ ] Trade-off scoring (what you lose with each sub)
  - [ ] Budget tier generation (full, mid, budget)
  - [ ] Price data from Scryfall
- [x] Implement streaming on /chat (SSE via Ollama backend)
- [x] Implement sampling presets (per-endpoint temperature tuning)
  - [x] Precise (temp 0.2) — /build-deck, /analyze-deck
  - [x] Balanced (temp 0.3-0.4) — /chat, /budget-sub, /evaluate-card, /evaluate-board
  - [x] Creative (temp 0.5) — /goldfish
  - [x] Manual override via `temperature` field on all requests

## Phase 4: Goldfish Engine

### Tier 1 (MVP — must ship)
- [ ] Deck representation (shuffled list of card objects from Scryfall)
- [ ] Draw opening hand (7 cards) with card images
- [ ] London Mulligan (put N back, draw 7-N)
- [ ] Basic stats over N sample hands
  - [ ] Land count distribution
  - [ ] Mana curve of opening hand
  - [ ] Color availability by turn (assuming one land drop/turn)
- [ ] LLM commentary on hand ("this is keepable because...")

### Tier 2 (Target — if time allows)
- [ ] Simplified turn engine (untap, draw, play land, cast spells by CMC)
- [ ] Track mana available, cards in hand, permanents on board
- [ ] Play out 5-7 turns
- [ ] Stats: average turn to deploy key threats, mana efficiency/turn

### Tier 3 (Stretch — nice to have)
- [ ] Mana ability resolution (fetchlands, dual lands, mana rocks)
- [ ] Spell sequencing heuristics (cantrips before committing)
- [ ] Combo detection ("assembled Marit Lage on turn 3")
- [ ] Full statistical summary over N simulated games

## Phase 5: Frontend (Gradio)

- [ ] Chat tab
  - [ ] Streaming conversation with deck-building bot
  - [ ] Card images rendered inline from Scryfall metadata
  - [ ] Chat history maintained
- [ ] Decklist tab
  - [ ] Visual decklist with card images (grid or list)
  - [ ] Mana curve chart
  - [ ] Color distribution
  - [ ] Card hover/click shows full Scryfall image + oracle text
- [ ] Deck import tab
  - [ ] Paste decklist text or URL
  - [ ] Archetype classification + full analysis view
  - [ ] Mana base audit, sideboard review, suggested improvements
- [ ] Goldfish tab
  - [ ] Hand display with card images
  - [ ] Mulligan button
  - [ ] Stats display
  - [ ] LLM commentary
- [ ] Budget mode toggle
  - [ ] Switch between full/mid/budget versions of any deck
  - [ ] Show trade-off explanations
- [ ] Connect all tabs to API

## Phase 6: Documentation & Demo

- [ ] Technical documentation
  - [ ] Architecture overview with diagram
  - [ ] Training data sources and preparation process
  - [ ] LoRA training process and hyperparameters
  - [ ] API reference (all endpoints, parameters, response formats)
  - [ ] Deployment instructions (how to reproduce)
  - [ ] Sampling method explanation (why each preset exists)
  - [ ] Evaluation results and analysis
- [ ] Demo presentation
  - [ ] Live walkthrough: play style → deck → view → goldfish
  - [ ] Show meta awareness and rules knowledge
  - [ ] Show deck import and analysis
  - [ ] Explain architectural decisions and trade-offs
  - [ ] Pre-record backup video in case of live issues
- [ ] Final eval run with polished model
