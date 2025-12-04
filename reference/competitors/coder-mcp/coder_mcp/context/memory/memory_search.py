"""
Memory search functionality for finding and filtering memories
"""

import logging
from typing import List, Optional

from .memory_store import MemoryStore
from .memory_types import MemoryType

logger = logging.getLogger(__name__)


class MemorySearch:
    """Handle memory search and filtering operations"""

    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store

    async def search_memories(
        self,
        query: str,
        memory_type: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[MemoryType]:
        """Search through project memories with various filters"""
        try:
            memories = await self.memory_store.load_memories()

            # Apply filters
            filtered_memories = memories

            # Filter by memory type
            if memory_type:
                filtered_memories = [
                    m for m in filtered_memories if m.get_type_name() == memory_type
                ]

            # Filter by category
            if category:
                filtered_memories = [
                    m for m in filtered_memories if m.get_category().value == category
                ]

            # Filter by tags
            if tags:
                filtered_memories = [
                    m for m in filtered_memories if any(tag in m.tags for tag in tags)
                ]

            # Search by query
            if query:
                query_results = []
                query_lower = query.lower()

                for memory in filtered_memories:
                    if memory.matches_query(query):
                        # Calculate relevance score
                        score = self._calculate_relevance_score(memory, query_lower)
                        query_results.append((score, memory))

                # Sort by relevance score (descending)
                query_results.sort(key=lambda x: x[0], reverse=True)
                filtered_memories = [memory for _, memory in query_results]

            # Sort by timestamp (most recent first) if no query provided
            elif not query:
                filtered_memories.sort(key=lambda m: m.timestamp, reverse=True)

            return filtered_memories[:limit]

        except (OSError, ValueError, TypeError, AttributeError) as e:
            logger.error("Memory search failed: %s", e)
            return []

    def _calculate_relevance_score(self, memory: MemoryType, query: str) -> float:
        """Calculate relevance score for a memory based on query"""
        score = 0.0

        # Content match scoring
        content_lower = memory.content.lower()
        if query in content_lower:
            score += 10.0
            # Boost for exact phrase match
            if f" {query} " in content_lower:
                score += 5.0

        # Tag match scoring
        for tag in memory.tags:
            if query in tag.lower():
                score += 8.0

        # Metadata match scoring
        for _, value in memory.metadata.items():
            if isinstance(value, str) and query in value.lower():
                score += 3.0

        # Word-level scoring
        query_words = query.split()
        for word in query_words:
            if word in content_lower:
                score += 2.0

        return score
