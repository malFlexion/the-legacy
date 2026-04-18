"""Tests for the budget substitution engine."""

import pytest

from src.budget_engine import (
    REPLACEMENTS,
    IRREPLACEABLE,
    BudgetEngine,
    Substitution,
)


class FakeCardIndex:
    """Minimal CardIndex stand-in for tests — no Scryfall dependency."""

    def __init__(self, prices: dict[str, float | None]):
        self.cards = {
            name: {"prices": {"usd": str(price) if price is not None else None}}
            for name, price in prices.items()
        }


@pytest.fixture
def engine():
    prices = {
        "Underground Sea": 650.00,
        "Watery Grave": 12.00,
        "Darkslick Shores": 4.00,
        "Underground River": 1.50,
        "Volcanic Island": 550.00,
        "Steam Vents": 12.00,
        "Force of Will": 85.00,
        "Force of Negation": 45.00,
        "Lion's Eye Diamond": 380.00,
        "Brainstorm": 1.50,
        "Ponder": 0.50,
        "Wasteland": 28.00,
        "Thoughtseize": 15.00,
        "Orcish Bowmasters": 40.00,
        "Murktide Regent": 35.00,
        "Dragon's Rage Channeler": 5.00,
        "Polluted Delta": 40.00,
        "Scalding Tarn": 40.00,
        "Misty Rainforest": 40.00,
        "Island": 0.25,
        "Swamp": 0.25,
    }
    return BudgetEngine(FakeCardIndex(prices))


# ----- Substitution lookups -----

def test_get_substitutions_for_known_card(engine):
    subs = engine.get_substitutions("Underground Sea")
    assert len(subs) == 3
    assert subs[0].replacement == "Watery Grave"


def test_get_substitutions_returns_empty_for_unknown_card(engine):
    assert engine.get_substitutions("Plains") == []


def test_irreplaceable_cards_have_no_subs_or_explicit_empty_list(engine):
    # LED is irreplaceable — either absent or has empty list
    led_subs = engine.get_substitutions("Lion's Eye Diamond")
    assert led_subs == []
    assert engine.is_irreplaceable("Lion's Eye Diamond")


def test_best_sub_listed_first(engine):
    # Shockland should come before pain land (smaller power_loss)
    subs = engine.get_substitutions("Underground Sea")
    assert subs[0].power_loss <= subs[-1].power_loss


# ----- Price lookup -----

def test_price_uses_usd_when_present(engine):
    assert engine.get_price("Brainstorm") == 1.50


def test_price_returns_none_for_unknown_card(engine):
    assert engine.get_price("Fictional Card") is None


def test_price_decklist_sums_across_copies(engine):
    decklist = {"Brainstorm": 4, "Ponder": 4, "Island": 10}
    # 4*1.50 + 4*0.50 + 10*0.25 = 6 + 2 + 2.5 = 10.5
    assert engine.price_decklist(decklist) == 10.5


# ----- Tier generation -----

def test_generate_tiers_produces_three_tiers(engine):
    decklist = {"Underground Sea": 4, "Brainstorm": 4, "Ponder": 4, "Island": 10}
    tiers = engine.generate_tiers(decklist)
    assert set(tiers.keys()) == {"full", "mid", "budget"}


def test_full_tier_is_unchanged(engine):
    decklist = {"Underground Sea": 4, "Brainstorm": 4}
    tiers = engine.generate_tiers(decklist)
    assert tiers["full"].decklist == decklist
    assert tiers["full"].substitutions_applied == []


def test_mid_tier_replaces_reserved_list_cards(engine):
    decklist = {"Underground Sea": 4, "Brainstorm": 4, "Wasteland": 4}
    tiers = engine.generate_tiers(decklist)
    # Underground Sea ($650) is above very_expensive threshold, gets replaced
    # Wasteland ($28) is below, stays
    assert "Underground Sea" not in tiers["mid"].decklist
    assert tiers["mid"].decklist.get("Watery Grave") == 4
    assert tiers["mid"].decklist.get("Wasteland") == 4


def test_budget_tier_replaces_more_aggressively(engine):
    decklist = {"Underground Sea": 4, "Force of Will": 4, "Murktide Regent": 4}
    tiers = engine.generate_tiers(decklist)
    # Budget threshold ($30) catches Murktide ($35), FoW ($85), Sea ($650)
    assert "Murktide Regent" not in tiers["budget"].decklist
    assert "Force of Will" not in tiers["budget"].decklist


def test_budget_price_lower_than_mid_lower_than_full(engine):
    decklist = {"Underground Sea": 4, "Force of Will": 4, "Brainstorm": 4}
    tiers = engine.generate_tiers(decklist)
    assert tiers["budget"].estimated_price_usd < tiers["mid"].estimated_price_usd
    assert tiers["mid"].estimated_price_usd < tiers["full"].estimated_price_usd


def test_tier_records_substitutions_applied(engine):
    decklist = {"Underground Sea": 4, "Brainstorm": 4}
    tiers = engine.generate_tiers(decklist)
    assert ("Underground Sea", "Watery Grave") in tiers["mid"].substitutions_applied


def test_irreplaceable_cards_flagged_not_substituted(engine):
    decklist = {"Lion's Eye Diamond": 4, "Brainstorm": 4}
    tiers = engine.generate_tiers(decklist)
    # LED stays in the deck but is flagged as irreplaceable
    assert tiers["budget"].decklist.get("Lion's Eye Diamond") == 4
    assert "Lion's Eye Diamond" in tiers["budget"].irreplaceable


def test_counts_merge_when_replacement_already_in_deck(engine):
    # If decklist has both original and its replacement, counts should merge
    decklist = {"Underground Sea": 2, "Watery Grave": 1}
    tiers = engine.generate_tiers(decklist)
    assert tiers["budget"].decklist.get("Watery Grave") == 3


# ----- Explanations -----

def test_explain_includes_prices_and_savings(engine):
    text = engine.explain_substitution("Underground Sea", "Watery Grave")
    assert "Underground Sea" in text
    assert "Watery Grave" in text
    assert "$650" in text
    assert "$12" in text
    assert "saves $638" in text


def test_explain_includes_tradeoffs(engine):
    text = engine.explain_substitution("Underground Sea", "Watery Grave")
    assert "2 life" in text.lower()


def test_explain_unknown_pair_returns_empty(engine):
    assert engine.explain_substitution("Unknown Card", "Also Unknown") == ""


# ----- Sanity checks on the REPLACEMENTS map itself -----

def test_every_replacement_has_at_least_one_tradeoff_or_notes():
    """A replacement with no trade-offs and no notes is suspicious —
    either it's actually irreplaceable or we forgot to document the downside."""
    for original, subs in REPLACEMENTS.items():
        for sub in subs:
            assert sub.tradeoffs or sub.notes, (
                f"{original} → {sub.replacement} has no trade-offs or notes documented"
            )


def test_power_loss_is_in_valid_range():
    for subs in REPLACEMENTS.values():
        for sub in subs:
            assert 0 <= sub.power_loss <= 10


def test_no_card_is_its_own_replacement():
    for original, subs in REPLACEMENTS.items():
        for sub in subs:
            assert sub.replacement != original


def test_irreplaceable_cards_are_known():
    """Sanity check: every card in IRREPLACEABLE should be a well-known expensive staple."""
    # These are hand-curated, so this is more of a documentation test
    assert "Lion's Eye Diamond" in IRREPLACEABLE
    assert "The Tabernacle at Pendrell Vale" in IRREPLACEABLE
