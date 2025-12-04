import json

import litellm
from dotenv import load_dotenv

from memori import Memori, create_memory_tool

load_dotenv()  # Load environment variables from .env file

# Create your workspace memory (without automatic injection)
office_work = Memori(
    database_connect="sqlite:///office_memory.db",
    # conscious_ingest=False,  # Disable background conscious analysis
    verbose=True,  # Enable verbose logging
)

office_work.enable()  # Start recording conversations

# Create memory tool for LLM function calling
memory_tool = create_memory_tool(office_work)

# Use LiteLLM with function calling

# System prompt
SYSTEM_PROMPT = """You are an AI assistant with memory capabilities. Use the memory_search tool to find relevant information about the user when needed."""


# Simple memory search function
def memory_search(query):
    """Search memories for relevant information"""
    try:
        result = memory_tool.execute(query=query)
        return result
    except Exception as e:
        return f"Error: {str(e)}"


# Tools definition
tools = [
    {
        "type": "function",
        "function": {
            "name": "memory_search",
            "description": "Search memories for relevant information about the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find relevant memories",
                    },
                },
                "required": ["query"],
            },
        },
    }
]


def chat_with_memory():
    conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("🧠 AI Assistant with Memory Tools")
    print("Ask me anything! I can remember our conversations and learn about you.")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye! Our conversation has been saved to memory.")
            break

        # Add user message to conversation
        conversation_history.append({"role": "user", "content": user_input})

        try:
            # Make LLM call with function calling
            response = litellm.completion(
                model="gpt-4o",
                messages=conversation_history,
                tools=tools,
                verbose=True,  # Enable verbose logging
                tool_choice="auto",  # auto is default, but we'll be explicit
            )

            response_message = response.choices[0].message
            tool_calls = response.choices[0].message.tool_calls

            # Handle function calls
            if tool_calls:
                conversation_history.append(response_message)

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    # Call memory search function
                    if function_name == "memory_search":
                        query = function_args.get("query", "")
                        function_response = memory_search(query)
                        print(f"🔍 Memory Tool: search -> Found results for '{query}'")

                        # Add function result to conversation
                        conversation_history.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": function_response,
                            }
                        )

                # Get final response after function calls
                final_response = litellm.completion(
                    model="gpt-4o", messages=conversation_history
                )

                final_content = final_response.choices[0].message.content
                print(f"AI: {final_content}")
                conversation_history.append(
                    {"role": "assistant", "content": final_content}
                )

            else:
                # No function calls, just respond normally
                content = response_message.content
                print(f"AI: {content}")
                conversation_history.append({"role": "assistant", "content": content})

        except Exception as e:
            print(f"Error: {e}")
            break


if __name__ == "__main__":
    chat_with_memory()
