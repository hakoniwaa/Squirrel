"""
Advanced Personal Assistant with Conscious Memory

This example shows how to build a sophisticated personal assistant that:
- Learns about you through natural conversation
- Builds a persistent memory of your preferences, projects, and relationships
- Provides increasingly personalized assistance over time
- Uses both automatic context injection AND memory tools for function calling
"""

import json

from dotenv import load_dotenv
from litellm import completion

from memori import Memori, create_memory_tool

load_dotenv()


class PersonalAssistant:
    def __init__(self):
        """Initialize the personal assistant with conscious memory"""
        self.memori = Memori(
            database_connect="sqlite:///personal_assistant.db",
            conscious_ingest=True,  # Enable background analysis
            verbose=True,
            namespace="personal_assistant",  # Separate namespace for organization
        )

        # Enable memory recording
        self.memori.enable()

        # Create memory search tool for function calling
        self.memory_tool = create_memory_tool(self.memori)

        # Define available tools
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_memory",
                    "description": "Search my personal memory for relevant information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "What to search for in memory",
                            },
                            "category": {
                                "type": "string",
                                "enum": [
                                    "fact",
                                    "preference",
                                    "skill",
                                    "context",
                                    "rule",
                                ],
                                "description": "Optional: filter by memory category",
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_essential_info",
                    "description": "Get my essential personal information and preferences",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        ]

        # System prompt for the assistant
        self.system_prompt = """You are an advanced personal assistant with access to the user's memory and preferences.

Your capabilities:
1. **Remember Everything**: You have access to all our past conversations and the user's preferences
2. **Learn Continuously**: You get smarter about the user with each interaction
3. **Proactive Memory**: Use memory tools when you need specific information
4. **Personal Context**: Automatic context injection provides recent relevant memories

Guidelines:
- Be helpful, friendly, and increasingly personalized
- Reference past conversations when relevant
- Use memory tools to find specific information when needed
- Learn about the user's preferences, projects, and goals
- Provide suggestions based on their interests and work patterns

Memory Tools Available:
- search_memory(query, category): Search for specific information
- get_essential_info(): Get core facts about the user"""

    def search_memory(self, query: str, category: str = None) -> str:
        """Search memory for relevant information"""
        try:
            if category:
                results = self.memori.search_memories_by_category(category, limit=5)
                # Filter results by query relevance
                relevant = [r for r in results if query.lower() in str(r).lower()]
                return (
                    json.dumps(relevant[:3], indent=2)
                    if relevant
                    else "No relevant memories found"
                )
            else:
                results = self.memory_tool.execute(query=query)
                return results
        except Exception as e:
            return f"Memory search error: {str(e)}"

    def get_essential_info(self) -> str:
        """Get essential information about the user"""
        try:
            essential = self.memori.get_essential_conversations(limit=10)
            if essential:
                info = []
                for conv in essential:
                    if isinstance(conv, dict):
                        summary = conv.get("summary", conv.get("content", ""))
                        if summary:
                            info.append(f"- {summary}")
                return "Essential information about you:\\n" + "\\n".join(info[:5])
            else:
                return "No essential information available yet. Let's chat more so I can learn about you!"
        except Exception as e:
            return f"Error getting essential info: {str(e)}"

    def chat(self):
        """Start interactive chat with the assistant"""
        print("🤖 Advanced Personal Assistant with Memory")
        print("=" * 50)
        print("I'm your AI assistant with persistent memory.")
        print("I learn about you with each conversation and remember everything.")
        print("Type 'help' for tips, 'memory' for memory stats, or 'quit' to exit.")
        print()

        conversation_history = [{"role": "system", "content": self.system_prompt}]

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("👋 Goodbye! I'll remember our conversation for next time.")
                break
            elif user_input.lower() == "help":
                self.show_help()
                continue
            elif user_input.lower() == "memory":
                self.show_memory_stats()
                continue
            elif not user_input:
                continue

            # Add user message to conversation
            conversation_history.append({"role": "user", "content": user_input})

            try:
                # Make LLM call with function calling support
                response = completion(
                    model="gpt-4o",
                    messages=conversation_history,
                    tools=self.tools,
                    tool_choice="auto",
                )

                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls

                # Handle function calls
                if tool_calls:
                    conversation_history.append(response_message)

                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        # Execute the appropriate function
                        if function_name == "search_memory":
                            result = self.search_memory(
                                function_args.get("query", ""),
                                function_args.get("category"),
                            )
                        elif function_name == "get_essential_info":
                            result = self.get_essential_info()
                        else:
                            result = "Unknown function"

                        # Add function result to conversation
                        conversation_history.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result,
                            }
                        )

                    # Get final response after function calls
                    final_response = completion(
                        model="gpt-4o", messages=conversation_history
                    )

                    content = final_response.choices[0].message.content
                    print(f"🤖 Assistant: {content}")
                    conversation_history.append(
                        {"role": "assistant", "content": content}
                    )

                else:
                    # No function calls, just respond normally
                    content = response_message.content
                    print(f"🤖 Assistant: {content}")
                    conversation_history.append(
                        {"role": "assistant", "content": content}
                    )

            except Exception as e:
                print(f"❌ Error: {e}")
                conversation_history.pop()  # Remove failed user message

    def show_help(self):
        """Show help information"""
        print("\\n💡 Tips for using your Personal Assistant:")
        print("- Tell me about yourself, your work, preferences, and goals")
        print("- Ask me to remember specific information or rules")
        print("- I automatically inject relevant context from our past conversations")
        print("- I can search my memory when you ask about specific topics")
        print("- The more we chat, the better I understand your needs")
        print("\\nExample queries:")
        print("- 'What do you know about my project preferences?'")
        print("- 'Remind me of my work schedule'")
        print("- 'What technologies am I learning?'")
        print("- 'Help me plan my day based on my habits'")
        print()

    def show_memory_stats(self):
        """Show memory statistics"""
        print("\\n📊 Memory Statistics:")
        try:
            stats = self.memori.get_memory_stats()
            print(f"💬 Total conversations: {stats.get('total_conversations', 0)}")
            print(f"🧠 Memory entries: {stats.get('total_memories', 0)}")

            essential = self.memori.get_essential_conversations(limit=10)
            print(f"⭐ Essential memories: {len(essential)}")

            # Show a few essential memories
            if essential:
                print("\\n🎯 Recent essential information:")
                for i, conv in enumerate(essential[:3], 1):
                    if isinstance(conv, dict):
                        summary = conv.get("summary", conv.get("content", ""))[:100]
                        print(f"  {i}. {summary}...")

        except Exception as e:
            print(f"❌ Could not get memory stats: {e}")
        print()


def main():
    assistant = PersonalAssistant()
    assistant.chat()


if __name__ == "__main__":
    main()
