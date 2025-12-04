"""
MongoDB schema generator for Memori
Defines collections, validation rules, and indexes for MongoDB
"""

from typing import Any

from ..connectors.base_connector import BaseSchemaGenerator, DatabaseType


class MongoDBSchemaGenerator(BaseSchemaGenerator):
    """MongoDB-specific schema generator"""

    def __init__(self):
        super().__init__(DatabaseType.MONGODB)

    def generate_core_schema(self) -> str:
        """
        Generate MongoDB schema documentation
        Note: MongoDB is schemaless, but we provide documentation for expected structure
        """
        return """
# MongoDB Collections Schema for Memori

## Collection: chat_history
Purpose: Store chat interactions between users and AI
Expected Document Structure:
{
    "_id": ObjectId,
    "chat_id": "string (unique)",
    "user_input": "string",
    "ai_output": "string",
    "model": "string",
    "timestamp": ISODate,
    "session_id": "string",
    "namespace": "string (default: 'default')",
    "tokens_used": "number",
    "metadata": "object (optional)"
}

## Collection: short_term_memory
Purpose: Store temporary memories with expiration
Expected Document Structure:
{
    "_id": ObjectId,
    "memory_id": "string (unique)",
    "chat_id": "string (optional, reference to chat_history)",
    "processed_data": "object",
    "importance_score": "number (0.0-1.0)",
    "category_primary": "string",
    "retention_type": "string (default: 'short_term')",
    "namespace": "string (default: 'default')",
    "created_at": ISODate,
    "expires_at": "ISODate (optional)",
    "access_count": "number (default: 0)",
    "last_accessed": "ISODate (optional)",
    "searchable_content": "string",
    "summary": "string",
    "is_permanent_context": "boolean (default: false)"
}

## Collection: long_term_memory
Purpose: Store persistent memories with enhanced metadata
Expected Document Structure:
{
    "_id": ObjectId,
    "memory_id": "string (unique)",
    "original_chat_id": "string (optional)",
    "processed_data": "object",
    "importance_score": "number (0.0-1.0)",
    "category_primary": "string",
    "retention_type": "string (default: 'long_term')",
    "namespace": "string (default: 'default')",
    "created_at": ISODate,
    "access_count": "number (default: 0)",
    "last_accessed": "ISODate (optional)",
    "searchable_content": "string",
    "summary": "string",
    "novelty_score": "number (0.0-1.0, default: 0.5)",
    "relevance_score": "number (0.0-1.0, default: 0.5)",
    "actionability_score": "number (0.0-1.0, default: 0.5)",

    // Enhanced Classification Fields
    "classification": "string (default: 'conversational')",
    "memory_importance": "string (default: 'medium')",
    "topic": "string (optional)",
    "entities_json": "array (default: [])",
    "keywords_json": "array (default: [])",

    // Conscious Context Flags
    "is_user_context": "boolean (default: false)",
    "is_preference": "boolean (default: false)",
    "is_skill_knowledge": "boolean (default: false)",
    "is_current_project": "boolean (default: false)",
    "promotion_eligible": "boolean (default: false)",

    // Memory Management
    "duplicate_of": "string (optional)",
    "supersedes_json": "array (default: [])",
    "related_memories_json": "array (default: [])",

    // Technical Metadata
    "confidence_score": "number (0.0-1.0, default: 0.8)",
    "extraction_timestamp": ISODate,
    "classification_reason": "string (optional)",

    // Processing Status
    "processed_for_duplicates": "boolean (default: false)",
    "conscious_processed": "boolean (default: false)",

    // Vector Search Support (MongoDB Atlas)
    "embedding_vector": "array<number> (optional, for vector search)"
}
"""

    def generate_indexes(self) -> str:
        """Generate MongoDB index creation documentation"""
        return """
# MongoDB Indexes for Memori Collections

## Indexes for chat_history collection:
- chat_id (unique)
- namespace + session_id (compound)
- timestamp (descending)
- model

## Indexes for short_term_memory collection:
- memory_id (unique)
- namespace + category_primary + importance_score (compound, descending on score)
- expires_at
- created_at (descending)
- text index on searchable_content + summary

## Indexes for long_term_memory collection:
- memory_id (unique)
- namespace + category_primary + importance_score (compound, descending on score)
- classification
- topic
- created_at (descending)
- text index on searchable_content + summary
- is_user_context + is_preference + is_skill_knowledge + promotion_eligible (compound)
- conscious_processed
- processed_for_duplicates
- confidence_score

## Vector Search Index (Atlas only):
- embedding_vector (vector search index for similarity search)
"""

    def generate_search_setup(self) -> str:
        """Generate MongoDB search setup documentation"""
        return """
# MongoDB Search Configuration

## Text Search Indexes:
MongoDB text indexes are automatically created for:
- short_term_memory: searchable_content, summary
- long_term_memory: searchable_content, summary

## Vector Search (MongoDB Atlas only):
For vector similarity search, create a vector search index on the 'embedding_vector' field:
- Field: embedding_vector
- Type: vector
- Dimensions: 1536 (or your embedding dimension)
- Similarity: cosine (or euclidean/dotProduct)

Vector search indexes must be created through MongoDB Atlas UI or Atlas Admin API.

## Search Strategies:
1. Text Search: Use MongoDB $text operator for full-text search
2. Regex Search: Fallback using $regex for pattern matching
3. Vector Search: Use Atlas Vector Search for semantic similarity (if available)
"""

    def get_data_type_mappings(self) -> dict[str, str]:
        """Get MongoDB data type mappings"""
        return {
            "string": "string",
            "number": "number",
            "boolean": "boolean",
            "date": "date",
            "object": "object",
            "array": "array",
            "objectId": "objectId",
        }

    def generate_collections_schema(self) -> dict[str, dict[str, Any]]:
        """Generate MongoDB collections with validation schemas"""
        return {
            "chat_history": {
                "validator": {
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": [
                            "chat_id",
                            "user_input",
                            "ai_output",
                            "model",
                            "timestamp",
                            "session_id",
                            "namespace",
                        ],
                        "properties": {
                            "chat_id": {
                                "bsonType": "string",
                                "description": "Unique chat interaction identifier",
                            },
                            "user_input": {
                                "bsonType": "string",
                                "description": "User's input message",
                            },
                            "ai_output": {
                                "bsonType": "string",
                                "description": "AI's response message",
                            },
                            "model": {
                                "bsonType": "string",
                                "description": "AI model used for response",
                            },
                            "timestamp": {
                                "bsonType": "date",
                                "description": "Interaction timestamp",
                            },
                            "session_id": {
                                "bsonType": "string",
                                "description": "Session identifier",
                            },
                            "namespace": {
                                "bsonType": "string",
                                "description": "Memory namespace",
                            },
                            "tokens_used": {
                                "bsonType": "int",
                                "minimum": 0,
                                "description": "Number of tokens used",
                            },
                            "metadata": {
                                "bsonType": "object",
                                "description": "Additional metadata",
                            },
                        },
                    }
                },
                "validationAction": "warn",  # Use "error" for strict validation
                "validationLevel": "moderate",
            },
            "short_term_memory": {
                "validator": {
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": [
                            "memory_id",
                            "processed_data",
                            "importance_score",
                            "category_primary",
                            "namespace",
                            "searchable_content",
                            "summary",
                        ],
                        "properties": {
                            "memory_id": {
                                "bsonType": "string",
                                "description": "Unique memory identifier",
                            },
                            "chat_id": {
                                "bsonType": "string",
                                "description": "Reference to chat interaction",
                            },
                            "processed_data": {
                                "bsonType": "object",
                                "description": "Processed memory data",
                            },
                            "importance_score": {
                                "bsonType": "double",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Memory importance score",
                            },
                            "category_primary": {
                                "bsonType": "string",
                                "description": "Primary memory category",
                            },
                            "retention_type": {
                                "bsonType": "string",
                                "description": "Memory retention type",
                            },
                            "namespace": {
                                "bsonType": "string",
                                "description": "Memory namespace",
                            },
                            "created_at": {
                                "bsonType": "date",
                                "description": "Memory creation timestamp",
                            },
                            "expires_at": {
                                "bsonType": ["date", "null"],
                                "description": "Memory expiration timestamp",
                            },
                            "access_count": {
                                "bsonType": "int",
                                "minimum": 0,
                                "description": "Memory access count",
                            },
                            "last_accessed": {
                                "bsonType": ["date", "null"],
                                "description": "Last access timestamp",
                            },
                            "searchable_content": {
                                "bsonType": "string",
                                "description": "Searchable text content",
                            },
                            "summary": {
                                "bsonType": "string",
                                "description": "Memory summary",
                            },
                            "is_permanent_context": {
                                "bsonType": "bool",
                                "description": "Whether memory is permanent context",
                            },
                        },
                    }
                },
                "validationAction": "warn",
                "validationLevel": "moderate",
            },
            "long_term_memory": {
                "validator": {
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": [
                            "memory_id",
                            "processed_data",
                            "importance_score",
                            "category_primary",
                            "namespace",
                            "searchable_content",
                            "summary",
                        ],
                        "properties": {
                            "memory_id": {
                                "bsonType": "string",
                                "description": "Unique memory identifier",
                            },
                            "original_chat_id": {
                                "bsonType": "string",
                                "description": "Original chat interaction reference",
                            },
                            "processed_data": {
                                "bsonType": "object",
                                "description": "Processed memory data",
                            },
                            "importance_score": {
                                "bsonType": "double",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Memory importance score",
                            },
                            "category_primary": {
                                "bsonType": "string",
                                "description": "Primary memory category",
                            },
                            "retention_type": {
                                "bsonType": "string",
                                "description": "Memory retention type",
                            },
                            "namespace": {
                                "bsonType": "string",
                                "description": "Memory namespace",
                            },
                            "created_at": {
                                "bsonType": "date",
                                "description": "Memory creation timestamp",
                            },
                            "access_count": {
                                "bsonType": "int",
                                "minimum": 0,
                                "description": "Memory access count",
                            },
                            "searchable_content": {
                                "bsonType": "string",
                                "description": "Searchable text content",
                            },
                            "summary": {
                                "bsonType": "string",
                                "description": "Memory summary",
                            },
                            "novelty_score": {
                                "bsonType": "double",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Memory novelty score",
                            },
                            "relevance_score": {
                                "bsonType": "double",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Memory relevance score",
                            },
                            "actionability_score": {
                                "bsonType": "double",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Memory actionability score",
                            },
                            "classification": {
                                "bsonType": "string",
                                "description": "Memory classification",
                            },
                            "memory_importance": {
                                "bsonType": "string",
                                "enum": ["low", "medium", "high", "critical"],
                                "description": "Memory importance level",
                            },
                            "topic": {
                                "bsonType": "string",
                                "description": "Memory topic",
                            },
                            "entities_json": {
                                "bsonType": "array",
                                "description": "Extracted entities",
                            },
                            "keywords_json": {
                                "bsonType": "array",
                                "description": "Extracted keywords",
                            },
                            "is_user_context": {
                                "bsonType": "bool",
                                "description": "Whether memory is user context",
                            },
                            "is_preference": {
                                "bsonType": "bool",
                                "description": "Whether memory is user preference",
                            },
                            "is_skill_knowledge": {
                                "bsonType": "bool",
                                "description": "Whether memory is skill knowledge",
                            },
                            "is_current_project": {
                                "bsonType": "bool",
                                "description": "Whether memory relates to current project",
                            },
                            "promotion_eligible": {
                                "bsonType": "bool",
                                "description": "Whether memory is eligible for promotion",
                            },
                            "duplicate_of": {
                                "bsonType": "string",
                                "description": "Reference to original if duplicate",
                            },
                            "supersedes_json": {
                                "bsonType": "array",
                                "description": "Memories this supersedes",
                            },
                            "related_memories_json": {
                                "bsonType": "array",
                                "description": "Related memory references",
                            },
                            "confidence_score": {
                                "bsonType": "double",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Memory confidence score",
                            },
                            "extraction_timestamp": {
                                "bsonType": "date",
                                "description": "Data extraction timestamp",
                            },
                            "classification_reason": {
                                "bsonType": "string",
                                "description": "Reason for classification",
                            },
                            "processed_for_duplicates": {
                                "bsonType": "bool",
                                "description": "Whether processed for duplicates",
                            },
                            "conscious_processed": {
                                "bsonType": "bool",
                                "description": "Whether consciously processed",
                            },
                            "embedding_vector": {
                                "bsonType": "array",
                                "items": {"bsonType": "double"},
                                "description": "Vector embedding for similarity search",
                            },
                        },
                    }
                },
                "validationAction": "warn",
                "validationLevel": "moderate",
            },
        }

    def generate_indexes_schema(self) -> dict[str, list[dict[str, Any]]]:
        """Generate index specifications for MongoDB collections"""
        return {
            "chat_history": [
                {"keys": [("chat_id", 1)], "name": "idx_chat_id", "unique": True},
                {
                    "keys": [("namespace", 1), ("session_id", 1)],
                    "name": "idx_namespace_session",
                },
                {"keys": [("timestamp", -1)], "name": "idx_timestamp"},
                {"keys": [("model", 1)], "name": "idx_model"},
            ],
            "short_term_memory": [
                {"keys": [("memory_id", 1)], "name": "idx_memory_id", "unique": True},
                {
                    "keys": [
                        ("namespace", 1),
                        ("category_primary", 1),
                        ("importance_score", -1),
                    ],
                    "name": "idx_namespace_category_importance",
                },
                {"keys": [("expires_at", 1)], "name": "idx_expires_at", "sparse": True},
                {"keys": [("created_at", -1)], "name": "idx_created_at"},
                {"keys": [("chat_id", 1)], "name": "idx_chat_id", "sparse": True},
                {
                    "keys": [("searchable_content", "text"), ("summary", "text")],
                    "name": "idx_text_search",
                },
                {
                    "keys": [("is_permanent_context", 1)],
                    "name": "idx_permanent_context",
                },
                {
                    "keys": [("access_count", -1), ("last_accessed", -1)],
                    "name": "idx_access_pattern",
                },
            ],
            "long_term_memory": [
                {"keys": [("memory_id", 1)], "name": "idx_memory_id", "unique": True},
                {
                    "keys": [
                        ("namespace", 1),
                        ("category_primary", 1),
                        ("importance_score", -1),
                    ],
                    "name": "idx_namespace_category_importance",
                },
                {"keys": [("classification", 1)], "name": "idx_classification"},
                {"keys": [("topic", 1)], "name": "idx_topic", "sparse": True},
                {"keys": [("created_at", -1)], "name": "idx_created_at"},
                {
                    "keys": [("searchable_content", "text"), ("summary", "text")],
                    "name": "idx_text_search",
                },
                {
                    "keys": [
                        ("is_user_context", 1),
                        ("is_preference", 1),
                        ("is_skill_knowledge", 1),
                        ("promotion_eligible", 1),
                    ],
                    "name": "idx_conscious_flags",
                },
                {
                    "keys": [("conscious_processed", 1)],
                    "name": "idx_conscious_processed",
                },
                {
                    "keys": [("processed_for_duplicates", 1)],
                    "name": "idx_duplicates_processed",
                },
                {"keys": [("confidence_score", -1)], "name": "idx_confidence"},
                {"keys": [("memory_importance", 1)], "name": "idx_memory_importance"},
                {
                    "keys": [
                        ("novelty_score", -1),
                        ("relevance_score", -1),
                        ("actionability_score", -1),
                    ],
                    "name": "idx_scores",
                },
                {
                    "keys": [("access_count", -1), ("last_accessed", -1)],
                    "name": "idx_access_pattern",
                },
            ],
        }

    def generate_vector_search_config(self) -> dict[str, Any]:
        """Generate vector search configuration for MongoDB Atlas"""
        return {
            "collection": "long_term_memory",
            "vector_index": {
                "name": "vector_search_index",
                "definition": {
                    "fields": [
                        {
                            "path": "embedding_vector",
                            "type": "vector",
                            "similarity": "cosine",
                            "dimensions": 1536,  # OpenAI ada-002 dimensions
                        }
                    ]
                },
            },
            "search_pipeline": [
                {
                    "$vectorSearch": {
                        "index": "vector_search_index",
                        "path": "embedding_vector",
                        "queryVector": "<<QUERY_VECTOR>>",  # Placeholder
                        "numCandidates": 100,
                        "limit": 10,
                    }
                },
                {
                    "$project": {
                        "memory_id": 1,
                        "searchable_content": 1,
                        "summary": 1,
                        "importance_score": 1,
                        "category_primary": 1,
                        "namespace": 1,
                        "score": {"$meta": "vectorSearchScore"},
                    }
                },
            ],
        }

    def generate_full_schema(self) -> str:
        """Generate complete MongoDB schema documentation"""
        schema_parts = [
            "# MongoDB Schema for Memori v2.0",
            "# Complete database schema with collections, validation, and indexes",
            "",
            self.generate_core_schema(),
            "",
            self.generate_indexes(),
            "",
            self.generate_search_setup(),
            "",
            "# Note: This is documentation only. MongoDB collections and indexes",
            "# are created programmatically by the MongoDBConnector and MongoDBAdapter.",
            "# Vector search indexes must be created via MongoDB Atlas UI or Admin API.",
        ]
        return "\n".join(schema_parts)

    def get_migration_strategy(self) -> dict[str, Any]:
        """Get strategy for migrating from SQL databases to MongoDB"""
        return {
            "approach": "ETL Pipeline",
            "steps": [
                "Extract data from source SQL database",
                "Transform data to MongoDB document format",
                "Handle data type conversions (timestamps, JSON, etc.)",
                "Load data into MongoDB collections",
                "Create indexes after data load",
                "Validate data integrity",
            ],
            "considerations": [
                "SQL foreign keys become document references or embedded documents",
                "JSON fields in SQL become native objects in MongoDB",
                "SQL joins become MongoDB aggregation pipelines or embedded documents",
                "Index strategy differs significantly between SQL and MongoDB",
                "Vector embeddings can be stored natively in MongoDB documents",
            ],
            "tools": [
                "MongoDB Compass for visual schema design",
                "MongoDB Database Tools for import/export",
                "Custom ETL scripts for complex transformations",
                "MongoDB Atlas Data Lake for large-scale migrations",
            ],
        }
