"""
MySQL connector for Memori v2.0
Implements BaseDatabaseConnector interface with FULLTEXT search support
"""

from typing import Any
from urllib.parse import urlparse

from loguru import logger

from ...utils.exceptions import DatabaseError
from .base_connector import BaseDatabaseConnector, DatabaseType


class MySQLConnector(BaseDatabaseConnector):
    """MySQL database connector with FULLTEXT search support"""

    def __init__(self, connection_config: dict[str, Any]):
        self._mysql = None
        self._setup_mysql()
        super().__init__(connection_config)

    def _setup_mysql(self):
        """Setup MySQL connection library"""
        try:
            import mysql.connector

            self._mysql = mysql.connector
        except ImportError:
            raise DatabaseError(
                "mysql-connector-python is required for MySQL support. "
                "Install it with: pip install mysql-connector-python"
            )

    def _detect_database_type(self) -> DatabaseType:
        """Detect database type from connection config"""
        return DatabaseType.MYSQL

    def _parse_connection_string(self, connection_string: str) -> dict[str, Any]:
        """Parse MySQL connection string into connection config"""
        if connection_string.startswith("mysql://"):
            parsed = urlparse(connection_string)
            return {
                "host": parsed.hostname or "localhost",
                "port": parsed.port or 3306,
                "user": parsed.username,
                "password": parsed.password,
                "database": parsed.path.lstrip("/") if parsed.path else None,
            }
        elif isinstance(self.connection_config, dict):
            return self.connection_config
        else:
            raise DatabaseError(
                f"Invalid MySQL connection configuration: {connection_string}"
            )

    def get_connection(self):
        """Get MySQL connection with proper configuration"""
        try:
            # Parse connection string if needed
            if isinstance(self.connection_config, str):
                config = self._parse_connection_string(self.connection_config)
            else:
                config = self.connection_config.copy()

            # Set MySQL-specific options
            config.update(
                {
                    "charset": "utf8mb4",
                    "collation": "utf8mb4_unicode_ci",
                    "autocommit": False,
                    "use_pure": True,  # Use pure Python implementation
                }
            )

            conn = self._mysql.connect(**config)

            # Set session variables for optimal performance
            cursor = conn.cursor()
            cursor.execute(
                "SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'"
            )
            cursor.execute("SET SESSION innodb_lock_wait_timeout = 30")
            cursor.execute(
                "SET SESSION ft_min_word_len = 3"
            )  # FULLTEXT minimum word length
            cursor.close()

            return conn

        except Exception as e:
            raise DatabaseError(f"Failed to connect to MySQL database: {e}")

    def execute_query(
        self, query: str, params: list[Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a query and return results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                results = cursor.fetchall()
                cursor.close()

                return results

        except Exception as e:
            raise DatabaseError(f"Failed to execute query: {e}")

    def execute_insert(self, query: str, params: list[Any] | None = None) -> str:
        """Execute an insert query and return the inserted row ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                conn.commit()
                inserted_id = str(cursor.lastrowid)
                cursor.close()

                return inserted_id

        except Exception as e:
            raise DatabaseError(f"Failed to execute insert: {e}")

    def execute_update(self, query: str, params: list[Any] | None = None) -> int:
        """Execute an update query and return number of affected rows"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                conn.commit()
                affected_rows = cursor.rowcount
                cursor.close()

                return affected_rows

        except Exception as e:
            raise DatabaseError(f"Failed to execute update: {e}")

    def execute_delete(self, query: str, params: list[Any] | None = None) -> int:
        """Execute a delete query and return number of affected rows"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                conn.commit()
                affected_rows = cursor.rowcount
                cursor.close()

                return affected_rows

        except Exception as e:
            raise DatabaseError(f"Failed to execute delete: {e}")

    def execute_transaction(self, queries: list[tuple[str, list[Any] | None]]) -> bool:
        """Execute multiple queries in a transaction"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                try:
                    conn.start_transaction()

                    for query, params in queries:
                        if params:
                            cursor.execute(query, params)
                        else:
                            cursor.execute(query)

                    conn.commit()
                    cursor.close()
                    return True

                except Exception as e:
                    conn.rollback()
                    cursor.close()
                    raise e

        except Exception as e:
            logger.error(f"MySQL transaction failed: {e}")
            return False

    def test_connection(self) -> bool:
        """Test if the database connection is working"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                cursor.close()
                return result is not None
        except Exception as e:
            logger.error(f"MySQL connection test failed: {e}")
            return False

    def initialize_schema(self, schema_sql: str | None = None):
        """Initialize database schema"""
        try:
            if not schema_sql:
                # Use MySQL-specific schema
                from ..schema_generators.mysql_schema_generator import (
                    MySQLSchemaGenerator,
                )

                schema_generator = MySQLSchemaGenerator()
                schema_sql = schema_generator.generate_full_schema()

            # Execute schema using transaction
            with self.get_connection() as conn:
                cursor = conn.cursor()

                try:
                    conn.start_transaction()

                    # Split schema into individual statements
                    statements = self._split_mysql_statements(schema_sql)

                    for statement in statements:
                        statement = statement.strip()
                        if statement and not statement.startswith("--"):
                            cursor.execute(statement)

                    conn.commit()
                    logger.info("MySQL database schema initialized successfully")

                except Exception as e:
                    conn.rollback()
                    logger.error(f"Failed to initialize MySQL schema: {e}")
                    raise DatabaseError(f"Schema initialization failed: {e}")
                finally:
                    cursor.close()

        except Exception as e:
            logger.error(f"Failed to initialize MySQL schema: {e}")
            raise DatabaseError(f"Failed to initialize MySQL schema: {e}")

    def _split_mysql_statements(self, schema_sql: str) -> list[str]:
        """Split SQL schema into individual statements handling MySQL syntax"""
        statements = []
        current_statement = []

        for line in schema_sql.split("\n"):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("--"):
                continue

            current_statement.append(line)

            # MySQL uses semicolon to end statements
            if line.endswith(";"):
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

    def supports_full_text_search(self) -> bool:
        """Check if MySQL supports FULLTEXT search"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Check MySQL version and InnoDB support for FULLTEXT
                cursor.execute("SELECT VERSION() as version")
                version_result = cursor.fetchone()

                cursor.execute("SHOW ENGINES")
                engines = cursor.fetchall()

                cursor.close()

                # MySQL 5.6+ with InnoDB supports FULLTEXT
                version = version_result["version"] if version_result else "0.0.0"
                version_parts = [int(x.split("-")[0]) for x in version.split(".")[:2]]

                innodb_available = any(
                    engine["Engine"] == "InnoDB"
                    and engine["Support"] in ("YES", "DEFAULT")
                    for engine in engines
                )

                return (
                    version_parts[0] > 5
                    or (version_parts[0] == 5 and version_parts[1] >= 6)
                ) and innodb_available

        except Exception as e:
            logger.warning(f"Could not determine MySQL FULLTEXT support: {e}")
            return False

    def create_full_text_index(
        self, table: str, columns: list[str], index_name: str
    ) -> str:
        """Create MySQL FULLTEXT index"""
        columns_str = ", ".join(columns)
        return f"ALTER TABLE {table} ADD FULLTEXT INDEX {index_name} ({columns_str})"

    def get_database_info(self) -> dict[str, Any]:
        """Get MySQL database information and capabilities"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                info = {}

                # Basic version info
                cursor.execute("SELECT VERSION() as version")
                version_result = cursor.fetchone()
                info["version"] = (
                    version_result["version"] if version_result else "unknown"
                )

                # Storage engines
                cursor.execute("SHOW ENGINES")
                info["engines"] = cursor.fetchall()

                # Database name
                cursor.execute("SELECT DATABASE() as db_name")
                db_result = cursor.fetchone()
                info["database"] = db_result["db_name"] if db_result else "unknown"

                # Character set info
                cursor.execute("SHOW VARIABLES LIKE 'character_set_%'")
                charset_vars = cursor.fetchall()
                info["character_sets"] = {
                    var["Variable_name"]: var["Value"] for var in charset_vars
                }

                # FULLTEXT configuration
                cursor.execute("SHOW VARIABLES LIKE 'ft_%'")
                fulltext_vars = cursor.fetchall()
                info["fulltext_config"] = {
                    var["Variable_name"]: var["Value"] for var in fulltext_vars
                }

                # Connection info
                info["database_type"] = self.database_type.value
                info["fulltext_support"] = self.supports_full_text_search()

                cursor.close()
                return info

        except Exception as e:
            logger.warning(f"Could not get MySQL database info: {e}")
            return {
                "database_type": self.database_type.value,
                "version": "unknown",
                "fulltext_support": False,
                "error": str(e),
            }
