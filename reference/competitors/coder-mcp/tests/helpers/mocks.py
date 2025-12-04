"""
Comprehensive mock utilities for coder-mcp tests.

This module provides realistic mocks for all major components of the MCP server,
including Redis, OpenAI, embedding providers, vector stores, and the MCP server itself.
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from unittest.mock import AsyncMock, Mock

import numpy as np


class MockMCPServer:
    """Mock MCP server with realistic tool handling."""

    def __init__(self):
        self.is_initialized = False
        self.tool_handlers = Mock()
        self.tool_handlers.handlers = {}
        self.health_status = "healthy"
        self.call_count = 0
        self.last_call_time = None

        # Setup default tool handlers
        self._setup_default_handlers()

    def _setup_default_handlers(self):
        """Setup default tool response handlers."""
        self.tool_handlers.handlers.update(
            {
                "read_file": AsyncMock(
                    return_value={"content": "mock file content", "lines": 10, "size": 100}
                ),
                "write_file": AsyncMock(return_value={"success": True, "bytes_written": 100}),
                "list_files": AsyncMock(
                    return_value={"files": ["file1.py", "file2.py"], "count": 2}
                ),
                "search_files": AsyncMock(
                    return_value={
                        "matches": [{"file": "test.py", "line": 10, "content": "match"}],
                        "total": 1,
                    }
                ),
                "analyze_code": AsyncMock(
                    return_value={
                        "quality_score": 8.5,
                        "issues": [],
                        "metrics": {"complexity": 5, "maintainability": 9},
                    }
                ),
                "get_context": AsyncMock(
                    return_value={"context": "mock context data", "relevance": 0.95}
                ),
            }
        )

    async def initialize(self):
        """Initialize the mock server."""
        await asyncio.sleep(0.01)  # Simulate initialization time
        self.is_initialized = True

    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a tool call with mock response."""
        self.call_count += 1
        self.last_call_time = datetime.now()

        if not self.is_initialized:
            raise RuntimeError("Server not initialized")

        if tool_name in self.tool_handlers.handlers:
            handler = self.tool_handlers.handlers[tool_name]
            return await handler(arguments)
        else:
            # Return a generic response for unknown tools
            return {
                "tool": tool_name,
                "arguments": arguments,
                "result": "mock_result",
                "success": True,
            }

    def get_health_status(self) -> Dict[str, Any]:
        """Get server health status."""
        return {
            "status": self.health_status,
            "initialized": self.is_initialized,
            "uptime": 3600,  # Mock uptime
            "call_count": self.call_count,
            "last_call": self.last_call_time.isoformat() if self.last_call_time else None,
        }


class MockRedisClient:
    """Mock Redis client with comprehensive operation support."""

    def __init__(self, initial_data: Dict[str, Any] = None):
        self._data = initial_data or {}
        self._hashes = {}
        self._sorted_sets = {}
        self._expiry = {}
        self._last_access = {}

    # String operations
    async def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        self._update_access(key)
        if key in self._expiry and time.time() > self._expiry[key]:
            del self._data[key]
            del self._expiry[key]
            return None
        return self._data.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set a key-value pair with optional expiry."""
        self._data[key] = value
        self._update_access(key)
        if ex:
            self._expiry[key] = time.time() + ex
        return True

    async def delete(self, key: str) -> int:
        """Delete a key."""
        if key in self._data:
            del self._data[key]
            self._expiry.pop(key, None)
            self._last_access.pop(key, None)
            return 1
        return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if key in self._expiry and time.time() > self._expiry[key]:
            del self._data[key]
            del self._expiry[key]
            return False
        return key in self._data

    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern."""
        if pattern == "*":
            return list(self._data.keys())
        # Simple pattern matching (could be enhanced)
        import fnmatch

        return [k for k in self._data.keys() if fnmatch.fnmatch(k, pattern)]

    # Hash operations
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value."""
        return self._hashes.get(name, {}).get(key)

    async def hset(self, name: str, key: str, value: str) -> int:
        """Set hash field value."""
        if name not in self._hashes:
            self._hashes[name] = {}
        old_value = self._hashes[name].get(key)
        self._hashes[name][key] = value
        return 0 if old_value else 1

    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields."""
        return self._hashes.get(name, {})

    async def hdel(self, name: str, key: str) -> int:
        """Delete hash field."""
        if name in self._hashes and key in self._hashes[name]:
            del self._hashes[name][key]
            return 1
        return 0

    # Sorted set operations
    async def zadd(self, name: str, mapping: Dict[str, float]) -> int:
        """Add members to sorted set."""
        if name not in self._sorted_sets:
            self._sorted_sets[name] = {}
        added = 0
        for member, score in mapping.items():
            if member not in self._sorted_sets[name]:
                added += 1
            self._sorted_sets[name][member] = score
        return added

    async def zrange(
        self, name: str, start: int, end: int, withscores: bool = False
    ) -> List[Union[str, tuple]]:
        """Get sorted set range."""
        if name not in self._sorted_sets:
            return []

        # Sort by score then by member name
        sorted_members = sorted(self._sorted_sets[name].items(), key=lambda x: (x[1], x[0]))

        selected = sorted_members[start : end + 1 if end != -1 else None]

        if withscores:
            return [(member, score) for member, score in selected]
        else:
            return [member for member, score in selected]

    # TTL operations
    async def ttl(self, key: str) -> int:
        """Get time to live for key."""
        if key not in self._data:
            return -2
        if key not in self._expiry:
            return -1
        remaining = self._expiry[key] - time.time()
        return max(0, int(remaining))

    def _update_access(self, key: str):
        """Update last access time for key."""
        self._last_access[key] = time.time()

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis mock statistics."""
        return {
            "total_keys": len(self._data),
            "hash_keys": len(self._hashes),
            "sorted_sets": len(self._sorted_sets),
            "keys_with_expiry": len(self._expiry),
            "memory_usage": sum(len(str(v)) for v in self._data.values()),
        }


class MockContextManager:
    """Mock context manager for file and project context."""

    def __init__(self):
        self.indexed_files = {}
        self.project_info = {
            "name": "test-project",
            "type": "python",
            "files_count": 42,
            "last_indexed": datetime.now().isoformat(),
        }
        self.search_results = []

    async def get_context(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Get context for a query."""
        return {
            "query": query,
            "results": self.search_results[:max_results],
            "total": len(self.search_results),
            "relevance_threshold": 0.7,
        }

    async def index_file(self, file_path: str, content: str) -> bool:
        """Index a file for search."""
        self.indexed_files[file_path] = {
            "content": content,
            "indexed_at": datetime.now().isoformat(),
            "size": len(content),
            "lines": content.count("\n") + 1,
        }
        return True

    async def search_similar(self, query: str, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar content."""
        # Mock similarity search
        results = []
        for file_path, file_info in self.indexed_files.items():
            # Simple keyword matching for mock - search in content, not filename
            if any(word.lower() in file_info["content"].lower() for word in query.split()):
                results.append(
                    {
                        "file": file_path,
                        "similarity": 0.85,  # Mock similarity score
                        "snippet": file_info["content"][:200] + "...",
                        "lines": file_info["lines"],
                    }
                )
        return results

    def get_project_metrics(self) -> Dict[str, Any]:
        """Get project metrics."""
        return {
            "files_indexed": len(self.indexed_files),
            "total_lines": sum(info["lines"] for info in self.indexed_files.values()),
            "total_size": sum(info["size"] for info in self.indexed_files.values()),
            "project_info": self.project_info,
        }


class MockOpenAIClient:
    """Mock OpenAI client with embeddings and chat completions."""

    def __init__(self):
        self.usage_stats = {"total_tokens": 0, "embedding_requests": 0, "chat_requests": 0}

    async def create_embedding(
        self, text: str, model: str = "text-embedding-ada-002"
    ) -> Dict[str, Any]:
        """Create embeddings for text."""
        self.usage_stats["embedding_requests"] += 1
        self.usage_stats["total_tokens"] += len(text.split())

        # Generate deterministic embedding based on text hash
        text_hash = hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()
        np.random.seed(int(text_hash[:8], 16))
        embedding = np.random.normal(0, 1, 1536).tolist()

        return {
            "object": "list",
            "data": [{"object": "embedding", "index": 0, "embedding": embedding}],
            "model": model,
            "usage": {"prompt_tokens": len(text.split()), "total_tokens": len(text.split())},
        }

    async def create_chat_completion(
        self, messages: List[Dict], model: str = "gpt-4"
    ) -> Dict[str, Any]:
        """Create chat completion."""
        self.usage_stats["chat_requests"] += 1

        # Extract context from messages
        user_message = next((msg["content"] for msg in messages if msg["role"] == "user"), "")
        user_message_lower = user_message.lower()

        # Generate contextual response based on message content
        if any(
            keyword in user_message_lower for keyword in ["error", "bug", "exception", "traceback"]
        ):
            response_content = (
                "I can help you debug this error. Let me analyze the issue and provide a solution."
            )
        elif any(
            keyword in user_message_lower
            for keyword in ["code", "example", "show", "implement", "write"]
        ):
            response_content = (
                "Here's an example implementation:\n\n```python\ndef example():\n    pass\n```"
            )
        elif any(keyword in user_message_lower for keyword in ["explain", "how", "what", "why"]):
            response_content = (
                "Let me explain this concept step by step to help you understand it better."
            )
        else:
            response_content = (
                "I understand your request. Here's my response based on the context provided."
            )

        total_tokens = sum(len(msg["content"].split()) for msg in messages) + len(
            response_content.split()
        )
        self.usage_stats["total_tokens"] += total_tokens

        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": response_content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": sum(len(msg["content"].split()) for msg in messages),
                "completion_tokens": len(response_content.split()),
                "total_tokens": total_tokens,
            },
        }

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return self.usage_stats.copy()


class MockEmbeddingProvider:
    """Mock embedding provider with deterministic results."""

    def __init__(self, dimensions: int = 1536):
        self.dimensions = dimensions
        self.cache = {}
        self.call_count = 0

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            if text in self.cache:
                embeddings.append(self.cache[text])
            else:
                embedding = self._generate_embedding(text)
                self.cache[text] = embedding
                embeddings.append(embedding)

        self.call_count += 1
        return embeddings

    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding for single text."""
        embeddings = await self.create_embeddings([text])
        return embeddings[0]

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate deterministic embedding based on text."""
        # Use text hash for deterministic results
        text_hash = hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()
        np.random.seed(int(text_hash[:8], 16))

        # Generate normalized embedding
        embedding = np.random.normal(0, 1, self.dimensions)
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.tolist()

    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics."""
        return {
            "dimensions": self.dimensions,
            "cached_embeddings": len(self.cache),
            "total_calls": self.call_count,
        }


class MockVectorStore:
    """Mock vector store with similarity search."""

    def __init__(self, dimensions: int = 1536):
        self.dimensions = dimensions
        self.vectors = {}
        self.metadata = {}

    async def add_vector(
        self, vector_id: str, vector: List[float], metadata: Dict[str, Any] = None
    ):
        """Add a vector to the store."""
        if len(vector) != self.dimensions:
            raise ValueError(f"Vector must have {self.dimensions} dimensions")

        self.vectors[vector_id] = np.array(vector)
        self.metadata[vector_id] = metadata or {}

    async def add_vectors(
        self, vectors: Dict[str, List[float]], metadata: Dict[str, Dict[str, Any]] = None
    ):
        """Add multiple vectors to the store."""
        for vector_id, vector in vectors.items():
            await self.add_vector(vector_id, vector, (metadata or {}).get(vector_id))

    async def search_similar(
        self, query_vector: List[float], top_k: int = 10, threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        if len(query_vector) != self.dimensions:
            raise ValueError(f"Query vector must have {self.dimensions} dimensions")

        query_np = np.array(query_vector)
        similarities = []

        for vector_id, vector in self.vectors.items():
            # Calculate cosine similarity
            query_norm = np.linalg.norm(query_np)
            vector_norm = np.linalg.norm(vector)

            if query_norm == 0 or vector_norm == 0:
                similarity = 0.0
            else:
                similarity = np.dot(query_np, vector) / (query_norm * vector_norm)

            if similarity >= threshold:
                similarities.append(
                    {
                        "id": vector_id,
                        "similarity": float(similarity),
                        "metadata": self.metadata.get(vector_id, {}),
                    }
                )

        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:top_k]

    async def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from the store."""
        if vector_id in self.vectors:
            del self.vectors[vector_id]
            self.metadata.pop(vector_id, None)
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return {
            "total_vectors": len(self.vectors),
            "dimensions": self.dimensions,
            "memory_usage": sum(v.nbytes for v in self.vectors.values()) if self.vectors else 0,
        }


# Factory functions for easy creation


def create_mock_server() -> MockMCPServer:
    """Create a mock MCP server."""
    return MockMCPServer()


def create_mock_redis(initial_data: Dict[str, Any] = None) -> MockRedisClient:
    """Create a mock Redis client."""
    return MockRedisClient(initial_data)


def create_mock_context_manager() -> MockContextManager:
    """Create a mock context manager."""
    return MockContextManager()


def create_mock_openai_client() -> MockOpenAIClient:
    """Create a mock OpenAI client."""
    return MockOpenAIClient()


def create_mock_embedding_provider(dimensions: int = 1536) -> MockEmbeddingProvider:
    """Create a mock embedding provider."""
    return MockEmbeddingProvider(dimensions)


def create_mock_vector_store(dimensions: int = 1536) -> MockVectorStore:
    """Create a mock vector store."""
    return MockVectorStore(dimensions)


def create_full_mock_suite() -> Dict[str, Any]:
    """Create a complete suite of mocks."""
    return {
        "server": create_mock_server(),
        "redis": create_mock_redis(),
        "context_manager": create_mock_context_manager(),
        "openai": create_mock_openai_client(),
        "embedding_provider": create_mock_embedding_provider(),
        "vector_store": create_mock_vector_store(),
    }


# Preset configurations for common scenarios


def create_populated_redis() -> MockRedisClient:
    """Create a Redis client with common test data."""
    initial_data = {
        "user:123": json.dumps({"name": "Test User", "email": "test@example.com"}),
        "session:abc": "active",
        "cache:key1": "cached_value",
        "config:app": json.dumps({"debug": True, "version": "1.0.0"}),
    }
    return create_mock_redis(initial_data)


def create_indexed_context_manager() -> MockContextManager:
    """Create a context manager with pre-indexed files."""
    cm = create_mock_context_manager()

    # Pre-populate with common files (synchronously, no async tasks)
    # Note: These will be available immediately for testing
    cm.indexed_files["src/main.py"] = {
        "content": """
def main():
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
""",
        "indexed_at": datetime.now().isoformat(),
        "size": 75,
        "lines": 6,
    }

    cm.indexed_files["src/utils.py"] = {
        "content": """
def calculate_metrics(data):
    return {
        "count": len(data),
        "sum": sum(data) if data else 0
    }
""",
        "indexed_at": datetime.now().isoformat(),
        "size": 89,
        "lines": 5,
    }

    return cm


def create_trained_vector_store() -> MockVectorStore:
    """Create a vector store with pre-computed embeddings."""
    store = create_mock_vector_store()
    provider = create_mock_embedding_provider()

    # Pre-populate with sample vectors (synchronously)
    sample_texts = [
        "Python programming language",
        "Machine learning algorithms",
        "Web development framework",
        "Database optimization techniques",
        "API design patterns",
    ]

    # Generate embeddings and add vectors synchronously
    for i, text in enumerate(sample_texts):
        # Use the provider's internal method to generate deterministic embeddings
        embedding = provider._generate_embedding(text)
        store.vectors[f"doc_{i}"] = np.array(embedding)
        store.metadata[f"doc_{i}"] = {"text": text, "category": "tech"}

    return store
