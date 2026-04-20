"""
Build the vector database for The Legacy.

Chunks and embeds:
1. MTG Comprehensive Rules (by rule section, ~400 tokens each)
2. Meta data, deck history, and strategy content (by section)

Uses ChromaDB for storage and sentence-transformers for embeddings.
Run this script to (re)build the database from scratch.
"""

import re
import os
import chromadb
from chromadb.utils import embedding_functions

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "vectordb")

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def chunk_comprehensive_rules(filepath: str) -> list[dict]:
    """Chunk the comprehensive rules by rule number (e.g., 100.1, 100.1a).

    Groups consecutive subrules under their parent rule to keep context
    together, targeting ~400 tokens per chunk. Each chunk includes the
    section header for context.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Find where the actual rules start (after the table of contents)
    # Rules start with "1. Game Concepts" after line ~180
    rules_match = re.search(r"\n1\. Game Concepts\n", text)
    if not rules_match:
        raise ValueError("Could not find start of rules")
    rules_text = text[rules_match.start() :]

    # Find where glossary starts
    glossary_match = re.search(r"\nGlossary\n", rules_text)
    if glossary_match:
        rules_text = rules_text[: glossary_match.start()]
        glossary_text = text[rules_match.start() + glossary_match.start() :]
    else:
        glossary_text = ""

    # Split into sections by top-level rule number (e.g., "100. General")
    # Each section is a major rule like 100, 101, 102, etc.
    section_pattern = re.compile(r"^(\d{3})\. (.+)$", re.MULTILINE)
    sections = []
    matches = list(section_pattern.finditer(rules_text))

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(rules_text)
        section_num = match.group(1)
        section_title = match.group(2)
        section_body = rules_text[start:end].strip()

        # Split section into chunks by individual rule numbers
        # Rules are like "100.1.", "100.1a", "100.2.", etc.
        rule_pattern = re.compile(
            r"^(" + section_num + r"\.\d+[a-z]?\.?) (.+?)(?=\n"
            + section_num
            + r"\.\d+[a-z]?\.? |\n\d{3}\. |\Z)",
            re.MULTILINE | re.DOTALL,
        )
        rules = list(rule_pattern.finditer(section_body))

        if not rules:
            # Section has no subrules, treat as one chunk
            sections.append(
                {
                    "id": f"rules-{section_num}",
                    "text": section_body,
                    "metadata": {
                        "source": "comprehensive-rules",
                        "section": section_num,
                        "title": section_title,
                        "type": "rules",
                    },
                }
            )
            continue

        # Group rules into chunks of ~400 tokens (~300 words)
        current_chunk = f"{section_num}. {section_title}\n\n"
        current_rules = []
        chunk_idx = 0

        for rule in rules:
            rule_text = rule.group(0).strip()
            # Rough token estimate: words * 1.3
            combined_len = len((current_chunk + rule_text).split()) * 1.3

            if combined_len > 400 and current_rules:
                # Save current chunk
                sections.append(
                    {
                        "id": f"rules-{section_num}-{chunk_idx}",
                        "text": current_chunk.strip(),
                        "metadata": {
                            "source": "comprehensive-rules",
                            "section": section_num,
                            "title": section_title,
                            "rules": ", ".join(current_rules),
                            "type": "rules",
                        },
                    }
                )
                chunk_idx += 1
                current_chunk = f"{section_num}. {section_title}\n\n"
                current_rules = []

            current_chunk += rule_text + "\n\n"
            current_rules.append(rule.group(1))

        # Save last chunk
        if current_rules:
            sections.append(
                {
                    "id": f"rules-{section_num}-{chunk_idx}",
                    "text": current_chunk.strip(),
                    "metadata": {
                        "source": "comprehensive-rules",
                        "section": section_num,
                        "title": section_title,
                        "rules": ", ".join(current_rules),
                        "type": "rules",
                    },
                }
            )

    # Chunk the glossary too
    if glossary_text:
        glossary_entries = re.split(r"\n\n(?=[A-Z])", glossary_text)
        for i in range(0, len(glossary_entries), 10):
            batch = "\n\n".join(glossary_entries[i : i + 10])
            sections.append(
                {
                    "id": f"rules-glossary-{i // 10}",
                    "text": batch.strip(),
                    "metadata": {
                        "source": "comprehensive-rules",
                        "section": "glossary",
                        "title": "Glossary",
                        "type": "rules-glossary",
                    },
                }
            )

    return sections


def chunk_scryfall_cards(card_index_path: str | None = None) -> list[dict]:
    """Emit one RAG chunk per Legacy-legal card.

    Each chunk is a compact card-sheet style block with name, mana cost,
    type line, oracle text, and (for creatures) P/T + keywords — what a
    player would want to see when the model references that card. Metadata
    marks the chunk as `source: 'scryfall-card'` so the frontend can
    distinguish card hits from rules/meta hits in the "grounded in N
    sources" badge.

    Filters to Legacy-legal only (~30k cards). That's sufficient for any
    deck / rules / evaluation question the finetune is targeting, and
    keeps the vector DB lean enough for fast queries.
    """
    import pickle

    if card_index_path is None:
        card_index_path = os.path.join(DATA_DIR, "card_index.pkl")

    # Gracefully skip if the card_index pickle isn't available — tests that
    # exercise build_database() against a synthetic data dir shouldn't need
    # 36k cards wired up. Production always has the file in the image.
    if not os.path.exists(card_index_path):
        print(f"  card_index not found at {card_index_path} — skipping card chunks")
        return []

    print(f"Loading card index from {card_index_path}...")
    with open(card_index_path, "rb") as f:
        data = pickle.load(f)

    cards = data["cards"]
    legacy_legal = data["legacy_legal"]

    chunks = []
    for name in sorted(legacy_legal):
        card = cards.get(name)
        if not card:
            continue

        # Build a compact, retrieval-friendly card sheet
        lines = [f"# {name}"]
        if card.get("mana_cost"):
            lines.append(f"Mana cost: {card['mana_cost']}")
        if card.get("type_line"):
            lines.append(f"Type: {card['type_line']}")
        if card.get("power") is not None and card.get("toughness") is not None:
            lines.append(f"Power/Toughness: {card['power']}/{card['toughness']}")
        if card.get("loyalty") is not None:
            lines.append(f"Loyalty: {card['loyalty']}")
        if card.get("keywords"):
            lines.append(f"Keywords: {', '.join(card['keywords'])}")
        if card.get("oracle_text"):
            lines.append("")
            lines.append(card["oracle_text"])

        text = "\n".join(lines)
        chunks.append({
            "id": f"card-{name.replace(' ', '-').replace('//', '__')[:80]}",
            "text": text,
            "metadata": {
                "source": "scryfall-card",
                "name": name,
                "title": name,  # used by the retrieval label
                "type": "card",
                "card_type": card.get("type_line", "").split("—")[0].strip(),
            },
        })

    print(f"  Built {len(chunks)} card chunks")
    return chunks


def chunk_markdown_file(filepath: str, source_name: str) -> list[dict]:
    """Chunk a markdown file by ## and ### headers.

    Each chunk is a section under a heading, with the heading included
    for context. Strips image tags to keep chunks text-focused.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Strip image tags
    text = re.sub(r"<img[^>]+>", "", text)
    # Strip Scryfall links but keep card names
    text = re.sub(r"\[([^\]]+)\]\(https://scryfall\.com/search[^)]+\)", r"\1", text)
    # Clean up multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Split by ## headers
    sections = re.split(r"(?=^## )", text, flags=re.MULTILINE)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Get section title
        title_match = re.match(r"^##+ (.+)$", section, re.MULTILINE)
        title = title_match.group(1) if title_match else "Introduction"

        # If section is short enough, keep as one chunk
        word_count = len(section.split())
        if word_count <= 400:
            chunks.append(
                {
                    "id": f"{source_name}-{len(chunks)}",
                    "text": section,
                    "metadata": {
                        "source": source_name,
                        "title": title,
                        "type": "strategy",
                    },
                }
            )
        else:
            # Split by ### subsections
            subsections = re.split(r"(?=^### )", section, flags=re.MULTILINE)
            for sub in subsections:
                sub = sub.strip()
                if not sub:
                    continue
                sub_title_match = re.match(r"^###+ (.+)$", sub, re.MULTILINE)
                sub_title = (
                    f"{title} > {sub_title_match.group(1)}"
                    if sub_title_match
                    else title
                )

                # Further split if still too long
                sub_words = len(sub.split())
                if sub_words <= 500:
                    chunks.append(
                        {
                            "id": f"{source_name}-{len(chunks)}",
                            "text": sub,
                            "metadata": {
                                "source": source_name,
                                "title": sub_title,
                                "type": "strategy",
                            },
                        }
                    )
                else:
                    # Split by paragraphs, grouping to ~400 words
                    paragraphs = sub.split("\n\n")
                    current = ""
                    for para in paragraphs:
                        if len((current + para).split()) > 400 and current:
                            chunks.append(
                                {
                                    "id": f"{source_name}-{len(chunks)}",
                                    "text": current.strip(),
                                    "metadata": {
                                        "source": source_name,
                                        "title": sub_title,
                                        "type": "strategy",
                                    },
                                }
                            )
                            current = ""
                        current += para + "\n\n"
                    if current.strip():
                        chunks.append(
                            {
                                "id": f"{source_name}-{len(chunks)}",
                                "text": current.strip(),
                                "metadata": {
                                    "source": source_name,
                                    "title": sub_title,
                                    "type": "strategy",
                                },
                            }
                        )

    return chunks


def build_database():
    """Build the complete vector database."""
    os.makedirs(DB_DIR, exist_ok=True)

    print("Initializing ChromaDB...")
    client = chromadb.PersistentClient(path=DB_DIR)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    # Delete existing collection if rebuilding
    try:
        client.delete_collection("legacy_knowledge")
    except (ValueError, chromadb.errors.NotFoundError):
        pass

    collection = client.create_collection(
        name="legacy_knowledge",
        embedding_function=ef,
        metadata={"description": "The Legacy - MTG Legacy deck builder knowledge base"},
    )

    all_chunks = []

    # 1. Comprehensive Rules
    print("Chunking comprehensive rules...")
    rules_path = os.path.join(DATA_DIR, "comprehensive-rules.txt")
    rules_chunks = chunk_comprehensive_rules(rules_path)
    all_chunks.extend(rules_chunks)
    print(f"  -> {len(rules_chunks)} rule chunks")

    # 2. Strategy content files
    strategy_files = {
        "legacy-basics": "legacy-basics.md",
        "deckbuilding-guide": "deckbuilding-guide.md",
        "legacy-analysis": "legacy-analysis.md",
        "archetype-guide": "archetype-guide.md",
        "legacy-deck-history": "legacy-deck-history.md",
        "mtg-slang": "mtg-slang.md",
    }

    for source_name, filename in strategy_files.items():
        filepath = os.path.join(DATA_DIR, filename)
        print(f"Chunking {filename}...")
        chunks = chunk_markdown_file(filepath, source_name)
        all_chunks.extend(chunks)
        print(f"  -> {len(chunks)} chunks")

    # 3. Scryfall cards — one chunk per Legacy-legal card, so queries like
    #    "what does Force of Will do?" or "is Akroma playable?" retrieve
    #    real card text instead of making the model fabricate oracle text.
    print("Chunking Scryfall cards...")
    card_chunks = chunk_scryfall_cards()
    all_chunks.extend(card_chunks)
    print(f"  -> {len(card_chunks)} chunks")

    # 4. Add all chunks to ChromaDB
    print(f"\nEmbedding and storing {len(all_chunks)} total chunks...")

    # ChromaDB has a batch limit, process in batches of 100
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        collection.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )
        print(f"  Stored {min(i + batch_size, len(all_chunks))}/{len(all_chunks)}")

    print(f"\nDone! {collection.count()} chunks in vector DB at {DB_DIR}")

    # Print stats
    sources = {}
    for c in all_chunks:
        src = c["metadata"]["source"]
        sources[src] = sources.get(src, 0) + 1
    print("\nChunks by source:")
    for src, count in sorted(sources.items()):
        print(f"  {src}: {count}")


if __name__ == "__main__":
    build_database()
