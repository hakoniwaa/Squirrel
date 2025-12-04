import os

from dotenv import load_dotenv

from memori import Memori
from memori.core.providers import ProviderConfig

load_dotenv()

# Create Azure provider configuration
azure_provider = ProviderConfig.from_azure(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version="2024-02-01",
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
)

print("Initializing Memori with Azure OpenAI...")
azure_memory = Memori(
    database_connect="sqlite:///azure_demo.db",
    conscious_ingest=True,
    auto_ingest=True,
    verbose=True,
    provider_config=azure_provider,
)

# Create client using the provider config
client = azure_provider.create_client()

print("Enabling memory tracking...")
azure_memory.enable()

print("Memori Azure OpenAI Example - Chat with GPT-4o while memory is being tracked")
print("Type 'exit' or press Ctrl+C to quit")
print("-" * 50)

while 1:
    try:
        user_input = input("User: ")
        if not user_input.strip():
            continue

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        print("Processing your message with memory tracking...")
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[{"role": "user", "content": user_input}],
        )
        print(f"AI: {response.choices[0].message.content}")
        print()  # Add blank line for readability
    except (EOFError, KeyboardInterrupt):
        print("\nExiting...")
        break
    except Exception as e:
        print(f"Error: {e}")
        continue
