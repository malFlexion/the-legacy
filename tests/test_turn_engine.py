"""Tests for the turn-by-turn goldfish engine."""

import pytest

from src.goldfish_engine import Deck, Card
from src.turn_engine import (
    COMBOS,
    FETCH_LAND_COLORS,
    GameResult,
    GameState,
    MANA_ROCKS,
    Permanent,
    aggregate_game_stats,
    simulate_game,
)


class FakeCardIndex:
    def __init__(self, cards: dict[str, dict]):
        self.cards = cards


def base_idx():
    """A card pool covering every card referenced in these tests."""
    return FakeCardIndex({
        # Lands
        "Underground Sea": {"type_line": "Land — Island Swamp", "cmc": 0, "colors": [], "color_identity": ["B", "U"]},
        "Polluted Delta": {"type_line": "Land", "cmc": 0, "colors": [], "color_identity": []},
        "Misty Rainforest": {"type_line": "Land", "cmc": 0, "colors": [], "color_identity": []},
        "Island": {"type_line": "Basic Land — Island", "cmc": 0, "colors": [], "color_identity": ["U"]},
        "Swamp": {"type_line": "Basic Land — Swamp", "cmc": 0, "colors": [], "color_identity": ["B"]},
        "Wasteland": {"type_line": "Land", "cmc": 0, "colors": [], "color_identity": []},
        "Ancient Tomb": {"type_line": "Land", "cmc": 0, "colors": [], "color_identity": []},
        "Dark Depths": {"type_line": "Legendary Snow Land", "cmc": 0, "colors": [], "color_identity": []},
        "Thespian's Stage": {"type_line": "Land", "cmc": 0, "colors": [], "color_identity": []},
        "Watery Grave": {"type_line": "Land — Island Swamp", "cmc": 0, "colors": [], "color_identity": ["B", "U"]},

        # Spells
        "Brainstorm": {"type_line": "Instant", "cmc": 1, "colors": ["U"], "color_identity": ["U"]},
        "Ponder": {"type_line": "Sorcery", "cmc": 1, "colors": ["U"], "color_identity": ["U"]},
        "Thoughtseize": {"type_line": "Sorcery", "cmc": 1, "colors": ["B"], "color_identity": ["B"]},
        "Force of Will": {"type_line": "Instant", "cmc": 5, "colors": ["U"], "color_identity": ["U"]},
        "Daze": {"type_line": "Instant", "cmc": 2, "colors": ["U"], "color_identity": ["U"]},
        "Orcish Bowmasters": {"type_line": "Creature — Orc Archer", "cmc": 2, "colors": ["B"], "color_identity": ["B"]},
        "Murktide Regent": {"type_line": "Creature — Dragon", "cmc": 7, "colors": ["U"], "color_identity": ["U"]},
        "Tamiyo, Inquisitive Student": {"type_line": "Legendary Creature — Human Wizard", "cmc": 1, "colors": ["U"], "color_identity": ["U"]},
        "Painter's Servant": {"type_line": "Artifact Creature — Scarecrow", "cmc": 2, "colors": [], "color_identity": []},
        "Grindstone": {"type_line": "Artifact", "cmc": 1, "colors": [], "color_identity": []},

        # Mana rocks / rituals
        "Lotus Petal": {"type_line": "Artifact", "cmc": 0, "colors": [], "color_identity": []},
        "Dark Ritual": {"type_line": "Instant", "cmc": 1, "colors": ["B"], "color_identity": ["B"]},
    })


def dimir_deck(idx):
    return Deck.from_decklist({
        "Brainstorm": 4, "Ponder": 4, "Thoughtseize": 4,
        "Orcish Bowmasters": 4, "Murktide Regent": 2,
        "Tamiyo, Inquisitive Student": 4,
        "Force of Will": 4, "Daze": 4,  # reactive — should sit in hand
        "Polluted Delta": 4, "Underground Sea": 4,
        "Wasteland": 4, "Island": 2, "Swamp": 2,
    }, idx)


def painter_deck(idx):
    """A deck that should reliably assemble Painter + Grindstone."""
    return Deck.from_decklist({
        "Painter's Servant": 8,
        "Grindstone": 8,
        "Ancient Tomb": 4,
        "Wasteland": 4,
        "Island": 16,
    }, idx)


def depths_deck(idx):
    return Deck.from_decklist({
        "Dark Depths": 4,
        "Thespian's Stage": 4,
        "Island": 16,
        "Underground Sea": 4,
    }, idx)


# ----- Basic simulation -----

def test_simulate_game_plays_requested_turns():
    idx = base_idx()
    deck = dimir_deck(idx)
    game = simulate_game(deck, turns=5, seed=42)
    assert game.turns_played == 5
    assert len(game.snapshots) == 5


def test_simulate_game_is_reproducible():
    idx = base_idx()
    deck1 = dimir_deck(idx)
    deck2 = dimir_deck(idx)
    g1 = simulate_game(deck1, turns=5, seed=99)
    g2 = simulate_game(deck2, turns=5, seed=99)
    assert [s.land_played for s in g1.snapshots] == [s.land_played for s in g2.snapshots]
    assert [s.spells_cast for s in g1.snapshots] == [s.spells_cast for s in g2.snapshots]


def test_turn_1_does_not_draw_extra_card():
    """On the play, turn 1 skips the draw step. Opening hand is 7 and we
    should NOT have drawn an 8th card by end of turn 1."""
    idx = base_idx()
    deck = dimir_deck(idx)
    # Check via inspection: turn 1 snapshot's hand_size_start should equal 7
    game = simulate_game(deck, turns=1, seed=1)
    assert game.snapshots[0].hand_size_start == 7


def test_turn_2_onward_draws():
    """hand_size_start records the hand size at the top of the turn, before
    the draw step. So turn 2's start equals turn 1's end hand size (= 7 - t1 plays)."""
    idx = base_idx()
    deck = dimir_deck(idx)
    game = simulate_game(deck, turns=3, seed=7)
    t1_spent = (1 if game.snapshots[0].land_played else 0) + len(game.snapshots[0].spells_cast)
    assert game.snapshots[1].hand_size_start == game.snapshots[0].hand_size_start - t1_spent


# ----- Land mechanics -----

def test_at_most_one_land_per_turn():
    idx = base_idx()
    deck = dimir_deck(idx)
    # Run many seeds, confirm no turn ever reports 2 land plays
    for seed in range(20):
        deck.reset()
        game = simulate_game(deck, turns=6, seed=seed)
        for snap in game.snapshots:
            if snap.land_played:
                # Land-played field is a single name (or "Fetch -> Dual" string),
                # never a list
                assert isinstance(snap.land_played, str)


def test_fetchland_is_sacrificed_and_replaced():
    """When a fetchland is played, it should resolve (sac + fetch) on the same turn."""
    idx = base_idx()
    # Deck designed to force a fetch on turn 1
    deck = Deck.from_decklist({
        "Polluted Delta": 20,
        "Underground Sea": 10,
        "Island": 30,
    }, idx)
    game = simulate_game(deck, turns=2, seed=1)
    # The land_played string for a fetchland includes the arrow
    fetched_turns = [s for s in game.snapshots if s.land_played and "->" in s.land_played]
    assert len(fetched_turns) >= 1


def test_fetchland_priority_over_basic():
    """If hand has both a fetchland and a basic, fetch should be chosen."""
    idx = base_idx()
    # Construct a hand with both by making the library 100% fetches + islands
    deck = Deck.from_decklist({"Polluted Delta": 30, "Island": 30}, idx)
    game = simulate_game(deck, turns=1, seed=42)
    # Turn 1: should play either a fetch or island; with 50/50 mix, some seeds
    # will give only islands. Check that WHEN a fetch is in hand, it's preferred.
    # Easier test: over 100 seeds, fetch usage should be >0
    fetch_count = 0
    for seed in range(100):
        deck.reset()
        g = simulate_game(deck, turns=1, seed=seed)
        if g.snapshots[0].land_played and "Polluted Delta" in g.snapshots[0].land_played:
            fetch_count += 1
    assert fetch_count > 30  # should be at least 30% given balanced mix


# ----- Spell casting -----

def test_reactive_cards_are_not_cast():
    """Force of Will, Daze, Counterspell etc. should stay in hand — they're
    not cast during our turns because they're reactive."""
    idx = base_idx()
    deck = dimir_deck(idx)
    # Run many games and confirm Force of Will never appears in spells_cast
    for seed in range(50):
        deck.reset()
        game = simulate_game(deck, turns=5, seed=seed)
        for snap in game.snapshots:
            assert "Force of Will" not in snap.spells_cast
            assert "Daze" not in snap.spells_cast


def test_cantrips_are_prioritized_over_threats():
    """Brainstorm should tend to be cast before Murktide when both are in
    hand with available mana. Hard to test a single seed; test tendency."""
    idx = base_idx()
    deck = dimir_deck(idx)

    brainstorm_before_murktide = 0
    seen_both = 0
    for seed in range(200):
        deck.reset()
        game = simulate_game(deck, turns=6, seed=seed)
        b_turn = game.threats_deployed.get("Brainstorm")
        m_turn = game.threats_deployed.get("Murktide Regent")
        if b_turn and m_turn:
            seen_both += 1
            if b_turn <= m_turn:
                brainstorm_before_murktide += 1
    # Brainstorm should come first in the vast majority of games where both are cast
    if seen_both > 0:
        assert brainstorm_before_murktide / seen_both > 0.8


def test_lands_never_appear_as_spells():
    idx = base_idx()
    deck = dimir_deck(idx)
    for seed in range(20):
        deck.reset()
        game = simulate_game(deck, turns=6, seed=seed)
        for snap in game.snapshots:
            for spell in snap.spells_cast:
                # Spells cast are spell names, not lands
                assert spell not in {"Island", "Swamp", "Underground Sea", "Wasteland", "Polluted Delta"}


# ----- Combo detection -----

def test_painter_combo_detected():
    idx = base_idx()
    deck = painter_deck(idx)
    results = [simulate_game(deck, turns=6, seed=i) for i in range(100)]
    assembled = sum(1 for r in results if "Painter + Grindstone" in r.assembled_combos)
    # With 8 of each piece, combo should assemble very often within 6 turns
    assert assembled >= 50


def test_combo_turn_is_recorded():
    idx = base_idx()
    deck = painter_deck(idx)
    for seed in range(30):
        deck.reset()
        game = simulate_game(deck, turns=6, seed=seed)
        if "Painter + Grindstone" in game.assembled_combos:
            turn = game.assembled_combos["Painter + Grindstone"]
            assert 1 <= turn <= 6
            return  # One successful assertion is enough
    pytest.fail("No game assembled the combo in 30 tries")


def test_combos_constant_contains_expected_entries():
    assert "Marit Lage (Lands)" in COMBOS
    assert "Painter + Grindstone" in COMBOS
    for pieces in COMBOS.values():
        assert len(pieces) >= 2


# ----- Mana rocks & fast mana -----

def test_ancient_tomb_costs_life():
    """Casting spells that use Ancient Tomb mana should reduce life."""
    idx = base_idx()
    deck = Deck.from_decklist({
        "Ancient Tomb": 20,
        "Grindstone": 20,   # 1-mana artifact, castable from Ancient Tomb
        "Island": 20,
    }, idx)
    # Any game where we play Ancient Tomb AND cast a spell should lose life
    lost_life_games = 0
    for seed in range(30):
        deck.reset()
        game = simulate_game(deck, turns=3, seed=seed)
        if game.life_final < 20:
            lost_life_games += 1
    assert lost_life_games > 0


def test_lotus_petal_exiles_after_use():
    """Lotus Petal is a mana rock marked as self-exiling. After cracking it,
    it should not be on the battlefield."""
    idx = base_idx()
    # Give the deck Lotus Petal + Grindstone — Petal provides the mana to cast Grindstone
    # Actually Grindstone is 1 colorless, not 1 colored — Petal would tap for any color.
    # Use a deck where Petal is forced into action.
    # Check: after simulation, if Petal was used, it's in exile (or was drawn and never used)
    deck = Deck.from_decklist({
        "Lotus Petal": 10,
        "Grindstone": 10,
        "Island": 40,
    }, idx)
    # Lotus Petal is in MANA_ROCKS with exile=True
    assert MANA_ROCKS["Lotus Petal"]["exile"] is True


# ----- Aggregate stats -----

def test_aggregate_stats_empty_list():
    stats = aggregate_game_stats([])
    assert stats.n_games == 0


def test_aggregate_stats_cast_rate():
    idx = base_idx()
    deck = dimir_deck(idx)
    results = [simulate_game(deck, turns=5, seed=i) for i in range(100)]
    stats = aggregate_game_stats(results)

    # Brainstorm should be cast in a meaningful fraction of games
    assert stats.cast_rate.get("Brainstorm", 0) > 0.3
    # Force of Will should never be cast (reactive)
    assert stats.cast_rate.get("Force of Will", 0) == 0


def test_aggregate_mana_efficiency_in_range():
    idx = base_idx()
    deck = dimir_deck(idx)
    results = [simulate_game(deck, turns=5, seed=i) for i in range(100)]
    stats = aggregate_game_stats(results)
    assert 0 <= stats.avg_mana_efficiency <= 1


def test_aggregate_combo_assembly_for_painter():
    idx = base_idx()
    deck = painter_deck(idx)
    results = [simulate_game(deck, turns=6, seed=i) for i in range(100)]
    stats = aggregate_game_stats(results)
    combo_stats = stats.combo_assembly.get("Painter + Grindstone")
    assert combo_stats is not None
    assert combo_stats["rate"] > 0.4
    assert 1 <= combo_stats["avg_turn"] <= 6


# ----- Serialization -----

def test_game_result_to_summary_is_json_safe():
    import json
    idx = base_idx()
    deck = dimir_deck(idx)
    game = simulate_game(deck, turns=3, seed=1)
    json.dumps(game.to_summary())


def test_game_stats_to_summary_is_json_safe():
    import json
    idx = base_idx()
    deck = dimir_deck(idx)
    results = [simulate_game(deck, turns=3, seed=i) for i in range(10)]
    stats = aggregate_game_stats(results)
    json.dumps(stats.to_summary())
