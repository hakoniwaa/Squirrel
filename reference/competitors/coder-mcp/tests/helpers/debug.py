"""
Test debugging utilities for easier troubleshooting.
"""

import json
import logging
import pprint
import sys
import time
import traceback
from contextlib import contextmanager
from pathlib import Path
from typing import Any, List, Union

import pytest
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

console = Console()


class TestDebugger:
    """Enhanced debugging utilities for tests."""

    def __init__(self):
        self.console = Console()
        self.snapshots = []
        self.performance_marks = {}

    def snapshot(self, obj: Any, name: str = ""):
        """Take a snapshot of an object's state."""
        snapshot = {
            "name": name,
            "timestamp": time.time(),
            "type": type(obj).__name__,
            "value": self._serialize(obj),
            "stack": traceback.extract_stack()[:-1],
        }
        self.snapshots.append(snapshot)
        return obj

    def _serialize(self, obj: Any) -> Any:
        """Serialize object for snapshot."""
        if isinstance(obj, (dict, list, str, int, float, bool, type(None))):
            return obj
        elif hasattr(obj, "__dict__"):
            return {
                "_type": type(obj).__name__,
                "_attrs": {k: self._serialize(v) for k, v in obj.__dict__.items()},
            }
        else:
            return str(obj)

    def print_snapshots(self):
        """Print all snapshots in a formatted way."""
        table = Table(title="Object Snapshots")
        table.add_column("Time", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Value", style="white")

        for snapshot in self.snapshots:
            table.add_row(
                f"{snapshot['timestamp']:.3f}",
                snapshot["name"],
                snapshot["type"],
                pprint.pformat(snapshot["value"], width=40),
            )

        self.console.print(table)

    def trace_calls(self, func):
        """Decorator to trace function calls during tests."""

        def wrapper(*args, **kwargs):
            self.console.print(f"[yellow]→ Calling {func.__name__}[/yellow]")
            self.console.print(f"  Args: {args}")
            self.console.print(f"  Kwargs: {kwargs}")

            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start
                self.console.print(
                    f"[green]← {func.__name__} returned[/green] (took {duration:.3f}s)"
                )
                self.console.print(f"  Result: {result}")
                return result
            except Exception as e:
                duration = time.perf_counter() - start
                self.console.print(f"[red]✗ {func.__name__} failed[/red] (after {duration:.3f}s)")
                self.console.print(f"  Exception: {e}")
                raise

        return wrapper

    def compare_objects(
        self, obj1: Any, obj2: Any, name1: str = "Object 1", name2: str = "Object 2"
    ):
        """Compare two objects and show differences."""
        from deepdiff import DeepDiff

        diff = DeepDiff(obj1, obj2, verbose_level=2)

        if not diff:
            self.console.print(f"[green]✓ {name1} and {name2} are identical[/green]")
        else:
            self.console.print(f"[red]✗ Differences between {name1} and {name2}:[/red]")
            self.console.print(json.dumps(diff, indent=2))

    @contextmanager
    def time_block(self, name: str):
        """Context manager to time a block of code."""
        self.console.print(f"[cyan]⏱  Starting: {name}[/cyan]")
        start = time.perf_counter()

        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.console.print(f"[cyan]⏱  Completed: {name} in {duration:.3f}s[/cyan]")
            self.performance_marks[name] = duration

    def assert_performance(self, operation: str, max_duration: float):
        """Assert that an operation completed within time limit."""
        if operation not in self.performance_marks:
            raise ValueError(f"No performance mark for operation: {operation}")

        actual = self.performance_marks[operation]
        if actual > max_duration:
            raise AssertionError(
                f"Operation '{operation}' took {actual:.3f}s, "
                f"exceeding limit of {max_duration:.3f}s"
            )


class AsyncDebugger(TestDebugger):
    """Async-aware test debugger."""

    async def trace_async_calls(self, func):
        """Decorator to trace async function calls."""

        async def wrapper(*args, **kwargs):
            self.console.print(f"[yellow]→ Calling async {func.__name__}[/yellow]")
            self.console.print(f"  Args: {args}")
            self.console.print(f"  Kwargs: {kwargs}")

            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start
                self.console.print(
                    f"[green]← {func.__name__} returned[/green] (took {duration:.3f}s)"
                )
                self.console.print(f"  Result: {result}")
                return result
            except Exception as e:
                duration = time.perf_counter() - start
                self.console.print(f"[red]✗ {func.__name__} failed[/red] (after {duration:.3f}s)")
                self.console.print(f"  Exception: {e}")
                raise

        return wrapper


def capture_logs(level=logging.DEBUG):
    """Decorator to capture and display logs during test."""

    def decorator(test_func):
        def wrapper(*args, **kwargs):
            # Create custom handler
            log_capture = []
            handler = logging.Handler()
            handler.emit = lambda record: log_capture.append(record)

            # Add handler to root logger
            root_logger = logging.getLogger()
            old_level = root_logger.level
            root_logger.setLevel(level)
            root_logger.addHandler(handler)

            try:
                result = test_func(*args, **kwargs)

                # Print captured logs
                if log_capture:
                    console.print("\n[yellow]Captured Logs:[/yellow]")
                    for record in log_capture:
                        console.print(f"[{record.levelname}] {record.name}: {record.getMessage()}")

                return result
            finally:
                root_logger.removeHandler(handler)
                root_logger.setLevel(old_level)

        return wrapper

    return decorator


class TestDataInspector:
    """Inspect and visualize test data."""

    @staticmethod
    def print_structure(obj: Any, name: str = "Object"):
        """Print object structure as a tree."""
        tree = Tree(f"[bold]{name}[/bold]")
        TestDataInspector._build_tree(tree, obj)
        console.print(tree)

    @staticmethod
    def _build_tree(tree: Tree, obj: Any, max_depth: int = 5, current_depth: int = 0):
        """Recursively build tree structure."""
        if current_depth >= max_depth:
            tree.add("[dim]... (max depth reached)[/dim]")
            return

        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    branch = tree.add(f"[cyan]{key}[/cyan]: [dim]{type(value).__name__}[/dim]")
                    TestDataInspector._build_tree(branch, value, max_depth, current_depth + 1)
                else:
                    tree.add(f"[cyan]{key}[/cyan]: {value}")

        elif isinstance(obj, list):
            for i, item in enumerate(obj[:10]):  # Limit to first 10 items
                if isinstance(item, (dict, list)):
                    branch = tree.add(f"[{i}]: [dim]{type(item).__name__}[/dim]")
                    TestDataInspector._build_tree(branch, item, max_depth, current_depth + 1)
                else:
                    tree.add(f"[{i}]: {item}")

            if len(obj) > 10:
                tree.add(f"[dim]... and {len(obj) - 10} more items[/dim]")

        else:
            tree.add(str(obj))

    @staticmethod
    def compare_files(file1: Path, file2: Path):
        """Compare two files and show differences."""
        import difflib

        content1 = file1.read_text().splitlines()
        content2 = file2.read_text().splitlines()

        diff = difflib.unified_diff(
            content1, content2, fromfile=str(file1), tofile=str(file2), lineterm=""
        )

        diff_text = "\n".join(diff)
        if diff_text:
            syntax = Syntax(diff_text, "diff", theme="monokai")
            console.print(syntax)
        else:
            console.print("[green]Files are identical[/green]")


def debug_on_exception(func):
    """Decorator that drops into debugger on exception."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            console.print(f"[red]Exception in {func.__name__}: {e}[/red]")
            console.print("[yellow]Dropping into debugger...[/yellow]")

            # Print local variables
            frame = sys._getframe()
            console.print("\n[cyan]Local variables:[/cyan]")
            for name, value in frame.f_locals.items():
                if not name.startswith("_"):
                    console.print(f"  {name} = {repr(value)}")

            # Drop into debugger
            import pdb

            pdb.post_mortem()
            raise

    return wrapper


class MockTracker:
    """Track mock calls and assertions."""

    def __init__(self):
        self.calls = []

    def track(self, mock_obj, method_name: str):
        """Track calls to a mock method."""
        original = getattr(mock_obj, method_name)

        def tracked(*args, **kwargs):
            call_info = {
                "method": method_name,
                "args": args,
                "kwargs": kwargs,
                "timestamp": time.time(),
            }
            self.calls.append(call_info)
            return original(*args, **kwargs)

        setattr(mock_obj, method_name, tracked)

    def print_calls(self):
        """Print all tracked calls."""
        table = Table(title="Mock Calls")
        table.add_column("Time", style="cyan")
        table.add_column("Method", style="green")
        table.add_column("Args", style="yellow")
        table.add_column("Kwargs", style="magenta")

        for call in self.calls:
            table.add_row(
                f"{call['timestamp']:.3f}", call["method"], str(call["args"]), str(call["kwargs"])
            )

        console.print(table)

    def assert_call_order(self, expected_order: List[str]):
        """Assert methods were called in specific order."""
        actual_order = [call["method"] for call in self.calls]

        if actual_order != expected_order:
            console.print("[red]Call order mismatch![/red]")
            console.print(f"Expected: {expected_order}")
            console.print(f"Actual:   {actual_order}")
            raise AssertionError("Mock methods called in wrong order")


# Pytest fixtures for debugging
@pytest.fixture
def debugger():
    """Provide test debugger instance."""
    return TestDebugger()


@pytest.fixture
def async_debugger():
    """Provide async test debugger instance."""
    return AsyncDebugger()


@pytest.fixture
def mock_tracker():
    """Provide mock tracker instance."""
    return MockTracker()


@pytest.fixture
def data_inspector():
    """Provide data inspector instance."""
    return TestDataInspector()


# Custom assertions
class BetterAssertions:
    """Enhanced assertions with better error messages."""

    @staticmethod
    def assert_file_contains(file_path: Path, expected_content: str, message: str = ""):
        """Assert file contains expected content."""
        actual = file_path.read_text()
        if expected_content not in actual:
            console.print(f"[red]File {file_path} does not contain expected content[/red]")
            console.print(f"[yellow]Expected to find:[/yellow]\n{expected_content}")
            console.print(f"[yellow]Actual content:[/yellow]\n{actual[:500]}...")
            raise AssertionError(message or f"File {file_path} missing expected content")

    @staticmethod
    def assert_json_equal(actual: Union[str, dict], expected: Union[str, dict], message: str = ""):
        """Assert JSON equality with formatted diff."""
        if isinstance(actual, str):
            actual = json.loads(actual)
        if isinstance(expected, str):
            expected = json.loads(expected)

        if actual != expected:
            from deepdiff import DeepDiff

            diff = DeepDiff(expected, actual, verbose_level=2)

            console.print("[red]JSON objects are not equal[/red]")
            console.print("[yellow]Differences:[/yellow]")
            console.print(json.dumps(diff, indent=2))
            raise AssertionError(message or "JSON objects differ")

    @staticmethod
    def assert_performance(
        operation_time: float, max_time: float, operation_name: str = "Operation"
    ):
        """Assert operation completed within time limit."""
        if operation_time > max_time:
            console.print("[red]Performance assertion failed[/red]")
            console.print(f"{operation_name} took {operation_time:.3f}s")
            console.print(f"Maximum allowed: {max_time:.3f}s")
            console.print(
                f"Exceeded by: {operation_time - max_time:.3f}s "
                f"({(operation_time/max_time - 1)*100:.1f}%)"
            )
            raise AssertionError(
                f"{operation_name} too slow: {operation_time:.3f}s > {max_time:.3f}s"
            )
