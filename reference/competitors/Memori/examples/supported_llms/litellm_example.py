from litellm import completion

from memori import Memori

print("Initializing Memori with SQLite database...")
litellm_memory = Memori(
    database_connect="sqlite:///litellm_demo.db",
    conscious_ingest=True,
    auto_ingest=True,
    # verbose=True,
)

print("Enabling memory tracking...")
litellm_memory.enable()

print("Memori SQLite Demo - Chat with GPT-4o while memory is being tracked")
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
        response = completion(
            model="gpt-4o", messages=[{"role": "user", "content": user_input}]
        )
        print(f"AI: {response.choices[0].message['content']}")
        print()  # Add blank line for readability
    except (EOFError, KeyboardInterrupt):
        print("\nExiting...")
        break
    except Exception as e:
        print(f"Error: {e}")
        continue
