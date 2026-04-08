"""Tests for the vector database builder."""

import os
import re
import tempfile
import pytest
import chromadb

from src.build_vectordb import chunk_comprehensive_rules, chunk_markdown_file

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RULES_PATH = os.path.join(DATA_DIR, "comprehensive-rules.txt")
RULES_EXIST = os.path.exists(RULES_PATH)
VECTORDB_DIR = os.path.join(os.path.dirname(__file__), "..", "vectordb")
VECTORDB_EXISTS = os.path.exists(VECTORDB_DIR)


# --- Fixtures ---


@pytest.fixture(scope="module")
def rules_chunks():
    """Chunk the real comprehensive rules file."""
    if not RULES_EXIST:
        pytest.skip("Comprehensive rules file not found")
    return chunk_comprehensive_rules(RULES_PATH)


@pytest.fixture
def sample_markdown(tmp_path):
    """Create a sample markdown file for testing."""
    content = """# Test Document

> **See also**: [Other Doc](other.md)

## Section One

This is the first section with some content about Magic cards.
Brainstorm is the best cantrip in Legacy.

### Subsection A

Force of Will is a free counterspell that defines the format.
It costs {3}{U}{U} or you can exile a blue card and pay 1 life.

### Subsection B

Wasteland destroys nonbasic lands. It pairs well with Daze
to create mana denial pressure in tempo decks.

## Section Two

<img src="https://api.scryfall.com/cards/named?exact=Force+of+Will&format=image&version=normal&set=all" alt="Force of Will" width="217">

This section has an image tag that should be stripped.
[Force of Will](https://scryfall.com/search?q=!%22Force+of+Will%22) is linked here.

| Card | Role |
|------|------|
| Brainstorm | Best cantrip |
| Ponder | Second best |

## Section Three - Very Long

""" + ("This is filler text to make this section very long. " * 100) + """

### Long Subsection

""" + ("More filler text for the long subsection. " * 100)

    filepath = tmp_path / "test.md"
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


@pytest.fixture
def sample_rules(tmp_path):
    """Create a minimal rules file for testing."""
    content = """Magic: The Gathering Comprehensive Rules

These rules are effective as of February 27, 2026.

Contents

1. Game Concepts
100. General
101. The Magic Golden Rules

Glossary

1. Game Concepts

100. General

100.1. These Magic rules apply to any Magic game with two or more players.

100.1a A two-player game is a game that begins with only two players.

100.1b A multiplayer game is a game that begins with more than two players.

100.2. To play, each player needs their own deck of traditional Magic cards.

100.2a In constructed play, each deck has a minimum deck size of 60 cards.

101. The Magic Golden Rules

101.1. Whenever a card's text directly contradicts these rules, the card takes precedence.

101.2. When a rule or effect allows or directs something to happen, and another effect states that it can't happen, the "can't" effect takes precedence.

Glossary

Activate
To activate an activated ability is to put it onto the stack and pay its costs.

Artifact
A card type. An artifact is a permanent. See rule 301, "Artifacts."

"""
    filepath = tmp_path / "rules.txt"
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


# --- Comprehensive Rules Chunking ---


class TestChunkComprehensiveRules:
    def test_chunks_from_sample_rules(self, sample_rules):
        chunks = chunk_comprehensive_rules(sample_rules)
        assert len(chunks) > 0

    def test_chunks_have_required_fields(self, sample_rules):
        chunks = chunk_comprehensive_rules(sample_rules)
        for chunk in chunks:
            assert "id" in chunk
            assert "text" in chunk
            assert "metadata" in chunk
            assert "source" in chunk["metadata"]
            assert "type" in chunk["metadata"]
            assert chunk["metadata"]["source"] == "comprehensive-rules"

    def test_chunk_ids_are_unique(self, sample_rules):
        chunks = chunk_comprehensive_rules(sample_rules)
        ids = [c["id"] for c in chunks]
        assert len(ids) == len(set(ids)), "Duplicate chunk IDs found"

    def test_chunks_contain_rule_text(self, sample_rules):
        chunks = chunk_comprehensive_rules(sample_rules)
        all_text = " ".join(c["text"] for c in chunks)
        assert "100.1" in all_text
        assert "two or more players" in all_text

    def test_glossary_is_chunked(self, sample_rules):
        chunks = chunk_comprehensive_rules(sample_rules)
        glossary_chunks = [
            c for c in chunks if c["metadata"].get("type") == "rules-glossary"
        ]
        assert len(glossary_chunks) > 0

    @pytest.mark.skipif(not RULES_EXIST, reason="Full rules not available")
    def test_real_rules_produce_many_chunks(self, rules_chunks):
        assert len(rules_chunks) > 100

    @pytest.mark.skipif(not RULES_EXIST, reason="Full rules not available")
    def test_real_rules_chunk_sizes_are_reasonable(self, rules_chunks):
        """Most chunks should be under 600 words (roughly 400 tokens)."""
        oversized = 0
        for chunk in rules_chunks:
            word_count = len(chunk["text"].split())
            if word_count > 800:
                oversized += 1
        # Allow some oversized (glossary entries, etc.) but most should be small
        assert oversized < len(rules_chunks) * 0.15, (
            f"{oversized}/{len(rules_chunks)} chunks are oversized"
        )

    @pytest.mark.skipif(not RULES_EXIST, reason="Full rules not available")
    def test_real_rules_cover_key_sections(self, rules_chunks):
        """Check that major rule sections are present."""
        sections = {c["metadata"].get("section") for c in rules_chunks}
        # Key sections that must exist
        assert "100" in sections  # General
        assert "117" in sections  # Timing and Priority
        assert "601" in sections  # Casting Spells
        assert "702" in sections  # Keyword Abilities
        assert "704" in sections  # State-Based Actions

    @pytest.mark.skipif(not RULES_EXIST, reason="Full rules not available")
    def test_real_rules_have_no_empty_chunks(self, rules_chunks):
        for chunk in rules_chunks:
            assert chunk["text"].strip(), f"Empty chunk: {chunk['id']}"


# --- Markdown Chunking ---


class TestChunkMarkdown:
    def test_chunks_from_sample(self, sample_markdown):
        chunks = chunk_markdown_file(sample_markdown, "test")
        assert len(chunks) > 0

    def test_chunks_have_required_fields(self, sample_markdown):
        chunks = chunk_markdown_file(sample_markdown, "test")
        for chunk in chunks:
            assert "id" in chunk
            assert "text" in chunk
            assert "metadata" in chunk
            assert chunk["metadata"]["source"] == "test"
            assert chunk["metadata"]["type"] == "strategy"

    def test_chunk_ids_are_unique(self, sample_markdown):
        chunks = chunk_markdown_file(sample_markdown, "test")
        ids = [c["id"] for c in chunks]
        assert len(ids) == len(set(ids))

    def test_image_tags_are_stripped(self, sample_markdown):
        chunks = chunk_markdown_file(sample_markdown, "test")
        all_text = " ".join(c["text"] for c in chunks)
        assert "<img" not in all_text

    def test_scryfall_links_are_stripped_but_names_kept(self, sample_markdown):
        chunks = chunk_markdown_file(sample_markdown, "test")
        all_text = " ".join(c["text"] for c in chunks)
        assert "scryfall.com" not in all_text
        assert "Force of Will" in all_text

    def test_section_titles_are_captured(self, sample_markdown):
        chunks = chunk_markdown_file(sample_markdown, "test")
        titles = [c["metadata"]["title"] for c in chunks]
        assert any("Section One" in t for t in titles)
        assert any("Section Two" in t for t in titles)

    def test_long_sections_are_split(self, sample_markdown):
        chunks = chunk_markdown_file(sample_markdown, "test")
        # Section Three is very long and should be split
        section_three_chunks = [
            c for c in chunks if "Section Three" in c["metadata"]["title"]
        ]
        assert len(section_three_chunks) > 1

    def test_see_also_header_preserved(self, sample_markdown):
        """The 'See also' line at the top should not cause issues."""
        chunks = chunk_markdown_file(sample_markdown, "test")
        assert len(chunks) > 0  # Didn't crash


class TestChunkRealMarkdownFiles:
    """Test chunking against the actual data files."""

    @pytest.fixture(
        params=[
            "legacy-basics.md",
            "deckbuilding-guide.md",
            "legacy-analysis.md",
            "archetype-guide.md",
            "legacy-deck-history.md",
            "mtg-slang.md",
        ]
    )
    def md_file(self, request):
        filepath = os.path.join(DATA_DIR, request.param)
        if not os.path.exists(filepath):
            pytest.skip(f"{request.param} not found")
        return filepath, request.param.replace(".md", "")

    def test_produces_chunks(self, md_file):
        filepath, source = md_file
        chunks = chunk_markdown_file(filepath, source)
        assert len(chunks) > 0

    def test_no_empty_chunks(self, md_file):
        filepath, source = md_file
        chunks = chunk_markdown_file(filepath, source)
        for chunk in chunks:
            assert chunk["text"].strip(), f"Empty chunk: {chunk['id']}"

    def test_no_image_tags_in_chunks(self, md_file):
        filepath, source = md_file
        chunks = chunk_markdown_file(filepath, source)
        for chunk in chunks:
            assert "<img" not in chunk["text"], (
                f"Image tag found in {chunk['id']}"
            )

    def test_no_scryfall_urls_in_chunks(self, md_file):
        filepath, source = md_file
        chunks = chunk_markdown_file(filepath, source)
        for chunk in chunks:
            assert "scryfall.com/search" not in chunk["text"], (
                f"Scryfall URL found in {chunk['id']}"
            )


# --- Vector DB Integration ---


class TestVectorDB:
    @pytest.mark.skipif(not VECTORDB_EXISTS, reason="Vector DB not built")
    def test_db_loads(self):
        client = chromadb.PersistentClient(path=VECTORDB_DIR)
        collection = client.get_collection("legacy_knowledge")
        assert collection.count() > 0

    @pytest.mark.skipif(not VECTORDB_EXISTS, reason="Vector DB not built")
    def test_db_has_expected_chunk_count(self):
        client = chromadb.PersistentClient(path=VECTORDB_DIR)
        collection = client.get_collection("legacy_knowledge")
        count = collection.count()
        assert count > 500, f"Expected 500+ chunks, got {count}"
        assert count < 2000, f"Unexpectedly many chunks: {count}"

    @pytest.mark.skipif(not VECTORDB_EXISTS, reason="Vector DB not built")
    def test_query_returns_results(self):
        from chromadb.utils import embedding_functions

        client = chromadb.PersistentClient(path=VECTORDB_DIR)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        collection = client.get_collection("legacy_knowledge", embedding_function=ef)
        results = collection.query(
            query_texts=["How does Force of Will work?"], n_results=3
        )
        assert len(results["documents"][0]) == 3
        assert all(len(doc) > 0 for doc in results["documents"][0])

    @pytest.mark.skipif(not VECTORDB_EXISTS, reason="Vector DB not built")
    def test_query_rules_question(self):
        from chromadb.utils import embedding_functions

        client = chromadb.PersistentClient(path=VECTORDB_DIR)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        collection = client.get_collection("legacy_knowledge", embedding_function=ef)
        results = collection.query(
            query_texts=["priority and the stack"], n_results=3
        )
        # Should return rules about priority/stack
        sources = [m["source"] for m in results["metadatas"][0]]
        assert "comprehensive-rules" in sources

    @pytest.mark.skipif(not VECTORDB_EXISTS, reason="Vector DB not built")
    def test_query_meta_question(self):
        from chromadb.utils import embedding_functions

        client = chromadb.PersistentClient(path=VECTORDB_DIR)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        collection = client.get_collection("legacy_knowledge", embedding_function=ef)
        results = collection.query(
            query_texts=["Dimir Tempo win rate metagame"], n_results=3
        )
        # Should return strategy/meta content
        sources = [m["source"] for m in results["metadatas"][0]]
        assert any(s != "comprehensive-rules" for s in sources)

    @pytest.mark.skipif(not VECTORDB_EXISTS, reason="Vector DB not built")
    def test_all_sources_represented(self):
        client = chromadb.PersistentClient(path=VECTORDB_DIR)
        collection = client.get_collection("legacy_knowledge")
        results = collection.get(include=["metadatas"])
        sources = {m["source"] for m in results["metadatas"]}
        expected_sources = {
            "comprehensive-rules", "legacy-basics", "deckbuilding-guide",
            "legacy-analysis", "archetype-guide", "legacy-deck-history",
            "mtg-slang",
        }
        assert expected_sources.issubset(sources), (
            f"Missing sources: {expected_sources - sources}"
        )
