# Memori Examples

Simple, focused examples demonstrating core Memori functionality.

## 📁 Examples

### `basic_usage.py`
**Simple memory recording and context injection**

Shows how to:
- Initialize Memori with basic settings
- Enable universal memory recording  
- See context automatically injected across conversations

```bash
python basic_usage.py
```

### `personal_assistant.py`  
**AI assistant that remembers your preferences**

Demonstrates:
- Personal memory namespace
- Preference and context retention
- Personalized responses based on memory

```bash
python personal_assistant.py
```

### `advanced_config.py`
**Configuration management and production settings**

Examples of:
- Configuration file usage
- Environment variable setup
- Production-ready configuration

```bash
python advanced_config.py
```

### `memori.json`
**Sample configuration file**

Template configuration showing:
- Database settings
- Agent configuration  
- Memory management options
- Logging preferences

## 🚀 Running Examples

1. **Install Memori**:
   ```bash
   pip install memorisdk
   ```

2. **Set API Key**:
   ```bash
   export OPENAI_API_KEY="sk-your-key-here"
   ```
   Or create `.env` file:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```

3. **Run Examples**:
   ```bash
   cd examples
   python basic_usage.py
   ```

## 💡 Key Concepts Demonstrated

- **Universal Integration**: Works with any LLM library
- **Conscious Context Injection**: Relevant memories automatically added
- **Memory Types**: Facts, preferences, skills, rules, context
- **Configuration**: File-based, environment, and programmatic setup
- **Namespaces**: Separate memory spaces for different projects

## 🎯 Philosophy in Action

These examples show Memori's core philosophy:
- **Second-memory for LLM work** - Never repeat context
- **Simple, reliable architecture** - Just works out of the box  
- **Flexible configuration** - Adapt to your workflow
- **Conscious context injection** - Intelligent memory retrieval

## 🔄 Next Steps

After running examples:
1. Check the generated `.db` files to see stored memories
2. Experiment with different namespaces
3. Try various LLM libraries (OpenAI, Anthropic, etc.)
4. Customize configuration for your use case