"""
Comprehensive tests for quality scoring system.

This module provides complete test coverage for quality score calculations
including comprehensive metrics, issue-based scoring, and error handling.
"""

import pytest

from coder_mcp.analysis.quality_scoring import (
    DEFAULT_QUALITY_SCORE,
    MAX_QUALITY_SCORE,
    MIN_QUALITY_SCORE,
    QualityScoreCalculator,
    QualityScoringError,
)


class TestQualityScoringError:
    """Test QualityScoringError exception class."""

    def test_basic_creation(self):
        """Test basic QualityScoringError creation."""
        error = QualityScoringError("Quality scoring failed")
        assert str(error) == "Quality scoring failed"
        assert error.metrics is None

    def test_creation_with_metrics(self):
        """Test QualityScoringError creation with metrics."""
        metrics = {"test": 123}
        error = QualityScoringError("Quality scoring failed", metrics=metrics)
        assert str(error) == "Quality scoring failed"
        assert error.metrics == metrics

    def test_inheritance(self):
        """Test QualityScoringError inherits from Exception."""
        error = QualityScoringError("Test error")
        assert isinstance(error, Exception)


class TestQualityScoreCalculator:
    """Test QualityScoreCalculator class."""

    def test_calculate_from_issues_zero_issues(self):
        """Test calculating score with zero issues."""
        score = QualityScoreCalculator.calculate_from_issues(0)

        assert score == 10  # Perfect score with no issues

    def test_calculate_from_issues_few_issues(self):
        """Test calculating score with few issues."""
        score = QualityScoreCalculator.calculate_from_issues(2)

        assert isinstance(score, int)
        assert MIN_QUALITY_SCORE <= score <= MAX_QUALITY_SCORE
        assert score < 10  # Should be less than perfect

    def test_calculate_from_issues_many_issues(self):
        """Test calculating score with many issues."""
        score = QualityScoreCalculator.calculate_from_issues(50)

        assert isinstance(score, int)
        assert MIN_QUALITY_SCORE <= score <= MAX_QUALITY_SCORE
        assert score < 5  # Should be quite low

    def test_calculate_from_issues_invalid_type(self):
        """Test calculating score with invalid issue count type."""
        with pytest.raises(QualityScoringError) as exc_info:
            QualityScoreCalculator.calculate_from_issues("invalid")

        assert "Issue count must be an integer" in str(exc_info.value)

    def test_calculate_from_issues_negative_count(self):
        """Test calculating score with negative issue count."""
        with pytest.raises(QualityScoringError) as exc_info:
            QualityScoreCalculator.calculate_from_issues(-5)

        assert "Issue count must be non-negative" in str(exc_info.value)

    def test_calculate_from_comprehensive_metrics_empty(self):
        """Test calculating score with empty metrics."""
        score = QualityScoreCalculator.calculate_from_comprehensive_metrics({})

        assert score is None

    def test_calculate_from_comprehensive_metrics_invalid_type(self):
        """Test calculating score with invalid metrics type."""
        with pytest.raises(QualityScoringError) as exc_info:
            QualityScoreCalculator.calculate_from_comprehensive_metrics("invalid")

        assert "Metrics must be a dictionary" in str(exc_info.value)

    def test_calculate_from_comprehensive_metrics_overall_score(self):
        """Test calculating score with overall quality score in metrics."""
        metrics = {"overall_quality_score": 75}  # 0-100 scale

        score = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)

        assert score == 7.5  # Converted to 0-10 scale

    def test_calculate_from_comprehensive_metrics_complexity(self):
        """Test calculating score with complexity metrics."""
        # Need sufficient metrics to reach 50% weight threshold
        metrics = {"cyclomatic_complexity": 3, "maintainability_index": 80, "test_coverage": 85}

        score = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)

        assert score is not None
        assert isinstance(score, float)
        assert MIN_QUALITY_SCORE <= score <= MAX_QUALITY_SCORE

    def test_calculate_from_comprehensive_metrics_maintainability(self):
        """Test calculating score with maintainability metrics."""
        # Add enough metrics to reach 50% weight threshold
        metrics = {"maintainability_index": 85, "test_coverage": 80, "cyclomatic_complexity": 5}

        score = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)

        assert score is not None
        assert isinstance(score, float)
        assert score >= 7.0  # Should be high score for good maintainability

    def test_calculate_from_comprehensive_metrics_readability(self):
        """Test calculating score with readability metrics."""
        # Add enough metrics to reach 50% weight threshold
        metrics = {
            "comment_ratio": 20,  # Good comment ratio
            "average_line_length": 75,  # Good line length
            "cyclomatic_complexity": 5,  # Add complexity metric
            "test_coverage": 80,  # Add reliability metric
        }

        score = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)

        assert score is not None
        assert isinstance(score, float)
        assert score >= 7.0  # Should be high score

    def test_calculate_from_comprehensive_metrics_reliability(self):
        """Test calculating score with reliability metrics."""
        # Add enough metrics to reach 50% weight threshold
        metrics = {
            "test_coverage": 85,  # Good coverage
            "error_handling_ratio": 75,  # Good error handling
            "cyclomatic_complexity": 5,  # Add complexity metric
            "maintainability_index": 80,  # Add maintainability metric
        }

        score = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)

        assert score is not None
        assert isinstance(score, float)
        assert score >= 7.0  # Should be high score

    def test_calculate_from_comprehensive_metrics_performance(self):
        """Test calculating score with performance metrics."""
        # Add enough metrics to reach 50% weight threshold
        metrics = {
            "performance_issues": 2,
            "cyclomatic_complexity": 8,
            "test_coverage": 75,
            "maintainability_index": 70,
        }

        score = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)

        assert score is not None
        assert isinstance(score, float)
        assert score >= 5.0  # Should be reasonable score

    def test_calculate_from_comprehensive_metrics_insufficient_data(self):
        """Test calculating score with insufficient metric data."""
        # Use only one metric that contributes 20% weight (below 50% threshold)
        metrics = {"cyclomatic_complexity": 10}

        score = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)

        assert score is None  # Not enough metrics to reach 50% weight threshold

    def test_score_complexity_cyclomatic_excellent(self):
        """Test complexity scoring with excellent cyclomatic complexity."""
        metrics = {"cyclomatic_complexity": 3}

        score = QualityScoreCalculator._score_complexity(metrics)

        assert score == 10.0

    def test_score_complexity_cyclomatic_poor(self):
        """Test complexity scoring with poor cyclomatic complexity."""
        metrics = {"cyclomatic_complexity": 25}

        score = QualityScoreCalculator._score_complexity(metrics)

        assert score == 2.0

    def test_score_complexity_cognitive_excellent(self):
        """Test complexity scoring with excellent cognitive complexity."""
        metrics = {"cognitive_complexity": 5}

        score = QualityScoreCalculator._score_complexity(metrics)

        assert score == 10.0

    def test_score_complexity_halstead_excellent(self):
        """Test complexity scoring with excellent Halstead difficulty."""
        metrics = {"halstead_difficulty": 8}

        score = QualityScoreCalculator._score_complexity(metrics)

        assert score == 10.0

    def test_score_complexity_mixed_metrics(self):
        """Test complexity scoring with mixed metrics."""
        metrics = {
            "cyclomatic_complexity": 3,  # Excellent
            "cognitive_complexity": 15,  # Good
            "halstead_difficulty": 25,  # Average
        }

        score = QualityScoreCalculator._score_complexity(metrics)

        assert score is not None
        assert 5.0 <= score <= 10.0  # Should be average of scores

    def test_score_complexity_no_metrics(self):
        """Test complexity scoring with no complexity metrics."""
        metrics = {"other_metric": 42}

        score = QualityScoreCalculator._score_complexity(metrics)

        assert score is None

    def test_score_maintainability_excellent(self):
        """Test maintainability scoring with excellent metrics."""
        metrics = {"maintainability_index": 90}

        score = QualityScoreCalculator._score_maintainability(metrics)

        assert score == 10.0

    def test_score_maintainability_technical_debt(self):
        """Test maintainability scoring with technical debt."""
        metrics = {"technical_debt_ratio": 3}  # Low technical debt

        score = QualityScoreCalculator._score_maintainability(metrics)

        assert score == 10.0

    def test_score_readability_optimal_comment_ratio(self):
        """Test readability scoring with optimal comment ratio."""
        metrics = {"comment_ratio": 20}  # Optimal range

        score = QualityScoreCalculator._score_readability(metrics)

        assert score == 10.0

    def test_score_readability_poor_comment_ratio(self):
        """Test readability scoring with poor comment ratio."""
        metrics = {"comment_ratio": 60}  # Too many comments

        score = QualityScoreCalculator._score_readability(metrics)

        assert score == 2.0

    def test_score_readability_optimal_line_length(self):
        """Test readability scoring with optimal line length."""
        metrics = {"average_line_length": 75}  # Good length

        score = QualityScoreCalculator._score_readability(metrics)

        assert score == 10.0

    def test_score_readability_naming_quality(self):
        """Test readability scoring with naming quality."""
        metrics = {"naming_quality": 8.5}

        score = QualityScoreCalculator._score_readability(metrics)

        assert score == 8.5

    def test_score_reliability_excellent_coverage(self):
        """Test reliability scoring with excellent test coverage."""
        metrics = {"test_coverage": 95}

        score = QualityScoreCalculator._score_reliability(metrics)

        assert score == 10.0

    def test_score_reliability_poor_coverage(self):
        """Test reliability scoring with poor test coverage."""
        metrics = {"test_coverage": 30}

        score = QualityScoreCalculator._score_reliability(metrics)

        assert score == 2.0

    def test_score_reliability_error_handling(self):
        """Test reliability scoring with error handling ratio."""
        metrics = {"error_handling_ratio": 85}

        score = QualityScoreCalculator._score_reliability(metrics)

        assert score == 10.0

    def test_score_performance_no_issues(self):
        """Test performance scoring with no performance issues."""
        metrics = {"performance_issues": 0}

        score = QualityScoreCalculator._score_performance(metrics)

        assert score == 10.0

    def test_score_performance_many_issues(self):
        """Test performance scoring with many performance issues."""
        metrics = {"performance_issues": 10}

        score = QualityScoreCalculator._score_performance(metrics)

        assert score == 2.0

    def test_score_performance_no_data(self):
        """Test performance scoring with no performance data."""
        metrics = {"other_metric": 42}

        score = QualityScoreCalculator._score_performance(metrics)

        # The method returns 10.0 as default for performance_issues=0 when no explicit
        # performance_issues
        assert score == 10.0

    def test_get_score_description_excellent(self):
        """Test score description for excellent score."""
        description = QualityScoreCalculator.get_score_description(9.5)

        assert description == "Excellent"

    def test_get_score_description_very_good(self):
        """Test score description for very good score."""
        description = QualityScoreCalculator.get_score_description(8.2)

        assert description == "Very Good"

    def test_get_score_description_good(self):
        """Test score description for good score."""
        description = QualityScoreCalculator.get_score_description(7.8)

        assert description == "Good"

    def test_get_score_description_above_average(self):
        """Test score description for above average score."""
        description = QualityScoreCalculator.get_score_description(6.5)

        assert description == "Above Average"

    def test_get_score_description_average(self):
        """Test score description for average score."""
        description = QualityScoreCalculator.get_score_description(5.0)

        assert description == "Average"

    def test_get_score_description_below_average(self):
        """Test score description for below average score."""
        description = QualityScoreCalculator.get_score_description(4.2)

        assert description == "Below Average"

    def test_get_score_description_poor(self):
        """Test score description for poor score."""
        description = QualityScoreCalculator.get_score_description(3.1)

        assert description == "Poor"

    def test_get_score_description_very_poor(self):
        """Test score description for very poor score."""
        description = QualityScoreCalculator.get_score_description(2.5)

        assert description == "Very Poor"

    def test_get_score_description_critical(self):
        """Test score description for critical score."""
        description = QualityScoreCalculator.get_score_description(1.0)

        assert description == "Critical"

    def test_get_score_description_invalid_score(self):
        """Test score description for invalid score."""
        description = QualityScoreCalculator.get_score_description("invalid")

        assert description == "Invalid score"

    def test_quality_score_constants(self):
        """Test quality score constants are properly defined."""
        assert MIN_QUALITY_SCORE == 0
        assert MAX_QUALITY_SCORE == 10
        assert DEFAULT_QUALITY_SCORE == 5

        # Constants should be in logical order
        assert MIN_QUALITY_SCORE <= DEFAULT_QUALITY_SCORE <= MAX_QUALITY_SCORE


class TestQualityScoreCalculatorIntegration:
    """Integration tests for QualityScoreCalculator."""

    def test_comprehensive_metrics_integration(self):
        """Test integration of comprehensive metrics calculation."""
        # Complex metrics scenario
        metrics = {
            "cyclomatic_complexity": 5,  # Excellent
            "maintainability_index": 80,  # Excellent
            "comment_ratio": 25,  # Excellent
            "test_coverage": 85,  # Excellent
            "performance_issues": 1,  # Good
        }

        score = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)

        assert score is not None
        assert score >= 8.0  # Should be high with mostly excellent metrics

    def test_mixed_quality_metrics_integration(self):
        """Test integration with mixed quality metrics."""
        metrics = {
            "cyclomatic_complexity": 15,  # Average
            "maintainability_index": 60,  # Good
            "comment_ratio": 5,  # Poor (too few comments)
            "test_coverage": 50,  # Average
            "performance_issues": 5,  # Average
        }

        score = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)

        assert score is not None
        assert 4.0 <= score <= 7.0  # Should be in average range

    def test_poor_quality_metrics_integration(self):
        """Test integration with poor quality metrics."""
        metrics = {
            "cyclomatic_complexity": 30,  # Poor
            "maintainability_index": 30,  # Poor
            "comment_ratio": 70,  # Poor (too many comments)
            "test_coverage": 20,  # Poor
            "performance_issues": 15,  # Poor
        }

        score = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)

        assert score is not None
        assert score <= 3.0  # Should be low with all poor metrics

    def test_edge_case_values(self):
        """Test edge case metric values."""
        # Test boundary values
        metrics = {
            "cyclomatic_complexity": 0,  # Edge case: no complexity
            "test_coverage": 100,  # Perfect coverage
            "comment_ratio": 0,  # No comments
            "performance_issues": -1,  # Invalid but should handle gracefully
        }

        score = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)

        # Should handle gracefully and return some score
        assert score is None or (MIN_QUALITY_SCORE <= score <= MAX_QUALITY_SCORE)

    def test_large_scale_metrics(self):
        """Test with large-scale project metrics."""
        # Simulate large project with many metrics
        metrics = {}
        for i in range(100):
            metrics[f"metric_{i}"] = i % 10  # Various values

        # Add some known metrics
        metrics.update(
            {
                "cyclomatic_complexity": 8,
                "test_coverage": 75,
                "maintainability_index": 70,
            }
        )

        score = QualityScoreCalculator.calculate_from_comprehensive_metrics(metrics)

        assert score is not None
        assert MIN_QUALITY_SCORE <= score <= MAX_QUALITY_SCORE
