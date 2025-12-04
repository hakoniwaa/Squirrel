#!/usr/bin/env python3
"""
Lightweight CrewAI + Memori Integration Example

A minimal example showing how to integrate Memori memory capabilities
with CrewAI agents for persistent memory across conversations.

Requirements:
- pip install memorisdk crewai python-dotenv
- Set OPENAI_API_KEY in environment or .env file

Usage:
    python crewai.py
"""

import os

from crewai import Agent, Crew, Process, Task
from crewai.tools import tool
from dotenv import load_dotenv

from memori import Memori, create_memory_tool

# Load environment variables
load_dotenv()

# Check for required API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY not found in environment variables")
    print("Please set your OpenAI API key:")
    print("export OPENAI_API_KEY='your-api-key-here'")
    print("or create a .env file with: OPENAI_API_KEY=your-api-key-here")
    exit(1)

print("🧠 Initializing Memori memory system...")

# Initialize Memori for persistent memory
memory_system = Memori(
    database_connect="sqlite:///crewai_example_memory.db",
    conscious_ingest=True,
    verbose=False,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    namespace="crewai_example",
)

# Enable the memory system
memory_system.enable()

# Create memory tool for agents
memory_tool = create_memory_tool(memory_system)

print("🤖 Creating memory-enhanced CrewAI agent...")


# Create a memory search tool wrapper for agents
@tool("search_memory")
def search_memory(query: str) -> str:
    """Search the agent's memory for past conversations and information.

    Args:
        query: What to search for in memory (e.g., "past conversations about AI", "user preferences")
    """
    try:
        if not query.strip():
            return "Please provide a search query"

        result = memory_tool.execute(query=query.strip())
        return str(result) if result else "No relevant memories found"

    except Exception as e:
        return f"Memory search error: {str(e)}"


# Create an AI assistant agent with memory capabilities
assistant_agent = Agent(
    role="AI Assistant with Memory",
    goal="Help users while remembering past conversations and preferences",
    backstory="""You are a helpful AI assistant with the ability to remember past
    conversations and user preferences. Always check your memory first to provide
    personalized and contextual responses.""",
    tools=[search_memory],
    verbose=False,
    allow_delegation=False,
    max_iter=5,
)


def chat_with_memory(user_input: str) -> str:
    """Process user input with memory-enhanced agent"""

    # Create a task for the agent
    task = Task(
        description=f"""
        User says: "{user_input}"

        Instructions:
        1. First, search your memory for relevant past conversations using the search_memory tool
        2. Use any relevant memories to provide a personalized response
        3. Provide a helpful and contextual answer
        4. Be conversational and friendly

        If this is the first conversation, introduce yourself and explain that you'll remember our conversations.
        """,
        agent=assistant_agent,
        expected_output="A helpful, personalized response that considers past conversations",
    )

    # Create and run crew
    crew = Crew(
        agents=[assistant_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    # Execute the task
    result = crew.kickoff()

    # Store the conversation in memory
    memory_system.record_conversation(user_input=user_input, ai_output=str(result))

    return str(result)


# Main interaction loop
print("✅ Setup complete! Chat with your memory-enhanced AI assistant.")
print("Type 'quit' or 'exit' to end the conversation.\n")

print("💡 Try asking about:")
print("- Your past conversations")
print("- Your preferences")
print("- Previous topics discussed")
print("- Any information you've shared before\n")

conversation_count = 0

while True:
    try:
        # Get user input
        user_input = input("You: ").strip()

        # Check for exit commands
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("\nAI: Goodbye! I'll remember our conversation for next time. 🤖✨")
            break

        if not user_input:
            continue

        conversation_count += 1
        print(f"\nAI (thinking... conversation #{conversation_count})")

        # Get response from memory-enhanced agent
        response = chat_with_memory(user_input)

        print(f"AI: {response}\n")

    except KeyboardInterrupt:
        print("\n\nAI: Goodbye! I'll remember our conversation for next time. 🤖✨")
        break
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please try again.\n")

print("\n📊 Session Summary:")
print(f"- Conversations processed: {conversation_count}")
print("- Memory database: crewai_example_memory.db")
print("- Namespace: crewai_example")
print("\nYour memories are saved and will be available in future sessions!")
