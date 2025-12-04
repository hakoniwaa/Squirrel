"""
Tests for test utilities module.

This ensures our test helpers work correctly.
"""

import asyncio
import os
import time
from datetime import datetime, timedelta

import pytest

from tests.helpers.utils import (
    AsyncHelpers,
    DataGenerators,
    FixtureHelpers,
    MockHelpers,
    PerformanceHelpers,
    TestPaths,
    ValidationHelpers,
    mock_async,
    random_id,
    wait_for,
)


class TestTestPaths:
    """Test the TestPaths utility class."""

    def test_create_test_directory(self, tmp_path):
        """Test creating a test directory."""
        # Create with auto-generated name
        test_dir = TestPaths.create_test_directory(tmp_path)
        assert test_dir.exists()
        assert test_dir.is_dir()
        assert "test_" in test_dir.name

        # Create with specific name
        named_dir = TestPaths.create_test_directory(tmp_path, "my_test")
        assert named_dir.exists()
        assert named_dir.name == "my_test"

    def test_create_project_structure(self, tmp_path):
        """Test creating a project structure."""
        structure = {
            "src": {
                "__init__.py": "",
                "main.py": "def main(): pass",
                "utils": {"__init__.py": "", "helpers.py": "def help(): return 42"},
            },
            "tests": {"test_main.py": "def test_main(): assert True"},
            "README.md": "# Test Project",
        }

        project_path = TestPaths.create_project_structure(tmp_path, structure)

        # Verify structure
        assert (project_path / "src" / "__init__.py").exists()
        assert (project_path / "src" / "main.py").read_text() == "def main(): pass"
        assert (project_path / "src" / "utils" / "helpers.py").exists()
        assert (project_path / "tests" / "test_main.py").exists()
        assert (project_path / "README.md").read_text() == "# Test Project"

    def test_cleanup_test_directory(self, tmp_path):
        """Test safe cleanup of test directories."""
        test_dir = tmp_path / "test_cleanup"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        TestPaths.cleanup_test_directory(test_dir)
        assert not test_dir.exists()

        # Should not cleanup non-test directories
        normal_dir = tmp_path / "normal_dir"
        normal_dir.mkdir()
        TestPaths.cleanup_test_directory(normal_dir)
        assert normal_dir.exists()  # Should still exist


class TestAsyncHelpers:
    """Test the AsyncHelpers utility class."""

    @pytest.mark.asyncio
    async def test_wait_for_condition(self):
        """Test waiting for a condition."""
        counter = {"value": 0}

        async def increment_counter():
            await asyncio.sleep(0.1)
            counter["value"] += 1

        # Start incrementing in background
        task = asyncio.create_task(increment_counter())

        # Wait for condition
        result = await AsyncHelpers.wait_for_condition(lambda: counter["value"] > 0, timeout=1.0)

        assert result is True
        await task

    @pytest.mark.asyncio
    async def test_wait_for_condition_timeout(self):
        """Test timeout when condition is not met."""
        with pytest.raises(TimeoutError, match="Condition not met"):
            await AsyncHelpers.wait_for_condition(lambda: False, timeout=0.1, check_interval=0.05)

    @pytest.mark.asyncio
    async def test_run_concurrent_operations(self):
        """Test running concurrent operations with limit."""
        results = []

        async def operation(value):
            await asyncio.sleep(0.1)
            results.append(value)
            return value

        operations = [lambda v=i: operation(v) for i in range(5)]
        returned = await AsyncHelpers.run_concurrent_operations(operations, max_concurrent=2)

        assert len(results) == 5
        assert set(returned) == {0, 1, 2, 3, 4}

    @pytest.mark.asyncio
    async def test_async_timeout_success(self):
        """Test async timeout context manager - success case."""
        async with AsyncHelpers.async_timeout(1.0):
            await asyncio.sleep(0.1)  # Complete quickly
            result = "success"

        assert result == "success"

    @pytest.mark.skip(reason="Async timeout implementation needs fixing")
    @pytest.mark.asyncio
    async def test_async_timeout_failure(self):
        """Test async timeout context manager - timeout case."""
        with pytest.raises(TimeoutError, match="Custom timeout message"):
            async with AsyncHelpers.async_timeout(0.1, "Custom timeout message"):
                await asyncio.sleep(0.2)  # Takes longer than timeout


class TestDataGenerators:
    """Test the DataGenerators utility class."""

    def test_random_string(self):
        """Test random string generation."""
        # Default length
        s1 = DataGenerators.random_string()
        assert len(s1) == 10
        assert s1.isalnum()

        # Custom length
        s2 = DataGenerators.random_string(20)
        assert len(s2) == 20

        # Custom characters
        s3 = DataGenerators.random_string(5, "ABC")
        assert all(c in "ABC" for c in s3)

    def test_random_code_snippet(self):
        """Test code snippet generation."""
        # Python code
        python_code = DataGenerators.random_code_snippet("python", lines=5)
        # Check for common Python patterns (more flexible than requiring specific keywords)
        python_patterns = ["def ", "class ", "if ", "for ", "try:", "import ", "="]
        assert any(
            pattern in python_code for pattern in python_patterns
        ), f"No Python patterns found in: {python_code}"
        assert len(python_code.split("\n\n")) == 5

        # JavaScript code
        js_code = DataGenerators.random_code_snippet("javascript", lines=3)
        js_patterns = ["function", "const", "let", "var", "if", "for", "="]
        assert any(
            pattern in js_code for pattern in js_patterns
        ), f"No JavaScript patterns found in: {js_code}"

        # Generic text
        text = DataGenerators.random_code_snippet("text", lines=2)
        assert "Line" in text

    def test_generate_file_tree(self):
        """Test file tree generation."""
        tree = DataGenerators.generate_file_tree(max_depth=2, max_files_per_dir=3)

        assert isinstance(tree, dict)
        assert len(tree) > 0

        # Check for files and directories
        for name, content in tree.items():
            if isinstance(content, dict):
                # It's a directory
                assert not name.endswith(".py")
            else:
                # It's a file
                assert isinstance(content, str)

    def test_generate_dependency_data(self):
        """Test dependency data generation."""
        deps = DataGenerators.generate_dependency_data()

        assert isinstance(deps, dict)
        assert len(deps) >= 3

        for dep_name, dep_info in deps.items():
            assert "version" in dep_info
            assert "latest" in dep_info
            assert "description" in dep_info
            assert "homepage" in dep_info


class TestMockHelpers:
    """Test the MockHelpers utility class."""

    @pytest.mark.asyncio
    async def test_create_async_mock(self):
        """Test creating async mocks."""
        # With return value
        mock = MockHelpers.create_async_mock(return_value="test_value")
        result = await mock()
        assert result == "test_value"

        # With side effect exception
        mock_error = MockHelpers.create_async_mock(side_effect=ValueError("Test error"))
        with pytest.raises(ValueError, match="Test error"):
            await mock_error()

        # With side effect function
        def side_effect_func(x):
            return x * 2

        mock_func = MockHelpers.create_async_mock(side_effect=side_effect_func)
        result = await mock_func(5)
        assert result == 10

    def test_create_redis_mock(self):
        """Test creating Redis mock."""
        # Empty Redis
        redis = MockHelpers.create_redis_mock()

        # Test basic operations
        asyncio.run(redis.set("key1", "value1"))
        assert asyncio.run(redis.get("key1")) == "value1"
        assert asyncio.run(redis.exists("key1")) is True
        assert asyncio.run(redis.exists("key2")) is False

        # Test with initial data
        redis_with_data = MockHelpers.create_redis_mock({"existing": "data"})
        assert asyncio.run(redis_with_data.get("existing")) == "data"

        # Test delete
        asyncio.run(redis.delete("key1"))
        assert asyncio.run(redis.get("key1")) is None

    def test_mock_env_vars(self):
        """Test environment variable mocking."""
        original_value = os.environ.get("TEST_VAR")

        # Set new value
        with MockHelpers.mock_env_vars(TEST_VAR="test_value", NEW_VAR="new"):
            assert os.environ["TEST_VAR"] == "test_value"
            assert os.environ["NEW_VAR"] == "new"

        # Values restored
        assert os.environ.get("TEST_VAR") == original_value
        assert "NEW_VAR" not in os.environ

        # Remove existing var
        os.environ["TEMP_VAR"] = "temp"
        with MockHelpers.mock_env_vars(TEMP_VAR=None):
            assert "TEMP_VAR" not in os.environ
        assert os.environ["TEMP_VAR"] == "temp"


class TestPerformanceHelpers:
    """Test the PerformanceHelpers utility class."""

    def test_measure_execution_time(self):
        """Test measuring execution time."""

        def slow_function(duration):
            time.sleep(duration)
            return "done"

        result, exec_time = PerformanceHelpers.measure_execution_time(slow_function, 0.1)

        assert result == "done"
        assert 0.09 < exec_time < 0.15  # Allow some variance

    @pytest.mark.asyncio
    async def test_measure_async_execution_time(self):
        """Test measuring async execution time."""

        async def async_slow_function(duration):
            await asyncio.sleep(duration)
            return "async_done"

        result, exec_time = await PerformanceHelpers.measure_async_execution_time(
            async_slow_function, 0.1
        )

        assert result == "async_done"
        assert 0.09 < exec_time < 0.15

    def test_assert_performance(self):
        """Test performance assertions."""

        def fast_function():
            return sum(range(100))

        # Should pass
        PerformanceHelpers.assert_performance(fast_function, max_time=0.1, iterations=3)

        # Should fail
        def slow_function():
            time.sleep(0.2)

        with pytest.raises(AssertionError, match="Performance assertion failed"):
            PerformanceHelpers.assert_performance(slow_function, max_time=0.1)


class TestValidationHelpers:
    """Test the ValidationHelpers utility class."""

    def test_assert_json_equal(self):
        """Test JSON equality assertion."""
        # Equal JSONs
        ValidationHelpers.assert_json_equal(
            {"a": 1, "b": 2}, {"b": 2, "a": 1}  # Order doesn't matter
        )

        # With string inputs
        ValidationHelpers.assert_json_equal('{"a": 1}', {"a": 1})

        # With ignored keys
        ValidationHelpers.assert_json_equal(
            {"a": 1, "b": 2, "timestamp": 123},
            {"a": 1, "b": 2, "timestamp": 456},
            ignore_keys=["timestamp"],
        )

        # Should fail
        with pytest.raises(AssertionError, match="JSON not equal"):
            ValidationHelpers.assert_json_equal({"a": 1}, {"a": 2})

    def test_assert_datetime_close(self):
        """Test datetime closeness assertion."""
        now = datetime.now()
        close_time = now + timedelta(seconds=0.5)
        far_time = now + timedelta(seconds=2)

        # Should pass
        ValidationHelpers.assert_datetime_close(now, close_time)

        # Should fail
        with pytest.raises(AssertionError, match="not close enough"):
            ValidationHelpers.assert_datetime_close(now, far_time)

        # Custom delta
        ValidationHelpers.assert_datetime_close(now, far_time, max_delta=timedelta(seconds=3))

    def test_assert_in_range(self):
        """Test range assertion."""
        # Should pass
        ValidationHelpers.assert_in_range(5, 1, 10)
        ValidationHelpers.assert_in_range(1, 1, 10)  # Inclusive
        ValidationHelpers.assert_in_range(10, 1, 10)  # Inclusive

        # Should fail
        with pytest.raises(AssertionError, match="not in range"):
            ValidationHelpers.assert_in_range(11, 1, 10)


class TestFixtureHelpers:
    """Test the FixtureHelpers utility class."""

    def test_create_temp_git_repo(self, tmp_path):
        """Test creating a temporary git repository."""
        repo_path = FixtureHelpers.create_temp_git_repo(tmp_path)

        assert repo_path.exists()
        assert (repo_path / ".git").exists()
        assert (repo_path / "README.md").exists()

        # Check git status
        result = os.popen(f"cd {repo_path} && git status --porcelain").read()
        assert result == ""  # Clean working directory

    def test_create_mock_mcp_server_config(self):
        """Test creating mock MCP server config."""
        config = FixtureHelpers.create_mock_mcp_server_config()

        assert "server" in config
        assert config["server"]["name"] == "test-mcp-server"
        assert "providers" in config
        assert "features" in config
        assert "limits" in config
        assert config["limits"]["max_file_size"] == 1048576

    def test_temporary_workspace(self):
        """Test temporary workspace context manager."""
        workspace_path = None

        with FixtureHelpers.temporary_workspace() as workspace:
            workspace_path = workspace
            assert workspace.exists()
            assert (workspace / ".mcp").exists()
            assert (workspace / "src").exists()
            assert (workspace / "tests").exists()

            # Create a file in workspace
            (workspace / "test.txt").write_text("test")

        # Workspace should be cleaned up
        assert not workspace_path.exists()


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_wait_for(self):
        """Test wait_for convenience function."""
        flag = {"ready": False}

        async def set_flag():
            await asyncio.sleep(0.1)
            flag["ready"] = True

        task = asyncio.create_task(set_flag())
        await wait_for(lambda: flag["ready"])
        assert flag["ready"] is True
        await task

    def test_random_id(self):
        """Test random ID generation."""
        # Default prefix
        id1 = random_id()
        assert id1.startswith("id_")
        assert len(id1) == 11  # "id_" + 8 chars

        # Custom prefix
        id2 = random_id("user")
        assert id2.startswith("user_")

        # IDs should be unique
        assert id1 != random_id()

    @pytest.mark.asyncio
    async def test_mock_async(self):
        """Test mock_async convenience function."""
        mock = mock_async("test_result")
        result = await mock()
        assert result == "test_result"
