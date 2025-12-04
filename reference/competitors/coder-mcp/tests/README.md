# Testing Best Practices for MCP Server

This guide provides comprehensive best practices for maintaining a world-class test suite.

## Table of Contents
1. [Test Organization](#test-organization)
2. [Writing Effective Tests](#writing-effective-tests)
3. [Mocking Strategies](#mocking-strategies)
4. [Async Testing](#async-testing)
5. [Performance Testing](#performance-testing)
6. [Test Data Management](#test-data-management)
7. [Debugging Tests](#debugging-tests)
8. [CI/CD Best Practices](#cicd-best-practices)

## Test Organization

### Directory Structure
```
tests/
├── unit/          # Fast, isolated tests
├── integration/   # Tests with real dependencies
├── e2e/          # Complete workflow tests
├── performance/   # Performance benchmarks
└── fixtures/      # Shared test data
```

### Naming Conventions
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<what_is_being_tested>`

### Example:
```python
# tests/unit/test_context_manager.py
class TestContextManagerFileOperations:
    def test_read_file_returns_content_on_success(self):
        """Test that read_file returns file content when successful."""
        # Test implementation
```

## Writing Effective Tests

### The AAA Pattern
Always structure tests with Arrange, Act, Assert:

```python
@pytest.mark.asyncio
async def test_file_caching(context_manager, temp_file):
    # Arrange
    expected_content = "test content"
    temp_file.write_text(expected_content)

    # Act
    first_read = await context_manager.read_file(temp_file.name)
    second_read = await context_manager.read_file(temp_file.name)

    # Assert
    assert first_read == expected_content
    assert second_read == expected_content
    assert context_manager.cache_hits == 1
```

### Test One Thing
Each test should verify a single behavior:

```python
# Good: Focused tests
def test_validation_rejects_path_traversal():
    assert not is_valid_path("../../../etc/passwd")

def test_validation_accepts_relative_paths():
    assert is_valid_path("src/main.py")

# Bad: Testing multiple things
def test_path_validation():
    assert is_valid_path("src/main.py")
    assert not is_valid_path("../../../etc/passwd")
    assert not is_valid_path("/etc/passwd")
    # Too many assertions!
```

### Use Descriptive Names
Test names should describe what they test and expected outcome:

```python
# Good
def test_read_file_raises_file_not_found_for_missing_file():
    pass

# Bad
def test_read_file_error():
    pass
```

## Mocking Strategies

### Mock at the Right Level
Mock external dependencies, not internal implementation:

```python
# Good: Mock external dependency
@patch('coder_mcp.storage.redis_client')
async def test_cache_fallback(mock_redis):
    mock_redis.get.side_effect = ConnectionError()
    # Test continues with local fallback

# Bad: Mocking internal methods
@patch.object(ContextManager, '_internal_method')
async def test_something(mock_method):
    # Too coupled to implementation
```

### Use Spec for Type Safety
Always use `spec` or `autospec` to catch interface changes:

```python
# Good
mock_store = Mock(spec=RedisVectorStore)
mock_store.search.return_value = []

# This would fail - good!
# mock_store.nonexistent_method()
```

### Mock Side Effects for Realistic Behavior
```python
# Simulate retry behavior
call_count = 0
def side_effect(*args):
    nonlocal call_count
    call_count += 1
    if call_count < 3:
        raise ConnectionError("Temporary failure")
    return "Success"

mock_api.call = Mock(side_effect=side_effect)
```

## Async Testing

### Use pytest-asyncio Fixtures
```python
@pytest_asyncio.fixture
async def initialized_server():
    server = MCPServer()
    await server.initialize()
    yield server
    await server.cleanup()
```

### Test Concurrent Operations
```python
@pytest.mark.asyncio
async def test_concurrent_file_reads(server):
    files = [f"file_{i}.txt" for i in range(100)]

    # Create files
    await asyncio.gather(*[
        server.write_file(f, f"content {i}")
        for i, f in enumerate(files)
    ])

    # Read concurrently
    start = time.time()
    results = await asyncio.gather(*[
        server.read_file(f) for f in files
    ])
    duration = time.time() - start

    assert len(results) == 100
    assert duration < 1.0  # Should handle 100 files in < 1s
```

### Test Timeouts
```python
@pytest.mark.asyncio
@pytest.mark.timeout(5)  # Test must complete in 5 seconds
async def test_long_operation_with_timeout():
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            very_long_operation(),
            timeout=1.0
        )
```

## Performance Testing

### Use pytest-benchmark
```python
def test_search_performance(benchmark, large_index):
    result = benchmark(
        search_index,
        query="test query",
        index=large_index
    )

    # Assertions on result
    assert len(result) > 0

    # Performance assertions
    assert benchmark.stats['mean'] < 0.1  # Mean under 100ms
    assert benchmark.stats['stddev'] < 0.02  # Consistent
```

### Memory Profiling
```python
@pytest.mark.performance
def test_memory_usage():
    import tracemalloc

    tracemalloc.start()

    # Operation to test
    process_large_dataset()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Memory usage should be reasonable
    assert peak / 1024 / 1024 < 100  # Less than 100MB
```

### Load Testing
```python
@pytest.mark.load
async def test_system_under_load():
    async def worker(server, worker_id):
        for i in range(100):
            await server.handle_request({
                "tool": "read_file",
                "params": {"path": f"file_{i}.txt"}
            })

    # Run 50 concurrent workers
    workers = [
        worker(server, i) for i in range(50)
    ]

    start = time.time()
    await asyncio.gather(*workers)
    duration = time.time() - start

    # Should handle 5000 requests reasonably fast
    assert duration < 30  # Under 30 seconds
    assert server.error_rate < 0.01  # Less than 1% errors
```

## Test Data Management

### Use Factories
```python
# tests/factories.py
class FileFactory:
    @staticmethod
    def create_python_file(
        name="test.py",
        complexity="medium",
        with_errors=False
    ):
        content = FileFactory._generate_content(complexity)
        if with_errors:
            content = FileFactory._add_errors(content)
        return {"name": name, "content": content}
```

### Fixture Composition
```python
@pytest.fixture
def small_project(temp_dir):
    return ProjectBuilder()\
        .with_size("small")\
        .with_tests()\
        .build_in(temp_dir)

@pytest.fixture
def large_project(temp_dir):
    return ProjectBuilder()\
        .with_size("large")\
        .with_files(1000)\
        .build_in(temp_dir)
```

### Parameterized Fixtures
```python
@pytest.fixture(params=["small", "medium", "large"])
def project_size(request):
    return request.param

@pytest.fixture
def test_project(project_size, temp_dir):
    return ProjectBuilder()\
        .with_size(project_size)\
        .build_in(temp_dir)
```

## Debugging Tests

### Use pytest Debugging Features
```python
# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Verbose output
pytest -vv

# Show print statements
pytest -s
```

### Add Debug Fixtures
```python
@pytest.fixture
def debug_on_failure(request):
    """Drop into debugger on test failure."""
    def fin():
        if request.node.rep_call.failed:
            import pdb; pdb.set_trace()
    request.addfinalizer(fin)
```

### Capture Logs in Tests
```python
def test_error_handling(caplog):
    with caplog.at_level(logging.ERROR):
        process_invalid_data()

    assert "Invalid data format" in caplog.text
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "ERROR"
```

## CI/CD Best Practices

### Parallel Test Execution
```yaml
# In GitHub Actions
- name: Run tests in parallel
  run: |
    poetry run pytest -n auto  # Use all CPU cores
```

### Test Sharding
```python
# Split tests across multiple CI jobs
# Job 1
pytest tests/unit --shard-id=0 --num-shards=3

# Job 2
pytest tests/unit --shard-id=1 --num-shards=3

# Job 3
pytest tests/unit --shard-id=2 --num-shards=3
```

### Fail Fast Strategy
```python
# pytest.ini
[tool.pytest.ini_options]
addopts = --maxfail=3  # Stop after 3 failures
```

### Test Result Caching
```yaml
# Cache test results to skip unchanged tests
- name: Cache pytest results
  uses: actions/cache@v3
  with:
    path: .pytest_cache
    key: pytest-${{ hashFiles('tests/**/*.py') }}
```

## Advanced Techniques

### Property-Based Testing
```python
from hypothesis import given, strategies as st

@given(
    file_content=st.text(min_size=1),
    file_name=st.from_regex(r'[a-z]+\.py')
)
async def test_write_then_read_preserves_content(
    server, file_content, file_name
):
    # Property: Writing then reading preserves content
    await server.write_file(file_name, file_content)
    read_content = await server.read_file(file_name)
    assert read_content == file_content
```

### Mutation Testing
```bash
# Install mutmut
pip install mutmut

# Run mutation testing
mutmut run --paths-to-mutate=coder_mcp/

# View results
mutmut results
```

### Contract Testing
```python
class TestMCPServerContract:
    """Ensure MCP server follows protocol specification."""

    @pytest.mark.parametrize("tool_name", get_all_tools())
    def test_tool_has_required_fields(self, server, tool_name):
        tool = server.get_tool(tool_name)
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool
        assert validate_json_schema(tool["parameters"])
```

### Snapshot Testing
```python
def test_code_generation(snapshot):
    generated_code = generate_api_endpoint("UserAuth")
    snapshot.assert_match(generated_code, 'user_auth_endpoint.py')
```

## Test Metrics and Quality

### Coverage Goals
- Unit tests: >90% coverage
- Integration tests: >80% coverage
- E2E tests: Critical paths covered

### Performance Benchmarks
- Unit tests: <10ms per test
- Integration tests: <100ms per test
- E2E tests: <5s per test
- Full suite: <5 minutes

### Quality Indicators
- No flaky tests
- Clear failure messages
- Fast feedback cycle
- Easy to debug failures
- Tests as documentation

## Continuous Improvement

1. **Regular Test Review**
   - Remove obsolete tests
   - Update test data
   - Refactor complex tests
   - Improve test names

2. **Monitor Test Metrics**
   - Track test execution time
   - Monitor coverage trends
   - Identify flaky tests
   - Measure test effectiveness

3. **Learn from Failures**
   - Add tests for bugs
   - Improve error messages
   - Document edge cases
   - Share testing knowledge

Remember: Tests are code too. Apply the same quality standards to tests as production code!
