"""
Generate Round 2 training data for all weak/missing categories.
All data is sourced from the project's own data files (meta analysis, deck history, etc.)
and Scryfall card data for factual accuracy.
"""

import json
from pathlib import Path

TRAINING_DIR = Path(__file__).parent.parent / "data" / "training"


def write_jsonl(filename, entries):
    """Append entries to an existing JSONL file."""
    filepath = TRAINING_DIR / filename
    with open(filepath, "a", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  {filename}: +{len(entries)} entries")


def pair(instruction, output):
    return {"instruction": instruction, "input": "", "output": output}


def gen_meta_awareness():
    """Generate meta awareness training pairs from real meta data."""
    entries = [
        # Current top deck
        pair(
            "What is the most played deck in Legacy right now?",
            "Dimir Tempo is the most played deck in Legacy at 14.6% meta share with 228 decks in the current sample. It uses Orcish Bowmasters, Tamiyo Inquisitive Student, Murktide Regent, and Barrowgoyf as threats, backed by Brainstorm, Ponder, Force of Will, Daze, and Thoughtseize. Its win rate is approximately 52.7%, which is strong but not oppressive. The format is considered healthy with no single deck dominating."
        ),
        # Top 5 decks
        pair(
            "What are the top 5 most played Legacy decks?",
            "The top 5 Legacy decks by meta share are: 1) Dimir Tempo at 14.6% — the clear best deck, UB tempo with Bowmasters and Thoughtseize. 2) Ocelot Pride Midrange at 8.5% — non-blue aggro/midrange using MH3 energy cards. 3) Oops! All Spells at 8.2% — zero-land combo that mills itself and wins with Thassa's Oracle. 4) Sneak and Show at 6.7% — cheats Emrakul or Atraxa into play with Show and Tell or Sneak Attack. 5) Izzet Delver at 4.3% — UR tempo with Delver of Secrets, Lightning Bolt, and Murktide Regent."
        ),
        # Combo vs fair
        pair(
            "Is combo or fair strategies more popular in Legacy?",
            "Both are well-represented but combo holds a slight edge in total meta share. Combo archetypes collectively make up about 40% of the field — spread across Oops (8.2%), Sneak and Show (6.7%), Painter (4.1%), TES (3.5%), Mystic Forge (3.0%), Doomsday (2.7%), and others. Tempo and aggro combine for about 30%, control and prison about 20%, and midrange about 10%. However, Dimir Tempo (a fair deck) is the single most played deck at 14.6%. Combo is more diverse but no single combo deck dominates."
        ),
        # Beat Dimir Tempo
        pair(
            "What deck should I play if I want to beat Dimir Tempo?",
            "The best decks against Dimir Tempo are: Lands (3.8%) — its Wasteland-proof mana base, Maze of Ith, and Punishing Fire grind out Dimir Tempo's small threats, plus the Dark Depths combo threatens a sudden 20/20. Eldrazi (3.1%) — Chalice of the Void on 1 shuts off cantrips and Thought-Knot Seer strips their hand. Ocelot Pride Midrange (8.5%) — goes wide with tokens that overwhelm one-for-one removal. These decks exploit Dimir Tempo's weaknesses: it struggles against strategies that don't care about Daze, can't be disrupted by Thoughtseize, or go wider than its removal can handle."
        ),
        # Format health
        pair(
            "Is Legacy a healthy format right now?",
            "Yes. The March 2026 B&R announcement made no changes, confirming WotC considers the format healthy. The data supports this: no deck has a win rate consistently above 55% (the top deck, Dimir Tempo, sits at 52.7%), there are 54 distinct competitive archetypes across 6,433 deck entries and roughly 35,000 matches since the Entomb ban in November 2025. Combo, tempo, control, prison, and midrange are all viable. The format is less blue-dependent than any time in recent memory thanks to MH3 energy cards enabling non-blue aggro."
        ),
        # Meta breakdown by strategy
        pair(
            "What is the Legacy metagame breakdown by strategy type?",
            "The Legacy metagame breaks down roughly as: Combo ~40% (the most diverse category — includes Oops, Sneak and Show, Storm, Doomsday, Painter, Mystic Forge, Aluren, and more), Tempo/Aggro ~30% (dominated by Dimir Tempo at 14.6%, plus Izzet Delver, Mardu Energy), Control/Prison ~20% (Lands, Beanstalk Control, Red Stompy, Affinity Stompy, Death and Taxes), and Midrange ~10% (Ocelot Pride Midrange, Mono Black, Jund). No single macro-archetype dominates, which is a sign of format health."
        ),
        # Tier list
        pair(
            "What are the tier 1 decks in Legacy?",
            "The current tier 1 Legacy decks are: Dimir Tempo (14.6%), Ocelot Pride Midrange (8.5%), Oops! All Spells (8.2%), and Sneak and Show (6.7%). Tier 2 includes Izzet Delver (4.3%), Painter (4.1%), Lands (3.8%), The EPIC Storm (3.5%), Eldrazi (3.1%), Mardu Energy (3.0%), and Mystic Forge Combo (3.0%). Tier 3 includes Doomsday (2.7%), Red Stompy (2.7%), Affinity (2.4%), Beanstalk Control (2.3%), and Death and Taxes (2.0%). The tiers are based on meta share and tournament results."
        ),
        # Recent tournament results
        pair(
            "What decks have been winning Legacy tournaments recently?",
            "Recent Legacy tournament results (April 2026) show strong diversity: the Legacy Showcase Qualifier was won by Sultai Aluren with Dimir Tempo, Sneak and Show, Lands, and Death and Taxes in the top 8. Legacy Challenge 32 events saw wins from Colorless and Oops! All Spells. League 5-0s include Cradle Control, Mystic Forge Combo, Azorius Stoneblade, and Mono-Green Cloudpost. The takeaway is that diverse strategies are winning — combo, tempo, control, and prison all appear in top 8s consistently."
        ),
        # Entomb ban impact
        pair(
            "How did the Entomb ban affect Legacy?",
            "The Entomb ban in November 2025 removed BR Reanimator as a tier 1 strategy. Before the ban, Reanimator could Entomb a Griselbrand or Atraxa on turn 1 and reanimate it immediately. The deck still exists using Faithful Mending and other discard outlets, but it is significantly slower and less consistent. The meta share previously occupied by Reanimator was absorbed primarily by Oops! All Spells (now 8.2%) and Sneak and Show (6.7%) — other ways to cheat big creatures into play. Overall, the ban is considered healthy for the format."
        ),
        # Energy cards impact
        pair(
            "What impact have MH3 energy cards had on Legacy?",
            "Modern Horizons 3 energy cards have significantly changed Legacy by creating viable non-blue aggressive strategies. Ocelot Pride, Guide of Souls, Amped Raptor, and Ajani Nacatl Pariah form the core of Ocelot Pride Midrange (8.5% meta share) and Mardu Energy (3.0%). These decks don't need Brainstorm or Force of Will — they win through raw card quality and board presence. The impact is that Legacy is less 'blue or bust' than any time in recent memory. Non-blue aggro and midrange have real competitive teeth."
        ),
        # Win rates
        pair(
            "What are the win rates of the top Legacy decks?",
            "Win rate data from the current Legacy meta: Oops! All Spells has the highest non-mirror win rate at approximately 53%, which is strong but considered fair by format standards. Dimir Tempo sits at 52.7% — the most popular deck but not oppressively high. Izzet Tempo underperforms relative to its play rate at around 49.8%. Overall, the format range is 49-53% for major archetypes, and a healthy format has no deck consistently above 55%. Legacy currently meets this criterion."
        ),
        # Most played cards
        pair(
            "What are the most played cards in Legacy?",
            "The most played cards in Legacy by percentage of decks: Wasteland (48%), Force of Will (45%), Brainstorm (43%), Thoughtseize (43%), Lotus Petal (41%), Ponder (38%), Leyline of the Void (36%), Force of Negation (35%), Orcish Bowmasters (29%), and Daze (27%). Wasteland being #1 reflects Legacy's emphasis on mana denial. The high rate of Leyline of the Void (36%) shows how much graveyard hate the format demands given combo diversity."
        ),
        # Matchup: Dimir Tempo vs Oops
        pair(
            "What is the Dimir Tempo vs Oops! All Spells matchup like?",
            "Game 1 is even to slightly unfavorable for Dimir Tempo because Oops is faster and can win turn 1 before Thoughtseize can be cast. Force of Will and Daze help but Oops runs its own Force of Will and Pact of Negation for protection. Post-sideboard the matchup flips to favorable for Dimir Tempo with Leyline of the Void and Surgical Extraction. Oops is extremely vulnerable to graveyard hate since its entire combo goes through the graveyard (Narcomoeba triggers, Dread Return flashback)."
        ),
        # Matchup: Dimir vs Lands
        pair(
            "What is the Dimir Tempo vs Lands matchup like?",
            "This is unfavorable for Dimir Tempo. Lands has a Wasteland-proof mana base (most of its lands are basics or utility lands that don't care about Wasteland), Maze of Ith blanks creature attacks, and Punishing Fire plus Grove of the Burnwillows creates a recurring removal engine that grinds out small threats. The Dark Depths plus Thespian's Stage combo threatens a sudden 20/20 indestructible flying token. Dimir Tempo's disruption (Daze, Thoughtseize) is less effective against a land-based strategy."
        ),
        # Artifact strategies
        pair(
            "Are artifact strategies good in Legacy right now?",
            "Yes, artifact strategies are thriving. Collectively they represent about 15% of the field: Painter (4.1%), Mystic Forge Combo (3.0%), Affinity Stompy (2.4%), and various 8-Cast variants. Urza's Saga is the glue card enabling many of these — it creates construct tokens and tutors for artifact win conditions. Chalice of the Void on 1 remains one of the best cards against the cantrip-heavy metagame (43% of decks play Brainstorm). The Ancient Tomb and City of Traitors fast mana package lets these decks deploy threats before opponents can set up."
        ),
        # Deck cost
        pair(
            "How much does a competitive Legacy deck cost?",
            "Legacy deck costs vary widely. Budget options: Oops! All Spells ($1,102), Belcher ($1,200), Burn ($1,500) — these avoid dual lands entirely. Mid-range: Eldrazi ($2,128), Painter ($2,481), Ocelot Pride ($2,569). Expensive: Dimir Tempo ($4,955), Sneak and Show ($4,370), Doomsday ($5,285), TES ($5,657). Very expensive: Lands ($8,284, driven by The Tabernacle at Pendrell Vale at $5,000+), Colorless Stompy ($13,328). The overwhelming cost driver is Reserved List cards, especially dual lands like Underground Sea ($600-800 each)."
        ),
        # What to play in a combo-heavy meta
        pair(
            "What should I play in a combo-heavy Legacy meta?",
            "In a combo-heavy meta, you want decks with free interaction: Dimir Tempo (14.6%) has Force of Will, Daze, and Thoughtseize — the exact disruption combo hates. You can also go the prison route: Eldrazi (3.1%) with Chalice of the Void on 1 shuts off cantrips and rituals. Red Stompy (2.7%) combines Blood Moon, Chalice, and Trinisphere. Death and Taxes (2.0%) uses Thalia to tax all noncreature spells. If you can't beat them, join them — Oops (8.2%) races other combo decks and has its own Force of Will."
        ),
        # What to play in a fair meta
        pair(
            "What should I play in a fair-heavy Legacy meta?",
            "In a fair-heavy meta, go over the top with card advantage or combo: Sneak and Show (6.7%) ignores fair creature decks entirely by putting Emrakul into play. Lands (3.8%) grinds out any fair deck with Life from the Loam, Wasteland recursion, and the Dark Depths combo. Beanstalk Control (2.3%) generates massive card advantage with Up the Beanstalk off pitch spells. Combo decks like TES (3.5%) and Doomsday (2.7%) are also strong since fair decks pack less combo hate in their sideboards."
        ),
        # Ocelot Pride matchup spread
        pair(
            "What are Ocelot Pride Midrange's matchups?",
            "Ocelot Pride Midrange at 8.5% has a mixed matchup spread. Slightly unfavorable vs Dimir Tempo — Bowmasters and Thoughtseize are effective, but the deck can grind through disruption with token generation. Unfavorable vs combo without blue countermagic — relies on Thalia effects and fast clocks to race. Favorable vs prison/Stompy — goes wide around Chalice of the Void since most of its threats cost more than 1. Even vs Lands — can race the Dark Depths combo with a fast enough board. The deck's biggest weakness is the lack of Force of Will against combo."
        ),
        # Sideboard trends
        pair(
            "What sideboard cards are most popular in Legacy right now?",
            "The most-played sideboard cards reflect the meta's demands: Leyline of the Void is in 36% of decks — graveyard hate is essential with Oops at 8.2% and Reanimator still present. Surgical Extraction sees heavy play for precision combo hate. Pyroblast and Hydroblast are staples in the blue mirror. Flusterstorm covers Storm, counter wars, and combo. Force of Negation provides additional free interaction. Plague Engineer punishes token strategies like Ocelot Pride. Null Rod and Collector Ouphe hit artifact decks. Sideboard construction must balance graveyard hate, anti-blue cards, and anti-combo tools."
        ),
        # Bowmasters meta impact
        pair(
            "How has Orcish Bowmasters changed the Legacy metagame?",
            "Orcish Bowmasters, printed in Lord of the Rings (June 2023), has been format-warping. At 29% of decks, it is the most played creature in Legacy. Its impact: it killed Elves as a competitive deck by pinging mana dorks, weakened Delver mirrors by punishing cantrips, and enabled Dimir Tempo as the top deck by giving black a creature that generates value passively. Cards that draw multiple cards (Brainstorm, Sylvan Library, Uro) became riskier. Small creatures with 1 toughness became worse. The card made black the best partner color for blue tempo shells, overtaking red."
        ),
        # Storm in the current meta
        pair(
            "How is Storm positioned in the current Legacy meta?",
            "The EPIC Storm (TES) is at 3.5% meta share, making it a solid tier 2 deck. It uses Burning Wish for flexibility, Lion's Eye Diamond for fast mana, and wins with Tendrils of Agony or Empty the Warrens. In the current meta, Storm faces challenges: Dimir Tempo (14.6%) runs Thoughtseize, Force of Will, and Daze — the exact disruption Storm hates. However, Storm is strong against fair non-blue decks and can race other combo. The deck rewards deep format knowledge and is one of the hardest decks to play well in Legacy."
        ),
        # Reanimator post-ban
        pair(
            "Is Reanimator still playable in Legacy after the Entomb ban?",
            "Reanimator still exists at about 2.0% meta share but is significantly weaker without Entomb. The deck now relies on Faithful Mending, Careful Study, and other discard outlets to get creatures into the graveyard, which is slower and less consistent than the old turn-1 Entomb into Reanimate line. The deck still plays Griselbrand, Atraxa, Reanimate, and Exhume, but it is now a tier 3 strategy rather than the tier 1 force it was before the ban. Many former Reanimator players have moved to Oops! All Spells or Sneak and Show."
        ),
        # Doomsday positioning
        pair(
            "Is Doomsday a good deck in Legacy?",
            "Doomsday is at 2.7% meta share, solidly tier 2-3. It is one of the most skill-intensive decks in any format — you cast Doomsday to stack 5 specific cards as your library, then draw through them to win with Thassa's Oracle. The deck is strong against fair blue mirrors because it can construct piles that play around Force of Will by including its own countermagic. It struggles against fast combo (slower than Oops or Storm) and prison (Chalice shuts off cantrips needed to draw through the pile). If you enjoy complex puzzles and high-skill gameplay, Doomsday is rewarding."
        ),
        # Death and Taxes positioning
        pair(
            "How is Death and Taxes positioned in the current Legacy meta?",
            "Death and Taxes is at 2.0% meta share, tier 3. It uses Thalia Guardian of Thraben to tax noncreature spells, Aether Vial to deploy creatures without paying mana (dodging countermagic), Rishadan Port and Wasteland for mana denial, and Stoneforge Mystic to tutor equipment. The deck is strong against combo (Thalia is devastating) and blue cantrip decks. It struggles against Lands (can't mana-deny a land deck) and against decks that go wide (Ocelot Pride tokens overwhelm one-for-one removal). It recently won the TOPdeck.Ru Championship as an Orzhov variant."
        ),
        # Cheapest competitive deck
        pair(
            "What is the cheapest competitive Legacy deck?",
            "The cheapest competitive Legacy decks are: Oops! All Spells at about $1,100 — a tier 1 combo deck with 8.2% meta share that runs zero dual lands. It wins by milling itself with Balustrade Spy and winning with Thassa's Oracle. Belcher at about $1,200 — another zero-land combo deck. Burn at about $1,500 — straightforward aggro that doesn't need dual lands. All three avoid Reserved List cards entirely, which is what makes Legacy expensive. Oops is particularly notable as a budget tier 1 option."
        ),
    ]
    write_jsonl("meta_awareness.jsonl", entries)
    return len(entries)


def gen_board_state():
    """Generate board state training pairs with correct rulings."""
    entries = [
        # Blood Moon + fetchlands (the one we got wrong)
        pair(
            "My opponent has Blood Moon in play. I have a Polluted Delta in hand. Can I use it to find an Island?",
            "No. If you play Polluted Delta while Blood Moon is in play, it enters the battlefield as a Mountain (Blood Moon makes all nonbasic lands into Mountains). It loses all its original abilities, including the ability to sacrifice and search for an Island or Swamp. It will only tap for red mana. If you need blue or black mana, you need basic Islands or Swamps, which Blood Moon does not affect."
        ),
        # Blood Moon + dual lands
        pair(
            "What happens to my Underground Sea when my opponent plays Blood Moon?",
            "Your Underground Sea becomes a Mountain. It loses its land types (Island and Swamp) and all abilities, and gains the Mountain land type and the ability to tap for red mana only. You cannot tap it for blue or black. This is why playing basic Islands and Swamps is important in a format where Blood Moon exists — basics are not affected."
        ),
        # Wasteland sequencing
        pair(
            "When should I use Wasteland in a game against Dimir Tempo?",
            "Timing Wasteland is critical. Early game: use it when your opponent has exactly one nonbasic land and is trying to cast a 2-mana spell (Bowmasters, Murktide with delve) — denying their only colored source can be game-winning. Do NOT waste it on turn 1 if they have a fetchland (they will just fetch in response). Mid game: save it for Underground Sea specifically, since they need UB for most spells. Late game: it loses value since they have multiple lands. Against Daze decks, Wasteland them on their upkeep when they tap out — they cannot Daze if they have no Island to bounce."
        ),
        # Chalice of the Void on different numbers
        pair(
            "My opponent plays Chalice of the Void on 1. What cards in my Dimir Tempo deck are affected?",
            "Chalice on 1 is devastating against Dimir Tempo. It counters: Brainstorm, Ponder, Thoughtseize, Fatal Push, Spell Pierce, Daze (if hard-cast for its mana cost of 1U — wait, Daze costs 1U so it has mana value 2, not 1. Daze is NOT countered by Chalice on 1). Cards countered: Brainstorm (MV 1), Ponder (MV 1), Thoughtseize (MV 1), Fatal Push (MV 1), Spell Pierce (MV 1). Cards NOT countered: Force of Will (MV 5, alternative cost doesn't change MV), Daze (MV 2), Murktide Regent (MV 7, reduced by delve but MV stays 7), Orcish Bowmasters (MV 2), Snuff Out (MV 4). You still have threats and free countermagic."
        ),
        # Force of Will alternative cost
        pair(
            "Does Chalice of the Void on 0 counter Force of Will cast for its alternative cost?",
            "No. Chalice on 0 counters spells with mana value 0. Force of Will has a mana value of 5 regardless of how you pay for it. The alternative cost (pay 1 life, exile a blue card) changes HOW you pay, not the spell's mana value. Mana value is always determined by the mana cost printed in the upper right corner of the card, which for Force of Will is 3UU = 5. Chalice on 0 would counter things like Lotus Petal, Mox Diamond, and Tormod's Crypt."
        ),
        # Karakas + Emrakul
        pair(
            "Can Karakas bounce Emrakul, the Aeons Torn?",
            "Yes. Karakas says 'Return target legendary creature to its owner's hand.' Emrakul is a legendary creature. Emrakul has protection from spells that are one or more colors, but Karakas's ability is not a spell — it is an activated ability of a land. Protection only prevents damage, enchanting/equipping, blocking, and targeting by spells of the protected colors. Karakas is colorless, so even if protection applied to abilities, it would not matter. This is one of Legacy's most important interactions — Sneak and Show players must respect Karakas."
        ),
        # Daze math
        pair(
            "My opponent has 2 lands in play and casts Brainstorm. I have Daze in hand. Should I Daze it?",
            "It depends. If they have 2 lands and both are tapped (they used both to cast something), Daze is free since they cannot pay 1. If they have 1 land untapped, they CAN pay for Daze, so you are betting they won't. Key question: what did they tap for? If they tapped 2 lands for a 2-mana spell and then cast Brainstorm off a Lotus Petal, they have no mana to pay. If they have any untapped land, assume they will pay unless the 1 mana matters. Early game against tempo decks, Dazing Brainstorm is often correct because it costs them a draw step and you bounce your Island (which you replay next turn)."
        ),
        # Sneak Attack + Emrakul timing
        pair(
            "If my opponent activates Sneak Attack to put Emrakul into play, when does Emrakul's extra turn trigger happen?",
            "Emrakul's trigger says 'When you CAST this spell, take an extra turn.' Sneak Attack puts Emrakul into play without casting it, so the extra turn trigger does NOT happen. Your opponent gets a 15/15 flying annihilator 6 for one turn (Sneak Attack sacrifices it at end of turn), but no extra turn. This is a meaningful difference from Show and Tell, where Emrakul is also put into play without casting. To get the extra turn, you must actually cast Emrakul (very rare in Legacy, costs 15 mana)."
        ),
        # Thalia tax interaction
        pair(
            "My opponent has Thalia Guardian of Thraben in play. How much does my Force of Will cost?",
            "If you pay the regular mana cost, Force of Will costs 3UU + 1 (Thalia tax) = 4UU (6 total mana). If you pay the alternative cost, you pay 1 life + exile a blue card + 1 (Thalia tax). Yes, Thalia taxes the alternative cost too. Any noncreature spell costs 1 more, regardless of which cost you choose to pay. This is why Thalia is so effective against blue decks — even 'free' spells like Force of Will and Daze now require mana. Daze with Thalia in play requires returning an Island AND paying 1 mana."
        ),
        # Show and Tell - what to put in
        pair(
            "My opponent casts Show and Tell. I have Karakas and Containment Priest in hand. What do I put in?",
            "Put in Containment Priest. When Show and Tell resolves, both players simultaneously reveal and put a permanent into play. Containment Priest enters alongside whatever your opponent puts in. If they put a creature in (Emrakul, Atraxa), Containment Priest's ability exiles it because it entered without being cast. Karakas would also work against legendary creatures, but you'd need to activate it after Show and Tell resolves, giving the creature a window to have an enters-the-battlefield effect (like Atraxa drawing 10 cards). Containment Priest prevents the creature from entering at all."
        ),
        # Opening hand: TES combo hand
        pair(
            "Should I keep this opening hand with TES: Dark Ritual, Rite of Flame, Lion's Eye Diamond, Burning Wish, Ponder, Volcanic Island, Badlands?",
            "Yes, this is a strong keep. You have a turn-2 kill: Turn 1 play Volcanic Island, cast Ponder to set up your library. Turn 2 play Badlands, Rite of Flame (RR), Dark Ritual (RRBBB), cast Lion's Eye Diamond, cast Burning Wish (crack LED in response for BBB), wish for Tendrils of Agony from sideboard. That is 6 spells cast (Ponder, Rite, Ritual, LED, Burning Wish, Tendrils), storm count 5, Tendrils drains for 12. Not lethal, but you can adjust sequencing or Ponder may find more rituals. Even without a perfect kill, this hand has all the combo pieces. Keep. 8/10."
        ),
        # Opening hand: Lands
        pair(
            "Should I keep this opening hand with Lands: Exploration, Life from the Loam, Wasteland, Wasteland, Dark Depths, Thespian's Stage, Mox Diamond?",
            "Snap keep. This is one of the best possible Lands opening hands. Turn 1: Mox Diamond (discard a Wasteland — you have two), play Exploration, play Dark Depths and Thespian's Stage. Turn 2: Activate Thespian's Stage to copy Dark Depths, both get sacrificed due to the legend rule, and you create Marit Lage (a 20/20 flying indestructible token). Meanwhile, Life from the Loam lets you dredge back your Wasteland for recurring mana denial. This hand has the combo, mana acceleration, and the grind engine. 10/10."
        ),
        # Opening hand: Death and Taxes
        pair(
            "Should I keep this opening hand with Death and Taxes: Aether Vial, Plains, Rishadan Port, Thalia Guardian of Thraben, Stoneforge Mystic, Swords to Plowshares, Flickerwisp?",
            "Excellent keep. Aether Vial on turn 1 is your best possible start. Turn 1: Plains, Aether Vial. Turn 2: Rishadan Port, Vial in Thalia (free, dodges countermagic). Now your opponent pays 1 more for every noncreature spell while you Port their land on their upkeep. Turn 3: Vial in Stoneforge (fetches Batterskull). You have Swords for removal and Flickerwisp for later value. The only concern is being light on white mana (1 Plains), but Vial handles most of your creature costs. 9/10."
        ),
        # Board state: Murktide delve decision
        pair(
            "I have 5 instants/sorceries in my graveyard, UU available, and Murktide Regent in hand. Should I cast it now?",
            "Murktide Regent with UU available and 5 instants/sorceries to delve enters as a 3/3 base + 5 counters = 8/8 flying. That is a massive threat for 2 mana. However, consider: do you need those graveyard cards for anything else? In Dimir Tempo, Barrowgoyf also cares about graveyard card types. If you exile all your instants/sorceries, Barrowgoyf may shrink. Also consider if you might need to delve less and keep Brainstorms and Ponders in the graveyard for future Murktides. A 6/6 Murktide (exile 3) is usually enough to win and preserves options."
        ),
        # Board state: Fetch land priority
        pair(
            "I have Polluted Delta and Misty Rainforest in play. My opponent has Wasteland. Which do I fetch with first?",
            "Fetch with whichever one finds the land you need most urgently. But strategically: if you need both blue and black, crack Polluted Delta first (finds Underground Sea for both colors). Save Misty Rainforest as a shuffle effect for future Brainstorms. If your opponent has Wasteland and you fear they'll destroy your nonbasic, consider fetching a basic Island or Swamp instead of Underground Sea — basics are immune to Wasteland and Blood Moon. Against Wasteland decks, getting a basic early is often more important than optimal color fixing."
        ),
        # Surgical Extraction timing
        pair(
            "My opponent just cast Brainstorm and put two cards back on top. I have Surgical Extraction. What do I do?",
            "Wait. If your opponent put two bad cards on top with Brainstorm, they will want to shuffle them away with a fetchland. If they crack a fetchland, you can respond with Surgical Extraction targeting a key card in their graveyard. But the real power move: if they fetch BEFORE shuffling (which they should), you cannot Surgical what's on top of their library because Surgical only targets cards in graveyards. However, if they have a specific card in their graveyard you want gone (like a combo piece), Surgical it now before they can use it. Surgical's best use is removing specific combo pieces, not disrupting Brainstorm."
        ),
    ]
    write_jsonl("board_state_analysis.jsonl", entries)
    return len(entries)


def gen_budget_subs():
    """Generate budget substitution training pairs with real prices."""
    entries = [
        # Correct Underground Sea replacement (this was wrong before)
        pair(
            "What is a budget replacement for Underground Sea in Dimir Tempo?",
            "Watery Grave ($10-15) is the best budget replacement. It enters untapped if you pay 2 life, providing the same UB mana fixing. The trade-off: in a typical game you might fetch Watery Grave 2-3 times, costing 4-6 life from shockland payments plus fetchland damage. Against Burn, this can be lethal. Against combo, life total rarely matters. Darkslick Shores ($3-5) is another option that enters untapped with no life cost if you have 2 or fewer other lands, perfect for turns 1-2. Underground River ($1-2) taps for colorless freely or UB for 1 life each. Use a mix: 2 Watery Grave + 1 Darkslick Shores is a common budget configuration."
        ),
        # Budget Dimir Tempo full conversion
        pair(
            "How do I build Dimir Tempo on a budget?",
            "The full deck costs about $4,955. The expensive cards and budget alternatives: Underground Sea ($600-800 each, need 3-4) → Watery Grave ($10-15) plus 1 Darkslick Shores ($3-5). That saves $2,400+. Polluted Delta ($35-45) and other fetchlands are actually affordable — keep them, they are essential. Force of Will ($80-100 each) has NO true replacement — if you can't afford them, consider a different deck. Wasteland ($25-35 each) → keep these, they are affordable and essential. The realistic budget path: replace duals with shocklands, keep everything else. Budget Dimir Tempo costs about $1,500-2,000 and is 85-90% as powerful. The life cost from shocklands is the main downside."
        ),
        # Budget Legacy entry points
        pair(
            "What are the best budget entry points into Legacy?",
            "The cheapest competitive decks: 1) Oops! All Spells (~$1,100) — tier 1 at 8.2%, zero dual lands, wins turn 1. 2) Belcher (~$1,200) — another zero-land combo deck. 3) Burn (~$1,500) — no dual lands, straightforward. 4) Red Stompy (~$2,000) — Blood Moon and Chalice of the Void, no dual lands. 5) Eldrazi (~$2,128) — Chalice plus Eldrazi threats, colorless mana base. 6) Death and Taxes (~$1,800) — mono-white, no dual lands needed. All avoid Reserved List dual lands. Oops is the strongest budget option since it is tier 1."
        ),
        # Budget mana base guide
        pair(
            "What are the best budget alternatives to dual lands in Legacy?",
            "In order of quality: 1) Shock lands (Watery Grave, Steam Vents, etc.) at $10-15 each — same colors, 2 life to enter untapped. The closest replacement. 2) Fast lands (Darkslick Shores, Spirebluff Canal) at $3-8 — untapped for free in the early turns when it matters most, tapped later. 3) Pain lands (Underground River, Shivan Reef) at $1-3 — always untapped, 1 life per colored activation. 4) Check lands (Drowned Catacomb, Sulfur Falls) at $2-5 — conditional untapped, unreliable in Legacy. Avoid: Triomes (always tapped, too slow), tap lands, bounce lands. The best budget mana base mixes 2-3 shock lands with 1-2 fast lands."
        ),
        # Honest about what CAN'T be replaced
        pair(
            "What Legacy staples have no budget replacement?",
            "Some cards are truly irreplaceable: 1) Force of Will — the only card that counters any spell for free at any time. Force of Negation only works on opponent's turn for noncreature spells. If you can't afford Force of Will, play a non-blue deck. 2) Lion's Eye Diamond — unique fast mana in Storm. Without it, switch to Ruby Storm which doesn't use LED. 3) The Tabernacle at Pendrell Vale ($5,000+) — nothing else does what it does in Lands. 4) Gaea's Cradle — Itlimoc is technically similar but far too slow. 5) Mox Diamond in Lands specifically — discarding a land is an upside with Life from the Loam. For all of these, the budget path is to play a deck that doesn't need them."
        ),
        # Upgrade path
        pair(
            "I have budget Dimir Tempo with shocklands. What should I upgrade first?",
            "Upgrade priority: 1) First Underground Sea ($600-800) — replace your most-fetched Watery Grave. This single swap saves you 2+ life per game. 2) Second Underground Sea — now you rarely need to shock. 3) Third Underground Sea — full playset means you almost never take shockland damage. 4) Fourth Underground Sea is optional — many lists only run 3 and keep 1 Watery Grave anyway. Each Underground Sea you add directly reduces life loss, which matters most against Burn, aggressive Ocelot Pride builds, and Izzet Delver. The $600-800 per copy is steep but the card holds its value as a Reserved List staple."
        ),
        # Budget sideboard
        pair(
            "Are Legacy sideboards expensive?",
            "Most sideboard staples are surprisingly affordable. Surgical Extraction ($5-8), Leyline of the Void ($5-10), Pyroblast ($2-3), Hydroblast ($2-3), Flusterstorm ($15-20), Null Rod ($8-12), Collector Ouphe ($1-2), Tormod's Crypt ($0.50), Grafdigger's Cage ($2-3). The expensive ones: Force of Negation ($40-50) and Subtlety ($15-20). A full competitive sideboard costs $50-150 for most decks. Don't skimp on sideboards — they are how you win games 2 and 3, and they are the cheapest part of a Legacy deck."
        ),
        # Mana base on MTGO
        pair(
            "Is Legacy cheaper on MTGO?",
            "Dramatically. The biggest reason: dual lands are $2-5 on MTGO instead of $600-800 in paper. Force of Will is about $10 instead of $80-100. A full Dimir Tempo deck costs about $200-300 on MTGO compared to $4,955 in paper. MTGO Legacy is thriving with weekly Challenges, Leagues, and Showcase events. If you want to play Legacy competitively without the paper investment, MTGO is by far the most accessible path. The downside: no physical cards, and WotC could theoretically shut down the platform."
        ),
    ]
    write_jsonl("budget_substitutions.jsonl", entries)
    return len(entries)


def gen_card_evaluation():
    """Generate card evaluation pairs with correct stats from Scryfall."""
    entries = [
        # Counterspell (was wrong before)
        pair(
            "Is Counterspell good in Legacy?",
            "Counterspell is playable but not a staple. It costs UU (2 mana, both blue) and counters any spell unconditionally. The problem: Legacy is a format of mana efficiency, and UU on turn 2 means you cannot deploy a threat and hold up countermagic. Daze (free with Island bounce) and Force of Will (free with card exile) are preferred because they let you interact while tapped out. Counterspell sees play in slower blue decks like Miracles and Beanstalk Control where you plan to hold up mana anyway, but tempo decks prefer Spell Pierce, Daze, and Force."
        ),
        # Orcish Bowmasters (correct stats this time)
        pair(
            "What are Orcish Bowmasters' stats and abilities?",
            "Orcish Bowmasters costs 1B (one generic, one black) and is a 1/1 Orc Archer creature with Flash. It has two abilities: 1) When it enters the battlefield, it deals 1 damage to any target and amasses Orcs 1 (creates a 1/1 Orc Army token or puts a +1/+1 counter on an existing one). 2) Whenever an opponent draws a card except the first one they draw in each of their draw steps, it deals 1 damage to any target and amasses Orcs 1. This means Brainstorm (draw 3) triggers Bowmasters twice (the 2nd and 3rd cards drawn). It is the most played creature in Legacy at 29% of decks."
        ),
        # Tamiyo
        pair(
            "Is Tamiyo, Inquisitive Student Legacy-playable?",
            "Yes, Tamiyo is a Legacy staple in Dimir Tempo. She costs U as a 0/3 creature that investigates when she deals combat damage. After you've investigated 3+ times, she transforms into a planeswalker that generates card advantage. In Legacy, the 0/3 body blocks Bowmasters tokens and survives Gut Shot, the investigate triggers fuel delve for Murktide Regent, and the planeswalker side provides grinding power. She has replaced Delver of Secrets in many Dimir Tempo lists because she is more reliable and provides card advantage rather than just a clock."
        ),
        # Barrowgoyf
        pair(
            "Is Barrowgoyf Legacy-playable?",
            "Yes, Barrowgoyf is a Legacy staple in Dimir Tempo and other graveyard-fueled decks. It is the Modern Horizons 3 successor to Tarmogoyf with improved efficiency in a format full of diverse card types in graveyards. Between fetchlands, cantrips, Thoughtseize, and removal spells, Legacy naturally fills graveyards with many card types, making Barrowgoyf a large, cheap threat. It has largely replaced Tarmogoyf in the format."
        ),
        # The One Ring
        pair(
            "Is The One Ring Legacy-playable?",
            "Yes, The One Ring sees play in prison and control decks. For 4 mana, it gives you protection from everything until your next turn (buying a full turn cycle), then draws increasing cards each turn: 1, then 2, then 3. In decks that can slow the game down (Stompy, 8-Cast, Control), it provides unbeatable card advantage. The burden counters dealing damage to you is the cost, but prison decks mitigate this by locking out the opponent before it matters. It's a format staple in artifact strategies but too slow for tempo decks."
        ),
        # Urza's Saga
        pair(
            "Is Urza's Saga Legacy-playable?",
            "Yes, Urza's Saga is one of the most impactful lands in Legacy. It is an Enchantment Land — Saga that creates construct tokens (which grow based on your artifact count) and then tutors for a 0-1 mana artifact. In Legacy, it finds Retrofitter Foundry, Shadowspear, Pithing Needle, Tormod's Crypt, and other silver bullets. It is core to 8-Cast, Affinity Stompy, Painter, and even some Death and Taxes builds. The card provides both a clock and utility in one land slot."
        ),
        # Solitude
        pair(
            "Is Solitude Legacy-playable?",
            "Yes, Solitude sees play in white midrange and control decks, particularly Ocelot Pride Midrange. It costs 3WW as a 3/2 lifelink creature, but its evoke cost (exile a white card from hand) lets you Swords to Plowshares a creature for free at instant speed. The lifelink body is relevant when hard-cast. It is strong in white-based decks that have enough white cards to pitch. Unlike Grief (which was banned), Solitude's free exile effect is considered fair because it trades 1-for-1 without the reanimate combo."
        ),
        # Chalice of the Void
        pair(
            "How good is Chalice of the Void in Legacy?",
            "Chalice of the Void is one of the best cards in Legacy, particularly on 1. It costs XX (so Chalice on 1 costs 2 mana). In a format where 43% of decks play Brainstorm and 38% play Ponder, Chalice on 1 shuts off the most played cards. It is core to Eldrazi (3.1%), Red Stompy (2.7%), Affinity Stompy (2.4%), and other prison strategies that use Ancient Tomb and City of Traitors to cast it on turn 1. Chalice on 0 hits Lotus Petal, Chrome Mox, and Mox Opal. The card defines what prison means in Legacy."
        ),
        # Natural Order
        pair(
            "Is Natural Order Legacy-playable?",
            "Natural Order is niche but sees occasional play. For 2GG, you sacrifice a green creature to search your library for a green creature and put it onto the battlefield. It historically powered Elves and Natural Order decks by tutoring Progenitus or Craterhoof Behemoth. In the current meta, it is not a major player — Orcish Bowmasters punishes the small green creatures you need to sacrifice, and the 4-mana sorcery speed makes it vulnerable to Daze and Force of Will. It's at less than 1% of the meta."
        ),
        # Pact of Negation
        pair(
            "Is Pact of Negation Legacy-playable?",
            "Yes, in combo decks specifically. Pact of Negation counters a spell for free — you pay 3UU on your next upkeep or lose the game. In combo decks like Oops! All Spells, you plan to win on the turn you cast Pact, so the upkeep cost never matters. It is not playable in fair decks because paying 3UU next turn is backbreaking. Oops runs Pact alongside Force of Will for maximum free protection of its combo turn. It is also occasionally seen in Doomsday and Show and Tell decks."
        ),
    ]
    write_jsonl("card_evaluation.jsonl", entries)
    return len(entries)


def gen_card_relevance():
    """Generate card relevance pairs with color/strategy constraints."""
    entries = [
        # White removal (the one that was wrong)
        pair(
            "What removal spell should I play in a white Legacy deck?",
            "Swords to Plowshares is the gold standard — W for instant-speed exile of any creature. No other white removal comes close in efficiency. After that: Solitude provides free exile by pitching a white card. Prismatic Ending hits any nonland permanent with MV equal to colors of mana spent. Council's Judgment exiles any nonland permanent and ignores hexproof and protection. March of Otherworldly Light exiles artifacts, creatures, or enchantments. All white. Do not look to other colors — white has the best creature removal in Legacy."
        ),
        # Blue card selection
        pair(
            "What are the best blue card selection spells in Legacy?",
            "Brainstorm (U, instant, draw 3 put 2 back) is the best — combined with fetchlands it's effectively draw 3. Ponder (U, sorcery, look at top 3, may shuffle) is second — always paired with Brainstorm. Preordain (U, sorcery, scry 2 then draw 1) is a distant third but still playable. Consider Bolas's Citadel in some lists. For countermagic: Force of Will (free), Daze (free), Force of Negation (free on opponent's turn), Spell Pierce (U), Flusterstorm (U, storm copies). All blue. Blue's card selection is why it is the dominant color in Legacy."
        ),
        # Black disruption
        pair(
            "What are the best black disruption spells for Legacy?",
            "Thoughtseize (B, take any nonland card, lose 2 life) is the best — surgical hand disruption for 1 mana. Orcish Bowmasters (1B, flash creature, punishes cantrips) doubles as disruption and a threat. Fatal Push (B, destroys creature with MV 2 or less, or 4 with revolt) is the best cheap black removal. Snuff Out (free with a Swamp, destroys nonblack creature for 4 life) gives free removal. Hymn to Tourach (BB, opponent discards 2 random) is devastating but random. Toxic Deluge (2B, all creatures get -X/-X) is the best black board wipe."
        ),
        # Red cards for aggro
        pair(
            "What are the best red cards for an aggressive Legacy deck?",
            "Lightning Bolt (R, 3 damage to any target) is the benchmark. Rite of Flame (R, add RR) for Storm. Pyroblast (R, counter blue spell or destroy blue permanent) is essential sideboard. Blood Moon (2R, nonbasic lands become Mountains) punishes greedy mana bases. Broadside Bombardiers sees play in Mardu Energy. For creatures: Dragon's Rage Channeler (R, 1/1 that grows with delirium), Goblin Welder (R, swap artifacts) in Painter. Red excels at direct damage, mana denial, and artifact synergies."
        ),
        # Green cards in Legacy
        pair(
            "What green cards are Legacy-playable?",
            "Green is less dominant than blue or black but has strong niche cards. Endurance (2G, flash, shuffles graveyard — free via evoke) is premium graveyard hate. Collector Ouphe (1G, shuts off artifacts) is a powerful sideboard card. Life from the Loam (1G, dredge back lands) is the engine of the Lands deck. Exploration (G, play extra lands) enables Lands' fast starts. Green Sun's Zenith (XG, tutor a green creature) provides a creature toolbox. Tarmogoyf/Barrowgoyf in BG shells. Green's strength is in creature-based strategies and land-focused decks."
        ),
        # Anti-graveyard cards (correct ones this time)
        pair(
            "What are the best sideboard cards against graveyard decks in Legacy?",
            "Leyline of the Void (free if in opening hand, exiles all opponent's graveyard cards) is the strongest — 36% of decks play it. Surgical Extraction (free, exile all copies of a specific card from everywhere) is precision removal. Endurance (free via evoke, shuffles opponent's graveyard into library) is the best green option. Tormod's Crypt (0 mana artifact, sacrifice to exile a graveyard) is the cheapest option. Grafdigger's Cage (1 mana artifact, prevents cards in graveyards from entering play) stops Reanimator and Dread Return. Rest in Peace (1W, exiles all graveyards permanently) if you're in white."
        ),
        # Anti-combo cards
        pair(
            "What cards should I put in my sideboard to beat combo?",
            "Depends on your colors. Blue: Force of Will (main), Force of Negation, Flusterstorm (stops Storm cold), Mindbreak Trap (free vs Storm). Black: Thoughtseize (main), Surgical Extraction. White: Thalia Guardian of Thraben (taxes all spells), Deafening Silence (1 noncreature per turn), Containment Priest (exiles cheated creatures), Ethersworn Canonist (1 nonartifact per turn). Red: Pyroblast (counters blue combo enablers), Red Elemental Blast. Colorless: Chalice of the Void (counters specific MV), Trinisphere (everything costs 3+). Pick based on your colors and which combo decks you expect."
        ),
        # Cards for a UW control deck
        pair(
            "What are the core cards for a UW control deck in Legacy?",
            "The UW control shell in Legacy: Card selection: 4 Brainstorm, 4 Ponder. Countermagic: 4 Force of Will, 2-3 Counterspell, 1-2 Force of Negation. Removal: 4 Swords to Plowshares, 1-2 Prismatic Ending, 1-2 Council's Judgment. Threats: 2-3 Monastery Mentor or Shark Typhoon. Card advantage: 2-3 Up the Beanstalk (if running pitch spells). Lands: Tundra (or Hallowed Fountain on budget), fetchlands, basics. The key to UW is that every card is white or blue — no off-color splashes diluting the mana base."
        ),
        # Cards for a mono-red deck
        pair(
            "What cards should be in a mono-red Legacy deck?",
            "Mono-red in Legacy means either Burn or Red Stompy. Burn: 4 Lightning Bolt, 4 Chain Lightning, 4 Rift Bolt, 4 Lava Spike, 4 Price of Progress (devastating vs nonbasics), 4 Eidolon of the Great Revel, 4 Goblin Guide. Red Stompy/Prison: 4 Chalice of the Void, 4 Blood Moon, 2-3 Trinisphere, 4 Ancient Tomb, 4 City of Traitors, 3-4 Chrome Mox, threats like Fury, Caves of Chaos Adventurer, or Broadside Bombardiers. All cards are red or colorless — no other colors needed."
        ),
    ]
    write_jsonl("card_relevance.jsonl", entries)
    return len(entries)


def gen_deck_construction():
    """Generate structured deck construction examples with exactly 60+15."""
    entries = [
        # Dimir Tempo complete list
        pair(
            "Give me a complete Dimir Tempo decklist for Legacy.",
            "Main Deck (60 cards): 4 Brainstorm, 4 Ponder, 4 Force of Will, 4 Daze, 3 Thoughtseize, 3 Fatal Push, 2 Spell Pierce, 1 Snuff Out, 4 Tamiyo Inquisitive Student, 4 Orcish Bowmasters, 3 Murktide Regent, 4 Barrowgoyf, 4 Polluted Delta, 3 Misty Rainforest, 2 Scalding Tarn, 4 Underground Sea, 1 Watery Grave, 4 Wasteland, 1 Island, 1 Swamp. (Total: 4+4+4+4+3+3+2+1+4+4+3+4+4+3+2+4+1+4+1+1 = 60) Sideboard (15 cards): 2 Surgical Extraction, 2 Hydroblast, 1 Force of Negation, 1 Dismember, 1 Sheoldred's Edict, 2 Plague Engineer, 1 Subtlety, 1 Stern Scolding, 1 Nihil Spellbomb, 2 Flusterstorm, 1 Massacre. (Total: 2+2+1+1+1+2+1+1+1+2+1 = 15)"
        ),
        # Oops! All Spells complete list
        pair(
            "Give me a complete Oops! All Spells decklist for Legacy.",
            "Main Deck (60 cards): 4 Balustrade Spy, 4 Undercity Informer, 4 Narcomoeba, 1 Thassa's Oracle, 1 Dread Return, 4 Force of Will, 4 Pact of Negation, 3 Force of Negation, 4 Dark Ritual, 4 Lotus Petal, 4 Chrome Mox, 4 Elvish Spirit Guide, 4 Simian Spirit Guide, 4 Summoner's Pact, 3 Once Upon a Time, 4 Agadeem's Awakening, 4 Sea Gate Restoration. (Total: 4+4+4+1+1+4+4+3+4+4+4+4+4+4+3+4+4 = 60) Sideboard (15 cards): 4 Leyline of the Void, 3 Thoughtseize, 2 Surgical Extraction, 2 Cabal Therapy, 1 Goblin Charbelcher, 1 Empty the Warrens, 1 Laboratory Maniac, 1 Dread Return. (Total: 4+3+2+2+1+1+1+1 = 15)"
        ),
        # Death and Taxes complete list
        pair(
            "Give me a complete Death and Taxes decklist for Legacy.",
            "Main Deck (60 cards): 4 Aether Vial, 4 Thalia Guardian of Thraben, 4 Stoneforge Mystic, 4 Flickerwisp, 3 Skyclave Apparition, 2 Solitude, 2 Phelia Exuberant Shepherd, 1 Palace Jailer, 4 Swords to Plowshares, 1 Batterskull, 1 Kaldra Compleat, 4 Rishadan Port, 4 Wasteland, 9 Plains, 4 Cavern of Souls, 1 Eiganjo Castle, 1 Karakas, 4 Flagstones of Trokair, 3 Silent Clearing. (Total: 4+4+4+4+3+2+2+1+4+1+1+4+4+9+4+1+1+4+3 = 60) Sideboard (15 cards): 2 Containment Priest, 2 Surgical Extraction, 2 Ethersworn Canonist, 2 Rest in Peace, 1 Deafening Silence, 1 Council's Judgment, 2 Faerie Macabre, 1 Tomik Distinguished Advokist, 1 Cathar Commando, 1 Pithing Needle. (Total: 2+2+2+2+1+1+2+1+1+1 = 15)"
        ),
        # Sneak and Show complete list
        pair(
            "Give me a complete Sneak and Show decklist for Legacy.",
            "Main Deck (60 cards): 4 Show and Tell, 4 Sneak Attack, 3 Emrakul the Aeons Torn, 3 Atraxa Grand Unifier, 4 Brainstorm, 4 Ponder, 4 Force of Will, 2 Daze, 1 Spell Pierce, 4 Lotus Petal, 3 Ancient Tomb, 2 City of Traitors, 4 Scalding Tarn, 3 Flooded Strand, 2 Volcanic Island, 2 Island, 3 Preordain, 2 Lórien Revealed, 2 Impulse, 4 Misty Rainforest. (Total: 4+4+3+3+4+4+4+2+1+4+3+2+4+3+2+2+3+2+2+4 = 60) Sideboard (15 cards): 3 Pyroclasm, 2 Pyroblast, 2 Flusterstorm, 2 Surgical Extraction, 1 Kozilek's Return, 1 Grafdigger's Cage, 1 Boseiju Who Endures, 1 Defense Grid, 1 Blood Moon, 1 Omniscience. (Total: 3+2+2+2+1+1+1+1+1+1 = 15)"
        ),
        # The EPIC Storm complete list
        pair(
            "Give me a complete TES (The EPIC Storm) decklist for Legacy.",
            "Main Deck (60 cards): 4 Burning Wish, 4 Dark Ritual, 4 Rite of Flame, 4 Lion's Eye Diamond, 4 Lotus Petal, 4 Chrome Mox, 4 Brainstorm, 4 Ponder, 2 Galvanic Relay, 1 Tendrils of Agony, 1 Ad Nauseam, 1 Echo of Eons, 2 Beseech the Mirror, 2 Wishclaw Talisman, 3 Badlands, 2 Volcanic Island, 1 Underground Sea, 4 Bloodstained Mire, 4 Scalding Tarn, 1 Swamp, 4 Mishra's Bauble. (Total: 4+4+4+4+4+4+4+4+2+1+1+1+2+2+3+2+1+4+4+1+4 = 60) Sideboard (15 cards): 1 Tendrils of Agony, 1 Empty the Warrens, 1 Peer into the Abyss, 1 Grapeshot, 1 Pulverize, 1 Shattering Spree, 1 Massacre, 2 Galvanic Relay, 1 Echo of Eons, 2 Defense Grid, 2 Carpet of Flowers, 1 Chain of Vapor. (Total: 1+1+1+1+1+1+1+2+1+2+2+1 = 15)"
        ),
        # Burn complete list
        pair(
            "Give me a complete Burn decklist for Legacy.",
            "Main Deck (60 cards): 4 Lightning Bolt, 4 Chain Lightning, 4 Rift Bolt, 4 Lava Spike, 4 Price of Progress, 4 Fireblast, 2 Searing Blaze, 4 Eidolon of the Great Revel, 4 Goblin Guide, 4 Monastery Swiftspear, 2 Roiling Vortex, 10 Mountain, 4 Inspiring Vantage, 2 Battlefield Forge, 2 Fiery Islet, 2 Sunbaked Canyon. (Total: 4+4+4+4+4+4+2+4+4+4+2+10+4+2+2+2 = 60) Sideboard (15 cards): 4 Leyline of the Void, 3 Smash to Smithereens, 2 Pyroblast, 2 Searing Blood, 2 Exquisite Firecraft, 1 Sulfuric Vortex, 1 Ensnaring Bridge. (Total: 4+3+2+2+2+1+1 = 15)"
        ),
    ]
    write_jsonl("deck_construction.jsonl", entries)
    return len(entries)


def gen_disambiguation():
    """Generate disambiguation pairs for cards vs mechanics vs archetypes."""
    entries = [
        # Dredge the mechanic vs Dredge the deck
        pair(
            "What is Dredge in Legacy?",
            "Dredge can mean two things in Legacy: 1) The MECHANIC: Dredge N means 'instead of drawing a card, you may mill N cards and return this card from your graveyard to your hand.' Cards like Golgari Grave-Troll (dredge 6) and Stinkweed Imp (dredge 5) have this mechanic. 2) The DECK: Dredge is a Legacy archetype that abuses the dredge mechanic to fill its graveyard rapidly, then wins with Narcomoeba triggers, Ichorid recurring from the graveyard, and Bridge from Below creating zombie tokens. The deck barely casts spells — it replaces draws with dredge to fuel graveyard synergies. When someone says 'I'm playing Dredge' they mean the deck. When they say 'dredge back my Loam' they mean the mechanic."
        ),
        # Storm the mechanic vs Storm the deck
        pair(
            "What is Storm in Legacy?",
            "Storm can mean two things: 1) The MECHANIC: Storm is a keyword that says 'when you cast this spell, copy it for each spell cast before it this turn.' So if you've cast 9 spells and then cast Tendrils of Agony (storm), you get 10 copies total, each draining 2 life = 20 damage. 2) The DECK(S): Several Legacy decks are called Storm — The EPIC Storm (TES) at 3.5% meta share uses Burning Wish, rituals, and Lion's Eye Diamond. ANT (Ad Nauseam Tendrils) is a related variant. Ruby Storm uses Ruby Medallion for cost reduction. All Storm decks aim to cast many cheap spells in one turn and win with a storm finisher."
        ),
        # Delver the card vs Delver the archetype
        pair(
            "What is Delver in Legacy?",
            "Delver can mean two things: 1) The CARD: Delver of Secrets is a 1-mana 0/1 creature that transforms into Insectile Aberration, a 3/2 flyer, when you reveal an instant or sorcery on top of your library during upkeep. 2) The ARCHETYPE: Delver decks are tempo strategies built around cheap threats plus countermagic and removal. Izzet Delver (UR, 4.3%) still plays the actual card. Dimir Tempo (UB, 14.6%) evolved from Delver but many lists no longer play Delver of Secrets, replacing it with Tamiyo Inquisitive Student. When someone says 'Delver decks' they usually mean the broader tempo archetype, not necessarily decks running the card."
        ),
        # Painter the card vs Painter the deck
        pair(
            "What is Painter in Legacy?",
            "Painter refers to: 1) The CARD: Painter's Servant is a 1/3 artifact creature for 2 mana that makes all cards everywhere the chosen color. 2) The DECK: Painter is a combo deck at 4.1% meta share that combines Painter's Servant with Grindstone. When you name a color with Painter's Servant, all cards become that color. Grindstone mills 2 cards at a time and repeats if they share a color — since all cards now share a color, it mills the opponent's entire library. The deck also uses Goblin Welder, Goblin Engineer for recursion, and Red Elemental Blast becomes an unconditional counter when Painter makes everything blue."
        ),
        # Show and Tell the card vs the deck
        pair(
            "Is Show and Tell a creature?",
            "No. Show and Tell is a SORCERY that costs 2U. Its text: 'Each player may put an artifact, creature, enchantment, or land card from their hand onto the battlefield.' It is not a creature, permanent, or anything that stays on the battlefield — it resolves and goes to the graveyard. The confusion may come from the deck named 'Sneak and Show' which uses Show and Tell to cheat CREATURES (Emrakul, Atraxa) into play. But Show and Tell itself is just the delivery method. It cannot be bounced by Karakas, killed by Swords to Plowshares, or targeted by creature removal."
        ),
        # Wasteland the card vs 'wasting' someone
        pair(
            "What does it mean to 'waste' someone in Legacy?",
            "In Legacy slang, 'to waste someone' means to destroy their land with Wasteland. Wasteland is a land card that sacrifices itself to destroy target nonbasic land. 'I wasted their Underground Sea' means 'I activated Wasteland targeting their Underground Sea, destroying it.' 'Getting wasted' means having your land destroyed. This is different from the general meaning of waste. The terminology is important because Wasteland is in 48% of Legacy decks and mana denial is a core format dynamic."
        ),
        # Flash the keyword vs flash decks
        pair(
            "What does Flash mean in Legacy?",
            "Flash has multiple meanings: 1) The KEYWORD: Flash means a spell can be cast at instant speed. Orcish Bowmasters has flash, meaning you can cast it on your opponent's turn. 2) The BANNED CARD: Flash is an actual card (1U instant) that was banned in Legacy. It lets you put a creature from your hand onto the battlefield, then sacrifice it unless you pay its mana cost. With Protean Hulk, this was a turn-1 kill combo. The card has been banned since 2008. 3) Flash as a concept: 'flash creatures' refers to any creature with the flash keyword. When someone says 'Bowmasters has flash' they mean the keyword. Nobody means the banned card in a current deck context."
        ),
        # Force the card vs 'force' as a verb
        pair(
            "What does 'Force' mean in Legacy?",
            "In Legacy slang, 'Force' almost always means Force of Will unless specified otherwise. 'I Forced it' = I countered it with Force of Will. 'Do you have Force?' = Do you have Force of Will in hand? Related cards: Force of Negation (often called 'FoN' or 'Negation') only works on opponent's turn for noncreature spells. Force of Vigor (green, destroys artifacts/enchantments). When someone says 'I'm playing Force,' they mean Force of Will specifically. The card is in 45% of Legacy decks and is the format's defining interaction."
        ),
        # Lands the deck vs lands the card type
        pair(
            "What is Lands in Legacy?",
            "Lands (capital L) is a specific Legacy deck at 3.8% meta share. It wins almost entirely through land abilities: Life from the Loam + Wasteland for recurring mana denial, Dark Depths + Thespian's Stage to create a 20/20 indestructible token, Exploration for extra land drops, Maze of Ith to blank attackers, and Punishing Fire with Grove of the Burnwillows for recurring removal. The deck costs about $8,284, driven by The Tabernacle at Pendrell Vale ($5,000+). When someone says 'I'm on Lands' they mean this specific deck, not just 'a deck that plays lands.'"
        ),
    ]
    write_jsonl("disambiguation.jsonl", entries)
    return len(entries)


def gen_uniqueness():
    """Generate uniqueness/brew pairs with novel deck concepts."""
    entries = [
        # Unique brew: UB Faeries Tempo
        pair(
            "Build me a unique Legacy deck that uses an unusual strategy.",
            "Here is a UB Faeries Tempo concept: Main threats: 4 Spellstutter Sprite (counters spells with MV equal to your Faerie count), 4 Brazen Borrower (bounce + 3/1 flash flyer), 2 Vendilion Clique (hand disruption + flying clock). Support: 4 Brainstorm, 4 Ponder, 4 Force of Will, 3 Daze, 3 Thoughtseize, 4 Orcish Bowmasters, 2 Spell Pierce, 2 Fatal Push. Lands: 4 Underground Sea, 4 Polluted Delta, 3 Misty Rainforest, 4 Wasteland, 2 Island, 1 Swamp, 2 Mutavault (becomes a Faerie for Spellstutter). The idea: all your threats have flash, so you never tap out on your own turn. Spellstutter gets better in multiples. Not tier 1 but a unique angle that leverages tribal synergies with Legacy's best disruption."
        ),
        # Unique brew: Mono-Black Control
        pair(
            "I want to build a unique black-based Legacy deck that is not Dimir Tempo.",
            "Mono-Black Pox control: 4 Smallpox (both players sacrifice a creature, discard, sacrifice a land — devastating vs tempo), 4 Hymn to Tourach (2-for-1 hand destruction), 4 Thoughtseize, 4 Dark Ritual (powers out early Hymns and Liliana), 3 Liliana of the Veil (repeated discard and sacrifice), 2 Toxic Deluge (board wipe), 3 Tourach Dread Cantor, 2 Nether Spirit (recurring threat that comes back from the graveyard if it is the only creature there), 4 Wasteland, 4 Rishadan Port (additional mana denial), 2 Urborg Tomb of Yawgmoth (makes Wasteland and Port tap for black), 4 Mishra's Factory (creature-land for Smallpox), 10 Swamp, 2 Castle Locthwain, 2 Bojuka Bog. The strategy: strip their hand, their board, and their mana simultaneously. You win with inevitability from recursive threats while they have nothing."
        ),
        # Unique brew: RG Lands Aggro
        pair(
            "Build me a Legacy deck that uses lands as its primary win condition but is different from the traditional Lands deck.",
            "RG Aggressive Lands: Instead of the slow Life from the Loam engine, go aggressive with land-based damage. 4 Valakut the Molten Pinnacle, 3 Primeval Titan, 4 Explore, 4 Exploration, 4 Sakura-Tribe Elder, 2 Ramunap Excavator, 4 Green Sun's Zenith (finds Titan, Elder, Excavator), 3 Crop Rotation (instant-speed Valakut or utility land), 4 Ancient Stirrings, 2 Blast Zone, 4 Wasteland, 4 Taiga, 2 Stomping Ground, 6 Mountain, 4 Forest, 2 Windswept Heath, 3 Wooded Foothills. Sideboard: 3 Pyroblast, 2 Collector Ouphe, 3 Endurance, 2 Force of Vigor, 2 Red Elemental Blast, 2 Choke, 1 Karakas. The idea: ramp into Primeval Titan, fetch Valakut + Mountains, and burn them out with land-based damage triggers."
        ),
        # Unique brew: Enchantress
        pair(
            "I want to build a Legacy deck that nobody expects but can win tournaments.",
            "Enchantress is a sleeper strategy at under 1% meta share. Core: 4 Enchantress's Presence (draw a card for each enchantment you cast), 4 Argothian Enchantress (same effect on a creature, has shroud), 4 Sythis Harvest's Hand (same effect but with lifegain), 4 Utopia Sprawl (mana + cantrip with Enchantress), 4 Wild Growth (same), 4 Solitary Confinement (you cannot be attacked or targeted — you skip your draw step but Enchantress effects replace drawing), 2 Rest in Peace (graveyard hate that is also an enchantment cantrip), 3 Destiny Spinner (uncounterable enchantments), 2 Emrakul the Aeons Torn (win condition shuffled back by Rest in Peace loop). Lands: 4 Serra's Sanctum (taps for W per enchantment you control), 4 Windswept Heath, 6 Forest, 2 Plains, 2 Savannah. The advantage: nobody sideboards for Enchantress because nobody plays it, so you face minimal hate in games 2-3."
        ),
    ]
    write_jsonl("uniqueness.jsonl", entries)
    return len(entries)


def gen_negative_examples():
    """Generate negative examples teaching the model to express uncertainty."""
    entries = [
        # Don't know specific meta percentage
        pair(
            "What is the exact win rate of Ocelot Pride Midrange vs Dimir Tempo?",
            "I do not have exact win rate data for that specific matchup. What I can tell you is that Ocelot Pride Midrange is generally considered slightly unfavorable against Dimir Tempo based on tournament results and community consensus. Bowmasters and Thoughtseize are effective against Ocelot's creature-based strategy. For precise win rates, check MTGGoldfish's matchup data or tournament result aggregators, which track head-to-head records from MTGO leagues."
        ),
        # Don't know a specific card interaction
        pair(
            "Does Dress Down remove Orcish Bowmasters' ability before it triggers on ETB?",
            "This is a complex layers interaction that depends on timing and the current rules. Dress Down removes all abilities from creatures. Whether it prevents Bowmasters' ETB trigger depends on whether Bowmasters enters with the trigger already on the stack or whether Dress Down's continuous effect removes it first. I am not confident in my answer here — check the MTG Comprehensive Rules section on layers (613) and triggered abilities (603), or ask a judge. Getting this wrong in a tournament could cost you a game."
        ),
        # Don't know future meta shifts
        pair(
            "What will the Legacy meta look like after the next set release?",
            "I cannot predict how future card releases will change the Legacy metagame. Legacy is affected by new cards less frequently than Standard or Modern, but when it is affected, the changes can be dramatic — Orcish Bowmasters from Lord of the Rings completely reshaped the format in 2023. What I can say: watch for efficient creatures and free spells, which tend to have the most Legacy impact. Check Legacy content creators and the first MTGO Challenge results after a new set releases for early signals."
        ),
        # Don't know a specific card's price
        pair(
            "How much does Orcish Bowmasters cost right now?",
            "I do not have real-time pricing data. Card prices fluctuate based on demand, reprints, and meta shifts. For current prices, check TCGPlayer, CardKingdom, or the Scryfall price tracker. What I can say is that Orcish Bowmasters is a multi-format staple (Legacy, Modern, Vintage) which tends to keep prices high, and as a Lord of the Rings mythic rare it has limited reprint potential."
        ),
        # Admit when a question is outside scope
        pair(
            "Should I buy into Legacy right now or wait for reprints?",
            "I am not qualified to give financial advice. What I can tell you about the format: Legacy's cost is driven primarily by Reserved List cards (dual lands, Lion's Eye Diamond, etc.) which Wizards of the Coast has promised never to reprint. Non-Reserved List staples like Force of Will do get reprinted periodically, which reduces their price temporarily. If you're considering Legacy, MTGO is dramatically cheaper than paper ($200-300 vs $3,000-5,000 for a typical deck). The decision depends on your budget, your local Legacy community, and your risk tolerance."
        ),
        # Uncertain about a ruling
        pair(
            "If I cast Stifle targeting the Balustrade Spy trigger in Oops, what happens?",
            "I want to be precise here because getting this wrong matters. Balustrade Spy's mill effect is an enters-the-battlefield triggered ability. If you Stifle it, the trigger is countered and no cards are milled. However, I am not 100% certain whether Oops lists have other ways to trigger the mill if Spy's ETB is countered — they may have backup plans. Also verify: can Stifle actually counter Spy's trigger specifically, or does the deck have Pact of Negation to protect it? In a real game, call a judge for complex stack interactions."
        ),
        # Don't know tournament-specific info
        pair(
            "Who won the last Legacy Grand Prix?",
            "I do not have data on the most recent Legacy Grand Prix results. For current tournament results, check MTGGoldfish tournament results, MTGTop8, or the official Magic: The Gathering competitive events page. I can tell you about the general metagame trends and what decks are performing well in recent MTGO Challenges if that would be helpful."
        ),
        # Honest about card evaluation limits
        pair(
            "Is this new spoiled card Legacy-playable?",
            "I cannot evaluate cards I have not seen. To evaluate a new card for Legacy playability, consider: 1) Does it cost 0-2 mana? Cards above 2 mana need to be game-changing to see Legacy play. 2) Does it do something unique that existing cards do not? Legacy has 30+ years of cards. 3) Does it survive Orcish Bowmasters (1 damage ping)? 4) Does it work under Chalice of the Void or Thalia? 5) Does it slot into an existing archetype or enable a new one? Share the card's stats and text and I can give you a more informed opinion."
        ),
        # Don't fabricate matchup data
        pair(
            "What is Painter's exact win rate against every tier 1 deck?",
            "I do not have precise win rate percentages for every Painter matchup. What I can tell you from meta data and community consensus: Painter is generally favored against blue cantrip decks (Painter naming blue makes Red Elemental Blast unconditional), roughly even against combo (it has its own fast combo but lacks Force of Will in some builds), and can struggle against decks with artifact removal or Null Rod effects. For specific win rates, the best source is the Painter community thread on MTG Salvation or the MTGO league data on MTGGoldfish."
        ),
        # Admit uncertainty about rules
        pair(
            "What happens if both players put Emrakul into play off Show and Tell at the same time?",
            "Both Emrakuls enter simultaneously from Show and Tell. Since neither was CAST (Show and Tell puts them into play), neither player gets the extra turn trigger. Then, since both players control a legendary permanent with the same name, each player must choose one to keep and put the other into their graveyard (legend rule). Each player keeps their own Emrakul. However, I want to flag: if both Emrakuls hit the graveyard, their shuffle triggers activate. The exact timing and state-based action ordering here is complex — in a tournament, call a judge for simultaneous legend rule interactions."
        ),
        # Honest about model limitations
        pair(
            "Can you build me a perfectly optimized deck that will win every tournament?",
            "No deck wins every tournament in Legacy — the format is too diverse and skill-intensive for that. Dimir Tempo is the most played deck at 14.6% but only wins about 52.7% of its non-mirror matches. Even the best deck loses to bad matchups, poor draws, and mistakes. What I can do: help you build a well-constructed deck for a specific metagame, explain card choices and matchups, and help you understand the strategic reasoning behind deck construction. Winning consistently comes from format knowledge, practice, and sideboard tuning, not from having a perfect 75."
        ),
        # Don't know about a very niche interaction
        pair(
            "How does Chains of Mephistopheles interact with Brainstorm?",
            "Chains of Mephistopheles is one of the most complex cards ever printed, and its interaction with Brainstorm is notoriously confusing. The general idea: Chains replaces draws beyond the first with 'discard then draw' or 'mill if hand is empty.' With Brainstorm, the first card drawn is normal, but cards 2 and 3 are replaced by Chains' effect. The exact sequence depends on replacement effect ordering. This is a card where I strongly recommend reading the Oracle text carefully and consulting a judge or the MTG rules Q&A. I do not want to give you an incorrect ruling on one of Legacy's most complex interactions."
        ),
    ]
    write_jsonl("negative_examples.jsonl", entries)
    return len(entries)


def main():
    print("=== Generating Round 2 Training Data ===\n")

    total = 0
    total += gen_meta_awareness()
    total += gen_board_state()
    total += gen_budget_subs()
    total += gen_card_evaluation()
    total += gen_card_relevance()
    total += gen_deck_construction()
    total += gen_disambiguation()
    total += gen_uniqueness()
    total += gen_negative_examples()

    print(f"\nTotal new entries: {total}")

    # Print final counts for all files
    print("\n=== Final Training Data Counts ===")
    grand_total = 0
    for jsonl_file in sorted(TRAINING_DIR.glob("*.jsonl")):
        with open(jsonl_file, "r", encoding="utf-8") as f:
            count = sum(1 for _ in f)
        print(f"  {jsonl_file.name}: {count}")
        grand_total += count
    print(f"\n  TOTAL: {grand_total}")


if __name__ == "__main__":
    main()
