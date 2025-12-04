"""
Semantic/Vector search operations for the context manager
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional

from ...core import ConfigurationManager
from ...utils.cache import ThreadSafeMetrics

logger = logging.getLogger(__name__)


class SemanticSearch:
    """Handle semantic/vector search operations"""

    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager

        # Get providers with null checks
        self.embedding_provider = getattr(config_manager, "embedding_provider", None)
        self.vector_store = getattr(config_manager, "vector_store", None)

        # Initialize metrics
        self.metrics = ThreadSafeMetrics()

    async def search(
        self, query: str, top_k: int = 10, filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search across indexed files AND memories/notes"""
        try:
            query_embedding = await self._get_query_embedding(query)
            if not query_embedding:
                return []
            filter_param = self._normalize_filters(filters)
            all_results = await self._search_files_and_memories(
                query_embedding, top_k, filter_param
            )
            final_results = self._deduplicate_and_sort_results(all_results, top_k)
            enhanced_results = await self._enhance_search_results(final_results, query)
            self.metrics.increment("vector_searches")
            logger.debug(
                "Semantic search completed: %d results for '%s'", len(enhanced_results), query
            )
            return enhanced_results
        except (AttributeError, ValueError, RuntimeError) as e:
            logger.error("Semantic search failed: %s", e)
            return []

    async def _get_query_embedding(self, query: str):
        if not self.embedding_provider:
            logger.warning("Embedding provider not available")
            return None
        if not self.vector_store:
            logger.warning("Vector store not available")
            return None
        query_embedding = await self.embedding_provider.create_embedding(query)
        if not query_embedding:
            logger.warning("Could not create embedding for query")
            return None
        return query_embedding

    def _normalize_filters(self, filters: Optional[Dict]) -> Optional[str]:
        if filters:
            return str(filters) if isinstance(filters, dict) else filters
        return None

    async def _search_files_and_memories(self, query_embedding, top_k, filter_param):
        file_results = await self.vector_store.search_vectors(
            query_embedding, top_k=top_k, filters=filter_param
        )
        memory_results = []
        try:
            if hasattr(self.vector_store, "search_vectors"):
                memory_results = await self.vector_store.search_vectors(
                    query_embedding,
                    top_k=top_k,
                    filters=filter_param,
                    namespace="memories",
                )
            elif hasattr(self.vector_store, "search"):
                memory_results = await self.vector_store.search(
                    query_vector=query_embedding, top_k=top_k, namespace="memories"
                )
        except TypeError as e:
            logger.debug(f"Vector store doesn't support namespace parameter: {e}")
        except Exception as e:
            logger.warning(f"Failed to search memories namespace: {e}")
        return file_results + memory_results

    def _deduplicate_and_sort_results(self, all_results, top_k):
        seen_ids = set()
        unique_results = []
        for result in all_results:
            result_id = result.get("metadata", {}).get("file_path") or result.get("id")
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return unique_results[:top_k]

    async def index_document(
        self, doc_id: str, content: str, metadata: Dict[str, Any], namespace: str = "default"
    ) -> bool:
        """
        Index a single document immediately in the vector store.
        This is used for immediate indexing of notes/memories.
        """
        try:
            if not self.embedding_provider or not self.vector_store:
                logger.warning("Cannot index document: provider(s) not available")
                return False
            embedding = await self.embedding_provider.create_embedding(content)
            if not embedding:
                logger.warning(f"Could not create embedding for document {doc_id}")
                return False
            indexed = await self._try_index_with_all_methods(doc_id, embedding, metadata, namespace)
            if indexed:
                logger.info(f"Successfully indexed document {doc_id} in namespace '{namespace}'")
                self.metrics.increment("documents_indexed")
                return True
            else:
                logger.error(
                    f"Failed to index document {doc_id}: no suitable vector store method found"
                )
                return False
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            return False

    async def _try_index_with_all_methods(self, doc_id, embedding, metadata, namespace):
        if await self._try_add_vectors(doc_id, embedding, metadata, namespace):
            return True
        if await self._try_upsert(doc_id, embedding, metadata, namespace):
            return True
        if await self._try_index_vector(doc_id, embedding, metadata, namespace):
            return True
        return False

    async def _try_add_vectors(self, doc_id, embedding, metadata, namespace):
        if hasattr(self.vector_store, "add_vectors"):
            try:
                await self.vector_store.add_vectors(
                    vectors=[(doc_id, embedding, metadata)], namespace=namespace
                )
                return True
            except TypeError:
                try:
                    await self.vector_store.add_vectors(vectors=[(doc_id, embedding, metadata)])
                    return True
                except Exception as e:
                    logger.debug(f"add_vectors failed: {e}")
        return False

    async def _try_upsert(self, doc_id, embedding, metadata, namespace):
        if hasattr(self.vector_store, "upsert"):
            try:
                await self.vector_store.upsert(
                    vectors=[{"id": doc_id, "values": embedding, "metadata": metadata}],
                    namespace=namespace,
                )
                return True
            except TypeError:
                try:
                    await self.vector_store.upsert(
                        vectors=[{"id": doc_id, "values": embedding, "metadata": metadata}]
                    )
                    return True
                except Exception as e:
                    logger.debug(f"upsert failed: {e}")
        return False

    async def _try_index_vector(self, doc_id, embedding, metadata, namespace):
        if hasattr(self.vector_store, "index_vector"):
            try:
                await self.vector_store.index_vector(
                    doc_id=doc_id, vector=embedding, metadata=metadata, namespace=namespace
                )
                return True
            except Exception as e:
                logger.debug(f"index_vector failed: {e}")
        return False

    async def delete_document(self, doc_id: str, namespace: str = "default") -> bool:
        """
        Delete a document from the vector store.
        """
        try:
            if not self.vector_store:
                logger.warning("Cannot delete document: vector store not available")
                return False
            deleted = await self._try_delete_with_all_methods(doc_id, namespace)
            if deleted:
                logger.info(f"Successfully deleted document {doc_id} from namespace '{namespace}'")
                return True
            else:
                logger.warning(f"Could not delete document {doc_id}: no suitable method found")
                return False
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False

    async def _try_delete_with_all_methods(self, doc_id, namespace):
        if hasattr(self.vector_store, "delete_vector"):
            try:
                await self.vector_store.delete_vector(doc_id, namespace=namespace)
                return True
            except TypeError:
                await self.vector_store.delete_vector(doc_id)
                return True
        elif hasattr(self.vector_store, "delete"):
            try:
                await self.vector_store.delete(ids=[doc_id], namespace=namespace)
                return True
            except TypeError:
                await self.vector_store.delete(ids=[doc_id])
                return True
        return False

    async def update_document(
        self, doc_id: str, content: str, metadata: Dict[str, Any], namespace: str = "default"
    ) -> bool:
        """
        Update a document in the vector store by re-indexing it.

        Args:
            doc_id: Document ID to update
            content: New content
            metadata: New metadata
            namespace: Namespace to update in

        Returns:
            bool: True if update succeeded, False otherwise
        """
        # For most vector stores, update is delete + re-index
        await self.delete_document(doc_id, namespace)
        return await self.index_document(doc_id, content, metadata, namespace)

    async def find_similar_files(
        self, file_embedding: List[float], top_k: int = 5, exclude_file: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find files with similar embeddings"""
        try:
            if not self.vector_store:
                logger.warning("Vector store not available")
                return []

            # Search for similar vectors
            results = await self.vector_store.search_vectors(
                file_embedding,
                top_k=top_k + (1 if exclude_file else 0),  # Get one extra if excluding a file
            )

            # Filter out the excluded file
            if exclude_file:
                results = [
                    r for r in results if r.get("metadata", {}).get("file_path") != exclude_file
                ]
                results = results[:top_k]

            # Enhance results with similarity context
            enhanced_results = []
            for result in results:
                enhanced_result = result.copy()
                enhanced_result["similarity_reason"] = self._generate_similarity_reason(result)
                enhanced_results.append(enhanced_result)

            self.metrics.increment("similarity_searches")
            return enhanced_results

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.error("Similar file search failed: %s", e)
            return []

    async def search_by_file_content(self, file_path: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for files similar to the content of a given file"""
        try:
            # Get the file's embedding from the vector store
            file_vector = await self._get_file_embedding(file_path)
            if not file_vector:
                logger.warning("Could not find embedding for file: %s", file_path)
                return []

            # Find similar files
            return await self.find_similar_files(file_vector, top_k, exclude_file=file_path)

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.error("Content-based search failed for %s: %s", file_path, e)
            return []

    async def search_with_context(
        self, query: str, context_files: Optional[List[str]] = None, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Perform search with additional context from specific files"""
        try:
            # Enhance query with context if provided
            enhanced_query = query
            if context_files:
                context_content = await self._get_context_content(context_files)
                enhanced_query = f"Context: {context_content}\n\nQuery: {query}"

            # Perform search with enhanced query
            results = await self.search(enhanced_query, top_k)

            # Add context metadata to results
            for result in results:
                result["search_context"] = {
                    "original_query": query,
                    "context_files": context_files or [],
                    "enhanced_query": len(enhanced_query) > len(query),
                }

            return results

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.error("Context search failed: %s", e)
            return []

    async def multi_query_search(
        self, queries: List[str], top_k: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Perform multiple searches and combine results"""
        try:
            all_results = {}

            for query in queries:
                results = await self.search(query, top_k)
                all_results[query] = results

            # Also provide combined results
            combined_results = await self._combine_search_results(all_results, top_k)
            all_results["_combined"] = combined_results

            return all_results

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.error("Multi-query search failed: %s", e)
            return {}

    async def _enhance_search_results(
        self, results: List[Dict[str, Any]], query: str
    ) -> List[Dict[str, Any]]:
        """Enhance search results with additional metadata"""
        enhanced_results = []

        for result in results:
            enhanced_result = result.copy()
            metadata = result.get("metadata", {})

            # Check if this is a memory/note result
            if metadata.get("type") == "memory" or metadata.get("memory_type"):
                # Format memory/note results differently
                enhanced_result["result_type"] = "memory"
                enhanced_result["memory_info"] = {
                    "type": metadata.get("memory_type", "note"),
                    "tags": metadata.get("tags", []),
                    "timestamp": metadata.get("timestamp", ""),
                }
                # Add relevance indicators for memories
                enhanced_result["relevance_indicators"] = (
                    await self._generate_memory_relevance_indicators(metadata, query)
                )
            else:
                # Regular file result
                enhanced_result["result_type"] = "file"
                # Add relevance indicators
                enhanced_result["relevance_indicators"] = await self._generate_relevance_indicators(
                    metadata, query
                )

                # Add file context
                enhanced_result["file_context"] = {
                    "file_type": metadata.get("file_type", "unknown"),
                    "file_size": metadata.get("file_size", 0),
                    "lines_of_code": metadata.get("lines_of_code", 0),
                    "last_modified": metadata.get("modified", ""),
                }

            # Add snippet from content preview
            content_preview = metadata.get("content_preview", "") or metadata.get("content", "")
            if content_preview:
                enhanced_result["content_snippet"] = self._extract_relevant_snippet(
                    content_preview, query
                )

            enhanced_results.append(enhanced_result)

        return enhanced_results

    async def _generate_memory_relevance_indicators(
        self, metadata: Dict[str, Any], query: str
    ) -> List[str]:
        """Generate relevance indicators for memory/note results"""
        indicators = []
        query_lower = query.lower()

        # Check memory type relevance
        memory_type = metadata.get("memory_type", "").lower()
        if memory_type and memory_type in query_lower:
            indicators.append(f"Memory type: {memory_type}")

        # Check tags relevance
        tags = metadata.get("tags", [])
        matching_tags = [tag for tag in tags if tag.lower() in query_lower]
        if matching_tags:
            indicators.append(f"Matching tags: {', '.join(matching_tags)}")

        # Check content relevance
        content = metadata.get("content", "").lower()
        query_words = query_lower.split()
        matching_words = [word for word in query_words if word in content]
        if matching_words:
            indicators.append(f"Content matches: {', '.join(matching_words[:3])}")

        # Check timestamp relevance (if query mentions time)
        time_keywords = ["today", "yesterday", "recent", "latest", "last"]
        if any(keyword in query_lower for keyword in time_keywords):
            timestamp = metadata.get("timestamp", "")
            if timestamp:
                indicators.append("Recent entry")

        return indicators

    async def _generate_relevance_indicators(
        self, metadata: Dict[str, Any], query: str
    ) -> List[str]:
        """Generate indicators of why this result is relevant"""
        indicators = []
        query_lower = query.lower()

        # Check file name relevance
        file_path = metadata.get("file_path", "")
        if any(word in file_path.lower() for word in query_lower.split()):
            indicators.append("Filename matches query terms")

        # Check file type relevance
        file_type = metadata.get("file_type", "")
        if file_type in query_lower:
            indicators.append(f"File type matches ({file_type})")

        # Check content preview relevance
        content_preview = metadata.get("content_preview", "").lower()
        query_words = query_lower.split()
        matching_words = [word for word in query_words if word in content_preview]
        if matching_words:
            indicators.append(f"Content contains: {', '.join(matching_words[:3])}")

        # Check language-specific relevance
        if metadata.get("python_functions") and "function" in query_lower:
            indicators.append("Contains Python functions")
        if metadata.get("js_functions") and "function" in query_lower:
            indicators.append("Contains JavaScript functions")
        if metadata.get("markdown_headings") and any(
            word in query_lower for word in ["heading", "title", "section"]
        ):
            indicators.append("Contains markdown structure")

        return indicators

    def _extract_relevant_snippet(self, content: str, query: str) -> str:
        """Extract a relevant snippet from content based on query"""
        query_words = query.lower().split()

        # Find the best matching position
        best_position = 0
        best_score = 0

        words = content.split()
        for i in range(len(words)):
            # Calculate score for this position
            window = " ".join(words[i : i + 20]).lower()  # 20-word window
            score = sum(1 for word in query_words if word in window)

            if score > best_score:
                best_score = score
                best_position = i

        # Extract snippet around the best position
        start = max(0, best_position - 10)
        end = min(len(words), best_position + 30)
        snippet = " ".join(words[start:end])

        # Truncate if too long
        if len(snippet) > 200:
            snippet = snippet[:200] + "..."

        return snippet

    def _generate_similarity_reason(self, result: Dict[str, Any]) -> str:
        """Generate a reason for why files are similar"""
        score = result.get("score", 0)

        if score > 0.9:
            return "Very similar content and structure"
        elif score > 0.8:
            return "Similar content with shared concepts"
        elif score > 0.7:
            return "Related content and patterns"
        elif score > 0.6:
            return "Some shared concepts and terminology"
        else:
            return "Loosely related content"

    async def _get_file_embedding(self, file_path: str) -> Optional[List[float]]:
        """Get the embedding for a specific file"""
        try:
            if not self.vector_store:
                logger.warning("Vector store not available")
                return None

            # Produce the same document ID used when indexing
            try:
                digest = hashlib.md5(file_path.encode("utf-8"), usedforsecurity=False)
            except TypeError:
                digest = hashlib.md5(file_path.encode("utf-8"))  # nosec B324
            doc_id = digest.hexdigest()

            # Retrieve the vector - handle case where get_vector might not exist
            if not hasattr(self.vector_store, "get_vector"):
                logger.warning("Vector store does not support get_vector operation")
                return None

            vector_data = await self.vector_store.get_vector(doc_id)
            if vector_data and "vector" in vector_data:
                vector = vector_data.get("vector")
                if isinstance(vector, list):
                    return vector

            return None

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.error("Failed to get file embedding for %s: %s", file_path, e)
            return None

    async def _get_context_content(self, context_files: List[str]) -> str:
        """Get content from context files to enhance search"""
        try:
            context_content = []

            for file_path in context_files[:3]:  # Limit to 3 files to avoid overwhelming the query
                # For now, just use the file path as context
                # In a full implementation, we'd want to read the actual file content
                # or get it from the vector store's metadata
                context_content.append(f"File: {file_path}")

            return " | ".join(context_content)

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.error("Failed to get context content: %s", e)
            return ""

    async def _combine_search_results(
        self, all_results: Dict[str, List[Dict[str, Any]]], top_k: int
    ) -> List[Dict[str, Any]]:
        """Combine results from multiple queries, removing duplicates and ranking by relevance"""
        try:
            combined = {}

            # Collect all results with aggregated scores
            for query, results in all_results.items():
                if query == "_combined":  # Skip the combined results key
                    continue

                for result in results:
                    # Get unique identifier (file_path for files, id for memories)
                    file_path = result.get("metadata", {}).get("file_path")
                    memory_id = result.get("id")
                    unique_id = file_path or memory_id

                    if unique_id:
                        if unique_id not in combined:
                            combined[unique_id] = result.copy()
                            combined[unique_id]["combined_score"] = result.get("score", 0)
                            combined[unique_id]["source_queries"] = [query]
                        else:
                            # Aggregate scores and track source queries
                            existing_score = combined[unique_id].get("combined_score", 0)
                            new_score = result.get("score", 0)
                            combined[unique_id]["combined_score"] = max(existing_score, new_score)
                            combined[unique_id]["source_queries"].append(query)

            # Sort by combined score and return top results
            sorted_results = sorted(
                combined.values(), key=lambda x: x.get("combined_score", 0), reverse=True
            )

            return sorted_results[:top_k]

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.error("Failed to combine search results: %s", e)
            return []

    async def get_search_stats(self) -> Dict[str, Any]:
        """Get statistics about search operations"""
        try:
            metrics_snapshot = self.metrics.get_snapshot()

            vector_stats = {}
            if self.vector_store and hasattr(self.vector_store, "get_stats"):
                try:
                    vector_stats = await self.vector_store.get_stats()
                except (AttributeError, ValueError, RuntimeError) as e:
                    logger.debug("Could not get vector store stats: %s", e)
                    vector_stats = {}

            return {
                "total_searches": metrics_snapshot.get("vector_searches", 0),
                "similarity_searches": metrics_snapshot.get("similarity_searches", 0),
                "documents_indexed": metrics_snapshot.get("documents_indexed", 0),
                "indexed_documents": vector_stats.get("total_vectors", 0),
                "vector_store_size": vector_stats.get("index_size", 0),
                "embedding_provider": (
                    type(self.embedding_provider).__name__ if self.embedding_provider else "None"
                ),
                "vector_store_provider": (
                    type(self.vector_store).__name__ if self.vector_store else "None"
                ),
            }

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.error("Failed to get search stats: %s", e)
            return {"error": str(e)}
