# Final Project Plan — The Legacy: AI-Powered MTG Legacy Deck Builder

## Project Vision

An AI-powered application that helps Magic: The Gathering players design, refine, and test **Legacy format** decks that are **unique in the current meta**. The user chats with the bot about their play style, preferences, and goals. The bot curates a deck, explains card choices in the context of the meta, evaluates board states, and lets the player "goldfish" (solitaire test) the deck — all backed by live Scryfall data with card images and full oracle text.

---

## What the Rubric Demands

The final project is worth **100 points** across three pillars:

### I. Model & Inference (40 pts)
| Category | Points | What "Excellent" Looks Like |
|----------|--------|-----------------------------|
| Model Functionality | 20 | Trained model producing meaningful outputs. Includes a **LoRA adapter**. Thoughtful evaluation with a **custom eval dataset**. |
| Innovation & Creativity | 20 | Clear stretch beyond comfort zone. Demonstrates understanding of where the field sits and how it can be improved. |

### II. Production Environment & Programmability (30 pts)
| Category | Points | What "Excellent" Looks Like |
|----------|--------|-----------------------------|
| Environment Setup | 15 | Model deployed in a production environment (local, AWS, etc.). Correctly configured and **accessible via API endpoint**. |
| Inference Pipeline | 15 | Robust, efficient, well-documented pipeline. Optimized for performance. Includes **appropriate sampling method** (temperature, top-k, top-p). |

### III. Documentation & Presentation (30 pts)
| Category | Points | What "Excellent" Looks Like |
|----------|--------|-----------------------------|
| Technical Documentation | 15 | Comprehensive docs covering model, inference pipeline, API, deployment process, and sampling method. |
| Demo & Presentation | 15 | Clear, concise, engaging demonstration of the project. |

---

## Skills From the Course That Apply

| Assignment | Skill | How It Applies to The Legacy |
|------------|-------|------------------------------|
| 0-1 | Tokenization | MTG has unique vocabulary (mana symbols, keywords, card names) that tokenizers need to handle |
| 2 | DataLoader | Loading card data, decklists, meta snapshots, and rules text for training |
| 3 | Evaluation | Custom eval: does the bot build legal decks? Does it respect the meta? Are card choices justified? |
| 4 | Sagemaker/GPUs | GPU infrastructure for training and potentially serving |
| 5-6 | Training & Finetuning | LoRA finetuning on MTG rules, card interactions, deck archetypes, and meta analysis |
| 7 | Serving | API endpoint for the deck builder service |
| 8 | Vector DB & RAG | RAG over the comprehensive rules, card database, and meta reports |
| 9 | Structured Output | Structured decklist output (60 cards main, 15 sideboard, proper formatting) |
| 10 | Prompt Optimization | Tuning prompts for deck-building advice quality |
| 11 | Frontend | Chat UI with card images, decklist display, goldfish simulator |

Book chapters most relevant:
- **Ch 5** (Training) — LoRA/QLoRA for MTG domain adaptation
- **Ch 6** (Services) — API design, streaming, RAG pipeline for rules/cards
- **Ch 7** (Prompt Engineering) — Tool use for Scryfall API calls, structured deck output
- **Ch 8** (Applications) — Chat UI with history, streaming, RAG integration
- **Ch 9** (Llama Project) — End-to-end reference for the build

---

## Application Features

### 1. Deck Building Chat
The core experience. The user describes what they want and the bot builds a deck through conversation:

- **Play style interview**: "I like controlling the board and winning with a combo finish"
- **Budget and card pool**: "I own these dual lands..." or "No budget limit"
- **Meta positioning**: "I want to be good against Reanimator and Death & Taxes"
- **Card-by-card reasoning**: The bot explains why each card is included, what it beats, what it loses to
- **Iterative refinement**: "What if I cut the Dazes for more removal?"

Output is a structured 75-card decklist (60 main + 15 sideboard) with card images pulled from Scryfall.

### 2. Meta Awareness
The bot understands the current Legacy metagame:

- Top decks and their archetypes (Reanimator, Delver, Death & Taxes, Lands, Storm, etc.)
- Win rates and matchup data
- Recent bans/unbans and their impact
- How to position a deck to exploit meta weaknesses
- What makes a deck "unique" vs. a known archetype

### 3. Board State Analysis
Given a described board state, the bot can:

- Assess who is ahead and why
- Suggest optimal plays or lines
- Identify threats that need answering
- Evaluate sequencing (e.g., "play around Daze by leading with the cheaper spell")

### 4. Goldfish Mode
Solitaire testing of the deck:

- Draw an opening hand, decide keep/mulligan
- Play out turns against no opponent (goldfish)
- Track mana curve, land drops, spell sequencing
- Assess consistency: "How often does this deck have a turn-1 play?"
- Simulate multiple hands to get statistical feel for the deck

### 5. Rules Knowledge
Deep understanding of MTG Comprehensive Rules:

- Correct card interaction rulings
- Stack resolution, priority, timing
- Legacy-specific rules (e.g., how Daze, Force of Will, Wasteland interact)
- Explain complex interactions when asked

### 6. Deck Import & Analysis
Users can paste an existing decklist and receive a full analysis:

- **Deck identification**: Classify the deck by archetype (Delver, Storm, D&T, etc.) or flag it as a unique brew
- **Strengths & weaknesses**: What matchups does this deck win? Where does it struggle?
- **Meta positioning**: How well does this list attack the current metagame? What percentage of the field is favorable vs. unfavorable?
- **Card-by-card evaluation**: Flag underperforming cards, suggest swaps, identify missing staples
- **Mana base analysis**: Is the mana base correct? Enough colored sources? Too many/few lands? Fetchland configuration optimal?
- **Sideboard audit**: Does the sideboard cover the top matchups? Are there gaps?
- **Comparison to known lists**: How does this list differ from the "stock" version? Are the deviations intentional meta calls or mistakes?
- **Suggested improvements**: Concrete changes with reasoning

### 7. Budget Substitutions
For players who can't afford full Legacy mana bases (Reserved List dual lands, etc.):

- **Automatic budget alternatives**: Given a decklist, suggest the cheapest functional replacements for expensive cards
- **Trade-off transparency**: Honestly explain what you lose with each substitution (e.g., "Watery Grave instead of Underground Sea costs 2 life per use — this matters more against aggressive decks")
- **Budget tiers**: Offer full-budget, mid-budget, and optimal versions of any deck
- **Reserved List awareness**: Know which cards can never be reprinted and which have reasonable alternatives
- **Cost tracking**: Estimate total deck cost using Scryfall/TCGPlayer price data
- **Proxy-friendly mode**: For LGS events that allow proxies, identify which expensive cards to proxy vs. own

### 8. Future Set Consideration
When new sets are spoiled or released:

- **Card evaluation for Legacy**: Given a spoiled card, assess whether it's Legacy-playable using the format's power-level criteria (mana efficiency, card advantage, disruption, clock, resilience)
- **Deck fit analysis**: "Would this new card slot into Dimir Tempo? What would it replace?"
- **Meta impact prediction**: "If this card sees play, how does it shift matchups? Which decks get better/worse?"
- **Historical comparison**: "This card is similar to [X] which saw play in [deck] during [era]"
- **Watchlist**: Track upcoming set releases and flag cards with Legacy potential as they're spoiled
- **Ban risk assessment**: "This card does [X] which historically has gotten cards banned in Legacy"

---

## Data Sources

### Data Files (Already Built)

| File | Size | Contents |
|------|------|----------|
| `data/comprehensive-rules.txt` | ~943 KB, 9,274 lines | Full MTG Comprehensive Rules (Feb 2026). Will be chunked by rule section for RAG. |
| `data/scryfall-cards.json` | ~508 MB (gitignored) | Complete Scryfall card database (all default cards). Card names, oracle text, mana costs, types, legality, image URIs. Download separately via Scryfall bulk data API. |
| `data/legacy-deck-history.md` | ~6,170 lines | 54 Legacy archetypes with full 75-card decklists, meta shares, win rates, matchups, cost estimates, historical timelines (2004-2026), ban impacts, similarity analysis. Includes a variant index mapping ~420 deck names across 65 parent categories. |
| `data/archetype-guide.md` | ~2,113 lines | Comprehensive guide to all 32 parent archetypes with 200+ variants. Each archetype has overview, key cards with Scryfall links, detailed variant sections, matchup analysis, and sideboard guide. |
| `data/mtg-slang.md` | 726 lines, 346 entries | MTG slang dictionary across 5 categories: gameplay, card nicknames, archetypes, strategy, Legacy-specific. Each entry has definition, related cards, and cross-references. |
| `data/legacy-basics.md` | Guide | Legacy format overview: rules, card pool, complete ban list with reasons, staples, metagame, history, strategic triangle, play patterns, and glossary. Includes Scryfall card reference links. |
| `data/deckbuilding-guide.md` | Guide | Deckbuilding principles from Reid Duke: mana base construction, blue card counts, Force of Will math, sideboarding, card evaluation, budget substitutions. Includes Scryfall card reference links with side-by-side budget comparisons. |
| `data/legacy-analysis.md` | Analysis | Current meta analysis from MTGGoldfish (1564 decks), MTGTop8 (555 decks). Win rates, staple usage, cost analysis, tournament results, format trends. Deep dives on tier 1 decks, 9x9 matchup matrix, sideboard hate matrix, historical meta evolution (2011-2026), brewing opportunities. Includes Scryfall card reference links. |

### Live Data Sources

| Source | Usage | Integration |
|--------|-------|-------------|
| [Scryfall API](https://scryfall.com) | Card search, images, oracle text, legality, prices | Deterministic tool layer (API calls from FastAPI, not model) |
| [MTGGoldfish](https://www.mtggoldfish.com/metagame/legacy) | Meta %, staples, deck prices, 5-0 lists, weekly analysis | RAG (periodic scrape into vector DB) |
| [MTGTop8](https://www.mtgtop8.com/format?f=LE) | Archetype breakdown, tournament results | RAG (periodic scrape into vector DB) |
| [mtgdecks.net](https://mtgdecks.net/Legacy) | Win rates, decklists, staple analysis | RAG (periodic scrape into vector DB) |
| [The Source](https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5) | Archetype primers, in-depth discussion | Training data source for LoRA |
| [Moxfield](https://www.moxfield.com) | Decklist browsing, visual tools | Reference for users; potential import source |

### Training Data (To Be Built)
- Synthetic Q&A pairs from comprehensive rules
- Deck-building rationale extracted from primers and strategy articles
- Card evaluation discussions from The Source
- Matchup guides and sideboard plans
- Budget substitution knowledge (card-to-card mappings with trade-off explanations)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Gradio)                     │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ Chat UI  │  │ Decklist     │  │ Goldfish Simulator  │    │
│  │ (stream) │  │ Display +    │  │ (hand draw, play    │    │
│  │          │  │ Card Images  │  │  out turns)         │    │
│  └────┬─────┘  └──────┬───────┘  └─────────┬──────────┘    │
└───────┼────────────────┼────────────────────┼───────────────┘
        │                │                    │
        ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                       │
│  /chat  /build-deck  /evaluate-board  /goldfish  /card-search│
└──────┬────────────────────┬─────────────────────────────────┘
       │                    │
       ▼                    ▼
┌──────────────┐    ┌───────────────┐    ┌──────────────────┐
│  Inference   │    │  Vector DB    │    │  Scryfall API    │
│  Engine      │    │  (Chroma/     │    │  (Live card      │
│  (vLLM or    │    │   FAISS)      │    │   data, images,  │
│   Ollama)    │    │               │    │   oracle text)   │
│              │    │  Contents:    │    └──────────────────┘
│  Base Model  │    │  - Comp Rules │
│  + LoRA      │    │  - Meta data  │
│              │    │  - Card rulings│
└──────────────┘    └───────────────┘
```

### Component Breakdown

#### 1. Finetuned Model (Base + LoRA)
- **Base**: Llama 3.2 3B (Legacy is complex — 1B may struggle with nuanced meta reasoning, but 1B is fallback if GPU-constrained)
- **Model size risk mitigation**: A 3B model will not match GPT-4 on complex multi-step reasoning (board state analysis, multi-card interaction chains). The strategy is to compensate with strong RAG context and well-structured prompts — the model reasons over *retrieved facts*, not from memorized weights alone. If 3B still falls short on board state analysis, that feature becomes LLM-assisted rather than LLM-driven (the API layer provides structured game state, the model comments on it). This trade-off will be documented honestly in the evaluation — rubric rewards thoughtful analysis of limitations, not perfection.
- **LoRA trained on**:
  - MTG rules comprehension (Q&A pairs from comprehensive rules)
  - Deck-building rationale (why cards are in decks, matchup reasoning)
  - Card evaluation in Legacy context
  - Structured decklist output format
- **Not trained on** (use RAG/tools instead):
  - Specific card data (changes with new sets — use Scryfall tool)
  - Current meta percentages (changes weekly — use RAG)
- **Training data quality plan**: Synthetic Q&A pairs will be generated in bulk, then a subset (~200-300) will be **hand-reviewed and corrected** before training. A small, accurate dataset beats a large noisy one for LoRA. Curated examples will prioritize: rules edge cases unique to Legacy, deck construction constraints, and matchup reasoning chains.

#### 2. Vector DB (RAG Knowledge Base)
- **Comprehensive Rules**: Chunked by rule section (~400 tokens each), embedded with sentence-transformers
- **Meta Snapshots**: Current top decks, metagame percentages, matchup data
- **Card Rulings**: Official rulings for complex Legacy staples (Force of Will, Brainstorm, etc.)
- **Strategy Content**: Legacy primers, matchup guides, sideboard plans
- **Database**: Chroma (simple, local) or FAISS (fast, lightweight)

#### 3. Scryfall Integration (Deterministic Tool Layer)
Rather than relying on the model to emit structured tool calls (unreliable with small models), the **API layer handles Scryfall calls deterministically**:
- The model's response is parsed for card names (regex + fuzzy match against a local card name index)
- The API layer resolves card names to Scryfall data automatically
- Card data (oracle text, mana cost, type, legality, image URIs) is attached to the response as structured metadata
- The frontend renders card images and oracle text from this metadata
- For explicit card searches ("find me a 1-mana blue cantrip"), the API layer translates the request into a Scryfall query and injects results into the next prompt as context
- Fallback: if the model names a card that doesn't exist or isn't Legacy-legal, the API layer flags it and asks the model to reconsider
- This hybrid approach gets tool-use benefits without requiring the model to learn a tool-calling protocol

#### 4. Goldfish Engine (Tiered Scope)
The goldfish engine is built in tiers so the core rubric requirements are met first:

**Tier 1 (MVP — must ship):**
- Represent a deck as a shuffled list of card objects (from Scryfall data)
- Draw opening hand (7 cards), support London Mulligan (put N back, draw 7-N)
- Display hand with card images
- Basic statistics over N sample hands: land count distribution, mana curve of opening hand, color availability by turn assuming one land drop per turn
- LLM comments on the hand ("this is a keepable hand because...")

**Tier 2 (Target — ship if time allows):**
- Simplified turn engine: untap, draw, play one land, cast spells by mana cost
- Track: mana available, cards in hand, permanents on "board" (name list)
- Play out 5-7 turns of goldfishing
- Stats: average turn to deploy key threats, mana efficiency per turn

**Tier 3 (Stretch — nice to have):**
- Mana ability resolution (fetchlands, dual lands, mana rocks)
- Spell sequencing heuristics (play cantrips before committing)
- Combo detection (e.g., "assembled Marit Lage on turn 3")
- Full statistical summary over N simulated games

#### 5. API Layer (FastAPI)
| Endpoint | Purpose |
|----------|---------|
| `POST /chat` | Main conversation endpoint, streaming response |
| `POST /build-deck` | Generate a full 75-card decklist from conversation context |
| `POST /analyze-deck` | Import a decklist (text or URL), return full analysis |
| `POST /evaluate-board` | Analyze a described board state |
| `POST /goldfish` | Run N goldfish hands, return stats |
| `POST /budget-sub` | Given a decklist, return budget substitutions with trade-offs |
| `POST /evaluate-card` | Assess a card's Legacy playability and deck fit |
| `GET /card/{name}` | Proxy to Scryfall for card data + image |

Sampling parameters exposed: temperature, top-k, top-p, max tokens.

**Deployment target**: Local deployment using **Ollama** as the primary inference engine. Ollama supports GGUF quantized models, runs on consumer hardware, and exposes an OpenAI-compatible API out of the box. This is the simplest path to a working endpoint and avoids ongoing cloud costs. If the demo environment needs to be accessible remotely, the Ollama server can be fronted by an ngrok tunnel or deployed to a Sagemaker instance as a fallback.

#### 6. Frontend (Gradio)
- **Chat tab**: Streaming conversation with the deck-building bot
- **Decklist tab**: Visual decklist with card images (grid or list), mana curve chart, color distribution
- **Goldfish tab**: Draw hands, play out turns, see stats across N simulations
- Card hover/click shows full Scryfall image and oracle text

---

## Sampling Strategy (Rubric Requirement)

The rubric specifically calls out "appropriate sampling method" — different tasks within The Legacy need different sampling configurations:

| Task | Temperature | Top-K | Top-P | Rationale |
|------|-------------|-------|-------|-----------|
| **Deck list generation** | 0.3 (low) | 40 | 0.9 | Decks must be legal and coherent. Low randomness prevents hallucinated card names and illegal counts. |
| **Card reasoning / explanation** | 0.5 (medium) | 50 | 0.9 | Needs to be factual but also express nuanced opinions about card choices. |
| **Creative brainstorming** | 0.8 (high) | 80 | 0.95 | "What spicy tech could I play?" benefits from creative, less obvious suggestions. |
| **Rules questions** | 0.1 (very low) | 20 | 0.85 | Rules answers must be deterministic and correct. Near-greedy decoding. |
| **Board state analysis** | 0.4 (low-medium) | 40 | 0.9 | Needs accurate assessment but should consider multiple lines of play. |
| **Deck analysis / import** | 0.3 (low) | 40 | 0.9 | Analysis should be factual and precise. Archetype identification must be correct. |
| **Budget substitutions** | 0.3 (low) | 40 | 0.9 | Substitution recommendations must be real cards with honest trade-off assessments. |
| **Card evaluation (new sets)** | 0.5 (medium) | 50 | 0.9 | Needs factual comparison but also reasoned speculation about format impact. |

The API exposes these as presets (e.g., `mode=precise` vs `mode=creative`) while also allowing manual override. The documentation will explain *why* each preset exists and how temperature/top-k/top-p interact for MTG-specific generation.

Key insight from Ch 7: temperature is applied during softmax over the logit distribution. For MTG, low temperature matters because the model's vocabulary includes thousands of card names — high temperature risks sampling from the long tail of similar-sounding but wrong card names.

---

## Innovation Angle (20% of Grade)

This project stretches beyond the assignments in several ways:

1. **Tool-augmented LLM**: The model uses Scryfall as a live tool — it's not just generating text, it's calling APIs and reasoning about structured card data (Ch 7: Toolformers/ReAct)
2. **Multi-source RAG**: Combines rules, meta data, and strategy content in a single retrieval pipeline — not just one document source
3. **Game state reasoning**: Board state analysis requires multi-step logical reasoning about card interactions, not just knowledge retrieval
4. **Goldfish simulator**: A non-LLM component that provides quantitative deck testing, feeding results back to the LLM for analysis
5. **Domain-specific LoRA**: Finetuning for a highly specialized domain (competitive MTG) where general models have shallow knowledge

---

## Evaluation Strategy

### Custom Eval Dataset
Build a test set covering each capability:

| Category | Example Test Case | Metric |
|----------|-------------------|--------|
| Deck legality | Generated deck is exactly 60 main + 15 side, all Legacy-legal | Pass/fail accuracy |
| Card relevance | Recommended cards match the stated strategy | Expert scoring (1-5) |
| Meta awareness | Bot correctly identifies top meta decks and their weaknesses | Factual accuracy |
| Rules knowledge | "Can I Daze a spell if I have no Islands?" → "No" | Exact match / F1 |
| Board state | Given a known board, does the bot identify the correct play? | Expert scoring (1-5) |
| Uniqueness | Is the deck meaningfully different from known meta lists? | Jaccard distance from top8 lists |
| Deck analysis | Given a known list, does the bot correctly identify archetype, strengths, weaknesses? | Expert scoring (1-5) |
| Budget subs | Are suggested substitutions functional and correctly assessed for trade-offs? | Expert scoring (1-5) |
| Card evaluation | "Is [new card] Legacy-playable?" for known good/bad examples | Accuracy |

### Before/After LoRA Comparison
- Run the same eval set against the base model (no LoRA) and the finetuned model
- Expect significant improvement in rules knowledge, deck structure, and Legacy-specific reasoning
- Report metrics in a table with percentage improvement

---

## Deliverables Checklist

- [ ] **Finetuned model with LoRA adapter**
  - Base: Llama 3.2 (1B or 3B)
  - LoRA trained on MTG rules, deck-building, card evaluation, Legacy meta
  - Weights saved separately, loadable on top of base

- [ ] **Custom evaluation dataset and results**
  - Test cases for deck legality, card relevance, rules, board state, uniqueness
  - Before/after comparison table
  - Analysis of where the model improves and where it still struggles

- [ ] **Deployed API endpoint**
  - FastAPI with /chat, /build-deck, /evaluate-board, /goldfish, /card, /analyze-deck, /budget-sub, /evaluate-card endpoints
  - Streaming support on /chat
  - Scryfall integration as deterministic tool layer
  - Deck import parser (text/Moxfield/MTGGoldfish URL)

- [ ] **Inference pipeline with sampling**
  - Temperature, top-k, top-p controls
  - Streaming token delivery
  - RAG retrieval integrated into the prompt construction

- [ ] **Vector DB with MTG knowledge**
  - Comprehensive rules chunked and embedded
  - Meta snapshots indexed
  - Card rulings and strategy content

- [ ] **Goldfish simulator**
  - Deck loading, shuffling, hand drawing
  - London Mulligan support
  - Turn-by-turn simplified play
  - Statistical summaries over N hands

- [ ] **Deck import & analysis**
  - Paste a decklist or URL, get archetype classification and full analysis
  - Strengths/weaknesses, meta positioning, card-by-card evaluation
  - Mana base audit and sideboard review

- [ ] **Budget substitution engine**
  - Card-to-card replacement mappings with trade-off explanations
  - Budget tiers (full, mid, budget) for any deck
  - Price awareness via Scryfall data

- [ ] **Future set evaluation**
  - Card evaluation framework for Legacy power level
  - Deck fit analysis for spoiled/new cards
  - Historical comparison to similar cards

- [ ] **Frontend (Gradio)**
  - Chat tab with streaming
  - Decklist display with Scryfall card images
  - Deck import tab (paste list or URL for analysis)
  - Goldfish tab with hand visualization
  - Budget mode toggle

- [ ] **Comprehensive documentation**
  - Architecture overview with diagram
  - Training data sources and preparation
  - LoRA training process and hyperparameters
  - API reference
  - Deployment instructions
  - Sampling method explanation
  - Evaluation results and analysis

- [ ] **Demo presentation**
  - Live walkthrough: describe a play style → get a deck → view it → goldfish it
  - Show meta awareness and rules knowledge
  - Explain architectural decisions and trade-offs

---

## Build Order

> **Priority rule**: Phases 1-3 and 6 are **rubric-required** — they cover the LoRA model, eval dataset, API endpoint, inference pipeline, and documentation. Phases 4-5 add polish and innovation. If time gets tight, a working Phase 1-3 with solid docs scores well. Goldfish Tier 1 is quick to build and adds significant demo value, so it's worth doing even under time pressure.

### Phase 1: Data Foundation ✅ (Mostly Complete)
1. ~~Download MTG Comprehensive Rules~~ → `data/comprehensive-rules.txt` (9,274 lines, Feb 2026)
2. ~~Download Scryfall bulk card data~~ → `data/scryfall-cards.json` (508 MB, gitignored)
3. ~~Build MTG slang dictionary~~ → `data/mtg-slang.md` (346 entries, 5 categories)
4. ~~Build Legacy deck history + variant index~~ → `data/legacy-deck-history.md` (54 archetypes, 420 variant mappings)
5. ~~Build archetype guide~~ → `data/archetype-guide.md` (32 parent archetypes, 200+ variants with Scryfall links)
6. ~~Write Legacy basics guide~~ → `data/legacy-basics.md` (with card images, ban list, play patterns)
7. ~~Write deckbuilding guide~~ → `data/deckbuilding-guide.md` (Reid Duke principles, budget comparisons)
8. ~~Write meta analysis~~ → `data/legacy-analysis.md` (matchup matrix, hate matrix, meta evolution)
9. **TODO**: Chunk comprehensive rules by section and embed into vector DB
10. **TODO**: Build card name index from Scryfall data for fuzzy matching
11. **TODO**: Index meta data, deck history, and strategy content into vector DB

### Phase 2: Model
11. Build the LoRA training dataset (Q&A pairs from rules, deck-building rationale, card evaluation, deck analysis, budget substitutions)
12. **Hand-review a curated subset** (~200-300 examples) for accuracy before training
13. Build the evaluation dataset (test cases across all 9 categories — added: deck analysis, budget subs, card evaluation)
14. Run baseline eval against un-finetuned model
15. LoRA finetune on the training set
16. Run eval against finetuned model, compare results
17. **Document honest analysis** of where the model improves and where it still struggles

### Phase 3: Infrastructure
18. Set up Ollama locally serving the finetuned model (GGUF quantized)
19. Build FastAPI layer with all endpoints (/chat, /build-deck, /analyze-deck, /evaluate-board, /goldfish, /budget-sub, /evaluate-card, /card)
20. Integrate RAG retrieval into the chat pipeline
21. Integrate deterministic Scryfall card resolution (parse model output → resolve card names → attach metadata)
22. Build deck import parser (plain text, Moxfield URL, MTGGoldfish URL)
23. Build budget substitution engine (card-to-card mappings with trade-off scoring)
24. Implement streaming on /chat
25. Implement sampling presets (precise, balanced, creative) with per-task defaults

### Phase 4: Goldfish Engine
26. Build Tier 1: deck representation, shuffler, hand draw, London Mulligan, basic stats, LLM commentary
27. Build Tier 2 (if time): simplified turn engine, mana tracking, turn-by-turn play
28. Build Tier 3 (stretch): fetchland resolution, combo detection, full simulation stats

### Phase 5: Frontend & Polish
29. Build Gradio chat interface with streaming
30. Build decklist display with card images from Scryfall
31. Build deck import tab (paste list or URL → analysis view)
32. Build goldfish tab (Tier 1 at minimum: hand display + stats)
33. Add budget mode toggle
34. Connect all tabs to the API

### Phase 6: Documentation & Demo
35. Write technical documentation (architecture, training, API reference, deployment, sampling rationale, eval analysis)
36. Record/prepare demo presentation (play style → deck → view → goldfish → explain decisions)
37. Final eval run with polished model

---

## Known Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **3B model can't do complex board state reasoning** | Board state feature underperforms | Compensate with RAG context injection. Document the limitation honestly — the rubric rewards thoughtful analysis of trade-offs. Downgrade to "LLM-assisted" board state (structured state from API, model comments) rather than "LLM-driven." |
| **Model hallucinates card names** | Illegal/nonexistent cards in decklists | Deterministic Scryfall validation layer catches this. Every card name in output is verified against the card index before reaching the user. Invalid names trigger a re-prompt. |
| **Training data quality is poor** | LoRA doesn't improve over base model | Hand-curate a subset before training. Run eval early and iterate on data before over-investing in training runs. Small + accurate > large + noisy. |
| **Goldfish engine scope creep** | Takes too much time away from rubric essentials | Tiered scope. Tier 1 (hand draw + stats) is 1-2 days of work and still demo-worthy. Tiers 2-3 are explicitly stretch goals. |
| **Scryfall rate limiting** | API calls slow down or get blocked during demo | Cache Scryfall responses locally. Pre-fetch bulk data for Legacy-legal cards. The card name index is local — only image fetches and new-set cards hit the live API. |
| **Demo environment issues** | Model or server crashes during live demo | Pre-record a backup demo video. Have a known-good conversation cached that can be replayed. Test the full flow end-to-end before presenting. |
