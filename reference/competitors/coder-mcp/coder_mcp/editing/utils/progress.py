"""
Progress reporting for long-running edit operations.
Provides callbacks and progress tracking for better user experience.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional


class ProgressState(Enum):
    """States for progress tracking."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProgressInfo:
    """Information about operation progress."""

    operation: str
    current: int = 0
    total: int = 0
    state: ProgressState = ProgressState.NOT_STARTED
    message: str = ""
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set start_time if not provided."""
        if self.start_time is None:
            self.start_time = time.time()

    @property
    def percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total == 0:
            return 0.0
        return min(100.0, (self.current / self.total) * 100)

    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        end = self.end_time or time.time()
        return end - (self.start_time or time.time())

    @property
    def estimated_remaining(self) -> Optional[float]:
        """Estimate remaining time based on current progress."""
        if self.current == 0 or self.percentage >= 100:
            return None

        elapsed = self.elapsed_time
        rate = self.current / elapsed
        remaining_items = self.total - self.current

        return remaining_items / rate if rate > 0 else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "operation": self.operation,
            "current": self.current,
            "total": self.total,
            "percentage": self.percentage,
            "state": self.state.value,
            "message": self.message,
            "elapsed_time": self.elapsed_time,
            "estimated_remaining": self.estimated_remaining,
            "metadata": self.metadata,
        }


# Type alias for progress callbacks
ProgressCallback = Callable[[ProgressInfo], None]


class ProgressReporter:
    """Manages progress reporting for operations."""

    def __init__(self, callback: Optional[ProgressCallback] = None):
        """
        Initialize progress reporter.

        Args:
            callback: Optional callback function for progress updates
        """
        self.callback = callback
        self.operations: Dict[str, ProgressInfo] = {}

    def start_operation(
        self,
        operation_id: str,
        operation_name: str,
        total_items: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProgressInfo:
        """
        Start tracking a new operation.

        Args:
            operation_id: Unique identifier for the operation
            operation_name: Human-readable operation name
            total_items: Total number of items to process
            metadata: Optional metadata for the operation

        Returns:
            ProgressInfo object for the operation
        """
        progress = ProgressInfo(
            operation=operation_name,
            total=total_items,
            state=ProgressState.IN_PROGRESS,
            message=f"Starting {operation_name}...",
            metadata=metadata or {},
        )

        self.operations[operation_id] = progress
        self._report(progress)

        return progress

    def update_progress(
        self,
        operation_id: str,
        current: Optional[int] = None,
        increment: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        """
        Update progress for an operation.

        Args:
            operation_id: Operation identifier
            current: Current item being processed (absolute value)
            increment: Amount to increment current progress by
            message: Optional status message
        """
        if operation_id not in self.operations:
            return

        progress = self.operations[operation_id]

        if current is not None:
            progress.current = current
        elif increment is not None:
            progress.current += increment

        if message:
            progress.message = message
        else:
            progress.message = f"Processing item {progress.current}/{progress.total}"

        self._report(progress)

    def increment_progress(self, operation_id: str, message: Optional[str] = None) -> None:
        """
        Increment progress by one.

        Args:
            operation_id: Operation identifier
            message: Optional status message
        """
        if operation_id not in self.operations:
            return

        progress = self.operations[operation_id]
        self.update_progress(operation_id, current=progress.current + 1, message=message)

    def complete_operation(self, operation_id: str, message: Optional[str] = None) -> None:
        """
        Mark an operation as completed.

        Args:
            operation_id: Operation identifier
            message: Optional completion message
        """
        if operation_id not in self.operations:
            return

        progress = self.operations[operation_id]
        progress.state = ProgressState.COMPLETED
        progress.current = progress.total
        progress.end_time = time.time()
        progress.message = message or f"{progress.operation} completed"

        self._report(progress)

    def fail_operation(self, operation_id: str, error_message: str) -> None:
        """
        Mark an operation as failed.

        Args:
            operation_id: Operation identifier
            error_message: Error message
        """
        if operation_id not in self.operations:
            return

        progress = self.operations[operation_id]
        progress.state = ProgressState.FAILED
        progress.end_time = time.time()
        progress.message = error_message

        self._report(progress)

    def cancel_operation(self, operation_id: str, message: Optional[str] = None) -> None:
        """
        Mark an operation as cancelled.

        Args:
            operation_id: Operation identifier
            message: Optional cancellation message
        """
        if operation_id not in self.operations:
            return

        progress = self.operations[operation_id]
        progress.state = ProgressState.CANCELLED
        progress.end_time = time.time()
        progress.message = message or f"{progress.operation} cancelled"

        self._report(progress)

    def get_progress(self, operation_id: str) -> Optional[ProgressInfo]:
        """Get progress info for an operation."""
        return self.operations.get(operation_id)

    def get_operation_info(self, operation_id: str) -> Optional[ProgressInfo]:
        """Get operation info for an operation (alias for get_progress)."""
        return self.get_progress(operation_id)

    def get_all_operations(self) -> Dict[str, ProgressInfo]:
        """Get all tracked operations."""
        return self.operations.copy()

    def clear_completed(self) -> None:
        """Remove completed operations from tracking."""
        self.operations = {
            op_id: progress
            for op_id, progress in self.operations.items()
            if progress.state != ProgressState.COMPLETED
        }

    def _report(self, progress: ProgressInfo) -> None:
        """Report progress via callback if available."""
        if self.callback:
            self.callback(progress)


class MultiOperationProgress:
    """Manages multiple progress reporters with a global callback."""

    def __init__(self, global_callback: Optional[ProgressCallback] = None):
        """
        Initialize multi-operation progress manager.

        Args:
            global_callback: Optional callback function for all progress updates
        """
        self.global_callback = global_callback
        self.reporters: Dict[str, ProgressReporter] = {}

    def create_reporter(self, task_id: str) -> ProgressReporter:
        """
        Create a new progress reporter for a task.

        Args:
            task_id: Unique identifier for the task

        Returns:
            ProgressReporter instance
        """
        reporter = ProgressReporter(self.global_callback)
        self.reporters[task_id] = reporter
        return reporter

    def get_reporter(self, task_id: str) -> Optional[ProgressReporter]:
        """
        Get an existing progress reporter.

        Args:
            task_id: Task identifier

        Returns:
            ProgressReporter instance or None if not found
        """
        return self.reporters.get(task_id)

    def get_all_progress(self) -> Dict[str, Dict[str, Any]]:
        """
        Get progress from all reporters.

        Returns:
            Dictionary with task.operation keys and progress info values
        """
        all_progress = {}
        for task_id, reporter in self.reporters.items():
            for op_id, progress in reporter.get_all_operations().items():
                key = f"{task_id}.{op_id}"
                all_progress[key] = progress.to_dict()
        return all_progress


class ProgressContext:
    """Context manager for progress tracking."""

    def __init__(
        self, reporter: ProgressReporter, operation_id: str, operation_name: str, total_items: int
    ):
        """
        Initialize progress context.

        Args:
            reporter: ProgressReporter instance
            operation_id: Unique operation identifier
            operation_name: Human-readable operation name
            total_items: Total items to process
        """
        self.reporter = reporter
        self.operation_id = operation_id
        self.operation_name = operation_name
        self.total_items = total_items
        self.progress: Optional[ProgressInfo] = None

    def __enter__(self) -> "ProgressContext":
        """Start progress tracking."""
        self.progress = self.reporter.start_operation(
            self.operation_id, self.operation_name, self.total_items
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete or fail operation based on exception."""
        if exc_type is None:
            self.reporter.complete_operation(self.operation_id)
        else:
            self.reporter.fail_operation(self.operation_id, f"{exc_type.__name__}: {exc_val}")

    def update(self, current: int, message: Optional[str] = None) -> None:
        """Update progress."""
        self.reporter.update_progress(self.operation_id, current=current, message=message)

    def increment(self, message: Optional[str] = None) -> None:
        """Increment progress."""
        self.reporter.increment_progress(self.operation_id, message)


# Example usage functions
def console_progress_callback(progress: ProgressInfo) -> None:
    """Example callback that prints to console."""
    bar_length = 40
    filled = int(bar_length * progress.percentage / 100)
    bar = "█" * filled + "░" * (bar_length - filled)

    print(
        f"\r{progress.operation}: [{bar}] {progress.percentage:.1f}% - {progress.message}", end=""
    )

    if progress.state in [ProgressState.COMPLETED, ProgressState.FAILED, ProgressState.CANCELLED]:
        print()  # New line at end


def create_progress_reporter(verbose: bool = True) -> ProgressReporter:
    """Create a progress reporter with optional console output."""
    callback = console_progress_callback if verbose else None
    return ProgressReporter(callback)
