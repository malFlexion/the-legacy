"""Tests for the goldfish engine."""

import pytest

from src.goldfish_engine import (
    Card,
    Deck,
    Hand,
    FETCH_LAND_COLORS,
    aggregate_stats,
    draw_opening_hand,
    london_mulligan,
    sample_hands,
)


class FakeCardIndex:
    """Minimal CardIndex stand-in with just the fields goldfish cares about."""

    def __init__(self, cards: dict[str, dict]):
        self.cards = cards


@pytest.fixture
def idx():
    """Card index for a realistic Dimir Tempo deck."""
    return FakeCardIndex({
        # Lands
        "Underground Sea": {
            "type_line": "Land — Island Swamp",
            "cmc": 0, "colors": [], "color_identity": ["B", "U"],
        },
        "Polluted Delta": {
            "type_line": "Land",  # fetch — overridden by FETCH_LAND_COLORS
            "cmc": 0, "colors": [], "color_identity": [],
        },
        "Misty Rainforest": {
            "type_line": "Land",
            "cmc": 0, "colors": [], "color_identity": [],
        },
        "Wasteland": {  # colorless utility land
            "type_line": "Land",
            "cmc": 0, "colors": [], "color_identity": [],
        },
        "Island": {
            "type_line": "Basic Land — Island",
            "cmc": 0, "colors": [], "color_identity": ["U"],
        },
        "Swamp": {
            "type_line": "Basic Land — Swamp",
            "cmc": 0, "colors": [], "color_identity": ["B"],
        },
        # Spells
        "Brainstorm": {
            "type_line": "Instant",
            "cmc": 1, "colors": ["U"], "color_identity": ["U"],
        },
        "Ponder": {
            "type_line": "Sorcery",
            "cmc": 1, "colors": ["U"], "color_identity": ["U"],
        },
        "Force of Will": {
            "type_line": "Instant",
            "cmc": 5, "colors": ["U"], "color_identity": ["U"],
        },
        "Daze": {
            "type_line": "Instant",
            "cmc": 2, "colors": ["U"], "color_identity": ["U"],
        },
        "Thoughtseize": {
            "type_line": "Sorcery",
            "cmc": 1, "colors": ["B"], "color_identity": ["B"],
        },
        "Orcish Bowmasters": {
            "type_line": "Creature — Orc Archer",
            "cmc": 2, "colors": ["B"], "color_identity": ["B"],
        },
        "Murktide Regent": {
            "type_line": "Creature — Dragon",
            "cmc": 7, "colors": ["U"], "color_identity": ["U"],
        },
    })


def dimir_list() -> dict[str, int]:
    """A Dimir-flavored test deck. 52 cards with 24 lands (close to a real ratio).

    Not a legal 60-card Legacy deck — this fixture exists to test engine
    mechanics, not deck legality. Use this for testing stats and behavior.
    """
    return {
        # Spells: 28
        "Brainstorm": 4, "Ponder": 4, "Force of Will": 4, "Daze": 4,
        "Thoughtseize": 4, "Orcish Bowmasters": 4, "Murktide Regent": 4,
        # Lands: 24
        "Underground Sea": 4, "Polluted Delta": 4, "Misty Rainforest": 4,
        "Wasteland": 4, "Island": 4, "Swamp": 4,
    }




# ----- Card / land detection -----

def test_card_is_land_detected_from_type_line(idx):
    deck = Deck.from_decklist({"Underground Sea": 1, "Brainstorm": 1}, idx)
    cards_by_name = {c.name: c for c in deck._original}
    assert cards_by_name["Underground Sea"].is_land is True
    assert cards_by_name["Brainstorm"].is_land is False


def test_fetchland_producible_colors_overridden(idx):
    deck = Deck.from_decklist({"Polluted Delta": 1}, idx)
    delta = deck._original[0]
    assert set(delta.producible_colors) == {"U", "B"}


def test_dual_land_producible_colors_from_color_identity(idx):
    deck = Deck.from_decklist({"Underground Sea": 1}, idx)
    sea = deck._original[0]
    assert set(sea.producible_colors) == {"B", "U"}


def test_colorless_land_produces_nothing(idx):
    deck = Deck.from_decklist({"Wasteland": 1}, idx)
    waste = deck._original[0]
    assert waste.producible_colors == []


# ----- Deck mechanics -----

def test_deck_size_matches_decklist(idx):
    decklist = dimir_list()
    deck = Deck.from_decklist(decklist, idx)
    assert len(deck) == sum(decklist.values())


def test_draw_reduces_library(idx):
    decklist = dimir_list()
    deck = Deck.from_decklist(decklist, idx)
    initial = len(deck)
    deck.draw(7)
    assert len(deck) == initial - 7


def test_draw_more_than_library_raises(idx):
    deck = Deck.from_decklist({"Brainstorm": 4}, idx)
    with pytest.raises(ValueError):
        deck.draw(10)


def test_reset_restores_library(idx):
    decklist = dimir_list()
    deck = Deck.from_decklist(decklist, idx)
    initial = len(deck)
    deck.shuffle(seed=42)
    deck.draw(7)
    assert len(deck) == initial - 7
    deck.reset()
    assert len(deck) == initial


def test_shuffle_is_deterministic_with_seed(idx):
    deck1 = Deck.from_decklist(dimir_list(), idx)
    deck1.shuffle(seed=42)
    order1 = [c.name for c in deck1.library]

    deck2 = Deck.from_decklist(dimir_list(), idx)
    deck2.shuffle(seed=42)
    order2 = [c.name for c in deck2.library]

    assert order1 == order2


def test_empty_deck_raises(idx):
    with pytest.raises(ValueError):
        Deck([])


# ----- Opening hand -----

def test_opening_hand_has_7_cards(idx):
    deck = Deck.from_decklist(dimir_list(), idx)
    hand = draw_opening_hand(deck, seed=1)
    assert len(hand) == 7


def test_opening_hand_is_reproducible(idx):
    deck1 = Deck.from_decklist(dimir_list(), idx)
    deck2 = Deck.from_decklist(dimir_list(), idx)
    h1 = draw_opening_hand(deck1, seed=99)
    h2 = draw_opening_hand(deck2, seed=99)
    assert [c.name for c in h1.cards] == [c.name for c in h2.cards]


# ----- Hand stats -----

def test_hand_land_count(idx):
    h = Hand([
        Deck.from_decklist({"Underground Sea": 1}, idx)._original[0],
        Deck.from_decklist({"Brainstorm": 1}, idx)._original[0],
        Deck.from_decklist({"Wasteland": 1}, idx)._original[0],
    ])
    assert h.land_count == 2
    assert h.spell_count == 1


def test_hand_mana_curve_excludes_lands(idx):
    h = Hand([
        Deck.from_decklist({"Underground Sea": 1}, idx)._original[0],  # land
        Deck.from_decklist({"Brainstorm": 1}, idx)._original[0],        # 1
        Deck.from_decklist({"Orcish Bowmasters": 1}, idx)._original[0], # 2
        Deck.from_decklist({"Orcish Bowmasters": 1}, idx)._original[0], # 2
    ])
    assert h.mana_curve == {1: 1, 2: 2}


def test_colors_by_turn_tracks_lands_in_order(idx):
    # Hand: Island, Brainstorm, Swamp, Wasteland
    cards = [
        Deck.from_decklist({"Island": 1}, idx)._original[0],
        Deck.from_decklist({"Brainstorm": 1}, idx)._original[0],
        Deck.from_decklist({"Swamp": 1}, idx)._original[0],
        Deck.from_decklist({"Wasteland": 1}, idx)._original[0],
    ]
    h = Hand(cards)
    colors = h.colors_available_by_turn(max_turn=4)

    # Turn 1: Island -> U
    assert colors[1] == {"U"}
    # Turn 2: +Swamp -> U, B
    assert colors[2] == {"U", "B"}
    # Turn 3: +Wasteland (colorless) -> still U, B
    assert colors[3] == {"U", "B"}
    # Turn 4: no more lands -> still U, B
    assert colors[4] == {"U", "B"}


def test_colors_by_turn_handles_fetchland(idx):
    cards = [
        Deck.from_decklist({"Polluted Delta": 1}, idx)._original[0],
    ]
    h = Hand(cards)
    colors = h.colors_available_by_turn(max_turn=2)
    # Polluted Delta can find Island or Swamp -> U, B available
    assert colors[1] == {"U", "B"}


# ----- London Mulligan -----

def test_london_mull_to_6_keeps_6(idx):
    deck = Deck.from_decklist(dimir_list(), idx)
    hand = london_mulligan(deck, keep_count=6, seed=42)
    assert len(hand) == 6


def test_london_mull_to_5_keeps_5(idx):
    deck = Deck.from_decklist(dimir_list(), idx)
    hand = london_mulligan(deck, keep_count=5, seed=42)
    assert len(hand) == 5


def test_london_mull_keep_7_is_no_mulligan(idx):
    deck = Deck.from_decklist(dimir_list(), idx)
    hand = london_mulligan(deck, keep_count=7, seed=42)
    assert len(hand) == 7


def test_london_mull_invalid_keep_count_raises(idx):
    deck = Deck.from_decklist(dimir_list(), idx)
    with pytest.raises(ValueError):
        london_mulligan(deck, keep_count=8)
    with pytest.raises(ValueError):
        london_mulligan(deck, keep_count=-1)


def test_london_mull_library_size_after(idx):
    """After mulling to 5 (keep 5, put 2 back), library = total - 5 in hand."""
    decklist = dimir_list()
    deck = Deck.from_decklist(decklist, idx)
    initial = len(deck)
    london_mulligan(deck, keep_count=5, seed=42)
    assert len(deck) == initial - 5


# ----- Sampling / aggregate stats -----

def test_sample_hands_returns_n_hands(idx):
    deck = Deck.from_decklist(dimir_list(), idx)
    hands = sample_hands(deck, n=100, seed=42)
    assert len(hands) == 100


def test_sample_hands_is_reproducible(idx):
    deck1 = Deck.from_decklist(dimir_list(), idx)
    deck2 = Deck.from_decklist(dimir_list(), idx)
    h1 = sample_hands(deck1, n=50, seed=42)
    h2 = sample_hands(deck2, n=50, seed=42)
    for a, b in zip(h1, h2):
        assert [c.name for c in a.cards] == [c.name for c in b.cards]


def test_sample_hands_nonzero_required(idx):
    deck = Deck.from_decklist(dimir_list(), idx)
    with pytest.raises(ValueError):
        sample_hands(deck, n=0)


def test_aggregate_stats_computes_averages(idx):
    decklist = dimir_list()
    deck = Deck.from_decklist(decklist, idx)
    hands = sample_hands(deck, n=5000, seed=42)
    stats = aggregate_stats(hands)

    # Expected avg lands in hand = (land_count_in_deck / deck_size) * 7
    land_count = sum(
        count for name, count in decklist.items()
        if "Land" in idx.cards[name]["type_line"]
    )
    deck_size = sum(decklist.values())
    expected_avg = (land_count / deck_size) * 7

    # Sampling noise is tiny at n=5000, so ±0.1 is plenty
    assert abs(stats.avg_land_count - expected_avg) < 0.1
    assert stats.n_samples == 5000

    # Most hands should have a reasonable land count
    assert stats.keepable_rate() > 0.6


def test_aggregate_stats_empty_list():
    stats = aggregate_stats([])
    assert stats.n_samples == 0
    assert stats.avg_land_count == 0.0


def test_probability_of_land_count_sanity(idx):
    deck = Deck.from_decklist(dimir_list(), idx)
    hands = sample_hands(deck, n=5000, seed=42)
    stats = aggregate_stats(hands)

    # Probability of any land count 0-7 = 1.0
    total_prob = sum(stats.land_count_distribution.values()) / stats.n_samples
    assert abs(total_prob - 1.0) < 0.001


def test_color_by_turn_probabilities_in_range(idx):
    deck = Deck.from_decklist(dimir_list(), idx)
    hands = sample_hands(deck, n=1000, seed=42)
    stats = aggregate_stats(hands)

    for turn in stats.color_by_turn:
        for color, prob in stats.color_by_turn[turn].items():
            assert 0.0 <= prob <= 1.0


def test_color_access_improves_with_turns(idx):
    """P(have color X by turn N+1) >= P(have color X by turn N)."""
    deck = Deck.from_decklist(dimir_list(), idx)
    hands = sample_hands(deck, n=2000, seed=42)
    stats = aggregate_stats(hands, max_turn := 4)

    for color in "UB":  # Dimir plays these
        for t in range(1, 4):
            assert stats.color_by_turn[t + 1][color] >= stats.color_by_turn[t][color] - 0.01, (
                f"Color {color} availability dropped from turn {t} to {t+1}"
            )


# ----- Serialization -----

def test_hand_to_summary_is_json_ready(idx):
    import json
    deck = Deck.from_decklist(dimir_list(), idx)
    hand = draw_opening_hand(deck, seed=42)
    summary = hand.to_summary()
    # Should round-trip through JSON without error
    json.dumps(summary)
    assert "cards" in summary
    assert "land_count" in summary


def test_stats_to_summary_is_json_ready(idx):
    import json
    deck = Deck.from_decklist(dimir_list(), idx)
    hands = sample_hands(deck, n=100, seed=42)
    stats = aggregate_stats(hands)
    summary = stats.to_summary()
    json.dumps(summary)
    assert summary["n_samples"] == 100


# ----- Integration check: known fetchland list is complete -----

def test_all_zendikar_fetches_covered():
    """All 10 allied/enemy Zendikar fetches should be in FETCH_LAND_COLORS."""
    expected = {
        "Marsh Flats", "Scalding Tarn", "Verdant Catacombs",
        "Arid Mesa", "Misty Rainforest",
        "Flooded Strand", "Polluted Delta", "Bloodstained Mire",
        "Wooded Foothills", "Windswept Heath",
    }
    assert expected <= set(FETCH_LAND_COLORS.keys())
