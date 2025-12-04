#!/usr/bin/env python3
"""
Lightweight Azure AI Foundry + Memori Integration Example

A minimal example showing how to integrate Memori memory capabilities
with Azure AI Foundry agents for persistent memory across conversations.

Requirements:
- pip install memorisdk azure-ai-projects azure-identity python-dotenv
- Set the following environment variables in your .env file or environment:
  * PROJECT_ENDPOINT: Your Azure AI Foundry project endpoint URL
  * AZURE_OPENAI_API_KEY: Your Azure OpenAI API key
  * AZURE_OPENAI_ENDPOINT: Your Azure OpenAI endpoint URL
  * AZURE_OPENAI_DEPLOYMENT_NAME: Your Azure OpenAI model deployment name
  * AZURE_OPENAI_API_VERSION: Azure OpenAI API version (e.g., "2024-12-01-preview")
- Configure Azure authentication (Azure CLI login or managed identity)

Example .env file:
    PROJECT_ENDPOINT=https://your-project.eastus2.ai.azure.com
    AZURE_OPENAI_API_KEY=your-azure-openai-api-key-here
    AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
    AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
    AZURE_OPENAI_API_VERSION=2024-12-01-preview

Usage:
    python azure_ai_foundry_example.py
"""

import json
import os
import time

from azure.ai.agents.models import FunctionTool
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from memori import Memori, create_memory_tool
from memori.core.providers import ProviderConfig

# Load environment variables
load_dotenv()

# Create Azure provider configuration for Memori
azure_provider = ProviderConfig.from_azure(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
)

print("🧠 Initializing Memori memory system...")

# Initialize Memori for persistent memory
memory_system = Memori(
    database_connect="sqlite:///azure_ai_foundry_memory.db",
    conscious_ingest=True,
    auto_ingest=True,
    verbose=False,
    provider_config=azure_provider,
    namespace="azure_ai_foundry_example",
)

# Enable the memory system
memory_system.enable()

# Create memory tool for agents
memory_tool = create_memory_tool(memory_system)

print("🤖 Setting up Azure AI Foundry client...")

# Get configuration from environment
project_endpoint = os.environ["PROJECT_ENDPOINT"]
model_name = os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]

# Initialize the AIProjectClient
project_client = AIProjectClient(
    endpoint=project_endpoint, credential=DefaultAzureCredential()
)

print("🔧 Creating memory-enhanced functions...")


def search_memory(query: str) -> str:
    """
    Search the agent's memory for past conversations and information.

    :param query: What to search for in memory (e.g., "past conversations about AI", "user preferences")
    :return: Relevant memories as a JSON string.
    """
    try:
        if not query.strip():
            return json.dumps({"error": "Please provide a search query"})

        result = memory_tool.execute(query=query.strip())
        memory_result = str(result) if result else "No relevant memories found"

        return json.dumps({"memories": memory_result, "search_query": query})

    except Exception as e:
        return json.dumps({"error": f"Memory search error: {str(e)}"})


# Define user functions for the agent
user_functions = {search_memory}

print("🚀 Creating Azure AI Foundry agent with memory capabilities...")

# Initialize the FunctionTool with user-defined functions
functions = FunctionTool(functions=user_functions)


def handle_function_calls(tool_calls):
    """Handle function calls from the agent"""
    tool_outputs = []

    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        try:
            if function_name == "search_memory":
                output = search_memory(function_args.get("query", ""))
            else:
                output = json.dumps({"error": f"Unknown function: {function_name}"})

            tool_outputs.append({"tool_call_id": tool_call.id, "output": output})

        except Exception as e:
            error_output = json.dumps({"error": f"Function execution error: {str(e)}"})
            tool_outputs.append({"tool_call_id": tool_call.id, "output": error_output})

    return tool_outputs


def chat_with_memory(user_input: str, agent, thread, client) -> str:
    """Process user input with memory-enhanced Azure AI Foundry agent"""

    try:
        # Send a message to the thread
        message = client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input,
        )

        # Create and process a run for the agent to handle the message
        run = client.agents.runs.create(thread_id=thread.id, agent_id=agent.id)

        # Poll the run status until it is completed or requires action
        while run.status in ["queued", "in_progress", "requires_action"]:
            time.sleep(1)
            run = client.agents.runs.get(thread_id=thread.id, run_id=run.id)

            if run.status == "requires_action":
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = handle_function_calls(tool_calls)

                client.agents.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs,
                )

        # Fetch the latest messages from the thread
        messages = client.agents.messages.list(thread_id=thread.id)

        # Get the assistant's response (the first message should be the latest)
        assistant_response = ""
        for message in messages:
            if message["role"] == "assistant":
                # Handle both string content and list content
                content = message["content"]
                if isinstance(content, list):
                    # Extract text from content blocks
                    text_parts = []
                    for block in content:
                        if hasattr(block, "text") and hasattr(block.text, "value"):
                            text_parts.append(block.text.value)
                        elif isinstance(block, dict) and "text" in block:
                            text_parts.append(block["text"].get("value", ""))
                    assistant_response = " ".join(text_parts)
                else:
                    assistant_response = str(content)
                break

        # Store the conversation in memory
        if assistant_response:
            memory_system.record_conversation(
                user_input=user_input, ai_output=assistant_response
            )

        return assistant_response or "I apologize, I couldn't generate a response."

    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        return error_msg


def cleanup_agent(agent, client):
    """Clean up the agent resources"""
    if agent:
        try:
            client.agents.delete_agent(agent.id)
            print(f"🗑️ Deleted agent {agent.id}")
        except Exception as e:
            print(f"Warning: Could not delete agent: {str(e)}")


# Main interaction loop
def main():
    """Main function to run the Azure AI Foundry + Memori integration"""

    print("🚀 Creating Azure AI Foundry agent with memory capabilities...")

    # Use the client within a context manager for the entire session
    with project_client:
        try:
            # Create an agent with custom functions including memory search
            agent = project_client.agents.create_agent(
                model=model_name,
                name="memory-enhanced-assistant",
                instructions="""You are a helpful AI assistant with the ability to remember past conversations and user preferences. You have access to memory search capabilities that allow you to recall previous interactions.

            Instructions:
            1. Always search your memory first for relevant past conversations using the search_memory function
            2. Use any relevant memories to provide personalized and contextual responses
            3. Be conversational, friendly, and helpful

            If this is the first conversation, introduce yourself and explain that you'll remember our conversations for future reference.""",
                tools=functions.definitions,
            )

            print(f"✅ Created agent with ID: {agent.id}")

            # Create a thread for communication
            thread = project_client.agents.threads.create()
            print(f"✅ Created thread with ID: {thread.id}")

            print(
                "\n✅ Setup complete! Chat with your memory-enhanced Azure AI Foundry assistant."
            )
            print("Type 'quit' or 'exit' to end the conversation.\n")

            print("💡 Try asking about:")
            print("- Your past conversations")
            print("- Your preferences from previous chats")
            print("- Any information you've shared before")
            print("- Previous topics discussed\n")

            conversation_count = 0

            while True:
                try:
                    # Get user input
                    user_input = input("You: ").strip()

                    # Check for exit commands
                    if user_input.lower() in ["quit", "exit", "bye"]:
                        print(
                            "\nAI: Goodbye! I'll remember our conversation for next time. 🤖✨"
                        )
                        break

                    if not user_input:
                        continue

                    conversation_count += 1
                    print(f"\nAI (thinking... conversation #{conversation_count})")

                    # Get response from memory-enhanced agent
                    response = chat_with_memory(
                        user_input, agent, thread, project_client
                    )

                    print(f"AI: {response}\n")

                except KeyboardInterrupt:
                    print(
                        "\n\nAI: Goodbye! I'll remember our conversation for next time. 🤖✨"
                    )
                    break
                except Exception as e:
                    print(f"\nError: {str(e)}")
                    print("Please try again.\n")

            print("\n📊 Session Summary:")
            print(f"- Conversations processed: {conversation_count}")
            print("- Memory database: azure_ai_foundry_memory.db")
            print("- Namespace: azure_ai_foundry_example")
            print("\nYour memories are saved and will be available in future sessions!")

        finally:
            # Clean up resources
            if "agent" in locals():
                cleanup_agent(agent, project_client)


if __name__ == "__main__":
    main()
