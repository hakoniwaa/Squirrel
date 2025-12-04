"""
Comprehensive tests for AnalysisResult module.

This module provides complete test coverage for the AnalysisResult class,
matching the actual API implementation.
"""

import pytest

from coder_mcp.analysis.analysis_result import AnalysisResult, AnalysisResultError


class TestAnalysisResultError:
    """Test AnalysisResultError exception class."""

    def test_basic_creation(self):
        """Test basic AnalysisResultError creation."""
        error = AnalysisResultError("Analysis failed")
        assert str(error) == "Analysis failed"

    def test_creation_with_file(self):
        """Test AnalysisResultError creation with file."""
        error = AnalysisResultError("Analysis failed", result_file="test.py")
        assert str(error) == "Analysis failed"
        assert error.result_file == "test.py"

    def test_inheritance(self):
        """Test AnalysisResultError inherits from Exception."""
        error = AnalysisResultError("Test error")
        assert isinstance(error, Exception)


class TestAnalysisResult:
    """Test AnalysisResult class."""

    @pytest.fixture
    def workspace_root(self, tmp_path):
        """Create workspace root directory."""
        return tmp_path

    @pytest.fixture
    def test_file(self, workspace_root):
        """Create test file."""
        file_path = workspace_root / "test.py"
        file_path.write_text("print('hello')")
        return file_path

    @pytest.fixture
    def result(self, test_file, workspace_root):
        """Create AnalysisResult instance."""
        return AnalysisResult(test_file, workspace_root)

    def test_initialization(self, result):
        """Test AnalysisResult initialization."""
        assert result.relative_path == "test.py"
        assert result.quality_score == 0.0
        assert result.issues == []
        assert result.suggestions == []
        assert result.metrics == {}
        assert isinstance(result.timestamp, str)

    def test_initialization_with_string_paths(self, workspace_root):
        """Test initialization with string paths."""
        test_file = workspace_root / "test.py"
        test_file.write_text("content")

        result = AnalysisResult(str(test_file), str(workspace_root))

        assert result.relative_path == "test.py"

    def test_relative_path_inside_workspace(self, result):
        """Test relative path for file inside workspace."""
        assert result.relative_path == "test.py"

    def test_relative_path_outside_workspace(self, tmp_path):
        """Test relative path for file outside workspace."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        outside_file = tmp_path / "outside.py"
        outside_file.write_text("content")

        result = AnalysisResult(outside_file, workspace)

        # Should use absolute path when outside workspace
        assert result.relative_path == str(outside_file.resolve())

    def test_relative_path_nested_file(self, workspace_root):
        """Test relative path for nested file."""
        nested_dir = workspace_root / "src" / "module"
        nested_dir.mkdir(parents=True)

        nested_file = nested_dir / "nested.py"
        nested_file.write_text("content")

        result = AnalysisResult(nested_file, workspace_root)

        assert result.relative_path == "src/module/nested.py"

    def test_add_issue_string(self, result):
        """Test adding string issue."""
        result.add_issue("Test issue")

        assert len(result.issues) == 1
        assert result.issues[0] == "Test issue"

    def test_add_issue_invalid_type(self, result):
        """Test adding invalid issue type."""
        with pytest.raises(AnalysisResultError) as exc_info:
            result.add_issue(123)

        assert "Issue must be a string" in str(exc_info.value)

    def test_add_issue_empty_string(self, result):
        """Test adding empty string issue (should be ignored)."""
        result.add_issue("")
        result.add_issue("   ")  # Only whitespace

        assert len(result.issues) == 0

    def test_add_issue_duplicate_prevention(self, result):
        """Test that duplicate issues are prevented."""
        result.add_issue("Duplicate issue")
        result.add_issue("Duplicate issue")

        assert len(result.issues) == 1
        assert result.issues[0] == "Duplicate issue"

    def test_add_suggestion_string(self, result):
        """Test adding string suggestion."""
        result.add_suggestion("Use better variable names")

        assert len(result.suggestions) == 1
        assert result.suggestions[0] == "Use better variable names"

    def test_add_suggestion_invalid_type(self, result):
        """Test adding invalid suggestion type."""
        with pytest.raises(AnalysisResultError) as exc_info:
            result.add_suggestion({"type": "refactor"})

        assert "Suggestion must be a string" in str(exc_info.value)

    def test_add_multiple_issues(self, result):
        """Test adding multiple issues."""
        issues = ["Issue 1", "Issue 2", "Issue 3"]
        result.add_multiple_issues(issues)

        assert len(result.issues) == 3
        assert result.issues == issues

    def test_add_multiple_issues_invalid_type(self, result):
        """Test adding invalid multiple issues."""
        with pytest.raises(AnalysisResultError) as exc_info:
            result.add_multiple_issues("not a list")

        assert "Issues must be a list" in str(exc_info.value)

    def test_add_multiple_suggestions(self, result):
        """Test adding multiple suggestions."""
        suggestions = ["Suggestion 1", "Suggestion 2"]
        result.add_multiple_suggestions(suggestions)

        assert len(result.suggestions) == 2
        assert result.suggestions == suggestions

    def test_set_metrics_valid_dict(self, result):
        """Test setting valid metrics dictionary."""
        metrics = {
            "lines_of_code": 100,
            "complexity": 5.2,
            "test_coverage": 85.5,
        }

        result.set_metrics(metrics)

        assert result.metrics == metrics

    def test_set_metrics_invalid_type(self, result):
        """Test setting invalid metrics type."""
        with pytest.raises(AnalysisResultError) as exc_info:
            result.set_metrics("invalid")

        assert "Metrics must be a dictionary" in str(exc_info.value)

    def test_set_metrics_invalid_key_type(self, result):
        """Test setting metrics with invalid key type."""
        with pytest.raises(AnalysisResultError) as exc_info:
            result.set_metrics({123: "value"})

        assert "Metric key must be string" in str(exc_info.value)

    def test_update_metrics(self, result):
        """Test updating metrics."""
        initial_metrics = {"lines": 100, "complexity": 3}
        result.set_metrics(initial_metrics)

        additional_metrics = {"coverage": 85, "maintainability": 7}
        result.update_metrics(additional_metrics)

        expected_metrics = {"lines": 100, "complexity": 3, "coverage": 85, "maintainability": 7}
        assert result.metrics == expected_metrics

    def test_set_quality_score_valid_range(self, result):
        """Test setting quality score in valid range."""
        valid_scores = [0.0, 5.5, 10.0]

        for score in valid_scores:
            result.set_quality_score(score)
            assert result.quality_score == score

    def test_set_quality_score_invalid_type(self, result):
        """Test setting quality score with invalid type."""
        with pytest.raises(AnalysisResultError) as exc_info:
            result.set_quality_score("invalid")

        assert "Quality score must be numeric" in str(exc_info.value)

    def test_set_quality_score_clamping(self, result):
        """Test quality score clamping to valid range."""
        # Test below range
        result.set_quality_score(-5.0)
        assert result.quality_score == 0.0

        # Test above range
        result.set_quality_score(15.0)
        assert result.quality_score == 10.0

    def test_calculate_quality_score_with_metrics(self, result):
        """Test quality score calculation with metrics."""
        result.set_metrics({"cyclomatic_complexity": 3, "maintainability_index": 85})
        result.calculate_quality_score()

        # Score should be calculated from metrics and be reasonable
        assert result.quality_score > 0
        assert result.quality_score <= 10

    def test_calculate_quality_score_fallback(self, result):
        """Test quality score fallback calculation."""
        result.add_issue("Test issue")
        result.calculate_quality_score()

        # Should use issue-based scoring when no comprehensive metrics
        assert result.quality_score > 0  # Some score should be calculated
        assert result.quality_score <= 10  # Should be in valid range

    def test_to_dict_basic(self, result):
        """Test basic dictionary conversion."""
        result_dict = result.to_dict()

        expected_keys = {"file", "quality_score", "issues", "suggestions", "metrics", "timestamp"}
        assert set(result_dict.keys()) == expected_keys

        assert result_dict["file"] == "test.py"
        assert result_dict["quality_score"] == 0.0
        assert result_dict["issues"] == []
        assert result_dict["suggestions"] == []
        assert result_dict["metrics"] == {}
        assert isinstance(result_dict["timestamp"], str)

    def test_to_dict_with_data(self, result):
        """Test dictionary conversion with data."""
        result.add_issue("Test issue")
        result.add_suggestion("Test suggestion")
        result.set_metrics({"lines": 50, "complexity": 3})
        result.set_quality_score(8.5)

        result_dict = result.to_dict()

        assert result_dict["quality_score"] == 8.5
        assert result_dict["issues"] == ["Test issue"]
        assert result_dict["suggestions"] == ["Test suggestion"]
        assert result_dict["metrics"] == {"lines": 50, "complexity": 3}

    def test_to_summary_dict(self, result):
        """Test summary dictionary conversion."""
        result.add_issue("Issue 1")
        result.add_issue("Issue 2")
        result.add_suggestion("Suggestion 1")
        result.set_quality_score(7.5)

        summary_dict = result.to_summary_dict()

        expected_keys = {"file", "quality_score", "issue_count", "suggestion_count", "timestamp"}
        assert set(summary_dict.keys()) == expected_keys
        assert summary_dict["issue_count"] == 2
        assert summary_dict["suggestion_count"] == 1
        assert summary_dict["quality_score"] == 7.5

    def test_has_issues(self, result):
        """Test checking if result has issues."""
        assert not result.has_issues()

        result.add_issue("Test issue")
        assert result.has_issues()

    def test_has_suggestions(self, result):
        """Test checking if result has suggestions."""
        assert not result.has_suggestions()

        result.add_suggestion("Test suggestion")
        assert result.has_suggestions()

    def test_has_metrics(self, result):
        """Test checking if result has metrics."""
        assert not result.has_metrics()

        result.set_metrics({"test": 123})
        assert result.has_metrics()

    def test_is_high_quality(self, result):
        """Test high quality check."""
        # Default threshold is 8.0
        result.set_quality_score(7.5)
        assert not result.is_high_quality()

        result.set_quality_score(8.5)
        assert result.is_high_quality()

        # Custom threshold
        result.set_quality_score(7.5)
        assert result.is_high_quality(threshold=7.0)

    def test_clear_methods(self, result):
        """Test clearing data."""
        # Add some data
        result.add_issue("Test issue")
        result.add_suggestion("Test suggestion")
        result.set_metrics({"test": 123})

        # Clear individually
        result.clear_issues()
        assert result.issues == []
        assert result.has_suggestions()  # Other data intact

        result.clear_suggestions()
        assert result.suggestions == []
        assert result.has_metrics()  # Other data intact

        result.clear_metrics()
        assert result.metrics == {}

    def test_reset(self, result):
        """Test resetting all data."""
        # Add some data
        result.add_issue("Test issue")
        result.add_suggestion("Test suggestion")
        result.set_metrics({"test": 123})
        result.set_quality_score(7.5)

        original_timestamp = result.timestamp

        # Reset
        result.reset()

        assert result.issues == []
        assert result.suggestions == []
        assert result.metrics == {}
        assert result.quality_score == 0.0
        assert result.timestamp != original_timestamp  # Should be updated

    def test_str_and_repr(self, result):
        """Test string representations."""
        result.add_issue("Test issue")
        result.set_quality_score(7.5)

        str_repr = str(result)
        assert "test.py" in str_repr
        assert "7.5/10" in str_repr
        assert "issues: 1" in str_repr

        repr_str = repr(result)
        assert "AnalysisResult" in repr_str
        assert "test.py" in repr_str
        assert "score=7.5" in repr_str
        assert "issues=1" in repr_str


class TestAnalysisResultEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_invalid_path_handling(self, tmp_path):
        """Test handling of invalid paths."""
        nonexistent_workspace = tmp_path / "nonexistent"
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        # Should still work even with questionable paths
        try:
            result = AnalysisResult(test_file, nonexistent_workspace)
            # Should use absolute path when relative calculation fails
            assert str(test_file.resolve()) in result.relative_path
        except AnalysisResultError:
            # This is also acceptable behavior
            pass

    def test_unicode_content(self, tmp_path):
        """Test handling of unicode in paths and content."""
        unicode_file = tmp_path / "тест_файл.py"
        unicode_file.write_text("# тест content")

        result = AnalysisResult(unicode_file, tmp_path)

        # Should handle unicode paths
        assert "тест_файл.py" in result.relative_path

        # Should handle unicode in issues/suggestions
        result.add_issue("Ошибка: неправильный код")
        result.add_suggestion("Исправьте код")

        assert "Ошибка" in result.issues[0]
        assert "Исправьте" in result.suggestions[0]

    def test_large_data_handling(self, tmp_path):
        """Test handling of large amounts of data."""
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        result = AnalysisResult(test_file, tmp_path)

        # Add many issues
        for i in range(1000):
            result.add_issue(f"Issue {i}")

        # Add many metrics
        large_metrics = {f"metric_{i}": i for i in range(1000)}
        result.set_metrics(large_metrics)

        assert len(result.issues) == 1000
        assert len(result.metrics) == 1000

        # Should still convert to dict efficiently
        result_dict = result.to_dict()
        assert len(result_dict["issues"]) == 1000
        assert len(result_dict["metrics"]) == 1000

    def test_metric_value_validation(self, tmp_path):
        """Test metric value validation."""
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        result = AnalysisResult(test_file, tmp_path)

        # Valid metric values
        valid_metrics = {
            "int_val": 123,
            "float_val": 45.67,
            "str_val": "test",
            "bool_val": True,
            "list_val": [1, 2, 3],
            "dict_val": {"nested": "value"},
            "none_val": None,
        }

        result.set_metrics(valid_metrics)
        assert result.metrics == valid_metrics
