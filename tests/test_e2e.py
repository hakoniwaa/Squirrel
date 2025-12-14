"""
End-to-end test: Full ingest pipeline with real LLM.

This test requires:
- ANTHROPIC_API_KEY or OPENAI_API_KEY
- Real Claude Code session logs

Run with: pytest tests/test_e2e.py -v -s
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from sqrl.chunking import ChunkConfig, chunk_events, events_to_json
from sqrl.db import (
    commit_memory_ops,
    get_active_memories,
    get_memory_by_id,
    get_metrics,
    init_db,
    insert_episode,
)
from sqrl.embeddings import embed_text_sync, make_embedding_getter
from sqrl.memory_writer import MemoryWriter, MemoryWriterConfig
from sqrl.parsers.claude_code import ClaudeCodeParser

# Check for API key
HAS_ANTHROPIC_KEY = bool(os.getenv("ANTHROPIC_API_KEY"))
HAS_OPENAI_KEY = bool(os.getenv("OPENAI_API_KEY"))
HAS_LLM_KEY = HAS_ANTHROPIC_KEY or HAS_OPENAI_KEY

# Find real session data
OFFER_I_PATH = Path.home() / ".claude/projects/-home-lyrica-Offer-I"
HAS_SESSION_DATA = OFFER_I_PATH.exists()


def find_session_with_events(min_events: int = 10) -> Path | None:
    """Find a session file with enough events for testing."""
    if not OFFER_I_PATH.exists():
        return None

    parser = ClaudeCodeParser()
    for session_file in sorted(OFFER_I_PATH.glob("*.jsonl"))[:20]:
        if session_file.name.startswith("agent-"):
            continue
        try:
            episodes = parser.parse_session(session_file)
            total_events = sum(len(ep.events) for ep in episodes)
            if total_events >= min_events:
                return session_file
        except Exception:
            continue
    return None


@pytest.mark.skipif(
    not HAS_LLM_KEY,
    reason="No LLM API key (ANTHROPIC_API_KEY or OPENAI_API_KEY)"
)
@pytest.mark.skipif(
    not HAS_SESSION_DATA,
    reason="No session data at ~/.claude/projects/-home-lyrica-Offer-I"
)
class TestEndToEnd:
    """End-to-end tests requiring real LLM and session data."""

    def test_full_ingest_pipeline(self):
        """
        Complete ingest pipeline:
        1. Parse real Claude Code logs
        2. Chunk events
        3. Run Memory Writer (real LLM)
        4. Store in SQLite
        5. Verify retrieval
        """
        # 1. Parse real logs
        session_file = find_session_with_events(min_events=10)
        if session_file is None:
            pytest.skip("No suitable session file found")

        parser = ClaudeCodeParser()
        episodes = parser.parse_session(session_file)
        assert len(episodes) >= 1

        print(f"\n=== Parsed {session_file.name} ===")
        print(f"Episodes: {len(episodes)}")

        # Flatten to events
        events = []
        for ep in episodes:
            events.extend(ep.events)
        print(f"Total events: {len(events)}")

        # 2. Chunk events
        config = ChunkConfig(chunk_size=25, overlap=5)
        chunks = list(chunk_events(events, config))
        print(f"Chunks created: {len(chunks)}")

        # 3. Run Memory Writer on first chunk
        chunk = chunks[0]
        events_json = events_to_json(chunk.events)

        # Determine model based on available API key
        if HAS_ANTHROPIC_KEY:
            model = "anthropic/claude-sonnet-4-20250514"
        else:
            model = "gpt-4o"

        writer_config = MemoryWriterConfig(model=model)
        writer = MemoryWriter(config=writer_config)

        print(f"\n=== Running Memory Writer ({model}) ===")
        print(f"Processing {len(chunk.events)} events...")

        result = writer.ingest_sync(
            events=events_json,
            project_id="test-e2e",
            owner_type="user",
            owner_id="test-user",
            chunk_index=0,
            recent_memories=[],
        )

        print(f"Episodes detected: {len(result.episodes)}")
        print(f"Memories extracted: {len(result.memories)}")

        if result.discard_reason:
            print(f"Discard reason: {result.discard_reason}")
        else:
            for mem in result.memories:
                print(f"  [{mem.kind.value}] {mem.text[:60]}...")

        # 4. Store in SQLite
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = init_db(db_path)

            # Insert episode
            episode_id = insert_episode(
                conn,
                project_id="test-e2e",
                start_ts=chunk.events[0].ts,
                end_ts=chunk.events[-1].ts,
                events_json="{}",
            )

            # Commit memories (without embeddings to avoid API costs)
            if result.memories:
                new_ids = commit_memory_ops(conn, result.memories, episode_id)
                print(f"\nStored {len(new_ids)} memories in SQLite")

                # 5. Verify retrieval
                for mem_id in new_ids:
                    memory = get_memory_by_id(conn, mem_id)
                    assert memory is not None
                    print(f"  Retrieved: {memory['id'][:8]}... {memory['kind']}")

                    # Verify metrics initialized
                    metrics = get_metrics(conn, mem_id)
                    assert metrics is not None
                    assert metrics["use_count"] == 0

                # Query active memories
                active = get_active_memories(conn)
                assert len(active) == len(new_ids)

            conn.close()

        print("\n=== End-to-end test PASSED ===")


@pytest.mark.skipif(
    not HAS_OPENAI_KEY,
    reason="No OPENAI_API_KEY for embeddings"
)
class TestEmbeddingsIntegration:
    """Test real embedding generation."""

    def test_real_embedding(self):
        """Generate a real embedding via OpenAI API."""
        text = "SSL errors with requests library, switch to httpx"

        embedding = embed_text_sync(text)

        print("\n=== Real Embedding ===")
        print(f"Text: {text}")
        print(f"Dimensions: {len(embedding)}")
        print(f"Sample values: {embedding[:5]}...")

        # Verify dimensions
        assert len(embedding) == 1536
        assert all(isinstance(v, float) for v in embedding)

    def test_embedding_getter_with_db(self):
        """Test embedding getter stores in SQLite correctly."""
        # Create getter
        getter = make_embedding_getter()

        # Get embedding as bytes
        text = "Test memory for embedding storage"
        embedding_bytes = getter(text)

        print("\n=== Embedding Bytes ===")
        print(f"Text: {text}")
        print(f"Bytes length: {len(embedding_bytes)}")

        # 1536 floats * 4 bytes = 6144 bytes
        assert len(embedding_bytes) == 1536 * 4

        # Store in SQLite
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = init_db(db_path)

            # Insert episode first (not used but initializes foreign key support)
            _ = insert_episode(
                conn,
                project_id="test",
                start_ts="2024-01-01T00:00:00Z",
                end_ts="2024-01-01T00:01:00Z",
                events_json="{}",
            )

            # Insert directly into memories table with embedding
            from sqrl.db.repository import generate_id, now_iso

            memory_id = generate_id()
            conn.execute(
                """
                INSERT INTO memories (
                    id, scope, owner_type, owner_id, kind, tier,
                    polarity, text, status, confidence, embedding,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory_id, "project", "user", "test",
                    "pattern", "short_term", 1, text,
                    "provisional", 0.8, embedding_bytes,
                    now_iso(), now_iso(),
                ),
            )
            conn.commit()

            # Verify storage
            cursor = conn.execute(
                "SELECT embedding FROM memories WHERE id = ?",
                (memory_id,),
            )
            row = cursor.fetchone()
            assert row is not None
            assert row["embedding"] == embedding_bytes

            conn.close()

        print("=== Embedding storage test PASSED ===")


# Quick test runner
if __name__ == "__main__":
    print("=== End-to-End Test Runner ===\n")

    if not HAS_LLM_KEY:
        print("WARNING: No LLM API key found")
        print("  Set ANTHROPIC_API_KEY or OPENAI_API_KEY")
    else:
        print(f"LLM API: {'Anthropic' if HAS_ANTHROPIC_KEY else 'OpenAI'}")

    if not HAS_SESSION_DATA:
        print("WARNING: No session data found at ~/.claude/projects/-home-lyrica-Offer-I")
    else:
        session = find_session_with_events()
        print(f"Session data: {session.name if session else 'None found'}")

    print("\nRun with: pytest tests/test_e2e.py -v -s")
