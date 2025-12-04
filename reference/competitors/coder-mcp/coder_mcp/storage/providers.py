#!/usr/bin/env python3
"""
Storage Provider Abstractions
Decoupled from specific vendors for better testability and flexibility
"""

import asyncio
import hashlib
import json
import logging
import math
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import numpy as np
from redis.commands.search.query import Query

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from openai import OpenAI


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""

    @abstractmethod
    async def create_embedding(self, text: str) -> Optional[List[float]]:
        """Create an embedding vector for the given text"""

    @abstractmethod
    def get_dimensions(self) -> int:
        """Get the dimensionality of embeddings"""

    @abstractmethod
    def get_max_tokens(self) -> int:
        """Get maximum token limit for input text"""


class VectorStoreProvider(ABC):
    """Abstract base class for vector storage providers"""

    @abstractmethod
    async def store_vector(
        self,
        doc_id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        namespace: str = "default",
    ) -> bool:
        """Store a vector with metadata in a specific namespace"""

    @abstractmethod
    async def search_vectors(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[str] = None,
        namespace: str = "default",
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in a specific namespace"""

    @abstractmethod
    async def delete_vector(self, doc_id: str, namespace: str = "default") -> bool:
        """Delete a vector by document ID from a specific namespace"""

    @abstractmethod
    async def get_stats(self, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get vector store statistics for a specific namespace or all namespaces"""

    async def add_vectors(
        self, vectors: List[Tuple[str, List[float], Dict[str, Any]]], namespace: str = "default"
    ) -> bool:
        """Batch store multiple vectors. Default implementation calls store_vector for each."""
        try:
            for doc_id, embedding, metadata in vectors:
                success = await self.store_vector(doc_id, embedding, metadata, namespace)
                if not success:
                    logger.warning(f"Failed to store vector {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add vectors: {e}")
            return False

    async def upsert(self, vectors: List[Dict[str, Any]], namespace: str = "default") -> bool:
        """Upsert vectors in Pinecone-style format. Adapts to store_vector."""
        try:
            for vector_data in vectors:
                doc_id = vector_data.get("id")
                embedding = vector_data.get("values")
                metadata = vector_data.get("metadata", {})

                if doc_id and embedding:
                    success = await self.store_vector(doc_id, embedding, metadata, namespace)
                    if not success:
                        logger.warning(f"Failed to upsert vector {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")
            return False

    async def get_vector(self, doc_id: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Get a specific vector by ID. Default implementation returns None."""
        return None


class CacheProvider(ABC):
    """Abstract base class for cache providers"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries"""


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider implementation"""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-large",
        dimensions: int = 3072,
        max_tokens: int = 8191,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions
        self.max_tokens = max_tokens
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> "OpenAI":
        """Lazy initialize OpenAI client"""
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self.api_key)
            except ImportError as exc:
                raise ImportError("openai package required for OpenAI provider") from exc
        return self._client

    async def create_embedding(self, text: str) -> Optional[List[float]]:
        """Create embedding using OpenAI API"""
        try:
            client = self._get_client()
            # Truncate if too long
            if len(text) > self.max_tokens:
                text = text[: self.max_tokens]
                logger.warning("Text truncated to %d characters", self.max_tokens)
            response = client.embeddings.create(
                model=self.model, input=text, dimensions=self.dimensions
            )
            return response.data[0].embedding
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Failed to create embedding: %s", e)
            return None

    def get_dimensions(self) -> int:
        return self.dimensions

    def get_max_tokens(self) -> int:
        return self.max_tokens


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local/mock embedding provider for testing"""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions
        self.max_tokens = 512

    async def create_embedding(self, text: str) -> Optional[List[float]]:
        """Create a simple hash-based embedding for testing"""
        try:
            hash_obj = hashlib.md5(text.encode("utf-8"), usedforsecurity=False)
        except TypeError:
            hash_obj = hashlib.md5(text.encode("utf-8"))  # nosec B324
        hash_bytes = hash_obj.digest()
        embedding = []
        for i in range(self.dimensions):
            byte_val = hash_bytes[i % len(hash_bytes)]
            float_val = (byte_val / 127.5) - 1.0  # Scale to [-1, 1]
            embedding.append(float_val)
        return embedding

    def get_dimensions(self) -> int:
        return self.dimensions

    def get_max_tokens(self) -> int:
        return self.max_tokens


class RedisVectorStore(VectorStoreProvider):
    """Redis vector store implementation with namespace support"""

    def __init__(self, redis_client: Any, index_name: str, prefix: str = "mcp:doc:") -> None:
        self.redis_client = redis_client
        self.index_name = index_name
        self.base_prefix = prefix
        # Store different namespaces as separate indexes or with prefixes
        self.namespace_indexes: dict[str, dict] = {}

    def _get_key(self, doc_id: str, namespace: str = "default") -> str:
        """Get the Redis key for a document in a specific namespace"""
        return f"{self.base_prefix}{namespace}:{doc_id}"

    def _get_index_name(self, namespace: str = "default") -> str:
        """Get the index name for a specific namespace"""
        if namespace == "default":
            return self.index_name
        return f"{self.index_name}_{namespace}"

    async def store_vector(
        self,
        doc_id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        namespace: str = "default",
    ) -> bool:
        """Store vector in Redis with metadata in a specific namespace"""
        try:
            # Convert embedding to bytes
            embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()

            # Add namespace to metadata
            metadata_with_ns = metadata.copy()
            metadata_with_ns["namespace"] = namespace

            # Prepare document data
            doc_data = {
                "embedding": embedding_bytes,
                "content": metadata.get("content", "").encode("utf-8"),
                "file_path": metadata.get("file_path", "").encode("utf-8"),
                "file_type": metadata.get("file_type", "unknown").encode("utf-8"),
                "file_size": metadata.get("file_size", 0),
                "timestamp": int(time.time()),
                "project": metadata.get("project", "").encode("utf-8"),
                "quality_score": metadata.get("quality_score", 0),
                "namespace": namespace.encode("utf-8"),
                # Add memory-specific fields
                "memory_type": metadata.get("memory_type", "").encode("utf-8"),
                "tags": json.dumps(metadata.get("tags", [])).encode("utf-8"),
            }

            # Store in Redis with namespace-specific key
            key = self._get_key(doc_id, namespace)
            self.redis_client.hset(key, mapping=doc_data)

            logger.debug(f"Stored vector for document: {doc_id} in namespace: {namespace}")
            return True

        except Exception as e:
            logger.error("Failed to store vector: %s", e)
            return False

    async def search_vectors(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[str] = None,
        namespace: str = "default",
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in Redis within a specific namespace"""
        try:
            # Convert query embedding to bytes
            query_bytes = np.array(query_embedding, dtype=np.float32).tobytes()

            # Add namespace filter
            namespace_filter = f"@namespace:[{namespace} {namespace}]"
            if filters:
                combined_filters = f"({filters}) {namespace_filter}"
            else:
                combined_filters = namespace_filter

            # Build query
            base_query = f"*=>[KNN {top_k} @embedding $vec AS score]"
            full_query = f"{combined_filters} {base_query}"

            q = Query(full_query).sort_by("score").paging(0, top_k).dialect(2)

            # Try to search with the namespace-aware query
            try:
                results = self.redis_client.ft(self.index_name).search(
                    q, query_params={"vec": query_bytes}
                )
                return self._parse_redis_search_results(results, namespace)
            except Exception as e:
                # If namespace filtering fails, fall back to post-filtering
                logger.debug(f"Namespace filtering failed, using post-filtering: {e}")

                # Search without namespace filter
                base_query = f"*=>[KNN {top_k * 2} @embedding $vec AS score]"
                if filters:
                    base_query = f"{filters} {base_query}"

                q = Query(base_query).sort_by("score").paging(0, top_k * 2).dialect(2)
                results = self.redis_client.ft(self.index_name).search(
                    q, query_params={"vec": query_bytes}
                )

                # Post-filter results by namespace
                all_results = self._parse_redis_search_results(results, namespace)
                filtered_results = [
                    r
                    for r in all_results
                    if r.get("metadata", {}).get("namespace", "default") == namespace
                ]
                return filtered_results[:top_k]

        except Exception as e:
            logger.error("Vector search failed: %s", e)
            return []

    def _parse_redis_search_results(self, results: Any, namespace: str) -> List[Dict[str, Any]]:
        """Helper to parse Redis search results into the expected format"""
        parsed_results: List[Dict[str, Any]] = []
        for doc in getattr(results, "docs", []):
            if not self._is_in_namespace(doc, namespace):
                continue
            result = self._extract_base_fields(doc)
            self._extract_content_fields(doc, result)
            self._extract_metadata_fields(doc, result)
            self._extract_numeric_fields(doc, result)
            parsed_results.append(result)
        return parsed_results

    def _is_in_namespace(self, doc, namespace: str) -> bool:
        doc_namespace = self._safe_decode(getattr(doc, "namespace", "default"))
        return namespace == "all" or doc_namespace == namespace

    def _extract_base_fields(self, doc) -> Dict[str, Any]:
        return {
            "id": doc.id,
            "score": float(getattr(doc, "score", 0.0)),
            "metadata": {"namespace": self._safe_decode(getattr(doc, "namespace", "default"))},
        }

    def _extract_content_fields(self, doc, result: Dict[str, Any]):
        if hasattr(doc, "content"):
            result["content"] = self._safe_decode(doc.content)
            result["metadata"]["content"] = result["content"]
        if hasattr(doc, "file_path"):
            result["file_path"] = self._safe_decode(doc.file_path)
            result["metadata"]["file_path"] = result["file_path"]

    def _extract_metadata_fields(self, doc, result: Dict[str, Any]):
        for field in ["file_type", "project", "memory_type"]:
            if hasattr(doc, field):
                result["metadata"][field] = self._safe_decode(getattr(doc, field))
        if hasattr(doc, "tags"):
            try:
                tags_str = self._safe_decode(doc.tags)
                result["metadata"]["tags"] = json.loads(tags_str) if tags_str else []
            except json.JSONDecodeError:
                result["metadata"]["tags"] = []

    def _extract_numeric_fields(self, doc, result: Dict[str, Any]):
        for field in ["file_size", "timestamp", "quality_score"]:
            if hasattr(doc, field):
                try:
                    result["metadata"][field] = float(getattr(doc, field))
                except Exception:
                    result["metadata"][field] = 0

    async def delete_vector(self, doc_id: str, namespace: str = "default") -> bool:
        """Delete vector from Redis in a specific namespace"""
        try:
            key = self._get_key(doc_id, namespace)
            deleted = self.redis_client.delete(key)
            return bool(deleted > 0)
        except Exception as e:
            logger.error("Failed to delete vector: %s", e)
            return False

    async def get_stats(self, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get Redis vector store statistics for a specific namespace or all"""
        try:
            info = self.redis_client.ft(self.index_name).info()
            stats = {
                "num_docs": info.get("num_docs", 0),
                "num_terms": info.get("num_terms", 0),
                "max_doc_id": info.get("max_doc_id", 0),
                "index_name": self.index_name,
            }

            # If namespace specified, count docs in that namespace
            if namespace:
                pattern = self._get_key("*", namespace)
                namespace_keys = self.redis_client.keys(pattern)
                stats["namespace_docs"] = len(namespace_keys)
                stats["namespace"] = namespace

            return stats
        except Exception as e:
            logger.error("Failed to get vector store stats: %s", e)
            return None

    async def get_vector(self, doc_id: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Get a specific vector by ID from a namespace"""
        try:
            key = self._get_key(doc_id, namespace)
            data = self.redis_client.hgetall(key)

            if not data:
                return None

            # Parse the data
            result = {
                "id": doc_id,
                "vector": list(np.frombuffer(data.get(b"embedding", b""), dtype=np.float32)),
                "metadata": {
                    "namespace": namespace,
                    "content": self._safe_decode(data.get(b"content", b"")),
                    "file_path": self._safe_decode(data.get(b"file_path", b"")),
                    "file_type": self._safe_decode(data.get(b"file_type", b"")),
                    "memory_type": self._safe_decode(data.get(b"memory_type", b"")),
                },
            }

            # Parse tags
            if b"tags" in data:
                try:
                    tags_str = self._safe_decode(data[b"tags"])
                    metadata = (
                        dict(result["metadata"]) if isinstance(result["metadata"], dict) else {}
                    )
                    metadata["tags"] = json.loads(tags_str) if tags_str else []
                    result["metadata"] = metadata
                except json.JSONDecodeError:
                    metadata = (
                        dict(result["metadata"]) if isinstance(result["metadata"], dict) else {}
                    )
                    metadata["tags"] = []
                    result["metadata"] = metadata

            return result

        except Exception as e:
            logger.error(f"Failed to get vector {doc_id}: {e}")
            return None

    def _safe_decode(self, value: Any) -> str:
        """Safely decode bytes to string"""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        elif isinstance(value, str):
            return value
        else:
            return str(value)


class MemoryVectorStore(VectorStoreProvider):
    """In-memory vector store for testing with namespace support"""

    def __init__(self) -> None:
        # Store vectors by namespace
        self.namespaces: Dict[str, Dict[str, List[float]]] = {"default": {}}
        self.metadata: Dict[str, Dict[str, Dict[str, Any]]] = {"default": {}}

    def _ensure_namespace(self, namespace: str) -> None:
        """Ensure a namespace exists"""
        if namespace not in self.namespaces:
            self.namespaces[namespace] = {}
            self.metadata[namespace] = {}

    async def store_vector(
        self,
        doc_id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        namespace: str = "default",
    ) -> bool:
        """Store vector in memory in a specific namespace"""
        try:
            self._ensure_namespace(namespace)
            self.namespaces[namespace][doc_id] = embedding
            # Add namespace to metadata
            metadata_with_ns = metadata.copy()
            metadata_with_ns["namespace"] = namespace
            self.metadata[namespace][doc_id] = metadata_with_ns
            return True
        except Exception as e:
            logger.error("Failed to store vector in memory: %s", e)
            return False

    async def search_vectors(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[str] = None,
        namespace: str = "default",
    ) -> List[Dict[str, Any]]:
        """Search vectors using cosine similarity within a namespace"""
        try:
            self._ensure_namespace(namespace)

            if not self.namespaces[namespace]:
                return []

            # Calculate cosine similarity for each vector in the namespace
            similarities = []
            for doc_id, embedding in self.namespaces[namespace].items():
                similarity = self._cosine_similarity(query_embedding, embedding)
                similarities.append((doc_id, similarity))

            # Sort by similarity and take top_k
            similarities.sort(key=lambda x: x[1], reverse=True)

            results = []
            for doc_id, score in similarities[:top_k]:
                metadata = self.metadata[namespace].get(doc_id, {})
                result = {"id": doc_id, "score": score, "metadata": metadata}

                # Add content and file_path to top level for compatibility
                if "content" in metadata:
                    result["content"] = metadata["content"]
                if "file_path" in metadata:
                    result["file_path"] = metadata["file_path"]

                results.append(result)

            return results

        except Exception as e:
            logger.error("Memory vector search failed: %s", e)
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Calculate dot product
            dot_product = sum(a * b for a, b in zip(vec1, vec2))

            # Calculate magnitudes
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(a * a for a in vec2))

            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0

            return dot_product / (magnitude1 * magnitude2)
        except Exception:
            return 0.0

    async def delete_vector(self, doc_id: str, namespace: str = "default") -> bool:
        """Delete vector from memory in a specific namespace"""
        try:
            self._ensure_namespace(namespace)
            if doc_id in self.namespaces[namespace]:
                del self.namespaces[namespace][doc_id]
            if doc_id in self.metadata[namespace]:
                del self.metadata[namespace][doc_id]
            return True
        except Exception as e:
            logger.error("Failed to delete vector from memory: %s", e)
            return False

    async def get_stats(self, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get memory vector store statistics"""
        if namespace:
            self._ensure_namespace(namespace)
            return {
                "num_docs": len(self.namespaces.get(namespace, {})),
                "namespace": namespace,
                "index_name": "memory",
                "storage_type": "in-memory",
            }
        else:
            total_docs = sum(len(docs) for docs in self.namespaces.values())
            return {
                "num_docs": total_docs,
                "namespaces": list(self.namespaces.keys()),
                "docs_by_namespace": {ns: len(docs) for ns, docs in self.namespaces.items()},
                "index_name": "memory",
                "storage_type": "in-memory",
            }

    async def get_vector(self, doc_id: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Get a specific vector by ID from a namespace"""
        try:
            self._ensure_namespace(namespace)
            if doc_id not in self.namespaces[namespace]:
                return None

            return {
                "id": doc_id,
                "vector": self.namespaces[namespace][doc_id],
                "metadata": self.metadata[namespace].get(doc_id, {}),
            }
        except Exception as e:
            logger.error(f"Failed to get vector {doc_id}: {e}")
            return None


class RedisCacheProvider(CacheProvider):
    """Redis cache implementation with proper async support and bytes handling"""

    def __init__(self, redis_client: Any, prefix: str = "mcp:cache:") -> None:
        self.redis_client = redis_client
        self.prefix = prefix
        self._executor = None  # Will use default executor

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._sync_get, key)

    def _sync_get(self, key: str) -> Optional[Any]:
        """Synchronous get operation"""
        try:
            redis_key = f"{self.prefix}{key}"
            value = self.redis_client.get(redis_key)
            if value:
                # Decode bytes to string if needed
                if isinstance(value, bytes):
                    value = value.decode("utf-8")
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value  # Return raw value if not JSON
            return None
        except Exception as e:
            logger.error("Redis cache get failed: %s", e)
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._sync_set, key, value, ttl)

    def _sync_set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Synchronous set operation"""
        try:
            redis_key = f"{self.prefix}{key}"

            # Convert value to string format
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
            elif isinstance(value, str):
                value_str = value
            else:
                value_str = str(value)

            # Store as string (will be encoded to bytes by Redis)
            if ttl:
                self.redis_client.setex(redis_key, ttl, value_str)
            else:
                self.redis_client.set(redis_key, value_str)

            return True
        except Exception as e:
            logger.error("Redis cache set failed: %s", e)
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._sync_delete, key)

    def _sync_delete(self, key: str) -> bool:
        """Synchronous delete operation"""
        try:
            redis_key = f"{self.prefix}{key}"
            deleted = self.redis_client.delete(redis_key)
            return bool(deleted > 0)
        except Exception as e:
            logger.error("Redis cache delete failed: %s", e)
            return False

    async def clear(self) -> bool:
        """Clear all cache entries with prefix"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._sync_clear)

    def _sync_clear(self) -> bool:
        """Synchronous clear operation"""
        try:
            pattern = f"{self.prefix}*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error("Redis cache clear failed: %s", e)
            return False
