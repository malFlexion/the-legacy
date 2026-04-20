# Demo Checklist — The Legacy

Target: ~12 minutes + Q&A (trim demo-1 or demo-2 prompts if your slot is shorter — keep the shortcomings + future-work sections intact, they're where the Innovation points live). Rubric coverage priorities: Model (40 pts), Production (30 pts), Docs & Demo (30 pts).

---

## Pre-demo (T-30 to T-5)

- [ ] `fly status -a the-legacy-api` — confirm machine is `started`, not `stopped`
- [ ] `curl https://the-legacy-api.fly.dev/health | jq` — verify:
  - `status: ok`
  - `llm.reachable: true`
  - `vector_chunks: > 30000` (confirms card chunks rebuilt; if it says `719`, the sanity check caught a bad build or you're on an old image — redeploy)
  - `boot_time` is recent
- [ ] Open `https://the-legacy-api.fly.dev/` in browser. Hit the footer — RAG badge should be green, card-chunk count visible
- [ ] **Warm the model**: send one throwaway chat message ("Hello"). First request after idle pays a 10s load cost; you don't want that in the live demo
- [ ] Have a second browser tab open to the GitHub repo (`README.md` view)
- [ ] Close notifications / Slack / calendar popups
- [ ] Have the backup plan ready: if Fly hiccups, screen-share a pre-opened terminal with `curl https://the-legacy-api.fly.dev/chat` examples

---

## Opening (≈30s)

**Say:**

> "The Legacy is an AI assistant for Magic: The Gathering's Legacy format — a 30-year-old competitive format with 36,000+ legal cards, ~54 viable archetypes, and a card pool that includes Alpha. The challenge I wanted to tackle: take a 1B-parameter base model that knows almost nothing about this format, and make it give honest, factually-grounded answers about specific cards and the current metagame."

**Point to:** the header tagline, the footer ("Source · Llama 3.2 1B + LoRA · 1,549 training pairs · 28.9% → 61.6% eval · RAG over ~31k chunks")

---

## Architecture overview (≈1 min)

**Say:** "Three things make this work end-to-end: a LoRA finetune, ground-truth card injection, and a RAG layer. They're stacked in a single Fly.io container that runs FastAPI, Ollama, and ChromaDB together — one URL, no cross-service credentials."

**Mention:**
- **LoRA finetune**: Llama 3.2 1B, rank 16, 5 epochs, 1,546 training pairs across 13 categories (rules Q&A, card evaluation, deck-building rationale, meta awareness, etc.). Eval: **28.9% baseline → 61.6% finetuned, +32.7 points**.
- **Card injection pipeline**: before the LLM sees the query, a deterministic Python function extracts named cards, pulls their real Scryfall data, and injects it into the system prompt. *"This is what actually beats the generic-embedding-doesn't-know-MTG problem."*
- **RAG**: ~31k chunks in ChromaDB — comprehensive rules, archetype guides, meta analysis, and one chunk per Legacy-legal card. When card injection fires, RAG filters out the card chunks (we already have ground truth) and returns only strategy/rules context.

---

## Demo 1 — Chat tab (≈3 min)

The rubric's "Model Functionality" and "Innovation" lines ride on this. Use prompts that showcase card injection + RAG + clickable refs.

### Prompt 1 — Card evaluation (shows card injection)

**Type:** `Is Force of Will still a 4-of staple in Dimir Tempo?`

**While it generates, say:**
> "Watch the left panel — as the response comes back, the server post-processes it to find card names, resolves them to Scryfall data, and renders them as clickable cards. The `[[Name]]` brackets you see in the text are real anchor tags — clicking opens Scryfall in a new tab."

**After response:**
- Point to the green RAG badge ("grounded in N sources")
- Click a `[[Force of Will]]` ref — shows it opens Scryfall
- Mention: "The oracle text the model references is coming from the card-lookup injection, not the model's weights. That's why the mana cost and effect are correct."

### Prompt 2 — Partial-name + ban query (shows fuzzy matching)

**Type:** `Is mox pearl legal?` (lowercase on purpose)

**Point out:**
- The extractor is case-insensitive
- It resolves banned cards too (Mox Pearl is on the Legacy ban list but still in the card pool)
- Response should correctly state it's banned — if it does, that's card injection working

### Prompt 3 — Meta / strategy question (shows RAG)

**Type:** `What's the best matchup against Reanimator?`

**Point out:**
- No specific card named → card injection returns nothing → RAG does the heavy lifting
- The RAG badge shows the sources came from `legacy-deck-history` / `archetype-guide` chunks, not cards
- This is the strategy/rules path — RAG context + LoRA-tuned reasoning

---

## Demo 2 — Import & Analyze tab (≈2 min)

**Switch to the Import tab. Say:**
> "This tab shows a second workflow — structured parsing of real-world decklists into LLM-ready context."

**Paste a Moxfield URL** (have one ready, e.g. a public Dimir Tempo list): `https://www.moxfield.com/decks/[...]`

**While it parses:**
> "The parser handles three input formats — plain text one-per-line, Moxfield's API, and MTGGoldfish's scraper — all normalizing to the same schema. Then the LLM runs archetype classification and a strengths-weaknesses breakdown on the parsed data, not free-form text."

**Show:**
- The card grid with counts
- The mana curve chart
- Click "Analyze" → the LLM output classifying the archetype

---

## Under the hood (≈1.5 min)

Flip to the GitHub tab, scroll through `README.md`.

**Highlight, in order:**
1. **Training Results table** — "This is the honest eval: +58 points on card evaluation, +67 on deck analysis, +33 on rules knowledge. Board state and budget subs didn't budge — that's documented in `notes/development/round1-analysis.md`."
2. **Inference pipeline section** — "Six-step walkthrough of every `/chat` request. The card injection design is the interesting part; it's what lets a 1B model avoid inventing card stats."
3. **Sampling section** — "Temperature 0.1 globally with per-endpoint overrides. Rubric asked for an appropriate sampling method with rationale — it's all in the table."
4. **Project structure** — briefly scroll through `src/`, `data/training/` (13 jsonl files), `tests/` ("219 tests, 86% coverage"), point out Goldfish and Budget modules: *"Two more workflows are shipped but hidden from the live UI — a goldfish simulator with combo detection and a budget-substitution engine. Docs are in the README, code is in `src/goldfish_engine.py` and `src/budget_engine.py`, reachable via the API today."*

---

## Known shortcomings (≈2.5 min)

**Graders reward self-awareness more than hidden flaws.** This is where Innovation points and "understands current state of the field" (rubric line) are actually earned. Walk through each one deliberately — each shortcoming is also a lens on a design decision.

### 1. 1B base model is the core constraint

**Say:**
> "Llama 3.2 1B is the smallest model in the family. Even with LoRA, RAG, and ground-truth card injection, it still occasionally invents tier placements and meta percentages for decks that RAG doesn't have a dedicated chunk for. You'll see this if you ask about a mid-Tier-3 deck — the model will confidently state a meta share that isn't in any source. The infrastructure catches the worst hallucinations (invented card stats, wrong oracle text) but it can't backstop everything the model thinks it knows."

**Show (if time):** Footer says "Llama 3.2 1B · 1.2 GiB Q8_0 GGUF" — the whole model fits in RAM on a laptop. That's the trade-off.

### 2. Generic embeddings don't understand MTG

**Say:**
> "The RAG retriever uses `all-MiniLM-L6-v2` — a 22M-parameter sentence embedding trained on generic web text. It has no idea that 'Akroma' and 'Akroma, Angel of Wrath' are the same concept, or that 'Brainstorm' is closer to 'Ponder' than to 'brainstorming sessions.' When I checked retrieval quality early on, queries about specific cards were pulling semantically-adjacent English words, not the cards themselves. That's the reason I built the deterministic card-injection layer in front of RAG — it completely bypasses the embedding for any card the user names explicitly."

**Point at:** README's "Inference pipeline" step 1 — the case-insensitive word-boundary + token-level fuzzy extraction. "This is the most interesting engineering in the project. It's what lets a small model give correct card stats despite a bad embedding."

### 3. LoRA improvements were uneven

**Say:**
> "The eval gains aren't flat. Card evaluation went +58 points, deck analysis +67, rules knowledge +33. But **board state and budget substitutions barely moved.** Board state was 42% baseline and 42% finetuned — no change. Budget subs 10% → 20%, which is still bad."

**Why:** small training sets in those categories (146 + 129 pairs), and both require reasoning over multiple cards/prices simultaneously, which is exactly where small models struggle. **The deterministic budget engine exists specifically to route around this** — `/budget-sub/lookup` and `/budget-tiers` are pure Python, no LLM calls. The LLM only adds narration on top.

### 4. The eval set is small

**Say:**
> "22 test cases across 9 categories is enough to show a trend but not enough to draw strong conclusions. A real evaluation would be 200+ cases, ideally with inter-annotator agreement. I scored each response on a -1/0/+1 scale manually — repeatable but subjective."

**Point at:** `notebooks/eval_report.json` — raw data is transparent, at least.

### 5. CPU inference is slow

**Say:**
> "We're on Fly's `performance-8x` (16 GB, 8 vCPU), no GPU. First-token latency is 3-5 seconds, full responses are 15-40 seconds depending on length. For a demo this is fine; for interactive production it isn't. The original plan was a SageMaker A10G endpoint — that code path still works, set `INFERENCE_BACKEND=sagemaker` — but the cost/complexity wasn't worth it at 1B size."

### 6. Context window juggling is fragile

**Say:**
> "Early in the demo rehearsal I saw Ollama logs warning `truncating input prompt limit=2048 prompt=9038 keep=5` — meaning 78% of the injected context was being dropped mid-request. The model fell back to raw-weight guessing because the ground-truth cards never reached it. I bumped `num_ctx` to 8192 and it's fine now, but the moral is: silent truncation is devastating when your anti-hallucination strategy depends on context fitting."

### 7. No human preference eval, no multi-turn eval

**Say (brief):**
> "The 22-case eval is single-turn. Multi-turn deck-building conversations — where the model has to stay consistent across 5+ turns — aren't tested. Neither is preference-style comparison against, say, GPT-4o on the same queries. Both would be the next rigor step."

---

## Where I'd take this next (≈1.5 min)

**Frame:** "If I had another cycle, here's the priority stack."

### Near-term (weeks)

1. **Bigger base model.** Llama 3.1 8B or Mistral 7B Instruct. Everything in the pipeline — LoRA training pairs, RAG chunks, card injection — transfers without changes. The infrastructure was designed so the model is swappable. I'd expect the "didn't budge" categories (board state, budget subs) to finally move.

2. **Domain-tuned embeddings.** Either finetune `all-MiniLM-L6-v2` on MTG card-to-card similarity pairs, or swap to a larger embedding (e.g. `bge-large-en`). Current RAG is dominated by surface keyword overlap; a domain embedding would let "Brainstorm-style cantrip" queries actually retrieve Ponder, Preordain, and Serum Visions instead of random cards with "stream" in the name.

3. **Reranker on top-10 retrieval.** Small cross-encoder re-scoring the top-10 RAG hits before context assembly. Closes a lot of the gap without a bigger embedding.

4. **Streaming card resolution in the UI.** Right now cards appear after the full response arrives. With SSE already wired, the frontend could render `[[Name]]` anchors as they stream.

### Medium-term (months)

5. **DPO or preference finetuning.** Current LoRA is pure SFT. A second pass with preference pairs — "this response is better than that response" — would likely tighten up the "confidently makes up meta percentages" failure mode more than adding SFT data.

6. **Tool use, not just RAG.** Let the model call Scryfall's search API directly for cards it's uncertain about, instead of hoping the injection layer caught them. Would also let it query live pricing (EDHRec, MTGGoldfish) instead of relying on static Scryfall prices.

7. **Automated regression eval in CI.** Every merge runs the 22-case eval against the finetuned model and posts the delta. Keeps training-data changes from silently regressing categories. Blocked on eval set size — need at least 100 cases to be meaningful.

### Longer-term / research-ish

8. **Multi-format generalization.** The same architecture should work for Modern, Pioneer, Pauper — just swap the card-pool filter and the strategy docs. Would be a strong test of whether the approach is actually about MTG or just about Legacy.

9. **Human eval with actual Legacy players.** Compare The Legacy against GPT-4o and Claude on real deckbuilding consultations. Blind scoring by a panel of ranked Legacy players. Expensive to run but the only "real" evaluation of whether this is useful.

10. **Open-source the training pipeline.** The 1,549-pair dataset, the LoRA recipe, the eval set — all in the repo already. A cleaner write-up of "how to build a domain-specific small model" would be useful to people doing similar projects.

---

---

## Likely Q&A — have an answer ready

Most of the deeper questions are now covered in Shortcomings + Where-I'd-take-this-next. These are the quick ones that might come in cold.

- **"Why 1B instead of a bigger model?"** → Demo cost + the constraint was instructive. Card injection is the technique that makes small models viable for domain-specific factual tasks. (Point to shortcoming #1.)
- **"How did you evaluate?"** → 22-case eval dataset across 9 categories, manual -1/0/+1 scoring. `notebooks/eval_report.json` has the raw numbers. Small — acknowledged in shortcoming #4.
- **"Why Fly instead of SageMaker?"** → SageMaker was the original plan (notebook + deploy script still in the repo under `INFERENCE_BACKEND=sagemaker`), but Fly's all-in-one path is simpler — one container, one URL, no AWS credentials. CPU is slower (shortcoming #5) but acceptable at demo scale.
- **"How does the card injection scale?"** → Linear in card-pool size (~30k regex passes per query, ~30ms). Token-level fuzzy match uses rapidfuzz, which is C-accelerated. If this grew past Legacy's 30k cards, I'd swap to a trie or Aho-Corasick.
- **"Isn't 61.6% still pretty low?"** → Yes. On a 22-case eval, +32.7 points is a directional signal, not a production metric. The deployed pipeline is better than that number suggests because RAG and card injection aren't counted in the raw eval — those are infra layers on top of the raw finetune.
- **"Why not just use GPT-4?"** → Cost + the assignment was about building the stack, not about picking the biggest API. Would it be better at answering MTG questions today? Probably. Would it cost $10s per demo session instead of $0.50? Also probably.
- **"What's the most interesting thing you learned?"** → That infrastructure (card injection, RAG filtering, version markers, context-budget sanity checks) compensates for model weakness more than I expected. At 1B size, the model is almost a rendering layer — the real intelligence is in the pipeline around it.

---

## If things go wrong

- **Fly machine stopped** — `fly machines start -a the-legacy-api`, wait 30s, refresh
- **Model not responding** — refresh once. If still broken, fall back to `curl https://the-legacy-api.fly.dev/chat -d '{"message": "..."}'` in terminal
- **Wrong answer in chat** — acknowledge it: *"That's the 1B model showing through — this is exactly the case where card injection is supposed to catch it, and for whatever reason it didn't fire. Happens maybe 1 in 10 on meta questions."*
- **Zero cards in left panel** — means extraction didn't find anything. Prompt with a more explicit card name and move on

---

## What NOT to do

- Don't demo Goldfish live — it's hidden for a reason (seconds-long sims, text-heavy output)
- Don't promise 61.6% on free-form queries — that number is on the 22-case eval set, not a live benchmark
- Don't open a tab with uncommitted work — stick to what's deployed
- Don't start a chat with "Hello" during the live demo — you already warmed the model in pre-demo
