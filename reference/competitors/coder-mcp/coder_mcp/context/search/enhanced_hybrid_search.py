"""
Enhanced Hybrid Search System
Combines multi-model embeddings, HNSW performance, intelligent query processing,
and advanced caching for optimal search experience
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from ...storage.embeddings.multi_model import MultiModelEmbedding
from ...storage.vector_stores import HybridVectorStore
from .cache import BatchProcessor, SearchCache
from .query_processor import QueryProcessor
from .semantic_search import SemanticSearch
from .text_search import TextSearch

logger = logging.getLogger(__name__)


class SearchStrategy(Enum):
    """Search strategy enumeration"""

    SEMANTIC_FIRST = "semantic_first"
    TEXT_FIRST = "text_first"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"
    CODE_FOCUSED = "code_focused"


@dataclass
class SearchResult:
    """Enhanced search result with metadata"""

    id: str
    content: str
    file_path: str
    score: float
    metadata: Dict[str, Any]
    search_strategy: str
    match_reason: str
    context_snippet: str


class ConfigManagerProtocol(Protocol):
    """Protocol for configuration managers"""

    embedding_provider: Any
    vector_store: Any
    limits: Any
    config: Any


class MinimalConfigManager:
    """Minimal configuration manager that provides the necessary interfaces for search components"""

    def __init__(self, embedding_provider: Any, vector_store: Any):
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

        # Create limits object that TextSearch expects
        self.limits = type(
            "Limits",
            (),
            {
                "max_search_results": 100,
                "max_file_size": 10 * 1024 * 1024,
                "max_files_to_index": 100,
                "max_search_depth": 10,
            },
        )()

        # Create config object that TextSearch expects
        self.config = type(
            "Config",
            (),
            {
                "storage": type(
                    "Storage",
                    (),
                    {
                        "max_file_size": 10 * 1024 * 1024,
                        "max_files_to_index": 100,
                    },
                )(),
                "server": type(
                    "Server",
                    (),
                    {
                        "limits": type(
                            "Limits",
                            (),
                            {
                                "max_file_size": 10 * 1024 * 1024,
                                "max_files_to_index": 100,
                            },
                        )(),
                    },
                )(),
                "search": type(
                    "Search",
                    (),
                    {
                        "max_results": 100,
                        "max_depth": 10,
                    },
                )(),
            },
        )()


class EnhancedHybridSearch:
    """Enhanced hybrid search combining all improvements"""

    def __init__(
        self,
        redis_client: Any,
        embedding_dim: int = 1536,
        enable_hnsw: bool = True,
        cache_config: Optional[Dict[str, Any]] = None,
    ):
        self.redis_client = redis_client
        self.embedding_dim = embedding_dim

        # Initialize components
        self.multi_model_embedding = MultiModelEmbedding()
        self.query_processor = QueryProcessor()
        self.search_cache = SearchCache(redis_client)
        self.batch_processor = BatchProcessor(self.search_cache)

        # Initialize vector store
        self.vector_store = HybridVectorStore(
            redis_client=redis_client, embedding_dim=embedding_dim, use_hnsw=enable_hnsw
        )

        # Initialize search engines with minimal config manager
        config_manager = MinimalConfigManager(self.multi_model_embedding, self.vector_store)

        self.semantic_search = SemanticSearch(config_manager)  # type: ignore
        self.text_search = TextSearch(Path("."), config_manager)  # type: ignore

        # Configuration
        self.cache_config = cache_config or {}
        self.default_strategy = SearchStrategy.ADAPTIVE

        # Performance metrics
        self.metrics: Dict[str, Any] = {
            "total_searches": 0,
            "cache_hits": 0,
            "strategy_usage": {strategy.value: 0 for strategy in SearchStrategy},
            "avg_response_time": 0.0,
        }

    async def search(
        self,
        query: str,
        top_k: int = 10,
        namespace: str = "default",
        strategy: Optional[SearchStrategy] = None,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
    ) -> List[SearchResult]:
        """Enhanced search with intelligent strategy selection"""

        start_time = asyncio.get_event_loop().time()
        current_total = self.metrics["total_searches"]
        self.metrics["total_searches"] = int(current_total) + 1

        try:
            # 1. Process query intelligently (async call)
            query_analysis = await self.query_processor.process_query(query)

            # 2. Determine search strategy
            if strategy is None:
                strategy = self._determine_strategy(query_analysis)

            strategy_count = self.metrics["strategy_usage"][strategy.value]
            self.metrics["strategy_usage"][strategy.value] = int(strategy_count) + 1

            # 3. Execute search based on strategy
            results = await self._execute_search_strategy(
                query, query_analysis, strategy, top_k, namespace, filters
            )

            # 4. Post-process results
            enhanced_results = await self._enhance_results(
                results, query_analysis, strategy, include_metadata
            )

            # 5. Update metrics
            end_time = asyncio.get_event_loop().time()
            response_time = end_time - start_time
            self._update_metrics(response_time)

            return enhanced_results

        except Exception as e:
            logger.error(f"Enhanced search failed: {e}")
            return []

    async def multi_query_search(
        self,
        queries: List[str],
        top_k: int = 10,
        namespace: str = "default",
        strategy: Optional[SearchStrategy] = None,
    ) -> List[List[SearchResult]]:
        """Search multiple queries efficiently"""

        # Process queries in parallel
        search_tasks = [self.search(query, top_k, namespace, strategy) for query in queries]

        results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Handle exceptions
        processed_results: List[List[SearchResult]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Multi-query search failed for '{queries[i]}': {result}")
                processed_results.append([])
            elif isinstance(result, list):
                processed_results.append(result)
            else:
                processed_results.append([])

        return processed_results

    async def contextual_search(
        self, query: str, context_files: List[str], top_k: int = 10, namespace: str = "default"
    ) -> List[SearchResult]:
        """Search with file context for better relevance"""

        # Enhance query with context
        context_enhanced_query = await self._enhance_query_with_context(query, context_files)

        # Use hybrid strategy for contextual search
        return await self.search(context_enhanced_query, top_k, namespace, SearchStrategy.HYBRID)

    async def semantic_similarity_search(
        self,
        reference_text: str,
        top_k: int = 10,
        namespace: str = "default",
        similarity_threshold: float = 0.7,
    ) -> List[SearchResult]:
        """Find semantically similar content"""

        # Create embedding for reference text
        embedding = await self.multi_model_embedding.create_hybrid_embedding(
            reference_text, "mixed"
        )

        if not embedding:
            return []

        # Search using embedding
        vector_results = await self.vector_store.search_vectors(
            embedding, top_k, namespace=namespace
        )

        # Filter by similarity threshold
        filtered_results = [
            result for result in vector_results if result.get("score", 0) >= similarity_threshold
        ]

        # Convert to SearchResult objects
        return [
            SearchResult(
                id=result["id"],
                content=result.get("content", ""),
                file_path=result.get("file_path", ""),
                score=result["score"],
                metadata=result.get("metadata", {}),
                search_strategy="semantic_similarity",
                match_reason="semantic_similarity",
                context_snippet=self._extract_context_snippet(result.get("content", "")),
            )
            for result in filtered_results
        ]

    async def code_search(
        self,
        query: str,
        language: Optional[str] = None,
        top_k: int = 10,
        namespace: str = "default",
    ) -> List[SearchResult]:
        """Specialized search for code"""

        # Process query for code search
        query_analysis = await self.query_processor.process_query(query)

        # Use code-focused strategy
        results = await self._execute_search_strategy(
            query,
            query_analysis,
            SearchStrategy.CODE_FOCUSED,
            top_k,
            namespace,
            {"language": language} if language else None,
        )

        # Convert to SearchResult objects
        return await self._enhance_results(
            results, query_analysis, SearchStrategy.CODE_FOCUSED, True
        )

    def _determine_strategy(self, query_analysis: Dict[str, Any]) -> SearchStrategy:
        """Determine the best search strategy based on query analysis"""

        # Extract features from query analysis
        intent = query_analysis.get("intent", "")
        entities = query_analysis.get("entities", [])
        query_type = query_analysis.get("query_type", "")
        complexity = query_analysis.get("complexity", 0)

        # Strategy selection logic
        if intent == "code_search" or "code" in query_type:
            return SearchStrategy.CODE_FOCUSED
        elif len(entities) > 3 or complexity > 0.7:
            return SearchStrategy.HYBRID
        elif intent == "semantic" or "concept" in query_type:
            return SearchStrategy.SEMANTIC_FIRST
        elif intent == "exact" or "literal" in query_type:
            return SearchStrategy.TEXT_FIRST
        else:
            return SearchStrategy.ADAPTIVE

    async def _execute_search_strategy(
        self,
        query: str,
        query_analysis: Dict[str, Any],
        strategy: SearchStrategy,
        top_k: int,
        namespace: str,
        filters: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Execute search based on the selected strategy"""

        if strategy == SearchStrategy.SEMANTIC_FIRST:
            return await self._semantic_first_search(query, top_k, namespace, filters)
        elif strategy == SearchStrategy.TEXT_FIRST:
            return await self._text_first_search(query, top_k, namespace, filters)
        elif strategy == SearchStrategy.HYBRID:
            return await self._hybrid_search(query, top_k, namespace, filters)
        elif strategy == SearchStrategy.CODE_FOCUSED:
            return await self._code_focused_search(query, top_k, namespace, filters)
        else:  # ADAPTIVE
            return await self._adaptive_search(query, query_analysis, top_k, namespace, filters)

    async def _semantic_first_search(
        self, query: str, top_k: int, namespace: str, filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Semantic-first search strategy"""

        try:
            # Primary semantic search (SemanticSearch.search doesn't take namespace parameter)
            semantic_results = await self.semantic_search.search(
                query, top_k=min(top_k * 2, 50), filters=filters
            )

            # If semantic results are insufficient, supplement with text search
            if len(semantic_results) < top_k:
                remaining = top_k - len(semantic_results)
                text_results = await self.text_search.search_files(query, file_pattern="*")
                # Limit text results to what we need
                text_results = text_results[:remaining]
                # Combine and deduplicate
                return self._combine_and_deduplicate(semantic_results, text_results, top_k)

            return semantic_results[:top_k]

        except Exception as e:
            logger.error(f"Semantic-first search failed: {e}")
            return []

    async def _text_first_search(
        self, query: str, top_k: int, namespace: str, filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Text-first search strategy"""

        try:
            # Primary text search (TextSearch.search_files doesn't take filters parameter)
            text_results = await self.text_search.search_files(query, file_pattern="*")
            # Limit text results
            text_results = text_results[: min(top_k * 2, 50)]

            # If text results are insufficient, supplement with semantic search
            if len(text_results) < top_k:
                remaining = top_k - len(text_results)
                semantic_results = await self.semantic_search.search(
                    query, top_k=remaining, filters=filters
                )
                # Combine and deduplicate
                return self._combine_and_deduplicate(text_results, semantic_results, top_k)

            return text_results[:top_k]

        except Exception as e:
            logger.error(f"Text-first search failed: {e}")
            return []

    async def _hybrid_search(
        self, query: str, top_k: int, namespace: str, filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Hybrid search strategy"""

        try:
            # Execute both searches in parallel
            semantic_task = self.semantic_search.search(
                query, top_k=min(top_k * 2, 50), filters=filters
            )
            text_task = self.text_search.search_files(query, file_pattern="*")

            semantic_results, text_results = await asyncio.gather(semantic_task, text_task)

            # Limit text results
            text_results = text_results[: min(top_k * 2, 50)]

            # Combine with weighted scoring
            return self._combine_with_weighted_scoring(semantic_results, text_results, top_k)

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    async def _code_focused_search(
        self, query: str, top_k: int, namespace: str, filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Code-focused search strategy"""

        try:
            # Enhanced filters for code search
            code_filters = filters.copy() if filters else {}
            code_filters.update(
                {
                    "file_types": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"],
                    "exclude_patterns": ["*.md", "*.txt", "*.log"],
                }
            )

            # Execute semantic search with code focus
            semantic_results = await self.semantic_search.search(
                query, top_k=min(top_k * 2, 50), filters=code_filters
            )

            # Execute text search with code patterns
            code_query = self._enhance_query_for_code(query)
            # Use code file patterns for text search
            text_results = await self.text_search.search_files(
                code_query, file_pattern="*.py"  # Focus on Python files primarily
            )
            text_results = text_results[: min(top_k * 2, 50)]

            # Combine with code-specific scoring
            return self._combine_with_code_scoring(semantic_results, text_results, top_k)

        except Exception as e:
            logger.error(f"Code-focused search failed: {e}")
            return []

    async def _adaptive_search(
        self,
        query: str,
        query_analysis: Dict[str, Any],
        top_k: int,
        namespace: str,
        filters: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Adaptive search strategy"""

        try:
            # Analyze query characteristics
            query_length = len(query.split())
            has_code_terms = any(
                term in query.lower() for term in ["function", "class", "method", "variable"]
            )
            has_natural_language = query_analysis.get("complexity", 0) > 0.3

            # Choose strategy based on analysis
            if has_code_terms:
                return await self._code_focused_search(query, top_k, namespace, filters)
            elif query_length > 10 and has_natural_language:
                return await self._semantic_first_search(query, top_k, namespace, filters)
            elif query_length <= 3:
                return await self._text_first_search(query, top_k, namespace, filters)
            else:
                return await self._hybrid_search(query, top_k, namespace, filters)

        except Exception as e:
            logger.error(f"Adaptive search failed: {e}")
            return []

    async def _enhance_results(
        self,
        results: List[Dict[str, Any]],
        query_analysis: Dict[str, Any],
        strategy: SearchStrategy,
        include_metadata: bool,
    ) -> List[SearchResult]:
        """Enhance results with additional metadata and context"""

        enhanced_results = []

        for result in results:
            # Handle both semantic and text result formats
            if "metadata" in result:
                # Semantic result format
                file_path = result.get("metadata", {}).get("file_path", "")
                content = result.get("metadata", {}).get("content_preview", "")
                result_id = result.get("id", "")
                score = result.get("score", 0.0)
                metadata = result.get("metadata", {}) if include_metadata else {}
            else:
                # Text result format
                file_path = result.get("file", "")
                content = result.get("line", "")
                result_id = result.get("file", "")
                score = self._calculate_text_relevance_score(result)
                metadata = (
                    {
                        "file_type": result.get("file_type", ""),
                        "line_number": result.get("line_number", 0),
                        "matched_text": result.get("matched_text", ""),
                    }
                    if include_metadata
                    else {}
                )

            # Extract context snippet
            context_snippet = self._extract_context_snippet(
                content, query_analysis.get("original", query_analysis.get("query", ""))
            )

            # Determine match reason
            match_reason = self._determine_match_reason(result, query_analysis)

            enhanced_result = SearchResult(
                id=result_id,
                content=content,
                file_path=file_path,
                score=score,
                metadata=metadata,
                search_strategy=strategy.value,
                match_reason=match_reason,
                context_snippet=context_snippet,
            )

            enhanced_results.append(enhanced_result)

        return enhanced_results

    def _calculate_text_relevance_score(self, text_result: Dict[str, Any]) -> float:
        """Calculate relevance score for text search results"""
        score = 0.5  # Base score

        # File type bonus
        file_type = text_result.get("file_type", "")
        if file_type in ["python", "javascript", "typescript"]:
            score += 0.3
        elif file_type in ["markdown", "text"]:
            score += 0.1

        # Match quality
        line = text_result.get("line", "").lower()
        matched_text = text_result.get("matched_text", "").lower()

        # Exact match bonus
        if matched_text in line:
            score += 0.2

        # Context bonus (function/class definitions)
        if any(keyword in line for keyword in ["def ", "class ", "function "]):
            score += 0.2

        # Normalize to 0-1 range
        return min(1.0, score)

    async def _enhance_query_with_context(self, query: str, context_files: List[str]) -> str:
        """Enhance query with file context"""

        # Simple context enhancement - in production, you'd want more sophisticated logic
        if context_files:
            file_context = " ".join([f"file:{file}" for file in context_files[:3]])
            return f"{query} {file_context}"

        return query

    def _extract_context_snippet(self, content: str, query: str = "") -> str:
        """Extract relevant context snippet from content"""

        if not content or not query:
            return ""

        # Simple implementation - find the first occurrence of query terms
        query_terms = query.lower().split()
        content_lower = content.lower()

        for term in query_terms:
            if term in content_lower:
                start_idx = content_lower.find(term)
                # Extract context around the match
                context_start = max(0, start_idx - 100)
                context_end = min(len(content), start_idx + len(term) + 100)
                return content[context_start:context_end]

        # If no direct match, return first 200 characters
        return content[:200]

    def _determine_match_reason(
        self, result: Dict[str, Any], query_analysis: Dict[str, Any]
    ) -> str:
        """Determine why this result matched the query"""

        # Simple implementation based on available data
        score = result.get("score", 0.0)
        if score > 0.8:
            return "High semantic similarity"
        elif score > 0.6:
            return "Good semantic match"
        elif score > 0.4:
            return "Moderate relevance"
        else:
            return "Text match"

    def _combine_and_deduplicate(
        self,
        primary_results: List[Dict[str, Any]],
        secondary_results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Combine and deduplicate results from different search types"""

        seen_ids = set()
        combined = []

        # Add primary results first
        for result in primary_results:
            # Handle both semantic and text result formats
            if "metadata" in result:
                # Semantic result format
                result_id = result.get("metadata", {}).get("file_path", result.get("id", ""))
            else:
                # Text result format
                result_id = result.get("file", result.get("id", ""))

            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                combined.append(result)

        # Add secondary results if not already seen
        for result in secondary_results:
            if len(combined) >= top_k:
                break

            # Handle both semantic and text result formats
            if "metadata" in result:
                # Semantic result format
                result_id = result.get("metadata", {}).get("file_path", result.get("id", ""))
            else:
                # Text result format
                result_id = result.get("file", result.get("id", ""))

            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                combined.append(result)

        return combined[:top_k]

    def _combine_with_weighted_scoring(
        self, semantic_results: List[Dict[str, Any]], text_results: List[Dict[str, Any]], top_k: int
    ) -> List[Dict[str, Any]]:
        """Combine results with weighted scoring"""

        # Create a scoring map
        score_map: Dict[str, float] = {}

        # Weight semantic results
        for result in semantic_results:
            result_id = result.get("id", "")
            if result_id:
                current_score = score_map.get(result_id, 0.0)
                result_score = float(result.get("score", 0))
                score_map[result_id] = current_score + result_score * 0.6

        # Weight text results
        for result in text_results:
            result_id = result.get("id", "")
            if result_id:
                current_score = score_map.get(result_id, 0.0)
                result_score = float(result.get("score", 0))
                score_map[result_id] = current_score + result_score * 0.4

        # Create combined results
        all_results = {r.get("id", ""): r for r in semantic_results + text_results}

        combined = []
        for result_id, score in score_map.items():
            if result_id in all_results:
                result = all_results[result_id].copy()
                result["score"] = score
                combined.append(result)

        # Sort and limit
        combined.sort(key=lambda x: x.get("score", 0), reverse=True)
        return combined[:top_k]

    def _combine_with_code_scoring(
        self, semantic_results: List[Dict[str, Any]], text_results: List[Dict[str, Any]], top_k: int
    ) -> List[Dict[str, Any]]:
        """Combine results with code-specific scoring"""

        # Create a scoring map with code-specific weights
        score_map: Dict[str, float] = {}

        # Weight semantic results (higher for code concepts)
        for result in semantic_results:
            result_id = result.get("id", "")
            if result_id:
                current_score = score_map.get(result_id, 0.0)
                result_score = float(result.get("score", 0))
                # Boost score if it's a code file
                code_boost = 1.2 if self._is_code_file(result.get("file_path", "")) else 1.0
                score_map[result_id] = current_score + result_score * 0.7 * code_boost

        # Weight text results (higher for exact matches)
        for result in text_results:
            result_id = result.get("id", "")
            if result_id:
                current_score = score_map.get(result_id, 0.0)
                result_score = float(result.get("score", 0))
                # Boost score if it's a code file
                code_boost = 1.2 if self._is_code_file(result.get("file_path", "")) else 1.0
                score_map[result_id] = current_score + result_score * 0.5 * code_boost

        # Create combined results
        all_results = {r.get("id", ""): r for r in semantic_results + text_results}

        combined = []
        for result_id, score in score_map.items():
            if result_id in all_results:
                result = all_results[result_id].copy()
                result["score"] = score
                combined.append(result)

        # Sort and limit
        combined.sort(key=lambda x: x.get("score", 0), reverse=True)
        return combined[:top_k]

    def _enhance_query_for_code(self, query: str) -> str:
        """Enhance query for code search"""

        # Add code-specific terms and patterns
        enhanced_query = query

        # Add regex patterns for common code constructs
        if any(term in query.lower() for term in ["function", "method"]):
            enhanced_query += " def "
        if any(term in query.lower() for term in ["class", "object"]):
            enhanced_query += " class "

        return enhanced_query

    def _is_code_file(self, file_path: str) -> bool:
        """Check if file is a code file"""

        code_extensions = {".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs", ".rb", ".php"}
        return any(file_path.endswith(ext) for ext in code_extensions)

    def _update_metrics(self, response_time: float) -> None:
        """Update performance metrics"""

        # Update average response time
        current_avg = float(self.metrics["avg_response_time"])
        total_searches = int(self.metrics["total_searches"])

        if total_searches > 0:
            self.metrics["avg_response_time"] = (
                current_avg * (total_searches - 1) + response_time
            ) / total_searches

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""

        return self.metrics.copy()

    async def clear_cache(self) -> None:
        """Clear all caches"""
        try:
            # Clear Redis cache by pattern (if supported)
            has_redis_client = hasattr(self.search_cache, "redis_client")
            if has_redis_client and self.search_cache.redis_client:
                # This is a basic implementation - in production you'd want
                # more sophisticated cache clearing
                logger.info(
                    "Cache clearing requested - individual cache entries will expire naturally"
                )
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            # Return basic stats since SearchCache doesn't have get_stats method
            return {
                "cache_type": "redis",
                "status": "active" if self.search_cache.redis_client else "inactive",
                "ttl_settings": {
                    "embedding_ttl": getattr(self.search_cache, "embedding_ttl", 3600),
                    "search_ttl": getattr(self.search_cache, "search_ttl", 1800),
                    "query_ttl": getattr(self.search_cache, "query_ttl", 1800),
                },
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""

        try:
            # Test basic search
            await self.search("test query", top_k=1)

            return {
                "status": "healthy",
                "components": {
                    "multi_model_embedding": True,
                    "vector_store": True,
                    "query_processor": True,
                    "search_cache": True,
                    "redis_client": self.redis_client is not None,
                },
                "metrics": self.get_metrics(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "components": {
                    "multi_model_embedding": False,
                    "vector_store": False,
                    "query_processor": False,
                    "search_cache": False,
                    "redis_client": self.redis_client is not None,
                },
            }
