"""
Personal Assistant with Memori
AI assistant with conscious ingestion and intelligent memory
"""

from dotenv import load_dotenv
from litellm import completion

from memori import Memori

load_dotenv()


def main():
    print("🤖 Personal Assistant with Conscious Memory")
    print("=" * 50)

    # Create personal memory space with conscious ingestion
    personal = Memori(
        database_connect="sqlite:///personal_assistant.db",
        namespace="personal",  # Separate from work memories
        conscious_ingest=True,  # 🧠 Enable background analysis
        verbose=True,  # Show conscious agent activity
        openai_api_key=None,  # Uses OPENAI_API_KEY from environment
    )

    personal.enable()
    print("✅ Personal assistant memory enabled")
    print("🧠 Background conscious analysis started")
    print("🎯 Essential memories will be automatically promoted")

    # Simulate a conversation flow
    conversations = [
        {
            "context": "Establishing preferences",
            "user": "I'm a software engineer who loves Python and prefers minimalist tools",
            "expected": "Remembers: Python preference, minimalist tools",
        },
        {
            "context": "Daily routine",
            "user": "I usually code in the mornings and prefer short, focused work sessions",
            "expected": "Remembers: Work schedule, focus preferences",
        },
        {
            "context": "Learning goals",
            "user": "I want to learn more about AI and machine learning this year",
            "expected": "Remembers: Learning goals for AI/ML",
        },
        {
            "context": "Applying memory - tool recommendation",
            "user": "What development tools should I use for my next project?",
            "expected": "Suggests Python tools, considers minimalist preference",
        },
        {
            "context": "Applying memory - schedule advice",
            "user": "How should I structure my learning time?",
            "expected": "Considers morning coding preference, short sessions",
        },
    ]

    for i, conv in enumerate(conversations, 1):
        print(f"\n--- Conversation {i}: {conv['context']} ---")
        print(f"You: {conv['user']}")

        response = completion(
            model="gpt-4o-mini", messages=[{"role": "user", "content": conv["user"]}]
        )

        print(f"Assistant: {response.choices[0].message.content}")
        print(f"💡 Expected memory: {conv['expected']}")

    print("\n🎯 Conscious Memory in Action:")
    print("  ✅ Preferences automatically categorized and stored")
    print("  ✅ Essential information promoted for instant access")
    print("  ✅ Context intelligently injected based on relevance")
    print("  ✅ Personalized responses improve over time")

    # Demonstrate conscious analysis
    print("\n🧠 Triggering conscious analysis...")
    try:
        personal.trigger_conscious_analysis()
        essential = personal.get_essential_conversations(limit=3)
        print(f"  ✅ Analysis complete: {len(essential)} essential memories promoted")
    except Exception as e:
        print(f"  ⚠️ Analysis requires more conversation data: {e}")

    print("\n💾 Check 'personal_assistant.db' to see stored memories!")
    print("🔬 Enable verbose=True to see agent activity in real-time")


if __name__ == "__main__":
    main()
