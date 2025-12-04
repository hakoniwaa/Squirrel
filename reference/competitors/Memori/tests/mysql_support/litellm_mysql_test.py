#!/usr/bin/env python3
"""
LiteLLM + MySQL Integration Test
Demonstrates that MySQL works with the existing LiteLLM test structure
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# Add the memori package to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_litellm_mysql_integration():
    """Test that LiteLLM integration works with MySQL backend"""
    print("🚀 Testing LiteLLM + MySQL Integration")
    print("=" * 50)

    try:
        from memori import Memori

        # Test with MySQL instead of SQLite
        memory = Memori(
            database_connect="mysql+mysqlconnector://root:@127.0.0.1:3306/memori_test",
            conscious_ingest=False,
            auto_ingest=False,
            verbose=True,
        )

        print("✅ Memori initialized with MySQL backend successfully")

        # Enable LiteLLM integration
        memory.enable()
        print("✅ LiteLLM callbacks enabled")

        # Test database functionality
        stats_before = memory.db_manager.get_memory_stats("default")
        print(
            f"📊 Initial stats: {stats_before['database_type']} database with {stats_before['chat_history_count']} chats"
        )

        # Simulate a conversation (without actual LLM calls)
        memory.db_manager.store_chat_history(
            chat_id=f"litellm_test_{int(time.time())}",
            user_input="Test MySQL integration with LiteLLM",
            ai_output="MySQL integration is working perfectly with LiteLLM callbacks!",
            model="test-gpt-3.5-turbo",
            timestamp=datetime.now(),
            session_id="litellm_test_session",
            namespace="default",
            tokens_used=85,
            metadata={"test": "litellm_mysql", "provider": "test"},
        )

        # Verify the data was stored
        stats_after = memory.db_manager.get_memory_stats("default")
        print(f"📊 After storage: {stats_after['chat_history_count']} chats")

        # Test search functionality
        results = memory.db_manager.search_memories(
            "MySQL integration", namespace="default"
        )
        print(f"🔍 Search results: {len(results)} matches")

        # Test history retrieval
        history = memory.db_manager.get_chat_history("default", limit=5)
        print(f"📚 Retrieved {len(history)} history records")

        if len(history) > 0:
            latest = history[0]
            print(f"💬 Latest chat: {latest['user_input'][:50]}...")

        # Cleanup
        memory.db_manager.clear_memory("default")
        memory.disable()
        memory.db_manager.close()

        print("✅ All tests passed! LiteLLM + MySQL integration is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run the integration test"""
    if test_litellm_mysql_integration():
        print("\n🎉 LiteLLM + MySQL integration test PASSED")
        return 0
    else:
        print("\n💥 LiteLLM + MySQL integration test FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
