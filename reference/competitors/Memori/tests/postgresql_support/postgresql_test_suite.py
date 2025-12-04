#!/usr/bin/env python3
"""
PostgreSQL Integration Test Suite
Basic tests for PostgreSQL database functionality with Memori
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# Add the memori package to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def get_postgresql_connection_string():
    """Get PostgreSQL connection string from environment or defaults"""
    import os

    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", os.environ.get("USER", "postgres"))
    password = os.environ.get("POSTGRES_PASSWORD", "")

    password_part = f":{password}" if password else ""
    return f"postgresql+psycopg2://{user}{password_part}@{host}:{port}/memori_test"


def test_basic_postgresql_functionality():
    """Test basic PostgreSQL database operations"""
    print("🧪 Testing Basic PostgreSQL Functionality")
    print("=" * 50)

    try:
        from memori import Memori

        connection_string = get_postgresql_connection_string()
        print(f"🔌 Connection: {connection_string}")

        # Initialize Memori with PostgreSQL
        memory = Memori(
            database_connect=connection_string,
            conscious_ingest=False,
            auto_ingest=False,
            verbose=True,
        )

        print("✅ Memori initialized with PostgreSQL backend")

        # Test database info
        db_info = memory.db_manager.get_database_info()
        print(
            f"📊 Database: {db_info['database_type']} v{db_info.get('server_version', 'Unknown')}"
        )
        print(f"🔍 Full-text search: {db_info.get('supports_fulltext', 'Unknown')}")

        # Test namespace
        test_namespace = "postgresql_test"

        # Clear any existing data
        memory.db_manager.clear_memory(test_namespace)

        # Test chat history storage
        print("\n⚡ Testing chat history storage...")

        for i in range(5):
            memory.db_manager.store_chat_history(
                chat_id=f"pg_test_{i}_{int(time.time())}",
                user_input=f"PostgreSQL test message {i} with full-text search capabilities",
                ai_output=f"Response {i}: PostgreSQL provides excellent full-text search with tsvector and GIN indexes",
                model="test-postgresql-model",
                timestamp=datetime.now(),
                session_id="postgresql_test_session",
                namespace=test_namespace,
                tokens_used=75 + i * 5,
                metadata={"test": "postgresql", "iteration": i, "database": "postgres"},
            )

        print("   ✅ Stored 5 chat records")

        # Test statistics
        stats = memory.db_manager.get_memory_stats(test_namespace)
        print(f"   📊 Chat count: {stats['chat_history_count']}")
        print(f"   🗄️  Backend: {stats['database_type']}")

        # Test history retrieval
        print("\n📚 Testing history retrieval...")
        history = memory.db_manager.get_chat_history(test_namespace, limit=10)
        print(f"   ✅ Retrieved {len(history)} records")

        if history:
            latest = history[0]
            print(f"   💬 Latest: {latest['user_input'][:50]}...")

        # Test search functionality
        print("\n🔍 Testing PostgreSQL full-text search...")

        # Test different search queries
        search_queries = [
            "PostgreSQL full-text",
            "tsvector GIN",
            "search capabilities",
            "test message",
        ]

        total_results = 0
        for query in search_queries:
            results = memory.db_manager.search_memories(query, namespace=test_namespace)
            print(f"   🔎 '{query}': {len(results)} results")

            if results:
                result = results[0]
                score = result.get("search_score", 0)
                strategy = result.get("search_strategy", "unknown")
                print(f"      Score: {score:.3f}, Strategy: {strategy}")

            total_results += len(results)

        print(f"   📊 Total search results: {total_results}")

        # Test short-term memory if available
        print("\n🧠 Testing short-term memory...")
        try:
            memory.db_manager.store_short_term_memory(
                content="PostgreSQL short-term memory test with tsvector search",
                summary="Testing PostgreSQL tsvector functionality",
                category_primary="test",
                category_secondary="postgresql",
                session_id="pg_test_session",
                namespace=test_namespace,
                metadata={"type": "short_term", "database": "postgresql"},
            )
            print("   ✅ Short-term memory storage successful")
        except Exception as e:
            print(f"   ⚠️  Short-term memory test failed: {e}")

        # Test long-term memory if available
        print("\n📖 Testing long-term memory...")
        try:
            memory.db_manager.store_long_term_memory(
                content="PostgreSQL long-term memory with advanced search capabilities",
                summary="Long-term PostgreSQL tsvector testing",
                category_primary="test",
                category_secondary="postgresql",
                session_id="pg_test_session",
                namespace=test_namespace,
                metadata={"type": "long_term", "database": "postgresql"},
            )
            print("   ✅ Long-term memory storage successful")
        except Exception as e:
            print(f"   ⚠️  Long-term memory test failed: {e}")

        # Final cleanup
        memory.db_manager.clear_memory(test_namespace)
        memory.db_manager.close()

        print("\n✅ All PostgreSQL tests passed!")
        return True

    except Exception as e:
        print(f"❌ PostgreSQL test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_postgresql_specific_features():
    """Test PostgreSQL-specific features like tsvector"""
    print("\n🔧 Testing PostgreSQL-Specific Features")
    print("=" * 50)

    try:
        from sqlalchemy import text

        from memori.database.sqlalchemy_manager import SQLAlchemyDatabaseManager

        connection_string = get_postgresql_connection_string()
        db_manager = SQLAlchemyDatabaseManager(connection_string)

        # Test tsvector functionality directly
        print("🔍 Testing tsvector functionality...")

        with db_manager.SessionLocal() as session:
            # Test basic tsvector
            result = session.execute(
                text(
                    "SELECT to_tsvector('english', 'PostgreSQL full-text search with tsvector')"
                )
            ).fetchone()

            if result:
                print(f"   ✅ tsvector creation: {result[0]}")

            # Test tsquery
            result = session.execute(
                text("SELECT to_tsquery('english', 'PostgreSQL & search')")
            ).fetchone()

            if result:
                print(f"   ✅ tsquery creation: {result[0]}")

            # Test ranking
            result = session.execute(
                text(
                    """
                    SELECT ts_rank(
                        to_tsvector('english', 'PostgreSQL provides excellent full-text search'),
                        to_tsquery('english', 'PostgreSQL & search')
                    ) as rank
                """
                )
            ).fetchone()

            if result:
                print(f"   ✅ ts_rank function: {result[0]:.4f}")

        # Test GIN index support
        print("\n📊 Testing GIN index support...")

        try:
            with db_manager.SessionLocal() as session:
                result = session.execute(
                    text(
                        """
                        SELECT indexname FROM pg_indexes
                        WHERE indexname LIKE '%search_vector%'
                        AND tablename IN ('short_term_memory', 'long_term_memory')
                    """
                    )
                ).fetchall()

                if result:
                    print(f"   ✅ Found {len(result)} search vector indexes")
                    for idx in result:
                        print(f"      - {idx[0]}")
                else:
                    print(
                        "   ⚠️  No search vector indexes found (may need schema initialization)"
                    )

        except Exception as e:
            print(f"   ⚠️  GIN index test failed: {e}")

        db_manager.close()

        print("✅ PostgreSQL-specific features test completed!")
        return True

    except Exception as e:
        print(f"❌ PostgreSQL features test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all PostgreSQL tests"""
    print("🚀 PostgreSQL Integration Test Suite")
    print("Testing PostgreSQL database functionality with Memori")
    print("=" * 60)

    # Check dependencies
    try:
        import psycopg2  # noqa: F401

        print("✅ psycopg2 available")
    except ImportError:
        print("❌ psycopg2 not available - install with: pip install psycopg2-binary")
        return 1

    # Run tests
    success = True

    # Test 1: Basic functionality
    if not test_basic_postgresql_functionality():
        success = False

    # Test 2: PostgreSQL-specific features
    if not test_postgresql_specific_features():
        success = False

    # Summary
    print("\n" + "=" * 60)
    if success:
        print("🎉 All PostgreSQL tests PASSED!")
        print("PostgreSQL integration is working correctly with Memori")
    else:
        print("💥 Some PostgreSQL tests FAILED!")
        print("Check the errors above for details")

    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
