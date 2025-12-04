"""
Conscious Ingestion Demo - Showcase of AI-powered memory management

This example demonstrates the full power of Memori's conscious ingestion system:
- Background analysis every 6 hours
- Essential memory promotion
- Intelligent context injection
- Personal identity extraction
"""

import time

from dotenv import load_dotenv
from litellm import completion

from memori import Memori

load_dotenv()  # Load environment variables from .env file


def main():
    print("🧠 Memori Conscious Ingestion Demo")
    print("=" * 50)
    print()

    # Create memory instance with conscious ingestion
    memori = Memori(
        database_connect="sqlite:///conscious_demo.db",
        conscious_ingest=True,  # 🔥 Enable AI-powered background analysis
        verbose=True,  # Show what's happening behind the scenes
        openai_api_key=None,  # Uses OPENAI_API_KEY from environment
    )

    print("✅ Conscious ingestion enabled!")
    print("📊 Background analysis will run every 6 hours")
    print("🎯 Essential memories will be automatically promoted")
    print()

    # Enable memory recording
    memori.enable()
    print("🟢 Memory recording started")
    print()

    # Demonstrate different types of information that get learned
    demo_conversations = [
        # Personal identity
        "Hi, I'm Sarah, a senior Python developer at TechCorp",
        # Preferences and habits
        "I prefer using FastAPI over Flask for web development. I usually work from 9 AM to 6 PM EST",
        # Skills and tools
        "I'm experienced with PostgreSQL, Redis, and Docker. Currently learning Kubernetes",
        # Current projects
        "I'm working on a microservices architecture for our e-commerce platform using Python and React",
        # Rules and guidelines
        "I always write tests first when developing. Code reviews are mandatory in our team",
        # Relationships
        "My teammate Mike is the DevOps expert, and Lisa handles the frontend React components",
    ]

    print("📝 Simulating conversations to build memory...")
    for i, user_message in enumerate(demo_conversations, 1):
        print(f"\n--- Conversation {i} ---")
        print(f"User: {user_message}")

        try:
            # Make LLM call with automatic context injection
            response = completion(
                model="gpt-4o", messages=[{"role": "user", "content": user_message}]
            )

            ai_response = response.choices[0].message.content
            print(f"AI: {ai_response}")

            # Small delay to simulate real conversation
            time.sleep(1)

        except Exception as e:
            print(f"❌ Error: {e}")
            continue

    print("\n" + "=" * 50)
    print("🔍 Memory Analysis")
    print("=" * 50)

    # Show memory statistics
    try:
        stats = memori.get_memory_stats()
        print(f"📊 Total conversations stored: {stats.get('total_conversations', 0)}")
        print(f"📊 Memory entries: {stats.get('total_memories', 0)}")
        print(
            f"📊 Essential conversations: {len(memori.get_essential_conversations())}"
        )
    except Exception as e:
        print(f"❌ Could not get stats: {e}")

    print("\n🧠 Triggering conscious analysis...")
    try:
        # Manually trigger background analysis to demonstrate
        memori.trigger_conscious_analysis()
        print("✅ Analysis complete - essential memories promoted!")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

    # Demonstrate context injection with a new query
    print("\n" + "=" * 50)
    print("🎯 Context Injection Demo")
    print("=" * 50)

    test_queries = [
        "What's my name and role?",
        "What technologies do I prefer?",
        "Tell me about my current project",
        "What are my work rules?",
    ]

    for query in test_queries:
        print(f"\n🔍 Query: {query}")

        try:
            # This will automatically inject relevant context
            response = completion(
                model="gpt-4o", messages=[{"role": "user", "content": query}]
            )

            ai_response = response.choices[0].message.content
            print(f"🤖 AI: {ai_response}")

        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "=" * 50)
    print("🎉 Demo Complete!")
    print("=" * 50)
    print()
    print("What happened:")
    print("✅ All conversations were automatically processed")
    print("✅ Entities extracted (people, technologies, projects)")
    print("✅ Memory categories assigned (facts, preferences, skills)")
    print("✅ Essential information promoted for context injection")
    print("✅ Relevant memories automatically included in responses")
    print()
    print("💡 The AI now 'remembers' you and can reference this information")
    print("   in future conversations without you having to repeat yourself!")


if __name__ == "__main__":
    main()
