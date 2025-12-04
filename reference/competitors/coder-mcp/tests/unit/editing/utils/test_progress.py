"""
Unit tests for coder_mcp.editing.utils.progress module.
Tests progress tracking and reporting functionality.
"""

import time
from unittest.mock import Mock, patch

import pytest

from coder_mcp.editing.utils.progress import (
    MultiOperationProgress,
    ProgressInfo,
    ProgressReporter,
    ProgressState,
)


class TestProgressState:
    """Test the ProgressState enum."""

    def test_enum_values(self):
        """Test that all expected enum values exist."""
        assert ProgressState.NOT_STARTED.value == "not_started"
        assert ProgressState.IN_PROGRESS.value == "in_progress"
        assert ProgressState.COMPLETED.value == "completed"
        assert ProgressState.FAILED.value == "failed"
        assert ProgressState.CANCELLED.value == "cancelled"

    def test_enum_members(self):
        """Test enum member access."""
        states = list(ProgressState)
        assert len(states) == 5
        assert ProgressState.NOT_STARTED in states


class TestProgressInfo:
    """Test the ProgressInfo dataclass."""

    def test_initialization_defaults(self):
        """Test ProgressInfo initialization with defaults."""
        info = ProgressInfo("test_operation")

        assert info.operation == "test_operation"
        assert info.current == 0
        assert info.total == 0
        assert info.state == ProgressState.NOT_STARTED
        assert info.message == ""
        assert info.end_time is None
        assert isinstance(info.metadata, dict)
        assert len(info.metadata) == 0

    def test_initialization_with_values(self):
        """Test ProgressInfo initialization with custom values."""
        metadata = {"key": "value"}
        info = ProgressInfo(
            operation="custom_op",
            current=5,
            total=10,
            state=ProgressState.IN_PROGRESS,
            message="Processing...",
            metadata=metadata,
        )

        assert info.operation == "custom_op"
        assert info.current == 5
        assert info.total == 10
        assert info.state == ProgressState.IN_PROGRESS
        assert info.message == "Processing..."
        assert info.metadata == metadata

    def test_percentage_calculation(self):
        """Test percentage calculation."""
        # Zero total
        info = ProgressInfo("op", current=0, total=0)
        assert info.percentage == 0.0

        # Normal calculation
        info = ProgressInfo("op", current=25, total=100)
        assert info.percentage == 25.0

        # Completed
        info = ProgressInfo("op", current=100, total=100)
        assert info.percentage == 100.0

        # Over 100% (capped)
        info = ProgressInfo("op", current=150, total=100)
        assert info.percentage == 100.0

    @patch("time.time")
    def test_elapsed_time(self, mock_time):
        """Test elapsed time calculation."""
        # Set up time sequence
        mock_time.side_effect = [1000.0, 1005.0]  # start_time, current_time

        info = ProgressInfo("op")
        assert info.start_time == 1000.0
        assert info.elapsed_time == 5.0

        # With end time
        info.end_time = 1003.0
        assert info.elapsed_time == 3.0

    @patch("time.time")
    def test_estimated_remaining(self, mock_time):
        """Test estimated remaining time calculation."""
        # Set up time sequence - need more values because each call to estimated_remaining
        # calls elapsed_time which calls time.time()
        mock_time.side_effect = [
            1000.0,
            1010.0,
            1010.0,
            1010.0,
            1010.0,
        ]  # start_time, current_time for each call

        # No progress yet
        info = ProgressInfo("op", current=0, total=100)
        assert info.estimated_remaining is None

        # In progress - 20 items in 10 seconds = 2 items/sec
        # 80 remaining / 2 items/sec = 40 seconds
        info = ProgressInfo("op", current=20, total=100, start_time=1000.0)
        assert info.estimated_remaining == pytest.approx(40.0)

        # Completed
        info = ProgressInfo("op", current=100, total=100)
        assert info.estimated_remaining is None

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metadata = {"key": "value", "count": 42}
        info = ProgressInfo(
            operation="test_op",
            current=50,
            total=100,
            state=ProgressState.IN_PROGRESS,
            message="Half way there",
            metadata=metadata,
        )

        result = info.to_dict()

        assert result["operation"] == "test_op"
        assert result["current"] == 50
        assert result["total"] == 100
        assert result["percentage"] == 50.0
        assert result["state"] == "in_progress"
        assert result["message"] == "Half way there"
        assert result["metadata"] == metadata
        assert "elapsed_time" in result
        assert "estimated_remaining" in result


class TestProgressReporter:
    """Test the ProgressReporter class."""

    def test_initialization(self):
        """Test ProgressReporter initialization."""
        # Without callback
        reporter = ProgressReporter()
        assert reporter.callback is None
        assert len(reporter.operations) == 0

        # With callback
        callback = Mock()
        reporter = ProgressReporter(callback)
        assert reporter.callback == callback

    def test_start_operation(self):
        """Test starting a new operation."""
        reporter = ProgressReporter()

        info = reporter.start_operation("op1", "Test Operation", 100, {"type": "test"})

        assert info.operation == "Test Operation"
        assert info.total == 100
        assert info.state == ProgressState.IN_PROGRESS
        assert info.metadata == {"type": "test"}
        assert "op1" in reporter.operations
        assert reporter.operations["op1"] == info

    def test_start_operation_with_callback(self):
        """Test starting operation triggers callback."""
        callback = Mock()
        reporter = ProgressReporter(callback)

        info = reporter.start_operation("op1", "Test", 50)

        callback.assert_called_once_with(info)

    def test_update_progress_increment(self):
        """Test updating progress with increment."""
        callback = Mock()
        reporter = ProgressReporter(callback)

        # Start operation
        reporter.start_operation("op1", "Test", 100)
        callback.reset_mock()

        # Update with increment
        reporter.update_progress("op1", increment=10, message="10% done")

        info = reporter.operations["op1"]
        assert info.current == 10
        assert info.message == "10% done"
        callback.assert_called_once_with(info)

    def test_update_progress_absolute(self):
        """Test updating progress with absolute value."""
        reporter = ProgressReporter()

        reporter.start_operation("op1", "Test", 100)
        reporter.update_progress("op1", current=25)

        info = reporter.operations["op1"]
        assert info.current == 25

    def test_update_progress_unknown_operation(self):
        """Test updating non-existent operation."""
        reporter = ProgressReporter()

        # Should not raise exception
        reporter.update_progress("unknown", increment=1)

        # Operation should not be created
        assert "unknown" not in reporter.operations

    def test_complete_operation(self):
        """Test completing an operation."""
        callback = Mock()
        reporter = ProgressReporter(callback)

        reporter.start_operation("op1", "Test", 100)
        reporter.update_progress("op1", current=100)
        callback.reset_mock()

        reporter.complete_operation("op1", "Success!")

        info = reporter.operations["op1"]
        assert info.state == ProgressState.COMPLETED
        assert info.message == "Success!"
        assert info.current == info.total
        assert info.end_time is not None
        callback.assert_called_once_with(info)

    def test_fail_operation(self):
        """Test failing an operation."""
        reporter = ProgressReporter()

        reporter.start_operation("op1", "Test", 100)
        reporter.fail_operation("op1", "Error occurred")

        info = reporter.operations["op1"]
        assert info.state == ProgressState.FAILED
        assert info.message == "Error occurred"
        assert info.end_time is not None

    def test_cancel_operation(self):
        """Test cancelling an operation."""
        reporter = ProgressReporter()

        reporter.start_operation("op1", "Test", 100)
        reporter.cancel_operation("op1", "User cancelled")

        info = reporter.operations["op1"]
        assert info.state == ProgressState.CANCELLED
        assert info.message == "User cancelled"
        assert info.end_time is not None

    def test_get_operation_info(self):
        """Test retrieving operation info."""
        reporter = ProgressReporter()

        # Non-existent operation
        assert reporter.get_operation_info("unknown") is None

        # Existing operation
        reporter.start_operation("op1", "Test", 100)
        info = reporter.get_operation_info("op1")
        assert info is not None
        assert info.operation == "Test"

    def test_get_all_operations(self):
        """Test retrieving all operations."""
        reporter = ProgressReporter()

        # Empty
        assert reporter.get_all_operations() == {}

        # With operations
        reporter.start_operation("op1", "Test1", 100)
        reporter.start_operation("op2", "Test2", 200)

        all_ops = reporter.get_all_operations()
        assert len(all_ops) == 2
        assert "op1" in all_ops
        assert "op2" in all_ops

    def test_clear_completed(self):
        """Test clearing completed operations."""
        reporter = ProgressReporter()

        # Create mix of operations
        reporter.start_operation("op1", "Test1", 100)
        reporter.start_operation("op2", "Test2", 100)
        reporter.start_operation("op3", "Test3", 100)

        reporter.complete_operation("op1")
        reporter.fail_operation("op2", "Test error")
        # op3 remains in progress

        reporter.clear_completed()

        # Only completed should be removed
        assert "op1" not in reporter.operations
        assert "op2" in reporter.operations  # Failed, not completed
        assert "op3" in reporter.operations  # In progress


class TestMultiOperationProgress:
    """Test the MultiOperationProgress class."""

    def test_initialization(self):
        """Test MultiOperationProgress initialization."""
        callback = Mock()
        multi = MultiOperationProgress(callback)

        assert multi.global_callback == callback
        assert len(multi.reporters) == 0

    def test_create_reporter(self):
        """Test creating a sub-reporter."""
        global_callback = Mock()
        multi = MultiOperationProgress(global_callback)

        reporter = multi.create_reporter("task1")

        assert "task1" in multi.reporters
        assert multi.reporters["task1"] == reporter

        # Test that operations trigger global callback
        reporter.start_operation("op1", "Test", 100)
        global_callback.assert_called_once()

    def test_get_reporter(self):
        """Test getting existing reporter."""
        multi = MultiOperationProgress()

        # Non-existent
        assert multi.get_reporter("unknown") is None

        # Existing
        reporter = multi.create_reporter("task1")
        assert multi.get_reporter("task1") == reporter

    def test_get_all_progress(self):
        """Test getting progress from all reporters."""
        multi = MultiOperationProgress()

        # Create reporters with operations
        reporter1 = multi.create_reporter("task1")
        reporter1.start_operation("op1", "Op1", 100)
        reporter1.update_progress("op1", current=50)

        reporter2 = multi.create_reporter("task2")
        reporter2.start_operation("op2", "Op2", 200)
        reporter2.update_progress("op2", current=100)

        all_progress = multi.get_all_progress()

        assert len(all_progress) == 2
        assert "task1.op1" in all_progress
        assert "task2.op2" in all_progress
        assert all_progress["task1.op1"]["current"] == 50
        assert all_progress["task2.op2"]["current"] == 100

    def test_callback_wrapping(self):
        """Test that callbacks are properly wrapped."""
        global_callback = Mock()
        multi = MultiOperationProgress(global_callback)

        reporter = multi.create_reporter("task1")
        info = reporter.start_operation("op1", "Test", 100)

        # Global callback should be called with the ProgressInfo
        global_callback.assert_called_once_with(info)


class TestProgressUsageScenarios:
    """Test realistic usage scenarios."""

    def test_file_processing_scenario(self):
        """Test progress tracking for file processing."""
        callback_calls = []

        def track_progress(info: ProgressInfo):
            callback_calls.append(
                {
                    "operation": info.operation,
                    "percentage": info.percentage,
                    "state": info.state.value,
                }
            )

        reporter = ProgressReporter(track_progress)

        # Start processing files
        reporter.start_operation("file_process", "Processing files", 3)

        # Process each file
        for i in range(3):
            reporter.update_progress("file_process", increment=1, message=f"Processing file {i+1}")
            time.sleep(0.01)  # Simulate work

        # Complete
        reporter.complete_operation("file_process", "All files processed")

        # Verify callbacks
        assert len(callback_calls) >= 4  # start + 3 updates + complete
        assert callback_calls[0]["state"] == "in_progress"
        assert callback_calls[-1]["state"] == "completed"
        assert callback_calls[-1]["percentage"] == 100.0

    def test_multi_stage_operation(self):
        """Test multi-stage operation with sub-progress."""
        multi = MultiOperationProgress()

        # Stage 1: Download
        download_reporter = multi.create_reporter("download")
        download_reporter.start_operation("download_files", "Downloading", 10)

        # Stage 2: Process
        process_reporter = multi.create_reporter("process")
        process_reporter.start_operation("process_files", "Processing", 10)

        # Simulate progress
        for i in range(10):
            download_reporter.update_progress("download_files", increment=1)
            if i >= 5:  # Start processing after half downloaded
                process_reporter.update_progress("process_files", increment=1)

        # Complete stages
        download_reporter.complete_operation("download_files")
        process_reporter.complete_operation("process_files")

        # Check overall progress
        all_progress = multi.get_all_progress()
        assert all_progress["download.download_files"]["state"] == "completed"
        assert all_progress["process.process_files"]["state"] == "completed"

    def test_error_handling_scenario(self):
        """Test progress tracking with error handling."""
        reporter = ProgressReporter()

        # Start operation
        reporter.start_operation("risky_op", "Risky operation", 100)

        try:
            # Simulate work
            for i in range(50):
                reporter.update_progress("risky_op", increment=1)
                if i == 30:
                    raise Exception("Something went wrong!")
        except Exception as e:
            reporter.fail_operation("risky_op", str(e))

        info = reporter.get_operation_info("risky_op")
        assert info.state == ProgressState.FAILED
        assert info.current == 31  # Failed after 30 iterations
        assert "Something went wrong!" in info.message

    @patch("time.time")
    def test_time_estimation_accuracy(self, mock_time):
        """Test time estimation becomes more accurate over time."""
        # Simulate consistent processing rate
        # Use a function that returns time based on current progress
        current_item = [0]  # Use list to allow modification in nested function

        def time_func():
            # Return time that simulates 0.1 seconds per item processed
            # Start time is 1000.0, then add 0.1 for each item
            return 1000.0 + current_item[0] * 0.1

        mock_time.side_effect = time_func

        reporter = ProgressReporter()
        info = reporter.start_operation("timed_op", "Timed operation", 100)

        estimates = []

        # Process items and track estimates
        for i in range(1, 51):  # Process half
            current_item[0] = i  # Update current item for time calculation
            reporter.update_progress("timed_op", current=i)
            if info.estimated_remaining is not None:
                estimates.append(info.estimated_remaining)

        # Estimates should converge to ~5 seconds (50 items * 0.1 sec/item)
        if estimates:
            assert estimates[-1] == pytest.approx(5.0, rel=0.1)
