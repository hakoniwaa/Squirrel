# Supported LLM Providers

Memori provides universal integration with any LLM provider through multiple integration approaches. Below is a comprehensive table of tested and supported LLM providers with links to working examples.

## Supported LLM Providers

| Provider | Example Link |
|----------|--------------|
| **OpenAI** | [OpenAI Example](https://github.com/GibsonAI/memori/tree/main/examples/supported_llms/openai_example.py) |
| **Azure OpenAI** | [Azure Example](https://github.com/GibsonAI/memori/tree/main/examples/supported_llms/azure_example.py) |
| **LiteLLM** | [LiteLLM Example](https://github.com/GibsonAI/memori/tree/main/examples/supported_llms/litellm_example.py) |
| **Ollama** | [Ollama Example](https://github.com/GibsonAI/memori/tree/main/examples/supported_llms/ollama_example.py) |
| **Any OpenAI-Compatible** | [Provider Config](https://github.com/GibsonAI/memori/tree/main/memori/core/providers.py) |

## Community Contributions

Missing a provider? Memori's universal integration approach means most LLM providers work out of the box. If you need specific support for a new provider:

1. Check if it's OpenAI-compatible (most are)
2. Try the universal integration first
3. Open an issue if you need custom integration support

All examples and integrations are maintained in the [GitHub repository](https://github.com/GibsonAI/memori) with regular updates as new providers and frameworks emerge.