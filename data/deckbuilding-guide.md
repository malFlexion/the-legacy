# Legacy Deckbuilding Guide

> **See also**: [Legacy Basics](legacy-basics.md) | [Meta Analysis](legacy-analysis.md) | [Archetype Guide](archetype-guide.md) | [Deck History & Variant Index](legacy-deck-history.md) | [MTG Slang](mtg-slang.md)

*Based on Reid Duke's articles on TCGPlayer and Ultimate Guard, supplemented with format-specific principles.*

## Philosophy

> "Legacy offers a boundless world of possibilities. It's MTG's biggest sandbox! In most formats, it's best to identify the most powerful cards and build around them. But Legacy's card pool is so deep that many cards can become gamewinners with the right support." — Reid Duke

The most obvious powerful cards are held in check when players choose their interactive spells with them in mind. When Murktide Regent dominated, the format responded with "a major uptick in Pyroblasts, Snuff Outs and Swords to Plowshares." Legacy is self-correcting — if you understand the meta, you can always find an angle.

## Step 1: Choose Your Strategy

### The Archetype Spectrum
Legacy decks fall along a spectrum from "fair" to "unfair":

- **Fair**: Wins through individually powerful cards, card advantage, and incremental edges. Plays "normal" Magic — lands, creatures, spells, combat.
- **Unfair**: Wins by breaking the rules of normal Magic — cheating on mana, putting cards into play without casting them, or winning without attacking.

### Fair Strategies
| Type | Description | Examples |
|------|-------------|----------|
| **Tempo** | Deploy cheap threat, protect it with free countermagic and mana denial | Dimir Tempo, Izzet Delver |
| **Control** | Answer everything, win with whatever's left | Beanstalk Control, Jeskai Control, Miracles |
| **Midrange** | Value-oriented, grindy, play the best cards at each mana cost | Ocelot Pride Midrange, Jund |
| **Hatebears/Taxes** | Disruptive creatures that slow the opponent | Death and Taxes, Maverick |

### Unfair Strategies
| Type | Description | Examples |
|------|-------------|----------|
| **Combo** | Combine specific cards to win on the spot | Storm, Doomsday, Oops! All Spells |
| **Cheat** | Put expensive things into play for free | Sneak and Show, Reanimator |
| **Prison** | Lock the opponent out of playing Magic | Red Stompy, Eldrazi, Lands |

### Choosing What's Right for You
- Do you like making decisions every turn? → **Tempo or Control**
- Do you like puzzles and deterministic wins? → **Combo (Storm, Doomsday)**
- Do you like turning creatures sideways? → **Midrange or Tribal**
- Do you like tilting your opponents? → **Prison or Taxes**
- Do you like winning on turn 1? → **Belcher, Oops**

## Step 2: Build Your Mana Base

> "What's the plan for casting your spells, and how are you going to leverage your mana base to your advantage?" — Reid Duke

This is the **first critical decision** in Legacy deckbuilding.

### Land Count Guidelines
| Deck Type | Land Count | Why |
|-----------|-----------|-----|
| Aggressive / Tempo | 18-20 | Cantrips (Brainstorm, Ponder) compensate for fewer lands. Delver runs ~15 colored sources. |
| Midrange | 22-24 | Need to curve out consistently to turns 3-4 |
| Control | 24-27 | Must hit land drops every turn. "Tons of basic lands." |
| Combo | 14-18 | Replace lands with fast mana (Lotus Petal, Chrome Mox, LED) |
| Prison/Stompy | 20-24 | Ancient Tomb + City of Traitors provide acceleration |

### Adjustments
- **-1 land per 4 mana creatures** (Noble Hierarch, Birds of Paradise)
- **-1 land per 4 cantrips** (Brainstorm, Ponder, Mishra's Bauble)
- Core principle from Gabriel Nassif: **"Don't cheat on lands!"**

### Colored Mana Source Requirements
| When You Need It | Sources Needed | Consistency |
|-----------------|----------------|-------------|
| Turn 1 (e.g., Delver of Secrets) | 14+ sources | ~86% |
| Turn 2 double-colored (e.g., Counterspell) | 20+ sources | ~85% |
| Splash color | 8-10 sources | Acceptable for non-critical spells |

### The Three Mana Base Questions

**1. How do you handle mana denial?**

![Blood Moon](https://api.scryfall.com/cards/named?exact=Blood+Moon&format=image&version=small) | ![Back to Basics](https://api.scryfall.com/cards/named?exact=Back+to+Basics&format=image&version=small)

Legacy has Wasteland, Daze, Blood Moon, and Back to Basics. You need a plan:
- **Against Wasteland**: Fetch basic lands. Run 2-4 basics minimum.
- **Against Blood Moon**: Keep fetchlands uncracked. Fetch basics early if Blood Moon is likely.
- **Against Daze**: Count your mana carefully. Play around it or force them to use it on less important spells.

**2. When do you need acceleration?**
- **Turn 1**: Requires Ancient Tomb, City of Traitors, Lotus Petal, Chrome Mox, or Simian/Elvish Spirit Guide
- **Turn 2-3**: Green acceleration (Noble Hierarch, Birds of Paradise) or artifact mana (Mox Diamond)

**3. What dual lands do you need?**
- Each color pair has one dual land (e.g., Underground Sea = U/B, Volcanic Island = U/R)
- Run 2-4 copies of your primary dual, 1-2 of secondary
- Fetchlands that find your duals are critical (Polluted Delta finds Underground Sea AND Island)
- Budget alternative: Shock lands (Watery Grave) work but cost 2 life per use

## Step 3: The Blue Card Question

### Brainstorm and Ponder

![Brainstorm](https://api.scryfall.com/cards/named?exact=Brainstorm&format=image&version=small) | ![Ponder](https://api.scryfall.com/cards/named?exact=Ponder&format=image&version=small)

> "Brainstorm and Ponder are awesome, and you should try to play with them. More than that, you should probably have a very good reason if you're going to leave home without them." — Reid Duke

These cards "vastly improve the consistency of your deck, and help you find your key cards." In Legacy, you face everything from turn-1 combo to prison to fair creature decks — you need different answers for each, and cantrips find the right answer.

**If you're playing blue**: 4 Brainstorm + 4 Ponder is nearly automatic.

**If you're not playing blue**: You need a very good reason. Non-blue decks compensate with:
- Raw power (![Ancient Tomb](https://api.scryfall.com/cards/named?exact=Ancient+Tomb&format=image&version=small) + ![Chalice of the Void](https://api.scryfall.com/cards/named?exact=Chalice+of+the+Void&format=image&version=small))
- Tutors (Green Sun's Zenith, Goblin Matron)
- Redundancy (lots of similar effects)

### Force of Will

![Force of Will](https://api.scryfall.com/cards/named?exact=Force+of+Will&format=image&version=small)

> "Force of Will is awesome, and makes you feel much better heading into the unknown. It's particularly great right now, as you need a plan against decks that do powerful things on turn one." — Reid Duke

**When to play it**: Almost always if you're in blue. It's the format's safety valve against unfair decks.

**The blue card count constraint**: Force of Will requires pitching a blue card. You need:
- **Minimum 19 blue cards** in your deck
- **Preferably 23-24 blue cards**
- **Check sideboard plans** — after boarding, make sure you're not dropping below 19 in any matchup

**When to sideboard it out**: "It can be bad in grindy matchups, or against opponents who have tons of Pyroblasts." Against fair decks where the game goes long, paying 1 life + a card is too costly.

### Wasteland and Daze

![Wasteland](https://api.scryfall.com/cards/named?exact=Wasteland&format=image&version=small) | ![Daze](https://api.scryfall.com/cards/named?exact=Daze&format=image&version=small)

Wasteland and Daze reward you if your deck can leverage tempo advantage:
- **Daze**: "Staple four-of in Delver decks." Also works in small numbers in creature-acceleration decks where you jump ahead on mana.
- **Wasteland**: Best in decks that can operate on 1-2 lands (Delver, D&T) or that use lands as a win condition (Lands).
- **Don't play them in pure control**: They're "never really happy to take a land off the battlefield" when your plan is to hit every land drop.

## Step 4: Build the 60

### Core Deck Skeleton
Most Legacy decks follow a pattern:

**Tempo / Delver Shell (~56 nonland + ~18 land):**

![Delver of Secrets](https://api.scryfall.com/cards/named?exact=Delver+of+Secrets&format=image&version=small) | ![Murktide Regent](https://api.scryfall.com/cards/named?exact=Murktide+Regent&format=image&version=small) | ![Stoneforge Mystic](https://api.scryfall.com/cards/named?exact=Stoneforge+Mystic&format=image&version=small)

- 8-12 threats (Delver, Murktide, Bowmasters)
- 8 cantrips (4 Brainstorm, 4 Ponder)
- 4 Force of Will
- 2-4 Force of Negation
- 4 Daze
- 4-6 removal (Lightning Bolt, Fatal Push, Swords to Plowshares)
- 4 Wasteland
- 6-8 fetchlands
- 2-4 dual lands
- 2-3 basic lands

**Control Shell (~34 nonland + ~25 land):**
- 2-6 win conditions (Monastery Mentor, Teferi, Entreat the Angels)
- 8 cantrips
- 4 Force of Will
- 4-6 additional counterspells
- 6-8 removal spells
- 25+ lands with heavy basics

**Combo Shell (~42-46 nonland + ~14-18 land):**
- 4 copies of key combo pieces
- Tutors and card selection to find them
- Protection (Force of Will, Thoughtseize, Duress, Veil of Summer)
- Fast mana (Lotus Petal, LED, Dark Ritual, Chrome Mox)

### Tutors: Power vs. Consistency
> "You also need to show restraint, as playing too many situational one-ofs can wind up weakening your draws." — Reid Duke

Ask: "Is a target winning you games that you'd be losing otherwise?" Don't add silver bullets just because you can tutor for them — your average draw quality matters more than your best-case scenario.

### Card Evaluation for Legacy
A card is Legacy-playable if it does at least one of:
1. **Costs 0-1 mana** and does something meaningful
2. **Generates card advantage** efficiently
3. **Disrupts the opponent's plan** proactively
4. **Ends the game quickly** once resolved
5. **Can't be answered cleanly** by common removal

Cards that cost 3+ mana need to be game-changing to justify their spot (Murktide Regent, True-Name Nemesis, Uro).

## Step 5: Build the Sideboard

### Sideboard Principles
- **Have a plan for each major matchup** — don't just jam 15 "good cards"
- **Know what you're cutting** — for every card that comes in, one goes out
- **Don't dilute your gameplan** — sideboard cards should complement your strategy, not fight it
- **Respect the blue card count** — if you board out too many blue cards, Force of Will becomes uncastable

### Common Sideboard Categories
| Category | Cards | Targets |
|----------|-------|---------|
| Graveyard hate | Leyline of the Void, Surgical Extraction, Endurance | Reanimator, Dredge, Doomsday |
| Artifact/Enchantment removal | Force of Vigor, Null Rod, Collector Ouphe | 8-Cast, Stompy, Urza's Saga |
| Anti-blue | Pyroblast, Red Elemental Blast | Delver, Control, Show and Tell |
| Anti-red | Hydroblast, Blue Elemental Blast | Stompy, Burn, Painter |
| Anti-combo | Flusterstorm, Mindbreak Trap, Deafening Silence | Storm, Oops, combo in general |
| Creature removal | Toxic Deluge, Supreme Verdict, Terminus | Go-wide strategies, Elves, D&T |
| Planeswalker/threat answers | Pithing Needle, Sheoldred's Edict | Specific problem permanents |

### Reid Duke's Sideboard Insight
At GP Providence 2011, Duke's **Ancient Grudge** was his best card: "I faced Stoneforge Mystic and Painter's Servant decks round after round." Know the meta, and sideboard for what you expect to face — not for theoretical worst cases.

## Step 6: Test and Iterate

### Goldfishing
Test your deck in solitaire to understand:
- How often do you have a turn-1 play?
- What does your average opening hand look like?
- How consistently do you hit your mana?
- When does your deck "turn the corner" and start winning?

### Matchup Testing
Play against the top 5 meta decks. For each matchup, know:
- What's your game plan pre-sideboard?
- What comes in and out post-sideboard?
- What cards from the opponent do you need to respect?
- What's your win rate?

### The Reid Duke Mantra
For controlling decks: **"Never do anything unless you have to."**

For aggressive decks: **"Every turn you wait is a turn they draw an answer."**

## Budget Considerations

### The Expensive Cards
| Card | Approximate Cost | Why It's Expensive |
|------|-----------------|-------------------|
| Underground Sea | $600-800 | Reserved List dual land |
| Volcanic Island | $500-700 | Reserved List dual land |
| Tropical Island | $400-600 | Reserved List dual land |
| Tundra | $300-500 | Reserved List dual land |
| The Tabernacle at Pendrell Vale | $5,000+ | Reserved List, Lands-only |
| Gaea's Cradle | $800-1,000 | Reserved List, Elves/Cradle Control |
| Lion's Eye Diamond | $300-400 | Reserved List, combo staple |
| Force of Will | $80-100 | Alliances, high demand |
| Mox Diamond | $400-500 | Reserved List |

### Budget Substitutions

Expensive staples vs. their budget replacements:

![Underground Sea](https://api.scryfall.com/cards/named?exact=Underground+Sea&format=image&version=small) vs. ![Watery Grave](https://api.scryfall.com/cards/named?exact=Watery+Grave&format=image&version=small) | ![Force of Will](https://api.scryfall.com/cards/named?exact=Force+of+Will&format=image&version=small) vs. ![Force of Negation](https://api.scryfall.com/cards/named?exact=Force+of+Negation&format=image&version=small)

| Expensive Card | Budget Alternative | Trade-off |
|----------------|-------------------|-----------|
| Dual lands | Shock lands (Watery Grave, etc.) | 2 life per untapped use. Real cost in aggressive matchups. |
| Dual lands | Fetchable duals (Zagoth Triome, etc.) | Enter tapped. Terrible for tempo decks. Acceptable in control. |
| Force of Will | Subtlety, Force of Negation | Narrower — FoN only on opponent's turn, Subtlety only hits creatures |
| Wasteland | Ghost Quarter, Field of Ruin | They give the opponent a basic. Much weaker mana denial. |
| Mox Diamond | Chrome Mox | Imprint cost instead of land discard. Different deckbuilding constraint. |
| The Tabernacle | Pendrell Mists | 4 mana enchantment instead of free land. Much slower. |

### Budget-Friendly Archetypes
- **Oops! All Spells** (~$1,100): No dual lands needed
- **Burn** (~$1,500): Mostly commons/uncommons + a few fetchlands
- **Belcher** (~$1,200): Fast mana is cheap, no dual lands
- **Dredge** (~$2,000): LED is the main expense, rest is budget
- **Red Stompy** (~$2,500): No dual lands, Ancient Tomb is the splurge
