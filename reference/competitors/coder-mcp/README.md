# coder-mcp: The Intelligent Code Development MCP Server 🚀

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/coder-mcp?style=for-the-badge)](https://pypi.org/project/coder-mcp/)
[![Python Versions](https://img.shields.io/pypi/pyversions/coder-mcp?style=for-the-badge)](https://pypi.org/project/coder-mcp/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](https://opensource.org/licenses/MIT)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success?style=for-the-badge)
![MCP](https://img.shields.io/badge/MCP-Compatible-purple?style=for-the-badge)

**Transform Claude into your most intelligent coding assistant with persistent memory, advanced code analysis, and context-aware development tools.**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Examples](#-examples) • [Contributing](#-contributing)

</div>

---

## 🌟 What Makes coder-mcp Unique?

While other MCP servers provide basic file operations or simple integrations, **coder-mcp** is the first comprehensive code intelligence platform for AI assistants. It's not just about reading and writing files—it's about understanding your entire codebase, remembering context across sessions, and providing intelligent assistance that improves over time.

### 🎯 **The Problem**
- Traditional MCP servers forget everything between sessions
- Basic file operations lack code understanding
- No semantic awareness of relationships between files
- Limited to simple read/write operations
- No code quality analysis or intelligent suggestions

### 💡 **Our Solution**
- **Persistent vector-based memory** that survives across sessions
- **AST-based code analysis** for deep understanding
- **Semantic search** across your entire codebase
- **Intelligent scaffolding** with best practices built-in
- **Multi-language support** with extensible architecture

---

## 🚀 Features

### 🧠 **Intelligent Context Management**
- **Cross-Session Memory**: Your AI assistant remembers your project, decisions, and patterns
- **Vector-Based Search**: Find code by meaning, not just text matching
- **Relationship Mapping**: Understands how files relate to each other
- **Project Intelligence**: Builds comprehensive knowledge of your codebase

### 🔍 **Advanced Code Analysis**
- **AST-Based Understanding**: Goes beyond text to understand code structure
- **Multi-Language Support**: Python, JavaScript, TypeScript (more coming)
- **Code Smell Detection**: Identifies issues like long functions, complex conditionals
- **Dependency Analysis**: Tracks and analyzes your project dependencies
- **Quality Metrics**: Calculates complexity, maintainability scores

### 🏗️ **Intelligent Code Generation**
- **Smart Scaffolding**: Generate boilerplate with your patterns and preferences
- **Best Practices**: Automatically applies language-specific best practices
- **Template System**: Extensible templates for common patterns
- **Context-Aware**: Uses your existing code style and patterns

### 🔒 **Enterprise-Ready Architecture**
- **Secure by Design**: Path traversal protection, input validation
- **High Performance**: Redis-backed storage with efficient caching
- **Scalable**: Handles large codebases with thousands of files
- **Reliable**: Comprehensive error handling and recovery

---

## 📋 Requirements

- Python 3.10+
- Redis server (for vector storage and caching)
- 4GB+ RAM recommended
- OpenAI API key (for embeddings)

---

## 🚀 Quick Start

### Installation

#### Install from PyPI (Recommended)

```bash
pip install coder-mcp
```

#### Install from Source

```bash
git clone https://github.com/coder-mcp/coder-mcp.git
cd coder-mcp
pip install -e .
```

### Configuration

1. **Set up your environment variables:**

```bash
cp .env.example .env
# Edit .env with your configuration:
# - OPENAI_API_KEY (required for embeddings)
# - REDIS_URL (defaults to localhost:6379)
# - Other optional settings
```

2. **Add to your MCP settings:**

```json
    "coder-mcp": {
      "command": "/{path}/{path}/{path}/coder-mcp/.venv/bin/python",
      "args": [
        "-m",
        "coder_mcp.server"
      ],
      "cwd": "/{path}/{path}/{path}/coder-mcp",
      "env": {
        "MCP_WORKSPACE_ROOT": "/{path}/{to}/{target}/{project}",
        "OPENAI_API_KEY": "sk-svcacct-xxxxxxxxxxxxxxxx"
      }
    }
```
<!-- pragma: allowlist secret -->

3. **Start using with Claude Desktop or your MCP client!**

---

## 🎯 Example Usage

### Initialize Your Project
```
"Initialize the coder-mcp context for my Python project"
```

### Smart Code Analysis
```
"Analyze the code quality of my API endpoints and suggest improvements"
```

### Intelligent Search
```
"Find all functions that handle user authentication"
```

### Generate Code with Context
```
"Create a new REST endpoint following the patterns in my existing code"
```

### Refactoring Assistant
```
"Help me refactor the payment processing module to improve testability"
```

---

## 📚 Documentation

- [Getting Started Guide](docs/GETTING_STARTED.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Development Guide](docs/DEVELOPER_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

---

## 🛠️ Advanced Features

### Vector Search Capabilities
```python
# Semantic search across your codebase
results = await search_context("functions that validate user input")
```

### Code Quality Analysis
```python
# Get detailed metrics and suggestions
analysis = await analyze_code("src/api/", analysis_type="deep")
```

### Smart Editing
```python
# Natural language code modifications
await smart_edit("add error handling to all database operations")
```

### Project Intelligence
```python
# Get AI-powered improvement suggestions
roadmap = await generate_improvement_roadmap(focus_areas=["security", "performance"])
```

---

## 🏗️ Architecture

coder-mcp is built with a modular, extensible architecture:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   MCP Client    │────▶│  coder-mcp      │────▶│     Redis       │
│ (Claude, etc.)  │     │    Server       │     │  Vector Store   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   Code Intel    │
                        │   Subsystems    │
                        └─────────────────┘
```

---

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Clone the repository
git clone https://github.com/coder-mcp/coder-mcp.git
cd coder-mcp

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black . && isort . && flake8
```

---

## 📊 Performance

- **Indexing Speed**: ~1000 files/second
- **Search Latency**: <100ms for most queries
- **Memory Usage**: ~500MB for 10k file project
- **Startup Time**: <2 seconds

---

## 🔒 Security

- Path traversal protection
- Input sanitization
- Secure credential handling
- No arbitrary code execution
- Audit logging for sensitive operations

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=coder-mcp/coder-mcp&type=Date)](https://star-history.com/#coder-mcp/coder-mcp&Date)

---

## 🙏 Acknowledgments

- Built on the [Model Context Protocol](https://modelcontextprotocol.com)
- Inspired by the need for better AI-assisted development
- Thanks to all our contributors and early adopters

---

<div align="center">
Made with ❤️ by the coder-mcp team

[Report Bug](https://github.com/coder-mcp/coder-mcp/issues) • [Request Feature](https://github.com/coder-mcp/coder-mcp/issues) • [Join Discussion](https://github.com/coder-mcp/coder-mcp/discussions)
</div>
