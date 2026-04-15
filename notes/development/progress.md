# The Legacy — Development Notes

Running notes on how development is going, what's working, what's not, and what to do next.

---

## Building the Dataset

### What we built
- 1,449 training pairs across 7 categories:
  - Rules Q&A (422 pairs) — sourced from comprehensive rules
  - Card evaluation (294 pairs) — Legacy playability assessments
  - Deck-building rationale (217 pairs) — why cards belong in archetypes
  - Deck analysis (146 pairs) — archetype classification, strengths/weaknesses
  - Board state analysis (130 pairs) — correct play identification
  - Budget substitutions (121 pairs) — functional replacements with trade-off honesty
  - Conversation flow (119 pairs) — multi-turn dialogue examples
- 22-case evaluation dataset across 9 categories

### What went well
- Good coverage across categories — not just rules trivia
- Eval dataset tests real capability (legality, meta awareness, card relevance, board reads)
- Baseline eval gave us a clear starting point (43.1%) to measure against

### What needs work
- Haven't done the hand-review pass on a curated subset yet (~200-300 examples)
- Some factual errors in training data surfaced during eval (Counterspell description, Bowmasters stats)
- Budget substitution pairs may be teaching the wrong thing — model recommends expensive cards like Mox Diamond instead of actual budget options

---

## Initial Training (Round 1)

### Setup
- LoRA finetune on the full 1,449-pair dataset
- 5 epochs with early stopping and train/val split
- Final training loss: 1.29

### Results
- Overall eval score: 54.8% (up from 43.1% baseline, +11.7%)
- Model pushed to HuggingFace Hub for persistence

### What improved
- The model picked up Legacy-specific knowledge it didn't have before
- Structured output improved (decklists closer to proper format)

### What regressed or stayed weak
- **Meta awareness**: 67% → 33% — model started hallucinating deck names that don't exist
- **Board state analysis**: 75% → 50% — got a Blood Moon ruling wrong it used to get right
- **Budget substitutions**: stuck at 10% — still recommending expensive cards
- **Card evaluation**: 13% → 29% — improved but still fabricating card stats (mana costs, P/T)

### Takeaways
- Finetuning helped where we had strong data (rules, deck building) but hurt where data was thin or had errors
- The model doesn't know how to say "I'm not sure" — it confidently hallucinates instead
- Round 2 needs: more pairs in weak categories, negative examples to teach uncertainty, and a factual accuracy scrub of existing data

---
