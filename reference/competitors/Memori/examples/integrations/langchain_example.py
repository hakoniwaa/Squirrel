#!/usr/bin/env python3
"""
Lightweight LangChain + Memori Integration Example

A minimal example showing how to integrate Memori memory capabilities
with LangChain agents for persistent memory across conversations.

Requirements:
- pip install memorisdk langchain==0.3.27 langchain-openai python-dotenv
- Set OPENAI_API_KEY in environment or .env file

Usage:
    python langchain_example.py
"""

import os

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

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
    database_connect="sqlite:///langchain_example_memory.db",
    conscious_ingest=True,
    verbose=False,
    namespace="langchain_example",
)

# Enable the memory system
memory_system.enable()

# Create memory tool for agents
memory_tool = create_memory_tool(memory_system)

print("🤖 Creating memory-enhanced LangChain agent...")


class MemorySearchInput(BaseModel):
    """Input for the memory search tool."""

    query: str = Field(
        description="What to search for in memory (e.g., 'past conversations about AI', 'user preferences')"
    )


class MemorySearchTool(BaseTool):
    """LangChain tool for searching agent memory."""

    name: str = "search_memory"
    description: str = (
        "Search the agent's memory for past conversations and information. "
        "Use this to recall previous interactions, user preferences, and context."
    )
    args_schema: type[BaseModel] = MemorySearchInput

    def _run(
        self,
        query: str,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        """Use the tool to search memory."""
        try:
            if not query.strip():
                return "Please provide a search query"

            result = memory_tool.execute(query=query.strip())
            return str(result) if result else "No relevant memories found"

        except Exception as e:
            return f"Memory search error: {str(e)}"


# Create the memory search tool
memory_search_tool = MemorySearchTool()

# Initialize the LLM
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)

# Create the prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful AI assistant with the ability to remember past
conversations and user preferences. Always check your memory first to provide
personalized and contextual responses.

Instructions:
1. First, search your memory for relevant past conversations using the search_memory tool
2. Use any relevant memories to provide a personalized response
3. Provide a helpful and contextual answer
4. Be conversational and friendly

If this is the first conversation, introduce yourself and explain that you'll remember our conversations.""",
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

# Create the agent
agent = create_openai_tools_agent(llm, [memory_search_tool], prompt)

# Create the agent executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=[memory_search_tool],
    verbose=False,
    handle_parsing_errors=True,
    max_iterations=5,
)


def chat_with_memory(user_input: str) -> str:
    """Process user input with memory-enhanced LangChain agent"""
    try:
        # Run the agent with the user input
        result = agent_executor.invoke(
            {
                "input": user_input,
                "chat_history": [],  # We're using Memori for persistent memory instead
            }
        )

        # Get the response content
        response_content = result.get(
            "output", "I apologize, but I couldn't generate a response."
        )

        # Store the conversation in memory
        memory_system.record_conversation(
            user_input=user_input, ai_output=response_content
        )

        return response_content

    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        return error_msg


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
print("- Memory database: langchain_example_memory.db")
print("- Namespace: langchain_example")
print("\nYour memories are saved and will be available in future sessions!")
