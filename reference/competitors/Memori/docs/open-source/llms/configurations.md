# LLM Provider Configuration

Configuration examples for different LLM providers with Memori.

## Provider Configuration Overview

Memori supports multiple LLM providers through the `ProviderConfig` class and universal integration.

## OpenAI Configuration

```python
from openai import OpenAI
from memori import Memori

# Simple OpenAI setup - uses OPENAI_API_KEY environment variable
client = OpenAI()

# Initialize Memori with universal integration
openai_memory = Memori(
    database_connect="sqlite:///openai_demo.db",
    conscious_ingest=True,
    auto_ingest=True,
    verbose=True,
)

# Enable universal memory tracking
openai_memory.enable()

# Use OpenAI normally - automatically recorded
response = client.chat.completions.create(
    model="gpt-4o", 
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Environment Variables
```bash
export OPENAI_API_KEY="sk-your-openai-api-key"
```

## Azure OpenAI Configuration

```python
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
    api_version="2024-08-01-preview",
    model="gpt-4o",
)

# Initialize Memori with Azure provider
azure_memory = Memori(
    database_connect="sqlite:///azure_demo.db",
    conscious_ingest=True,
    auto_ingest=True,
    verbose=True,
    provider_config=azure_provider,
)

# Create client using the provider config
client = azure_provider.create_client()

# Enable memory tracking
azure_memory.enable()

# Use Azure OpenAI - automatically recorded
response = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    messages=[{"role": "user", "content": "Hello"}],
)
```

### Environment Variables
```bash
export AZURE_OPENAI_API_KEY="your-azure-openai-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-deployment-name"
```

## LiteLLM Configuration

```python
from litellm import completion
from memori import Memori

# Initialize Memori for LiteLLM
litellm_memory = Memori(
    database_connect="sqlite:///litellm_demo.db",
    conscious_ingest=True,
    auto_ingest=True,
)

# Enable memory tracking
litellm_memory.enable()

# Use any LiteLLM-supported model - automatically recorded
response = completion(
    model="gpt-4o", 
    messages=[{"role": "user", "content": "Hello"}]
)

# Works with any provider through LiteLLM
response = completion(
    model="claude-3-sonnet-20240229",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Environment Variables
```bash
# For OpenAI through LiteLLM
export OPENAI_API_KEY="sk-your-openai-api-key"

# For Anthropic through LiteLLM
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# For any other provider supported by LiteLLM
```

## Ollama Configuration

```python
import os
from memori import Memori
from memori.core.providers import ProviderConfig

# Create Ollama provider configuration
ollama_provider = ProviderConfig.from_custom(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # Ollama doesn't require an API key, but OpenAI client needs something
    model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),  # Default to llama3.2:3b
)

# Initialize Memori with Ollama
ollama_memory = Memori(
    database_connect="sqlite:///ollama_demo.db",
    conscious_ingest=True,
    auto_ingest=True,
    verbose=True,
    provider_config=ollama_provider,
)

# Create client using the provider config
client = ollama_provider.create_client()

# Enable memory tracking
ollama_memory.enable()

# Use Ollama - automatically recorded
response = client.chat.completions.create(
    model=ollama_provider.model,
    messages=[{"role": "user", "content": "Hello"}],
)
```

### Environment Variables
```bash
export OLLAMA_MODEL="llama3.2:3b"
```

### Prerequisites
```bash
# Start Ollama server
ollama serve

# Pull the model
ollama pull llama3.2:3b
```