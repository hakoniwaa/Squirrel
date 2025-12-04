# coder-mcp Developer Guide

## Getting Started

### Prerequisites

- Python 3.10+ (tested up to 3.13)
- Poetry for dependency management
- Redis (optional, for vector storage)
- OpenAI API key (optional, for embeddings)

### Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/coder-mcp/coder-mcp.git
cd coder-mcp
```

2. **Install Poetry**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. **Install dependencies**
```bash
# Install all dependencies including dev and test groups
poetry install --with dev,test

# Install pre-commit hooks
poetry run pre-commit install
```

4. **Set up environment**
```bash
# Copy example environment file
cp .env.mcp.example .env.mcp

# Edit .env.mcp with your settings
```

5. **Run tests**
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=coder_mcp --cov-report=html

# Run specific test categories
poetry run pytest -m "not integration"  # Skip integration tests
poetry run pytest -m redis  # Only Redis tests
```

## Project Structure

```
coder-mcp/
├── coder_mcp/              # Main package
│   ├── __init__.py
│   ├── server.py           # Main MCP server
│   ├── core/               # Core functionality
│   │   ├── config/         # Configuration management
│   │   ├── providers/      # Provider interfaces
│   │   └── manager.py      # Configuration manager
│   ├── context/            # Context management
│   │   ├── manager.py      # Context orchestrator
│   │   ├── indexer.py      # File indexing
│   │   └── search.py       # Search functionality
│   ├── tools/              # MCP tools
│   │   ├── __init__.py
│   │   ├── handlers.py     # Tool registry
│   │   ├── file_ops.py     # File operations
│   │   ├── search.py       # Search tools
│   │   └── analysis.py     # Analysis tools
│   ├── analysis/           # Code analysis
│   │   ├── analyzer.py     # Main analyzer
│   │   ├── languages/      # Language-specific
│   │   └── visitors/       # AST visitors
│   ├── templates/          # Code templates
│   │   ├── manager.py      # Template engine
│   │   └── generators/     # Language generators
│   └── security/           # Security features
│       ├── validator.py    # Input validation
│       └── sandbox.py      # Path restrictions
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test fixtures
├── scripts/               # Utility scripts
├── docs/                  # Documentation
└── pyproject.toml         # Project configuration
```

## Core Concepts

### 1. Providers

Providers are pluggable implementations for various services:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class EmbeddingProvider(ABC):
    """Base class for embedding providers."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider."""
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass
```

### 2. Tools

Tools are MCP-compatible functions:

```python
from coder_mcp.tools import tool_handler, ToolResult

@tool_handler(
    name="my_tool",
    description="Does something useful",
    input_schema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
            "param2": {"type": "integer", "default": 10}
        },
        "required": ["param1"]
    }
)
async def my_tool(param1: str, param2: int = 10) -> ToolResult:
    """Tool implementation."""
    # Your implementation here
    return ToolResult(
        success=True,
        data={"result": "something"}
    )
```

### 3. Configuration

Configuration uses Pydantic models:

```python
from pydantic import BaseModel, Field

class MyFeatureConfig(BaseModel):
    """Configuration for my feature."""

    enabled: bool = Field(True, description="Enable this feature")
    timeout: int = Field(30, description="Timeout in seconds", ge=1)
    options: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
```

## Adding New Features

### 1. Adding a New Provider

**Step 1: Create the provider interface**

```python
# coder_mcp/core/providers/my_provider.py
from abc import ABC, abstractmethod

class MyProvider(ABC):
    """Abstract base for my provider."""

    @abstractmethod
    async def do_something(self, input: str) -> str:
        """Do something with input."""
        pass
```

**Step 2: Implement the provider**

```python
# coder_mcp/providers/my_provider_impl.py
from coder_mcp.core.providers import MyProvider

class MyProviderImpl(MyProvider):
    """Concrete implementation."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def initialize(self) -> None:
        """Initialize the provider."""
        # Setup connections, etc.

    async def do_something(self, input: str) -> str:
        """Implementation."""
        return f"Processed: {input}"
```

**Step 3: Register with factory**

```python
# coder_mcp/core/providers/factory.py
def create_my_provider(config: Dict[str, Any]) -> MyProvider:
    """Create provider based on config."""
    provider_type = config.get("type", "default")

    if provider_type == "default":
        from coder_mcp.providers import MyProviderImpl
        return MyProviderImpl(config)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
```

### 2. Adding a New Tool

**Step 1: Create tool module**

```python
# coder_mcp/tools/my_new_tool.py
from typing import Dict, Any
from coder_mcp.tools import tool_handler, ToolResult

@tool_handler(
    name="my_new_tool",
    description="Performs a new operation",
    input_schema={
        "type": "object",
        "properties": {
            "input": {"type": "string", "description": "Input data"},
            "options": {"type": "object", "description": "Options"}
        },
        "required": ["input"]
    }
)
async def my_new_tool(
    input: str,
    options: Dict[str, Any] = None
) -> ToolResult:
    """
    Implement the new tool.

    Args:
        input: The input string
        options: Optional configuration

    Returns:
        ToolResult with the output
    """
    # Validate input
    if not input:
        return ToolResult(
            success=False,
            error="Input cannot be empty"
        )

    # Process
    result = await process_input(input, options or {})

    return ToolResult(
        success=True,
        data={"result": result}
    )
```

**Step 2: Register the tool**

```python
# coder_mcp/tools/handlers.py
from .my_new_tool import my_new_tool

class ToolHandlers:
    def __init__(self):
        self.register_tool(my_new_tool)
```

**Step 3: Add tests**

```python
# tests/unit/test_my_new_tool.py
import pytest
from coder_mcp.tools.my_new_tool import my_new_tool

class TestMyNewTool:
    @pytest.mark.asyncio
    async def test_basic_functionality(self):
        result = await my_new_tool("test input")
        assert result.success
        assert result.data["result"] == "expected output"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        result = await my_new_tool("")
        assert not result.success
        assert "empty" in result.error
```

### 3. Adding Language Support

**Step 1: Create language analyzer**

```python
# coder_mcp/analysis/languages/rust.py
import ast
from typing import Dict, Any
from coder_mcp.analysis.base import LanguageAnalyzer

class RustAnalyzer(LanguageAnalyzer):
    """Analyzer for Rust code."""

    language = "rust"
    file_extensions = [".rs"]

    async def analyze(self, content: str) -> Dict[str, Any]:
        """Analyze Rust code."""
        # Parse and analyze
        metrics = {
            "functions": 0,
            "structs": 0,
            "traits": 0,
            "impls": 0,
        }

        # Your analysis logic here

        return {
            "language": self.language,
            "metrics": metrics,
            "imports": [],
            "exports": []
        }
```

**Step 2: Register analyzer**

```python
# coder_mcp/analysis/registry.py
from .languages.rust import RustAnalyzer

LANGUAGE_ANALYZERS = {
    "rust": RustAnalyzer,
    # ... other analyzers
}
```

## Testing

### 1. Unit Tests

Test individual components in isolation:

```python
# tests/unit/test_example.py
import pytest
from unittest.mock import Mock, AsyncMock

class TestMyComponent:
    """Test my component."""

    @pytest.fixture
    def component(self):
        """Create component instance."""
        return MyComponent()

    def test_sync_method(self, component):
        """Test synchronous method."""
        result = component.sync_method("input")
        assert result == "expected"

    @pytest.mark.asyncio
    async def test_async_method(self, component):
        """Test asynchronous method."""
        result = await component.async_method("input")
        assert result == "expected"

    @pytest.mark.asyncio
    async def test_with_mock(self, component):
        """Test with mocked dependency."""
        component.dependency = AsyncMock(return_value="mocked")
        result = await component.method_using_dependency()
        assert result == "mocked"
```

### 2. Integration Tests

Test component interactions:

```python
# tests/integration/test_integration.py
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow(mcp_server, temp_workspace):
    """Test complete workflow."""
    # Create file
    await mcp_server.handle_tool_call(
        "write_file",
        {"path": "test.py", "content": "print('hello')"}
    )

    # Analyze it
    analysis = await mcp_server.handle_tool_call(
        "analyze_code",
        {"path": "test.py"}
    )

    assert analysis["data"]["language"] == "python"
```

### 3. Testing Best Practices

1. **Use fixtures for common setup**
```python
@pytest.fixture
async def redis_client():
    """Provide Redis client for tests."""
    client = await create_test_redis()
    yield client
    await client.flushall()
```

2. **Mark tests appropriately**
```python
@pytest.mark.slow
@pytest.mark.redis
async def test_redis_operations():
    """Test that requires Redis."""
    pass
```

3. **Test error cases**
```python
async def test_error_handling():
    """Test error scenarios."""
    with pytest.raises(ValidationError):
        await tool("invalid input")
```

## Code Style

### 1. Python Style

Follow PEP 8 with these modifications:
- Line length: 100 characters
- Use type hints for all public APIs
- Use docstrings for all public functions

### 2. Import Order

```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import pytest
from pydantic import BaseModel

# Local
from coder_mcp.core import ConfigManager
from coder_mcp.tools import tool_handler
```

### 3. Docstrings

Use Google-style docstrings:

```python
def my_function(param1: str, param2: int = 10) -> Dict[str, Any]:
    """
    Brief description of function.

    Longer description if needed, explaining behavior,
    edge cases, etc.

    Args:
        param1: Description of param1
        param2: Description of param2 with default

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is not numeric

    Example:
        >>> result = my_function("test", 20)
        >>> print(result["status"])
        success
    """
```

## Performance Optimization

### 1. Profiling

Use built-in profiler:

```python
import cProfile
import pstats

def profile_function():
    """Profile a function."""
    profiler = cProfile.Profile()
    profiler.enable()

    # Your code here
    result = expensive_operation()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10
```

### 2. Async Best Practices

```python
# Good: Concurrent execution
results = await asyncio.gather(
    fetch_data1(),
    fetch_data2(),
    fetch_data3()
)

# Bad: Sequential execution
result1 = await fetch_data1()
result2 = await fetch_data2()
result3 = await fetch_data3()
```

### 3. Caching

```python
from functools import lru_cache
from coder_mcp.core.cache import async_cache

@lru_cache(maxsize=128)
def expensive_computation(input: str) -> str:
    """Cached synchronous function."""
    return compute(input)

@async_cache(ttl=3600)
async def expensive_async_operation(input: str) -> str:
    """Cached async function with TTL."""
    return await fetch_data(input)
```

## Debugging

### 1. Debug Logging

```python
import logging

logger = logging.getLogger(__name__)

# Set debug level
logger.setLevel(logging.DEBUG)

# Use structured logging
logger.debug(
    "Processing request",
    extra={
        "tool": tool_name,
        "args": arguments,
        "user": user_id
    }
)
```

### 2. Interactive Debugging

```python
import pdb

def debug_function():
    """Function with debugger."""
    # Set breakpoint
    pdb.set_trace()

    # Or use breakpoint() in Python 3.7+
    breakpoint()
```

### 3. Async Debugging

```python
import asyncio

# Enable debug mode
asyncio.run(main(), debug=True)

# Or set environment variable
# PYTHONASYNCIODEBUG=1 python script.py
```

## Release Process

### 1. Version Bump

```bash
# Bump version in pyproject.toml
poetry version patch  # or minor, major
```

### 2. Update Changelog

```markdown
## [5.1.0] - 2024-06-23

### Added
- New feature X
- Support for Y

### Changed
- Improved Z performance

### Fixed
- Bug in feature A
```

### 3. Run Release Checks

```bash
# Run all tests
poetry run pytest

# Check code quality
poetry run black --check .
poetry run isort --check .
poetry run flake8
poetry run mypy

# Build package
poetry build
```

### 4. Create Release

```bash
# Tag release
git tag -a v5.1.0 -m "Release version 5.1.0"
git push origin v5.1.0

# Publish to PyPI (if applicable)
poetry publish
```

## Common Issues

### 1. Import Errors

**Problem**: `ModuleNotFoundError`
**Solution**: Ensure you're using Poetry shell or running with `poetry run`

### 2. Redis Connection

**Problem**: Cannot connect to Redis
**Solution**: Check Redis is running and configuration is correct

### 3. Type Errors

**Problem**: Type checking failures
**Solution**: Update type stubs: `poetry add --group dev types-redis`

## Resources

- [MCP Specification](https://github.com/modelcontextprotocol/specification)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Redis Documentation](https://redis.io/documentation)
- [AsyncIO Documentation](https://docs.python.org/3/library/asyncio.html)
