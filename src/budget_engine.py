"""
Budget substitution engine for Legacy decks.

Curated card-to-card replacement mappings with honest trade-off descriptions,
plus a tier generator that produces full/mid/budget versions of any decklist.

The LLM scores 20% on budget substitutions in our evals — it confidently
recommends expensive cards as "budget alternatives" (e.g. Mox Diamond for
Underground Sea). This module provides deterministic, curated answers
instead of relying on the model.

Usage:
    from src.budget_engine import BudgetEngine
    from src.card_index import CardIndex

    idx = CardIndex()
    idx.load()
    engine = BudgetEngine(idx)

    subs = engine.get_substitutions("Underground Sea")
    # → [Substitution(replacement="Watery Grave", ...), ...]

    tiers = engine.generate_tiers({"Underground Sea": 4, "Brainstorm": 4, ...})
    # → {"full": {...}, "mid": {...}, "budget": {...}}
"""

from dataclasses import dataclass, field


@dataclass
class Substitution:
    replacement: str
    tradeoffs: list[str]
    power_loss: int  # 0-10, where 0 = near-identical, 10 = fundamentally different
    notes: str = ""


@dataclass
class TierResult:
    """A budget tier of a decklist."""
    decklist: dict[str, int]
    estimated_price_usd: float
    substitutions_applied: list[tuple[str, str]] = field(default_factory=list)
    irreplaceable: list[str] = field(default_factory=list)


# Curated replacement mappings. Built from Legacy domain knowledge — these
# are the subs experienced players actually recommend, not what a model
# might guess from card-name similarity.
#
# Ordering: best replacement first. "Best" means closest to the original's
# function with the smallest practical downside.
REPLACEMENTS: dict[str, list[Substitution]] = {
    # Dual lands (Reserved List, $300-800 each)
    "Underground Sea": [
        Substitution(
            "Watery Grave",
            ["2 life to enter untapped", "takes 4-6 life per game from shocks"],
            power_loss=2,
            notes="Shockland. Closest playable budget sub. Worst against Burn.",
        ),
        Substitution(
            "Darkslick Shores",
            ["enters tapped after turn 2 (3+ other lands)"],
            power_loss=3,
            notes="Fast land. Untapped turns 1-2 when it matters most.",
        ),
        Substitution(
            "Underground River",
            ["1 life per colored activation", "always untapped"],
            power_loss=4,
            notes="Pain land. Best when you only need ~5 colored activations/game.",
        ),
    ],
    "Volcanic Island": [
        Substitution("Steam Vents", ["2 life to enter untapped"], power_loss=2),
        Substitution("Spirebluff Canal", ["enters tapped after turn 2"], power_loss=3),
        Substitution("Shivan Reef", ["1 life per colored activation"], power_loss=4),
    ],
    "Tropical Island": [
        Substitution("Breeding Pool", ["2 life to enter untapped"], power_loss=2),
        Substitution("Botanical Sanctum", ["enters tapped after turn 2"], power_loss=3),
        Substitution("Yavimaya Coast", ["1 life per colored activation"], power_loss=4),
    ],
    "Tundra": [
        Substitution("Hallowed Fountain", ["2 life to enter untapped"], power_loss=2),
        Substitution("Seachrome Coast", ["enters tapped after turn 2"], power_loss=3),
        Substitution("Adarkar Wastes", ["1 life per colored activation"], power_loss=4),
    ],
    "Bayou": [
        Substitution("Overgrown Tomb", ["2 life to enter untapped"], power_loss=2),
        Substitution("Blooming Marsh", ["enters tapped after turn 2"], power_loss=3),
        Substitution("Llanowar Wastes", ["1 life per colored activation"], power_loss=4),
    ],
    "Plateau": [
        Substitution("Sacred Foundry", ["2 life to enter untapped"], power_loss=2),
        Substitution("Inspiring Vantage", ["enters tapped after turn 2"], power_loss=3),
        Substitution("Battlefield Forge", ["1 life per colored activation"], power_loss=4),
    ],
    "Savannah": [
        Substitution("Temple Garden", ["2 life to enter untapped"], power_loss=2),
        Substitution("Razorverge Thicket", ["enters tapped after turn 2"], power_loss=3),
        Substitution("Brushland", ["1 life per colored activation"], power_loss=4),
    ],
    "Scrubland": [
        Substitution("Godless Shrine", ["2 life to enter untapped"], power_loss=2),
        Substitution("Concealed Courtyard", ["enters tapped after turn 2"], power_loss=3),
        Substitution("Caves of Koilos", ["1 life per colored activation"], power_loss=4),
    ],
    "Taiga": [
        Substitution("Stomping Ground", ["2 life to enter untapped"], power_loss=2),
        Substitution("Copperline Gorge", ["enters tapped after turn 2"], power_loss=3),
        Substitution("Karplusan Forest", ["1 life per colored activation"], power_loss=4),
    ],
    "Badlands": [
        Substitution("Blood Crypt", ["2 life to enter untapped"], power_loss=2),
        Substitution("Blackcleave Cliffs", ["enters tapped after turn 2"], power_loss=3),
        Substitution("Sulfurous Springs", ["1 life per colored activation"], power_loss=4),
    ],
    "Tundra": [  # white/blue
        Substitution("Hallowed Fountain", ["2 life to enter untapped"], power_loss=2),
        Substitution("Seachrome Coast", ["enters tapped after turn 2"], power_loss=3),
    ],

    # Free countermagic
    "Force of Will": [
        Substitution(
            "Force of Negation",
            ["only works on opponent's turn", "doesn't counter creatures"],
            power_loss=5,
            notes="Closest to FoW but much more restrictive. If you can't afford FoW, seriously consider a non-blue deck.",
        ),
    ],

    # Fast mana
    "Lion's Eye Diamond": [
        # LED genuinely has no replacement in Storm. The only real "budget
        # path" is to play a different combo deck.
    ],
    "Mox Diamond": [
        Substitution(
            "Chrome Mox",
            ["exile a nonland card (loses a spell instead of a land)"],
            power_loss=5,
            notes="Worse than Mox Diamond in most decks since spells > lands. In Lands deck, Mox Diamond is irreplaceable (discarding a land is an upside with Loam).",
        ),
    ],

    # Staples with no direct replacement
    "The Tabernacle at Pendrell Vale": [],  # Lands only; nothing close
    "Gaea's Cradle": [
        Substitution(
            "Itlimoc, Cradle of the Sun",
            ["requires 4+ creatures to transform", "way too slow for Legacy"],
            power_loss=9,
            notes="Only budget shell that uses similar effects is casual Elves. Not competitive.",
        ),
    ],

    # Utility lands
    "Wasteland": [
        Substitution(
            "Ghost Quarter",
            ["opponent gets a basic land", "massively weaker mana denial"],
            power_loss=6,
            notes="Wasteland is actually affordable ($25-35). Consider buying rather than substituting.",
        ),
        Substitution(
            "Field of Ruin",
            ["costs 2 to activate", "opponent gets a basic"],
            power_loss=7,
        ),
    ],
    "Rishadan Port": [
        Substitution(
            "Ghost Quarter",
            ["one-shot land destruction instead of repeatable tap effect"],
            power_loss=7,
            notes="Not a true replacement — Port is a unique effect.",
        ),
    ],

    # Blue cantrips (keep — these are all cheap already)
    # Brainstorm, Ponder, Preordain all under $5

    # Format staples with affordable prices (no replacement needed)
    # Thoughtseize, Swords to Plowshares, Lightning Bolt, Dark Ritual,
    # Daze, Spell Pierce, Fatal Push — all under $10

    # Expensive threats
    "Murktide Regent": [
        Substitution(
            "Dragon's Rage Channeler",
            ["delirium-dependent, much smaller"],
            power_loss=5,
            notes="Not a direct replacement. DRC is a different threat type (cheap cantrip creature).",
        ),
        Substitution(
            "Delver of Secrets",
            ["one mana, requires instant/sorcery on top to flip"],
            power_loss=6,
            notes="Different role — Delver is a 1-drop clock, not a finisher.",
        ),
    ],

    # Sideboard staples (many are already cheap)
    "Leyline of the Void": [
        Substitution(
            "Rest in Peace",
            ["costs 1W", "not free on turn 0"],
            power_loss=3,
            notes="Rest in Peace is $2-5, Leyline is $5-10. The budget difference is small.",
        ),
        Substitution(
            "Tormod's Crypt",
            ["one-shot", "must be drawn early"],
            power_loss=5,
            notes="Free graveyard hate but single-use. $0.50.",
        ),
    ],

    # MH3/recent expensive cards
    "Orcish Bowmasters": [
        # No true replacement. If you can't afford, play a different deck.
        # Cursed Scroll and Plague Engineer are the closest in different roles.
    ],
    "Solitude": [
        Substitution(
            "Swords to Plowshares",
            ["costs mana", "not a creature"],
            power_loss=4,
            notes="Solitude gives you a free removal via evoke PLUS a 3/2 lifelinker if hard-cast. StP is just the removal.",
        ),
    ],
}


# Cards that are genuinely irreplaceable. Including these triggers an
# honest "play a different deck" response rather than a bad substitution.
IRREPLACEABLE = {
    "Lion's Eye Diamond",
    "The Tabernacle at Pendrell Vale",
    "Gaea's Cradle",
    "Orcish Bowmasters",
}


class BudgetEngine:
    """Deterministic budget substitution engine backed by Scryfall prices."""

    # Price threshold above which a card is considered "expensive enough to sub"
    EXPENSIVE_USD = 30.0
    # Threshold for "very expensive" tier (mid tier replaces these)
    VERY_EXPENSIVE_USD = 150.0

    def __init__(self, card_index):
        self.card_index = card_index

    def get_price(self, card_name: str) -> float | None:
        """Return USD price from Scryfall data, or None if unavailable."""
        card = self.card_index.cards.get(card_name)
        if not card:
            return None
        prices = card.get("prices") or {}
        usd = prices.get("usd")
        if usd is not None:
            try:
                return float(usd)
            except (ValueError, TypeError):
                pass
        # Reserved List cards often have null usd but non-null eur/foil
        eur = prices.get("eur")
        if eur is not None:
            try:
                return float(eur) * 1.10  # rough EUR→USD
            except (ValueError, TypeError):
                pass
        return None

    def get_substitutions(self, card_name: str) -> list[Substitution]:
        """Return curated substitutions for a card, best first.

        Returns empty list if no known subs (including for irreplaceable cards).
        """
        return REPLACEMENTS.get(card_name, [])

    def is_irreplaceable(self, card_name: str) -> bool:
        return card_name in IRREPLACEABLE

    def price_decklist(self, decklist: dict[str, int]) -> float:
        """Sum Scryfall prices for all copies in a decklist. Missing prices count as 0."""
        total = 0.0
        for name, count in decklist.items():
            price = self.get_price(name)
            if price is not None:
                total += price * count
        return total

    def generate_tiers(self, decklist: dict[str, int]) -> dict[str, TierResult]:
        """Produce full/mid/budget versions of a decklist.

        - full:   original, unchanged
        - mid:    replaces only cards above VERY_EXPENSIVE_USD (typically Reserved List)
        - budget: replaces every card with a known substitution
        """
        full = TierResult(
            decklist=dict(decklist),
            estimated_price_usd=self.price_decklist(decklist),
        )

        mid = self._apply_substitutions(decklist, threshold=self.VERY_EXPENSIVE_USD)
        budget = self._apply_substitutions(decklist, threshold=self.EXPENSIVE_USD)

        return {"full": full, "mid": mid, "budget": budget}

    def _apply_substitutions(
        self, decklist: dict[str, int], threshold: float
    ) -> TierResult:
        """Replace every card above `threshold` with its best substitution."""
        new_decklist: dict[str, int] = {}
        subs_applied: list[tuple[str, str]] = []
        irreplaceable: list[str] = []

        for name, count in decklist.items():
            price = self.get_price(name)
            if price is None or price < threshold:
                new_decklist[name] = new_decklist.get(name, 0) + count
                continue

            if self.is_irreplaceable(name):
                irreplaceable.append(name)
                new_decklist[name] = new_decklist.get(name, 0) + count
                continue

            subs = self.get_substitutions(name)
            if not subs:
                new_decklist[name] = new_decklist.get(name, 0) + count
                continue

            replacement = subs[0].replacement
            new_decklist[replacement] = new_decklist.get(replacement, 0) + count
            subs_applied.append((name, replacement))

        return TierResult(
            decklist=new_decklist,
            estimated_price_usd=self.price_decklist(new_decklist),
            substitutions_applied=subs_applied,
            irreplaceable=irreplaceable,
        )

    def explain_substitution(self, original: str, replacement: str) -> str:
        """Human-readable explanation of a specific sub, or empty string if unknown."""
        for sub in self.get_substitutions(original):
            if sub.replacement == replacement:
                orig_price = self.get_price(original) or 0
                repl_price = self.get_price(replacement) or 0
                savings = orig_price - repl_price
                tradeoff_str = "; ".join(sub.tradeoffs) if sub.tradeoffs else "no significant downside"
                lines = [
                    f"{original} (${orig_price:.2f}) → {replacement} (${repl_price:.2f}), saves ${savings:.2f} per copy.",
                    f"Trade-offs: {tradeoff_str}.",
                ]
                if sub.notes:
                    lines.append(sub.notes)
                return " ".join(lines)
        return ""
