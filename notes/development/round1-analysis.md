# Round 1 Training Analysis — Honest Assessment

## Summary

LoRA finetune of Llama 3.2 1B Instruct on 1,449 training pairs. 5 epochs, rank 16, final loss 1.29. Overall eval score improved from 43.1% to 54.8% (+11.7%). That headline number masks a more complicated story: three categories improved dramatically, two regressed, and one didn't move at all.

---

## What Improved

### Rules Knowledge: 58% → 83% (+25%)

The strongest real improvement. Before finetuning, the base model made basic errors — calling Daze a "removal spell," confusing Karakas's ability, giving nonsensical explanations about mana triggers. After finetuning, the model correctly answers that you can't Daze without Islands, correctly handles Chalice vs. Force of Will's alternative cost, and gets the Karakas/Emrakul interaction right.

The one partial miss is Orcish Bowmasters triggers off Brainstorm — both baseline and finetuned get this partially wrong, but for different reasons. The baseline says Bowmasters "triggers 4 mana" (nonsense). The finetuned version says Bowmasters triggers off "spells with mana value 3 or less" (wrong — it triggers on opponent drawing cards). The finetuning taught it *something* about Bowmasters but not the correct trigger condition.

**Why it improved**: Rules Q&A was our largest training category (422 pairs, 29% of all data). Volume works.

### Deck Analysis: 17% → 67% (+50%)

The biggest single jump. Before finetuning, the model couldn't identify Sneak and Show from its card list — it described Show and Tell as "a basic creature that can be played" and Sneak Attack as dealing "2 damage to any target." After finetuning, it correctly identifies the archetype, names the combo, and explains the game plan.

Death and Taxes analysis is still weak — the finetuned model claims it has "a perfect win rate against all other decks" which is absurd. But the improvement from "doesn't know what these cards do" to "can identify archetypes and explain their game plan" is real.

**Why it improved**: 146 deck analysis pairs taught pattern recognition — given a list of cards, identify the archetype.

### Card Relevance: 0% → 50% (+50%)

The base model was completely lost here. Asked for tempo cards that beat combo, it recommended building "a combo deck." Asked for white removal, it suggested Lightning Bolt (a red card). After finetuning, it correctly recommends Brainstorm, Ponder, Thoughtseize, Daze, and Surgical Extraction as the core of an anti-combo tempo shell.

Still mixed — the graveyard sideboard answer recommends "Dredge" as a sideboard card against dredge decks (Dredge is the mechanic/deck, not a sideboard card), and it lists Pyroblast as destroying "Reanimate tokens" (not a thing). The white removal question still gets answered with blue/black cards (Daze, Surgical Extraction, Toxic Deluge), completely ignoring the "white" constraint.

**Why it improved**: 217 deckbuilding rationale pairs taught which cards go together. The model learned card associations even if it doesn't always respect constraints.

---

## What Regressed

### Meta Awareness: 67% → 33% (-33%)

This is the most concerning regression. The base model gave vague but roughly correct answers about the Legacy meta. After finetuning, the model confidently invents things:

- Claims "Orc & Giant Stompy" is the most played deck at 2.5% — this deck doesn't exist
- Repeats "Orcish Bowmasters" three times in the same deck description
- Gives bad strategic advice: says to beat Dimir Tempo you should not play Brainstorm, Ponder, or Force of Will — those are exactly the cards you *should* play in most decks
- Claims combo is more popular than fair strategies and wins 55-60% of matches — the actual meta data shows Dimir Tempo (a fair deck) at 14.6% is the most played

The finetuning taught the model to sound confident and use MTG vocabulary, but when it doesn't have specific knowledge, it generates plausible-sounding nonsense instead of hedging like the base model did.

**Why it regressed**: We had no meta awareness training pairs. The model learned a confident MTG-expert tone from other categories and applied it to meta questions where it has no data, replacing the base model's cautious "I don't know" with fabricated specifics.

### Board State: 75% → 50% (-25%)

Mixed results. The opening hand analysis improved — the finetuned model correctly says to keep the Dimir Tempo hand and explains why (which the baseline struggled with). But the Blood Moon question went from partially correct to completely wrong.

The base model said you can't use Polluted Delta under Blood Moon (getting the right answer for a somewhat wrong reason). The finetuned model says "Yes, you can use it" and then fabricates a rule about Blood Moon exiling lands from graveyards — completely wrong on the card's actual effect (it makes nonbasic lands into Mountains).

**Why it regressed**: Only 130 board state pairs, and clearly not enough Blood Moon scenarios. The model learned to give detailed-sounding answers about board interactions but doesn't have enough examples to get specific rulings right.

---

## What Didn't Move

### Budget Substitutions: 10% → 10% (no change)

The worst category, and finetuning didn't help at all. Asked for a budget replacement for Underground Sea ($400+), the finetuned model recommends Mox Diamond ($500+) and Mox Opal ($80+). It learned card names from training data but not the concept of "budget" — it's recommending expensive staples, not cheap alternatives.

The correct answer is Watery Grave ($10), Darkslick Shores ($3), or Underground River ($1). The training data for budget substitutions apparently didn't emphasize actual prices or the concept of trading down in power for savings.

The cheapest deck question gets a partial answer (names Oops All Spells, which is reasonable) but claims it costs $500-700 and uses "no dual lands, no fetches" — Oops All Spells actually uses Lion's Eye Diamond ($300+) and other expensive cards, so the price claim is wrong.

**Why it didn't improve**: 121 budget pairs, but the training data itself may have quality issues — if the examples don't consistently model "expensive card → cheaper alternative with trade-off," the model can't learn the pattern.

---

## What Stayed the Same

### Deck Legality: 100% → 100% (held)

The one perfect score, and it held. The model correctly knows the 4-copy rule and can flag illegal cards. This was likely already in the base model's training data since deck construction rules are widely documented.

Note: the deck *building* sub-task (constructing a full 75-card list) scored -1 both times — the model generates lists that look like decks but don't add up to exactly 60+15. This is a structured output problem more than a knowledge problem.

---

## Patterns Across Categories

### The Confidence Problem

The most consistent pattern: finetuning made the model more confident without making it more accurate in weak areas. The base model would hedge with "I can provide general information" or "this depends on the metagame." The finetuned model states things as facts, even when wrong:

- "Orc & Giant Stompy is the most played deck at 2.5%"
- "Death and Taxes has a perfect win rate against all other decks"
- "Orcish Bowmasters is a 1/1 trample for 1GG" (it's actually a 1/1 for 1B with a completely different ability)
- "Counterspell costs 1UU and counters a spell with mana value 2 or less" (it costs UU and counters any spell)

The model learned to mimic expert tone from the training data but applies it indiscriminately. This is worse than uncertainty in some ways — a user might trust a confident wrong answer.

### Data Volume Correlates With Improvement

| Category | Training Pairs | Score Change |
|---|---|---|
| rules_knowledge | 422 | +25% |
| card_evaluation | 294 | +17% |
| deckbuilding_rationale | 217 | +50% (card_relevance) |
| deck_analysis | 146 | +50% |
| board_state | 130 | -25% |
| budget_substitutions | 121 | 0% |
| conversation_flow | 119 | N/A (no direct eval) |
| meta_awareness | 0 | -33% |

The top two improvements (rules, card relevance) come from the two largest training categories. The regressions come from categories with either no data (meta) or thin data with errors (board state, budget).

### Factual Errors in Training Data Propagate

The Orcish Bowmasters card is consistently wrong across multiple categories — wrong stats (1/1 trample for 1GG vs actual 1/1 for 1B), wrong trigger (mana value check vs card draw trigger), wrong description. The Counterspell description is also wrong (costs 1UU vs actual UU, limited to mana value 2 or less vs actual "any spell"). These errors almost certainly come from the training data itself.

### The 1B Model Limitation

Llama 3.2 1B is a small model. Some failures may be fundamental capacity limits rather than data issues:
- Counting to 60 for deck construction (structured output)
- Tracking multiple interacting rules (Blood Moon + fetchlands)
- Distinguishing between similar card names and abilities
- Holding meta context (which decks beat which) across a response

These might improve with more data, or they might need a larger model.

---

## What Round 2 Needs

### High Priority
1. **Add meta awareness pairs** — Currently zero. The model needs concrete examples: "What's the most played deck?" → "Dimir Tempo at 14.6%." Without these, it will keep hallucinating deck names.
2. **Add negative examples** — Teach the model to say "I'm not sure" or "I don't have current data on that." Right now it never hedges.
3. **Fix factual errors** — Audit the training data for wrong card descriptions (Bowmasters, Counterspell, and likely others). Every wrong fact in training data becomes a wrong fact the model states confidently.

### Medium Priority
4. **Expand board state pairs** — Focus on common Legacy interactions: Blood Moon + nonbasics, Wasteland sequencing, fetchland priority, Chalice implications. 130 pairs wasn't enough.
5. **Fix budget substitution data** — The pairs need to consistently model the pattern: expensive card → cheaper card + what you lose. Include actual price ranges.
6. **Add more card evaluation pairs with correct stats** — The model fabricates mana costs and P/T values. Training pairs should always include the real stats.

### Lower Priority
7. **Expand deck building examples** — The model can't count to 60. May need structured output training or a different approach (generate slots, not full lists).
8. **Add multi-turn examples for weak categories** — Some categories only have single-turn Q&A. Multi-turn conversation examples might help the model maintain accuracy across a longer exchange.

---

## Bottom Line

The +11.7% improvement is real but misleading. What actually happened:

- Three categories got substantially better because we had good training data for them
- Two categories got worse because the model learned to be confidently wrong instead of cautiously wrong
- One category didn't move because the training data itself had issues
- The model never learned to say "I don't know"

Round 2 isn't just about adding more data. It's about adding the *right* data (meta awareness, negative examples), fixing the *wrong* data (card facts), and teaching the model when to be uncertain. The confidence problem is the single biggest issue — a model that's right 55% of the time but acts sure 100% of the time is dangerous for users who trust it.
