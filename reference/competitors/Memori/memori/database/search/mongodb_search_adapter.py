"""
MongoDB-specific search adapter with Atlas Vector Search support
"""

from datetime import datetime, timezone
from typing import Any

from loguru import logger

try:
    import pymongo  # noqa: F401
    from pymongo.collection import Collection  # noqa: F401
    from pymongo.errors import OperationFailure

    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

from ...utils.exceptions import ValidationError
from ...utils.input_validator import DatabaseInputValidator
from ..connectors.base_connector import BaseSearchAdapter
from ..connectors.mongodb_connector import MongoDBConnector


class MongoDBSearchAdapter(BaseSearchAdapter):
    """MongoDB-specific search implementation with Atlas Vector Search support"""

    def __init__(self, connector: MongoDBConnector):
        """Initialize MongoDB search adapter"""
        if not PYMONGO_AVAILABLE:
            raise ImportError(
                "pymongo is required for MongoDB support. Install with: pip install pymongo"
            )

        super().__init__(connector)
        self.mongodb_connector = connector
        self.database = connector.get_database()

        # Collection references
        self.short_term_collection = connector.get_collection("short_term_memory")
        self.long_term_collection = connector.get_collection("long_term_memory")

        # Check capabilities
        self._vector_search_available = None
        self._text_search_available = None

    def execute_fulltext_search(
        self,
        query: str,
        namespace: str = "default",
        category_filter: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Execute MongoDB text search with proper validation"""
        try:
            # Validate all parameters
            validated = DatabaseInputValidator.validate_search_params(
                query, namespace, category_filter, limit
            )

            # Check if text search is available
            if not self._check_text_search_available():
                logger.debug("Text search not available, falling back to regex search")
                return self.execute_fallback_search(
                    validated["query"],
                    validated["namespace"],
                    validated["category_filter"],
                    validated["limit"],
                )

            # Execute MongoDB text search
            return self._execute_mongodb_text_search(
                validated["query"],
                validated["namespace"],
                validated["category_filter"],
                validated["limit"],
            )

        except ValidationError as e:
            logger.error(f"Invalid search parameters: {e}")
            return []
        except Exception as e:
            logger.error(f"MongoDB text search failed: {e}")
            # Fallback to regex search on error
            return self.execute_fallback_search(
                query, namespace, category_filter, limit
            )

    def _execute_mongodb_text_search(
        self,
        query: str,
        namespace: str,
        category_filter: list[str] | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Execute MongoDB $text search across collections"""
        results = []

        # Search both collections
        collections = [
            (self.short_term_collection, "short_term"),
            (self.long_term_collection, "long_term"),
        ]

        for collection, memory_type in collections:
            try:
                # Build search filter
                search_filter: dict[str, Any] = {
                    "$text": {"$search": query},
                    "namespace": namespace,
                }

                if category_filter:
                    search_filter["category_primary"] = {"$in": category_filter}

                # For short-term memories, exclude expired ones
                if memory_type == "short_term":
                    search_filter["$or"] = [
                        {"expires_at": {"$exists": False}},
                        {"expires_at": None},
                        {"expires_at": {"$gt": datetime.now(timezone.utc)}},
                    ]

                # Execute search with text score
                cursor = (
                    collection.find(search_filter, {"score": {"$meta": "textScore"}})
                    .sort([("score", {"$meta": "textScore"}), ("importance_score", -1)])
                    .limit(limit)
                )

                # Process results
                for document in cursor:
                    memory = self._convert_document_to_memory(document)
                    memory["memory_type"] = memory_type
                    memory["search_strategy"] = "mongodb_text"
                    memory["text_score"] = document.get("score", 0)
                    results.append(memory)

            except Exception as e:
                logger.warning(f"Text search failed for {memory_type}: {e}")
                continue

        # Sort by text score and importance
        results.sort(
            key=lambda x: (x.get("text_score", 0), x.get("importance_score", 0)),
            reverse=True,
        )

        return results[:limit]

    def execute_vector_search(
        self,
        query_vector: list[float],
        namespace: str = "default",
        category_filter: list[str] | None = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """Execute MongoDB Atlas Vector Search"""
        try:
            if not self._check_vector_search_available():
                logger.warning("Vector search not available in this MongoDB deployment")
                return []

            # Validate inputs
            if not query_vector or not isinstance(query_vector, list):
                raise ValueError("query_vector must be a non-empty list of floats")

            # Build vector search pipeline
            pipeline = self._build_vector_search_pipeline(
                query_vector, namespace, category_filter, limit, similarity_threshold
            )

            # Execute vector search on long-term memory (primary collection for vectors)
            try:
                cursor = self.long_term_collection.aggregate(pipeline)
                results = []

                for document in cursor:
                    memory = self._convert_document_to_memory(document)
                    memory["memory_type"] = "long_term"
                    memory["search_strategy"] = "vector_search"
                    memory["vector_score"] = document.get("score", 0)
                    results.append(memory)

                logger.debug(f"Vector search returned {len(results)} results")
                return results

            except OperationFailure as e:
                if "vector search" in str(e).lower():
                    logger.error(f"Vector search not configured properly: {e}")
                    return []
                else:
                    raise

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def _build_vector_search_pipeline(
        self,
        query_vector: list[float],
        namespace: str,
        category_filter: list[str] | None,
        limit: int,
        similarity_threshold: float,
    ) -> list[dict[str, Any]]:
        """Build MongoDB aggregation pipeline for vector search"""
        pipeline = [
            # Vector search stage (Atlas only)
            {
                "$vectorSearch": {
                    "index": "vector_search_index",  # Must be created in Atlas
                    "path": "embedding_vector",
                    "queryVector": query_vector,
                    "numCandidates": min(limit * 10, 1000),  # Search more candidates
                    "limit": limit * 2,  # Get more results to filter
                }
            },
            # Add similarity score
            {"$addFields": {"score": {"$meta": "vectorSearchScore"}}},
            # Filter by similarity threshold
            {
                "$match": {
                    "score": {"$gte": similarity_threshold},
                    "namespace": namespace,
                }
            },
        ]

        # Add category filter if specified
        if category_filter:
            pipeline.append({"$match": {"category_primary": {"$in": category_filter}}})

        # Final projection and limit
        pipeline.extend(
            [
                {
                    "$project": {
                        "_id": 1,
                        "memory_id": 1,
                        "searchable_content": 1,
                        "summary": 1,
                        "importance_score": 1,
                        "category_primary": 1,
                        "namespace": 1,
                        "classification": 1,
                        "topic": 1,
                        "created_at": 1,
                        "confidence_score": 1,
                        "score": 1,
                    }
                },
                {"$limit": limit},
            ]
        )

        return pipeline

    def execute_hybrid_search(
        self,
        query: str,
        query_vector: list[float] | None = None,
        namespace: str = "default",
        category_filter: list[str] | None = None,
        limit: int = 10,
        text_weight: float = 0.5,
        vector_weight: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Execute hybrid search combining text and vector search"""
        try:
            text_results = []
            vector_results = []

            # Execute text search
            if query:
                text_results = self.execute_fulltext_search(
                    query, namespace, category_filter, limit * 2
                )

            # Execute vector search if available and vector provided
            if query_vector and self._check_vector_search_available():
                vector_results = self.execute_vector_search(
                    query_vector, namespace, category_filter, limit * 2
                )

            # Combine and score results
            return self._combine_search_results(
                text_results, vector_results, text_weight, vector_weight, limit
            )

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            # Fallback to text search only
            return self.execute_fulltext_search(
                query, namespace, category_filter, limit
            )

    def _combine_search_results(
        self,
        text_results: list[dict[str, Any]],
        vector_results: list[dict[str, Any]],
        text_weight: float,
        vector_weight: float,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Combine text and vector search results with weighted scoring"""
        # Create lookup for faster deduplication
        seen_memories = {}
        combined_results = []

        # Process text results
        for result in text_results:
            memory_id = result.get("memory_id")
            if memory_id:
                text_score = result.get("text_score", 0)
                importance_score = result.get("importance_score", 0)

                combined_score = (text_score * text_weight) + (importance_score * 0.1)

                result["combined_score"] = combined_score
                result["has_text_match"] = True
                result["has_vector_match"] = False

                seen_memories[memory_id] = result
                combined_results.append(result)

        # Process vector results
        for result in vector_results:
            memory_id = result.get("memory_id")
            if memory_id:
                vector_score = result.get("vector_score", 0)
                importance_score = result.get("importance_score", 0)

                if memory_id in seen_memories:
                    # Update existing result with vector score
                    existing = seen_memories[memory_id]
                    existing_combined = existing.get("combined_score", 0)
                    vector_combined = (vector_score * vector_weight) + (
                        importance_score * 0.1
                    )

                    # Combine scores
                    existing["combined_score"] = existing_combined + vector_combined
                    existing["has_vector_match"] = True
                    existing["vector_score"] = vector_score
                    existing["search_strategy"] = "hybrid"
                else:
                    # New result from vector search
                    combined_score = (vector_score * vector_weight) + (
                        importance_score * 0.1
                    )

                    result["combined_score"] = combined_score
                    result["has_text_match"] = False
                    result["has_vector_match"] = True

                    seen_memories[memory_id] = result
                    combined_results.append(result)

        # Sort by combined score
        combined_results.sort(key=lambda x: x.get("combined_score", 0), reverse=True)

        logger.debug(
            f"Hybrid search combined {len(text_results)} text + {len(vector_results)} vector results"
        )
        return combined_results[:limit]

    def create_search_indexes(self) -> list[str]:
        """Create MongoDB-specific search indexes"""
        indexes_created = []

        try:
            # Create text indexes
            collections = [
                (self.short_term_collection, "short_term_memory"),
                (self.long_term_collection, "long_term_memory"),
            ]

            for collection, collection_name in collections:
                try:
                    # Create text index for full-text search
                    collection.create_index(
                        [("searchable_content", "text"), ("summary", "text")],
                        name=f"{collection_name}_text_search",
                        background=True,
                    )

                    indexes_created.append(f"{collection_name}_text_search")
                    logger.info(f"Created text index for {collection_name}")

                except Exception as e:
                    logger.warning(
                        f"Failed to create text index for {collection_name}: {e}"
                    )

            # Note about vector indexes
            if self.mongodb_connector.supports_vector_search():
                logger.info(
                    "Vector search is supported. Create vector indexes via MongoDB Atlas UI or Admin API."
                )
                indexes_created.append("vector_search_index (manual creation required)")
            else:
                logger.info("Vector search not supported in this deployment")

            return indexes_created

        except Exception as e:
            logger.error(f"Failed to create search indexes: {e}")
            return indexes_created

    def translate_search_query(self, query: str) -> str:
        """Translate search query to MongoDB text search syntax"""
        if not query or not query.strip():
            return '""'  # Empty query

        # MongoDB text search supports:
        # - Phrase search: "exact phrase"
        # - Term search: term1 term2
        # - Negation: -unwanted
        # - OR operations: term1 OR term2

        # For safety, we'll do minimal processing
        sanitized = query.strip()

        # If query contains special characters, wrap in quotes for phrase search
        if any(char in sanitized for char in ['"', "(", ")", "-", "|"]):
            # Remove existing quotes and wrap the whole thing
            sanitized = sanitized.replace('"', "")
            return f'"{sanitized}"'

        return sanitized

    def execute_fallback_search(
        self,
        query: str,
        namespace: str = "default",
        category_filter: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Execute regex-based fallback search for MongoDB"""
        try:
            results = []

            # Create case-insensitive regex pattern
            regex_pattern = {"$regex": query, "$options": "i"}

            collections = [
                (self.short_term_collection, "short_term"),
                (self.long_term_collection, "long_term"),
            ]

            for collection, memory_type in collections:
                try:
                    # Build search filter using regex
                    search_filter = {
                        "$or": [
                            {"searchable_content": regex_pattern},
                            {"summary": regex_pattern},
                        ],
                        "namespace": namespace,
                    }

                    if category_filter:
                        search_filter["category_primary"] = {"$in": category_filter}

                    # For short-term memories, exclude expired ones
                    if memory_type == "short_term":
                        search_filter["$and"] = [
                            {"$or": search_filter["$or"]},
                            {"namespace": namespace},
                            {
                                "$or": [
                                    {"expires_at": {"$exists": False}},
                                    {"expires_at": None},
                                    {"expires_at": {"$gt": datetime.now(timezone.utc)}},
                                ]
                            },
                        ]
                        # Remove the top-level filters since they're now in $and
                        del search_filter["$or"]
                        del search_filter["namespace"]

                        if category_filter:
                            search_filter["$and"].append(
                                {"category_primary": {"$in": category_filter}}
                            )
                            del search_filter["category_primary"]

                    # Execute regex search
                    cursor = (
                        collection.find(search_filter)
                        .sort([("importance_score", -1), ("created_at", -1)])
                        .limit(limit)
                    )

                    for document in cursor:
                        memory = self._convert_document_to_memory(document)
                        memory["memory_type"] = memory_type
                        memory["search_strategy"] = "regex_fallback"
                        results.append(memory)

                except Exception as e:
                    logger.warning(f"Regex search failed for {memory_type}: {e}")
                    continue

            # Sort by importance score
            results.sort(key=lambda x: x.get("importance_score", 0), reverse=True)

            logger.debug(f"Regex fallback search returned {len(results)} results")
            return results[:limit]

        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return []

    def _convert_document_to_memory(self, document: dict[str, Any]) -> dict[str, Any]:
        """Convert MongoDB document to memory format"""
        if not document:
            return {}

        memory = document.copy()

        # Convert ObjectId to string
        if "_id" in memory:
            memory["_id"] = str(memory["_id"])

        # Convert datetime objects to ISO strings for JSON compatibility
        datetime_fields = [
            "created_at",
            "expires_at",
            "last_accessed",
            "extraction_timestamp",
        ]
        for field in datetime_fields:
            if field in memory and isinstance(memory[field], datetime):
                memory[field] = memory[field].isoformat()

        return memory

    def _check_text_search_available(self) -> bool:
        """Check if MongoDB text search is available"""
        if self._text_search_available is not None:
            return self._text_search_available

        try:
            # Try to get text indexes
            indexes = list(self.short_term_collection.list_indexes())
            self._text_search_available = any(
                "text" in str(index.get("key", {})) for index in indexes
            )
        except Exception:
            self._text_search_available = False

        return self._text_search_available

    def _check_vector_search_available(self) -> bool:
        """Check if MongoDB Atlas Vector Search is available"""
        if self._vector_search_available is not None:
            return self._vector_search_available

        try:
            # This is a comprehensive check for vector search availability
            self._vector_search_available = (
                self.mongodb_connector.supports_vector_search()
            )

            # Additional check: try to see if we have vector search indexes
            if self._vector_search_available:
                try:
                    # Try a simple vector search to see if indexes exist
                    # This is a minimal test query
                    test_pipeline = [
                        {
                            "$vectorSearch": {
                                "index": "vector_search_index",
                                "path": "embedding_vector",
                                "queryVector": [0.0] * 1536,  # Dummy vector
                                "numCandidates": 1,
                                "limit": 1,
                            }
                        },
                        {"$limit": 0},  # Don't return any results
                    ]

                    # If this doesn't throw an error, vector search is properly configured
                    list(self.long_term_collection.aggregate(test_pipeline))
                    logger.debug("Vector search is available and configured")

                except OperationFailure as e:
                    if "vector search" in str(e).lower() or "index" in str(e).lower():
                        logger.warning(
                            "Vector search is supported but not configured (missing indexes)"
                        )
                        self._vector_search_available = False
                    else:
                        # Other errors might still allow vector search
                        pass

        except Exception:
            self._vector_search_available = False

        return self._vector_search_available

    def optimize_search_performance(self):
        """Optimize MongoDB search performance"""
        try:
            # Update collection statistics for better query planning
            collections = [self.short_term_collection, self.long_term_collection]

            for collection in collections:
                try:
                    # MongoDB doesn't have ANALYZE like SQL, but we can:
                    # 1. Ensure indexes are being used effectively
                    # 2. Check for slow operations

                    # Get collection stats
                    stats = self.database.command("collStats", collection.name)
                    logger.debug(
                        f"Collection {collection.name} stats: {stats.get('count', 0)} documents"
                    )

                    # List indexes to ensure they exist
                    indexes = list(collection.list_indexes())
                    logger.debug(
                        f"Collection {collection.name} has {len(indexes)} indexes"
                    )

                except Exception as e:
                    logger.warning(f"Failed to get stats for {collection.name}: {e}")

            logger.info("MongoDB search optimization completed")

        except Exception as e:
            logger.warning(f"MongoDB search optimization failed: {e}")

    def get_search_capabilities(self) -> dict[str, Any]:
        """Get MongoDB search capabilities"""
        return {
            "text_search": self._check_text_search_available(),
            "vector_search": self._check_vector_search_available(),
            "regex_search": True,  # Always available in MongoDB
            "faceted_search": True,  # MongoDB aggregation supports faceting
            "geospatial_search": True,  # MongoDB has good geospatial support
            "full_text_operators": [
                "$text",  # Text search
                "$regex",  # Pattern matching
                "$search",  # Atlas Search (if available)
            ],
            "supported_similarity_metrics": ["cosine", "euclidean", "dotProduct"],
            "max_vector_dimensions": 2048,  # Atlas limit
            "hybrid_search": True,
        }
