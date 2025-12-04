"""
Test utilities for coder-mcp tests.

This module provides common utility functions and classes used across test suites.
"""

import asyncio
import json
import os
import random
import shutil
import string
import tempfile
import time
import uuid
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Type alias for file tree structure (can contain strings or nested dicts)
FileTree = Dict[str, Union[str, "FileTree"]]


class TestPaths:
    """Utility class for managing test paths and directories."""

    @staticmethod
    def create_test_directory(base_path: Path, name: Optional[str] = None) -> Path:
        """Create a test directory with optional name."""
        if name is None:
            name = f"test_{int(time.time())}_{random.randint(1000, 9999)}"

        test_dir = base_path / name
        test_dir.mkdir(parents=True, exist_ok=True)
        return test_dir

    @staticmethod
    def create_project_structure(base_path: Path, structure: Dict[str, Any]) -> Path:
        """
        Create a project directory structure from a dictionary.

        Example:
            structure = {
                "src": {
                    "__init__.py": "",
                    "main.py": "print('Hello')",
                    "utils": {
                        "__init__.py": "",
                        "helpers.py": "def help(): pass"
                    }
                },
                "tests": {
                    "test_main.py": "def test_main(): pass"
                }
            }
        """

        def create_structure(path: Path, struct: Dict[str, Any]):
            for name, content in struct.items():
                item_path = path / name
                if isinstance(content, dict):
                    # It's a directory
                    item_path.mkdir(parents=True, exist_ok=True)
                    create_structure(item_path, content)
                else:
                    # It's a file
                    item_path.write_text(content)

        create_structure(base_path, structure)
        return base_path

    @staticmethod
    def cleanup_test_directory(path: Path):
        """Safely remove a test directory."""
        # Only remove directories whose name (not full path) starts with "test_"
        if path.exists() and path.name.startswith("test_"):
            shutil.rmtree(path, ignore_errors=True)


class AsyncHelpers:
    """Utilities for async test operations."""

    @staticmethod
    async def wait_for_condition(
        condition_func: Callable,
        timeout: float = 5.0,
        check_interval: float = 0.1,
        error_message: str = "Condition not met within timeout",
    ) -> Any:
        """Wait for a condition to become true."""
        start_time = time.time()
        last_result = None

        while time.time() - start_time < timeout:
            result = (
                await condition_func()
                if asyncio.iscoroutinefunction(condition_func)
                else condition_func()
            )
            if result:
                return result
            last_result = result
            await asyncio.sleep(check_interval)

        raise TimeoutError(f"{error_message}. Last result: {last_result}")

    @staticmethod
    @asynccontextmanager
    async def timeout_context(seconds: float):
        """Context manager for operations with timeout."""

        async def timeout_handler():
            await asyncio.sleep(seconds)
            raise TimeoutError(f"Operation timed out after {seconds} seconds")

        timeout_task = asyncio.create_task(timeout_handler())
        try:
            yield
        finally:
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass

    @staticmethod
    async def run_concurrent_operations(
        operations: List[Callable], max_concurrent: int = 10
    ) -> List[Any]:
        """Run multiple async operations concurrently with a limit."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited_operation(op):
            async with semaphore:
                return await op()

        tasks = [limited_operation(op) for op in operations]
        return await asyncio.gather(*tasks)

    @staticmethod
    @asynccontextmanager
    async def async_timeout(timeout_seconds: float, error_message: str = "Operation timed out"):
        """Async context manager with timeout - simplified implementation."""
        # For now, just yield without actual timeout logic
        # The test is skipped until we can implement this properly
        yield


class MockHelpers:
    """Utilities for creating and managing mocks in tests."""

    @staticmethod
    def create_async_mock(return_value=None, side_effect=None):
        """Create a mock that returns an async function."""

        async def async_func(*args, **kwargs):
            if side_effect:
                if callable(side_effect):
                    result = side_effect(*args, **kwargs)
                    # Don't await if the result is not a coroutine
                    if asyncio.iscoroutine(result):
                        return await result
                    return result
                else:
                    raise side_effect
            return return_value

        mock = Mock()
        mock.side_effect = async_func
        return mock

    @staticmethod
    @contextmanager
    def patch_environment(env_vars: Dict[str, str]):
        """Context manager to temporarily set environment variables."""
        original_env = {}
        for key, value in env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            yield
        finally:
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value

    @staticmethod
    def create_redis_mock(initial_data: Optional[Dict[str, str]] = None):
        """Create a mock Redis client."""
        # Use a dictionary to store data
        data = initial_data.copy() if initial_data else {}

        async def mock_get(key):
            return data.get(key)

        async def mock_set(key, value):
            data[key] = value
            return True

        async def mock_delete(key):
            if key in data:
                del data[key]
                return 1
            return 0

        async def mock_exists(key):
            return key in data

        redis_mock = Mock()
        redis_mock.get = AsyncMock(side_effect=mock_get)
        redis_mock.set = AsyncMock(side_effect=mock_set)
        redis_mock.delete = AsyncMock(side_effect=mock_delete)
        redis_mock.exists = AsyncMock(side_effect=mock_exists)
        redis_mock.flushdb = AsyncMock(return_value=True)
        redis_mock.ping = AsyncMock(return_value=True)
        return redis_mock

    @staticmethod
    @contextmanager
    def mock_env_vars(**env_vars):
        """Context manager for mocking environment variables."""
        # Handle None values by removing keys
        env_changes = {}
        keys_to_remove = []

        for key, value in env_vars.items():
            if value is None:
                keys_to_remove.append(key)
            else:
                env_changes[key] = value

        # Store original values
        original_values = {}
        for key in env_changes:
            original_values[key] = os.environ.get(key)
        for key in keys_to_remove:
            original_values[key] = os.environ.get(key)

        try:
            # Apply changes
            for key, value in env_changes.items():
                os.environ[key] = value
            for key in keys_to_remove:
                if key in os.environ:
                    del os.environ[key]
            yield
        finally:
            # Restore original values
            for key, original_value in original_values.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value


class DataGenerators:
    """Utilities for generating test data."""

    @staticmethod
    def random_string(length: int = 10, charset: Optional[str] = None) -> str:
        """Generate a random string."""
        if charset is None:
            charset = string.ascii_letters + string.digits
        return "".join(random.choice(charset) for _ in range(length))

    @staticmethod
    def random_code_snippet(language: str = "python", lines: int = 3) -> str:
        """Generate a random code snippet for testing."""
        if language == "python":
            snippets = [
                "def hello_world():\n    print('Hello, World!')",
                "class TestClass:\n    def __init__(self):\n        self.value = 42",
                "import math\nresult = math.sqrt(16)",
                "for i in range(10):\n    if i % 2 == 0:\n        print(i)",
                "try:\n    result = 1 / 0\nexcept ZeroDivisionError:\n    pass",
                "def calculate(x, y):\n    return x + y",
            ]
        elif language == "javascript":
            snippets = [
                "function helloWorld() {\n    console.log('Hello, World!');\n}",
                "const multiply = (a, b) => a * b;",
                "class TestClass {\n    constructor() {\n        this.value = 42;\n    }\n}",
                "for (let i = 0; i < 10; i++) {\n    console.log(i);\n}",
            ]
        elif language == "text":
            snippets = [f"Line {i}: Sample text content" for i in range(1, 11)]
        else:
            snippets = ["// Generic code snippet", "var x = 1;", "function test() {}"]

        # Ensure we get exactly the requested number of lines/blocks without duplicates
        if lines <= len(snippets):
            selected = random.sample(snippets, lines)
        else:
            # If we need more lines than available snippets, allow duplicates
            selected = []
            for _ in range(lines):
                selected.append(random.choice(snippets))
        return "\n\n".join(selected)

    @staticmethod
    def generate_file_content(file_type: str, size_kb: int = 1) -> str:
        """Generate file content of specified type and size."""
        target_size = size_kb * 1024
        base_content = {
            "python": "def function():\n    pass\n",
            "javascript": "function test() {\n    return true;\n}\n",
            "text": "Sample text content.\n",
            "json": '{"key": "value"}\n',
        }.get(file_type, "content\n")

        # Repeat content to reach target size
        repeat_count = max(1, target_size // len(base_content))
        return base_content * repeat_count

    @staticmethod
    def generate_file_tree(max_depth: int = 3, max_files_per_dir: int = 5) -> FileTree:
        """Generate a random file tree structure."""

        def create_tree(depth: int) -> FileTree:
            if depth <= 0:
                return {}

            tree = {}
            num_items = random.randint(1, max_files_per_dir)

            for _ in range(num_items):
                if random.choice([True, False]) and depth > 1:
                    # Create directory
                    dir_name = f"dir_{DataGenerators.random_string(5)}"
                    tree[dir_name] = create_tree(depth - 1)
                else:
                    # Create file
                    file_name = f"file_{DataGenerators.random_string(5)}.py"
                    tree[file_name] = DataGenerators.random_code_snippet()  # type: ignore

            return tree  # type: ignore

        return create_tree(max_depth)

    @staticmethod
    def generate_dependency_data() -> Dict[str, Dict[str, str]]:
        """Generate mock dependency data."""
        deps = {}
        for _ in range(random.randint(3, 8)):
            name = f"package-{DataGenerators.random_string(6)}"
            deps[name] = {
                "version": f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                "latest": f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                "description": f"Mock package {name}",
                "homepage": f"https://github.com/mock/{name}",
            }
        return deps


class TimeHelpers:
    """Utilities for time-related testing."""

    @staticmethod
    def freeze_time(target_time: datetime):
        """Mock time to a specific datetime."""
        return patch("time.time", return_value=target_time.timestamp())

    @staticmethod
    def generate_timestamps(
        count: int, start_time: Optional[datetime] = None, interval_minutes: int = 5
    ) -> List[datetime]:
        """Generate a series of timestamps."""
        if start_time is None:
            start_time = datetime.now()

        timestamps = []
        current_time = start_time
        for _ in range(count):
            timestamps.append(current_time)
            current_time += timedelta(minutes=interval_minutes)

        return timestamps


class AssertionHelpers:
    """Custom assertion utilities."""

    @staticmethod
    def assert_json_equal(actual: Union[str, dict], expected: Union[str, dict]):
        """Assert that two JSON objects are equal."""
        if isinstance(actual, str):
            actual = json.loads(actual)
        if isinstance(expected, str):
            expected = json.loads(expected)

        assert actual == expected

    @staticmethod
    def assert_file_contains(file_path: Path, expected_content: str):
        """Assert that a file contains specific content."""
        assert file_path.exists(), f"File {file_path} does not exist"
        content = file_path.read_text()
        assert expected_content in content

    @staticmethod
    def assert_directory_structure(base_path: Path, expected_structure: Dict[str, Any]):
        """Assert that a directory has the expected structure."""

        def check_structure(path: Path, structure: Dict[str, Any]):
            for name, content in structure.items():
                item_path = path / name
                assert item_path.exists(), f"Expected {item_path} to exist"
                if isinstance(content, dict):
                    assert item_path.is_dir(), f"Expected {item_path} to be a directory"
                    check_structure(item_path, content)
                else:
                    assert item_path.is_file(), f"Expected {item_path} to be a file"

        check_structure(base_path, expected_structure)


class PerformanceHelpers:
    """Utilities for performance testing."""

    @staticmethod
    @contextmanager
    def measure_time(name: str = "Operation"):
        """Context manager to measure execution time."""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            print(f"{name} took {end_time - start_time:.4f} seconds")

    @staticmethod
    def measure_execution_time(func: Callable, *args, **kwargs) -> tuple:
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        execution_time = time.perf_counter() - start_time
        return result, execution_time

    @staticmethod
    async def measure_async_execution_time(func: Callable, *args, **kwargs) -> tuple:
        """Measure execution time of an async function."""
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        execution_time = time.perf_counter() - start_time
        return result, execution_time

    @staticmethod
    async def measure_async_operation(
        operation: Callable, iterations: int = 100
    ) -> Dict[str, float]:
        """Measure performance of an async operation over multiple iterations."""
        times = []
        for _ in range(iterations):
            start_time = time.perf_counter()
            if asyncio.iscoroutinefunction(operation):
                await operation()
            else:
                operation()
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        return {
            "min": min(times),
            "max": max(times),
            "avg": sum(times) / len(times),
            "total": sum(times),
        }

    @staticmethod
    def assert_performance(func: Callable, max_time: float, iterations: int = 1, *args, **kwargs):
        """Assert that a function completes within a time limit."""
        # Extract iterations from kwargs if present
        if "iterations" in kwargs:
            iterations = kwargs.pop("iterations")

        total_time = 0
        for _ in range(iterations):
            result, execution_time = PerformanceHelpers.measure_execution_time(
                func, *args, **kwargs
            )
            total_time += execution_time

        avg_time = total_time / iterations
        assert avg_time <= max_time, (
            f"Performance assertion failed: Function took {avg_time:.4f}s average, "
            f"expected <= {max_time}s"
        )


# New utility classes and functions for the missing imports


class FixtureHelpers:
    """Utilities for creating test fixtures."""

    @staticmethod
    def create_temp_git_repo(base_path: Path) -> Path:
        """Create a temporary git repository."""
        repo_path = base_path / "test_repo"
        repo_path.mkdir(exist_ok=True)

        # Create .git directory
        git_dir = repo_path / ".git"
        git_dir.mkdir(exist_ok=True)

        # Create some basic files
        (repo_path / "README.md").write_text("# Test Repository")
        (repo_path / ".gitignore").write_text("*.pyc\n__pycache__/")

        return repo_path

    @staticmethod
    def create_mock_mcp_server_config() -> Dict[str, Any]:
        """Create a mock MCP server configuration."""
        return {
            "server": {"name": "test-mcp-server", "version": "1.0.0"},
            "tools": {"enabled": True, "timeout": 30},
            "workspace": {
                "max_file_size": 1024 * 1024,
                "allowed_extensions": [".py", ".js", ".ts", ".md"],
            },
            "providers": ["filesystem", "git", "redis"],
            "features": ["analysis", "search", "refactoring"],
            "limits": {"max_file_size": 1048576, "max_files": 1000},
        }

    @staticmethod
    @contextmanager
    def temporary_workspace():
        """Create a temporary workspace directory."""
        with tempfile.TemporaryDirectory(prefix="test_workspace_") as temp_dir:
            workspace_path = Path(temp_dir)
            # Create .mcp directory to simulate a proper workspace
            mcp_dir = workspace_path / ".mcp"
            mcp_dir.mkdir(exist_ok=True)
            # Create src and tests directories as expected by tests
            src_dir = workspace_path / "src"
            src_dir.mkdir(exist_ok=True)
            tests_dir = workspace_path / "tests"
            tests_dir.mkdir(exist_ok=True)
            yield workspace_path


class ValidationHelpers:
    """Utilities for validation and assertions."""

    @staticmethod
    def assert_json_equal(
        actual: Union[str, dict],
        expected: Union[str, dict],
        ignore_keys: Optional[List[str]] = None,
    ):
        """Assert that two JSON objects are equal."""
        if isinstance(actual, str):
            actual = json.loads(actual)
        if isinstance(expected, str):
            expected = json.loads(expected)

        # Remove ignored keys if specified
        if ignore_keys:
            if isinstance(actual, dict):
                actual = {k: v for k, v in actual.items() if k not in ignore_keys}
            if isinstance(expected, dict):
                expected = {k: v for k, v in expected.items() if k not in ignore_keys}

        assert actual == expected, f"JSON not equal: {actual} != {expected}"

    @staticmethod
    def assert_datetime_close(
        dt1: datetime, dt2: datetime, max_delta: timedelta = timedelta(seconds=1)
    ):
        """Assert that two datetimes are close to each other."""
        delta = abs((dt1 - dt2).total_seconds())
        max_seconds = max_delta.total_seconds()
        assert delta <= max_seconds, f"Datetimes not close enough: {delta}s > {max_seconds}s"

    @staticmethod
    def assert_in_range(
        value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]
    ):
        """Assert that a value is within a range (inclusive)."""
        assert min_val <= value <= max_val, f"Value {value} not in range [{min_val}, {max_val}]"


class FileAssertions:
    """File-related assertion utilities."""

    @staticmethod
    def assert_file_exists(file_path: Path):
        """Assert that a file exists."""
        assert file_path.exists(), f"File {file_path} does not exist"

    @staticmethod
    def assert_file_not_exists(file_path: Path):
        """Assert that a file does not exist."""
        assert not file_path.exists(), f"File {file_path} should not exist"

    @staticmethod
    def assert_is_file(file_path: Path):
        """Assert that path is a file."""
        assert file_path.is_file(), f"Path {file_path} is not a file"

    @staticmethod
    def assert_is_directory(dir_path: Path):
        """Assert that path is a directory."""
        assert dir_path.is_dir(), f"Path {dir_path} is not a directory"


class ConfigEnvironment:
    """Utility for managing test environment configuration."""

    def __init__(self):
        self._original_env = {}
        self._temp_dirs = []

    def set_env_var(self, key: str, value: str):
        """Set an environment variable, storing original value."""
        if key not in self._original_env:
            self._original_env[key] = os.environ.get(key)
        os.environ[key] = value

    def cleanup(self):
        """Restore original environment variables and clean up temp directories."""
        for key, original_value in self._original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value

        for temp_dir in self._temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)


class FileBuilder:
    """Builder for creating test files."""

    def __init__(self):
        self._name = "test_file.py"
        self._language = "python"
        self._content = ""

    def with_name(self, name: str):
        """Set the file name."""
        self._name = name
        return self

    def with_language(self, language: str):
        """Set the file language."""
        self._language = language
        return self

    def with_content(self, content: str):
        """Set the file content."""
        self._content = content
        return self

    def build(self) -> Dict[str, Any]:
        """Build the file specification."""
        if not self._content:
            self._content = DataGenerators.random_code_snippet(self._language)

        return {"name": self._name, "language": self._language, "content": self._content}


class ProjectBuilder:
    """Builder for creating test projects."""

    def __init__(self):
        self._name = "test_project"
        self._type = "python"
        self._size = "small"

    def with_name(self, name: str):
        """Set the project name."""
        self._name = name
        return self

    def with_type(self, project_type: str):
        """Set the project type."""
        self._type = project_type
        return self

    def with_size(self, size: str):
        """Set the project size."""
        self._size = size
        return self

    def build(self) -> Dict[str, str]:
        """Build the project structure."""
        if self._type == "python":
            files = {
                "main.py": "def main():\n    print('Hello, World!')",
                "utils.py": "def helper():\n    return 42",
                "__init__.py": "",
            }

            if self._size == "medium":
                files.update(
                    {
                        "config.py": "DEBUG = True",
                        "models.py": "class Model:\n    pass",
                    }
                )
            elif self._size == "large":
                files.update(
                    {
                        "config.py": "DEBUG = True",
                        "models.py": "class Model:\n    pass",
                        "views.py": "def view():\n    pass",
                        "controllers.py": "class Controller:\n    pass",
                    }
                )
        else:
            files = {"index.js": "console.log('Hello, World!');"}

        return files


class AsyncAssertions:
    """Async-specific assertion utilities."""

    @staticmethod
    async def assert_completes_within(coro, timeout: float, message: str = "Operation timed out"):
        """Assert that a coroutine completes within a timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise AssertionError(f"{message} (timeout: {timeout}s)")

    @staticmethod
    async def assert_concurrent_safe(
        operations: List[Callable], max_concurrent: int = 10
    ) -> List[Any]:
        """Assert that operations can run concurrently without issues."""
        return await AsyncHelpers.run_concurrent_operations(operations, max_concurrent)


# Convenience functions that are imported directly


def mock_async(return_value=None, side_effect=None):
    """Create an async mock function."""

    async def async_func(*args, **kwargs):
        if side_effect:
            if callable(side_effect):
                result = side_effect(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    return await result
                return result
            else:
                raise side_effect
        return return_value

    return async_func


def random_id(prefix: str = "id") -> str:
    """Generate a random ID."""
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{unique_id}"


async def wait_for(condition: Callable, timeout: float = 5.0, check_interval: float = 0.1) -> Any:
    """Wait for a condition to become true."""
    return await AsyncHelpers.wait_for_condition(condition, timeout, check_interval)


# Pytest fixtures


@pytest.fixture
def temp_test_dir():
    """Provide a temporary test directory."""
    with tempfile.TemporaryDirectory(prefix="test_") as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_async_context():
    """Provide an async mock context."""

    async def setup():
        # Setup code here
        pass

    async def teardown():
        # Teardown code here
        pass

    return {"setup": setup, "teardown": teardown}


# Export commonly used utilities
__all__ = [
    "TestPaths",
    "AsyncHelpers",
    "MockHelpers",
    "DataGenerators",
    "TimeHelpers",
    "AssertionHelpers",
    "PerformanceHelpers",
    "temp_test_dir",
    "mock_async_context",
]
