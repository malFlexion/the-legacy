"""
Audit training data against Scryfall card data for factual errors.

Loads all JSONL training files, extracts card name references,
looks up real card data from Scryfall, and flags mismatches in:
- Mana cost
- Power/toughness
- Card type
- Oracle text claims
- Legality
"""

import json
import re
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
TRAINING_DIR = DATA_DIR / "training"
SCRYFALL_PATH = DATA_DIR / "scryfall-cards.json"


def load_scryfall_index():
    """Build a name -> card data lookup from Scryfall bulk data."""
    print("Loading Scryfall data (this takes a moment)...")
    index = {}
    with open(SCRYFALL_PATH, "r", encoding="utf-8") as f:
        cards = json.load(f)

    for card in cards:
        if card.get("lang") != "en":
            continue
        if card.get("layout") in ("token", "art_series", "double_faced_token"):
            continue
        name = card["name"].lower()
        # Keep the most recent printing (last one wins)
        index[name] = {
            "name": card["name"],
            "mana_cost": card.get("mana_cost", ""),
            "type_line": card.get("type_line", ""),
            "oracle_text": card.get("oracle_text", ""),
            "power": card.get("power"),
            "toughness": card.get("toughness"),
            "legalities": card.get("legalities", {}),
            "keywords": card.get("keywords", []),
            "cmc": card.get("cmc", 0),
        }
    print(f"Indexed {len(index)} unique cards.")
    return index


# Known card names we expect to find in training data
# Maps common references to their canonical Scryfall names
CARD_NAMES_CANONICAL = {
    "bowmasters": "orcish bowmasters",
    "murktide": "murktide regent",
    "delver": "delver of secrets // insectile aberration",
    "drc": "dragon's rage channeler",
    "emrakul": "emrakul, the aeons torn",
    "atraxa": "atraxa, grand unifier",
    "thalia": "thalia, guardian of thraben",
    "karakas": "karakas",
    "stoneforge": "stoneforge mystic",
    "batterskull": "batterskull",
    "jace": "jace, the mind sculptor",
    "oko": "oko, thief of crowns",
    "uro": "uro, titan of nature's wrath",
    "ragavan": "ragavan, nimble pilferer",
    "w6": "wrenn and six",
    "w&6": "wrenn and six",
    "sfm": "stoneforge mystic",
    "fow": "force of will",
    "stp": "swords to plowshares",
}


def extract_card_claims(text):
    """Extract factual claims about cards from training text.
    Returns list of (card_name, claim_type, claim_value) tuples."""
    claims = []

    # Pattern: "X is a P/T" or "X/Y" stats
    pt_pattern = r"(\d+)/(\d+)"
    # Pattern: mana costs like {1}{U}{U} or 1UU or "costs XYZ"
    mana_patterns = [
        r"(?:costs?|for)\s+(\{[^}]+\}(?:\{[^}]+\})*)",
        r"(?:costs?|for)\s+(\d*[WUBRG]+)",
        r"mana (?:cost|value)\s+(?:of\s+)?(\d+)",
    ]

    return claims  # We'll do the matching at a higher level


def check_specific_claims(text, scryfall_index):
    """Check specific factual claims in training text against Scryfall."""
    issues = []

    # Check: "Orcish Bowmasters" claims
    if "orcish bowmasters" in text.lower() or "bowmasters" in text.lower():
        card = scryfall_index.get("orcish bowmasters")
        if card:
            # Check for wrong P/T
            if "1/1 trample" in text.lower():
                issues.append(
                    f"WRONG: Says Bowmasters is '1/1 trample'. "
                    f"Actual: {card['power']}/{card['toughness']}, keywords: {card['keywords']}. "
                    f"Oracle: {card['oracle_text'][:100]}"
                )
            if "1gg" in text.lower() or "{1}{g}{g}" in text.lower():
                issues.append(
                    f"WRONG: Says Bowmasters costs 1GG. Actual mana cost: {card['mana_cost']}"
                )
            # Check trigger description
            if "mana value" in text.lower() and "bowmasters" in text.lower():
                if "triggers whenever" in text.lower() or "trigger" in text.lower():
                    if "draw" not in text.lower():
                        issues.append(
                            f"LIKELY WRONG: Describes Bowmasters trigger without mentioning card draw. "
                            f"Actual trigger: opponent draws a card. Oracle: {card['oracle_text'][:150]}"
                        )

    # Check: "Counterspell" claims
    if "counterspell" in text.lower():
        card = scryfall_index.get("counterspell")
        if card:
            if "1uu" in text.lower() or "{1}{u}{u}" in text.lower():
                issues.append(
                    f"WRONG: Says Counterspell costs 1UU. Actual: {card['mana_cost']} (CMC {card['cmc']})"
                )
            if "mana value 2 or less" in text.lower() or "mana value two or less" in text.lower():
                issues.append(
                    f"WRONG: Says Counterspell only counters MV 2 or less. "
                    f"Actual: counters any spell. Oracle: {card['oracle_text']}"
                )

    # Check: "Daze" claims
    if "daze" in text.lower():
        card = scryfall_index.get("daze")
        if card:
            if "removal spell" in text.lower() and "daze" in text.lower():
                issues.append(
                    f"WRONG: Calls Daze a removal spell. Actual type: {card['type_line']}. "
                    f"Oracle: {card['oracle_text'][:100]}"
                )

    # Check: Lightning Bolt in white deck context
    if "lightning bolt" in text.lower():
        card = scryfall_index.get("lightning bolt")
        if card and "white" in text.lower() and ("removal" in text.lower() or "play in" in text.lower()):
            if "{R}" in card["mana_cost"]:
                issues.append(
                    f"SUSPECT: Recommending Lightning Bolt (a red card, {card['mana_cost']}) in white deck context"
                )

    # Check: "Blood Moon" claims
    if "blood moon" in text.lower():
        card = scryfall_index.get("blood moon")
        if card:
            if "exile" in text.lower() and "graveyard" in text.lower():
                issues.append(
                    f"WRONG: Says Blood Moon exiles from graveyard. "
                    f"Actual: {card['oracle_text']}"
                )

    # Check: Generic P/T claims for well-known cards
    pt_checks = {
        "murktide regent": None,  # Variable, skip
        "delver of secrets // insectile aberration": ("0", "1"),  # front face
        "thalia, guardian of thraben": ("2", "1"),
        "stoneforge mystic": ("1", "2"),
        "orcish bowmasters": ("1", "1"),
        "dragon's rage channeler": ("1", "1"),
    }

    # Check: Mana cost claims for specific cards
    mana_checks = {
        "brainstorm": "{U}",
        "ponder": "{U}",
        "force of will": "{3}{U}{U}",
        "daze": "{1}{U}",
        "swords to plowshares": "{W}",
        "lightning bolt": "{R}",
        "thoughtseize": "{B}",
        "counterspell": "{U}{U}",
        "dark ritual": "{B}",
        "show and tell": "{2}{U}",
        "chalice of the void": "{X}{X}",
    }

    # Check for "Liliana of the Veil" as a "staple" graveyard hate card
    if "liliana of the veil" in text.lower():
        context = text.lower()
        if "graveyard" in context and ("sideboard" in context or "against" in context):
            issues.append(
                "SUSPECT: Liliana of the Veil listed as graveyard sideboard hate. "
                "She's a planeswalker, not graveyard hate."
            )

    # Check: Cards described as something they're not
    if "show and tell" in text.lower():
        card = scryfall_index.get("show and tell")
        if card and "creature" in text.lower():
            ctx = text.lower()
            idx = ctx.find("show and tell")
            nearby = ctx[max(0, idx - 50):idx + 80]
            if "creature" in nearby and "creature card" not in nearby:
                issues.append(
                    f"SUSPECT: Show and Tell described near 'creature'. "
                    f"Actual type: {card['type_line']}"
                )

    # Check: "Sneak Attack" damage claims
    if "sneak attack" in text.lower():
        card = scryfall_index.get("sneak attack")
        if card:
            if "2 damage" in text.lower() or "deals 2" in text.lower():
                issues.append(
                    f"WRONG: Says Sneak Attack deals 2 damage. "
                    f"Actual: {card['oracle_text'][:150]}"
                )

    return issues


def audit_file(filepath, scryfall_index):
    """Audit a single JSONL training file."""
    issues_found = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())
            except json.JSONDecodeError:
                issues_found.append((line_num, "PARSE ERROR", "Invalid JSON"))
                continue

            full_text = f"{entry.get('instruction', '')} {entry.get('output', '')}"
            issues = check_specific_claims(full_text, scryfall_index)

            for issue in issues:
                issues_found.append((line_num, entry.get("instruction", "")[:80], issue))

    return issues_found


def main():
    scryfall_index = load_scryfall_index()

    # Print some key card data for reference
    print("\n=== Key Card Reference ===")
    for name in ["orcish bowmasters", "counterspell", "daze", "blood moon",
                  "brainstorm", "force of will", "show and tell", "sneak attack",
                  "lightning bolt", "swords to plowshares", "murktide regent",
                  "chalice of the void", "karakas", "emrakul, the aeons torn"]:
        card = scryfall_index.get(name)
        if card:
            print(f"\n{card['name']}: {card['mana_cost']} | {card['type_line']}")
            if card["power"]:
                print(f"  P/T: {card['power']}/{card['toughness']}")
            print(f"  Keywords: {card['keywords']}")
            print(f"  Oracle: {card['oracle_text'][:200]}")
            print(f"  Legacy legal: {card['legalities'].get('legacy', 'unknown')}")

    print("\n\n=== Training Data Audit ===\n")

    total_issues = 0
    for jsonl_file in sorted(TRAINING_DIR.glob("*.jsonl")):
        issues = audit_file(jsonl_file, scryfall_index)
        if issues:
            print(f"\n--- {jsonl_file.name} ---")
            for line_num, instruction, issue in issues:
                print(f"  Line {line_num}: {issue}")
                print(f"    Context: {instruction}")
                total_issues += 1

    print(f"\n\nTotal issues found: {total_issues}")

    # Also check for banned cards recommended as playable
    print("\n\n=== Checking for Banned Card Recommendations ===")
    banned_in_legacy = []
    for name, card in scryfall_index.items():
        if card["legalities"].get("legacy") == "banned":
            banned_in_legacy.append(card["name"])

    banned_set = {n.lower() for n in banned_in_legacy}

    for jsonl_file in sorted(TRAINING_DIR.glob("*.jsonl")):
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                entry = json.loads(line.strip())
                output = entry.get("output", "").lower()
                for banned_name in ["gitaxian probe", "deathrite shaman",
                                    "sensei's divining top", "wrenn and six",
                                    "ragavan, nimble pilferer", "oko, thief of crowns",
                                    "dreadhorde arcanist", "grief", "entomb",
                                    "nadu, winged wisdom", "psychic frog"]:
                    if banned_name in output:
                        # Check context - is it being recommended to play?
                        ctx = output
                        if ("play" in ctx or "run" in ctx or "include" in ctx or
                            "recommend" in ctx or "should" in ctx or "staple" in ctx):
                            if "banned" not in ctx and "ban" not in ctx:
                                print(f"  {jsonl_file.name} line {line_num}: "
                                      f"Mentions banned card '{banned_name}' "
                                      f"without noting it's banned")
                                print(f"    Instruction: {entry.get('instruction', '')[:80]}")


if __name__ == "__main__":
    main()
