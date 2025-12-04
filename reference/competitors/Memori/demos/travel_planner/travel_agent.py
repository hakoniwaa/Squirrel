"""
Travel Planning Agent Module
Contains the CrewAI agents and tasks for travel planning with Memori integration
"""

import json
import os
from datetime import datetime

import litellm

# CrewAI imports
from crewai import Agent, Crew, Process, Task
from crewai.tools import tool
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

# Memori imports
from memori import Memori, create_memory_tool

# Load environment variables from .env file
load_dotenv()


def create_memory_search_tool(memori_tool):
    """Create a memory search tool function"""

    @tool("memory_search")
    def memory_search(query: str) -> str:
        """Search user's memory for preferences, past trips, and personal travel information.

        Use this tool to find information about the user's previous travel experiences,
        preferences, destinations visited, budget ranges, accommodation preferences,
        dining preferences, activity preferences, and any other travel-related information
        that has been stored in their memory.

        Args:
            query: A descriptive search query about what travel information you're looking for.
                  Examples: "past trips to Europe", "budget preferences", "favorite hotels",
                  "dietary restrictions", "preferred activities"
        """
        try:
            if not query or not query.strip():
                return "Please provide a specific search query for memory search"

            if memori_tool is None:
                return "Memory tool not initialized"

            # Clean the query
            clean_query = query.strip()
            result = memori_tool.execute(query=clean_query)
            return str(result)
        except Exception as e:
            return f"Memory search error: {str(e)}"

    return memory_search


class TravelPlannerAgent:
    """Main travel planner agent class that manages memory and agents"""

    def __init__(self):
        """Initialize the travel planner with memory and environment variables"""
        # Validate environment variables
        self._validate_environment()

        # Initialize Memori
        self.travel_memory = None
        self.memory_tool = None
        self._initialize_memory()

    def _validate_environment(self):
        """Validate that required environment variables are present"""
        required_vars = ["OPENAI_API_KEY", "SERPER_API_KEY"]
        missing_vars = []

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                f"Please set them in your .env file or environment."
            )

    def _initialize_memory(self):
        """Initialize Memori instance and memory tool"""
        try:
            # Create personalized travel memory
            self.travel_memory = Memori(
                database_connect="sqlite:///travel_planner_memory.db",
                conscious_ingest=True,  # Enable background analysis
                verbose=True,
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                namespace="travel_planner",  # Separate namespace for travel planning
            )

            self.travel_memory.enable()

            # Create memory tool
            self.memory_tool = create_memory_tool(self.travel_memory)

        except Exception as e:
            raise RuntimeError(f"Failed to initialize memory system: {str(e)}")

    def create_travel_agents(self) -> tuple[Agent, Agent, Agent]:
        """Create the travel planning crew agents"""

        # Create SerperDevTool for web searching
        search_tool = SerperDevTool()

        # Memory search tool wrapper
        memory_search_tool = create_memory_search_tool(self.memory_tool)

        # Travel Research Agent
        research_agent = Agent(
            role="Travel Research Specialist",
            goal="Research destinations, flights, accommodations, and activities based on user preferences",
            backstory="""You are an expert travel researcher with access to real-time information
            and user memory. You excel at finding the best travel deals, hidden gems, and
            personalized recommendations based on past preferences and current trends.

            IMPORTANT: Always start by searching the user's memory with specific queries like:
            - "past trips to [destination]" to find previous experiences
            - "budget preferences" to understand spending patterns
            - "accommodation preferences" to know hotel/lodging preferences
            - "activity preferences" to understand what they enjoy
            - "dietary restrictions" for food-related planning
            - "travel style preferences" to understand their travel personality

            Use specific, descriptive search terms instead of generic queries.""",
            tools=[search_tool, memory_search_tool],
            verbose=True,
            allow_delegation=False,
            max_reasoning_attempts=2,
            max_iter=3,  # Limit iterations to avoid infinite loops
        )

        # Travel Planning Agent
        planning_agent = Agent(
            role="Personal Travel Planner",
            goal="Create detailed, personalized travel itineraries based on research and user preferences",
            backstory="""You are a seasoned travel planner who creates amazing, personalized
            travel experiences. You consider user preferences, budget, time constraints, and
            special interests to craft perfect itineraries.

            IMPORTANT: Use memory search to understand the user's preferences:
            - Search for "past itinerary preferences" to understand their travel patterns
            - Look for "pace preferences" (relaxed vs. packed schedules)
            - Check "meal preferences" and "dining habits" from past trips
            - Search for "transportation preferences" (walking, metro, taxi, etc.)
            - Look for "accommodation feedback" from previous stays
            - Search for "activity preferences" (cultural, adventure, relaxation, etc.)
            Always personalize based on their history and stated preferences.""",
            tools=[memory_search_tool],
            verbose=True,
            allow_delegation=False,
            max_reasoning_attempts=2,
            max_iter=3,  # Limit iterations to avoid infinite loops
        )

        # Budget Advisor Agent
        budget_agent = Agent(
            role="Travel Budget Advisor",
            goal="Provide accurate budget estimates and money-saving tips for travel plans",
            backstory="""You are a financial expert specializing in travel budgeting.
            You help travelers make the most of their money while ensuring they have
            amazing experiences within their budget constraints.""",
            tools=[search_tool, memory_search_tool],
            verbose=True,
            allow_delegation=False,
            max_reasoning_attempts=2,
            max_iter=3,  # Limit iterations to avoid infinite loops
        )

        return research_agent, planning_agent, budget_agent

    def create_travel_tasks(
        self, agents: tuple[Agent, Agent, Agent], travel_request: str
    ) -> list[Task]:
        """Create travel planning tasks"""

        research_agent, planning_agent, budget_agent = agents

        # Research Task
        research_task = Task(
            description=f"""Research travel options for: {travel_request}

            STEP 1 - MEMORY SEARCH (CRITICAL): Start by searching the user's memory with specific queries:
            - "trips to [destination]" or "past visits to [destination]"
            - "budget preferences for international trips" or "typical trip spending"
            - "preferred accommodation types" (hotel, hostel, Airbnb, etc.)
            - "activity preferences" (museums, outdoor, nightlife, culture, etc.)
            - "food preferences and restrictions"
            - "travel style" (luxury, budget, mid-range, backpacking, etc.)

            STEP 2 - WEB RESEARCH: Based on memory insights, research:
            1. Current flight options and prices from user's likely departure locations
            2. Accommodation options matching their preferred style and budget
            3. Activities and attractions aligned with their interests
            4. Weather and seasonal considerations for the travel period
            5. Current travel deals and promotions
            6. Local customs and travel tips

            Provide a comprehensive research report that references their past preferences and includes specific recommendations.""",
            agent=research_agent,
            expected_output="Detailed research report with personalized recommendations based on user's memory, flight options, accommodations, activities, and current deals",
        )

        # Planning Task
        planning_task = Task(
            description=f"""Create a detailed travel itinerary for: {travel_request}

            Based on the research findings and user memory:
            1. Create a day-by-day itinerary
            2. Include transportation between locations
            3. Suggest dining options based on preferences
            4. Plan activities that match user interests
            5. Include backup options for weather issues
            6. Provide practical travel tips

            Make it personal and exciting!""",
            agent=planning_agent,
            expected_output="Complete day-by-day travel itinerary with personalized recommendations",
            dependencies=[research_task],
        )

        # Budget Task
        budget_task = Task(
            description=f"""Provide budget analysis for: {travel_request}

            Based on the research and itinerary:
            1. Calculate estimated costs for flights
            2. Estimate accommodation costs
            3. Budget for meals and dining
            4. Include activity and attraction costs
            5. Add transportation costs
            6. Suggest money-saving tips
            7. Provide budget alternatives

            Include both conservative and premium budget options.""",
            agent=budget_agent,
            expected_output="Detailed budget breakdown with cost estimates and money-saving tips",
            dependencies=[research_task, planning_task],
        )

        return [research_task, planning_task, budget_task]

    def plan_trip(self, travel_request: str, user_preferences: dict = None) -> str:
        """
        Plan a trip based on the travel request and preferences

        Args:
            travel_request: The user's travel request description
            user_preferences: Optional dictionary with user preferences

        Returns:
            Formatted travel plan as string
        """
        try:
            # Store preferences in memory if provided
            if user_preferences:
                preference_data = {
                    **user_preferences,
                    "request": travel_request,
                    "timestamp": datetime.now().isoformat(),
                }

                # Record preferences in memory
                memory_entry = f"Travel request: {travel_request}. Preferences: {json.dumps(preference_data)}. Plan requested on {datetime.now().strftime('%Y-%m-%d %H:%M')}"

                # Store in memory before planning
                self.travel_memory.record_conversation(
                    user_input=memory_entry,
                    ai_output="Planning trip request received and processing...",
                )

            # Create agents
            agents = self.create_travel_agents()

            # Create tasks
            tasks = self.create_travel_tasks(agents, travel_request)

            # Create and run crew
            crew = Crew(
                agents=list(agents),
                tasks=tasks,
                process=Process.sequential,
                verbose=True,
            )

            # Execute the crew
            result = crew.kickoff()

            # Store the result in memory
            if user_preferences:
                self.travel_memory.record_conversation(
                    user_input=f"Travel request: {travel_request}. Preferences: {json.dumps(user_preferences)}",
                    ai_output=str(result),
                )

            return str(result)

        except Exception as e:
            error_msg = f"Error creating travel plan: {str(e)}"
            print(f"TravelPlannerAgent Error: {error_msg}")
            return error_msg

    def search_memory(self, query: str) -> str:
        """Search the travel memory for past trips and preferences with user-friendly formatting"""
        try:
            if not self.memory_tool:
                return "Memory system not initialized"

            if not query or not query.strip():
                return "Please provide a specific search query"

            # Get raw results from memory
            raw_results = self.memory_tool.execute(query=query.strip())

            # If no results found
            if not raw_results or str(raw_results).strip() in [
                "",
                "None",
                "null",
                "[]",
                "{}",
            ]:
                return f"🔍 I couldn't find any information about '{query}' in your travel memory yet. Try planning some trips to build up your memory!"

            # Use LiteLLM to format the results into user-friendly response
            conversation_history = [
                {
                    "role": "system",
                    "content": """You are a helpful travel assistant that formats memory search results into friendly, conversational responses.

                    Your job is to take raw memory search results and present them in a clear, user-friendly way.

                    Guidelines:
                    - Be conversational and friendly
                    - Use emojis appropriately
                    - Format information clearly with bullet points or sections when helpful
                    - If the user asks about "last trip" or "recent trip", focus on the most recent information
                    - If asking about preferences, summarize the key preferences found
                    - If asking about specific destinations, highlight relevant trips and experiences
                    - Keep responses concise but informative
                    - If the raw results seem technical or unclear, extract the key human-readable information
                    """,
                },
                {
                    "role": "user",
                    "content": f"""The user asked: "{query}"

                    Here are the raw memory search results:
                    {raw_results}

                    Please format this into a friendly, conversational response that directly answers their question. Focus on the most relevant information and present it in an easy-to-read format.""",
                },
            ]

            final_response = litellm.completion(
                model="gpt-4o",
                messages=conversation_history,
                api_key=os.getenv("OPENAI_API_KEY"),
            )

            return final_response.choices[0].message.content

        except Exception as e:
            return f"Memory search error: {str(e)}"

    def get_memory_stats(self) -> dict:
        """Get basic statistics about the memory system"""
        try:
            # This would depend on Memori's actual stats API
            # For now, return basic info
            return {
                "status": "Active" if self.travel_memory else "Inactive",
                "database": "travel_planner_memory.db",
                "namespace": "travel_planner",
                "conscious_ingest": True,
            }
        except Exception as e:
            return {"error": str(e)}


def main():
    """CLI interface for testing the travel planner agent"""
    print("🌍 Travel Planner Agent - CLI Mode")
    print("=" * 50)

    try:
        # Initialize the agent
        agent = TravelPlannerAgent()
        print("✅ Travel planner initialized successfully!")

        # Example usage
        travel_request = input("\nDescribe your travel plans: ")

        if travel_request.strip():
            print("\n🤖 Planning your trip...")
            result = agent.plan_trip(travel_request)
            print("\n" + "=" * 50)
            print("📋 YOUR TRAVEL PLAN:")
            print("=" * 50)
            print(result)
        else:
            print("❌ Please provide a travel request")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Make sure you have:")
        print("   1. Created a .env file with OPENAI_API_KEY and SERPER_API_KEY")
        print("   2. Installed all required dependencies")


if __name__ == "__main__":
    main()
