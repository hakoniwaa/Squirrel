# Basic Example with Conscious Ingestion

Simple demonstration of Memori enhanced conscious ingestion system.

## Overview

This example shows how to:

- Initialize Memori with conscious ingestion
- Enable AI-powered background analysis
- See intelligent context injection in action
- Understand memory promotion and essential information extraction

## Code

```python title="basic_example.py"
from memori import Memori
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

def main():
    print("Memori - AI Memory with Conscious Ingestion")
    
    # Initialize your workspace memory with conscious ingestion
    office_work = Memori(
        database_connect="sqlite:///office_memory.db",
        conscious_ingest=True,  # Enable AI-powered background analysis
        verbose=True,  # Show what's happening behind the scenes
        openai_api_key=None  # Uses OPENAI_API_KEY from environment
    )
    
    # Enable memory recording
    office_work.enable()
    print("Memory enabled - all conversations will be recorded!")
    
    # First conversation - establishing context
    print("\n--- First conversation ---")
    response1 = completion(
        model="gpt-4o-mini",
        messages=[{
            "role": "user", 
            "content": "I'm working on a FastAPI project with PostgreSQL database"
        }]
    )
    print(f"Assistant: {response1.choices[0].message.content}")
    
    # Second conversation - memory automatically provides context
    print("\n--- Second conversation (with memory context) ---")
    response2 = completion(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": "Help me write database connection code"
        }]
    )
    print(f"Assistant: {response2.choices[0].message.content}")
    
    # Third conversation - showing preference memory
    print("\n--- Third conversation (preferences remembered) ---")
    response3 = completion(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": "I prefer clean, well-documented code with type hints"
        }]
    )
    print(f"Assistant: {response3.choices[0].message.content}")
    
    print("\nThat's it! Your AI now remembers your:")
    print("  - Tech stack (FastAPI, PostgreSQL)")  
    print("  - Coding preferences (clean code, type hints)")
    print("  - Project context (user models, database connections)")
    print("\nWith conscious_ingest=True:")
    print("  - Background analysis will identify essential information")
    print("  - Key facts automatically promoted for instant access")
    print("  - Context injection gets smarter over time")
    print("\nNo more repeating context - just chat naturally!")

if __name__ == "__main__":
    main()
```

## What Happens

### 1. Memory Initialization with Conscious Ingestion
```python
office_work = Memori(
    database_connect="sqlite:///office_memory.db",
    conscious_ingest=True,  # The magic happens here
    verbose=True,  # Show background activity
    openai_api_key=None  # Uses environment variable
)
```

**What `conscious_ingest=True` enables:**

- **Background Analysis**: AI analyzes memory patterns every 6 hours
- **Essential Memory Promotion**: Key personal facts promoted to immediate access
- **Smart Context Injection**: 3-5 most relevant memories automatically included
- **Continuous Learning**: System adapts to your preferences and patterns

**Intelligence Layers:**

1. **Memory Agent** - Processes conversations with Pydantic structured outputs
2. **Conscious Agent** - Identifies essential information worth promoting
3. **Retrieval Agent** - Selects most relevant context for injection

### 2. Universal Recording

```python
office_work.enable()
```

- Activates universal LLM conversation recording
- Works with ANY LLM library (LiteLLM, OpenAI, Anthropic)
- Processes conversations with Pydantic-based intelligence

### 3. Intelligent Context Injection
Each conversation builds on the previous with AI-powered selection:

1. **First**: Establishes tech stack (FastAPI, PostgreSQL) → Gets categorized as "fact"
2. **Second**: Memory automatically provides FastAPI + PostgreSQL context
3. **Third**: Records code preferences → Gets categorized as "preference"  
4. **Background**: Conscious agent identifies these as essential personal facts
5. **Future**: All responses include essential + contextually relevant memories

**Memory Categories Learned:**

- **Facts**: "I use FastAPI and PostgreSQL"
- **Preferences**: "I prefer clean, documented code with type hints"
- **Skills**: Programming expertise and technology familiarity
- **Context**: Current project details and work patterns

## Expected Output

```
Memori - Your AI's Second Memory
Memory enabled - all conversations will be recorded!

--- First conversation ---
Assistant: Great! FastAPI with PostgreSQL is an excellent stack for building modern APIs...

--- Second conversation (with memory context) ---  
Assistant: Since you're working with FastAPI and PostgreSQL, here's how to set up your database connection...

--- Third conversation (preferences remembered) ---
Assistant: I'll keep that in mind! Clean, well-documented code with type hints is definitely the way to go...

That's it! Your AI now remembers your:
  - Tech stack (FastAPI, PostgreSQL)
  - Coding preferences (clean code, type hints)  
  - Project context (user models, database connections)

No more repeating context - just chat naturally!
```

## Database Contents

After running, check `office_memory.db`:

### Tables Created

- `chat_history` - All conversations
- `short_term_memory` - Recent context  
- `long_term_memory` - Important insights
- `memory_entities` - Extracted entities (FastAPI, PostgreSQL, etc.)

### Memory Processing

Each conversation is processed to extract:

- **Entities**: FastAPI, PostgreSQL, code, type hints
- **Categories**: fact, preference, skill, context
- **Importance**: Scored for relevance and retention

## Running the Example

### Prerequisites
```bash
pip install memorisdk python-dotenv
```

### Setup
```bash
# Set API key
export OPENAI_API_KEY="sk-your-key-here"

# Or create .env file
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### Run
```bash
python basic_example.py
```