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

- [ ] Build LoRA training dataset
  - [ ] Q&A pairs from comprehensive rules
  - [ ] Deck-building rationale (why cards are in decks, matchup reasoning)
  - [ ] Card evaluation in Legacy context
  - [ ] Deck analysis examples (archetype identification, strengths/weaknesses)
  - [ ] Budget substitution examples (card-to-card with trade-offs)
- [ ] Hand-review curated subset (~200-300 examples) for accuracy
- [ ] Build evaluation dataset
  - [ ] Deck legality (60 main + 15 side, all Legacy-legal)
  - [ ] Card relevance (recommended cards match stated strategy)
  - [ ] Meta awareness (correctly identifies top decks and weaknesses)
  - [ ] Rules knowledge (correct rulings on card interactions)
  - [ ] Board state analysis (identifies correct play given a board)
  - [ ] Uniqueness (deck is meaningfully different from known lists)
  - [ ] Deck analysis (correctly classifies archetype, strengths, weaknesses)
  - [ ] Budget substitutions (functional replacements with honest trade-offs)
  - [ ] Card evaluation (correctly assesses Legacy playability)
- [ ] Run baseline eval against un-finetuned model
- [ ] LoRA finetune on training set
- [ ] Run eval against finetuned model, compare results
- [ ] Document honest analysis of improvements and remaining weaknesses

## Phase 3: Infrastructure

- [ ] Set up Ollama locally serving finetuned model (GGUF quantized)
- [ ] Build FastAPI layer
  - [ ] `POST /chat` — main conversation, streaming
  - [ ] `POST /build-deck` — generate 75-card decklist
  - [ ] `POST /analyze-deck` — import + analyze a decklist
  - [ ] `POST /evaluate-board` — board state analysis
  - [ ] `POST /goldfish` — run N goldfish hands
  - [ ] `POST /budget-sub` — budget substitutions
  - [ ] `POST /evaluate-card` — card Legacy playability
  - [ ] `GET /card/{name}` — Scryfall proxy
- [ ] Integrate RAG retrieval into chat pipeline
- [ ] Integrate deterministic Scryfall card resolution
  - [ ] Parse card names from model output (regex + fuzzy match)
  - [ ] Resolve to Scryfall data (oracle text, mana cost, type, legality, image)
  - [ ] Attach as structured metadata to response
  - [ ] Flag invalid/non-Legacy-legal cards for re-prompt
- [ ] Build deck import parser
  - [ ] Plain text decklist
  - [ ] Moxfield URL
  - [ ] MTGGoldfish URL
- [ ] Build budget substitution engine
  - [ ] Card-to-card replacement mappings
  - [ ] Trade-off scoring (what you lose with each sub)
  - [ ] Budget tier generation (full, mid, budget)
  - [ ] Price data from Scryfall
- [ ] Implement streaming on /chat
- [ ] Implement sampling presets
  - [ ] Precise (temp 0.1-0.3) — rules, deck generation, analysis
  - [ ] Balanced (temp 0.4-0.5) — card reasoning, board state
  - [ ] Creative (temp 0.8) — brainstorming, spicy tech suggestions
  - [ ] Manual override option

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
