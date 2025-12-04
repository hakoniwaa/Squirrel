"""
Lightweight Swarms + Memori Integration Example

A minimal example showing how to integrate Memori memory capabilities
with Swarms agents for persistent memory across conversations.

Requirements:
- pip install memorisdk swarms python-dotenv
- Set OPENAI_API_KEY in environment or .env file

Usage:
    python swarms_example.py
"""

from swarms import Agent

from memori import Memori

# Initialize Memori for customer service with persistent memory
customer_service_memory = Memori(
    database_connect="sqlite:///swarms_memory.db",
    auto_ingest=True,  # Automatically store conversation history
    conscious_ingest=True,  # Store important customer preferences and issues
    verbose=False,  # Enable logging for audit purposes
)

customer_service_memory.enable()

# Create a customer service agent with memory capabilities
customer_service_agent = Agent(
    model_name="gpt-4o",
    system_prompt="""You are Sarah, a helpful customer service representative for TechCorp.
    You have access to conversation history and customer preferences through your memory system.
    """,
    max_loops=1,
)

# Sample conversation demonstrating memory usage
print("=== Customer Service Chat Session ===")

# First interaction
customer_service_agent.run(
    """
Hi, I'm John Smith, customer ID JS-12345. I ordered a laptop last week
(Order #ORD-789456) but it hasn't arrived yet. I need it for a business
presentation on Friday. Can you help me track it? Also, I prefer email
communication over phone calls.
"""
)

print("\n" + "=" * 50 + "\n")

# Follow-up interaction (agent should remember John and his preferences)
customer_service_agent.run(
    """
Hi Sarah, I just wanted to follow up on
order we discussed earlier. Any updates on the delivery?
"""
)

print("\n" + "=" * 50 + "\n")

# Another follow-up showing memory of customer preferences
customer_service_agent.run(
    """
The order arrived but there's a small issue with the keyboard.
Some keys are sticking. What should I do?
"""
)
