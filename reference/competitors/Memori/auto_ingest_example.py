"""
Auto-Ingest Example - Dynamic Memory Retrieval

This example demonstrates how auto_ingest=True works:
- Analyzes every user query intelligently using retrieval agent
- Searches through entire database (short-term + long-term memory)
- Injects 3-5 most relevant memories per LLM call
- Performance optimized with caching and async processing
"""

from dotenv import load_dotenv
from litellm import completion

from memori import Memori

load_dotenv()  # Load environment variables from .env file

# Create memory system with auto-ingest mode
# This mode continuously searches and injects relevant memories
memory_system = Memori(
    database_connect="sqlite:///auto_ingest_memory.db",
    auto_ingest=True,  # 🔍 Enable dynamic memory retrieval
    verbose=True,  # See what's happening behind the scenes
    openai_api_key="your-openai-key",  # Required for intelligent search
)

# Enable universal memory recording
memory_system.enable()

print("🚀 Auto-Ingest Memory System Active!")
print("How it works:")
print("- Every question you ask gets analyzed by the retrieval agent")
print("- System searches entire database for relevant memories")
print("- 3-5 most relevant memories automatically injected into context")
print("- Performance optimized with caching and background processing")
print("\nTry asking about topics you've discussed before!\n")

# Interactive conversation loop
while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit", "bye"]:
        print("💾 All conversations saved! Goodbye!")
        break

    if user_input.lower() == "help":
        print("\n📚 Auto-Ingest Help:")
        print("- Ask about any topic and relevant memories will be auto-injected")
        print("- Example: 'Help me with Python' -> finds all Python-related memories")
        print(
            "- Example: 'What did I learn about databases?' -> searches database memories"
        )
        print("- Example: 'My preferences for coding' -> finds preference memories")
        print("- Type 'exit' to quit\n")
        continue

    # Make LLM call - auto_ingest will automatically:
    # 1. Analyze user query with retrieval agent
    # 2. Search entire database for relevant memories
    # 3. Inject 3-5 most relevant memories into context
    try:
        print("🔍 Searching memory database for relevant context...")

        response = completion(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Use the provided memory context to give more personalized and informed responses.",
                },
                {"role": "user", "content": user_input},
            ],
        )

        ai_response = response.choices[0].message.content
        print(f"🤖 AI: {ai_response}")
        print("✨ Memory context automatically injected based on your query!\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have set your OpenAI API key in .env file\n")

print("\n📊 Memory Statistics:")
try:
    stats = memory_system.get_memory_stats()
    print(f"Total memories stored: {stats.get('total_memories', 0)}")
    print(f"Categories: {list(stats.get('memories_by_category', {}).keys())}")
except Exception:
    print("Memory stats not available")
