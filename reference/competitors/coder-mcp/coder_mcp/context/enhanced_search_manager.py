"""
Enhanced Search Manager
Unified interface for all enhanced search capabilities
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.config import MCPConfiguration
from ..core.manager import ConfigurationManager
from ..core.providers import ProviderFactory
from .indexing import BatchIndexer
from .memory import MemoryStore
from .search import EnhancedHybridSearch, SearchResult, SearchStrategy

logger = logging.getLogger(__name__)


class EnhancedSearchManager:
    """
    Unified search manager that integrates all enhanced search capabilities
    """

    def __init__(
        self,
        config: Optional[MCPConfiguration] = None,
        redis_client: Optional[Any] = None,
        workspace_path: Optional[str] = None,
    ):
        self.config = config or MCPConfiguration()
        self.workspace_path = workspace_path or str(Path.cwd())

        if redis_client:
            self.redis_client = redis_client
        else:
            # Create redis client using provider factory
            provider_factory = ProviderFactory(self.config)
            self.redis_client = provider_factory._get_redis_client()

        # Initialize enhanced search system
        self.enhanced_search = EnhancedHybridSearch(
            redis_client=self.redis_client,
            embedding_dim=self.config.openai.embedding_dimension,
            enable_hnsw=True,  # Default to enabled
            cache_config={"ttl": self.config.storage.cache_ttl},
        )

        workspace_path_obj = Path(self.workspace_path)
        config_manager = ConfigurationManager(self.config)

        self.batch_indexer = BatchIndexer(workspace_path_obj, config_manager)
        self.memory_store = MemoryStore(workspace_path_obj, config_manager)

        # Track initialization state
        self._initialized = False
        self._indexing_in_progress = False

    async def initialize(self, force_reindex: bool = False) -> bool:
        """Initialize the search manager"""

        try:
            if self._initialized and not force_reindex:
                return True

            logger.info("Initializing Enhanced Search Manager...")

            # Health check
            health_status = await self.enhanced_search.health_check()
            if health_status["status"] != "healthy":
                logger.error(f"Search system unhealthy: {health_status}")
                return False

            # Index workspace if needed
            if force_reindex or await self._needs_indexing():
                await self._index_workspace()

            self._initialized = True
            logger.info("Enhanced Search Manager initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Enhanced Search Manager: {e}")
            return False

    async def search(
        self,
        query: str,
        top_k: int = 10,
        namespace: str = "default",
        strategy: Optional[Union[str, SearchStrategy]] = None,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
        context_files: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Unified search interface

        Args:
            query: Search query
            top_k: Number of results to return
            namespace: Search namespace
            strategy: Search strategy (semantic_first, text_first, hybrid, adaptive, code_focused)
            filters: Additional filters
            include_metadata: Include metadata in results
            context_files: Files to use as context

        Returns:
            List of enhanced search results
        """

        if not self._initialized:
            await self.initialize()

        # Convert string strategy to enum
        if isinstance(strategy, str):
            strategy = SearchStrategy(strategy)

        # Use contextual search if context files provided
        if context_files:
            return await self.enhanced_search.contextual_search(
                query, context_files, top_k, namespace
            )

        return await self.enhanced_search.search(
            query, top_k, namespace, strategy, filters, include_metadata
        )

    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        namespace: str = "default",
        similarity_threshold: float = 0.7,
    ) -> List[SearchResult]:
        """Semantic similarity search"""

        if not self._initialized:
            await self.initialize()

        return await self.enhanced_search.semantic_similarity_search(
            query, top_k, namespace, similarity_threshold
        )

    async def code_search(
        self,
        query: str,
        language: Optional[str] = None,
        top_k: int = 10,
        namespace: str = "default",
    ) -> List[SearchResult]:
        """Code-specific search"""

        if not self._initialized:
            await self.initialize()

        return await self.enhanced_search.code_search(query, language, top_k, namespace)

    async def multi_query_search(
        self,
        queries: List[str],
        top_k: int = 10,
        namespace: str = "default",
        strategy: Optional[Union[str, SearchStrategy]] = None,
    ) -> List[List[SearchResult]]:
        """Search multiple queries efficiently"""

        if not self._initialized:
            await self.initialize()

        # Convert string strategy to enum
        if isinstance(strategy, str):
            strategy = SearchStrategy(strategy)

        return await self.enhanced_search.multi_query_search(queries, top_k, namespace, strategy)

    async def find_similar_files(
        self,
        reference_file: str,
        top_k: int = 10,
        namespace: str = "default",
        similarity_threshold: float = 0.6,
    ) -> List[SearchResult]:
        """Find files similar to a reference file"""

        try:
            # Read reference file content
            file_path = Path(self.workspace_path) / reference_file
            if not file_path.exists():
                logger.error(f"Reference file not found: {reference_file}")
                return []

            content = file_path.read_text(encoding="utf-8")

            # Use semantic similarity search
            return await self.semantic_search(content, top_k, namespace, similarity_threshold)

        except Exception as e:
            logger.error(f"Failed to find similar files: {e}")
            return []

    async def search_by_file_type(
        self, query: str, file_extensions: List[str], top_k: int = 10, namespace: str = "default"
    ) -> List[SearchResult]:
        """Search within specific file types"""

        filters = {"file_extensions": file_extensions}
        return await self.search(query, top_k, namespace, filters=filters)

    async def search_recent_changes(
        self, query: str, days: int = 7, top_k: int = 10, namespace: str = "default"
    ) -> List[SearchResult]:
        """Search in recently modified files"""

        filters = {"modified_within_days": days}
        return await self.search(query, top_k, namespace, filters=filters)

    async def add_document(
        self,
        doc_id: str,
        content: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        namespace: str = "default",
    ) -> bool:
        """Add a document to the search index"""

        try:
            # Create embedding
            embedding = await self.enhanced_search.multi_model_embedding.create_hybrid_embedding(
                content, "mixed"
            )

            if not embedding:
                logger.error(f"Failed to create embedding for document: {doc_id}")
                return False

            # Prepare metadata
            doc_metadata = {
                "content": content,
                "file_path": file_path,
                "indexed_at": asyncio.get_event_loop().time(),
                **(metadata or {}),
            }

            # Store in vector store
            success = await self.enhanced_search.vector_store.store_vector(
                doc_id, embedding, doc_metadata, namespace
            )

            if success:
                logger.debug(f"Added document to index: {doc_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False

    async def remove_document(self, doc_id: str, namespace: str = "default") -> bool:
        """Remove a document from the search index"""

        try:
            success = await self.enhanced_search.vector_store.delete_vector(doc_id, namespace)

            if success:
                logger.debug(f"Removed document from index: {doc_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to remove document: {e}")
            return False

    async def reindex_workspace(self, force: bool = False) -> bool:
        """Reindex the entire workspace"""

        if self._indexing_in_progress:
            logger.info("Indexing already in progress")
            return False

        try:
            self._indexing_in_progress = True
            return await self._index_workspace(force)

        finally:
            self._indexing_in_progress = False

    async def get_search_stats(self) -> Dict[str, Any]:
        """Get comprehensive search statistics"""

        try:
            # Get enhanced search metrics
            search_metrics = self.enhanced_search.get_metrics()

            # Get vector store stats
            vector_stats = await self.enhanced_search.vector_store.get_stats()

            # Get memory stats
            memory_stats = (
                await self.memory_store.get_stats()
                if hasattr(self.memory_store, "get_stats")
                else {}
            )

            return {
                "search_metrics": search_metrics,
                "vector_store_stats": vector_stats,
                "memory_stats": memory_stats,
                "initialization_status": {
                    "initialized": self._initialized,
                    "indexing_in_progress": self._indexing_in_progress,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get search stats: {e}")
            return {}

    async def clear_cache(self) -> bool:
        """Clear all search caches"""

        try:
            await self.enhanced_search.clear_cache()
            logger.info("Search caches cleared")
            return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""

        try:
            # Check enhanced search system
            search_health = await self.enhanced_search.health_check()

            # Check Redis connection
            redis_healthy = False
            if self.redis_client:
                try:
                    await asyncio.get_event_loop().run_in_executor(None, self.redis_client.ping)
                    redis_healthy = True
                except Exception:
                    pass

            # Check workspace access
            workspace_accessible = Path(self.workspace_path).exists()

            overall_status = (
                search_health["status"] == "healthy" and redis_healthy and workspace_accessible
            )

            return {
                "status": "healthy" if overall_status else "unhealthy",
                "components": {
                    "enhanced_search": search_health,
                    "redis_connection": redis_healthy,
                    "workspace_accessible": workspace_accessible,
                    "initialized": self._initialized,
                },
                "workspace_path": self.workspace_path,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "components": {
                    "enhanced_search": False,
                    "redis_connection": False,
                    "workspace_accessible": False,
                    "initialized": False,
                },
            }

    async def _needs_indexing(self) -> bool:
        """Check if workspace needs indexing"""

        try:
            # Check if vector store has any documents
            stats = await self.enhanced_search.vector_store.get_stats()
            if not stats or stats.get("num_docs", 0) == 0:
                return True

            # Could add more sophisticated checks here
            # (e.g., check modification times, file counts, etc.)

            return False

        except Exception:
            return True

    async def _index_workspace(self, force: bool = False) -> bool:
        """Index the workspace"""

        try:
            logger.info(f"Starting workspace indexing: {self.workspace_path}")

            # Use batch indexer to index workspace
            result = await self.batch_indexer.batch_index_files(force_reindex=force)
            success = bool(result.get("indexed_count", 0) > 0 or result.get("error_count", 0) == 0)

            if success:
                logger.info("Workspace indexing completed successfully")
            else:
                logger.error("Workspace indexing failed")

            return success

        except Exception as e:
            logger.error(f"Failed to index workspace: {e}")
            return False

    def __del__(self):
        """Cleanup on deletion"""

        try:
            if hasattr(self, "redis_client") and self.redis_client:
                # Close Redis connection if needed
                pass
        except Exception:
            pass
