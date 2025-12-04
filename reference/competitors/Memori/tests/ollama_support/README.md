# Ollama Support Tests for Memori

This directory contains test scripts for using Memori with Ollama's local LLM models.

## Prerequisites

1. **Install Ollama**: Download from [ollama.ai](https://ollama.ai)
2. **Start Ollama server**: 
   ```bash
   ollama serve
   ```
3. **Pull a model** (if not already installed):
   ```bash
   ollama pull gemma3:1b  # Or any other model
   ```

## Test Files

### 1. `ollama_test.py` - Automated Test Suite
Runs through a set of predefined test inputs to verify Ollama integration with Memori.

```bash
python ollama_test.py
```

Features:
- Loads test inputs from `test_inputs.json`
- Tests memory storage and retrieval
- Shows memory statistics
- Saves to `ollama_memory.db`

### 2. `ollama_interactive.py` - Interactive Chat
Interactive chat session with memory persistence.

```bash
python ollama_interactive.py
```

Features:
- Interactive conversation loop
- Maintains conversation history
- Persists memories across sessions
- Saves to `ollama_interactive.db`

## Configuration

You can configure Ollama settings via environment variables:

```bash
# Set custom Ollama server URL (default: http://localhost:11434)
export OLLAMA_BASE_URL=http://localhost:11434

# Set model to use (default: gemma3:1b)
export OLLAMA_MODEL=llama2:7b

# Run the test
python ollama_test.py
```

## Supported Models

Popular models that work well with Memori:
- `gemma3:1b` - Fast, lightweight model (default)
- `llama2:7b` - Balanced performance
- `mistral:7b` - Good for general tasks
- `codellama:7b` - Better for code-related conversations

Install any model with:
```bash
ollama pull <model-name>
```

## How It Works

1. **LiteLLM Integration**: Uses LiteLLM for OpenAI-compatible API calls to Ollama
2. **Memory Configuration**: Memori is configured to use Ollama for both:
   - Main LLM calls (conversation)
   - Memory processing agents (classification, extraction)
3. **Local Storage**: All memories stored in local SQLite database

## Memory Features Tested

- **Conscious Ingest**: Smart extraction of important information
- **Auto Ingest**: Automatic context injection into conversations
- **Memory Persistence**: Long-term storage of conversation data
- **Context Retrieval**: Retrieving relevant memories for new conversations

## Troubleshooting

### Connection Error
```
❌ Connection error - make sure Ollama is running
```
**Solution**: Start Ollama server with `ollama serve`

### Model Not Found
```
❌ Model 'gemma3:1b' not found
```
**Solution**: Install the model with `ollama pull gemma3:1b`

### Slow Performance
- Try a smaller model like `gemma3:1b`
- Reduce `max_tokens` in the completion call
- Check CPU/GPU usage

## Database Files

The tests create SQLite database files:
- `ollama_memory.db` - From automated test
- `ollama_interactive.db` - From interactive chat

You can inspect these with any SQLite viewer:
```bash
sqlite3 ollama_memory.db
.tables
SELECT * FROM long_term_memory LIMIT 5;
```

## Example Output

```
🦙 Ollama Test with Memori
📍 Server: http://localhost:11434
🤖 Model: gemma3:1b
--------------------------------------------------
📝 Loaded 10 test inputs
🚀 Starting test...

[1/10] User: What is the capital of France?
[1/10] AI: The capital of France is **Paris**.

[2/10] User: My name is John and I'm a developer
[2/10] AI: Nice to meet you, John! It's great to hear you're a developer...

📊 Final Memory Statistics:
   Long-term memories: 10
   Chat history entries: 10
==================================================
✅ Test completed!
💾 Database saved to: ollama_memory.db
```