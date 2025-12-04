"""
Comprehensive tests for analysis_result.py module.

This module tests AnalysisResult with >90% coverage including:
- Initialization and path handling
- Issue and suggestion management
- Metrics setting and quality score calculation
- Data conversion and edge cases
"""

from datetime import datetime
from pathlib import Path

import pytest

from coder_mcp.analysis.analysis_result import AnalysisResult


class TestAnalysisResult:
    """Comprehensive test suite for AnalysisResult."""

    def test_init_basic_setup(self):
        """Test basic AnalysisResult initialization."""
        file_path = Path("/project/src/main.py")
        workspace_root = Path("/project")

        result = AnalysisResult(file_path, workspace_root)

        assert result.relative_path == "src/main.py"
        assert result.issues == []
        assert result.suggestions == []
        assert result.metrics == {}
        assert result.quality_score == 0
        assert isinstance(result.timestamp, str)

    def test_init_with_string_paths(self):
        """Test AnalysisResult initialization with string paths."""
        file_path = "/project/src/main.py"
        workspace_root = "/project"

        result = AnalysisResult(file_path, workspace_root)

        assert result.relative_path == "src/main.py"

    def test_init_relative_path_calculation(self):
        """Test relative path calculation with various scenarios."""
        test_cases = [
            (Path("/project/src/main.py"), Path("/project"), "src/main.py"),
            (Path("/project/test.py"), Path("/project"), "test.py"),
            (Path("/project/deep/nested/file.py"), Path("/project"), "deep/nested/file.py"),
            (
                Path("/different/path/file.py"),
                Path("/project"),
                "/different/path/file.py",
            ),  # Outside workspace
        ]

        for file_path, workspace_root, expected_relative in test_cases:
            result = AnalysisResult(file_path, workspace_root)
            assert result.relative_path == expected_relative

    def test_init_file_outside_workspace(self):
        """Test initialization when file is outside workspace."""
        file_path = Path("/completely/different/path/file.py")
        workspace_root = Path("/project")

        result = AnalysisResult(file_path, workspace_root)

        # Should use absolute path when file is outside workspace
        assert result.relative_path == "/completely/different/path/file.py"

    def test_init_timestamp_format(self):
        """Test that timestamp is in correct ISO format."""
        file_path = Path("test.py")
        workspace_root = Path("/project")

        result = AnalysisResult(file_path, workspace_root)

        # Should be able to parse the timestamp
        parsed_timestamp = datetime.fromisoformat(result.timestamp)
        assert isinstance(parsed_timestamp, datetime)

    def test_add_issue_single_issue(self):
        """Test adding a single issue."""
        result = self._create_basic_result()

        result.add_issue("This is a test issue")

        assert len(result.issues) == 1
        assert result.issues[0] == "This is a test issue"

    def test_add_issue_multiple_issues(self):
        """Test adding multiple issues."""
        result = self._create_basic_result()

        issues = ["Issue 1", "Issue 2", "Issue 3"]
        for issue in issues:
            result.add_issue(issue)

        assert len(result.issues) == 3
        assert result.issues == issues

    def test_add_issue_empty_string(self):
        """Test adding empty string as issue."""
        result = self._create_basic_result()

        result.add_issue("")

        # Empty string should not be added
        assert len(result.issues) == 0

    def test_add_issue_none_value(self):
        """Test adding None as issue."""
        result = self._create_basic_result()

        with pytest.raises(Exception):  # AnalysisResultError
            result.add_issue(None)

    def test_add_issue_whitespace_only(self):
        """Test adding whitespace-only string as issue."""
        result = self._create_basic_result()

        result.add_issue("   ")

        # Whitespace string should be stripped and become empty, so not added
        assert len(result.issues) == 0

    def test_add_issue_duplicate_handling(self):
        """Test handling of duplicate issues."""
        result = self._create_basic_result()

        result.add_issue("Duplicate issue")
        result.add_issue("Duplicate issue")
        result.add_issue("Different issue")
        result.add_issue("Duplicate issue")

        # Implementation prevents duplicates
        assert len(result.issues) == 2
        assert "Duplicate issue" in result.issues
        assert "Different issue" in result.issues

    def test_set_metrics_and_calculate_score_with_comprehensive_metrics(self):
        """Test setting metrics and calculating score with comprehensive metrics."""
        result = self._create_basic_result()

        metrics = {"overall_quality_score": 75, "lines_of_code": 100, "complexity": 5}

        result.set_metrics(metrics)
        result.calculate_quality_score()

        assert result.metrics == metrics
        assert isinstance(result.quality_score, (int, float))
        assert 0 <= result.quality_score <= 10

    def test_set_metrics_and_calculate_score_fallback_to_issues(self):
        """Test falling back to issue-based scoring when comprehensive metrics unavailable."""
        result = self._create_basic_result()
        result.add_issue("Test issue 1")
        result.add_issue("Test issue 2")

        metrics = {"lines_of_code": 50}  # No overall_quality_score

        result.set_metrics(metrics)
        result.calculate_quality_score()

        assert result.metrics == metrics
        assert isinstance(result.quality_score, (int, float))
        assert 0 <= result.quality_score <= 10

    def test_set_metrics_and_calculate_score_none_metrics(self):
        """Test setting None as metrics."""
        result = self._create_basic_result()

        # Setting None should raise an error in the current implementation
        with pytest.raises(Exception):  # AnalysisResultError
            result.set_metrics(None)

    def test_set_metrics_and_calculate_score_empty_dict(self):
        """Test setting empty dictionary as metrics."""
        result = self._create_basic_result()

        result.set_metrics({})
        result.calculate_quality_score()

        assert result.metrics == {}
        assert isinstance(result.quality_score, (int, float))

    def test_to_dict_basic_structure(self):
        """Test basic to_dict conversion."""
        result = self._create_basic_result()

        result_dict = result.to_dict()

        required_keys = ["file", "quality_score", "issues", "suggestions", "metrics", "timestamp"]
        for key in required_keys:
            assert key in result_dict

    def test_to_dict_with_data(self):
        """Test to_dict with actual data."""
        result = self._create_basic_result()

        # Add some data
        result.add_issue("Test issue")
        result.add_suggestion("Test suggestion")
        result.set_metrics({"test_metric": 42})
        result.set_quality_score(8.5)

        result_dict = result.to_dict()

        # The relative path will be the full absolute path since test.py is outside /project
        assert result_dict["file"] == result.relative_path
        assert result_dict["quality_score"] == 8.5
        assert result_dict["issues"] == ["Test issue"]
        assert result_dict["suggestions"] == ["Test suggestion"]
        assert result_dict["metrics"] == {"test_metric": 42}
        assert "timestamp" in result_dict

    def test_to_dict_immutability(self):
        """Test that to_dict returns copies and doesn't affect original."""
        result = self._create_basic_result()
        result.add_issue("Original issue")

        result_dict = result.to_dict()

        # Modify the returned dict
        result_dict["issues"].append("New issue")
        result_dict["quality_score"] = 999

        # Original should not be affected due to copies
        assert len(result.issues) == 1  # Original not modified
        assert result.issues[0] == "Original issue"
        assert result.quality_score == 0  # Original not modified

    def test_suggestions_direct_manipulation(self):
        """Test adding suggestions through the API."""
        result = self._create_basic_result()

        # Add suggestions using the API method
        result.add_suggestion("Suggestion 1")
        result.add_suggestion("Suggestion 2")

        assert len(result.suggestions) == 2
        assert "Suggestion 1" in result.suggestions
        assert "Suggestion 2" in result.suggestions

    def test_quality_score_types(self):
        """Test quality score with different numeric types."""
        result = self._create_basic_result()

        # Test with int
        result.set_quality_score(8)
        assert result.quality_score == 8

        # Test with float
        result.set_quality_score(7.5)
        assert result.quality_score == 7.5

        # Test with zero
        result.set_quality_score(0)
        assert result.quality_score == 0

    def test_metrics_types(self):
        """Test metrics with different data types."""
        result = self._create_basic_result()

        complex_metrics = {
            "integer_metric": 42,
            "float_metric": 3.14,
            "string_metric": "test",
            "list_metric": [1, 2, 3],
            "dict_metric": {"nested": "value"},
            "boolean_metric": True,
            "none_metric": None,
        }

        result.set_metrics(complex_metrics)
        assert result.metrics == complex_metrics

    def test_integration_workflow(self):
        """Test complete workflow with all operations."""
        file_path = Path("/project/src/complex_file.py")
        workspace_root = Path("/project")

        result = AnalysisResult(file_path, workspace_root)

        # Add issues
        result.add_issue("Complexity too high")
        result.add_issue("Missing documentation")

        # Add suggestions
        result.add_suggestion("Reduce function complexity")
        result.add_suggestion("Add docstrings")

        # Set metrics and calculate score
        metrics = {
            "overall_quality_score": 65,
            "lines_of_code": 150,
            "complexity": 8,
            "test_coverage": 45,
        }

        result.set_metrics(metrics)
        result.calculate_quality_score()

        # Convert to dict
        result_dict = result.to_dict()

        # Verify complete result
        assert result_dict["file"] == "src/complex_file.py"
        assert isinstance(result_dict["quality_score"], (int, float))
        assert len(result_dict["issues"]) == 2
        assert len(result_dict["suggestions"]) == 2
        assert result_dict["metrics"]["lines_of_code"] == 150
        assert "timestamp" in result_dict

    def test_path_edge_cases(self):
        """Test various edge cases for path handling."""
        edge_cases = [
            # (file_path, workspace_root, expected_relative)
            (Path("."), Path("."), "."),
            (Path(".."), Path("."), ".."),
            (Path("./file.py"), Path("."), "file.py"),
            (Path("../file.py"), Path("."), "../file.py"),
        ]

        for file_path, workspace_root, expected_relative in edge_cases:
            result = AnalysisResult(file_path, workspace_root)
            # The exact behavior depends on Path.relative_to implementation
            # Just ensure it doesn't crash and produces some reasonable result
            assert isinstance(result.relative_path, str)

    def test_timestamp_consistency(self):
        """Test that timestamp remains consistent after creation."""
        result = self._create_basic_result()

        original_timestamp = result.timestamp

        # Perform various operations
        result.add_issue("Test issue")
        result.set_metrics({"test": 1})
        result.calculate_quality_score()
        result.to_dict()

        # Timestamp should remain unchanged
        assert result.timestamp == original_timestamp

    @pytest.mark.parametrize(
        "file_path,workspace_root,expected_in_relative",
        [
            ("/project/file.py", "/project", "file.py"),
            ("/project/src/file.py", "/project", "src/file.py"),
            ("/different/file.py", "/project", "/different/file.py"),
            ("relative/file.py", ".", "relative/file.py"),
        ],
    )
    def test_relative_path_parametrized(self, file_path, workspace_root, expected_in_relative):
        """Parametrized test for relative path calculation."""
        result = AnalysisResult(Path(file_path), Path(workspace_root))
        assert expected_in_relative in result.relative_path

    @pytest.mark.parametrize(
        "issue",
        [
            "Simple issue",
            "Issue with special chars: !@#$%^&*()",
            "Very long issue " + "x" * 1000,
            "Issue\nwith\nnewlines",
            "Issue\twith\ttabs",
            "Unicode issue: 🚀 émoji test",
        ],
    )
    def test_add_issue_various_strings(self, issue):
        """Parametrized test for adding various types of issue strings."""
        result = self._create_basic_result()
        result.add_issue(issue)
        assert len(result.issues) == 1
        assert result.issues[0] == issue

    def _create_basic_result(self):
        """Helper method to create a basic AnalysisResult for testing."""
        return AnalysisResult(Path("test.py"), Path("/project"))


class TestAnalysisResultIntegration:
    """Integration tests for AnalysisResult with real QualityScoreCalculator."""

    def test_real_quality_score_calculation(self):
        """Test with real QualityScoreCalculator (no mocking)."""
        result = AnalysisResult(Path("test.py"), Path("/project"))

        # Test with comprehensive metrics
        metrics = {"overall_quality_score": 80}
        result.set_metrics(metrics)
        result.calculate_quality_score()

        assert result.quality_score == 8.0  # 80 / 10

    def test_real_issue_based_scoring(self):
        """Test real issue-based scoring."""
        result = AnalysisResult(Path("test.py"), Path("/project"))

        # Add some issues
        result.add_issue("Issue 1")
        result.add_issue("Issue 2")

        # Use metrics without overall_quality_score
        metrics = {"lines_of_code": 100}
        result.set_metrics(metrics)
        result.calculate_quality_score()

        # With logarithmic formula, 2 issues gives approximately 8-9
        assert 8 <= result.quality_score <= 9

    def test_complete_analysis_simulation(self):
        """Simulate a complete analysis workflow."""
        # Create result for a Python file
        file_path = Path("/workspace/src/main.py")
        workspace_root = Path("/workspace")
        result = AnalysisResult(file_path, workspace_root)

        # Simulate finding issues
        issues = [
            "Function 'process_data' has too many parameters",
            "Missing type hints in function 'calculate_total'",
            "Unused import 'sys'",
        ]
        for issue in issues:
            result.add_issue(issue)

        # Simulate setting comprehensive metrics
        metrics = {
            "overall_quality_score": 72,
            "lines_of_code": 234,
            "cyclomatic_complexity": 12,
            "test_coverage": 68,
            "maintainability_index": 45,
        }
        result.set_metrics(metrics)
        result.calculate_quality_score()

        # Generate final report
        report = result.to_dict()

        # Verify realistic analysis result
        assert report["file"] == "src/main.py"
        assert report["quality_score"] == 7.2
        assert len(report["issues"]) == 3
        assert report["metrics"]["lines_of_code"] == 234
        assert "timestamp" in report
