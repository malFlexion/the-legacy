"""
Goldfish engine — deterministic deck sampling and hand analysis.

Simulates drawing opening hands from a decklist, supports the London Mulligan,
and aggregates statistics over N samples: land count distribution, mana curve
of the average opening hand, and probability of having each color available
on turns 1-N (assuming one land drop per turn).

This is the deterministic counterpart to the LLM-driven /goldfish endpoint —
useful for consistency testing, sideboarding decisions, and mulligan research.

Usage:
    from src.goldfish_engine import Deck, sample_hands, aggregate_stats
    from src.card_index import CardIndex

    idx = CardIndex(); idx.load()

    deck = Deck.from_decklist(
        {"Brainstorm": 4, "Underground Sea": 4, "Orcish Bowmasters": 4, ...},
        idx,
    )

    hands = sample_hands(deck, n=10_000)
    stats = aggregate_stats(hands)

    print(stats.avg_land_count)                # ~2.8 for a 20-land deck
    print(stats.probability_of_land_count(2, 5))  # P(2 <= lands <= 5)
    print(stats.color_by_turn[1]["U"])         # P(U available on turn 1)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterator


# Fetchlands don't have color_identity populated on Scryfall (they're colorless
# lands until activated), so we override them with what they can *find*. These
# are the Onslaught and Zendikar fetches, all legal in Legacy.
FETCH_LAND_COLORS: dict[str, list[str]] = {
    # Enemy-color fetches (Zendikar)
    "Marsh Flats": ["W", "B"],
    "Scalding Tarn": ["U", "R"],
    "Verdant Catacombs": ["B", "G"],
    "Arid Mesa": ["W", "R"],
    "Misty Rainforest": ["G", "U"],
    # Ally-color fetches (Onslaught / Khans reprints)
    "Flooded Strand": ["W", "U"],
    "Polluted Delta": ["U", "B"],
    "Bloodstained Mire": ["B", "R"],
    "Wooded Foothills": ["R", "G"],
    "Windswept Heath": ["W", "G"],
    # Any-basic fetches
    "Fabled Passage": ["W", "U", "B", "R", "G"],
    "Evolving Wilds": ["W", "U", "B", "R", "G"],
    "Terramorphic Expanse": ["W", "U", "B", "R", "G"],
    "Prismatic Vista": ["W", "U", "B", "R", "G"],
}

# Generic five-color lands that have no color_identity in Scryfall data
# but can produce any color.
FIVE_COLOR_LANDS: set[str] = {
    "City of Brass",
    "Mana Confluence",
    "Forbidden Orchard",
    "Grand Coliseum",
    "Cavern of Souls",  # technically tribe-gated but treated as any color
}


@dataclass(frozen=True)
class Card:
    """Minimal card representation for goldfish simulation."""
    name: str
    cmc: int
    type_line: str
    colors: list[str]
    color_identity: list[str]
    producible_colors: list[str]  # for lands: what colors of mana this can produce

    @property
    def is_land(self) -> bool:
        return "Land" in self.type_line

    @property
    def is_basic_land(self) -> bool:
        return "Basic Land" in self.type_line


def _producible_colors_for_land(name: str, color_identity: list[str]) -> list[str]:
    """Determine which colors a land can produce for goldfish purposes."""
    if name in FETCH_LAND_COLORS:
        return list(FETCH_LAND_COLORS[name])
    if name in FIVE_COLOR_LANDS:
        return ["W", "U", "B", "R", "G"]
    # Default: color_identity. This works for duals (Underground Sea = [B, U]),
    # basics (Island = [U]), shocks, pains, and most other lands. Colorless
    # lands like Ancient Tomb and Wasteland end up as [].
    return list(color_identity)


def _build_card(name: str, card_data: dict | None) -> Card:
    """Build a Card from card_index data. Missing cards get minimal defaults."""
    if card_data is None:
        # Unknown card — assume a 0 CMC non-land. Shouldn't happen with a valid decklist.
        return Card(
            name=name, cmc=0, type_line="", colors=[],
            color_identity=[], producible_colors=[],
        )
    type_line = card_data.get("type_line", "") or ""
    color_identity = list(card_data.get("color_identity") or [])
    producible = (
        _producible_colors_for_land(name, color_identity)
        if "Land" in type_line
        else []
    )
    return Card(
        name=name,
        cmc=int(card_data.get("cmc", 0) or 0),
        type_line=type_line,
        colors=list(card_data.get("colors") or []),
        color_identity=color_identity,
        producible_colors=producible,
    )


@dataclass
class Hand:
    """A drawn hand, with derived stats computed on demand."""
    cards: list[Card]

    def __len__(self) -> int:
        return len(self.cards)

    @property
    def land_count(self) -> int:
        return sum(1 for c in self.cards if c.is_land)

    @property
    def spell_count(self) -> int:
        return len(self.cards) - self.land_count

    @property
    def mana_curve(self) -> dict[int, int]:
        """CMC -> count of spells at that CMC. Lands are excluded."""
        curve: dict[int, int] = {}
        for c in self.cards:
            if not c.is_land:
                curve[c.cmc] = curve.get(c.cmc, 0) + 1
        return curve

    def colors_available_by_turn(self, max_turn: int = 4) -> dict[int, set[str]]:
        """Simulate one land drop per turn (in the order lands appear in hand).

        Returns {turn: set of colors producible by a land in play by that turn}.
        A fetchland contributes all of its possible targets, which is optimistic
        (it can only fetch one), but reasonable for a "do I have access?" check.
        """
        lands_in_hand = [c for c in self.cards if c.is_land]
        available: set[str] = set()
        result: dict[int, set[str]] = {}
        for turn in range(1, max_turn + 1):
            if turn <= len(lands_in_hand):
                available |= set(lands_in_hand[turn - 1].producible_colors)
            result[turn] = set(available)
        return result

    def to_summary(self) -> dict:
        """Serializable summary for API responses."""
        return {
            "cards": [c.name for c in self.cards],
            "land_count": self.land_count,
            "spell_count": self.spell_count,
            "mana_curve": dict(self.mana_curve),
        }


class Deck:
    """A shuffleable decklist. Maintains an original ordering so reset() is cheap."""

    def __init__(self, cards: list[Card]):
        if not cards:
            raise ValueError("Deck must contain at least one card")
        self._original: list[Card] = list(cards)
        self.library: list[Card] = list(cards)

    @classmethod
    def from_decklist(
        cls, decklist: dict[str, int], card_index, include_basics: bool = True
    ) -> Deck:
        """Build a Deck from {card_name: count} using data from card_index.

        Cards not found in card_index get minimal default data (logged as a
        warning would be nice, but we don't want to force logging on callers).
        """
        cards: list[Card] = []
        for name, count in decklist.items():
            data = card_index.cards.get(name) if card_index else None
            card = _build_card(name, data)
            cards.extend([card] * count)
        return cls(cards)

    def __len__(self) -> int:
        return len(self.library)

    def shuffle(self, seed: int | None = None) -> None:
        rng = random.Random(seed)
        rng.shuffle(self.library)

    def draw(self, n: int) -> list[Card]:
        if n > len(self.library):
            raise ValueError(
                f"Cannot draw {n} cards from library of size {len(self.library)}"
            )
        drawn = self.library[:n]
        self.library = self.library[n:]
        return drawn

    def reset(self) -> None:
        """Restore the library to its original ordering (before shuffles/draws)."""
        self.library = list(self._original)


def draw_opening_hand(deck: Deck, seed: int | None = None) -> Hand:
    """Shuffle deck, draw 7. Does not mutate the caller's reference to the deck's
    library beyond resetting+shuffling+drawing (which is the normal cycle)."""
    deck.reset()
    deck.shuffle(seed=seed)
    return Hand(deck.draw(7))


def london_mulligan(
    deck: Deck, keep_count: int, seed: int | None = None
) -> Hand:
    """London Mulligan: always draw 7, then put (7 - keep_count) cards back on bottom.

    keep_count of 7 = no mulligan (draw 7, keep all 7).
    keep_count of 6 = mulligan to 6 (draw 7, put 1 back).
    keep_count of 0 = "free" 7 with all cards put back (silly but legal).

    Which cards go back: we keep the first `keep_count` drawn. In a real game,
    the player chooses optimally; this function leaves that to higher-level
    callers (who can pass in an already-drawn hand and reorder it).
    """
    if not (0 <= keep_count <= 7):
        raise ValueError(f"keep_count must be in [0, 7], got {keep_count}")
    deck.reset()
    deck.shuffle(seed=seed)
    drawn = deck.draw(7)
    kept = drawn[:keep_count]
    put_back = drawn[keep_count:]
    deck.library.extend(put_back)
    return Hand(kept)


def sample_hands(
    deck: Deck,
    n: int,
    mulligan_to: int = 7,
    seed: int | None = None,
) -> list[Hand]:
    """Run n independent trials of drawing an opening hand.

    Each trial uses an independent seed derived from the master `seed`,
    so results are reproducible when `seed` is fixed.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    rng = random.Random(seed)
    hands: list[Hand] = []
    for _ in range(n):
        trial_seed = rng.randint(0, 2**31 - 1)
        hands.append(london_mulligan(deck, keep_count=mulligan_to, seed=trial_seed))
    return hands


@dataclass
class HandStats:
    """Aggregated statistics over N sampled hands."""
    n_samples: int
    land_count_distribution: dict[int, int] = field(default_factory=dict)
    avg_land_count: float = 0.0
    mana_curve_avg: dict[int, float] = field(default_factory=dict)
    color_by_turn: dict[int, dict[str, float]] = field(default_factory=dict)

    def probability_of_land_count(self, lo: int, hi: int) -> float:
        """P(lo <= land_count <= hi). Inclusive on both ends."""
        matches = sum(
            count for lc, count in self.land_count_distribution.items()
            if lo <= lc <= hi
        )
        return matches / self.n_samples if self.n_samples else 0.0

    def keepable_rate(self, min_lands: int = 2, max_lands: int = 5) -> float:
        """Rough 'keepable' heuristic — hands with a reasonable land count.

        Default range is the traditional "2-5 lands in a 7-card hand" guideline
        for most fair decks. Combo and prison decks have different targets.
        """
        return self.probability_of_land_count(min_lands, max_lands)

    def to_summary(self) -> dict:
        """Serializable summary."""
        return {
            "n_samples": self.n_samples,
            "land_count_distribution": dict(self.land_count_distribution),
            "avg_land_count": round(self.avg_land_count, 3),
            "mana_curve_avg": {str(k): round(v, 3) for k, v in self.mana_curve_avg.items()},
            "color_by_turn": {
                str(t): {c: round(p, 3) for c, p in colors.items()}
                for t, colors in self.color_by_turn.items()
            },
            "keepable_rate": round(self.keepable_rate(), 3),
        }


def aggregate_stats(hands: list[Hand], max_turn: int = 4) -> HandStats:
    """Compute aggregate statistics from a list of sampled hands."""
    if not hands:
        return HandStats(n_samples=0)

    n = len(hands)
    lc_dist: dict[int, int] = {}
    total_lands = 0
    curve_totals: dict[int, int] = {}
    color_counts = {t: {c: 0 for c in "WUBRG"} for t in range(1, max_turn + 1)}

    for hand in hands:
        lc = hand.land_count
        lc_dist[lc] = lc_dist.get(lc, 0) + 1
        total_lands += lc

        for cmc, cnt in hand.mana_curve.items():
            curve_totals[cmc] = curve_totals.get(cmc, 0) + cnt

        by_turn = hand.colors_available_by_turn(max_turn)
        for t, colors in by_turn.items():
            for c in colors:
                if c in color_counts[t]:
                    color_counts[t][c] += 1

    return HandStats(
        n_samples=n,
        land_count_distribution=lc_dist,
        avg_land_count=total_lands / n,
        mana_curve_avg={cmc: cnt / n for cmc, cnt in curve_totals.items()},
        color_by_turn={
            t: {c: cnt / n for c, cnt in colors.items()}
            for t, colors in color_counts.items()
        },
    )
