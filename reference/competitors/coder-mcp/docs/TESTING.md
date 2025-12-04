# coder-mcp Testing Guide

## Testing Overview

coder-mcp uses a comprehensive testing strategy with multiple levels:

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test component interactions
3. **System Tests** - Test the complete MCP server
4. **Performance Tests** - Benchmark and profile

## Running Tests

### Basic Commands

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=coder_mcp --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_code_analyzer.py

# Run specific test
poetry run pytest tests/unit/test_code_analyzer.py::TestCodeAnalyzer::test_analyze_file_python

# Run tests matching pattern
poetry run pytest -k "test_analyze"

# Run with verbose output
poetry run pytest -v

# Run in parallel
poetry run pytest -n auto
```

### Test Categories

```bash
# Skip slow tests
poetry run pytest -m "not slow"

# Run only unit tests
poetry run pytest -m "not integration"

# Run only Redis tests
poetry run pytest -m redis

# Run only tests that don't require external services
poetry run pytest -m "not redis and not openai"
```

## Test Structure

### Test Markers

```python
import pytest

@pytest.mark.unit
def test_basic_functionality():
    """Fast unit test."""
    pass

@pytest.mark.integration
def test_component_interaction():
    """Integration test."""
    pass

@pytest.mark.redis
def test_redis_operations():
    """Test requiring Redis."""
    pass

@pytest.mark.slow
def test_performance():
    """Slow test."""
    pass

@pytest.mark.skipif(not has_gpu(), reason="GPU not available")
def test_gpu_operations():
    """Test requiring GPU."""
    pass
```

### Test Fixtures

Common fixtures in `conftest.py`:

```python
@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace

@pytest.fixture
async def mock_redis():
    """Provide mock Redis for testing."""
    from tests.mocks import MockRedis
    redis = MockRedis()
    await redis.initialize()
    yield redis
    await redis.cleanup()

@pytest.fixture
async def mcp_server(temp_workspace, mock_redis):
    """Create MCP server instance."""
    server = ModularMCPServer(workspace_root=temp_workspace)
    await server.initialize()
    yield server
    await server.cleanup()
```

## Writing Tests

### Unit Test Example

```python
# tests/unit/test_example.py
import pytest
from unittest.mock import Mock, AsyncMock, patch

from coder_mcp.tools.file_ops import FileOperations

class TestFileOperations:
    """Test file operations."""

    @pytest.fixture
    def file_ops(self, temp_workspace):
        """Create FileOperations instance."""
        return FileOperations(workspace_root=temp_workspace)

    def test_get_file_type(self, file_ops):
        """Test file type detection."""
        assert file_ops.get_file_type("test.py") == "python"
        assert file_ops.get_file_type("test.js") == "javascript"
        assert file_ops.get_file_type("test.unknown") == "text"

    @pytest.mark.asyncio
    async def test_read_file(self, file_ops, temp_workspace):
        """Test file reading."""
        # Create test file
        test_file = temp_workspace / "test.txt"
        test_file.write_text("Hello, World!")

        # Read file
        result = await file_ops.read_file("test.txt")

        # Assertions
        assert result["content"] == "Hello, World!"
        assert result["size"] == 13
        assert result["encoding"] == "utf-8"

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, file_ops):
        """Test reading nonexistent file."""
        with pytest.raises(FileNotFoundError):
            await file_ops.read_file("nonexistent.txt")

    @pytest.mark.parametrize("filename,expected", [
        ("test.py", "python"),
        ("test.js", "javascript"),
        ("test.md", "markdown"),
        ("test.unknown", "text"),
    ])
    def test_file_types_parametrized(self, file_ops, filename, expected):
        """Test multiple file types."""
        assert file_ops.get_file_type(filename) == expected
```

### Integration Test Example

```python
# tests/integration/test_search_integration.py
import pytest

@pytest.mark.integration
class TestSearchIntegration:
    """Test search functionality with real components."""

    @pytest.mark.asyncio
    async def test_semantic_search(self, mcp_server, temp_workspace):
        """Test semantic search across files."""
        # Create test files
        files = {
            "calculator.py": """
def add(a, b):
    '''Add two numbers'''
    return a + b
""",
            "math_utils.py": """
def multiply(x, y):
    '''Multiply two values'''
    return x * y
""",
            "string_utils.py": """
def concat(s1, s2):
    '''Concatenate strings'''
    return s1 + s2
"""
        }

        for filename, content in files.items():
            await mcp_server.handle_tool_call(
                "write_file",
                {"path": filename, "content": content}
            )

        # Initialize context
        await mcp_server.handle_tool_call(
            "initialize_context",
            {"force_refresh": True}
        )

        # Search for arithmetic operations
        results = await mcp_server.handle_tool_call(
            "search_context",
            {"query": "arithmetic operations on numbers"}
        )

        # Should find calculator.py and math_utils.py
        assert len(results["data"]) >= 2
        file_names = [r["file_path"] for r in results["data"]]
        assert "calculator.py" in file_names
        assert "math_utils.py" in file_names
```

### Performance Test Example

```python
# tests/performance/test_indexing_performance.py
import pytest
import time

@pytest.mark.performance
@pytest.mark.slow
class TestIndexingPerformance:
    """Test indexing performance."""

    @pytest.mark.asyncio
    async def test_large_project_indexing(self, mcp_server, temp_workspace):
        """Test indexing performance on large project."""
        # Create many files
        num_files = 100
        for i in range(num_files):
            content = f"""
def function_{i}():
    '''Function {i} documentation'''
    return {i}
"""
            await mcp_server.handle_tool_call(
                "write_file",
                {"path": f"file_{i}.py", "content": content}
            )

        # Measure indexing time
        start_time = time.time()
        await mcp_server.handle_tool_call(
            "initialize_context",
            {"force_refresh": True}
        )
        elapsed_time = time.time() - start_time

        # Performance assertions
        assert elapsed_time < 10.0  # Should index 100 files in < 10s

        # Verify all files indexed
        context = await mcp_server.get_context_info()
        assert context["files_indexed"] == num_files
```

## Testing Best Practices

### 1. Test Organization

```
tests/
├── unit/              # Fast, isolated tests
├── integration/       # Component interaction tests
├── system/           # Full system tests
├── performance/      # Performance benchmarks
├── fixtures/         # Test data and files
└── mocks/           # Mock implementations
```

### 2. Mock External Services

```python
# tests/mocks/openai_mock.py
class MockOpenAIProvider:
    """Mock OpenAI provider for testing."""

    async def embed(self, text: str) -> List[float]:
        """Return deterministic embeddings."""
        # Simple hash-based embedding for testing
        hash_val = hash(text)
        return [float((hash_val >> i) & 1) for i in range(3072)]
```

### 3. Use Factories

```python
# tests/factories.py
from faker import Faker

fake = Faker()

def create_python_file(name: str = None) -> str:
    """Create Python file content."""
    name = name or fake.word()
    return f'''
def {name}():
    """{fake.sentence()}"""
    return "{fake.word()}"
'''

def create_project_structure(num_files: int = 5) -> Dict[str, str]:
    """Create project file structure."""
    return {
        f"src/{fake.word()}.py": create_python_file()
        for _ in range(num_files)
    }
```

### 4. Test Data Management

```python
# tests/fixtures/test_projects/
# ├── small_project/
# ├── large_project/
# └── edge_cases/

@pytest.fixture
def sample_project(tmp_path):
    """Copy sample project to temp directory."""
    import shutil
    source = Path("tests/fixtures/test_projects/small_project")
    shutil.copytree(source, tmp_path / "project")
    return tmp_path / "project"
```

## Coverage Reports

### Generate Coverage

```bash
# Run tests with coverage
poetry run pytest --cov=coder_mcp --cov-report=html --cov-report=term

# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Configuration

```toml
# pyproject.toml
[tool.coverage.run]
source = ["coder_mcp"]
branch = true
omit = [
    "*/tests/*",
    "*/.venv/*",
    "*/migrations/*",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

## Debugging Tests

### 1. Print Debugging

```python
def test_complex_logic(capsys):
    """Test with print debugging."""
    result = complex_function()

    # Capture print output
    captured = capsys.readouterr()
    print(f"Result: {result}")
    print(f"Captured output: {captured.out}")

    assert result == expected
```

### 2. Interactive Debugging

```python
def test_debug_me():
    """Test with debugger."""
    # Drop into debugger
    import pdb; pdb.set_trace()

    # Or use breakpoint() in Python 3.7+
    breakpoint()
```

### 3. Pytest Debugging

```bash
# Drop into debugger on failure
poetry run pytest --pdb

# Drop into debugger on first failure
poetry run pytest -x --pdb

# Show local variables on failure
poetry run pytest -l

# Maximum verbosity
poetry run pytest -vvv

# Show print statements
poetry run pytest -s
```

### 4. Async Debugging

```python
@pytest.mark.asyncio
async def test_async_debug():
    """Debug async code."""
    # Enable asyncio debug mode
    import asyncio
    asyncio.get_event_loop().set_debug(True)

    # Your async test
    result = await async_function()
    assert result == expected
```

## Common Test Issues

### 1. Flaky Tests

```python
# Mark flaky tests
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_unreliable_network():
    """Test that might fail due to network."""
    pass

# Or use pytest-retry
@pytest.mark.retry(3)
def test_with_retry():
    """Test with automatic retry."""
    pass
```

### 2. Test Isolation

```python
# Ensure test isolation
@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state before each test."""
    # Setup
    clear_caches()
    reset_singletons()

    yield

    # Teardown
    clear_caches()
    reset_singletons()
```

### 3. Async Test Issues

```python
# Correct async test setup
@pytest.mark.asyncio
async def test_async_correctly():
    """Properly structured async test."""
    # Use async fixtures
    async with create_resource() as resource:
        result = await resource.operation()
        assert result == expected

# Wrong - don't do this
def test_async_wrong():
    """This will fail."""
    result = asyncio.run(async_function())  # Don't use asyncio.run in tests
```

### 4. Resource Cleanup

```python
# Ensure cleanup with finalizers
@pytest.fixture
def database(request):
    """Database fixture with cleanup."""
    db = create_database()

    def cleanup():
        db.drop_all_tables()
        db.close()

    request.addfinalizer(cleanup)
    return db
```

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python: [3.10, 3.11, 3.12, 3.13]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python }}

    - name: Install Poetry
      run: |
        curl -sSL https://install.python-poetry.org | python3 -

    - name: Install dependencies
      run: poetry install --with dev,test

    - name: Run tests
      run: poetry run pytest --cov=coder_mcp

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      if: matrix.python == '3.11' && matrix.os == 'ubuntu-latest'
```

## Test Checklist

Before committing:

- [ ] All tests pass locally
- [ ] New features have tests
- [ ] Bug fixes have regression tests
- [ ] Coverage hasn't decreased
- [ ] No hardcoded paths or credentials
- [ ] Tests work in isolation
- [ ] Performance tests pass
- [ ] Documentation updated

## Advanced Testing

### Property-Based Testing

```python
from hypothesis import given, strategies as st

@given(st.text())
def test_encoding_roundtrip(text):
    """Test encoding/decoding is lossless."""
    encoded = encode(text)
    decoded = decode(encoded)
    assert decoded == text
```

### Mutation Testing

```bash
# Install mutmut
poetry add --group dev mutmut

# Run mutation testing
poetry run mutmut run --paths-to-mutate=coder_mcp

# View results
poetry run mutmut results
```

### Load Testing

```python
# tests/load/test_concurrent_operations.py
import asyncio
import pytest

@pytest.mark.load
async def test_concurrent_file_operations(mcp_server):
    """Test server under load."""
    num_operations = 100

    async def file_operation(i):
        await mcp_server.handle_tool_call(
            "write_file",
            {"path": f"test_{i}.txt", "content": f"Content {i}"}
        )
        result = await mcp_server.handle_tool_call(
            "read_file",
            {"path": f"test_{i}.txt"}
        )
        assert result["data"]["content"] == f"Content {i}"

    # Run operations concurrently
    start_time = time.time()
    await asyncio.gather(*[
        file_operation(i) for i in range(num_operations)
    ])
    elapsed = time.time() - start_time

    # Should handle 100 operations efficiently
    assert elapsed < 10.0
```
