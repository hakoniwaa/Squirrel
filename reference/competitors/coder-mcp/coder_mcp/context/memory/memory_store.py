"""
Memory storage and management for project context
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...core import ConfigurationManager
from ...utils.file_utils import FileManager
from .memory_types import MemoryType, TemporaryMemory, create_memory, memory_from_dict

logger = logging.getLogger(__name__)


class MemoryStore:
    """Manages project context and memories with caching support"""

    def _workspace_hash(self) -> str:
        return hashlib.md5(
            str(self.workspace_root).encode("utf-8"), usedforsecurity=False
        ).hexdigest()[
            :8
        ]  # nosec B324

    @property
    def CONTEXT_KEY(self) -> str:
        return f"project_context_{self._workspace_hash()}"

    @property
    def MEMORY_KEY(self) -> str:
        return f"project_memories_{self._workspace_hash()}"

    def __init__(self, workspace_root: Path, config_manager: ConfigurationManager):
        self.workspace_root = workspace_root
        self.config_manager = config_manager
        self.file_manager = FileManager()

        # Storage paths
        self.context_dir = workspace_root / ".coder_mcp"
        self.context_file = self.context_dir / "context.json"
        self.memories_file = self.context_dir / "memories.json"

        # Configuration
        self.max_memories = getattr(config_manager.config.storage, "max_memories", 1000)
        self.max_memory_age_days = getattr(
            config_manager.config.storage, "max_memory_age_days", 365
        )

    async def load_context(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Load project context from cache or storage"""
        # Try cache first if not forcing refresh
        if (
            not force_refresh
            and hasattr(self.config_manager, "cache_provider")
            and self.config_manager.cache_provider
        ):
            # Try cache first
            cached_context = await self.config_manager.cache_provider.get(self.CONTEXT_KEY)
            if cached_context:
                return dict(cached_context)

        # Load from local file
        if self.context_file.exists():
            try:
                content = await self.file_manager.safe_read_file(self.context_file)
                context = json.loads(content)

                # Cache the loaded context
                if (
                    hasattr(self.config_manager, "cache_provider")
                    and self.config_manager.cache_provider
                ):
                    await self.config_manager.cache_provider.set(
                        self.CONTEXT_KEY, context, ttl=self.config_manager.config.storage.cache_ttl
                    )

                return dict(context)
            except (OSError, json.JSONDecodeError, ValueError) as e:
                logger.warning("Could not load context from file: %s", e)

        # Return default context
        return self._create_default_context()

    async def save_context(self, context: Dict[str, Any]) -> bool:
        """Save context to cache and local storage"""
        try:
            # Update timestamps
            context["last_updated"] = datetime.now().isoformat()

            # Save to cache
            if (
                hasattr(self.config_manager, "cache_provider")
                and self.config_manager.cache_provider
            ):
                await self.config_manager.cache_provider.set(
                    self.CONTEXT_KEY, context, ttl=self.config_manager.config.storage.cache_ttl
                )

            # Ensure context directory exists
            self.context_dir.mkdir(parents=True, exist_ok=True)

            # Save to local file
            content = json.dumps(context, indent=2)
            await self.file_manager.safe_write_file(self.context_file, content)

            return True

        except (OSError, ValueError, TypeError) as e:
            logger.error("Failed to save context: %s", e)
            return False

    async def update_context(self, updates: Dict[str, Any]) -> bool:
        """Update specific sections of the context"""
        context = await self.load_context()

        # Deep merge updates
        for key, value in updates.items():
            if isinstance(value, dict) and key in context and isinstance(context[key], dict):
                context[key].update(value)
            else:
                context[key] = value

        return await self.save_context(context)

    async def load_memories(self) -> List[MemoryType]:
        """Load all memories from storage"""
        # Try cache first
        cached_memories = await self._load_memories_from_cache()
        if cached_memories is not None:
            return cached_memories

        # Load from file
        return await self._load_memories_from_file()

    async def _load_memories_from_cache(self) -> Optional[List[MemoryType]]:
        """Load memories from cache if available"""
        if not (
            hasattr(self.config_manager, "cache_provider") and self.config_manager.cache_provider
        ):
            return None

        try:
            cached_memories = await self.config_manager.cache_provider.get(self.MEMORY_KEY)
            if cached_memories:
                return [memory_from_dict(mem_data) for mem_data in cached_memories]
        except (OSError, json.JSONDecodeError, ValueError, KeyError) as e:
            logger.debug("Failed to load memories from cache: %s", e)

        return None

    async def _load_memories_from_file(self) -> List[MemoryType]:
        """Load memories from file storage"""
        if not self.memories_file.exists():
            return []

        try:
            content = await self.file_manager.safe_read_file(self.memories_file)
            memories_data = json.loads(content)
            memories = self._parse_memory_data(memories_data)

            # Cache the loaded memories
            await self._cache_memories(memories)
            return memories

        except (OSError, json.JSONDecodeError, ValueError) as e:
            logger.warning("Could not load memories from file: %s", e)
            return []

    def _parse_memory_data(self, memories_data: List[Dict[str, Any]]) -> List[MemoryType]:
        """Parse memory data and filter out expired memories"""
        memories = []
        for mem_data in memories_data:
            try:
                memory = memory_from_dict(mem_data)
                # Skip expired temporary memories
                if isinstance(memory, TemporaryMemory) and memory.is_expired():
                    continue
                memories.append(memory)
            except (ValueError, KeyError, TypeError) as e:
                logger.debug("Failed to load memory: %s", e)
        return memories

    async def save_memories(self, memories: List[MemoryType]) -> bool:
        """Save all memories to storage"""
        try:
            # Filter out expired temporary memories
            active_memories = []
            for memory in memories:
                if isinstance(memory, TemporaryMemory) and memory.is_expired():
                    continue
                active_memories.append(memory)

            # Limit number of memories
            if len(active_memories) > self.max_memories:
                # Sort by timestamp (most recent first) and keep only the limit
                active_memories.sort(key=lambda m: m.timestamp, reverse=True)
                active_memories = active_memories[: self.max_memories]

            # Convert to dictionary format
            memories_data = [memory.to_dict() for memory in active_memories]

            # Save to cache
            await self._cache_memories(active_memories)

            # Ensure directory exists
            self.context_dir.mkdir(parents=True, exist_ok=True)

            # Save to file
            content = json.dumps(memories_data, indent=2)
            await self.file_manager.safe_write_file(self.memories_file, content)

            logger.debug("Saved %d memories to storage", len(active_memories))
            return True

        except (OSError, ValueError, TypeError) as e:
            logger.error("Failed to save memories: %s", e)
            return False

    async def add_memory(
        self, memory_type: str, content: str, tags: Optional[List[str]] = None, **kwargs
    ) -> bool:
        """Add a new memory to the store"""
        try:
            # Create the memory instance
            memory = create_memory(memory_type, content, tags=tags or [], **kwargs)

            # Load existing memories
            memories = await self.load_memories()

            # Add the new memory
            memories.append(memory)

            # Save updated memories
            success = await self.save_memories(memories)

            if success:
                logger.debug("Added %s memory: %s...", memory_type, content[:50])

            return success

        except (ValueError, TypeError, KeyError) as e:
            logger.error("Failed to add memory: %s", e)
            return False

    async def remove_memory(self, memory_id: str) -> bool:
        """Remove a memory by ID"""
        try:
            memories = await self.load_memories()

            # Find and remove the memory
            initial_count = len(memories)
            memories = [m for m in memories if m.id != memory_id]

            if len(memories) < initial_count:
                success = await self.save_memories(memories)
                if success:
                    logger.debug("Removed memory with ID: %s", memory_id)
                return success
            else:
                logger.warning("Memory with ID %s not found", memory_id)
                return False

        except (OSError, ValueError, TypeError) as e:
            logger.error("Failed to remove memory %s: %s", memory_id, e)
            return False

    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory's content or metadata"""
        try:
            memories = await self.load_memories()

            # Find and update the memory
            for memory in memories:
                if memory.id == memory_id:
                    # Update memory attributes
                    for key, value in updates.items():
                        if hasattr(memory, key):
                            setattr(memory, key, value)

                    # Save updated memories
                    success = await self.save_memories(memories)
                    if success:
                        logger.debug("Updated memory %s", memory_id)
                    return success

            logger.warning("Memory with ID %s not found for update", memory_id)
            return False

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to update memory %s: %s", memory_id, e)
            return False

    async def get_memory_by_id(self, memory_id: str) -> Optional[MemoryType]:
        """Get a specific memory by its ID"""
        try:
            memories = await self.load_memories()

            for memory in memories:
                if memory.id == memory_id:
                    return memory

            return None

        except (OSError, ValueError, TypeError) as e:
            logger.error("Failed to get memory %s: %s", memory_id, e)
            return None

    async def get_memories_by_category(self, category: str) -> List[MemoryType]:
        """Get all memories of a specific category"""
        try:
            memories = await self.load_memories()
            return [m for m in memories if m.get_category().value == category]

        except (OSError, ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to get memories by category %s: %s", category, e)
            return []

    async def get_memories_by_tags(
        self, tags: List[str], match_all: bool = False
    ) -> List[MemoryType]:
        """Get memories that match the given tags"""
        try:
            memories = await self.load_memories()

            if match_all:
                # Memory must have ALL specified tags
                return [m for m in memories if all(tag in m.tags for tag in tags)]
            else:
                # Memory must have ANY of the specified tags
                return [m for m in memories if any(tag in m.tags for tag in tags)]

        except (OSError, ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to get memories by tags %s: %s", tags, e)
            return []

    async def cleanup_expired_memories(self) -> int:
        """Remove expired temporary memories and return count of removed memories"""
        try:
            memories = await self.load_memories()
            initial_count = len(memories)

            # Filter out expired memories
            active_memories = []
            for memory in memories:
                if isinstance(memory, TemporaryMemory) and memory.is_expired():
                    continue
                active_memories.append(memory)

            removed_count = initial_count - len(active_memories)

            if removed_count > 0:
                await self.save_memories(active_memories)
                logger.info("Cleaned up %d expired memories", removed_count)

            return removed_count

        except (OSError, ValueError, TypeError) as e:
            logger.error("Failed to cleanup expired memories: %s", e)
            return 0

    async def _cache_memories(self, memories: List[MemoryType]) -> None:
        """Cache memories in the cache provider"""
        if not (
            hasattr(self.config_manager, "cache_provider") and self.config_manager.cache_provider
        ):
            return

        try:
            memories_data = [memory.to_dict() for memory in memories]
            await self.config_manager.cache_provider.set(
                self.MEMORY_KEY, memories_data, ttl=self.config_manager.config.storage.cache_ttl
            )
        except (OSError, ValueError, TypeError) as e:
            logger.debug("Failed to cache memories: %s", e)

    def _create_default_context(self) -> Dict[str, Any]:
        """Create default project context"""
        return {
            "workspace": {
                "root": str(self.workspace_root),
                "name": self.workspace_root.name,
                "type": self._detect_project_type(),
                "initialized_at": datetime.now().isoformat(),
            },
            "structure": {},
            "dependencies": {},
            "quality_metrics": {
                "overall_score": 0,
                "files_reviewed": 0,
                "issues_found": 0,
                "improvements_made": 0,
            },
            "patterns": [],
            "known_issues": [],
            "improvements_made": [],
            "file_access": {},
            "last_updated": datetime.now().isoformat(),
        }

    def _detect_project_type(self) -> str:
        """Detect project type from marker files"""
        indicators = {
            "python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
            "javascript": ["package.json"],
            "typescript": ["tsconfig.json"],
            "go": ["go.mod"],
            "rust": ["Cargo.toml"],
            "java": ["pom.xml", "build.gradle"],
        }

        for lang, files in indicators.items():
            if any((self.workspace_root / f).exists() for f in files):
                return lang

        return "unknown"

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories"""
        try:
            memories = await self.load_memories()

            # Count by category
            category_counts: Dict[str, int] = {}
            for memory in memories:
                category = memory.get_category().value
                category_counts[category] = category_counts.get(category, 0) + 1

            # Count by type
            type_counts: Dict[str, int] = {}
            for memory in memories:
                mem_type = memory.get_type_name()
                type_counts[mem_type] = type_counts.get(mem_type, 0) + 1

            # Find oldest and newest
            oldest: Optional[str] = None
            newest: Optional[str] = None
            if memories:
                timestamps = [datetime.fromisoformat(m.timestamp) for m in memories]
                oldest = min(timestamps).isoformat()
                newest = max(timestamps).isoformat()

            return {
                "total_memories": len(memories),
                "category_counts": category_counts,
                "type_counts": type_counts,
                "oldest_memory": oldest,
                "newest_memory": newest,
                "storage_file": str(self.memories_file),
                "max_memories": self.max_memories,
            }

        except (OSError, ValueError, TypeError) as e:
            logger.error("Failed to get memory stats: %s", e)
            return {"error": str(e)}

    async def _cache_operation(self, operation: str, key: str, value: Any = None):
        """Perform cache operation with fallback handling"""
        try:
            cache = getattr(self.config_manager, "cache_provider", None)
            if not cache:
                # No cache available - operation succeeds silently
                return True

            if operation == "get":
                return await cache.get(key)
            elif operation == "set" and value is not None:
                return await cache.set(key, value)
            elif operation == "delete":
                return await cache.delete(key)
            else:
                return None

        except (OSError, ValueError, TypeError, AttributeError) as e:
            logger.debug("Cache operation %s failed for key %s: %s", operation, key, e)
            return None

    async def search_memories(
        self, query: str, memory_type: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> List[MemoryType]:
        """Search memories with proper null handling"""
        try:
            # Handle None tags parameter properly
            search_tags = tags or []

            return await self._perform_memory_search(query, memory_type, search_tags)

        except (ValueError, TypeError) as e:
            logger.error("Memory search failed: %s", e)
            return []

    async def _perform_memory_search(
        self, query: str, memory_type: Optional[str], tags: List[str]
    ) -> List[MemoryType]:
        """Internal method to perform memory search with proper types"""
        # Implementation would go here
        # For now, return empty list as placeholder
        _ = query, memory_type, tags  # Mark parameters as intentionally unused
        return []
