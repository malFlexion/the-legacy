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
    training/                   # LoRA training dataset (1,449 pairs across 7 categories)
      rules_qa.jsonl            #   Rules Q&A (422 pairs)
      card_evaluation.jsonl     #   Card playability assessment (294 pairs)
      deckbuilding_rationale.jsonl  # Deck-building rationale (217 pairs)
      deck_analysis.jsonl       #   Archetype ID, meta positioning (146 pairs)
      board_state_analysis.jsonl #  Opening hands, board states, sequencing (130 pairs)
      conversation_flow.jsonl   #   Deck consultation dialogues (119 pairs)
      budget_substitutions.jsonl #  Budget alternatives, upgrade paths (121 pairs)
  src/
    build_vectordb.py           # Builds ChromaDB vector database (719 chunks)
    card_index.py               # Card name index for fuzzy matching (36,670 cards)
  tests/
    test_card_index.py          # 32 tests for card index
    test_build_vectordb.py      # 47 tests for vector DB builder
  notebooks/
    finetune_legacy.ipynb       # LoRA finetuning notebook (SageMaker)
    eval_report.json            # Evaluation results (Round 1)
  scripts/                      # Training data generator scripts
  notes/
    assignment-00.md ... assignment-11.md   # Course assignment notes
    chapter-01.md ... chapter-12.md         # Book chapter notes
    final-project.md                        # Rubric breakdown
  vectordb/                     # ChromaDB vector database (gitignored, rebuild with src/build_vectordb.py)
  checklist.md                  # Project progress checklist
  final-project-plan.md         # Detailed implementation plan
  README.md                     # This file
```

## Training Results (Round 1)

LoRA finetune of Llama 3.2 1B on 1,449 training pairs (5 epochs, rank 16, loss 1.29).

| Category | Baseline | Finetuned | Change |
|---|---|---|---|
| deck_legality | 100% | 100% | — |
| rules_knowledge | 58% | 83% | **+25%** |
| deck_analysis | 17% | 67% | **+50%** |
| card_relevance | 0% | 50% | **+50%** |
| card_evaluation | 13% | 29% | +17% |
| board_state | 75% | 50% | -25% |
| meta_awareness | 67% | 33% | -33% |
| budget_subs | 10% | 10% | — |
| **Overall** | **43.1%** | **54.8%** | **+11.7%** |

**Key findings**: Strong gains in deck analysis and card relevance. Regressions in meta awareness and board state — the model hallucates confidently rather than hedging. Round 2 will focus on fixing regressions, expanding weak categories, and adding negative examples.

## Technology Stack

- **Model**: Llama 3.2 1B + LoRA adapter finetuned on 1,449 MTG domain pairs (SageMaker, Tesla T4)
- **RAG**: Vector DB (Chroma/FAISS) over comprehensive rules, meta data, and strategy content
- **Inference**: Ollama (local) with FastAPI wrapper
- **Frontend**: Gradio with chat, decklist display, and goldfish simulator tabs
- **Card Data**: Live Scryfall API integration with local caching
- **Evaluation**: Custom 22-case eval dataset across 9 categories (deck legality, card relevance, rules knowledge, meta awareness, board state, uniqueness, deck analysis, budget subs, card evaluation)

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
