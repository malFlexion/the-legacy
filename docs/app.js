// The Legacy — static frontend.
//
// Talks to the FastAPI backend at window.API_BASE (set in config.js).
// No build step, no framework — plain DOM manipulation + fetch.

"use strict";

// window.API_BASE is set in config.js. Empty string = same origin.
// Use `??` not `||` so an empty string isn't treated as "unset".
const API = window.API_BASE ?? "http://localhost:8000";

// ---------- Tab navigation ----------

document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        const tab = btn.dataset.tab;
        document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById(`tab-${tab}`).classList.add("active");
    });
});

// ---------- Utility helpers ----------

function el(tag, props = {}, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) {
        if (k === "class") node.className = v;
        else if (k === "html") node.innerHTML = v;
        else if (k.startsWith("on")) node.addEventListener(k.slice(2).toLowerCase(), v);
        else node.setAttribute(k, v);
    }
    for (const child of children) {
        if (child == null) continue;
        node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
    }
    return node;
}

function renderError(parent, message) {
    parent.innerHTML = "";
    parent.appendChild(el("div", { class: "error" }, message));
}

async function api(path, options = {}) {
    const res = await fetch(`${API}${path}`, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });
    if (!res.ok) {
        let detail = res.statusText;
        try {
            const body = await res.json();
            if (body.detail) detail = body.detail;
        } catch (_) {}
        throw new Error(`${res.status}: ${detail}`);
    }
    return res.json();
}

// ---------- Parse a decklist textarea into {name: count} ----------

function parseDecklist(text) {
    const lines = text
        .split("\n")
        .map((l) => l.trim())
        .filter((l) => l && !l.startsWith("//") && !l.startsWith("#"));
    const result = {};
    for (const line of lines) {
        // Accept "4 Brainstorm", "4x Brainstorm", "Brainstorm x4"
        let m = line.match(/^(\d+)\s*x?\s+(.+)$/i);
        if (!m) m = line.match(/^(.+?)\s*x\s*(\d+)$/i);
        if (!m) continue;
        const [count, name] = m[1].match(/^\d+$/) ? [parseInt(m[1]), m[2]] : [parseInt(m[2]), m[1]];
        const key = name.replace(/\s+/g, " ").trim();
        result[key] = (result[key] || 0) + count;
    }
    return result;
}

// ---------- Card thumb rendering ----------

function cardThumb(card, count = null) {
    const name = card.name;
    const displayName = cardDisplayName(card);
    const legal = card.legacy_legal !== false;
    const href = card.scryfall_uri || `https://scryfall.com/search?q=${encodeURIComponent(name)}`;
    // Scryfall's `named?format=image` endpoint serves card images for any
    // valid name, including MDFCs and split cards (returns the front face).
    // Use the front-face name so the query matches what Scryfall indexes.
    const scryfallImg = `https://api.scryfall.com/cards/named?format=image&version=normal&exact=${encodeURIComponent(displayName)}`;
    const imgUrl = card.image_url || scryfallImg;

    const thumb = el("a", {
        class: `card-thumb ${legal ? "" : "illegal"}`,
        href,
        target: "_blank",
        title: legal ? displayName : `${displayName} (not Legacy-legal)`,
    });

    thumb.appendChild(el("img", { src: imgUrl, alt: displayName, loading: "lazy" }));

    if (count != null && count > 1) {
        thumb.appendChild(el("div", { class: "card-count" }, `${count}×`));
    }

    return thumb;
}

// ---------- API health check ----------

async function checkHealth() {
    const pill = document.querySelector(".api-status");
    const healthSpan = document.getElementById("api-health");

    function setState(state) {
        pill.classList.remove("ok", "fail", "warn");
        pill.classList.add(state);
    }

    try {
        const h = await api("/health");
        const llm = h.llm || {};
        const parts = [];

        if (llm.reachable) {
            parts.push(`LLM ${llm.detail}`);
            setState("ok");
            healthSpan.className = "health-ok";
        } else {
            parts.push(`LLM ${llm.detail || "unreachable"}`);
            setState("fail");
            healthSpan.className = "health-fail";
        }

        // Explicit RAG status so users know whether responses are grounded in
        // the rules/meta corpus or coming purely from the model's weights.
        if (h.vector_db) {
            parts.push(`RAG ${h.vector_chunks}`);
        } else {
            parts.push(`RAG off`);
        }

        healthSpan.textContent = parts.join(" · ");

        // Footer deploy timestamp — shows when this container booted.
        const bootSpan = document.getElementById("footer-boot-time");
        if (bootSpan) {
            if (h.boot_time && h.boot_time !== "unknown") {
                const dt = new Date(h.boot_time);
                // Compact local-time formatting: "Apr 20, 22:17 UTC"
                bootSpan.textContent = `deployed ${dt.toUTCString().replace(" GMT", " UTC")}`;
                bootSpan.title = `Container boot time: ${h.boot_time}`;
            } else {
                bootSpan.textContent = "deploy time unknown";
            }
        }
    } catch (err) {
        setState("fail");
        healthSpan.textContent = err.message;
        healthSpan.className = "health-fail";
    }
}

// ---------- Chat tab ----------

const chatState = { messages: [] };

// Enter submits; Shift+Enter inserts a newline.
document.getElementById("chat-input").addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" && !ev.shiftKey) {
        ev.preventDefault();
        document.getElementById("chat-form").requestSubmit();
    }
});

document.getElementById("chat-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const input = document.getElementById("chat-input");
    const submit = document.getElementById("chat-submit");
    const content = input.value.trim();
    if (!content) return;

    chatState.messages.push({ role: "user", content });
    input.value = "";
    submit.disabled = true;
    submit.textContent = "Thinking…";
    renderChat();

    try {
        const res = await api("/chat", {
            method: "POST",
            body: JSON.stringify({
                messages: chatState.messages,
                stream: false,
                temperature: 0.3,
                max_tokens: 768,
            }),
        });
        chatState.messages.push({
            role: "assistant",
            content: res.content,
            cards: res.cards || [],
            ragChunks: res.rag_chunks || 0,
            ragSources: res.rag_sources || [],
        });
    } catch (err) {
        chatState.messages.push({
            role: "assistant",
            content: `Error: ${err.message}`,
            cards: [],
        });
    } finally {
        submit.disabled = false;
        submit.textContent = "Send";
        renderChat();
    }
});

function renderChat() {
    const container = document.getElementById("chat-messages");
    container.innerHTML = "";
    if (chatState.messages.length === 0) {
        container.appendChild(el("p", { class: "placeholder" }, "Start a conversation — ask about decks, cards, rules, or the meta."));
        return;
    }
    // Accumulate unique cards across the entire conversation; we render
    // them once in the side panel rather than inline per-message.
    const cardsByName = new Map();

    for (const msg of chatState.messages) {
        const block = el("div", { class: "chat-message" });
        block.appendChild(el("div", { class: `chat-role ${msg.role}` }, msg.role));

        // Render the message content with [[Card Name]] tokens converted to
        // inline styled refs. Tokens that don't resolve to a real card fall
        // through as plain text (with brackets stripped).
        const contentEl = el("div", { class: "chat-content" });
        renderContentWithCardRefs(contentEl, msg.content, msg.cards || []);
        block.appendChild(contentEl);

        // Collect cards from this message into the conversation-wide map
        if (msg.cards) {
            for (const card of msg.cards) {
                if (!cardsByName.has(card.name)) cardsByName.set(card.name, card);
            }
        }

        // Show RAG grounding status on assistant messages — helps distinguish
        // "answer came from the rules/meta corpus" (trustworthy) from
        // "answer came purely from the model's weights" (may hallucinate).
        if (msg.role === "assistant") {
            if (msg.ragChunks > 0) {
                const sourceList = msg.ragSources && msg.ragSources.length
                    ? ": " + msg.ragSources.slice(0, 3).join(" · ")
                    : "";
                block.appendChild(el(
                    "div",
                    { class: "rag-badge rag-on" },
                    `grounded in ${msg.ragChunks} source${msg.ragChunks === 1 ? "" : "s"}${sourceList}`
                ));
            } else if (msg.ragChunks === 0 && msg.ragSources !== undefined) {
                block.appendChild(el(
                    "div",
                    { class: "rag-badge rag-off" },
                    "no RAG grounding — response came from model weights only"
                ));
            }
        }

        container.appendChild(block);
    }
    container.scrollTop = container.scrollHeight;

    // Populate the side panel with all unique cards from the conversation
    renderChatCardsPanel(Array.from(cardsByName.values()));
}

// Split the message content by [[Card Name]] tokens and append mixed text
// + card-ref spans to the parent element. Keeps newlines visible because
// the parent has white-space: pre-wrap in CSS.
function renderContentWithCardRefs(parent, content, cards) {
    // Build a lookup of bracketed-name → card so the span can carry a
    // tooltip showing the mana cost + type line.
    const cardByName = new Map();
    for (const c of cards) cardByName.set(c.name.toLowerCase(), c);

    const re = /\[\[([^\[\]]+?)\]\]/g;
    let lastIdx = 0;
    let match;
    while ((match = re.exec(content)) !== null) {
        if (match.index > lastIdx) {
            parent.appendChild(document.createTextNode(content.slice(lastIdx, match.index)));
        }
        const rawName = match[1].trim();
        const resolved = cardByName.get(rawName.toLowerCase());
        const href = (resolved && resolved.scryfall_uri)
            || `https://scryfall.com/search?q=${encodeURIComponent(resolved ? resolved.name : rawName)}`;
        const anchor = el("a", {
            class: "card-ref",
            href,
            target: "_blank",
            rel: "noopener",
            title: resolved
                ? `${resolved.name} — ${resolved.mana_cost || ""} ${resolved.type_line || ""}`.trim()
                : rawName,
        }, rawName);
        parent.appendChild(anchor);
        lastIdx = match.index + match[0].length;
    }
    if (lastIdx < content.length) {
        parent.appendChild(document.createTextNode(content.slice(lastIdx)));
    }
}

function renderChatCardsPanel(cards) {
    const grid = document.getElementById("chat-cards-grid");
    if (!grid) return;
    grid.innerHTML = "";
    if (cards.length === 0) {
        grid.appendChild(el("p", { class: "chat-cards-empty" },
            "Cards referenced in the conversation will appear here."));
        return;
    }
    for (const card of cards) {
        grid.appendChild(cardThumb(card));
    }
}

// ---------- Deck import & analyze ----------

let parsedImportDeck = null;

document.getElementById("import-parse-btn").addEventListener("click", async () => {
    const input = document.getElementById("import-input").value.trim();
    const output = document.getElementById("import-output");
    const analyzeBtn = document.getElementById("import-analyze-btn");

    if (!input) {
        renderError(output, "Paste a decklist or URL first.");
        return;
    }

    output.innerHTML = "";
    output.appendChild(el("p", { class: "placeholder" }, "Parsing…"));

    try {
        let body;
        if (input.startsWith("http://") || input.startsWith("https://")) {
            body = { url: input };
        } else {
            body = { text: input };
        }
        const result = await api("/import-deck", {
            method: "POST",
            body: JSON.stringify(body),
        });
        parsedImportDeck = result;
        renderImportedDeck(result);
        analyzeBtn.disabled = false;
        copyToGoldfishAndBudget(result);
    } catch (err) {
        renderError(output, err.message);
    }
});

function copyToGoldfishAndBudget(deck) {
    const qty = (e) => e.quantity ?? e.count ?? 0;
    const main = deck.main || [];
    const side = deck.sideboard || deck.side || [];
    const text = [
        ...main.map((e) => `${qty(e)} ${e.name}`),
        ...(side.length > 0 ? ["", "Sideboard:"] : []),
        ...side.map((e) => `${qty(e)} ${e.name}`),
    ].join("\n");
    const goldfishInput = document.getElementById("goldfish-input");
    const budgetInput = document.getElementById("budget-input");
    if (goldfishInput) goldfishInput.value = text;
    if (budgetInput) budgetInput.value = text;
}

// Classify a card's type_line into a high-level grouping for the render.
// Order here is the display order — creatures first since they're usually
// the bulk of a deck, lands last.
const TYPE_GROUPS = ["Creature", "Planeswalker", "Instant", "Sorcery", "Artifact", "Enchantment", "Land"];
// Correct English plural for headings; naive "${group}s" would emit "Sorcerys".
const TYPE_GROUP_PLURAL = {
    Creature: "Creatures",
    Planeswalker: "Planeswalkers",
    Instant: "Instants",
    Sorcery: "Sorceries",
    Artifact: "Artifacts",
    Enchantment: "Enchantments",
    Land: "Lands",
    Other: "Other",
};
function cardTypeGroup(card) {
    const t = card?.type_line || "";
    for (const group of TYPE_GROUPS) {
        if (t.includes(group)) return group;
    }
    return "Other";
}

// MDFCs and split cards come through the card_index as
// "Front Face // Back Face". The grid reads cleaner if we show only the
// front face — same card, less visual noise.
function cardDisplayName(card) {
    const raw = (card && card.name) || "";
    return raw.split(" // ")[0] || raw;
}

function renderImportedDeck(deck) {
    const output = document.getElementById("import-output");
    output.innerHTML = "";

    const main = deck.main || [];
    // Server returns `sideboard`; keep `side` as a fallback for any older
    // payload shape.
    const side = deck.sideboard || deck.side || [];

    // Summary stats — server field is `quantity`; tolerate `count` for
    // backward compat with older payloads.
    const qty = (e) => e.quantity ?? e.count ?? 0;

    const stats = el("div", { class: "stats-grid" });
    stats.appendChild(statCard("Main deck", main.reduce((s, e) => s + qty(e), 0)));
    stats.appendChild(statCard("Sideboard", side.reduce((s, e) => s + qty(e), 0)));
    output.appendChild(stats);

    // Mana curve — exclude lands
    const curve = {};
    for (const entry of main) {
        const card = entry.card;
        if (card && !card.type_line?.includes("Land")) {
            const cmc = Math.floor(card.cmc || 0);
            curve[cmc] = (curve[cmc] || 0) + qty(entry);
        }
    }
    if (Object.keys(curve).length > 0) {
        output.appendChild(el("h3", { style: "margin-top: 20px;" }, "Mana curve"));
        const maxCount = Math.max(...Object.values(curve));
        const curveEl = el("div", { class: "mana-curve" });
        for (const cmc of Object.keys(curve).sort((a, b) => a - b)) {
            curveEl.appendChild(el("div", { class: "curve-label" }, `${cmc} mana`));
            const bar = el("div", {
                class: "curve-bar",
                style: `width: ${(curve[cmc] / maxCount) * 100}%`,
            }, `${curve[cmc]}`);
            curveEl.appendChild(bar);
        }
        output.appendChild(curveEl);
    }

    // Card grid, grouped by type
    output.appendChild(el("h3", { style: "margin-top: 20px;" }, "Main deck"));
    renderGroupedCardGrid(output, main, qty);

    if (side.length > 0) {
        output.appendChild(el("h3", { style: "margin-top: 20px;" }, "Sideboard"));
        renderGroupedCardGrid(output, side, qty);
    }
}

function renderGroupedCardGrid(parent, entries, qty) {
    // Bucket entries by display group
    const groups = new Map();
    for (const entry of entries) {
        const card = entry.card || { name: entry.name };
        const group = cardTypeGroup(card);
        if (!groups.has(group)) groups.set(group, []);
        groups.get(group).push(entry);
    }
    // Render in TYPE_GROUPS order, then "Other" last
    const orderedGroups = [...TYPE_GROUPS, "Other"].filter((g) => groups.has(g));
    for (const group of orderedGroups) {
        const groupEntries = groups.get(group);
        const groupCount = groupEntries.reduce((s, e) => s + qty(e), 0);
        const label = TYPE_GROUP_PLURAL[group] || `${group}s`;
        const heading = el("h4", { class: "type-group-heading" }, `${label} (${groupCount})`);
        parent.appendChild(heading);
        const grid = el("div", { class: "card-grid" });
        for (const entry of groupEntries) {
            const card = entry.card || { name: entry.name };
            grid.appendChild(cardThumb(card, qty(entry)));
        }
        parent.appendChild(grid);
    }
}

function statCard(label, value) {
    return el(
        "div",
        { class: "stat-card" },
        el("div", { class: "stat-label" }, label),
        el("div", { class: "stat-value" }, `${value}`)
    );
}

document.getElementById("import-analyze-btn").addEventListener("click", async () => {
    const analysisContainer = document.getElementById("import-analysis");
    if (!parsedImportDeck) return;

    // Render into the full-width container below the input/parse split so
    // the LLM's prose isn't squeezed into a narrow right-hand column.
    analysisContainer.innerHTML = "";
    const analysis = el("div");
    analysis.appendChild(el("h3", {}, "AI analysis"));
    analysis.appendChild(el("p", { class: "placeholder" }, "Asking the model…"));
    analysisContainer.appendChild(analysis);

    try {
        const qty = (e) => e.quantity ?? e.count ?? 0;
        const main = parsedImportDeck.main || [];
        const side = parsedImportDeck.sideboard || parsedImportDeck.side || [];
        const mainList = main.map((e) => `${qty(e)} ${e.name}`).join("\n");
        const sideList = side.map((e) => `${qty(e)} ${e.name}`).join("\n");
        const decklist = sideList
            ? `Main deck:\n${mainList}\n\nSideboard:\n${sideList}`
            : `Main deck:\n${mainList}`;
        const res = await api("/analyze-deck", {
            method: "POST",
            body: JSON.stringify({
                messages: [{ role: "user", content: `Analyze this Legacy deck:\n\n${decklist}` }],
                temperature: 0.2,
                max_tokens: 512,
            }),
        });
        analysis.innerHTML = "";
        analysis.appendChild(el("h3", {}, "AI analysis"));
        analysis.appendChild(el("div", { class: "chat-content" }, res.content));
    } catch (err) {
        analysis.innerHTML = "";
        analysis.appendChild(el("h3", {}, "AI analysis"));
        analysis.appendChild(el("div", { class: "error" }, err.message));
    }
});

// ---------- Goldfish tab ----------

let goldfishHandSeed = null;
let goldfishKeepCount = 7;

document.getElementById("goldfish-draw-btn").addEventListener("click", async () => {
    const text = document.getElementById("goldfish-input").value.trim();
    const output = document.getElementById("goldfish-output");
    const status = document.getElementById("goldfish-status");
    const mullBtn = document.getElementById("goldfish-mull-btn");

    const decklist = parseDecklist(text);
    if (Object.keys(decklist).length === 0) {
        renderError(output, "Paste a decklist first.");
        return;
    }

    goldfishHandSeed = Math.floor(Math.random() * 1e9);
    goldfishKeepCount = 7;
    mullBtn.disabled = false;
    status.textContent = `Hand seed ${goldfishHandSeed}, keep ${goldfishKeepCount}`;

    await drawGoldfishHand(decklist, goldfishHandSeed, goldfishKeepCount);
});

document.getElementById("goldfish-mull-btn").addEventListener("click", async () => {
    const text = document.getElementById("goldfish-input").value.trim();
    const status = document.getElementById("goldfish-status");
    const mullBtn = document.getElementById("goldfish-mull-btn");

    goldfishKeepCount -= 1;
    if (goldfishKeepCount <= 0) {
        mullBtn.disabled = true;
        status.textContent = "Cannot mulligan below 1 card.";
        return;
    }
    const decklist = parseDecklist(text);
    goldfishHandSeed = Math.floor(Math.random() * 1e9);
    status.textContent = `Hand seed ${goldfishHandSeed}, keep ${goldfishKeepCount} (London mulligan)`;
    await drawGoldfishHand(decklist, goldfishHandSeed, goldfishKeepCount);
});

async function drawGoldfishHand(decklist, seed, keepCount) {
    const output = document.getElementById("goldfish-output");
    output.innerHTML = "";
    output.appendChild(el("p", { class: "placeholder" }, "Drawing…"));

    try {
        const hand = await api("/goldfish/draw", {
            method: "POST",
            body: JSON.stringify({ decklist, keep_count: keepCount, seed }),
        });
        output.innerHTML = "";

        const stats = el("div", { class: "stats-grid" });
        stats.appendChild(statCard("Lands", hand.land_count));
        stats.appendChild(statCard("Spells", hand.spell_count));
        stats.appendChild(statCard("Hand size", hand.cards.length));
        output.appendChild(stats);

        output.appendChild(el("h3", { style: "margin-top: 20px;" }, `Opening hand (${hand.cards.length} cards)`));
        const grid = el("div", { class: "card-grid" });
        for (const card of hand.cards) {
            grid.appendChild(cardThumb(card));
        }
        output.appendChild(grid);

        if (hand.colors_by_turn) {
            output.appendChild(el("h3", { style: "margin-top: 20px;" }, "Colors available by turn"));
            const tbl = el("div", { class: "turn-log" });
            for (const [turn, colors] of Object.entries(hand.colors_by_turn)) {
                const row = el("div", { class: "turn-log-row" });
                row.appendChild(el("span", { class: "turn-log-turn" }, `Turn ${turn}`));
                row.appendChild(document.createTextNode(colors.length ? colors.join(" ") : "— (no colored mana)"));
                tbl.appendChild(row);
            }
            output.appendChild(tbl);
        }
    } catch (err) {
        renderError(output, err.message);
    }
}

document.getElementById("goldfish-sim-btn").addEventListener("click", async () => {
    const text = document.getElementById("goldfish-input").value.trim();
    const output = document.getElementById("goldfish-output");
    const decklist = parseDecklist(text);
    if (Object.keys(decklist).length === 0) {
        renderError(output, "Paste a decklist first.");
        return;
    }

    output.innerHTML = "";
    output.appendChild(el("p", { class: "placeholder" }, "Simulating…"));

    try {
        const game = await api("/goldfish/simulate", {
            method: "POST",
            body: JSON.stringify({ decklist, turns: 6, seed: Math.floor(Math.random() * 1e9) }),
        });
        output.innerHTML = "";
        output.appendChild(el("h3", {}, `Goldfish game (${game.turns_played} turns, ${game.life_final} life)`));
        const log = el("div", { class: "turn-log" });
        for (const t of game.turns) {
            const row = el("div", { class: "turn-log-row" });
            row.appendChild(el("span", { class: "turn-log-turn" }, `T${t.turn}`));
            const parts = [];
            if (t.land_played) parts.push(`land: ${t.land_played}`);
            if (t.spells_cast && t.spells_cast.length) parts.push(`cast: ${t.spells_cast.join(", ")}`);
            if (parts.length === 0) parts.push("(no plays)");
            row.appendChild(document.createTextNode(" " + parts.join("  ·  ")));
            row.appendChild(el("span", { class: "turn-log-mana" }, `mana ${t.mana_used}/${t.mana_available}`));
            if (t.combos && t.combos.length > 0) {
                row.appendChild(el("div", { class: "turn-log-combo" }, `⚡ Combo assembled: ${t.combos.join(", ")}`));
            }
            log.appendChild(row);
        }
        output.appendChild(log);

        if (Object.keys(game.assembled_combos || {}).length > 0) {
            output.appendChild(el("h3", { style: "margin-top: 20px;" }, "Combos this game"));
            for (const [name, turn] of Object.entries(game.assembled_combos)) {
                output.appendChild(el("p", {}, `${name}: assembled on turn ${turn}`));
            }
        }
    } catch (err) {
        renderError(output, err.message);
    }
});

document.getElementById("goldfish-stats-btn").addEventListener("click", async () => {
    const text = document.getElementById("goldfish-input").value.trim();
    const output = document.getElementById("goldfish-output");
    const decklist = parseDecklist(text);
    if (Object.keys(decklist).length === 0) {
        renderError(output, "Paste a decklist first.");
        return;
    }

    output.innerHTML = "";
    output.appendChild(el("p", { class: "placeholder" }, "Running 1000 games… (takes a few seconds)"));

    try {
        const stats = await api("/goldfish/simulate-many", {
            method: "POST",
            body: JSON.stringify({ decklist, n_games: 1000, turns: 6 }),
        });
        output.innerHTML = "";
        output.appendChild(el("h3", {}, `Aggregate over ${stats.n_games} games`));

        const grid = el("div", { class: "stats-grid" });
        grid.appendChild(statCard("Avg mana efficiency", `${(stats.avg_mana_efficiency * 100).toFixed(1)}%`));
        grid.appendChild(statCard("Avg final life", stats.avg_life_final.toFixed(1)));
        output.appendChild(grid);

        const combos = Object.entries(stats.combo_assembly || {});
        if (combos.length > 0) {
            output.appendChild(el("h3", { style: "margin-top: 20px;" }, "Combo assembly"));
            for (const [name, info] of combos) {
                output.appendChild(el(
                    "p",
                    {},
                    `${name}: ${(info.rate * 100).toFixed(1)}% of games, avg turn ${info.avg_turn.toFixed(1)}`
                ));
            }
        }

        output.appendChild(el("h3", { style: "margin-top: 20px;" }, "Top cards cast"));
        const ranked = Object.entries(stats.cast_rate)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 15);
        const castTable = el("div", { class: "turn-log" });
        for (const [card, rate] of ranked) {
            const row = el("div", { class: "turn-log-row" });
            row.appendChild(el("span", { class: "turn-log-turn" }, `${(rate * 100).toFixed(0)}%`));
            row.appendChild(document.createTextNode(` ${card}`));
            const avgTurn = stats.avg_turn_first_cast[card];
            if (avgTurn != null) {
                row.appendChild(el("span", { class: "turn-log-mana" }, `avg T${avgTurn.toFixed(1)}`));
            }
            castTable.appendChild(row);
        }
        output.appendChild(castTable);
    } catch (err) {
        renderError(output, err.message);
    }
});

// ---------- Budget tab ----------

document.getElementById("budget-tiers-btn").addEventListener("click", async () => {
    const text = document.getElementById("budget-input").value.trim();
    const output = document.getElementById("budget-output");
    const decklist = parseDecklist(text);
    if (Object.keys(decklist).length === 0) {
        renderError(output, "Paste a decklist first.");
        return;
    }

    output.innerHTML = "";
    output.appendChild(el("p", { class: "placeholder" }, "Computing tiers…"));

    try {
        const tiers = await api("/budget-tiers", {
            method: "POST",
            body: JSON.stringify({ decklist }),
        });
        output.innerHTML = "";
        output.appendChild(el("h3", {}, "Full vs. Mid vs. Budget"));
        const grid = el("div", { class: "tiers-grid" });
        for (const [name, tier] of Object.entries({ full: tiers.full, mid: tiers.mid, budget: tiers.budget })) {
            const card = el("div", { class: "tier-card" });
            card.appendChild(el("div", { class: "tier-name" }, name.toUpperCase()));
            card.appendChild(el("div", { class: "tier-price" }, `$${tier.estimated_price_usd.toLocaleString()}`));

            if (tier.substitutions_applied && tier.substitutions_applied.length > 0) {
                const subs = el("div", { class: "tier-subs" });
                subs.appendChild(el("strong", {}, "Substitutions:"));
                const ul = el("ul");
                for (const [orig, repl] of tier.substitutions_applied) {
                    ul.appendChild(el("li", {}, `${orig} → ${repl}`));
                }
                subs.appendChild(ul);
                card.appendChild(subs);
            }

            if (tier.irreplaceable && tier.irreplaceable.length > 0) {
                const irr = el("div", { class: "tier-irreplaceable" });
                irr.appendChild(el("strong", {}, "Irreplaceable: "));
                irr.appendChild(document.createTextNode(tier.irreplaceable.join(", ")));
                card.appendChild(irr);
            }

            grid.appendChild(card);
        }
        output.appendChild(grid);

        output.appendChild(el(
            "p",
            { class: "hint", style: "margin-top: 20px;" },
            `Full → Budget savings: $${(tiers.full.estimated_price_usd - tiers.budget.estimated_price_usd).toLocaleString()}`
        ));
    } catch (err) {
        renderError(output, err.message);
    }
});

// ---------- Boot ----------

checkHealth();
renderChat();
