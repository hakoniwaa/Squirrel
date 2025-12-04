"""
MySQL schema generator for Memori v2.0
Converts SQLite schema to MySQL-compatible schema with FULLTEXT search
"""

from ..connectors.base_connector import BaseSchemaGenerator, DatabaseType


class MySQLSchemaGenerator(BaseSchemaGenerator):
    """MySQL-specific schema generator"""

    def __init__(self):
        super().__init__(DatabaseType.MYSQL)

    def get_data_type_mappings(self) -> dict[str, str]:
        """Get MySQL-specific data type mappings from SQLite"""
        return {
            "TEXT": "TEXT",
            "INTEGER": "INT",
            "REAL": "DECIMAL(10,2)",
            "BOOLEAN": "BOOLEAN",
            "TIMESTAMP": "TIMESTAMP",
            "AUTOINCREMENT": "AUTO_INCREMENT",
        }

    def generate_core_schema(self) -> str:
        """Generate core tables schema for MySQL"""
        return """
-- Chat History Table
CREATE TABLE IF NOT EXISTS chat_history (
    chat_id VARCHAR(255) PRIMARY KEY,
    user_input TEXT NOT NULL,
    ai_output TEXT NOT NULL,
    model VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL DEFAULT 'default',
    tokens_used INT DEFAULT 0,
    metadata JSON
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Short-term Memory Table
CREATE TABLE IF NOT EXISTS short_term_memory (
    memory_id VARCHAR(255) PRIMARY KEY,
    chat_id VARCHAR(255),
    processed_data JSON NOT NULL,
    importance_score DECIMAL(3,2) NOT NULL DEFAULT 0.5,
    category_primary VARCHAR(255) NOT NULL,
    retention_type VARCHAR(50) NOT NULL DEFAULT 'short_term',
    namespace VARCHAR(255) NOT NULL DEFAULT 'default',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    access_count INT DEFAULT 0,
    last_accessed TIMESTAMP NULL,
    searchable_content TEXT NOT NULL,
    summary TEXT NOT NULL,
    is_permanent_context BOOLEAN DEFAULT FALSE,
    INDEX idx_chat_id (chat_id),
    FOREIGN KEY (chat_id) REFERENCES chat_history (chat_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Long-term Memory Table
CREATE TABLE IF NOT EXISTS long_term_memory (
    memory_id VARCHAR(255) PRIMARY KEY,
    original_chat_id VARCHAR(255),
    processed_data JSON NOT NULL,
    importance_score DECIMAL(3,2) NOT NULL DEFAULT 0.5,
    category_primary VARCHAR(255) NOT NULL,
    retention_type VARCHAR(50) NOT NULL DEFAULT 'long_term',
    namespace VARCHAR(255) NOT NULL DEFAULT 'default',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    access_count INT DEFAULT 0,
    last_accessed TIMESTAMP NULL,
    searchable_content TEXT NOT NULL,
    summary TEXT NOT NULL,
    novelty_score DECIMAL(3,2) DEFAULT 0.5,
    relevance_score DECIMAL(3,2) DEFAULT 0.5,
    actionability_score DECIMAL(3,2) DEFAULT 0.5,

    -- Enhanced Classification Fields
    classification VARCHAR(50) NOT NULL DEFAULT 'conversational',
    memory_importance VARCHAR(20) NOT NULL DEFAULT 'medium',
    topic VARCHAR(255),
    entities_json JSON DEFAULT (JSON_ARRAY()),
    keywords_json JSON DEFAULT (JSON_ARRAY()),

    -- Conscious Context Flags
    is_user_context BOOLEAN DEFAULT FALSE,
    is_preference BOOLEAN DEFAULT FALSE,
    is_skill_knowledge BOOLEAN DEFAULT FALSE,
    is_current_project BOOLEAN DEFAULT FALSE,
    promotion_eligible BOOLEAN DEFAULT FALSE,

    -- Memory Management
    duplicate_of VARCHAR(255),
    supersedes_json JSON DEFAULT (JSON_ARRAY()),
    related_memories_json JSON DEFAULT (JSON_ARRAY()),

    -- Technical Metadata
    confidence_score DECIMAL(3,2) DEFAULT 0.8,
    extraction_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    classification_reason TEXT,

    -- Processing Status
    processed_for_duplicates BOOLEAN DEFAULT FALSE,
    conscious_processed BOOLEAN DEFAULT FALSE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

    def generate_indexes(self) -> str:
        """Generate MySQL-specific indexes"""
        return """
-- Chat History Indexes
CREATE INDEX idx_chat_namespace_session ON chat_history(namespace, session_id);
CREATE INDEX idx_chat_timestamp ON chat_history(timestamp);
CREATE INDEX idx_chat_model ON chat_history(model);

-- Short-term Memory Indexes
CREATE INDEX idx_short_term_namespace ON short_term_memory(namespace);
CREATE INDEX idx_short_term_category ON short_term_memory(category_primary);
CREATE INDEX idx_short_term_importance ON short_term_memory(importance_score);
CREATE INDEX idx_short_term_expires ON short_term_memory(expires_at);
CREATE INDEX idx_short_term_created ON short_term_memory(created_at);
CREATE INDEX idx_short_term_access ON short_term_memory(access_count, last_accessed);
CREATE INDEX idx_short_term_permanent ON short_term_memory(is_permanent_context);

-- Long-term Memory Indexes
CREATE INDEX idx_long_term_namespace ON long_term_memory(namespace);
CREATE INDEX idx_long_term_category ON long_term_memory(category_primary);
CREATE INDEX idx_long_term_importance ON long_term_memory(importance_score);
CREATE INDEX idx_long_term_created ON long_term_memory(created_at);
CREATE INDEX idx_long_term_access ON long_term_memory(access_count, last_accessed);
CREATE INDEX idx_long_term_scores ON long_term_memory(novelty_score, relevance_score, actionability_score);

-- Enhanced Classification Indexes
CREATE INDEX idx_long_term_classification ON long_term_memory(classification);
CREATE INDEX idx_long_term_memory_importance ON long_term_memory(memory_importance);
CREATE INDEX idx_long_term_topic ON long_term_memory(topic);
CREATE INDEX idx_long_term_conscious_flags ON long_term_memory(is_user_context, is_preference, is_skill_knowledge, promotion_eligible);
CREATE INDEX idx_long_term_conscious_processed ON long_term_memory(conscious_processed);
CREATE INDEX idx_long_term_duplicates ON long_term_memory(processed_for_duplicates);
CREATE INDEX idx_long_term_confidence ON long_term_memory(confidence_score);

-- Composite indexes for search optimization
CREATE INDEX idx_short_term_namespace_category_importance ON short_term_memory(namespace, category_primary, importance_score);
CREATE INDEX idx_long_term_namespace_category_importance ON long_term_memory(namespace, category_primary, importance_score);
"""

    def generate_search_setup(self) -> str:
        """Generate MySQL FULLTEXT search setup"""
        return """
-- MySQL FULLTEXT Search Indexes
-- These replace SQLite's FTS5 virtual table with MySQL's native FULLTEXT indexes

-- FULLTEXT index for short-term memory
ALTER TABLE short_term_memory ADD FULLTEXT INDEX ft_short_term_search (searchable_content, summary);

-- FULLTEXT index for long-term memory
ALTER TABLE long_term_memory ADD FULLTEXT INDEX ft_long_term_search (searchable_content, summary);

-- Additional FULLTEXT indexes for enhanced search capabilities
ALTER TABLE long_term_memory ADD FULLTEXT INDEX ft_long_term_topic (topic);

-- Note: MySQL FULLTEXT indexes are maintained automatically
-- No triggers needed like SQLite FTS5
"""

    def generate_mysql_specific_optimizations(self) -> str:
        """Generate MySQL-specific optimizations"""
        return """
-- MySQL-specific optimizations

-- Set InnoDB buffer pool size (if you have permission)
-- SET GLOBAL innodb_buffer_pool_size = 268435456;  -- 256MB

-- Optimize FULLTEXT search settings
-- SET GLOBAL ft_min_word_len = 3;
-- SET GLOBAL ft_boolean_syntax = ' +-><()~*:""&|';

-- Enable query cache (MySQL 5.7 and below)
-- SET GLOBAL query_cache_type = ON;
-- SET GLOBAL query_cache_size = 67108864;  -- 64MB
"""

    def generate_full_schema(self) -> str:
        """Generate complete MySQL schema"""
        schema_parts = [
            "-- Memori v2.0 MySQL Schema",
            "-- Generated schema for cross-database compatibility",
            "",
            "-- Set MySQL session variables for optimal performance",
            "SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';",
            "SET SESSION innodb_lock_wait_timeout = 30;",
            "",
            self.generate_core_schema(),
            "",
            self.generate_indexes(),
            "",
            self.generate_search_setup(),
            "",
            "-- Schema generation completed",
        ]
        return "\n".join(schema_parts)

    def get_migration_queries(self) -> list[str]:
        """Get queries to migrate from SQLite to MySQL"""
        return [
            # Note: These would be used for data migration from SQLite to MySQL
            # Data migration is complex and would require specialized tooling
            "-- Data migration queries would go here",
            "-- This requires extracting data from SQLite and inserting into MySQL",
            "-- with proper data type conversions and character encoding handling",
        ]
