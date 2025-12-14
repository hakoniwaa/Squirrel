"""Integration test: Parse real Claude Code logs and run ingest pipeline."""

import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

from sqrl.chunking import ChunkConfig, chunk_events, events_to_json
from sqrl.parsers.claude_code import ClaudeCodeParser

# Find a real session file
OFFER_I_PATH = Path.home() / ".claude/projects/-home-lyrica-Offer-I"


def find_session_with_events(min_events: int = 10) -> Path | None:
    """Find a session file with enough events for testing."""
    if not OFFER_I_PATH.exists():
        return None

    parser = ClaudeCodeParser()
    for session_file in sorted(OFFER_I_PATH.glob("*.jsonl"))[:20]:
        # Skip agent files
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


def skipif_decorator(condition, reason=""):
    """Fallback skipif decorator when pytest not available."""
    def decorator(cls_or_func):
        return cls_or_func
    return decorator

skipif = pytest.mark.skipif if HAS_PYTEST else skipif_decorator

def skip(reason=""):
    """Skip test with reason."""
    if HAS_PYTEST:
        pytest.skip(reason)
    else:
        print(f"SKIP: {reason}")
        return None


@skipif(
    not OFFER_I_PATH.exists(),
    reason="Offer-I session logs not available"
)
class TestIntegration:
    """Integration tests using real session data."""

    def test_parse_real_session(self):
        """Parse a real Claude Code session file."""
        session_file = find_session_with_events(min_events=5)
        if session_file is None:
            return skip("No suitable session file found")

        parser = ClaudeCodeParser()
        episodes = parser.parse_session(session_file)

        print(f"\n=== Parsed {session_file.name} ===")
        print(f"Episodes found: {len(episodes)}")

        total_events = 0
        for i, ep in enumerate(episodes[:3]):  # Show first 3 episodes
            print(f"\nEpisode {i}: {len(ep.events)} events")
            for event in ep.events[:5]:  # Show first 5 events per episode
                summary = event.summary[:60] + "..." if len(event.summary) > 60 else event.summary
                print(f"  [{event.role}] {event.kind}: {summary}")
            total_events += len(ep.events)

        print(f"\nTotal events across all episodes: {total_events}")
        assert len(episodes) >= 1

    def test_chunk_real_events(self):
        """Chunk events from a real session."""
        session_file = find_session_with_events(min_events=10)
        if session_file is None:
            return skip("No suitable session file found")

        parser = ClaudeCodeParser()
        episodes = parser.parse_session(session_file)

        # Flatten episodes to events
        events = []
        for ep in episodes:
            events.extend(ep.events)

        # Chunk with small size for testing
        config = ChunkConfig(chunk_size=20, overlap=5)
        chunks = list(chunk_events(events, config))

        print(f"\n=== Chunking {len(events)} events ===")
        print(f"Config: chunk_size={config.chunk_size}, overlap={config.overlap}")
        print(f"Chunks created: {len(chunks)}")

        for i, chunk in enumerate(chunks[:3]):
            print(f"\nChunk {i}: {len(chunk.events)} events")
            if chunk.events:
                first = chunk.events[0]
                last = chunk.events[-1]
                print(f"  First: [{first.role}] {first.kind}")
                print(f"  Last:  [{last.role}] {last.kind}")

        assert len(chunks) >= 1

    def test_events_to_json(self):
        """Test JSON serialization of events."""
        session_file = find_session_with_events(min_events=5)
        if session_file is None:
            return skip("No suitable session file found")

        parser = ClaudeCodeParser()
        episodes = parser.parse_session(session_file)

        # Get first few events
        events = episodes[0].events[:5]
        json_events = events_to_json(events)

        print("\n=== JSON serialization ===")
        print(f"Events: {len(events)}")
        for je in json_events:
            print(f"  {je}")

        assert len(json_events) == len(events)
        for je in json_events:
            assert "ts" in je
            assert "role" in je
            assert "kind" in je
            assert "summary" in je


# Quick test runner
if __name__ == "__main__":
    print("Finding session file...")
    session_file = find_session_with_events(min_events=10)
    if session_file:
        print(f"Found: {session_file}")

        parser = ClaudeCodeParser()
        episodes = parser.parse_session(session_file)

        print(f"\nParsed {len(episodes)} episodes")
        for i, ep in enumerate(episodes[:5]):
            print(f"\nEpisode {i}: {len(ep.events)} events")
            for event in ep.events[:3]:
                summary = event.summary[:80] if event.summary else "(no summary)"
                print(f"  [{event.role}] {event.kind}: {summary}")
    else:
        print("No suitable session found")
