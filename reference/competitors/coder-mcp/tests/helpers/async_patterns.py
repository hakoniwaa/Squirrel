"""
Async testing patterns and utilities for coder-mcp tests.

This module provides specialized async testing utilities that make async tests
faster, more reliable, and easier to write.
"""

import asyncio
import functools
import time
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, TypeVar, Union
from unittest.mock import AsyncMock

import pytest

T = TypeVar("T")


class AsyncTestHelper:
    """Comprehensive async testing utilities."""

    @staticmethod
    async def run_with_timeout(
        coro: Awaitable[T], timeout: float = 5.0, error_msg: str = None
    ) -> T:
        """Run coroutine with timeout and clear error messages."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise AssertionError(error_msg or f"Operation timed out after {timeout}s")

    @staticmethod
    async def run_concurrently(
        operations: List[Callable[[], Awaitable[Any]]],
        max_concurrent: int = 10,
        timeout: float = 10.0,
    ) -> List[Any]:
        """Run operations concurrently with control over concurrency and timeout."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_semaphore(operation):
            async with semaphore:
                return await operation()

        tasks = [run_with_semaphore(op) for op in operations]

        try:
            return await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), timeout=timeout
            )
        except asyncio.TimeoutError:
            # Cancel all tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            raise AssertionError(f"Concurrent operations timed out after {timeout}s")

    @staticmethod
    async def wait_for_condition(
        condition: Callable[[], Union[bool, Awaitable[bool]]],
        timeout: float = 5.0,
        check_interval: float = 0.1,
        description: str = "condition",
    ) -> bool:
        """Wait for a condition to become true with exponential backoff."""
        start_time = time.time()
        current_interval = check_interval

        while time.time() - start_time < timeout:
            try:
                if asyncio.iscoroutinefunction(condition):
                    result = await condition()
                else:
                    result = condition()

                if result:
                    return True

            except Exception:
                # Log but continue checking
                pass

            await asyncio.sleep(current_interval)
            # Exponential backoff with max interval of 1 second
            current_interval = min(current_interval * 1.2, 1.0)

        raise AssertionError(f"Timeout waiting for {description} after {timeout}s")

    @staticmethod
    async def ensure_async_cleanup(cleanup_funcs: List[Callable[[], Awaitable[None]]]):
        """Ensure all cleanup functions run, even if some fail."""
        errors = []

        for cleanup_func in cleanup_funcs:
            try:
                await cleanup_func()
            except Exception as e:
                errors.append(e)

        if errors:
            raise AssertionError(f"Cleanup errors: {errors}")


class AsyncMockManager:
    """Advanced async mock management."""

    def __init__(self):
        self.mocks: Dict[str, AsyncMock] = {}
        self.call_history: List[Tuple[str, tuple, dict]] = []

    def create_async_mock(
        self, name: str, return_value: Any = None, side_effect: Any = None, delay: float = 0.0
    ) -> AsyncMock:
        """Create an async mock with optional delay simulation."""

        async def mock_func(*args, **kwargs):
            # Record call
            self.call_history.append((name, args, kwargs))

            # Simulate delay
            if delay > 0:
                await asyncio.sleep(delay)

            # Handle side effect
            if side_effect:
                if isinstance(side_effect, Exception):
                    raise side_effect
                elif callable(side_effect):
                    result = side_effect(*args, **kwargs)
                    if asyncio.iscoroutine(result):
                        return await result
                    return result
                else:
                    return side_effect

            return return_value

        mock = AsyncMock(side_effect=mock_func)
        self.mocks[name] = mock
        return mock

    def create_failing_mock(self, name: str, exception: Exception) -> AsyncMock:
        """Create a mock that always fails with specified exception."""
        return self.create_async_mock(name, side_effect=exception)

    def create_delayed_mock(self, name: str, delay: float, return_value: Any = None) -> AsyncMock:
        """Create a mock with simulated delay."""
        return self.create_async_mock(name, return_value=return_value, delay=delay)

    def get_call_count(self, name: str) -> int:
        """Get number of times a mock was called."""
        return len([call for call in self.call_history if call[0] == name])

    def get_last_call(self, name: str) -> Optional[Tuple[tuple, dict]]:
        """Get last call arguments for a mock."""
        calls = [call for call in self.call_history if call[0] == name]
        return (calls[-1][1], calls[-1][2]) if calls else None

    def reset_history(self):
        """Reset call history."""
        self.call_history.clear()


class AsyncTestPatterns:
    """Common async test patterns."""

    @staticmethod
    async def test_async_initialization(
        init_func: Callable[[], Awaitable[Any]], timeout: float = 5.0
    ) -> Any:
        """Test async initialization pattern."""
        start_time = time.time()
        result = await AsyncTestHelper.run_with_timeout(
            init_func(), timeout, f"Initialization timeout after {timeout}s"
        )
        duration = time.time() - start_time

        # Assert reasonable initialization time
        assert duration < timeout, f"Initialization too slow: {duration:.2f}s"
        assert result is not None, "Initialization returned None"

        return result

    @staticmethod
    async def test_async_cleanup(
        resource: Any, cleanup_func: Callable[[Any], Awaitable[None]], timeout: float = 5.0
    ):
        """Test async cleanup pattern."""
        await AsyncTestHelper.run_with_timeout(
            cleanup_func(resource), timeout, f"Cleanup timeout after {timeout}s"
        )

    @staticmethod
    async def test_concurrent_safety(
        func: Callable[[], Awaitable[Any]], num_operations: int = 10, max_concurrent: int = 5
    ) -> List[Any]:
        """Test function is safe for concurrent execution."""
        operations = [func for _ in range(num_operations)]

        results = await AsyncTestHelper.run_concurrently(operations, max_concurrent=max_concurrent)

        # Check for exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert not exceptions, f"Concurrent execution failed: {exceptions}"

        return results

    @staticmethod
    async def test_async_retry_pattern(
        func: Callable[[], Awaitable[Any]], max_retries: int = 3, initial_delay: float = 0.1
    ) -> Any:
        """Test async retry pattern."""
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    await asyncio.sleep(initial_delay * (2**attempt))

        raise AssertionError(
            f"Retry pattern failed after {max_retries + 1} attempts: {last_exception}"
        )

    @staticmethod
    async def test_async_context_manager(
        context_manager: Any, operation: Callable[[Any], Awaitable[Any]], timeout: float = 5.0
    ) -> Any:
        """Test async context manager pattern."""
        async with AsyncTestHelper.run_with_timeout(
            context_manager, timeout, "Context manager entry timeout"
        ) as resource:
            return await operation(resource)


class AsyncAssertions:
    """Advanced async assertions."""

    @staticmethod
    async def assert_async_raises(
        exception_type: type, coro: Awaitable[Any], match: str = None, timeout: float = 5.0
    ):
        """Assert async operation raises expected exception."""
        with pytest.raises(exception_type, match=match):
            await asyncio.wait_for(coro, timeout=timeout)

    @staticmethod
    async def assert_completes_quickly(coro: Awaitable[Any], max_duration: float = 1.0) -> Any:
        """Assert async operation completes within time limit."""
        start = time.time()
        result = await coro
        duration = time.time() - start

        assert (
            duration <= max_duration
        ), f"Operation took {duration:.2f}s, expected <= {max_duration}s"
        return result

    @staticmethod
    async def assert_no_pending_tasks():
        """Assert no tasks are left pending after test."""
        # Wait a moment for any pending tasks to surface
        await asyncio.sleep(0.1)

        tasks = [task for task in asyncio.all_tasks() if not task.done()]

        if tasks:
            # Cancel pending tasks
            for task in tasks:
                task.cancel()

            # Give them a chance to cancel
            await asyncio.sleep(0.1)

            still_pending = [task for task in tasks if not task.done()]
            assert not still_pending, f"Pending tasks after test: {still_pending}"

    @staticmethod
    async def assert_async_sequence(
        operations: List[Callable[[], Awaitable[Any]]], expected_results: List[Any] = None
    ) -> List[Any]:
        """Assert sequence of async operations completes successfully."""
        results = []

        for i, operation in enumerate(operations):
            try:
                result = await operation()
                results.append(result)

                if expected_results and i < len(expected_results):
                    assert (
                        result == expected_results[i]
                    ), f"Operation {i} result {result} != expected {expected_results[i]}"

            except Exception as e:
                raise AssertionError(f"Operation {i} failed: {e}")

        return results


class AsyncResourceManager:
    """Manage async resources in tests."""

    def __init__(self):
        self.resources: List[Any] = []
        self.cleanup_funcs: List[Callable[[], Awaitable[None]]] = []

    def add_resource(self, resource: Any, cleanup_func: Callable[[Any], Awaitable[None]] = None):
        """Add a resource with optional cleanup function."""
        self.resources.append(resource)

        if cleanup_func:
            self.cleanup_funcs.append(lambda: cleanup_func(resource))
        elif hasattr(resource, "close") and asyncio.iscoroutinefunction(resource.close):
            self.cleanup_funcs.append(resource.close)
        elif hasattr(resource, "cleanup") and asyncio.iscoroutinefunction(resource.cleanup):
            self.cleanup_funcs.append(resource.cleanup)

    async def cleanup_all(self):
        """Clean up all resources."""
        await AsyncTestHelper.ensure_async_cleanup(self.cleanup_funcs)
        self.resources.clear()
        self.cleanup_funcs.clear()


# Decorators for async test optimization
def async_test_timeout(timeout: float = 10.0):
    """Decorator to add timeout to async tests."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await AsyncTestHelper.run_with_timeout(
                func(*args, **kwargs), timeout, f"Test {func.__name__} timed out after {timeout}s"
            )

        return wrapper

    return decorator


def async_test_with_cleanup(cleanup_funcs: List[Callable[[], Awaitable[None]]]):
    """Decorator to ensure cleanup functions run after test."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            finally:
                await AsyncTestHelper.ensure_async_cleanup(cleanup_funcs)

        return wrapper

    return decorator


def concurrent_test(num_operations: int = 10, max_concurrent: int = 5):
    """Decorator to test function with concurrent execution."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            operations = [lambda: func(*args, **kwargs) for _ in range(num_operations)]

            return await AsyncTestHelper.run_concurrently(operations, max_concurrent=max_concurrent)

        return wrapper

    return decorator


# Context managers for async testing
@asynccontextmanager
async def async_test_context(setup_func: Callable[[], Awaitable[Any]] = None):
    """Async context manager for test setup/teardown."""
    resource = None

    try:
        if setup_func:
            resource = await setup_func()
        yield resource
    finally:
        if resource and hasattr(resource, "close"):
            if asyncio.iscoroutinefunction(resource.close):
                await resource.close()
            else:
                resource.close()


@asynccontextmanager
async def temporary_async_server(server_factory: Callable[[], Awaitable[Any]]):
    """Context manager for temporary async server."""
    server = await server_factory()

    try:
        # Ensure server is initialized
        if hasattr(server, "initialize"):
            await server.initialize()

        yield server
    finally:
        # Cleanup server
        if hasattr(server, "shutdown"):
            await server.shutdown()
        elif hasattr(server, "close"):
            await server.close()


# Pytest fixtures
@pytest.fixture
async def async_helper():
    """Provide async test helper instance."""
    return AsyncTestHelper()


@pytest.fixture
async def async_mock_manager():
    """Provide async mock manager instance."""
    manager = AsyncMockManager()
    yield manager
    manager.reset_history()


@pytest.fixture
async def async_resource_manager():
    """Provide async resource manager with automatic cleanup."""
    manager = AsyncResourceManager()
    yield manager
    await manager.cleanup_all()


@pytest.fixture
async def async_assertions():
    """Provide async assertions instance."""
    return AsyncAssertions()


# Convenience functions
async def create_async_mock_server():
    """Create a mock server for async testing."""
    server = AsyncMock()
    server.initialize = AsyncMock()
    server.shutdown = AsyncMock()
    server.handle_request = AsyncMock(return_value={"status": "ok"})
    server.is_running = AsyncMock(return_value=True)

    return server


async def simulate_async_work(duration: float = 0.1, result: Any = "completed"):
    """Simulate async work with configurable duration."""
    await asyncio.sleep(duration)
    return result


async def simulate_async_failure(delay: float = 0.1, exception: Exception = None):
    """Simulate async operation that fails."""
    await asyncio.sleep(delay)
    raise exception or RuntimeError("Simulated async failure")
