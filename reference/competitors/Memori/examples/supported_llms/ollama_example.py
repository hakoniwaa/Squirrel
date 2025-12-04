import os

from memori import Memori
from memori.core.providers import ProviderConfig

# Create Ollama provider configuration
# Ollama runs locally on port 11434 by default
ollama_provider = ProviderConfig.from_custom(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # Ollama doesn't require an API key, but OpenAI client needs something
    model=os.getenv(
        "OLLAMA_MODEL", "llama3.2:3b"
    ),  # Default to llama3.2:3b, can be overridden
)

print("Initializing Memori with Ollama...")
ollama_memory = Memori(
    database_connect="sqlite:///ollama_demo.db",
    conscious_ingest=True,
    auto_ingest=True,
    verbose=True,
    provider_config=ollama_provider,
)

# Create client using the provider config
client = ollama_provider.create_client()

print("Enabling memory tracking...")
ollama_memory.enable()

print(
    f"Memori Ollama Example - Chat with {ollama_provider.model} while memory is being tracked"
)
print("Make sure Ollama is running locally (ollama serve)")
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
            model=ollama_provider.model,
            messages=[{"role": "user", "content": user_input}],
        )
        print(f"AI: {response.choices[0].message.content}")
        print()  # Add blank line for readability
    except (EOFError, KeyboardInterrupt):
        print("\nExiting...")
        break
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Ollama is running: 'ollama serve'")
        print(
            f"And that you have pulled the model: 'ollama pull {ollama_provider.model}'"
        )
        continue
