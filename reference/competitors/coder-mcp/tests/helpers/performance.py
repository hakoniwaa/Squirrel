"""
Performance testing utilities for coder-mcp tests.

This module provides specialized tools for measuring and asserting performance
characteristics, with focus on making performance tests fast and reliable.
"""

import asyncio
import time
import tracemalloc
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import pytest


@dataclass
class PerformanceMetrics:
    """Container for performance measurement results."""

    duration: float
    memory_peak: Optional[int] = None
    memory_current: Optional[int] = None
    iterations: int = 1
    operation_name: str = "unknown"

    @property
    def duration_ms(self) -> float:
        """Duration in milliseconds."""
        return self.duration * 1000

    @property
    def memory_peak_mb(self) -> Optional[float]:
        """Peak memory in MB."""
        return self.memory_peak / 1024 / 1024 if self.memory_peak else None

    @property
    def avg_duration(self) -> float:
        """Average duration per iteration."""
        return self.duration / self.iterations if self.iterations > 0 else 0

    def __str__(self) -> str:
        memory_info = f", Peak Memory: {self.memory_peak_mb:.2f}MB" if self.memory_peak_mb else ""
        return f"Operation: {self.operation_name}, Duration: {self.duration_ms:.2f}ms{memory_info}"


class PerformanceBenchmark:
    """High-performance benchmarking utilities."""

    def __init__(self, name: str = "benchmark"):
        self.name = name
        self.results: List[PerformanceMetrics] = []
        self._warmup_iterations = 3
        self._measure_memory = False

    def with_warmup(self, iterations: int = 3):
        """Set warmup iterations."""
        self._warmup_iterations = iterations
        return self

    def with_memory_tracking(self, enabled: bool = True):
        """Enable memory tracking."""
        self._measure_memory = enabled
        return self

    @contextmanager
    def measure(self, operation_name: str = "operation"):
        """Context manager for measuring a single operation."""
        # Warmup if needed
        if self._warmup_iterations > 0:
            yield  # Run once for warmup, don't measure
            self._warmup_iterations = 0  # Only warmup once

        # Start memory tracking if enabled
        if self._measure_memory:
            tracemalloc.start()

        start_time = time.perf_counter()

        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time

            # Get memory stats
            memory_current, memory_peak = None, None
            if self._measure_memory:
                memory_current, memory_peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

            # Store result
            metrics = PerformanceMetrics(
                duration=duration,
                memory_peak=memory_peak,
                memory_current=memory_current,
                operation_name=operation_name,
            )
            self.results.append(metrics)

    @asynccontextmanager
    async def measure_async(self, operation_name: str = "async_operation"):
        """Async context manager for measuring async operations."""
        # Start memory tracking if enabled
        if self._measure_memory:
            tracemalloc.start()

        start_time = time.perf_counter()

        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time

            # Get memory stats
            memory_current, memory_peak = None, None
            if self._measure_memory:
                memory_current, memory_peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

            # Store result
            metrics = PerformanceMetrics(
                duration=duration,
                memory_peak=memory_peak,
                memory_current=memory_current,
                operation_name=operation_name,
            )
            self.results.append(metrics)

    def benchmark_function(
        self, func: Callable, iterations: int = 10, *args, **kwargs
    ) -> PerformanceMetrics:
        """Benchmark a function with multiple iterations."""
        durations = []
        memory_peaks = []

        # Warmup
        for _ in range(self._warmup_iterations):
            func(*args, **kwargs)

        # Actual benchmarking
        for i in range(iterations):
            if self._measure_memory:
                tracemalloc.start()

            start_time = time.perf_counter()
            func(*args, **kwargs)
            end_time = time.perf_counter()

            durations.append(end_time - start_time)

            if self._measure_memory:
                _, peak = tracemalloc.get_traced_memory()
                memory_peaks.append(peak)
                tracemalloc.stop()

        # Calculate metrics
        avg_duration = sum(durations) / len(durations)
        avg_memory = sum(memory_peaks) / len(memory_peaks) if memory_peaks else None

        metrics = PerformanceMetrics(
            duration=avg_duration,
            memory_peak=int(avg_memory) if avg_memory else None,
            iterations=iterations,
            operation_name=func.__name__,
        )
        self.results.append(metrics)
        return metrics

    async def benchmark_async_function(
        self, func: Callable, iterations: int = 10, *args, **kwargs
    ) -> PerformanceMetrics:
        """Benchmark an async function with multiple iterations."""
        durations = []
        memory_peaks = []

        # Warmup
        for _ in range(self._warmup_iterations):
            await func(*args, **kwargs)

        # Actual benchmarking
        for i in range(iterations):
            if self._measure_memory:
                tracemalloc.start()

            start_time = time.perf_counter()
            await func(*args, **kwargs)
            end_time = time.perf_counter()

            durations.append(end_time - start_time)

            if self._measure_memory:
                _, peak = tracemalloc.get_traced_memory()
                memory_peaks.append(peak)
                tracemalloc.stop()

        # Calculate metrics
        avg_duration = sum(durations) / len(durations)
        avg_memory = sum(memory_peaks) / len(memory_peaks) if memory_peaks else None

        metrics = PerformanceMetrics(
            duration=avg_duration,
            memory_peak=int(avg_memory) if avg_memory else None,
            iterations=iterations,
            operation_name=func.__name__,
        )
        self.results.append(metrics)
        return metrics

    def get_summary(self) -> Dict[str, Any]:
        """Get benchmark summary."""
        if not self.results:
            return {"message": "No benchmark results"}

        return {
            "total_operations": len(self.results),
            "avg_duration_ms": sum(r.duration_ms for r in self.results) / len(self.results),
            "min_duration_ms": min(r.duration_ms for r in self.results),
            "max_duration_ms": max(r.duration_ms for r in self.results),
            "total_duration_ms": sum(r.duration_ms for r in self.results),
            "operations": [str(r) for r in self.results],
        }


class FastPerformanceAsserter:
    """Ultra-fast performance assertions for tests."""

    @staticmethod
    def assert_fast(max_duration_ms: float = 100):
        """Decorator to assert function completes quickly."""

        def decorator(func):
            if asyncio.iscoroutinefunction(func):

                async def async_wrapper(*args, **kwargs):
                    start = time.perf_counter()
                    result = await func(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start) * 1000

                    assert duration_ms <= max_duration_ms, (
                        f"Function {func.__name__} took {duration_ms:.2f}ms, "
                        f"exceeding limit of {max_duration_ms}ms"
                    )
                    return result

                return async_wrapper
            else:

                def sync_wrapper(*args, **kwargs):
                    start = time.perf_counter()
                    result = func(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start) * 1000

                    assert duration_ms <= max_duration_ms, (
                        f"Function {func.__name__} took {duration_ms:.2f}ms, "
                        f"exceeding limit of {max_duration_ms}ms"
                    )
                    return result

                return sync_wrapper

        return decorator

    @staticmethod
    def assert_memory_efficient(max_memory_mb: float = 10):
        """Decorator to assert function uses minimal memory."""

        def decorator(func):
            def wrapper(*args, **kwargs):
                tracemalloc.start()
                result = func(*args, **kwargs)
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                peak_mb = peak / 1024 / 1024
                assert peak_mb <= max_memory_mb, (
                    f"Function {func.__name__} used {peak_mb:.2f}MB, "
                    f"exceeding limit of {max_memory_mb}MB"
                )
                return result

            return wrapper

        return decorator

    @staticmethod
    def assert_scales_linearly(max_factor: float = 2.0):
        """Decorator to assert function scales linearly with input size."""

        def decorator(func):
            def wrapper(*args, **kwargs):
                # This is a simplified linear scaling test
                # In practice, you'd want to test with multiple input sizes
                start = time.perf_counter()
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start

                # Store timing for comparison (simplified)
                if not hasattr(wrapper, "_baseline_time"):
                    wrapper._baseline_time = duration
                else:
                    ratio = duration / wrapper._baseline_time
                    assert (
                        ratio <= max_factor
                    ), f"Function {func.__name__} scaling ratio {ratio:.2f} exceeds {max_factor}"

                return result

            return wrapper

        return decorator


class TestSuiteOptimizer:
    """Optimize entire test suite performance."""

    def __init__(self):
        self.test_times: Dict[str, float] = {}
        self.slow_tests: List[Tuple[str, float]] = []
        self.optimization_suggestions: List[str] = []

    def track_test(self, test_name: str, duration: float):
        """Track individual test performance."""
        self.test_times[test_name] = duration

        # Flag slow tests
        if duration > 1.0:  # > 1 second
            self.slow_tests.append((test_name, duration))
            self.optimization_suggestions.append(
                f"Consider optimizing {test_name} (took {duration:.2f}s)"
            )

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report for test suite."""
        if not self.test_times:
            return {"message": "No test performance data"}

        total_time = sum(self.test_times.values())
        avg_time = total_time / len(self.test_times)

        return {
            "total_tests": len(self.test_times),
            "total_time_seconds": total_time,
            "average_time_seconds": avg_time,
            "slow_tests": self.slow_tests,
            "optimization_suggestions": self.optimization_suggestions,
            "fastest_test": min(self.test_times.items(), key=lambda x: x[1]),
            "slowest_test": max(self.test_times.items(), key=lambda x: x[1]),
        }


# Convenience functions and decorators
def time_function(func: Callable) -> Callable:
    """Simple timing decorator for development."""
    if asyncio.iscoroutinefunction(func):

        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            duration = time.perf_counter() - start
            print(f"⏱  {func.__name__} took {duration*1000:.2f}ms")
            return result

        return async_wrapper
    else:

        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start
            print(f"⏱  {func.__name__} took {duration*1000:.2f}ms")
            return result

        return sync_wrapper


def benchmark_this(iterations: int = 10, warmup: int = 3):
    """Decorator to automatically benchmark a function."""

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            benchmark = PerformanceBenchmark(func.__name__).with_warmup(warmup)

            if asyncio.iscoroutinefunction(func):

                async def run_benchmark():
                    return await benchmark.benchmark_async_function(
                        func, iterations, *args, **kwargs
                    )

                result = asyncio.run(run_benchmark())
            else:
                result = benchmark.benchmark_function(func, iterations, *args, **kwargs)

            print(f"📊 Benchmark result: {result}")
            return func(*args, **kwargs)  # Return actual function result

        return wrapper

    return decorator


@contextmanager
def performance_monitor(operation_name: str = "operation", print_result: bool = True):
    """Simple performance monitoring context manager."""
    start = time.perf_counter()
    tracemalloc.start()

    try:
        yield
    finally:
        duration = time.perf_counter() - start
        _, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        if print_result:
            print(
                f"🔍 {operation_name}: {duration*1000:.2f}ms, "
                f"Peak Memory: {peak_memory/1024/1024:.2f}MB"
            )


# Pytest fixtures
@pytest.fixture
def performance_benchmark():
    """Provide performance benchmark instance."""
    return PerformanceBenchmark()


@pytest.fixture
def performance_asserter():
    """Provide performance asserter instance."""
    return FastPerformanceAsserter()


@pytest.fixture
def test_optimizer():
    """Provide test suite optimizer instance."""
    return TestSuiteOptimizer()


# Special assertions for common performance patterns
def assert_sub_second(func: Callable, *args, **kwargs):
    """Assert function completes in under 1 second."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    duration = time.perf_counter() - start

    assert duration < 1.0, f"Function took {duration:.2f}s, should be < 1.0s"
    return result


async def assert_sub_second_async(func: Callable, *args, **kwargs):
    """Assert async function completes in under 1 second."""
    start = time.perf_counter()
    result = await func(*args, **kwargs)
    duration = time.perf_counter() - start

    assert duration < 1.0, f"Async function took {duration:.2f}s, should be < 1.0s"
    return result


def assert_minimal_memory(func: Callable, max_mb: float = 5.0, *args, **kwargs):
    """Assert function uses minimal memory."""
    tracemalloc.start()
    result = func(*args, **kwargs)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / 1024 / 1024
    assert peak_mb <= max_mb, f"Function used {peak_mb:.2f}MB, should be <= {max_mb}MB"
    return result
