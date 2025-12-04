"""
Personal Fitness Coach Agent with Memory

This example demonstrates how to use the Memori ToolKit with Agno Agents
to create a personal fitness coach that remembers your goals, preferences,
workouts, and progress across conversations.

Run: `pip install memorisdk agno` to install dependencies
"""

from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.memori import MemoriTools

# Setup the Memori ToolKit for fitness tracking
memori_tools = MemoriTools(
    database_connect="sqlite:///fitness_coach_memory.db",
    namespace="fitness_coach",
)

# Setup your Personal Fitness Coach Agent
coach = Agent(
    # Add the Memori ToolKit to the Agent
    tools=[memori_tools],
    model=OpenAIChat(id="gpt-4o"),
    show_tool_calls=True,
    markdown=True,
    instructions=dedent(
        """\
        You are a personal fitness coach with persistent memory. Your role is to:

        1. Always search your memory first for the client's fitness history, goals, and preferences
        2. Track workout progress, injuries, and personal preferences
        3. Provide personalized workout recommendations based on past conversations
        4. Remember dietary restrictions, favorite exercises, and scheduling preferences
        5. Be encouraging and supportive while maintaining professional expertise

        If this is a new client, introduce yourself and gather basic fitness information.
        Always reference past conversations to show continuity and progress tracking.
    """
    ),
)

# Initial consultation - gathering basic information
coach.print_response(
    "Hi! I'm looking to start a fitness routine. I'm 28 years old, work a desk job, "
    "and haven't exercised regularly in about 2 years. I have a minor knee issue from "
    "an old soccer injury. My goal is to lose 15 pounds and build some muscle."
)

# Follow-up conversation - coach should remember previous details
coach.print_response(
    "I completed the beginner workout you suggested yesterday. The squats were tough "
    "but my knee felt okay. I'm ready for my next session - what do you recommend?"
)

# Progress tracking - coach should reference past conversations
coach.print_response(
    "It's been 3 weeks since we started. Can you review my progress and adjust my "
    "routine? I've been consistent with the workouts but want to increase intensity."
)

# Dietary consultation - building on established relationship
coach.print_response(
    "I've been focusing on the exercise routine, but I think my diet needs work too. "
    "What nutrition advice do you have based on my fitness goals?"
)

# Memory utilization - testing coach's recall
coach.print_response(
    "What do you remember about my fitness journey so far? Can you give me a summary "
    "of my goals, limitations, and progress?"
)


# Additional example interactions:
#
# coach.print_response("I tweaked my knee during yesterday's workout. What should I do?")
# coach.print_response("I'm traveling next week - can you suggest hotel room workouts?")
# coach.print_response("I've been feeling unmotivated lately. Help me stay on track.")
# coach.print_response("Show me my workout history and progress metrics")
