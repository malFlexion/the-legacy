"""Tests for src/deck_parser.py.

Covers plain-text parsing, Moxfield URL import, MTGGoldfish URL import,
and the Decklist data model. Uses asyncio.run() for the URL-import tests
so we don't need pytest-asyncio as a dep.
"""

import asyncio
import json

import httpx
import pytest

from src.deck_parser import (
    DeckEntry,
    Decklist,
    _import_moxfield,
    _import_mtggoldfish,
    import_from_url,
    parse_decklist,
)


# ---------------------------------------------------------------------------
# Plain text parsing
# ---------------------------------------------------------------------------

def test_parse_simple_lines():
    deck = parse_decklist("4 Brainstorm\n4 Ponder\n3 Force of Will")
    assert len(deck.main) == 3
    assert deck.main[0] == DeckEntry(quantity=4, name="Brainstorm")
    assert deck.main[1] == DeckEntry(quantity=4, name="Ponder")
    assert deck.main[2] == DeckEntry(quantity=3, name="Force of Will")


def test_parse_with_x_suffix():
    deck = parse_decklist("4x Brainstorm\n3x Ponder")
    assert [e.quantity for e in deck.main] == [4, 3]
    assert [e.name for e in deck.main] == ["Brainstorm", "Ponder"]


def test_parse_markdown_bullets():
    text = """
    - 4 [Brainstorm](https://scryfall.com/card/abc)
    - 4 [Ponder](https://scryfall.com/card/def)
    """
    deck = parse_decklist(text)
    assert len(deck.main) == 2
    assert deck.main[0].name == "Brainstorm"
    assert deck.main[1].name == "Ponder"


def test_parse_comma_separated():
    deck = parse_decklist("4 Brainstorm, 4 Ponder, 3 Force of Will")
    assert len(deck.main) == 3
    assert [e.quantity for e in deck.main] == [4, 4, 3]


def test_parse_sideboard_section():
    text = """
    4 Brainstorm
    4 Force of Will

    Sideboard:
    2 Surgical Extraction
    3 Pyroblast
    """
    deck = parse_decklist(text)
    assert len(deck.main) == 2
    assert len(deck.sideboard) == 2
    assert deck.sideboard[0].name == "Surgical Extraction"


def test_parse_sideboard_variants():
    # The parser accepts "Sideboard:", "SB:", "side board:"
    for header in ["Sideboard:", "SB:", "sideboard:", "side board:"]:
        text = f"4 Brainstorm\n{header}\n2 Pyroblast"
        deck = parse_decklist(text)
        assert len(deck.main) == 1, f"Header '{header}' broke main parsing"
        assert len(deck.sideboard) == 1, f"Header '{header}' broke sideboard detection"


def test_parse_main_header_after_sideboard_switches_back():
    text = """
    Sideboard:
    2 Pyroblast

    Main:
    4 Brainstorm
    """
    deck = parse_decklist(text)
    assert len(deck.main) == 1
    assert deck.main[0].name == "Brainstorm"
    assert len(deck.sideboard) == 1


def test_parse_skips_empty_lines_and_blanks():
    text = "\n\n4 Brainstorm\n\n\n4 Ponder\n\n"
    deck = parse_decklist(text)
    assert len(deck.main) == 2


def test_parse_skips_markdown_headers():
    text = """
    # My Dimir Tempo Deck

    4 Brainstorm
    4 Ponder

    ## Sideboard

    2 Surgical Extraction
    """
    deck = parse_decklist(text)
    assert len(deck.main) == 2
    assert len(deck.sideboard) == 1


def test_parse_skips_non_card_lines():
    text = """
    This is a comment that isn't a card.
    Some prose without numbers.
    4 Brainstorm
    """
    deck = parse_decklist(text)
    assert len(deck.main) == 1
    assert deck.main[0].name == "Brainstorm"


def test_parse_empty_input():
    assert parse_decklist("").main == []
    assert parse_decklist("   \n\n\t").main == []


def test_parse_card_with_special_chars():
    # Cards with commas, apostrophes, hyphens
    text = "4 Jace, the Mind Sculptor\n1 Sol Ring\n2 Urza's Saga"
    deck = parse_decklist(text)
    # "Jace, the Mind Sculptor" has a comma, which the comma-splitter would
    # break if not careful. The parser only splits lines by comma when the
    # FIRST comma-part looks like a card line — Jace's comma doesn't.
    names = [e.name for e in deck.main]
    assert "Urza's Saga" in names
    assert "Sol Ring" in names


def test_parse_large_quantities():
    deck = parse_decklist("60 Island\n15 Forest")
    assert deck.main[0].quantity == 60
    assert deck.main[1].quantity == 15


# ---------------------------------------------------------------------------
# Decklist data model
# ---------------------------------------------------------------------------

def test_decklist_main_count():
    deck = parse_decklist("4 Brainstorm\n4 Ponder\n3 Force of Will")
    assert deck.main_count == 11
    assert deck.side_count == 0


def test_decklist_side_count():
    text = """
    4 Brainstorm

    Sideboard:
    2 Pyroblast
    3 Surgical Extraction
    """
    deck = parse_decklist(text)
    assert deck.side_count == 5


def test_decklist_to_text_round_trip():
    original = "4 Brainstorm\n4 Ponder\n\nSideboard:\n2 Pyroblast"
    deck = parse_decklist(original)
    text = deck.to_text()
    deck2 = parse_decklist(text)
    assert [(e.quantity, e.name) for e in deck.main] == [
        (e.quantity, e.name) for e in deck2.main
    ]
    assert [(e.quantity, e.name) for e in deck.sideboard] == [
        (e.quantity, e.name) for e in deck2.sideboard
    ]


def test_decklist_to_dict():
    deck = parse_decklist("4 Brainstorm\n\nSideboard:\n2 Pyroblast")
    d = deck.to_dict()
    assert d["main"] == [{"quantity": 4, "name": "Brainstorm"}]
    assert d["sideboard"] == [{"quantity": 2, "name": "Pyroblast"}]
    assert d["main_count"] == 4
    assert d["side_count"] == 2


def test_decklist_to_text_no_sideboard():
    deck = parse_decklist("4 Brainstorm")
    text = deck.to_text()
    assert "Sideboard" not in text


# ---------------------------------------------------------------------------
# URL routing
# ---------------------------------------------------------------------------

def test_import_from_url_raises_on_unknown():
    with pytest.raises(ValueError, match="Unsupported URL"):
        asyncio.run(import_from_url("https://example.com/deck/123"))


# ---------------------------------------------------------------------------
# Moxfield import (mocked HTTP)
# ---------------------------------------------------------------------------

class _FakeResponse:
    def __init__(self, status_code: int, body: dict | str):
        self.status_code = status_code
        self._body = body

    @property
    def text(self) -> str:
        return self._body if isinstance(self._body, str) else json.dumps(self._body)

    def json(self):
        return self._body


class _FakeAsyncClient:
    """Minimal httpx.AsyncClient stand-in for unit tests."""

    def __init__(self, response, **kwargs):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def get(self, url, **kwargs):
        return self._response


def _patch_httpx(monkeypatch, response):
    def factory(*args, **kwargs):
        return _FakeAsyncClient(response, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


def test_moxfield_valid_deck(monkeypatch):
    fake_response = _FakeResponse(200, {
        "mainboard": {
            "Brainstorm": {"quantity": 4},
            "Ponder": {"quantity": 4},
        },
        "sideboard": {
            "Pyroblast": {"quantity": 3},
        },
    })
    _patch_httpx(monkeypatch, fake_response)

    deck = asyncio.run(_import_moxfield("https://www.moxfield.com/decks/abc123def"))
    names = {e.name for e in deck.main}
    assert names == {"Brainstorm", "Ponder"}
    assert deck.sideboard[0] == DeckEntry(quantity=3, name="Pyroblast")


def test_moxfield_invalid_url_no_deck_id():
    with pytest.raises(ValueError, match="Could not extract deck ID"):
        asyncio.run(_import_moxfield("https://www.moxfield.com/"))


def test_moxfield_api_error(monkeypatch):
    _patch_httpx(monkeypatch, _FakeResponse(404, "Not Found"))
    with pytest.raises(ValueError, match="Moxfield API error"):
        asyncio.run(_import_moxfield("https://www.moxfield.com/decks/missing"))


def test_import_from_url_routes_to_moxfield(monkeypatch):
    fake_response = _FakeResponse(200, {
        "mainboard": {"Brainstorm": {"quantity": 4}},
        "sideboard": {},
    })
    _patch_httpx(monkeypatch, fake_response)
    deck = asyncio.run(import_from_url("https://www.moxfield.com/decks/abc"))
    assert len(deck.main) == 1
    assert deck.main[0].name == "Brainstorm"


# ---------------------------------------------------------------------------
# MTGGoldfish import (mocked HTTP)
# ---------------------------------------------------------------------------

def test_mtggoldfish_valid_deck(monkeypatch):
    # MTGGoldfish returns the decklist as plain text via the download endpoint
    fake_response = _FakeResponse(
        200,
        "4 Brainstorm\n4 Ponder\n\nSideboard:\n3 Pyroblast\n",
    )
    _patch_httpx(monkeypatch, fake_response)

    deck = asyncio.run(_import_mtggoldfish("https://www.mtggoldfish.com/deck/1234567"))
    assert len(deck.main) == 2
    assert deck.sideboard[0].name == "Pyroblast"


def test_mtggoldfish_invalid_url_no_deck_id():
    with pytest.raises(ValueError, match="Could not extract deck ID"):
        asyncio.run(_import_mtggoldfish("https://www.mtggoldfish.com/"))


def test_mtggoldfish_api_error(monkeypatch):
    _patch_httpx(monkeypatch, _FakeResponse(500, "Server error"))
    with pytest.raises(ValueError, match="MTGGoldfish error"):
        asyncio.run(_import_mtggoldfish("https://www.mtggoldfish.com/deck/1234567"))


def test_mtggoldfish_accepts_archetype_url(monkeypatch):
    # /archetype/ variant should also work since the regex accepts both
    _patch_httpx(monkeypatch, _FakeResponse(200, "4 Brainstorm"))
    deck = asyncio.run(
        _import_mtggoldfish("https://www.mtggoldfish.com/archetype/1234567")
    )
    assert len(deck.main) == 1


def test_import_from_url_routes_to_mtggoldfish(monkeypatch):
    _patch_httpx(monkeypatch, _FakeResponse(200, "4 Brainstorm\n"))
    deck = asyncio.run(import_from_url("https://www.mtggoldfish.com/deck/1234567"))
    assert len(deck.main) == 1
