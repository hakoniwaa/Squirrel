"""
Ingest pipeline for Squirrel.

Ties together: parser → chunking → Memory Writer → results.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from sqrl.chunking import ChunkConfig, chunk_events
from sqrl.memory_writer import MemoryWriter, MemoryWriterConfig, MemoryWriterOutput
from sqrl.parsers.base import BaseParser, Event


@dataclass
class IngestResult:
    """Result of ingesting a session or project."""

    chunks_processed: int = 0
    episodes_detected: int = 0
    memories_extracted: int = 0
    # Collected outputs from each chunk
    chunk_outputs: list[MemoryWriterOutput] = field(default_factory=list)
    # Any errors encountered
    errors: list[str] = field(default_factory=list)


class IngestPipeline:
    """
    Pipeline for ingesting logs into memories.

    Flow:
    1. Parse logs → Events
    2. Chunk events
    3. Call Memory Writer for each chunk (with carry_state)
    4. Collect results
    """

    def __init__(
        self,
        parser: BaseParser,
        chunk_config: Optional[ChunkConfig] = None,
        writer_config: Optional[MemoryWriterConfig] = None,
    ):
        self.parser = parser
        self.chunk_config = chunk_config or ChunkConfig()
        self.writer = MemoryWriter(writer_config)

    async def ingest_events(
        self,
        events: list[Event],
        project_id: str,
        owner_type: str = "user",
        owner_id: str = "default",
        recent_memories: Optional[list[dict]] = None,
    ) -> IngestResult:
        """
        Ingest a list of events through the pipeline.

        Args:
            events: List of Event objects to process
            project_id: Project identifier
            owner_type: Owner type (user/team/org)
            owner_id: Owner identifier
            recent_memories: Existing memories for context

        Returns:
            IngestResult with aggregated results
        """
        result = IngestResult()
        carry_state: Optional[str] = None

        for chunk in chunk_events(events, self.chunk_config):
            try:
                output = await self.writer.process_chunk(
                    events=chunk.events,
                    project_id=project_id,
                    owner_type=owner_type,
                    owner_id=owner_id,
                    chunk_index=chunk.chunk_index,
                    carry_state=carry_state,
                    recent_memories=recent_memories,
                )

                result.chunks_processed += 1
                result.episodes_detected += len(output.episodes)
                result.memories_extracted += len(output.memories)
                result.chunk_outputs.append(output)

                # Pass carry_state to next chunk
                carry_state = output.carry_state

            except Exception as e:
                result.errors.append(f"Chunk {chunk.chunk_index}: {e}")

        return result

    async def ingest_session(
        self,
        session_path: Path,
        project_id: str,
        owner_type: str = "user",
        owner_id: str = "default",
        recent_memories: Optional[list[dict]] = None,
    ) -> IngestResult:
        """
        Ingest a single session file.

        Args:
            session_path: Path to session log file
            project_id: Project identifier
            owner_type: Owner type (user/team/org)
            owner_id: Owner identifier
            recent_memories: Existing memories for context

        Returns:
            IngestResult with aggregated results
        """
        # Parse session into episodes, then flatten to events
        episodes = self.parser.parse_session(session_path)
        events = []
        for ep in episodes:
            events.extend(ep.events)

        return await self.ingest_events(
            events=events,
            project_id=project_id,
            owner_type=owner_type,
            owner_id=owner_id,
            recent_memories=recent_memories,
        )

    async def ingest_project(
        self,
        project_path: Path,
        project_id: str,
        owner_type: str = "user",
        owner_id: str = "default",
        recent_memories: Optional[list[dict]] = None,
    ) -> IngestResult:
        """
        Ingest all sessions for a project.

        Args:
            project_path: Path to project root
            project_id: Project identifier
            owner_type: Owner type (user/team/org)
            owner_id: Owner identifier
            recent_memories: Existing memories for context

        Returns:
            IngestResult with aggregated results from all sessions
        """
        result = IngestResult()

        sessions = self.parser.get_sessions(project_path)
        for session_path in sessions:
            session_result = await self.ingest_session(
                session_path=session_path,
                project_id=project_id,
                owner_type=owner_type,
                owner_id=owner_id,
                recent_memories=recent_memories,
            )

            # Aggregate results
            result.chunks_processed += session_result.chunks_processed
            result.episodes_detected += session_result.episodes_detected
            result.memories_extracted += session_result.memories_extracted
            result.chunk_outputs.extend(session_result.chunk_outputs)
            result.errors.extend(session_result.errors)

        return result

    def ingest_events_sync(
        self,
        events: list[Event],
        project_id: str,
        owner_type: str = "user",
        owner_id: str = "default",
        recent_memories: Optional[list[dict]] = None,
    ) -> IngestResult:
        """Synchronous wrapper for ingest_events."""
        import asyncio

        return asyncio.run(
            self.ingest_events(
                events=events,
                project_id=project_id,
                owner_type=owner_type,
                owner_id=owner_id,
                recent_memories=recent_memories,
            )
        )
