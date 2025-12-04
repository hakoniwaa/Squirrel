#!/usr/bin/env python3
"""
Personal Diary Assistant with Memori Integration

A comprehensive personal diary assistant that records daily updates,
analyzes patterns, and provides personalized recommendations for
improving efficiency and well-being.

Features:
- Daily diary entries with memory
- Mood tracking and analysis
- Productivity insights
- Personalized recommendations
- Goal tracking and progress monitoring
- Habit analysis

Requirements:
- pip install memorisdk litellm python-dotenv streamlit
- Set OPENAI_API_KEY in environment or .env file
"""

import json
import os
from datetime import date, datetime

import litellm
from dotenv import load_dotenv

from memori import Memori, create_memory_tool

load_dotenv()  # Load environment variables from .env file


class PersonalDiaryAssistant:
    """Personal Diary Assistant with advanced memory and analysis capabilities."""

    def __init__(self, database_path: str = "personal_diary.db"):
        """Initialize the Personal Diary Assistant."""
        self.database_path = database_path
        self.memory_system = Memori(
            database_connect=f"sqlite:///{database_path}",
            conscious_ingest=True,
            verbose=False,  # Set to True for debugging
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            namespace="personal_diary",
        )

        # Enable memory system
        self.memory_system.enable()

        # Create memory tool
        self.memory_tool = create_memory_tool(self.memory_system)

        # Initialize conversation history for session
        self.conversation_history = []

        # System prompts for different functionalities
        self.system_prompts = {
            "diary": """You are a supportive personal diary assistant with advanced memory capabilities.
            Your role is to help users reflect on their daily experiences, track their progress, and provide
            personalized insights for improving their life. Use memory_search to understand the user's patterns,
            goals, and past experiences. Be empathetic, encouraging, and provide actionable advice.""",
            "analysis": """You are an expert life coach and data analyst. Analyze the user's diary entries,
            mood patterns, productivity levels, and life events to provide deep insights. Use memory_search
            to gather comprehensive information about the user's history. Provide specific, actionable
            recommendations for improvement.""",
            "goal_tracking": """You are a goal achievement specialist. Help users set, track, and achieve
            their personal and professional goals. Use memory_search to understand their past goals,
            progress, and challenges. Provide motivation and practical steps for success.""",
        }

        # Available tools for LLM function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "memory_search",
                    "description": "Search memories for relevant information about the user's past entries, patterns, goals, and experiences",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query to find relevant memories (e.g., 'mood patterns last month', 'productivity goals', 'work stress')",
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_patterns",
                    "description": "Analyze patterns in user's diary entries, mood, productivity, and life events",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis_type": {
                                "type": "string",
                                "enum": [
                                    "mood",
                                    "productivity",
                                    "habits",
                                    "goals",
                                    "relationships",
                                    "overall",
                                ],
                                "description": "Type of analysis to perform",
                            },
                            "time_period": {
                                "type": "string",
                                "enum": [
                                    "week",
                                    "month",
                                    "quarter",
                                    "year",
                                    "all_time",
                                ],
                                "description": "Time period for analysis",
                            },
                        },
                        "required": ["analysis_type"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recommendations",
                    "description": "Generate personalized recommendations based on user's patterns and goals",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "focus_area": {
                                "type": "string",
                                "enum": [
                                    "productivity",
                                    "wellbeing",
                                    "relationships",
                                    "habits",
                                    "goals",
                                    "general",
                                ],
                                "description": "Area to focus recommendations on",
                            },
                        },
                        "required": ["focus_area"],
                    },
                },
            },
        ]

    def memory_search(self, query: str) -> str:
        """Search memories for relevant information."""
        try:
            result = self.memory_tool.execute(query=query)
            return str(result) if result else "No relevant memories found."
        except Exception as e:
            return f"Memory search error: {str(e)}"

    def analyze_patterns(self, analysis_type: str, time_period: str = "month") -> str:
        """Analyze patterns in user's diary entries."""
        try:
            # Search for relevant memories based on analysis type and time period
            search_queries = {
                "mood": f"mood feelings emotions {time_period}",
                "productivity": f"productivity work achievements tasks {time_period}",
                "habits": f"habits routines daily activities {time_period}",
                "goals": f"goals objectives targets progress {time_period}",
                "relationships": f"relationships social interactions family friends {time_period}",
                "overall": f"life patterns general trends {time_period}",
            }

            query = search_queries.get(analysis_type, f"{analysis_type} {time_period}")
            memories = self.memory_search(query)

            # Use LLM to analyze the patterns
            analysis_prompt = f"""
            Based on the following memories about {analysis_type} over the {time_period}:

            {memories}

            Please provide a comprehensive analysis including:
            1. Key patterns and trends identified
            2. Notable improvements or concerning areas
            3. Correlations between different factors
            4. Specific insights and observations
            5. Actionable recommendations for improvement

            Be specific and provide concrete examples from the data.
            """

            response = litellm.completion(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompts["analysis"]},
                    {"role": "user", "content": analysis_prompt},
                ],
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Pattern analysis error: {str(e)}"

    def get_recommendations(self, focus_area: str) -> str:
        """Generate personalized recommendations."""
        try:
            # Search for relevant memories for the focus area
            recent_memories = self.memory_search(
                f"recent {focus_area} challenges goals progress"
            )
            patterns = self.memory_search(f"{focus_area} patterns trends habits")

            recommendation_prompt = f"""
            Based on the user's history and patterns in {focus_area}:

            Recent Context: {recent_memories}
            Historical Patterns: {patterns}

            Please provide personalized recommendations including:
            1. 3-5 specific, actionable steps for improvement
            2. Potential obstacles and how to overcome them
            3. Short-term (1 week) and medium-term (1 month) goals
            4. Resources or tools that might help
            5. Ways to track progress

            Make recommendations specific to this user's unique situation and history.
            """

            response = litellm.completion(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompts["analysis"]},
                    {"role": "user", "content": recommendation_prompt},
                ],
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Recommendation error: {str(e)}"

    def process_diary_entry(
        self,
        entry: str,
        mood: str | None = None,
        productivity: int | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """Process a diary entry with mood and productivity tracking."""
        try:
            # Prepare the enhanced entry with metadata
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%H:%M")

            enhanced_entry = f"""
            Date: {current_date}
            Time: {current_time}
            Entry: {entry}
            """

            if mood:
                enhanced_entry += f"\nMood: {mood}"
            if productivity is not None:
                enhanced_entry += f"\nProductivity Level: {productivity}/10"
            if tags:
                enhanced_entry += f"\nTags: {', '.join(tags)}"

            # Store the entry in memory
            self.memory_system.record_conversation(
                user_input=enhanced_entry, ai_output="Diary entry recorded successfully"
            )

            return "✅ Diary entry recorded successfully! I'll remember this for future insights."

        except Exception as e:
            return f"Error recording diary entry: {str(e)}"

    def chat_with_memory(self, user_input: str, mode: str = "diary") -> str:
        """Process user input with memory-enhanced conversation."""
        try:
            # Initialize conversation if empty
            if not self.conversation_history:
                self.conversation_history = [
                    {
                        "role": "system",
                        "content": self.system_prompts.get(
                            mode, self.system_prompts["diary"]
                        ),
                    }
                ]

            # Add user message to conversation
            self.conversation_history.append({"role": "user", "content": user_input})

            # Make LLM call with function calling
            response = litellm.completion(
                model="gpt-4o",
                messages=self.conversation_history,
                tools=self.tools,
                tool_choice="auto",
            )

            response_message = response.choices[0].message
            tool_calls = response.choices[0].message.tool_calls

            # Handle function calls
            if tool_calls:
                self.conversation_history.append(response_message)

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    # Execute the appropriate function
                    if function_name == "memory_search":
                        query = function_args.get("query", "")
                        function_response = self.memory_search(query)
                    elif function_name == "analyze_patterns":
                        analysis_type = function_args.get("analysis_type", "overall")
                        time_period = function_args.get("time_period", "month")
                        function_response = self.analyze_patterns(
                            analysis_type, time_period
                        )
                    elif function_name == "get_recommendations":
                        focus_area = function_args.get("focus_area", "general")
                        function_response = self.get_recommendations(focus_area)
                    else:
                        function_response = "Unknown function called"

                    # Add function result to conversation
                    self.conversation_history.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": function_response,
                        }
                    )

                # Get final response after function calls
                final_response = litellm.completion(
                    model="gpt-4o", messages=self.conversation_history
                )

                final_content = final_response.choices[0].message.content
                self.conversation_history.append(
                    {"role": "assistant", "content": final_content}
                )

                # Record this conversation in memory
                self.memory_system.record_conversation(
                    user_input=user_input, ai_output=final_content
                )

                return final_content

            else:
                # No function calls, just respond normally
                content = response_message.content
                self.conversation_history.append(
                    {"role": "assistant", "content": content}
                )

                # Record this conversation in memory
                self.memory_system.record_conversation(
                    user_input=user_input, ai_output=content
                )

                return content

        except Exception as e:
            return f"Error processing your request: {str(e)}"

    def get_daily_summary(self) -> str:
        """Generate a summary of today's activities and insights."""
        try:
            today = date.today().strftime("%Y-%m-%d")
            today_memories = self.memory_search(
                f"today {today} diary entries mood productivity"
            )

            if "No relevant memories found" in today_memories:
                return "No diary entries found for today. Consider adding your first entry!"

            summary_prompt = f"""
            Based on today's diary entries and activities:

            {today_memories}

            Please provide a helpful daily summary including:
            1. Key highlights from today
            2. Mood and productivity observations
            3. Accomplishments and challenges
            4. Suggestions for tomorrow
            5. Overall reflection

            Keep it concise but insightful.
            """

            response = litellm.completion(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompts["analysis"]},
                    {"role": "user", "content": summary_prompt},
                ],
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error generating daily summary: {str(e)}"

    def clear_session_history(self):
        """Clear the current session's conversation history."""
        self.conversation_history = []


def main():
    """Main function for command-line interface."""
    print("🌟 Personal Diary Assistant with Memory")
    print("=" * 50)
    print("Welcome to your intelligent personal diary!")
    print(
        "I can help you track your daily life, analyze patterns, and provide personalized advice."
    )
    print("Type 'exit' or 'quit' to stop.\n")

    # Initialize the assistant
    assistant = PersonalDiaryAssistant("personal_diary.db")

    print("💡 Try these commands:")
    print("- Share your daily experiences")
    print("- Ask for productivity insights")
    print("- Request mood analysis")
    print("- Get personalized recommendations")
    print("- Ask about your progress on goals")
    print("- Type 'summary' for today's overview\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["exit", "quit", "bye"]:
                print(
                    "\nAssistant: Goodbye! Your memories are safely stored for our next conversation. 🌟"
                )
                break

            if user_input.lower() == "summary":
                response = assistant.get_daily_summary()
                print(f"\n📊 Daily Summary:\n{response}\n")
                continue

            if not user_input:
                continue

            # Process the input
            response = assistant.chat_with_memory(user_input)
            print(f"\nAssistant: {response}\n")

        except KeyboardInterrupt:
            print("\n\nAssistant: Goodbye! Your memories are safely stored. 🌟")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again.\n")


if __name__ == "__main__":
    main()
