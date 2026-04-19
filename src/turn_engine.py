"""
Simplified turn-by-turn goldfish simulator.

Models just enough MTG to play out 5-7 turns of a single-player goldfish
and produce useful stats: how fast does this deck deploy threats, does it
assemble its combo, how much mana does it waste each turn.

Explicitly NOT modeled (goldfish only):
- Opponent / combat phase (no attacks, blocks, or damage)
- Most triggered abilities (Bowmasters pings, Thoughtseize triggers, etc.)
- Instant-speed interaction (counterspells and removal sit in hand)
- Stack resolution, priority windows, timing restrictions
- State-based actions beyond "combo assembled"
- Effects that target the opponent (Thoughtseize, Surgical Extraction, Bolt)

What IS modeled:
- Untap, draw, one land drop per turn
- Mana pool tracking by color (WUBRGC) with generic mana conversion
- Fetchlands: crack, search library for a matching dual or basic, shuffle
- Dual lands, shocklands, basics, colorless utility lands (Ancient Tomb,
  City of Traitors, Wasteland), fast mana (Lotus Petal, Chrome Mox)
- Greedy spell casting: at each main phase, cast the biggest spell we can
  pay for, with heuristics to prefer cantrips before committing threats
- Combo detection for common Legacy win conditions
- Mana efficiency: mana used vs. mana available per turn

Usage:
    from src.turn_engine import simulate_game, aggregate_game_stats
    from src.goldfish_engine import Deck
    from src.card_index import CardIndex

    idx = CardIndex(); idx.load()
    deck = Deck.from_decklist(dimir_list, idx)

    game = simulate_game(deck, turns=6, seed=42)
    print(game.to_summary())

    # Aggregate over N games
    results = [simulate_game(deck, turns=6, seed=i) for i in range(1000)]
    stats = aggregate_game_stats(results)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable

from .goldfish_engine import Card, Deck, FETCH_LAND_COLORS, FIVE_COLOR_LANDS


# ---------------------------------------------------------------------------
# Known combo patterns: a combo "assembles" when all required cards are
# on the battlefield together. This is a simple presence check — it doesn't
# verify activation mana or timing, which is fine for goldfish.
# ---------------------------------------------------------------------------

COMBOS: dict[str, list[str]] = {
    "Marit Lage (Lands)": ["Dark Depths", "Thespian's Stage"],
    "Painter + Grindstone": ["Painter's Servant", "Grindstone"],
    "Helm of Obedience + Leyline": ["Helm of Obedience", "Leyline of the Void"],
    "Thopter Foundry + Sword of the Meek": ["Thopter Foundry", "Sword of the Meek"],
    "Food Chain (Squee)": ["Food Chain", "Squee, Goblin Nabob"],
    "Enduring Ideal + Dovescape": ["Enduring Ideal", "Dovescape"],
}


# ---------------------------------------------------------------------------
# Mana rocks / free mana sources. Each entry: (produced_mana, life_cost,
# self_exile_on_use). These tap-for-mana actions are available on the turn
# they enter play (they don't respect summoning sickness in goldfish).
# ---------------------------------------------------------------------------

MANA_ROCKS: dict[str, dict] = {
    "Lotus Petal": {"produces": ["W", "U", "B", "R", "G"], "life": 0, "exile": True},
    "Chrome Mox": {"produces": ["W", "U", "B", "R", "G"], "life": 0, "exile": False},
    "Mox Diamond": {"produces": ["W", "U", "B", "R", "G"], "life": 0, "exile": False},
    "Lion's Eye Diamond": {"produces": ["W", "U", "B", "R", "G"], "life": 0, "exile": True},
    "Ancient Tomb": {"produces": ["C", "C"], "life": 2, "exile": False},
    "City of Traitors": {"produces": ["C", "C"], "life": 0, "exile": False},
}


# Colorless lands — tap for C only
COLORLESS_LANDS = {"Wasteland", "Rishadan Port", "Mishra's Factory", "Mutavault"}


# Cards to prioritize casting before committing to board threats — cantrips
# that improve future draws, hand disruption that protects key plays, and
# tutors that find combo pieces.
CANTRIP_PRIORITY = {
    "Brainstorm", "Ponder", "Preordain", "Gitaxian Probe",
    "Sleight of Hand", "Serum Visions", "Opt",
    "Thoughtseize", "Duress", "Inquisition of Kozilek",
    "Lotus Petal", "Dark Ritual", "Cabal Ritual", "Chrome Mox",
    "Once Upon a Time", "Green Sun's Zenith", "Entomb",
}


# Reactive cards that goldfish skips (won't cast during our turns).
# Counterspells, removal that needs a target, combat tricks.
REACTIVE_SKIP = {
    "Force of Will", "Force of Negation", "Daze", "Spell Pierce",
    "Counterspell", "Flusterstorm", "Stern Scolding", "Mindbreak Trap",
    "Pact of Negation", "Subtlety",
    "Swords to Plowshares", "Fatal Push", "Lightning Bolt", "Snuff Out",
    "Dismember", "Unholy Heat", "Prismatic Ending", "Solitude",
}


# ---------------------------------------------------------------------------
# State model
# ---------------------------------------------------------------------------

@dataclass
class Permanent:
    """A card on the battlefield."""
    card: Card
    tapped: bool = False


@dataclass
class TurnSnapshot:
    """Per-turn record of what happened. Used for post-game analysis."""
    turn: int
    hand_size_start: int
    land_played: str | None = None
    spells_cast: list[str] = field(default_factory=list)
    mana_available: int = 0
    mana_used: int = 0
    combos_assembled: list[str] = field(default_factory=list)

    @property
    def mana_wasted(self) -> int:
        return max(0, self.mana_available - self.mana_used)


@dataclass
class GameState:
    """Complete game state for a single-player goldfish."""
    library: list[Card]
    hand: list[Card]
    battlefield: list[Permanent] = field(default_factory=list)
    graveyard: list[Card] = field(default_factory=list)
    exile: list[Card] = field(default_factory=list)
    life: int = 20
    turn: int = 0
    land_played_this_turn: bool = False
    rng: random.Random = field(default_factory=random.Random)
    snapshots: list[TurnSnapshot] = field(default_factory=list)
    assembled_combos: dict[str, int] = field(default_factory=dict)  # combo -> turn assembled

    def battlefield_names(self) -> set[str]:
        return {p.card.name for p in self.battlefield}


@dataclass
class GameResult:
    """Post-simulation summary."""
    turns_played: int
    life_final: int
    snapshots: list[TurnSnapshot]
    assembled_combos: dict[str, int]
    threats_deployed: dict[str, int]  # card name -> turn first cast

    def to_summary(self) -> dict:
        return {
            "turns_played": self.turns_played,
            "life_final": self.life_final,
            "turns": [
                {
                    "turn": s.turn,
                    "land_played": s.land_played,
                    "spells_cast": s.spells_cast,
                    "mana_available": s.mana_available,
                    "mana_used": s.mana_used,
                    "mana_wasted": s.mana_wasted,
                    "combos": s.combos_assembled,
                }
                for s in self.snapshots
            ],
            "assembled_combos": dict(self.assembled_combos),
            "threats_deployed": dict(self.threats_deployed),
        }


# ---------------------------------------------------------------------------
# Mana handling
# ---------------------------------------------------------------------------

def _parse_mana_cost(mana_cost_str: str) -> dict[str, int]:
    """Parse a mana cost like '{2}{U}{B}' into {'generic': 2, 'U': 1, 'B': 1}.

    Ignores X costs (X = 0 for goldfish purposes) and phyrexian mana
    (treated as 1 life, not a mana color — we approximate as generic).
    """
    cost: dict[str, int] = {}
    # Strip braces and split
    parts = mana_cost_str.replace("{", "").replace("}", " ").split()
    for p in parts:
        if not p:
            continue
        if p.isdigit():
            cost["generic"] = cost.get("generic", 0) + int(p)
        elif p == "X":
            # X = 0 for goldfish
            continue
        elif p in ("W", "U", "B", "R", "G", "C"):
            cost[p] = cost.get(p, 0) + 1
        elif "/" in p:
            # hybrid or phyrexian — just use the first listed color as generic approx
            cost["generic"] = cost.get("generic", 0) + 1
        else:
            # Unknown symbol — treat as generic
            cost["generic"] = cost.get("generic", 0) + 1
    return cost


def _available_mana(state: GameState) -> dict[str, int]:
    """Compute the max mana pool we could float this turn by tapping everything.

    Returns a dict with colors WUBRGC and total. Doesn't account for the
    choice of which color a dual produces — that's resolved at pay time.
    """
    pool = {c: 0 for c in "WUBRGC"}
    for perm in state.battlefield:
        if perm.tapped:
            continue
        name = perm.card.name
        if name in MANA_ROCKS:
            info = MANA_ROCKS[name]
            # For max-available, assume we can produce any one of its colors
            # (picking the right one at pay time). Don't double count — Lotus
            # Petal produces 1 mana total, not 5.
            pool["C"] += len(info["produces"]) if info["produces"] == ["C", "C"] else 1
        elif name in FIVE_COLOR_LANDS:
            pool["C"] += 1  # we'll account for the color flexibility at pay time
        elif name in COLORLESS_LANDS:
            pool["C"] += 1
        elif perm.card.is_land:
            pool["C"] += 1  # count as a generic source; color resolution below
    return pool


def _try_pay_cost(state: GameState, cost: dict[str, int]) -> list[Permanent] | None:
    """Try to pay the given cost by tapping permanents. Returns the permanents
    that would be tapped (caller applies), or None if the cost can't be paid.

    Greedy: for each colored requirement, find an untapped permanent that can
    produce that color, prefer specific (basic/dual for exact color) over
    flexible (fetchland, 5-color land). Then fill generic with whatever's left.
    """
    # Collect all untapped mana sources with what they can produce
    sources = []  # list of (permanent, producible_colors_set)
    for perm in state.battlefield:
        if perm.tapped:
            continue
        name = perm.card.name
        if name in MANA_ROCKS:
            info = MANA_ROCKS[name]
            # For goldfish we ignore life cost checks here; callers pay Ancient Tomb life
            sources.append((perm, set(info["produces"])))
        elif perm.card.is_land:
            colors = set(perm.card.producible_colors) if perm.card.producible_colors else {"C"}
            sources.append((perm, colors))

    used: list[Permanent] = []

    # Pay each colored requirement first
    for color in "WUBRG":
        needed = cost.get(color, 0)
        for _ in range(needed):
            # Find the most-specific source that can make this color
            pick = None
            for perm, colors in sources:
                if perm in used:
                    continue
                if color in colors:
                    # Prefer fewer-color sources (more specific)
                    if pick is None or len(colors) < len(sources[[p for p, _ in sources].index(pick)][1]):
                        pick = perm
            if pick is None:
                return None  # can't pay
            used.append(pick)

    # Pay generic and colorless with anything remaining
    remaining_generic = cost.get("generic", 0) + cost.get("C", 0)
    for perm, colors in sources:
        if remaining_generic == 0:
            break
        if perm in used:
            continue
        # Ancient Tomb produces 2 colorless — account for it
        if perm.card.name == "Ancient Tomb":
            remaining_generic -= 2
        else:
            remaining_generic -= 1
        used.append(perm)

    if remaining_generic > 0:
        return None

    return used


def _apply_payment(state: GameState, used: list[Permanent], cost: dict[str, int]) -> int:
    """Tap the permanents, apply any life costs, handle LED-style self-exile.

    Returns total life paid.
    """
    life_paid = 0
    for perm in used:
        name = perm.card.name
        perm.tapped = True

        if name in MANA_ROCKS:
            info = MANA_ROCKS[name]
            life_paid += info["life"]
            if info["exile"]:
                state.battlefield.remove(perm)
                state.exile.append(perm.card)

        # Ancient Tomb pings for 2 life (even though it's in MANA_ROCKS)
        # — handled above

    state.life -= life_paid
    return life_paid


# ---------------------------------------------------------------------------
# Fetchland resolution
# ---------------------------------------------------------------------------

# Hand-curated preferred fetch targets for common Legacy decks. When a
# fetchland resolves, we pick the first matching dual in the library;
# otherwise a basic. This is "smart enough" for goldfish.
PREFERRED_DUALS = {
    frozenset(["U", "B"]): ["Underground Sea", "Watery Grave", "Darkslick Shores", "Underground River"],
    frozenset(["U", "R"]): ["Volcanic Island", "Steam Vents", "Spirebluff Canal", "Shivan Reef"],
    frozenset(["U", "G"]): ["Tropical Island", "Breeding Pool", "Botanical Sanctum", "Yavimaya Coast"],
    frozenset(["U", "W"]): ["Tundra", "Hallowed Fountain", "Seachrome Coast", "Adarkar Wastes"],
    frozenset(["B", "G"]): ["Bayou", "Overgrown Tomb", "Blooming Marsh", "Llanowar Wastes"],
    frozenset(["W", "R"]): ["Plateau", "Sacred Foundry", "Inspiring Vantage", "Battlefield Forge"],
    frozenset(["W", "G"]): ["Savannah", "Temple Garden", "Razorverge Thicket", "Brushland"],
    frozenset(["W", "B"]): ["Scrubland", "Godless Shrine", "Concealed Courtyard", "Caves of Koilos"],
    frozenset(["R", "G"]): ["Taiga", "Stomping Ground", "Copperline Gorge", "Karplusan Forest"],
    frozenset(["B", "R"]): ["Badlands", "Blood Crypt", "Blackcleave Cliffs", "Sulfurous Springs"],
}


def _resolve_fetchland(state: GameState, fetch_perm: Permanent) -> str | None:
    """Crack a fetchland: sacrifice it, search library for the best dual/basic
    that matches its color targets, put that land into play tapped, shuffle.

    Returns the name of the fetched land, or None if nothing suitable was found.
    """
    fetch_name = fetch_perm.card.name
    target_colors = FETCH_LAND_COLORS.get(fetch_name)
    if not target_colors:
        return None

    # Sacrifice the fetchland
    state.battlefield.remove(fetch_perm)
    state.graveyard.append(fetch_perm.card)

    # Prefer duals, then shocks, then basics matching the colors
    preferred = PREFERRED_DUALS.get(frozenset(target_colors), [])
    fetched = None
    for preferred_name in preferred:
        for card in state.library:
            if card.name == preferred_name:
                fetched = card
                break
        if fetched:
            break

    # Fallback: basic land matching any target color
    if fetched is None:
        basic_names = {"W": "Plains", "U": "Island", "B": "Swamp", "R": "Mountain", "G": "Forest"}
        for color in target_colors:
            basic_name = basic_names.get(color)
            if basic_name is None:
                continue
            for card in state.library:
                if card.name == basic_name:
                    fetched = card
                    break
            if fetched:
                break

    if fetched:
        state.library.remove(fetched)
        # Fetchland targets enter untapped by default (Onslaught/Zendikar fetches)
        state.battlefield.append(Permanent(card=fetched, tapped=False))
        state.rng.shuffle(state.library)
        return fetched.name

    # Nothing found, just shuffle
    state.rng.shuffle(state.library)
    return None


def _is_fetchland(card: Card) -> bool:
    return card.name in FETCH_LAND_COLORS


# ---------------------------------------------------------------------------
# Turn steps
# ---------------------------------------------------------------------------

def _untap_step(state: GameState) -> None:
    """Untap all permanents. City of Traitors doesn't untap — we approximate by
    tapping it and leaving it that way (the deck lose-tempo mechanic)."""
    for perm in state.battlefield:
        if perm.card.name == "City of Traitors":
            # stays tapped as a simplification of its drawback
            continue
        perm.tapped = False
    state.land_played_this_turn = False


def _draw_step(state: GameState) -> Card | None:
    """Draw one card. Returns the drawn card, or None if library is empty."""
    if not state.library:
        return None
    drawn = state.library[0]
    state.library = state.library[1:]
    state.hand.append(drawn)
    return drawn


def _select_land_to_play(state: GameState) -> Card | None:
    """Pick the best land in hand to play this turn.

    Priority: fetchland (maximizes deck thinning and shuffle for cantrips),
    then dual/shock matching colors we need, then basic, then colorless
    utility (Wasteland last since it has nothing to destroy in goldfish).
    """
    lands = [c for c in state.hand if c.is_land]
    if not lands:
        return None

    # Priority 1: fetchlands
    for card in lands:
        if _is_fetchland(card):
            return card

    # Priority 2: lands that produce colors (skip colorless utility)
    for card in lands:
        if card.producible_colors:
            return card

    # Priority 3: anything else (colorless utility lands)
    return lands[0]


def _play_land(state: GameState) -> str | None:
    """Play a land if we haven't this turn. Returns the land name or None."""
    if state.land_played_this_turn:
        return None
    card = _select_land_to_play(state)
    if card is None:
        return None

    state.hand.remove(card)
    perm = Permanent(card=card, tapped=False)
    state.battlefield.append(perm)
    state.land_played_this_turn = True

    # Fetchlands: crack immediately for the goldfish (humans often wait, but
    # cracking fetches on main phase is correct for thinning and cantrip fuel)
    if _is_fetchland(card):
        fetched = _resolve_fetchland(state, perm)
        return f"{card.name} -> {fetched}" if fetched else card.name

    return card.name


def _castable_order(hand: list[Card]) -> list[Card]:
    """Order hand for casting: cantrips/rituals first, then by CMC descending."""
    def sort_key(c: Card):
        is_priority = 0 if c.name in CANTRIP_PRIORITY else 1
        return (is_priority, -c.cmc)

    return sorted(hand, key=sort_key)


def _try_cast(state: GameState, card: Card) -> bool:
    """Attempt to cast `card` from hand using current mana. Returns True on success."""
    if card.name in REACTIVE_SKIP:
        return False
    if card.is_land:
        return False

    # Parse the cost from the Card's mana_cost. Our Card class doesn't store
    # mana_cost text directly — we only have cmc. Use cmc as generic cost
    # when parsed cost isn't available.
    # For goldfish, approximate: pay cmc from available mana, using colored
    # sources where possible.
    cost = {"generic": card.cmc}
    # If the card has colors, require at least one of each
    for color in card.colors:
        cost[color] = cost.get(color, 0) + 1
        cost["generic"] = max(0, cost["generic"] - 1)

    used = _try_pay_cost(state, cost)
    if used is None:
        return False

    _apply_payment(state, used, cost)

    # Move from hand to battlefield (permanents) or graveyard (non-permanents)
    state.hand.remove(card)
    if "Creature" in card.type_line or "Artifact" in card.type_line or "Enchantment" in card.type_line or "Planeswalker" in card.type_line:
        state.battlefield.append(Permanent(card=card, tapped=False))
    else:
        state.graveyard.append(card)
    return True


def _main_phase(state: GameState) -> list[str]:
    """Cast spells greedily until nothing more is castable. Returns list of card names cast."""
    cast: list[str] = []
    while True:
        progress = False
        for card in _castable_order(state.hand):
            if _try_cast(state, card):
                cast.append(card.name)
                progress = True
                break
        if not progress:
            break
    return cast


def _check_combos(state: GameState) -> list[str]:
    """Return list of combo names that are assembled on the battlefield."""
    assembled = []
    on_field = state.battlefield_names()
    for combo_name, pieces in COMBOS.items():
        if all(p in on_field for p in pieces):
            assembled.append(combo_name)
    return assembled


# ---------------------------------------------------------------------------
# Game simulation
# ---------------------------------------------------------------------------

def simulate_game(
    deck: Deck,
    turns: int = 6,
    seed: int | None = None,
    starting_hand_size: int = 7,
) -> GameResult:
    """Play out a goldfish game from turn 1 to `turns`. Returns a GameResult.

    The deck is reset and shuffled; an opening hand is drawn (no mulligan logic
    here — callers that want mulligan behavior should use london_mulligan first
    and pass a pre-mulliganed state in via the lower-level APIs).
    """
    rng = random.Random(seed)
    deck.reset()
    deck.shuffle(seed=seed)

    state = GameState(
        library=list(deck.library),
        hand=[],
        rng=rng,
    )
    # Opening hand
    for _ in range(starting_hand_size):
        _draw_step(state)

    threats_deployed: dict[str, int] = {}

    for turn in range(1, turns + 1):
        state.turn = turn
        hand_size_start = len(state.hand)

        _untap_step(state)

        # Skip draw on turn 1 when we're on the play (mirroring MTG's turn-1 rule)
        if turn > 1:
            _draw_step(state)

        # Compute mana available BEFORE casting spells so we can measure efficiency
        pool_before = _available_mana(state)
        total_mana_available = sum(pool_before.values())

        # Main phase: play land, then cast spells
        land_played = _play_land(state)
        spells = _main_phase(state)

        # Compute mana used (approximation: sum of CMC of spells cast this turn)
        mana_used = sum(
            c for name in spells
            for c in [next((p.card.cmc for p in state.battlefield if p.card.name == name), 0)
                      or next((g.cmc for g in state.graveyard if g.name == name), 0)]
        )

        # Track when each threat first hit the battlefield
        for spell in spells:
            if spell not in threats_deployed:
                threats_deployed[spell] = turn

        # Check combos
        newly_assembled = []
        for combo in _check_combos(state):
            if combo not in state.assembled_combos:
                state.assembled_combos[combo] = turn
                newly_assembled.append(combo)

        state.snapshots.append(TurnSnapshot(
            turn=turn,
            hand_size_start=hand_size_start,
            land_played=land_played,
            spells_cast=spells,
            mana_available=total_mana_available,
            mana_used=mana_used,
            combos_assembled=newly_assembled,
        ))

    return GameResult(
        turns_played=len(state.snapshots),
        life_final=state.life,
        snapshots=state.snapshots,
        assembled_combos=state.assembled_combos,
        threats_deployed=threats_deployed,
    )


# ---------------------------------------------------------------------------
# Aggregate stats over N games
# ---------------------------------------------------------------------------

@dataclass
class GameStats:
    n_games: int
    avg_life_final: float
    avg_mana_efficiency: float  # used / available across all turns
    combo_assembly: dict[str, dict]  # combo -> {"rate": 0.73, "avg_turn": 3.2}
    avg_turn_first_cast: dict[str, float]  # card_name -> avg turn first cast (when cast)
    cast_rate: dict[str, float]  # card_name -> fraction of games where card was cast

    def to_summary(self) -> dict:
        return {
            "n_games": self.n_games,
            "avg_life_final": round(self.avg_life_final, 2),
            "avg_mana_efficiency": round(self.avg_mana_efficiency, 3),
            "combo_assembly": {
                k: {"rate": round(v["rate"], 3), "avg_turn": round(v["avg_turn"], 2)}
                for k, v in self.combo_assembly.items()
            },
            "avg_turn_first_cast": {k: round(v, 2) for k, v in self.avg_turn_first_cast.items()},
            "cast_rate": {k: round(v, 3) for k, v in self.cast_rate.items()},
        }


def aggregate_game_stats(results: list[GameResult], min_cast_rate: float = 0.05) -> GameStats:
    """Aggregate per-game results into summary statistics.

    `min_cast_rate` filters the avg_turn_first_cast report to cards cast in
    at least that fraction of games (default 5%) — keeps noise out.
    """
    n = len(results)
    if n == 0:
        return GameStats(
            n_games=0, avg_life_final=20.0, avg_mana_efficiency=0.0,
            combo_assembly={}, avg_turn_first_cast={}, cast_rate={},
        )

    total_life = sum(r.life_final for r in results)
    total_mana_available = 0
    total_mana_used = 0
    combo_counts: dict[str, list[int]] = {}  # combo -> [turns it assembled]
    threat_counts: dict[str, list[int]] = {}  # card -> [turns first cast]

    for r in results:
        for snap in r.snapshots:
            total_mana_available += snap.mana_available
            total_mana_used += snap.mana_used
        for combo, turn in r.assembled_combos.items():
            combo_counts.setdefault(combo, []).append(turn)
        for card, turn in r.threats_deployed.items():
            threat_counts.setdefault(card, []).append(turn)

    combo_assembly = {
        combo: {
            "rate": len(turns) / n,
            "avg_turn": sum(turns) / len(turns),
        }
        for combo, turns in combo_counts.items()
    }

    cast_rate = {card: len(turns) / n for card, turns in threat_counts.items()}
    avg_turn_first_cast = {
        card: sum(turns) / len(turns)
        for card, turns in threat_counts.items()
        if len(turns) / n >= min_cast_rate
    }

    return GameStats(
        n_games=n,
        avg_life_final=total_life / n,
        avg_mana_efficiency=(total_mana_used / total_mana_available) if total_mana_available else 0.0,
        combo_assembly=combo_assembly,
        avg_turn_first_cast=avg_turn_first_cast,
        cast_rate=cast_rate,
    )
