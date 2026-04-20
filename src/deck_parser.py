"""
Deck import parser.

Parses decklists from plain text, Moxfield URLs, and MTGGoldfish URLs
into a structured format with card resolution via the card index.

Supported formats:
    - Plain text: "4 Brainstorm" (one per line or comma-separated)
    - Markdown: "- 4 [Brainstorm](link)"
    - Moxfield URL: https://www.moxfield.com/decks/{id}
    - MTGGoldfish URL: https://www.mtggoldfish.com/deck/{id}

Usage:
    from src.deck_parser import parse_decklist, import_from_url

    deck = parse_decklist("4 Brainstorm\\n4 Ponder\\n...")
    deck = await import_from_url("https://www.moxfield.com/decks/abc123")
"""

import re
from dataclasses import dataclass, field

import httpx


@dataclass
class DeckEntry:
    quantity: int
    name: str


@dataclass
class Decklist:
    main: list[DeckEntry] = field(default_factory=list)
    sideboard: list[DeckEntry] = field(default_factory=list)

    @property
    def main_count(self) -> int:
        return sum(e.quantity for e in self.main)

    @property
    def side_count(self) -> int:
        return sum(e.quantity for e in self.sideboard)

    def to_text(self) -> str:
        """Export as plain text decklist."""
        lines = []
        for entry in self.main:
            lines.append(f"{entry.quantity} {entry.name}")
        if self.sideboard:
            lines.append("")
            lines.append("Sideboard:")
            for entry in self.sideboard:
                lines.append(f"{entry.quantity} {entry.name}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "main": [{"quantity": e.quantity, "name": e.name} for e in self.main],
            "sideboard": [{"quantity": e.quantity, "name": e.name} for e in self.sideboard],
            "main_count": self.main_count,
            "side_count": self.side_count,
        }


# ---------------------------------------------------------------------------
# Plain text parsing
# ---------------------------------------------------------------------------

# Matches: "4 Brainstorm", "4x Brainstorm", "- 4 [Brainstorm](link)"
_CARD_LINE = re.compile(
    r"^[-*]?\s*(\d+)\s*[xX]?\s+"  # quantity (with optional bullet/x)
    r"\[?([^\]\n]+?)\]?"           # card name (with optional markdown brackets)
    r"(?:\(.*?\))?\s*$"            # optional markdown link in parens
)

_SIDEBOARD_HEADER = re.compile(
    r"^\s*(?:sideboard|side\s*board|sb)\s*:?\s*$", re.IGNORECASE
)

_MAIN_HEADER = re.compile(
    r"^\s*(?:main\s*(?:deck|board)?|maindeck|deck)\s*:?\s*$", re.IGNORECASE
)


def parse_decklist(text: str) -> Decklist:
    """Parse a decklist from plain text.

    Handles:
        - One card per line: "4 Brainstorm"
        - With x: "4x Brainstorm"
        - Markdown bullets: "- 4 [Brainstorm](link)"
        - Comma-separated: "4 Brainstorm, 4 Ponder, 3 Force of Will"
        - Sideboard section after "Sideboard:" header
    """
    # Card names legitimately contain commas: "Phlage, Titan of Fire's Fury",
    # "Ragavan, Nimble Pilferer", "Ajani, Nacatl Pariah", etc. We can only
    # treat a comma as a separator if EVERY comma-delimited part independently
    # looks like a "N CardName" line. Otherwise the first card with a comma
    # in its name gets truncated at the comma.
    def _all_parts_look_like_cards(raw: str) -> bool:
        parts = [p.strip() for p in raw.split(",")]
        return len(parts) > 1 and all(_CARD_LINE.match(p) for p in parts)

    # If comma-separated on a single line with no newlines, split only if
    # every part is a valid card line ("4 Brainstorm, 4 Ponder, 3 FoW").
    if "\n" not in text.strip() and "," in text and _all_parts_look_like_cards(text):
        text = text.replace(",", "\n")

    # Same guard for mixed-format input with newlines AND commas.
    lines = []
    for raw_line in text.strip().splitlines():
        if "," in raw_line and _all_parts_look_like_cards(raw_line):
            lines.extend(part.strip() for part in raw_line.split(","))
        else:
            lines.append(raw_line)

    deck = Decklist()
    in_sideboard = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if _SIDEBOARD_HEADER.match(line):
            in_sideboard = True
            continue

        if _MAIN_HEADER.match(line):
            in_sideboard = False
            continue

        # Skip markdown headers and other non-card lines
        if line.startswith("#") or line.startswith("**"):
            if "sideboard" in line.lower() or "side board" in line.lower():
                in_sideboard = True
            elif "main" in line.lower() or "deck" in line.lower():
                in_sideboard = False
            continue

        match = _CARD_LINE.match(line)
        if not match:
            continue

        quantity = int(match.group(1))
        name = match.group(2).strip()

        entry = DeckEntry(quantity=quantity, name=name)
        if in_sideboard:
            deck.sideboard.append(entry)
        else:
            deck.main.append(entry)

    return deck


# ---------------------------------------------------------------------------
# URL imports
# ---------------------------------------------------------------------------


async def import_from_url(url: str) -> Decklist:
    """Import a decklist from a Moxfield or MTGGoldfish URL."""
    if "moxfield.com" in url:
        return await _import_moxfield(url)
    elif "mtggoldfish.com" in url:
        return await _import_mtggoldfish(url)
    else:
        raise ValueError(f"Unsupported URL: {url}. Use Moxfield or MTGGoldfish.")


async def _import_moxfield(url: str) -> Decklist:
    """Import from Moxfield API.

    URL format: https://www.moxfield.com/decks/{deck_id}
    API: https://api2.moxfield.com/v3/decks/all/{deck_id}
    """
    # Extract deck ID from URL
    match = re.search(r"moxfield\.com/decks/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise ValueError(f"Could not extract deck ID from Moxfield URL: {url}")

    deck_id = match.group(1)
    api_url = f"https://api2.moxfield.com/v3/decks/all/{deck_id}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            api_url,
            headers={"User-Agent": "The-Legacy-Deckbuilder/1.0"},
        )
        if resp.status_code != 200:
            raise ValueError(
                f"Moxfield API error ({resp.status_code}): {resp.text}"
            )
        data = resp.json()

    deck = Decklist()

    # Main deck
    for card_name, card_data in data.get("mainboard", {}).items():
        qty = card_data.get("quantity", 1)
        deck.main.append(DeckEntry(quantity=qty, name=card_name))

    # Sideboard
    for card_name, card_data in data.get("sideboard", {}).items():
        qty = card_data.get("quantity", 1)
        deck.sideboard.append(DeckEntry(quantity=qty, name=card_name))

    return deck


async def _import_mtggoldfish(url: str) -> Decklist:
    """Import from MTGGoldfish download endpoint.

    URL format: https://www.mtggoldfish.com/deck/{deck_id}
    Download: https://www.mtggoldfish.com/deck/download/{deck_id}
    """
    # Extract deck ID from URL
    match = re.search(r"mtggoldfish\.com/(?:deck|archetype)/(?:download/)?(\d+)", url)
    if not match:
        raise ValueError(
            f"Could not extract deck ID from MTGGoldfish URL: {url}"
        )

    deck_id = match.group(1)
    download_url = f"https://www.mtggoldfish.com/deck/download/{deck_id}"

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        resp = await client.get(
            download_url,
            headers={"User-Agent": "The-Legacy-Deckbuilder/1.0"},
        )
        if resp.status_code != 200:
            raise ValueError(
                f"MTGGoldfish error ({resp.status_code}): {resp.text}"
            )

    return parse_decklist(resp.text)
