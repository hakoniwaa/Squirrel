"""
MySQL-specific search adapter with FULLTEXT support and proper security
"""

from typing import Any

from loguru import logger

from ...utils.exceptions import ValidationError
from ...utils.input_validator import DatabaseInputValidator
from ...utils.query_builder import DatabaseDialect, DatabaseQueryExecutor
from ..connectors.base_connector import BaseDatabaseConnector, BaseSearchAdapter


class MySQLSearchAdapter(BaseSearchAdapter):
    """MySQL-specific search implementation with FULLTEXT and security measures"""

    def __init__(self, connector: BaseDatabaseConnector):
        super().__init__(connector)
        self.query_executor = DatabaseQueryExecutor(connector, DatabaseDialect.MYSQL)
        self._fts_available = None
        self._mysql_version = None

    def execute_fulltext_search(
        self,
        query: str,
        namespace: str = "default",
        category_filter: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Execute MySQL FULLTEXT search with proper validation"""
        try:
            # Validate all parameters
            validated = DatabaseInputValidator.validate_search_params(
                query, namespace, category_filter, limit
            )

            # Check if FULLTEXT is available
            if not self._check_fts_available():
                logger.debug(
                    "MySQL FULLTEXT not available, falling back to LIKE search"
                )
                return self.execute_fallback_search(
                    validated["query"],
                    validated["namespace"],
                    validated["category_filter"],
                    validated["limit"],
                )

            # Execute MySQL FULLTEXT search
            return self.query_executor.execute_search(
                validated["query"],
                validated["namespace"],
                validated["category_filter"],
                validated["limit"],
                use_fts=True,
            )

        except ValidationError as e:
            logger.error(f"Invalid search parameters: {e}")
            return []
        except Exception as e:
            logger.error(f"MySQL FULLTEXT search failed: {e}")
            return self.execute_fallback_search(
                query, namespace, category_filter, limit
            )

    def create_search_indexes(self) -> list[str]:
        """Create MySQL-specific search indexes"""
        indexes = []

        try:
            with self.connector.get_connection() as conn:
                cursor = conn.cursor()

                # Create FULLTEXT indexes (requires InnoDB in MySQL 5.6+)
                fulltext_indexes = [
                    "ALTER TABLE short_term_memory ADD FULLTEXT idx_st_fulltext (searchable_content, summary)",
                    "ALTER TABLE long_term_memory ADD FULLTEXT idx_lt_fulltext (searchable_content, summary)",
                ]

                for index_sql in fulltext_indexes:
                    try:
                        cursor.execute(index_sql)
                        indexes.append("fulltext_index")
                        logger.debug("Created FULLTEXT index")
                    except Exception as e:
                        logger.warning(f"Failed to create FULLTEXT index: {e}")

                # Create standard indexes for fallback search
                standard_indexes = [
                    "CREATE INDEX idx_st_search_mysql ON short_term_memory(namespace, category_primary, importance_score)",
                    "CREATE INDEX idx_lt_search_mysql ON long_term_memory(namespace, category_primary, importance_score)",
                    "CREATE INDEX idx_st_content_mysql ON short_term_memory(searchable_content(255))",  # Prefix index
                    "CREATE INDEX idx_lt_content_mysql ON long_term_memory(searchable_content(255))",
                ]

                for index_sql in standard_indexes:
                    try:
                        cursor.execute(index_sql)
                        indexes.append(index_sql.split()[2])  # Extract index name
                    except Exception as e:
                        logger.warning(f"Failed to create index: {e}")

                conn.commit()
                logger.info(f"Created {len(indexes)} MySQL search indexes")

        except Exception as e:
            logger.error(f"Failed to create MySQL search indexes: {e}")

        return indexes

    def translate_search_query(self, query: str) -> str:
        """Translate search query to MySQL FULLTEXT boolean syntax"""
        if not query or not query.strip():
            return ""

        # Sanitize input for MySQL FULLTEXT
        sanitized = query.strip()

        # Remove potentially dangerous boolean operators (use phrase search instead)
        dangerous_operators = ["+", "-", "~", "*", '"', "(", ")", "<", ">"]
        for op in dangerous_operators:
            sanitized = sanitized.replace(op, " ")

        # Split into words and prepare for boolean mode
        words = [
            word.strip()
            for word in sanitized.split()
            if word.strip() and len(word) >= 3
        ]  # MySQL ft_min_word_len

        if not words:
            return ""

        # Use phrase search for safety (wrap in quotes)
        return f'"{" ".join(words)}"'

    def _check_fts_available(self) -> bool:
        """Check if MySQL FULLTEXT search is available"""
        if self._fts_available is not None:
            return self._fts_available

        try:
            with self.connector.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                # Check MySQL version
                cursor.execute("SELECT VERSION() as version")
                version_result = cursor.fetchone()
                version = version_result["version"] if version_result else "0.0.0"
                self._mysql_version = version

                # Check if InnoDB supports FULLTEXT (MySQL 5.6+)
                version_parts = [int(x.split("-")[0]) for x in version.split(".")[:2]]
                version_ok = version_parts[0] > 5 or (
                    version_parts[0] == 5 and version_parts[1] >= 6
                )

                # Check if we have FULLTEXT indexes
                cursor.execute(
                    """
                    SELECT COUNT(*) as fulltext_count
                    FROM information_schema.STATISTICS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND (TABLE_NAME = 'short_term_memory' OR TABLE_NAME = 'long_term_memory')
                    AND INDEX_TYPE = 'FULLTEXT'
                """
                )
                fulltext_result = cursor.fetchone()
                has_fulltext = fulltext_result and fulltext_result["fulltext_count"] > 0

                self._fts_available = version_ok and has_fulltext

        except Exception as e:
            logger.debug(f"Error checking MySQL FULLTEXT availability: {e}")
            self._fts_available = False

        return self._fts_available

    def execute_fallback_search(
        self,
        query: str,
        namespace: str = "default",
        category_filter: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Execute LIKE-based fallback search for MySQL"""
        try:
            return self.query_executor.execute_search(
                query, namespace, category_filter, limit, use_fts=False
            )
        except Exception as e:
            logger.error(f"MySQL fallback search failed: {e}")
            return []

    def optimize_database(self):
        """Perform MySQL-specific optimizations"""
        try:
            with self.connector.get_connection() as conn:
                cursor = conn.cursor()

                # Analyze tables for better query planning
                cursor.execute("ANALYZE TABLE short_term_memory")
                cursor.execute("ANALYZE TABLE long_term_memory")

                # Optimize FULLTEXT indexes
                try:
                    cursor.execute("OPTIMIZE TABLE short_term_memory")
                    cursor.execute("OPTIMIZE TABLE long_term_memory")
                    logger.debug("Optimized MySQL FULLTEXT indexes")
                except Exception as e:
                    logger.warning(f"Table optimization failed: {e}")

                conn.commit()
                logger.info("MySQL database optimization completed")

        except Exception as e:
            logger.warning(f"MySQL optimization failed: {e}")

    def configure_fulltext_settings(self):
        """Configure MySQL FULLTEXT settings for optimal performance"""
        try:
            with self.connector.get_connection() as conn:
                cursor = conn.cursor()

                # Check current FULLTEXT settings
                cursor.execute("SHOW VARIABLES LIKE 'ft_%'")
                settings = cursor.fetchall()

                current_settings = {}
                if hasattr(cursor, "description") and cursor.description:
                    for row in settings:
                        if isinstance(row, list | tuple) and len(row) >= 2:
                            current_settings[row[0]] = row[1]

                logger.debug(f"Current MySQL FULLTEXT settings: {current_settings}")

                # Recommended settings (these require server restart or global privileges)
                recommended_settings = {
                    "ft_min_word_len": "3",  # Minimum word length
                    "ft_max_word_len": "84",  # Maximum word length
                    "ft_boolean_syntax": '+ -><()~*:""&|',  # Boolean operators
                }

                for setting, value in recommended_settings.items():
                    if (
                        setting in current_settings
                        and current_settings[setting] != value
                    ):
                        logger.info(
                            f"Consider setting {setting} = {value} (current: {current_settings.get(setting)})"
                        )

        except Exception as e:
            logger.debug(f"Could not check MySQL FULLTEXT settings: {e}")

    def repair_fulltext_indexes(self):
        """Repair FULLTEXT indexes if they become corrupted"""
        try:
            with self.connector.get_connection() as conn:
                cursor = conn.cursor()

                # Check and repair tables with FULLTEXT indexes
                tables_to_repair = ["short_term_memory", "long_term_memory"]

                for table in tables_to_repair:
                    try:
                        cursor.execute(f"CHECK TABLE {table}")
                        cursor.execute(f"REPAIR TABLE {table}")
                        logger.debug(f"Repaired table {table}")
                    except Exception as e:
                        logger.warning(f"Could not repair table {table}: {e}")

                conn.commit()

        except Exception as e:
            logger.warning(f"FULLTEXT index repair failed: {e}")

    def get_fulltext_statistics(self) -> dict[str, Any]:
        """Get statistics about FULLTEXT usage and performance"""
        stats = {}

        try:
            with self.connector.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                # Get FULLTEXT index information
                cursor.execute(
                    """
                    SELECT
                        TABLE_NAME,
                        INDEX_NAME,
                        COLUMN_NAME,
                        INDEX_TYPE
                    FROM information_schema.STATISTICS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND INDEX_TYPE = 'FULLTEXT'
                    ORDER BY TABLE_NAME, INDEX_NAME
                """
                )

                fulltext_indexes = cursor.fetchall()
                stats["fulltext_indexes"] = fulltext_indexes

                # Get table sizes
                cursor.execute(
                    """
                    SELECT
                        TABLE_NAME,
                        TABLE_ROWS,
                        DATA_LENGTH,
                        INDEX_LENGTH
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME IN ('short_term_memory', 'long_term_memory')
                """
                )

                table_stats = cursor.fetchall()
                stats["table_statistics"] = table_stats

                # MySQL version and FULLTEXT variables
                stats["mysql_version"] = self._mysql_version
                stats["fts_available"] = self._fts_available

        except Exception as e:
            logger.warning(f"Could not get FULLTEXT statistics: {e}")
            stats["error"] = str(e)

        return stats
