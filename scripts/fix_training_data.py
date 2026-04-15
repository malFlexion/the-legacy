"""
Fix known issues in training data:
1. Remove duplicate Grief entries (keep the one that mentions the ban)
2. Remove duplicate Psychic Frog entry, update remaining to note ban
3. Fix Containment Priest contradictory text
4. Fix Blood Moon graveyard error
5. Fix Counterspell "MV 2 or less" errors
6. Update Entomb references to note it's banned where it's presented as playable
"""

import json
from pathlib import Path

TRAINING_DIR = Path(__file__).parent.parent / "data" / "training"


def fix_card_evaluation():
    """Fix card_evaluation.jsonl"""
    filepath = TRAINING_DIR / "card_evaluation.jsonl"
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            entries.append(json.loads(line.strip()))

    fixed = []
    grief_count = 0
    frog_count = 0
    changes = []

    for i, entry in enumerate(entries):
        inst = entry["instruction"]
        out = entry["output"]

        # Fix Grief: keep only one entry that notes the ban
        if inst == "Is Grief Legacy-playable?":
            grief_count += 1
            if grief_count == 1:
                # Replace first occurrence with correct banned version
                entry["output"] = (
                    "No, Grief is banned in Legacy. Before the ban, it was a key piece of "
                    "Scam strategies that paired it with Reanimate or Not Dead After All. "
                    "Evoking Grief for zero mana on turn 1 to strip a card, then reanimating "
                    "it for a 3/2 menace body plus a second Thoughtseize trigger was devastating. "
                    "The evoke-reanimate play pattern was deemed too powerful and consistent, "
                    "leading to Grief's ban alongside other format health changes. If you want "
                    "similar hand disruption, Thoughtseize is the best remaining option at 1 mana."
                )
                fixed.append(entry)
                changes.append(f"  Line {i+1}: Rewrote Grief entry to note ban")
            else:
                changes.append(f"  Line {i+1}: Removed duplicate Grief entry (#{grief_count})")
                continue  # skip duplicate

        # Fix Psychic Frog: keep only one entry that notes the ban
        elif inst == "Is Psychic Frog Legacy-playable?":
            frog_count += 1
            if frog_count == 1:
                entry["output"] = (
                    "No, Psychic Frog is banned in Legacy. Before the ban, it was a staple in "
                    "Dimir and Esper tempo/midrange decks. For UB, you got a 1/2 that grew by "
                    "discarding cards, gained flying until end of turn, and could exile cards "
                    "from graveyards for card advantage. It synergized perfectly with Legacy's "
                    "cantrip-heavy blue-black shell and was replacing Delver of Secrets in some "
                    "builds. The card was banned for being too efficient as a threat that also "
                    "provided card advantage. Murktide Regent and Orcish Bowmasters are the "
                    "current top threats in Dimir Tempo."
                )
                fixed.append(entry)
                changes.append(f"  Line {i+1}: Rewrote Psychic Frog entry to note ban")
            else:
                changes.append(f"  Line {i+1}: Removed duplicate Psychic Frog entry (#{frog_count})")
                continue  # skip duplicate

        # Fix Counterspell "MV 2 or less" — search all outputs
        elif "counterspell" in out.lower() and ("mana value 2 or less" in out.lower() or "mana value two or less" in out.lower()):
            entry["output"] = out.replace(
                "mana value 2 or less", "any mana value"
            ).replace(
                "mana value two or less", "any mana value"
            )
            fixed.append(entry)
            changes.append(f"  Line {i+1}: Fixed Counterspell 'MV 2 or less' -> counters any spell ({inst[:60]})")

        # Fix any Counterspell mana cost errors (1UU -> UU)
        elif "counterspell" in out.lower() and ("costs 1uu" in out.lower() or "for 1uu" in out.lower()):
            entry["output"] = out.replace("1UU", "UU").replace("1uu", "UU")
            fixed.append(entry)
            changes.append(f"  Line {i+1}: Fixed Counterspell mana cost 1UU -> UU ({inst[:60]})")

        else:
            fixed.append(entry)

    with open(filepath, "w", encoding="utf-8") as f:
        for entry in fixed:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"card_evaluation.jsonl: {len(entries)} -> {len(fixed)} entries")
    for c in changes:
        print(c)


def fix_rules_qa():
    """Fix rules_qa.jsonl"""
    filepath = TRAINING_DIR / "rules_qa.jsonl"
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            entries.append(json.loads(line.strip()))

    changes = []
    for i, entry in enumerate(entries):
        inst = entry["instruction"]
        out = entry["output"]

        # Fix Containment Priest contradictory text
        if "containment priest" in inst.lower() and "collected company" in inst.lower():
            entry["output"] = (
                "Containment Priest says if a nontoken creature would enter the battlefield "
                "and it was not cast, exile it instead. Collected Company puts creatures from "
                "the top of your library onto the battlefield WITHOUT casting them. With Priest "
                "in play, creatures CoCo tries to put in play are exiled instead. This applies "
                "regardless of who controls Priest - if YOU control Priest and cast CoCo, "
                "Priest exiles your own creatures too. Priest does not discriminate by controller. "
                "In Legacy, this interaction is rarely relevant since CoCo is not a Legacy staple, "
                "but the same logic applies to Show and Tell, Natural Order, and any other effect "
                "that puts creatures into play without casting them."
            )
            changes.append(f"  Line {i+1}: Fixed contradictory Containment Priest text")

        # Fix Blood Moon graveyard error
        elif "blood moon" in inst.lower() and "fetch" in inst.lower() and "graveyard" in inst.lower():
            entry["output"] = (
                "Blood Moon makes all nonbasic lands into Mountains. This means fetchlands in "
                "play become Mountains and lose their ability to sacrifice and search. You "
                "cannot activate a Polluted Delta under Blood Moon because it no longer has "
                "its fetch ability - it just taps for red mana. Fetchlands already in the "
                "graveyard are not affected by Blood Moon since Blood Moon only changes lands "
                "on the battlefield. If you crack a fetchland before Blood Moon resolves, it "
                "works normally. This is why experienced players fetch in response to Blood Moon "
                "being cast."
            )
            changes.append(f"  Line {i+1}: Fixed Blood Moon graveyard error")

        # Fix Counterspell errors in rules_qa too
        elif "counterspell" in out.lower() and ("mana value 2 or less" in out.lower()):
            entry["output"] = out.replace("mana value 2 or less", "any mana value")
            changes.append(f"  Line {i+1}: Fixed Counterspell 'MV 2 or less' ({inst[:60]})")

        # Fix Entomb entries - add ban note where it's described as currently playable
        elif "entomb" in inst.lower() and "how does entomb work" in inst.lower():
            if "banned" not in out.lower():
                entry["output"] = (
                    "Note: Entomb is banned in Legacy as of November 2025. "
                    + out
                    + " While Entomb is no longer legal, understanding its mechanics is useful "
                    "for format history and for recognizing similar effects."
                )
                changes.append(f"  Line {i+1}: Added ban note to Entomb rules explanation")

    with open(filepath, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"\nrules_qa.jsonl: {len(entries)} entries (no removals)")
    for c in changes:
        print(c)


def fix_all_entomb_references():
    """Add ban context to Entomb references across all files where it's presented as playable."""
    for jsonl_file in sorted(TRAINING_DIR.glob("*.jsonl")):
        entries = []
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                entries.append(json.loads(line.strip()))

        changes = []
        for i, entry in enumerate(entries):
            out = entry["output"]
            inst = entry["instruction"]

            # Skip files already handled
            if jsonl_file.name in ("card_evaluation.jsonl", "rules_qa.jsonl"):
                continue

            # If Entomb is mentioned as something to play/use without ban note
            if "entomb" in out.lower() and "banned" not in out.lower():
                # Check if it's being recommended
                out_lower = out.lower()
                entomb_idx = out_lower.find("entomb")
                context = out_lower[max(0, entomb_idx-100):entomb_idx+100]
                if any(w in context for w in ["play", "cast", "use", "run", "include", "tutor"]):
                    # Add a note
                    entry["output"] = out.replace(
                        "Entomb", "Entomb (now banned in Legacy)"
                    ).replace(
                        "entomb", "Entomb (now banned in Legacy)"
                    )
                    # Only replace first occurrence if multiple
                    changes.append(f"  {jsonl_file.name} line {i+1}: Added ban note to Entomb reference ({inst[:60]})")

        if changes:
            with open(jsonl_file, "w", encoding="utf-8") as f:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            for c in changes:
                print(c)


def main():
    print("=== Fixing Training Data ===\n")
    fix_card_evaluation()
    fix_rules_qa()
    print("\n--- Fixing Entomb references in other files ---")
    fix_all_entomb_references()

    # Print final counts
    print("\n=== Final Counts ===")
    for jsonl_file in sorted(TRAINING_DIR.glob("*.jsonl")):
        with open(jsonl_file, "r", encoding="utf-8") as f:
            count = sum(1 for _ in f)
        print(f"  {jsonl_file.name}: {count} entries")


if __name__ == "__main__":
    main()
