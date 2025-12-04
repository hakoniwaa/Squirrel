"""
Conscious-Ingest Example - Short-Term Working Memory

This example demonstrates how conscious_ingest=True works:
- At startup: Conscious agent analyzes long-term memory patterns
- Promotes 5-10 essential conversations to short-term memory storage
- Injects this working memory ONCE at the first LLM call
- Like human short-term memory: names, current projects, preferences readily available
- No repeated injection during the same session (one-shot behavior)
"""

from dotenv import load_dotenv
from litellm import completion

from memori import Memori

load_dotenv()  # Load environment variables from .env file

# Create memory system with conscious-ingest mode
# This mode promotes essential memories to short-term storage at startup
office_work = Memori(
    database_connect="sqlite:///office_memory.db",
    conscious_ingest=True,  # 🧠 Enable short-term working memory
    verbose=True,  # See the conscious agent in action
    openai_api_key="your-openai-key",  # Required for conscious agent
)

# Enable universal memory recording
# This also triggers conscious agent analysis if long-term memories exist
office_work.enable()

print("🧠 Conscious-Ingest Memory System Active!")
print("How it works:")
print("- At startup: Conscious agent analyzed your long-term memories")
print("- Essential conversations promoted to short-term working memory")
print("- First LLM call: Working memory injected once (like human consciousness)")
print("- Subsequent calls: No repeated injection (one-shot behavior)")
print("- Working memory contains: your name, preferences, current projects, skills")
print("\nStart a conversation - your essential context is ready!\n")

# Track if this is the first call (for demonstration)
first_call = True

# Interactive conversation loop
while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit", "bye"]:
        print("💾 All conversations saved to long-term memory! Goodbye!")
        break

    if user_input.lower() == "help":
        print("\n📚 Conscious-Ingest Help:")
        print("- Your essential memories are already loaded in working memory")
        print("- First question: Short-term context gets injected automatically")
        print("- Following questions: No context re-injection (one-shot)")
        print("- Essential info includes: name, preferences, skills, current projects")
        print("- Type 'exit' to quit\n")
        continue

    # Make LLM call - conscious_ingest will:
    # - Inject short-term working memory on FIRST call only
    # - Subsequent calls have no automatic injection
    try:
        if first_call:
            print("🧠 Injecting short-term working memory (one-shot)...")
            first_call = False
        else:
            print("💭 Using conversation context (no memory re-injection)...")

        response = completion(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Use any provided memory context to give personalized responses that acknowledge the user's background and preferences.",
                },
                {"role": "user", "content": user_input},
            ],
        )

        ai_response = response.choices[0].message.content
        print(f"🤖 AI: {ai_response}")

        if not first_call:
            print(
                "✨ Short-term working memory was injected once and is now part of context!"
            )
        else:
            print("💭 Continuing conversation with established context...")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have set your OpenAI API key in .env file\n")

print("\n📊 Memory Statistics:")
try:
    stats = office_work.get_memory_stats()
    print(f"Total memories stored: {stats.get('total_memories', 0)}")
    print(
        f"Short-term memories: {stats.get('memories_by_retention', {}).get('short_term', 0)}"
    )
    print(
        f"Long-term memories: {stats.get('memories_by_retention', {}).get('long_term', 0)}"
    )
except Exception:
    print("Memory stats not available")
