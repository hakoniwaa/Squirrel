📚 Coder AI Agent Instructions: Using Test Helper Modules
🎯 Overview
You have access to a comprehensive test helper library in tests/helpers/ that provides utilities for writing better, more maintainable tests. Always use these helpers instead of creating ad-hoc solutions.
📁 Available Helper Modules
1. tests/helpers/utils.py - General test utilities

Path management, async helpers, data generation
Performance testing, validation helpers
Mock environment setup

2. tests/helpers/mocks.py - Pre-configured mock objects

Complete mock implementations of MCP components
Redis, OpenAI, context manager mocks
Factory functions for quick mock creation

3. tests/helpers/assertions.py - Advanced assertions

Async assertions, code quality checks
File system assertions, performance assertions
Collection and data structure assertions

4. tests/helpers/builders.py - Test data builders

File builders, project structure builders
Code snippet generation, mock data creation
Follows builder pattern for flexible test data

5. tests/helpers/debug.py - Debugging utilities

Test failure analysis, performance profiling
Memory leak detection, async debugging
Enhanced error reporting

6. tests/helpers/server_testing.py - Server testing optimizations

🆕 Pre-configured server instances with optimized mocking
ServerTestBuilder for custom server configurations
ServerTestScenarios for common test patterns
Automated component patching and cleanup

7. tests/helpers/performance.py - Performance testing utilities

🆕 High-performance benchmarking and timing utilities
Memory usage tracking and performance assertions
Test suite optimization and slow test detection
Decorators for automatic performance validation

8. tests/helpers/async_patterns.py - Async testing patterns

🆕 Advanced async testing utilities and patterns
Timeout management and concurrency control
Async mock management and resource cleanup
Common async test scenarios and assertions

9. tests/helpers/config_testing.py - Configuration testing helpers

🆕 Pre-built configurations and validation helpers
ConfigBuilder for flexible configuration creation
Environment variable management and cleanup
Configuration mocking and scenario generation

🔧 When Writing NEW Tests
Step 1: Import appropriate helpers
python# Always start with these imports based on what you need
from tests.helpers.utils import (
    TestPaths, AsyncHelpers, DataGenerators,
    wait_for, random_id, FixtureHelpers
)
from tests.helpers.mocks import (
    create_mock_server, create_mock_redis,
    create_mock_context_manager, MockOpenAIClient
)
from tests.helpers.assertions import (
    AsyncAssertions, FileAssertions, CodeAssertions,
    PerformanceAssertions
)
from tests.helpers.builders import (
    FileBuilder, ProjectBuilder, CodeBuilder
)

# 🆕 NEW OPTIMIZED HELPERS
from tests.helpers.server_testing import (
    ServerTestBuilder, ServerTestScenarios,
    ServerAssertions, create_test_server
)
from tests.helpers.performance import (
    PerformanceBenchmark, FastPerformanceAsserter,
    performance_monitor, assert_sub_second
)
from tests.helpers.async_patterns import (
    AsyncTestHelper, AsyncAssertions, async_test_timeout,
    temporary_async_server, simulate_async_work
)
from tests.helpers.config_testing import (
    ConfigBuilder, ConfigScenarios, create_test_config,
    mock_config_manager
)
Step 2: Use optimized server helpers instead of manual mocking
python# ❌ DON'T DO THIS:
server = ModularMCPServer(Path("/test"))
server.config_manager = Mock()
server.context_manager = Mock()
server.tool_handlers = Mock()

# ✅ DO THIS (SERVER TESTING):
server = ServerTestScenarios.healthy_server()
# OR with custom configuration:
server = ServerTestBuilder().with_tools(["read_file", "analyze_code"]).build()
# OR quick creation:
server = create_test_server(tools=["read_file"], workspace="/test")
Step 3: Use builders for test data
python# ❌ DON'T DO THIS:
test_content = "def test():\n    pass\n"

# ✅ DO THIS:
test_file = FileBuilder()\
    .with_name("test.py")\
    .with_language("python")\
    .with_complexity("medium")\
    .build()
Step 4: Use performance-aware testing
python# ❌ DON'T DO THIS:
start_time = time.time()
result = await slow_operation()
duration = time.time() - start_time
assert duration < 1.0

# ✅ DO THIS (PERFORMANCE):
result = await assert_sub_second_async(slow_operation)
# OR with context manager:
with performance_monitor("operation_name"):
    result = await operation()

Step 5: Use async patterns for reliability
python# ❌ DON'T DO THIS:
await asyncio.sleep(1)  # Hope operation completes
result = get_result()

# ✅ DO THIS (ASYNC PATTERNS):
result = await AsyncTestHelper.wait_for_condition(
    lambda: operation_completed(),
    timeout=5.0,
    description="operation completion"
)

Step 6: Use configuration helpers for setup
python# ❌ DON'T DO THIS:
config = {
    "providers": {"redis": {"host": "localhost"}},
    "limits": {"max_file_size": 1000000}
}

# ✅ DO THIS (CONFIG TESTING):
config = ConfigBuilder().with_redis_disabled().build_server_config()
# OR pre-built scenarios:
config = ConfigScenarios.minimal_config()
📝 Refactoring EXISTING Tests
Pattern 1: Replace manual async mocks
python# BEFORE:
async def mock_read_file(*args, **kwargs):
    return {"content": "test"}
mock_handler = AsyncMock(side_effect=mock_read_file)

# AFTER:
from tests.helpers.utils import mock_async
mock_handler = mock_async(return_value={"content": "test"})
Pattern 2: Replace file system operations
python# BEFORE:
import tempfile
import shutil
temp_dir = tempfile.mkdtemp()
try:
    # test code
finally:
    shutil.rmtree(temp_dir)

# AFTER:
from tests.helpers.utils import FixtureHelpers
with FixtureHelpers.temporary_workspace() as workspace:
    # test code
Pattern 3: Replace Redis mocking
python# BEFORE:
mock_redis = Mock()
mock_redis.get = AsyncMock(return_value=b"value")
mock_redis.set = AsyncMock(return_value=True)

# AFTER:
from tests.helpers.mocks import create_mock_redis
mock_redis = create_mock_redis({"key": "value"})
Pattern 4: Replace complex assertions
python# BEFORE:
import json
actual_json = json.loads(response)
expected_json = json.loads(expected)
assert actual_json == expected_json

# AFTER:
from tests.helpers.utils import ValidationHelpers
ValidationHelpers.assert_json_equal(
    response,
    expected,
    ignore_keys=["timestamp", "id"]
)
🎯 Best Practices Guide
1. Test Structure
pythonclass TestFeatureName:
    """Group related tests in classes."""

    @pytest.fixture
    async def setup_data(self):
        """Use fixtures with helpers."""
        server = create_mock_server()
        await server.initialize()

        project = ProjectBuilder()\
            .with_structure({
                "src": {"main.py": "print('hello')"},
                "tests": {}
            })\
            .build()

        return server, project

    @pytest.mark.asyncio
    async def test_specific_behavior(self, setup_data):
        """Test one specific behavior."""
        server, project = setup_data

        # Use async helpers
        await AsyncHelpers.wait_for_condition(
            lambda: server._initialized
        )

        # Use advanced assertions
        AsyncAssertions.assert_completes_within(
            server.handle_tool_call("read_file", {"path": "src/main.py"}),
            timeout=2.0
        )
2. Mock Customization
python# Create base mock
server = create_mock_server()

# Customize specific behavior
async def custom_analyzer(**kwargs):
    return {
        "metrics": {"complexity": 10},
        "issues": ["High complexity detected"],
        "success": True
    }

server.tool_handlers.handlers["smart_analyze"] = custom_analyzer
3. Performance Testing
pythonfrom tests.helpers.utils import PerformanceHelpers
from tests.helpers.assertions import PerformanceAssertions

# Measure performance
result, exec_time = await PerformanceHelpers.measure_async_execution_time(
    server.handle_tool_call,
    "analyze_dependencies",
    {}
)

# Assert performance
PerformanceAssertions.assert_execution_time(
    exec_time,
    max_time=1.0,
    message="Dependency analysis too slow"
)
4. Data Generation
pythonfrom tests.helpers.utils import DataGenerators
from tests.helpers.builders import CodeBuilder

# Generate test data
test_files = {}
for i in range(5):
    filename = f"module_{random_id()}.py"
    test_files[filename] = CodeBuilder()\
        .with_functions(3)\
        .with_classes(2)\
        .with_complexity("medium")\
        .build()

# Create project with generated files
TestPaths.create_project_structure(tmp_path, {"src": test_files})
🔍 Common Patterns
Pattern: Testing Async Operations
python@pytest.mark.asyncio
async def test_concurrent_operations(self):
    """Test concurrent file operations."""
    server = create_mock_server()
    await server.initialize()

    # Run concurrent operations
    operations = [
        lambda: server.handle_tool_call("read_file", {"path": f"file{i}.py"})
        for i in range(10)
    ]

    results = await AsyncHelpers.run_concurrent_operations(
        operations,
        max_concurrent=5
    )

    # Verify all succeeded
    assert all(r[0].text for r in results)
Pattern: Testing with Timeouts
python@pytest.mark.asyncio
async def test_with_timeout(self):
    """Test operation with timeout."""
    async with AsyncHelpers.async_timeout(5.0, "Operation timed out"):
        result = await slow_operation()

    assert result is not None
Pattern: Testing Error Scenarios
python@pytest.mark.asyncio
async def test_error_handling(self):
    """Test error scenarios with helpers."""
    server = create_mock_server()

    # Test uninitialized error
    await AsyncAssertions.assert_raises_async(
        RuntimeError,
        server.handle_tool_call("read_file", {"path": "test.txt"}),
        match="not initialized"
    )
Pattern: Testing with Mock Data
pythondef test_with_mock_dependencies(self):
    """Test with generated dependency data."""
    deps = DataGenerators.generate_dependency_data()

    # deps contains realistic package data
    for package, info in deps.items():
        assert "version" in info
        assert "latest" in info
        assert info["homepage"].startswith("https://")
📋 Checklist for Test Reviews
When reviewing or writing tests, ensure:

 Using helper imports instead of stdlib directly
 Using mock factories instead of manual Mock() creation
 Using builders for test data instead of hardcoded strings
 Using advanced assertions for better error messages
 Using async helpers for async operations
 Using validation helpers for complex comparisons
 Using performance helpers when testing performance
 Using fixture helpers for test setup

🚀 Quick Reference
Most Used Imports
python# For 90% of tests, start with:
from tests.helpers.utils import (
    TestPaths, AsyncHelpers, mock_async, wait_for
)
from tests.helpers.mocks import (
    create_mock_server, create_mock_redis, create_mock_context_manager
)
from tests.helpers.assertions import AsyncAssertions, FileAssertions
from tests.helpers.builders import FileBuilder, ProjectBuilder
Common Operations
python# Create mock server
server = create_mock_server()
await server.initialize()

# Create test project
project = ProjectBuilder().with_files({
    "main.py": "print('hello')"
}).build()

# Wait for condition
await wait_for(lambda: condition_is_true())

# Assert async operation completes
await AsyncAssertions.assert_completes_within(
    async_operation(), timeout=5.0
)

# Create mock with async return
mock = mock_async(return_value={"status": "ok"})
🎓 Guidelines for Specific Scenarios
Testing File Operations
Always use FileBuilder and TestPaths:
python# Create test files
test_file = FileBuilder()\
    .with_name("test.py")\
    .with_size(1024)\
    .build()

# Create project structure
TestPaths.create_project_structure(tmp_path, {
    "src": {"main.py": test_file["content"]}
})
Testing Redis Operations
Always use create_mock_redis:
pythonredis = create_mock_redis({
    "key1": "value1",
    "hash:field": {"nested": "data"}
})
Testing Context Manager
Always use create_mock_context_manager:
pythoncontext = create_mock_context_manager()
context.context_data["custom"] = "value"
Testing Performance
Always use performance helpers:
pythonPerformanceHelpers.assert_performance(
    function_to_test,
    max_time=1.0,
    iterations=3
)
❌ Anti-Patterns to Avoid

Don't create ad-hoc mocks - Use the mock factories
Don't use time.sleep - Use AsyncHelpers.wait_for_condition
Don't hardcode test data - Use builders and generators
Don't use basic assertions - Use advanced assertions
Don't manage temp files manually - Use TestPaths helpers
Don't write complex async coordination - Use AsyncHelpers

📚 Remember

Helpers make tests more readable and maintainable
Consistent patterns make tests easier to understand
Better assertions provide clearer failure messages
Mock factories ensure consistent behavior
Builders make test data creation flexible

Always check tests/helpers/ for existing utilities before creating new ones!
