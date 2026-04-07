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
    scryfall-cards.json         # Complete Scryfall card database (~508MB)
    mtg-slang.json              # 226-entry MTG slang dictionary
    legacy-deck-history.json    # 54 Legacy archetypes with decklists, history, meta data
    legacy-basics.md            # Legacy format guide
    deckbuilding-guide.md       # Deckbuilding principles (Reid Duke)
    legacy-analysis.md          # Meta analysis from MTGTop8, MTGGoldfish, etc.
  notes/
    assignment-00.md ... assignment-11.md   # Course assignment notes
    chapter-01.md ... chapter-12.md         # Book chapter notes
    final-project.md                        # Rubric breakdown
  final-project-plan.md        # Detailed implementation plan
  README.md                    # This file
```

## Technology Stack

- **Model**: Llama 3.2 (1B or 3B) + LoRA adapter finetuned on MTG domain data
- **RAG**: Vector DB (Chroma/FAISS) over comprehensive rules, meta data, and strategy content
- **Inference**: Ollama (local) with FastAPI wrapper
- **Frontend**: Gradio with chat, decklist display, and goldfish simulator tabs
- **Card Data**: Live Scryfall API integration with local caching
- **Evaluation**: Custom eval dataset covering deck legality, card relevance, rules knowledge, meta awareness, and board state analysis

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
