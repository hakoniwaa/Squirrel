#!/usr/bin/env python3
"""
Demo script for Personal Diary Assistant

This script demonstrates the key features of the Personal Diary Assistant
with example interactions and use cases.
"""

import os
import time

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if we can import the assistant
try:
    from diary_assistant import PersonalDiaryAssistant
except ImportError:
    print("❌ Error: Could not import PersonalDiaryAssistant")
    print("Please make sure you're in the personal_diary_assistant directory")
    print("and that all dependencies are installed.")
    exit(1)


def demo_print(text, delay=1):
    """Print with a delay for better demo experience."""
    print(text)
    time.sleep(delay)


def main():
    """Run the demo."""
    print("🌟 Personal Diary Assistant Demo")
    print("=" * 50)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found")
        print("Please set up your .env file with your OpenAI API key")
        return

    demo_print("📦 Initializing Personal Diary Assistant...")

    # Initialize the assistant
    assistant = PersonalDiaryAssistant("demo_diary.db")

    demo_print("✅ Assistant initialized successfully!\n")

    # Demo 1: Daily diary entry
    demo_print("📝 Demo 1: Adding a diary entry with mood and productivity tracking")
    demo_print("-" * 60)

    sample_entry = """Had a great morning! Started with a 30-minute workout,
    then had a productive work session where I completed the quarterly report.
    Team meeting went well, and I got positive feedback on my presentation.
    Feeling energized and accomplished."""

    demo_print(f"Adding entry: {sample_entry[:50]}...")

    result = assistant.process_diary_entry(
        entry=sample_entry,
        mood="happy",
        productivity=8,
        tags=["work", "exercise", "presentation"],
    )

    demo_print(f"Result: {result}\n", 2)

    # Demo 2: Interactive conversation
    demo_print("💬 Demo 2: Interactive conversation with memory")
    demo_print("-" * 50)

    questions = [
        "How has my productivity been lately?",
        "What patterns do you notice in my mood?",
        "Can you give me some recommendations for maintaining my energy levels?",
    ]

    for question in questions:
        demo_print(f"User: {question}")
        response = assistant.chat_with_memory(question)
        demo_print(f"Assistant: {response[:200]}...\n", 2)

    # Demo 3: Pattern analysis
    demo_print("📊 Demo 3: Pattern analysis")
    demo_print("-" * 30)

    demo_print("Analyzing productivity patterns...")
    analysis = assistant.analyze_patterns("productivity", "week")
    demo_print(f"Analysis: {analysis[:200]}...\n", 2)

    # Demo 4: Personalized recommendations
    demo_print("🎯 Demo 4: Getting personalized recommendations")
    demo_print("-" * 45)

    demo_print("Getting wellbeing recommendations...")
    recommendations = assistant.get_recommendations("wellbeing")
    demo_print(f"Recommendations: {recommendations[:200]}...\n", 2)

    # Demo 5: Daily summary
    demo_print("📋 Demo 5: Daily summary")
    demo_print("-" * 25)

    demo_print("Generating daily summary...")
    summary = assistant.get_daily_summary()
    demo_print(f"Summary: {summary[:200]}...\n", 2)

    # Demo complete
    demo_print("🎉 Demo completed successfully!")
    demo_print("=" * 50)
    demo_print("✨ Key features demonstrated:")
    demo_print("   • Diary entry recording with metadata")
    demo_print("   • Memory-enhanced conversations")
    demo_print("   • Pattern analysis across different dimensions")
    demo_print("   • Personalized recommendations")
    demo_print("   • Daily summaries and insights")

    demo_print("\n🚀 Ready to try the full applications:")
    demo_print("   • Streamlit UI: streamlit run streamlit_app.py")
    demo_print("   • Command Line: python diary_assistant.py")

    # Cleanup demo database
    demo_db_files = ["demo_diary.db", "demo_diary.db-shm", "demo_diary.db-wal"]
    for db_file in demo_db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except Exception:
                pass

    demo_print("\n🧹 Demo database cleaned up.")


if __name__ == "__main__":
    main()
