"""
Card name index for fuzzy matching.

Builds a searchable index of all Legacy-legal card names from
Scryfall bulk data. Supports fuzzy matching to resolve card names
from model output even with typos or partial names.

Usage:
    index = CardIndex()
    index.build()  # First time, builds from scryfall-cards.json
    index.load()   # Subsequent times, loads from disk

    results = index.search("Forse of Will")  # Fuzzy match
    # → [("Force of Will", 95.0), ...]

    card = index.get("Force of Will")  # Exact lookup
    # → {"name": "Force of Will", "mana_cost": "{3}{U}{U}", ...}
"""

import json
import os
import pickle
from rapidfuzz import fuzz, process

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INDEX_PATH = os.path.join(DATA_DIR, "card_index.pkl")


class CardIndex:
    def __init__(self):
        self.cards: dict[str, dict] = {}  # name -> card data
        self.names: list[str] = []  # sorted list for fuzzy matching
        self.legacy_legal: set[str] = set()  # names of Legacy-legal cards

    def build(self, scryfall_path: str | None = None):
        """Build the index from Scryfall bulk data JSON."""
        if scryfall_path is None:
            scryfall_path = os.path.join(DATA_DIR, "scryfall-cards.json")

        print(f"Loading Scryfall data from {scryfall_path}...")
        with open(scryfall_path, "r", encoding="utf-8") as f:
            cards_raw = json.load(f)

        print(f"Processing {len(cards_raw)} cards...")
        seen_names = set()

        for card in cards_raw:
            name = card.get("name", "")

            # Skip duplicates (same card from different sets)
            if name in seen_names:
                continue
            seen_names.add(name)

            # Extract the fields we care about
            entry = {
                "name": name,
                "mana_cost": card.get("mana_cost", ""),
                "cmc": card.get("cmc", 0),
                "type_line": card.get("type_line", ""),
                "oracle_text": card.get("oracle_text", ""),
                "colors": card.get("colors", []),
                "color_identity": card.get("color_identity", []),
                "keywords": card.get("keywords", []),
                "power": card.get("power"),
                "toughness": card.get("toughness"),
                "loyalty": card.get("loyalty"),
                "rarity": card.get("rarity", ""),
                "set": card.get("set", ""),
                "set_name": card.get("set_name", ""),
                "legalities": card.get("legalities", {}),
                "image_uris": card.get("image_uris", {}),
                "scryfall_uri": card.get("scryfall_uri", ""),
                "prices": card.get("prices", {}),
            }

            self.cards[name] = entry

            # Track Legacy legality
            legalities = card.get("legalities", {})
            if legalities.get("legacy") in ("legal", "restricted"):
                self.legacy_legal.add(name)

        self.names = sorted(self.cards.keys())
        print(
            f"Indexed {len(self.cards)} unique cards, "
            f"{len(self.legacy_legal)} Legacy-legal"
        )

        self.save()

    def save(self):
        """Save the index to disk."""
        data = {
            "cards": self.cards,
            "names": self.names,
            "legacy_legal": self.legacy_legal,
        }
        with open(INDEX_PATH, "wb") as f:
            pickle.dump(data, f)
        size_mb = os.path.getsize(INDEX_PATH) / (1024 * 1024)
        print(f"Saved index to {INDEX_PATH} ({size_mb:.1f} MB)")

    def load(self):
        """Load the index from disk."""
        with open(INDEX_PATH, "rb") as f:
            data = pickle.load(f)
        self.cards = data["cards"]
        self.names = data["names"]
        self.legacy_legal = data["legacy_legal"]
        print(
            f"Loaded {len(self.cards)} cards, "
            f"{len(self.legacy_legal)} Legacy-legal"
        )

    def search(
        self,
        query: str,
        limit: int = 5,
        legacy_only: bool = True,
        threshold: int = 70,
    ) -> list[tuple[str, float]]:
        """Fuzzy search for card names.

        Returns list of (card_name, score) tuples sorted by match quality.
        Score is 0-100, with 100 being exact match.
        """
        search_pool = (
            sorted(self.legacy_legal) if legacy_only else self.names
        )
        results = process.extract(
            query,
            search_pool,
            scorer=fuzz.WRatio,
            limit=limit,
            score_cutoff=threshold,
        )
        return [(name, score) for name, score, _ in results]

    def get(self, name: str) -> dict | None:
        """Get full card data by exact name."""
        return self.cards.get(name)

    def is_legacy_legal(self, name: str) -> bool:
        """Check if a card is Legacy-legal."""
        return name in self.legacy_legal

    def resolve(self, text: str, legacy_only: bool = True) -> list[dict]:
        """Find all card names mentioned in a block of text.

        Returns list of card data dicts for each unique card found.
        Uses exact matching first, then fuzzy matching for unresolved names.
        """
        found = []
        found_names = set()

        # First pass: exact matches (longest first to avoid partial matches)
        search_pool = self.legacy_legal if legacy_only else set(self.names)
        for name in sorted(search_pool, key=len, reverse=True):
            if name in text and name not in found_names:
                found.append(self.cards[name])
                found_names.add(name)

        return found

    def scryfall_image_url(
        self, name: str, version: str = "normal"
    ) -> str | None:
        """Get the Scryfall image URL for a card."""
        card = self.get(name)
        if card and card.get("image_uris"):
            return card["image_uris"].get(version)
        return None


if __name__ == "__main__":
    index = CardIndex()
    index.build()

    # Demo some searches
    print("\n--- Demo searches ---")
    for query in [
        "Forse of Will",
        "brainstom",
        "Orcish Bowmaster",
        "underground sea",
        "wastland",
        "murktide",
        "Show and Tel",
    ]:
        results = index.search(query, limit=3)
        print(f'  "{query}" -> {results}')

    # Demo text resolution
    print("\n--- Text resolution ---")
    sample = "I want to play Force of Will and Brainstorm with Murktide Regent"
    cards = index.resolve(sample)
    print(f"  Found {len(cards)} cards in: {sample}")
    for c in cards:
        print(f"    {c['name']} ({c['mana_cost']}) - {c['type_line']}")
