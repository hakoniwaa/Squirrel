"""
Advanced Memori Configuration Example
Demonstrates configuration management and production settings
"""

from litellm import completion

from memori import ConfigManager, Memori


def main():
    print("⚙️ Advanced Memori Configuration")
    print("=" * 35)

    # Method 1: Configuration Manager (Recommended)
    print("\n1. Using ConfigManager...")
    config_manager = ConfigManager()

    # Auto-load from files and environment
    config_manager.auto_load()

    # Create instance with loaded config
    memori = Memori()
    memori.enable()
    print("✅ Loaded configuration automatically")

    # Method 2: Manual configuration
    print("\n2. Manual configuration...")
    work_memory = Memori(
        database_connect="postgresql://user:pass@localhost/work_memory",
        namespace="work_project",
        conscious_ingest=True,
        openai_api_key="sk-...",
        shared_memory=False,
        memory_filters={
            "min_importance": 0.4,
            "categories": ["fact", "preference", "skill"],
        },
    )
    work_memory.enable()
    print("✅ Manual configuration applied")

    # Method 3: Environment-based
    print("\n3. Environment variables...")
    print("Set these environment variables:")
    print("  MEMORI_DATABASE__CONNECTION_STRING=postgresql://...")
    print("  MEMORI_AGENTS__OPENAI_API_KEY=sk-...")
    print("  MEMORI_MEMORY__NAMESPACE=production")
    print("  MEMORI_LOGGING__LEVEL=INFO")

    # Show configuration info
    print("\n📊 Configuration Info:")
    config_info = config_manager.get_config_info()
    print(f"  Sources: {', '.join(config_info['sources'])}")
    print(f"  Debug mode: {config_info['debug_mode']}")
    print(f"  Production: {config_info['is_production']}")

    # Test with a conversation
    print("\n💬 Testing conversation...")
    response = completion(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "Help me optimize database queries in my project",
            }
        ],
    )
    print(f"Response: {response.choices[0].message.content[:100]}...")

    print("\n✅ Advanced configuration example completed!")


if __name__ == "__main__":
    main()
