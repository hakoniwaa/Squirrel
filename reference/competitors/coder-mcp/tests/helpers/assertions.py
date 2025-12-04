import math

"""
import math
Custom assertions for more expressive and informative tests.
"""

import ast
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, cast

import pytest


class AsyncAssertions:
    """Assertions for async operations."""

    @staticmethod
    async def assert_completes_within(coro, timeout: float, message: str = ""):
        """Assert that a coroutine completes within specified timeout."""
        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            raise AssertionError(message or f"Coroutine did not complete within {timeout}s")

    @staticmethod
    async def assert_raises_async(expected_exception, coro, match: Optional[str] = None):
        """Assert that an async function raises expected exception."""
        with pytest.raises(expected_exception, match=match):
            await coro

    @staticmethod
    async def assert_concurrent_safe(
        func: Callable, args_list: List[tuple], expected_results: Optional[List[Any]] = None
    ):
        """Assert function is safe for concurrent execution."""
        tasks = [func(*args) for args in args_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check no exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        if exceptions:
            raise AssertionError(f"Concurrent execution failed with exceptions: {exceptions}")

        # Check expected results if provided
        if expected_results is not None:
            assert (
                results == expected_results
            ), f"Concurrent results {results} != expected {expected_results}"

        return results


class CodeAssertions:
    """Assertions for code quality and structure."""

    @staticmethod
    def assert_valid_python(code: str, message: str = ""):
        """Assert that string is valid Python code."""
        try:
            ast.parse(code)
        except SyntaxError as e:
            raise AssertionError(message or f"Invalid Python syntax at line {e.lineno}: {e.msg}")

    @staticmethod
    def assert_follows_pattern(code: str, pattern: str, message: str = ""):
        """Assert code follows a specific pattern."""
        if not re.search(pattern, code, re.MULTILINE | re.DOTALL):
            raise AssertionError(message or f"Code does not match pattern: {pattern}")

    @staticmethod
    def assert_complexity_below(code: str, max_complexity: int, message: str = ""):
        """Assert code complexity is below threshold."""
        # Simple complexity calculation (can be enhanced)
        tree = ast.parse(code)
        complexity = 1

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1

        if complexity > max_complexity:
            raise AssertionError(
                message or f"Code complexity {complexity} exceeds maximum {max_complexity}"
            )

    @staticmethod
    def assert_no_hardcoded_secrets(code: str, message: str = ""):
        """Assert code contains no hardcoded secrets."""
        secret_patterns = [
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'secret[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'password\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
        ]

        for pattern in secret_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                raise AssertionError(
                    message or f"Code contains hardcoded secrets matching pattern: {pattern}"
                )


class FileAssertions:
    """Assertions for file operations."""

    @staticmethod
    def assert_file_exists(path: Union[str, Path], message: str = ""):
        """Assert file exists."""
        path = Path(path)
        if not path.exists():
            raise AssertionError(message or f"File does not exist: {path}")

    @staticmethod
    def assert_file_not_exists(path: Union[str, Path], message: str = ""):
        """Assert file does not exist."""
        path = Path(path)
        if path.exists():
            raise AssertionError(message or f"File should not exist: {path}")

    @staticmethod
    def assert_file_size(
        path: Union[str, Path],
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        message: str = "",
    ):
        """Assert file size is within bounds."""
        path = Path(path)
        size = path.stat().st_size

        if min_size is not None and size < min_size:
            raise AssertionError(message or f"File {path} size {size} < minimum {min_size}")

        if max_size is not None and size > max_size:
            raise AssertionError(message or f"File {path} size {size} > maximum {max_size}")

    @staticmethod
    def assert_file_content_matches(path: Union[str, Path], pattern: str, message: str = ""):
        """Assert file content matches regex pattern."""
        path = Path(path)
        content = path.read_text()

        if not re.search(pattern, content, re.MULTILINE | re.DOTALL):
            raise AssertionError(
                message or f"File {path} content does not match pattern: {pattern}"
            )

    @staticmethod
    def assert_files_equal(
        file1: Union[str, Path],
        file2: Union[str, Path],
        ignore_whitespace: bool = False,
        message: str = "",
    ):
        """Assert two files have identical content."""
        content1 = Path(file1).read_text()
        content2 = Path(file2).read_text()

        if ignore_whitespace:
            content1 = re.sub(r"\s+", " ", content1).strip()
            content2 = re.sub(r"\s+", " ", content2).strip()

        if content1 != content2:
            # Show first difference
            for i, (c1, c2) in enumerate(zip(content1, content2)):
                if c1 != c2:
                    # context = 20
                    # start = max(0, i - context)
                    # end = min(len(content1), i + context)
                    raise AssertionError(message or "Files differ at this position.")

            # Different lengths
            raise AssertionError(message or "Files have different lengths.")


class DataAssertions:
    """Assertions for data structures and values."""

    @staticmethod
    def assert_deep_equal(
        actual: Any, expected: Any, message: str = "", ignore_keys: Optional[List[str]] = None
    ):
        """Deep equality assertion with optional key ignoring."""
        ignore_keys = ignore_keys or []

        def clean_dict(d: dict) -> dict:
            return {k: v for k, v in d.items() if k not in ignore_keys}

        def clean_value(value: Any) -> Any:
            if isinstance(value, dict):
                return clean_dict(value)
            elif isinstance(value, list):
                return [clean_value(item) for item in value]
            return value

        actual_clean = clean_value(actual)
        expected_clean = clean_value(expected)

        if actual_clean != expected_clean:
            import json

            raise AssertionError(
                message
                or f"Deep equality assertion failed:\n"
                f"Actual:   {json.dumps(actual_clean, indent=2)}\n"
                f"Expected: {json.dumps(expected_clean, indent=2)}"
            )

    @staticmethod
    def assert_subset(subset: Dict, superset: Dict, message: str = ""):
        """Assert that subset is contained in superset."""
        for key, value in subset.items():
            if key not in superset:
                raise AssertionError(message or f"Key '{key}' not found in superset")

            if isinstance(value, dict) and isinstance(superset[key], dict):
                DataAssertions.assert_subset(value, superset[key])
            elif superset[key] != value:
                raise AssertionError(
                    message or f"Value mismatch for key '{key}': " f"{value} != {superset[key]}"
                )

    @staticmethod
    def assert_json_schema(data: Union[str, dict], schema: dict, message: str = ""):
        """Assert data matches JSON schema."""
        import jsonschema

        if isinstance(data, str):
            data = json.loads(data)

        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            raise AssertionError(message or f"JSON schema validation failed: {e.message}")

    @staticmethod
    def assert_sorted(
        sequence: List, key: Optional[Callable] = None, reverse: bool = False, message: str = ""
    ):
        """Assert sequence is sorted."""
        sorted_seq = sorted(sequence, key=key, reverse=reverse)

        if sequence != sorted_seq:
            # Find first difference
            for i, (actual, expected) in enumerate(zip(sequence, sorted_seq)):
                if actual != expected:
                    raise AssertionError(message or "Sequence not sorted at this index.")


class PerformanceAssertions:
    """Assertions for performance characteristics."""

    @staticmethod
    def assert_memory_usage(
        func: Callable,
        max_memory_mb: float,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ):
        """Assert function uses less than specified memory."""
        import tracemalloc

        kwargs = kwargs or {}

        tracemalloc.start()
        func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / 1024 / 1024
        if peak_mb > max_memory_mb:
            raise AssertionError(
                f"Peak memory usage {peak_mb:.2f}MB exceeds limit {max_memory_mb}MB"
            )

    @staticmethod
    def assert_time_complexity(
        func: Callable, input_sizes: List[int], max_factor: float = 2.0, complexity: str = "linear"
    ):
        """Assert function has expected time complexity."""
        import time

        times = []
        for size in input_sizes:
            # Generate input of given size
            test_input = list(range(size))

            start = time.perf_counter()
            func(test_input)
            duration = time.perf_counter() - start

            times.append(duration)

        # Check complexity
        if complexity == "linear":
            # Time should grow linearly with input size
            for i in range(1, len(times)):
                size_ratio = input_sizes[i] / input_sizes[i - 1]
                time_ratio = times[i] / times[i - 1]

                if time_ratio > size_ratio * max_factor:
                    raise AssertionError(
                        f"Time complexity appears worse than linear: "
                        f"size increased {size_ratio}x but time increased {time_ratio:.2f}x"
                    )

        elif complexity == "logarithmic":
            # Time should grow logarithmically
            for i in range(1, len(times)):
                size_ratio = input_sizes[i] / input_sizes[i - 1]
                time_ratio = times[i] / times[i - 1]
                log_ratio = math.log(input_sizes[i]) / math.log(input_sizes[i - 1])

                if time_ratio > log_ratio * max_factor:
                    raise AssertionError("Time complexity appears worse than logarithmic")


class SecurityAssertions:
    """Assertions for security requirements."""

    @staticmethod
    def assert_no_sql_injection(query_func: Callable, malicious_inputs: List[str]):
        """Assert function is safe from SQL injection."""
        for malicious_input in malicious_inputs:
            try:
                result = query_func(malicious_input)
                # If we get here, the function handled the input
                # Check that it didn't execute the malicious SQL
                if isinstance(result, str) and any(
                    danger in result.lower() for danger in ["drop table", "delete from", "; --"]
                ):
                    raise AssertionError(
                        "SQL injection vulnerability: malicious input was included in query"
                    )
            except Exception as e:
                # Function should safely handle/reject malicious input
                # but not with a SQL error
                if "sql" in str(e).lower():
                    raise AssertionError(f"SQL injection vulnerability: {e}")

    @staticmethod
    def assert_validates_input(
        func: Callable, invalid_inputs: List[Any], expected_exception: type = ValueError
    ):
        """Assert function properly validates input."""
        for invalid_input in invalid_inputs:
            with pytest.raises(expected_exception):
                func(invalid_input)

    @staticmethod
    def assert_sanitized_output(output: str, dangerous_patterns: Optional[List[str]] = None):
        """Assert output is properly sanitized."""
        dangerous_patterns = dangerous_patterns or [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe",
            r"eval\s*\(",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, output, re.IGNORECASE | re.DOTALL):
                raise AssertionError(f"Output contains dangerous pattern: {pattern}")


# Convenience functions for common assertions
async def assert_async_raises(exception_type, async_func, *args, **kwargs):
    """Assert async function raises expected exception."""
    with pytest.raises(exception_type):
        await async_func(*args, **kwargs)


def assert_eventually(
    condition_func: Callable[[], bool],
    timeout: float = 5.0,
    poll_interval: float = 0.1,
    message: str = "",
):
    """Assert that condition becomes true within timeout."""
    import time

    start = time.time()
    while time.time() - start < timeout:
        if condition_func():
            return
        time.sleep(poll_interval)

    raise AssertionError(message or "Condition did not become true within timeout.")


def assert_recent_timestamp(
    timestamp: Union[datetime, float], max_age_seconds: float = 60.0, message: str = ""
):
    """Assert timestamp is recent."""
    if isinstance(timestamp, float):
        timestamp_dt = datetime.fromtimestamp(timestamp)
    else:
        timestamp_dt = cast(datetime, timestamp)

    age = datetime.now() - timestamp_dt
    if age.total_seconds() > max_age_seconds:
        raise AssertionError(
            message
            or f"Timestamp {timestamp_dt} is too old: {age.total_seconds():.1f}s > "
            f"{max_age_seconds}s"
        )
