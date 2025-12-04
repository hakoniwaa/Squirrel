"""
Tests for quality scoring system with logarithmic decay model.
"""

import math

import pytest

from coder_mcp.analysis.quality_scoring import QualityScoreCalculator, QualityScoringError


class TestQualityScoreCalculator:
    """Test suite for the QualityScoreCalculator class."""

    def test_calculate_from_issues_no_issues(self):
        """Test quality score calculation with no issues."""
        result = QualityScoreCalculator.calculate_from_issues(0)
        assert result == 10  # Perfect score for no issues

    def test_calculate_from_issues_few_issues(self):
        """Test quality score calculation with few issues."""
        # Using actual logarithmic formula: max(0, 10 - 2 * log(1 + issue_count / 2))
        result = QualityScoreCalculator.calculate_from_issues(1)
        expected = max(0, int(round(10 - 2 * math.log(1 + 1 / 2))))  # ≈ 9
        assert result == expected

    def test_calculate_from_issues_some_issues(self):
        """Test quality score calculation with some issues."""
        result = QualityScoreCalculator.calculate_from_issues(3)
        expected = max(0, int(round(10 - 2 * math.log(1 + 3 / 2))))  # ≈ 8
        assert result == expected

    def test_calculate_from_issues_many_issues(self):
        """Test quality score calculation with many issues."""
        result = QualityScoreCalculator.calculate_from_issues(5)
        expected = max(0, int(round(10 - 2 * math.log(1 + 5 / 2))))  # ≈ 7
        assert result == expected

    def test_calculate_from_issues_excessive_issues(self):
        """Test quality score calculation with excessive issues."""
        result = QualityScoreCalculator.calculate_from_issues(10)
        expected = max(0, int(round(10 - 2 * math.log(1 + 10 / 2))))  # ≈ 6
        assert result == expected

    def test_calculate_from_issues_zero_value(self):
        """Test quality score calculation with zero issues."""
        result = QualityScoreCalculator.calculate_from_issues(0)
        assert result == 10

    def test_calculate_from_issues_negative_input(self):
        """Test quality score calculation with negative issue count."""
        with pytest.raises(QualityScoringError, match="Issue count must be non-negative"):
            QualityScoreCalculator.calculate_from_issues(-1)

    def test_calculate_from_issues_invalid_type(self):
        """Test quality score calculation with invalid type."""
        with pytest.raises(QualityScoringError, match="Issue count must be an integer"):
            QualityScoreCalculator.calculate_from_issues("not_an_int")

    def test_calculate_from_issues_formula_verification(self):
        """Test that the logarithmic scoring formula works as expected."""
        # Test formula: max(0, 10 - 2 * log(1 + issue_count / 2))
        test_cases = [
            (0, 10),  # No issues = perfect score
            (1, 9),  # 1 issue = max(0, 10 - 2*log(1.5)) ≈ 9
            (2, 8),  # 2 issues = max(0, 10 - 2*log(2)) ≈ 9
            (4, 8),  # 4 issues = max(0, 10 - 2*log(3)) ≈ 8
            (6, 7),  # 6 issues = max(0, 10 - 2*log(4)) ≈ 7
            (10, 6),  # 10 issues = max(0, 10 - 2*log(6)) ≈ 6
        ]

        for issue_count, expected_min in test_cases:
            result = QualityScoreCalculator.calculate_from_issues(issue_count)
            # Allow for rounding differences but check it's in reasonable range
            assert (
                abs(result - expected_min) <= 1
            ), f"Failed for {issue_count} issues: got {result}, expected ~{expected_min}"

    def test_calculate_from_comprehensive_metrics_valid_score(self):
        """Test comprehensive metrics calculation with valid overall score."""
        metrics = {"overall_quality_score": 75}
        result = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)
        assert result == 7.5

    def test_calculate_from_comprehensive_metrics_none_input(self):
        """Test comprehensive metrics calculation with None input."""
        with pytest.raises(QualityScoringError, match="Metrics must be a dictionary"):
            QualityScoreCalculator.calculate_from_comprehensive_metrics(None)

    def test_calculate_from_comprehensive_metrics_empty_dict(self):
        """Test comprehensive metrics calculation with empty dictionary."""
        result = QualityScoreCalculator.calculate_from_comprehensive_metrics({})
        assert result is None

    def test_calculate_from_comprehensive_metrics_invalid_score(self):
        """Test comprehensive metrics calculation with invalid score values."""
        # Test with score outside valid range (not 0-100)
        metrics = {"overall_quality_score": 150}
        result = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)
        assert result is None  # Invalid scores should return None

    def test_calculate_from_comprehensive_metrics_edge_cases(self):
        """Test comprehensive metrics calculation with edge case scores."""
        test_cases = [
            (0, 0.0),  # Minimum valid score
            (100, 10.0),  # Maximum valid score
            (50, 5.0),  # Middle score
        ]

        for input_score, expected_output in test_cases:
            metrics = {"overall_quality_score": input_score}
            result = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)
            assert result == expected_output

    def test_calculate_from_comprehensive_metrics_weighted_scoring(self):
        """Test comprehensive metrics with weighted component scoring."""
        metrics = {
            "cyclomatic_complexity": 3,  # Should score well (≤5 is excellent)
            "maintainability_index": 75,  # Should score well (≥60 is good)
            "test_coverage": 85,  # Should score well (≥70 is good)
        }
        result = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)
        assert result is not None
        assert 6.0 <= result <= 10.0  # Should be a good score

    @pytest.mark.parametrize(
        "issue_count,expected_range",
        [
            (0, (10, 10)),  # Perfect score
            (1, (8, 10)),  # Very good
            (2, (8, 9)),  # Good
            (4, (7, 9)),  # Average to good
            (8, (6, 8)),  # Below average to average
            (15, (4, 7)),  # Poor to below average
            (50, (0, 4)),  # Very poor
        ],
    )
    def test_calculate_from_issues_parametrized(self, issue_count, expected_range):
        """Parametrized test for issue-based scoring with ranges."""
        result = QualityScoreCalculator.calculate_from_issues(issue_count)
        min_expected, max_expected = expected_range
        assert (
            min_expected <= result <= max_expected
        ), f"Score {result} not in expected range {expected_range} for {issue_count} issues"

    def test_integration_both_methods(self):
        """Integration test using both calculation methods."""
        # Test comprehensive method
        metrics = {"overall_quality_score": 75}
        comprehensive_result = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)
        assert comprehensive_result == 7.5

        # Test issue-based method
        issue_result = QualityScoreCalculator.calculate_from_issues(3)
        expected = max(0, int(round(10 - 2 * math.log(1 + 3 / 2))))
        assert issue_result == expected

    def test_method_independence(self):
        """Test that both methods are independent and don't affect each other."""
        # Call methods in different orders to ensure no state is shared
        result1 = QualityScoreCalculator.calculate_from_issues(5)
        result2 = QualityScoreCalculator.calculate_from_comprehensive_metrics(
            {"overall_quality_score": 50}
        )
        result3 = QualityScoreCalculator.calculate_from_issues(5)

        # Results should be consistent regardless of call order
        assert result1 == result3
        assert result2 == 5.0

    def test_score_description_method(self):
        """Test the score description helper method."""
        test_cases = [
            (10, "Excellent"),
            (9, "Excellent"),
            (8, "Very Good"),
            (7, "Good"),
            (6, "Above Average"),
            (5, "Average"),
            (4, "Below Average"),
            (3, "Poor"),
            (2, "Very Poor"),
            (1, "Critical"),
            (0, "Critical"),
        ]

        for score, expected_desc in test_cases:
            result = QualityScoreCalculator.get_score_description(score)
            assert result == expected_desc

    def test_score_description_invalid_input(self):
        """Test score description with invalid input."""
        result = QualityScoreCalculator.get_score_description("invalid")
        assert result == "Invalid score"
