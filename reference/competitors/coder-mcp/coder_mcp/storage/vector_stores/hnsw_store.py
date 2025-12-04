"""
HNSW Vector Store Implementation
High-performance approximate nearest neighbor search using HNSW algorithm
"""

import asyncio
import logging
import pickle
from typing import Any, Dict, List, Optional, Union

import numpy as np

from ..providers import VectorStoreProvider

logger = logging.getLogger(__name__)

try:
    import hnswlib

    HNSW_AVAILABLE = True
except ImportError:
    HNSW_AVAILABLE = False
    logger.warning("hnswlib not available. Install with: pip install hnswlib")


class HNSWVectorStore(VectorStoreProvider):
    """High-performance approximate nearest neighbor search using HNSW"""

    def __init__(
        self,
        dim: int,
        max_elements: int = 1000000,
        ef_construction: int = 200,
        M: int = 16,
        ef_search: int = 50,
        space: str = "cosine",
        redis_client: Optional[Any] = None,
    ):
        if not HNSW_AVAILABLE:
            raise ImportError(
                "hnswlib is required for HNSWVectorStore. Install with: pip install hnswlib"
            )

        self.dim = dim
        self.max_elements = max_elements
        self.ef_construction = ef_construction
        self.M = M
        self.ef_search = ef_search
        self.space = space
        self.redis_client = redis_client

        # Initialize HNSW index
        self.index = hnswlib.Index(space=space, dim=dim)
        self.index.init_index(max_elements=max_elements, ef_construction=ef_construction, M=M)
        self.index.set_ef(ef_search)

        # Store metadata separately
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.namespace_metadata: Dict[str, Dict[str, Dict[str, Any]]] = {"default": {}}

        # Track current size
        self.current_size = 0

    async def store_vector(
        self,
        doc_id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        namespace: str = "default",
    ) -> bool:
        """Store a vector with metadata in a specific namespace"""
        try:
            # Ensure namespace exists
            if namespace not in self.namespace_metadata:
                self.namespace_metadata[namespace] = {}

            # Convert doc_id to numeric ID for HNSW
            numeric_id = self._get_numeric_id(doc_id, namespace)

            # Add to HNSW index
            embedding_array = np.array(embedding, dtype=np.float32)
            if len(embedding_array) != self.dim:
                logger.warning(
                    f"Embedding dimension mismatch: expected {self.dim}, got {len(embedding_array)}"
                )
                # Pad or truncate as needed
                if len(embedding_array) < self.dim:
                    embedding_array = np.pad(embedding_array, (0, self.dim - len(embedding_array)))
                else:
                    embedding_array = embedding_array[: self.dim]

            self.index.add_items(embedding_array.reshape(1, -1), [numeric_id])

            # Store metadata with namespace
            metadata_with_ns = metadata.copy()
            metadata_with_ns["namespace"] = namespace
            metadata_with_ns["doc_id"] = doc_id

            self.namespace_metadata[namespace][doc_id] = metadata_with_ns
            self.metadata[str(numeric_id)] = metadata_with_ns

            self.current_size += 1

            # Persist to Redis if available
            if self.redis_client:
                await self._persist_to_redis(namespace)

            logger.debug(f"Stored vector for document: {doc_id} in namespace: {namespace}")
            return True

        except Exception as e:
            logger.error(f"Failed to store vector: {e}")
            return False

    async def search_vectors(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[str] = None,
        namespace: str = "default",
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors using HNSW"""
        try:
            if self.current_size == 0:
                return []

            query_array = self._prepare_query_array(query_embedding)
            candidates_k = self._get_candidates_k(top_k, filters, namespace)
            labels, distances = self.index.knn_query(query_array.reshape(1, -1), k=candidates_k)

            results = self._process_search_results(
                labels[0], distances[0], namespace, filters, top_k
            )
            return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

        except Exception as e:
            logger.error(f"HNSW vector search failed: {e}")
            return []

    def _prepare_query_array(self, query_embedding: List[float]) -> np.ndarray:
        """Prepare and normalize query embedding array"""
        query_array = np.array(query_embedding, dtype=np.float32)
        if len(query_array) != self.dim:
            if len(query_array) < self.dim:
                query_array = np.pad(query_array, (0, self.dim - len(query_array)))
            else:
                query_array = query_array[: self.dim]
        return query_array

    def _get_candidates_k(self, top_k: int, filters: Optional[str], namespace: str) -> int:
        """Calculate number of candidates needed for filtering"""
        return min(top_k * 3, self.current_size) if filters or namespace != "default" else top_k

    def _process_search_results(
        self,
        labels: List[int],
        distances: List[float],
        namespace: str,
        filters: Optional[str],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Process HNSW search results into formatted results"""
        results = []
        for label, distance in zip(labels, distances):
            metadata = self.metadata.get(str(label), {})

            if metadata.get("namespace", "default") != namespace:
                continue
            if filters and not self._matches_filters(metadata, filters):
                continue

            score = self._distance_to_score(distance)
            result = self._create_result_dict(metadata, label, score)
            results.append(result)

            if len(results) >= top_k:
                break
        return results

    def _distance_to_score(self, distance: float) -> float:
        """Convert distance to similarity score"""
        if self.space == "cosine":
            return 1 - distance
        elif self.space == "l2":
            return 1 / (1 + distance)
        else:
            return 1 - distance

    def _create_result_dict(
        self, metadata: Dict[str, Any], label: int, score: float
    ) -> Dict[str, Any]:
        """Create result dictionary with metadata"""
        result = {
            "id": metadata.get("doc_id", str(label)),
            "score": float(score),
            "metadata": metadata,
        }
        if "content" in metadata:
            result["content"] = metadata["content"]
        if "file_path" in metadata:
            result["file_path"] = metadata["file_path"]
        return result

    async def delete_vector(self, doc_id: str, namespace: str = "default") -> bool:
        """Delete a vector by document ID from a specific namespace"""
        try:
            if namespace not in self.namespace_metadata:
                return False

            if doc_id not in self.namespace_metadata[namespace]:
                return False

            # HNSW doesn't support deletion, so we just remove from metadata
            # In a production system, you might want to rebuild the index periodically
            del self.namespace_metadata[namespace][doc_id]

            # Find and remove from main metadata
            numeric_id = None
            for nid, meta in self.metadata.items():
                if meta.get("doc_id") == doc_id and meta.get("namespace") == namespace:
                    numeric_id = nid
                    break

            if numeric_id:
                del self.metadata[numeric_id]

            logger.debug(f"Deleted vector for document: {doc_id} from namespace: {namespace}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete vector: {e}")
            return False

    async def get_stats(self, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get HNSW vector store statistics"""
        try:
            if namespace:
                namespace_docs = len(self.namespace_metadata.get(namespace, {}))
                return {
                    "num_docs": namespace_docs,
                    "namespace": namespace,
                    "index_name": "hnsw",
                    "storage_type": "hnsw",
                    "dimensions": self.dim,
                    "max_elements": self.max_elements,
                    "ef_construction": self.ef_construction,
                    "M": self.M,
                    "ef_search": self.ef_search,
                    "space": self.space,
                }
            else:
                total_docs = sum(len(docs) for docs in self.namespace_metadata.values())
                return {
                    "num_docs": total_docs,
                    "current_size": self.current_size,
                    "namespaces": list(self.namespace_metadata.keys()),
                    "docs_by_namespace": {
                        ns: len(docs) for ns, docs in self.namespace_metadata.items()
                    },
                    "index_name": "hnsw",
                    "storage_type": "hnsw",
                    "dimensions": self.dim,
                    "max_elements": self.max_elements,
                    "ef_construction": self.ef_construction,
                    "M": self.M,
                    "ef_search": self.ef_search,
                    "space": self.space,
                }

        except Exception as e:
            logger.error(f"Failed to get HNSW stats: {e}")
            return None

    async def get_vector(self, doc_id: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Get a specific vector by ID from a namespace"""
        try:
            if namespace not in self.namespace_metadata:
                return None

            if doc_id not in self.namespace_metadata[namespace]:
                return None

            metadata = self.namespace_metadata[namespace][doc_id]

            # Find the numeric ID and get the vector
            numeric_id = None
            for nid, meta in self.metadata.items():
                if meta.get("doc_id") == doc_id and meta.get("namespace") == namespace:
                    numeric_id = int(nid)
                    break

            if numeric_id is None:
                return None

            # Note: HNSW doesn't provide direct vector retrieval
            # In a production system, you might want to store vectors separately
            return {"id": doc_id, "vector": [], "metadata": metadata}  # Not available in HNSW

        except Exception as e:
            logger.error(f"Failed to get vector {doc_id}: {e}")
            return None

    def _get_numeric_id(self, doc_id: str, namespace: str) -> int:
        """Convert string doc_id to numeric ID for HNSW"""
        # Simple hash-based approach
        import hashlib

        combined_id = f"{namespace}:{doc_id}"
        hash_obj = hashlib.md5(combined_id.encode(), usedforsecurity=False)
        # Convert to positive integer
        return abs(int.from_bytes(hash_obj.digest()[:4], byteorder="big"))

    def _matches_filters(
        self, metadata: Dict[str, Any], filters: Union[str, Dict[str, Any]]
    ) -> bool:
        """Check if metadata matches the given filters"""
        # Simple filter matching - in production, you'd want more sophisticated filtering
        try:
            # Convert filters string to dict if needed
            if isinstance(filters, str):
                # Simple key:value parsing
                filter_pairs = filters.split(",")
                filter_dict = {}
                for pair in filter_pairs:
                    if ":" in pair:
                        key, value = pair.split(":", 1)
                        filter_dict[key.strip()] = value.strip()
                filters = filter_dict

            if not isinstance(filters, dict):
                return True

            for key, value in filters.items():
                if key not in metadata:
                    return False
                if str(metadata[key]).lower() != str(value).lower():
                    return False

            return True

        except Exception:
            return True  # Default to including the result if filtering fails

    async def _persist_to_redis(self, namespace: str) -> None:
        """Persist metadata to Redis for durability"""
        try:
            if not self.redis_client:
                return

            # Store namespace metadata
            key = f"hnsw:metadata:{namespace}"
            data = pickle.dumps(self.namespace_metadata[namespace])
            await asyncio.get_event_loop().run_in_executor(None, self.redis_client.set, key, data)

            # Store index configuration
            config_key = f"hnsw:config:{namespace}"
            config_data = {
                "dim": self.dim,
                "max_elements": self.max_elements,
                "ef_construction": self.ef_construction,
                "M": self.M,
                "ef_search": self.ef_search,
                "space": self.space,
            }
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.set, config_key, pickle.dumps(config_data)
            )

        except Exception as e:
            logger.error(f"Failed to persist to Redis: {e}")

    async def save_index(self, filepath: str) -> bool:
        """Save HNSW index to file"""
        try:
            self.index.save_index(filepath)

            # Also save metadata
            metadata_path = filepath + ".metadata"
            with open(metadata_path, "wb") as f:
                pickle.dump(
                    {
                        "namespace_metadata": self.namespace_metadata,
                        "metadata": self.metadata,
                        "current_size": self.current_size,
                    },
                    f,
                )

            return True

        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            return False

    async def load_index(self, filepath: str) -> bool:
        """Load HNSW index from file"""
        try:
            self.index.load_index(filepath)

            # Load metadata
            metadata_path = filepath + ".metadata"
            with open(metadata_path, "rb") as f:
                # Note: pickle is used here for performance with HNSW metadata
                # This is safe as we control the data source (our own saved files)
                data = pickle.load(f)  # nosec B301
                self.namespace_metadata = data["namespace_metadata"]
                self.metadata = data["metadata"]
                self.current_size = data["current_size"]

            return True

        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False
