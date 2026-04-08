"""Tests for the card name index and fuzzy matching."""

import os
import pickle
import pytest
from src.card_index import CardIndex

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INDEX_EXISTS = os.path.exists(os.path.join(DATA_DIR, "card_index.pkl"))
SCRYFALL_EXISTS = os.path.exists(os.path.join(DATA_DIR, "scryfall-cards.json"))


@pytest.fixture(scope="module")
def index():
    """Load the card index. Skip if not built yet."""
    if not INDEX_EXISTS:
        pytest.skip("Card index not built (run python src/card_index.py first)")
    idx = CardIndex()
    idx.load()
    return idx


@pytest.fixture
def empty_index():
    """An empty CardIndex for testing without data."""
    return CardIndex()


# --- Construction and loading ---


class TestIndexConstruction:
    def test_empty_index_has_no_cards(self, empty_index):
        assert len(empty_index.cards) == 0
        assert len(empty_index.names) == 0
        assert len(empty_index.legacy_legal) == 0

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_load_populates_cards(self, index):
        assert len(index.cards) > 30000
        assert len(index.names) > 30000
        assert len(index.legacy_legal) > 25000

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_names_are_sorted(self, index):
        assert index.names == sorted(index.names)

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_legacy_legal_is_subset_of_all_cards(self, index):
        assert index.legacy_legal.issubset(set(index.names))

    @pytest.mark.skipif(not SCRYFALL_EXISTS, reason="Scryfall data not available")
    def test_build_from_scryfall(self, tmp_path):
        """Build a mini index from the real Scryfall data and verify it works."""
        idx = CardIndex()
        idx.build(os.path.join(DATA_DIR, "scryfall-cards.json"))
        assert len(idx.cards) > 30000
        assert "Force of Will" in idx.cards
        assert "Force of Will" in idx.legacy_legal


# --- Exact lookup ---


class TestExactLookup:
    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_get_existing_card(self, index):
        card = index.get("Force of Will")
        assert card is not None
        assert card["name"] == "Force of Will"
        assert card["mana_cost"] == "{3}{U}{U}"
        assert "Instant" in card["type_line"]

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_get_nonexistent_card(self, index):
        assert index.get("Totally Fake Card Name") is None

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_get_card_has_required_fields(self, index):
        card = index.get("Brainstorm")
        assert card is not None
        required_fields = [
            "name", "mana_cost", "cmc", "type_line", "oracle_text",
            "colors", "color_identity", "legalities", "image_uris",
        ]
        for field in required_fields:
            assert field in card, f"Missing field: {field}"

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_get_card_oracle_text(self, index):
        card = index.get("Brainstorm")
        assert "Draw three cards" in card["oracle_text"]

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_get_split_card(self, index):
        """Split cards use 'Name A // Name B' format."""
        card = index.get("Fire // Ice")
        if card:  # May not exist in all Scryfall dumps
            assert "//" in card["name"]


# --- Legacy legality ---


class TestLegality:
    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_legal_card(self, index):
        assert index.is_legacy_legal("Force of Will")
        assert index.is_legacy_legal("Brainstorm")
        assert index.is_legacy_legal("Wasteland")

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_banned_card_is_not_legal(self, index):
        # These are banned in Legacy
        assert not index.is_legacy_legal("Black Lotus")
        assert not index.is_legacy_legal("Ancestral Recall")

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_nonexistent_card_is_not_legal(self, index):
        assert not index.is_legacy_legal("Totally Fake Card")

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_recently_banned_cards(self, index):
        """Cards banned in Legacy should not be legal."""
        banned_cards = [
            "Sensei's Divining Top", "Deathrite Shaman", "Gitaxian Probe",
            "Wrenn and Six", "Ragavan, Nimble Pilferer", "Entomb",
        ]
        for card in banned_cards:
            assert not index.is_legacy_legal(card), f"{card} should be banned"

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_legacy_staples_are_legal(self, index):
        staples = [
            "Force of Will", "Brainstorm", "Ponder", "Wasteland", "Daze",
            "Swords to Plowshares", "Lightning Bolt", "Dark Ritual",
            "Orcish Bowmasters", "Murktide Regent",
            "Chalice of the Void", "Show and Tell", "Lotus Petal",
        ]
        for card in staples:
            assert index.is_legacy_legal(card), f"{card} should be legal"

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_double_faced_cards_are_legal(self, index):
        """Double-faced cards use 'Front // Back' naming in Scryfall."""
        results = index.search("Delver of Secrets", limit=1)
        assert len(results) > 0
        name = results[0][0]
        assert index.is_legacy_legal(name), f"{name} should be legal"


# --- Fuzzy search ---


class TestFuzzySearch:
    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_exact_name_returns_high_score(self, index):
        results = index.search("Force of Will")
        assert len(results) > 0
        assert results[0][0] == "Force of Will"
        assert results[0][1] > 90

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_typo_still_matches(self, index):
        results = index.search("Forse of Will")
        assert len(results) > 0
        assert results[0][0] == "Force of Will"

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_partial_name_matches(self, index):
        results = index.search("Murktide")
        assert any("Murktide" in name for name, _ in results)

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_lowercase_matches(self, index):
        results = index.search("underground sea")
        assert any("Underground Sea" in name for name, _ in results)

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_limit_parameter(self, index):
        results = index.search("bolt", limit=2)
        assert len(results) <= 2

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_threshold_filters_bad_matches(self, index):
        results = index.search("xyzzy", threshold=90)
        assert len(results) == 0

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_legacy_only_filter(self, index):
        results = index.search("Force of Will", legacy_only=True)
        for name, _ in results:
            assert index.is_legacy_legal(name)

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_common_misspellings(self, index):
        misspellings = {
            "brainstom": "Brainstorm",
            "wastland": "Wasteland",
            "Orcish Bowmaster": "Orcish Bowmasters",
            "Show and Tel": "Show and Tell",
            "Thoughseize": "Thoughtseize",
        }
        for typo, expected in misspellings.items():
            results = index.search(typo, limit=1)
            assert len(results) > 0, f"No match for '{typo}'"
            assert results[0][0] == expected, (
                f"'{typo}' matched '{results[0][0]}' instead of '{expected}'"
            )


# --- Text resolution ---


class TestTextResolution:
    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_resolve_finds_cards_in_text(self, index):
        text = "I cast Force of Will pitching Brainstorm to counter their Show and Tell"
        cards = index.resolve(text)
        names = {c["name"] for c in cards}
        assert "Force of Will" in names
        assert "Brainstorm" in names
        assert "Show and Tell" in names

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_resolve_empty_text(self, index):
        assert index.resolve("") == []

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_resolve_no_cards_in_text(self, index):
        assert index.resolve("the weather is nice today") == []

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_resolve_deduplicates(self, index):
        text = "Force of Will counters Force of Will"
        cards = index.resolve(text)
        names = [c["name"] for c in cards]
        assert names.count("Force of Will") == 1

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_resolve_legacy_only(self, index):
        text = "I play Force of Will and Black Lotus"
        cards = index.resolve(text, legacy_only=True)
        names = {c["name"] for c in cards}
        assert "Force of Will" in names
        # Black Lotus is banned, shouldn't appear in legacy_only mode
        assert "Black Lotus" not in names


# --- Scryfall image URL ---


class TestScryfallImageUrl:
    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_image_url_for_existing_card(self, index):
        url = index.scryfall_image_url("Force of Will")
        assert url is not None
        assert "scryfall" in url or "cards" in url

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_image_url_for_nonexistent_card(self, index):
        url = index.scryfall_image_url("Totally Fake Card")
        assert url is None

    @pytest.mark.skipif(not INDEX_EXISTS, reason="Index not built")
    def test_image_url_version_parameter(self, index):
        url_normal = index.scryfall_image_url("Force of Will", version="normal")
        url_small = index.scryfall_image_url("Force of Will", version="small")
        if url_normal and url_small:
            assert url_normal != url_small
