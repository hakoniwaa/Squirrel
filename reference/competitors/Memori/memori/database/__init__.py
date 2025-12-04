"""Database components for Memoriai"""

from .connectors import MySQLConnector, PostgreSQLConnector, SQLiteConnector

try:
    from .connectors import MongoDBConnector

    MONGODB_AVAILABLE = True
except ImportError:
    MongoDBConnector = None  # type: ignore
    MONGODB_AVAILABLE = False

__all__ = ["SQLiteConnector", "PostgreSQLConnector", "MySQLConnector"]

if MONGODB_AVAILABLE:
    __all__.append("MongoDBConnector")
