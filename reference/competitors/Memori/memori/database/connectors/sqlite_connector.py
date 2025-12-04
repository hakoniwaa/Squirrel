"""
SQLite connector for Memori v1.0
"""

import sqlite3
from pathlib import Path
from typing import Any

from loguru import logger

from ...utils.exceptions import DatabaseError
from ...utils.input_validator import InputValidator
from .base_connector import BaseDatabaseConnector, DatabaseType


class SQLiteConnector(BaseDatabaseConnector):
    """SQLite database connector with FTS5 support"""

    def __init__(self, connection_config):
        """Initialize SQLite connector"""
        if isinstance(connection_config, str):
            self.db_path = self._parse_db_path(connection_config)
        else:
            self.db_path = connection_config.get("database", ":memory:")
        self._ensure_directory_exists()
        super().__init__(connection_config)

    def _detect_database_type(self) -> DatabaseType:
        """Detect database type from connection config"""
        return DatabaseType.SQLITE

    def _parse_db_path(self, connection_string: str) -> str:
        """Parse SQLite connection string to get database path"""
        if connection_string.startswith("sqlite:///"):
            return connection_string.replace("sqlite:///", "")
        elif connection_string.startswith("sqlite://"):
            return connection_string.replace("sqlite://", "")
        else:
            return connection_string

    def _ensure_directory_exists(self):
        """Ensure the database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Get SQLite connection with proper configuration"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access

            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")

            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode = WAL")

            # Enable FTS5 tokenizer if available
            try:
                conn.execute("PRAGMA enable_fts3_tokenizer=1")
            except sqlite3.Error:
                # FTS3 tokenizer not available, continue without it
                pass

            return conn

        except Exception as e:
            raise DatabaseError(f"Failed to connect to SQLite database: {e}")

    def execute_query(
        self, query: str, params: list | None = None
    ) -> list[dict[str, Any]]:
        """Execute a query and return results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                # Return results as list of dictionaries
                results = []
                for row in cursor.fetchall():
                    results.append(dict(row))

                return results

        except Exception as e:
            raise DatabaseError(f"Failed to execute query: {e}")

    def execute_insert(self, query: str, params: list | None = None) -> str:
        """Execute an insert query and return the inserted row ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                conn.commit()
                return str(cursor.lastrowid)

        except Exception as e:
            raise DatabaseError(f"Failed to execute insert: {e}")

    def execute_update(self, query: str, params: list | None = None) -> int:
        """Execute an update query and return number of affected rows"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                conn.commit()
                return cursor.rowcount

        except Exception as e:
            raise DatabaseError(f"Failed to execute update: {e}")

    def execute_delete(self, query: str, params: list | None = None) -> int:
        """Execute a delete query and return number of affected rows"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                conn.commit()
                return cursor.rowcount

        except Exception as e:
            raise DatabaseError(f"Failed to execute delete: {e}")

    def execute_transaction(self, queries: list[tuple]) -> bool:
        """Execute multiple queries in a transaction"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                for query, params in queries:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return False

    def test_connection(self) -> bool:
        """Test if the database connection is working"""
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def initialize_schema(self, schema_sql: str | None = None):
        """Initialize SQLite database schema"""
        try:
            if not schema_sql:
                # Use SQLite-specific schema
                try:
                    from ..schema_generators.sqlite_schema_generator import (  # type: ignore
                        SQLiteSchemaGenerator,
                    )

                    schema_generator = SQLiteSchemaGenerator()
                    schema_sql = schema_generator.generate_full_schema()
                except ImportError:
                    # Fall back to None - let base functionality handle it
                    schema_sql = None

            # Execute schema using transaction
            with self.get_connection() as conn:
                cursor = conn.cursor()

                try:
                    # Split schema into individual statements
                    statements = self._split_sqlite_statements(schema_sql)

                    for statement in statements:
                        statement = statement.strip()
                        if statement and not statement.startswith("--"):
                            cursor.execute(statement)

                    conn.commit()
                    logger.info("SQLite database schema initialized successfully")

                except Exception as e:
                    conn.rollback()
                    logger.error(f"Failed to initialize SQLite schema: {e}")
                    raise DatabaseError(f"Schema initialization failed: {e}")

        except Exception as e:
            logger.error(f"Failed to initialize SQLite schema: {e}")
            raise DatabaseError(f"Failed to initialize SQLite schema: {e}")

    def supports_full_text_search(self) -> bool:
        """Check if SQLite supports FTS5"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("CREATE VIRTUAL TABLE fts_test USING fts5(content)")
                cursor.execute("DROP TABLE fts_test")
                return True
        except sqlite3.OperationalError:
            return False
        except Exception:
            return False

    def create_full_text_index(
        self, table: str, columns: list[str], index_name: str
    ) -> str:
        """Create SQLite FTS5 virtual table"""
        # Validate inputs
        try:
            table = InputValidator.sanitize_sql_identifier(table)
            index_name = InputValidator.sanitize_sql_identifier(index_name)
            for col in columns:
                InputValidator.sanitize_sql_identifier(col)
        except Exception as e:
            raise DatabaseError(f"Invalid index parameters: {e}")

        columns_str = ", ".join(columns)
        return f"CREATE VIRTUAL TABLE {index_name} USING fts5({columns_str})"

    def get_database_info(self) -> dict[str, Any]:
        """Get SQLite database information and capabilities"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                info = {}

                # SQLite version
                cursor.execute("SELECT sqlite_version() as version")
                version_result = cursor.fetchone()
                info["version"] = version_result[0] if version_result else "unknown"

                # Database file info
                info["database_file"] = self.db_path
                info["database_type"] = self.database_type.value

                # Check capabilities
                info["fts5_support"] = self.supports_full_text_search()

                # Pragma settings
                cursor.execute("PRAGMA journal_mode")
                journal_mode = cursor.fetchone()
                info["journal_mode"] = journal_mode[0] if journal_mode else "unknown"

                cursor.execute("PRAGMA synchronous")
                synchronous = cursor.fetchone()
                info["synchronous"] = synchronous[0] if synchronous else "unknown"

                cursor.execute("PRAGMA cache_size")
                cache_size = cursor.fetchone()
                info["cache_size"] = cache_size[0] if cache_size else "unknown"

                return info

        except Exception as e:
            logger.warning(f"Could not get SQLite database info: {e}")
            return {
                "database_type": self.database_type.value,
                "version": "unknown",
                "fts5_support": False,
                "error": str(e),
            }

    def _split_sqlite_statements(self, schema_sql: str) -> list[str]:
        """Split SQL schema into individual statements handling SQLite syntax"""
        statements = []
        current_statement = []
        in_trigger = False

        for line in schema_sql.split("\n"):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("--"):
                continue

            # Track trigger boundaries
            if line.upper().startswith("CREATE TRIGGER"):
                in_trigger = True
            elif line.upper() == "END;" and in_trigger:
                current_statement.append(line)
                statement = " ".join(current_statement)
                if statement.strip():
                    statements.append(statement)
                current_statement = []
                in_trigger = False
                continue

            current_statement.append(line)

            # SQLite uses semicolon to end statements (except within triggers)
            if line.endswith(";") and not in_trigger:
                statement = " ".join(current_statement)
                if statement.strip():
                    statements.append(statement)
                current_statement = []

        # Add any remaining statement
        if current_statement:
            statement = " ".join(current_statement)
            if statement.strip():
                statements.append(statement)

        return statements
