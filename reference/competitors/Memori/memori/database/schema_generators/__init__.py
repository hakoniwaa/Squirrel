"""
Schema generators for different database backends
"""

from .mysql_schema_generator import MySQLSchemaGenerator

try:
    from .mongodb_schema_generator import MongoDBSchemaGenerator

    MONGODB_SCHEMA_AVAILABLE = True
except ImportError:
    MongoDBSchemaGenerator = None  # type: ignore
    MONGODB_SCHEMA_AVAILABLE = False

__all__ = ["MySQLSchemaGenerator"]

if MONGODB_SCHEMA_AVAILABLE:
    __all__.append("MongoDBSchemaGenerator")
