"""
Search adapters for different database backends
"""

from .mysql_search_adapter import MySQLSearchAdapter
from .sqlite_search_adapter import SQLiteSearchAdapter

try:
    from .mongodb_search_adapter import MongoDBSearchAdapter

    MONGODB_SEARCH_AVAILABLE = True
except ImportError:
    MongoDBSearchAdapter = None  # type: ignore
    MONGODB_SEARCH_AVAILABLE = False

__all__ = ["SQLiteSearchAdapter", "MySQLSearchAdapter"]

if MONGODB_SEARCH_AVAILABLE:
    __all__.append("MongoDBSearchAdapter")
