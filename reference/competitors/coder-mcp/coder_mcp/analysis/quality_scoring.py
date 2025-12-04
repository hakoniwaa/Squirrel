"""
Quality scoring system for code analysis.

This module provides robust algorithms for calculating code quality scores
based on various metrics and issues. The scoring system is designed to be
extensible and configurable.

Classes:
    QualityScoreCalculator: Advanced utility for quality score calculations
    QualityScoringError: Custom exception for scoring errors

Constants:
    Various scoring thresholds and weights
"""

import math
from typing import Any, Dict, Optional, Union

# Quality score constants
MIN_QUALITY_SCORE = 0
MAX_QUALITY_SCORE = 10
DEFAULT_QUALITY_SCORE = 5

# Issue-based scoring constants
ISSUE_PENALTY_WEIGHT = 2.0
ISSUE_GROUP_SIZE = 2
EXCELLENT_THRESHOLD = 10

# Metrics-based scoring weights
COMPLEXITY_WEIGHT = 0.2
MAINTAINABILITY_WEIGHT = 0.25
READABILITY_WEIGHT = 0.2
RELIABILITY_WEIGHT = 0.2
PERFORMANCE_WEIGHT = 0.15

# Metric thresholds
COMPLEXITY_EXCELLENT = 5
COMPLEXITY_GOOD = 10
COMPLEXITY_POOR = 20

MAINTAINABILITY_EXCELLENT = 80
MAINTAINABILITY_GOOD = 60
MAINTAINABILITY_POOR = 40

TEST_COVERAGE_EXCELLENT = 90
TEST_COVERAGE_GOOD = 70
TEST_COVERAGE_POOR = 50

# Quality score values
SCORE_EXCELLENT = 10.0
SCORE_GOOD = 7.5
SCORE_AVERAGE = 5.0
SCORE_POOR = 2.0

# Comment ratio thresholds (percentages)
COMMENT_RATIO_OPTIMAL_MIN = 10
COMMENT_RATIO_OPTIMAL_MAX = 30
COMMENT_RATIO_ACCEPTABLE_MIN = 5
COMMENT_RATIO_ACCEPTABLE_MAX = 40
COMMENT_RATIO_POOR_MAX = 50

# Line length thresholds
OPTIMAL_LINE_LENGTH = 80
GOOD_LINE_LENGTH = 120
POOR_LINE_LENGTH = 150


class QualityScoringError(Exception):
    """Custom exception for quality scoring errors."""

    def __init__(self, message: str, metrics: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.metrics = metrics


class QualityScoreCalculator:
    """Advanced utility for calculating comprehensive quality scores.

    This class provides multiple algorithms for scoring code quality based on
    different metrics and issue types. It supports both simple issue-based
    scoring and comprehensive metrics-based scoring.
    """

    @staticmethod
    def calculate_from_issues(issue_count: int) -> int:
        """Calculate quality score from issue count using a logarithmic decay model.

        This method provides a more nuanced scoring approach than simple linear
        penalties, recognizing that initial issues have more impact on quality
        than additional issues in already problematic code.

        Args:
            issue_count: Number of detected issues

        Returns:
            Quality score (0-10)

        Raises:
            QualityScoringError: If issue_count is invalid
        """
        if not isinstance(issue_count, int):
            raise QualityScoringError(f"Issue count must be an integer, got {type(issue_count)}")

        if issue_count < 0:
            raise QualityScoringError(f"Issue count must be non-negative, got {issue_count}")

        if issue_count == 0:
            return EXCELLENT_THRESHOLD

        # Logarithmic decay model: quality decreases more slowly as issues accumulate
        # Formula: max(MIN_SCORE, MAX_SCORE - WEIGHT * log(1 + issues/GROUP_SIZE))
        penalty = ISSUE_PENALTY_WEIGHT * math.log(1 + issue_count / ISSUE_GROUP_SIZE)
        score = MAX_QUALITY_SCORE - penalty

        return max(MIN_QUALITY_SCORE, int(round(score)))

    @staticmethod
    def calculate_from_comprehensive_metrics(metrics: Dict[str, Any]) -> Optional[float]:
        """Calculate quality score from comprehensive metrics using weighted scoring.

        This method combines various code metrics using a weighted approach to
        provide a holistic quality assessment. Returns None if insufficient
        metrics are available.

        Args:
            metrics: Dictionary of collected metrics

        Returns:
            Quality score (0.0-10.0) or None if insufficient data

        Raises:
            QualityScoringError: If metrics structure is invalid
        """
        if not isinstance(metrics, dict):
            raise QualityScoringError(f"Metrics must be a dictionary, got {type(metrics)}")
        if not metrics:
            return None

        score = QualityScoreCalculator._extract_overall_score(metrics)
        if score is not None:
            return score

        return QualityScoreCalculator._calculate_weighted_score(metrics)

    @staticmethod
    def _extract_overall_score(metrics: Dict[str, Any]) -> Optional[float]:
        if "overall_quality_score" in metrics:
            score = metrics["overall_quality_score"]
            if isinstance(score, (int, float)) and 0 <= score <= 100:
                return round(score / 10.0, 1)  # Convert from 0-100 to 0-10 scale
        return None

    @staticmethod
    def _calculate_weighted_score(metrics: Dict[str, Any]) -> Optional[float]:
        total_score = 0.0
        total_weight = 0.0

        # Complexity scoring
        complexity_score = QualityScoreCalculator._score_complexity(metrics)
        if complexity_score is not None:
            total_score += complexity_score * COMPLEXITY_WEIGHT
            total_weight += COMPLEXITY_WEIGHT

        # Maintainability scoring
        maintainability_score = QualityScoreCalculator._score_maintainability(metrics)
        if maintainability_score is not None:
            total_score += maintainability_score * MAINTAINABILITY_WEIGHT
            total_weight += MAINTAINABILITY_WEIGHT

        # Readability scoring
        readability_score = QualityScoreCalculator._score_readability(metrics)
        if readability_score is not None:
            total_score += readability_score * READABILITY_WEIGHT
            total_weight += READABILITY_WEIGHT

        # Reliability scoring (test coverage, error handling)
        reliability_score = QualityScoreCalculator._score_reliability(metrics)
        if reliability_score is not None:
            total_score += reliability_score * RELIABILITY_WEIGHT
            total_weight += RELIABILITY_WEIGHT

        # Performance scoring
        performance_score = QualityScoreCalculator._score_performance(metrics)
        if performance_score is not None:
            total_score += performance_score * PERFORMANCE_WEIGHT
            total_weight += PERFORMANCE_WEIGHT

        # Return weighted average if we have enough data
        if total_weight >= 0.5:  # At least 50% of metrics available
            return round(total_score / total_weight, 1)

        return None

    @staticmethod
    def _score_complexity(metrics: Dict[str, Any]) -> Optional[float]:
        """Score code complexity metrics.

        Args:
            metrics: Metrics dictionary

        Returns:
            Complexity score (0-10) or None
        """
        cyclomatic = metrics.get("cyclomatic_complexity")
        cognitive = metrics.get("cognitive_complexity")
        halstead = metrics.get("halstead_difficulty")

        scores = []

        cyclomatic_score = QualityScoreCalculator._score_cyclomatic_complexity(cyclomatic)
        if cyclomatic_score is not None:
            scores.append(cyclomatic_score)

        cognitive_score = QualityScoreCalculator._score_cognitive_complexity(cognitive)
        if cognitive_score is not None:
            scores.append(cognitive_score)

        halstead_score = QualityScoreCalculator._score_halstead_difficulty(halstead)
        if halstead_score is not None:
            scores.append(halstead_score)

        return sum(scores) / len(scores) if scores else None

    @staticmethod
    def _score_cyclomatic_complexity(cyclomatic: Any) -> Optional[float]:
        if isinstance(cyclomatic, (int, float)) and cyclomatic >= 0:
            if cyclomatic <= COMPLEXITY_EXCELLENT:
                return 10.0
            elif cyclomatic <= COMPLEXITY_GOOD:
                return 7.5
            elif cyclomatic <= COMPLEXITY_POOR:
                return 5.0
            else:
                return 2.0
        return None

    @staticmethod
    def _score_cognitive_complexity(cognitive: Any) -> Optional[float]:
        if isinstance(cognitive, (int, float)) and cognitive >= 0:
            if cognitive <= COMPLEXITY_EXCELLENT * 1.5:
                return 10.0
            elif cognitive <= COMPLEXITY_GOOD * 1.5:
                return 7.5
            elif cognitive <= COMPLEXITY_POOR * 1.5:
                return 5.0
            else:
                return 2.0
        return None

    @staticmethod
    def _score_halstead_difficulty(halstead: Any) -> Optional[float]:
        if isinstance(halstead, (int, float)) and halstead > 0:
            if halstead <= 10:
                return 10.0
            elif halstead <= 20:
                return 7.5
            elif halstead <= 40:
                return 5.0
            else:
                return 2.0
        return None

    @staticmethod
    def _score_maintainability(metrics: Dict[str, Any]) -> Optional[float]:
        """Score maintainability metrics.

        Args:
            metrics: Metrics dictionary

        Returns:
            Maintainability score (0-10) or None
        """
        maintainability_index = metrics.get("maintainability_index")
        technical_debt = metrics.get("technical_debt_ratio")

        scores = []

        if isinstance(maintainability_index, (int, float)):
            if maintainability_index >= MAINTAINABILITY_EXCELLENT:
                scores.append(10.0)
            elif maintainability_index >= MAINTAINABILITY_GOOD:
                scores.append(7.5)
            elif maintainability_index >= MAINTAINABILITY_POOR:
                scores.append(5.0)
            else:
                scores.append(2.0)

        if isinstance(technical_debt, (int, float)) and technical_debt >= 0:
            # Technical debt ratio: lower is better
            if technical_debt <= 5:
                scores.append(10.0)
            elif technical_debt <= 10:
                scores.append(7.5)
            elif technical_debt <= 20:
                scores.append(5.0)
            else:
                scores.append(2.0)

        return sum(scores) / len(scores) if scores else None

    @staticmethod
    def _score_readability(metrics: Dict[str, Any]) -> Optional[float]:
        """Score readability metrics.

        Args:
            metrics: Metrics dictionary

        Returns:
            Readability score (0-10) or None
        """
        comment_ratio = metrics.get("comment_ratio")
        avg_line_length = metrics.get("average_line_length")
        naming_score = metrics.get("naming_quality")

        scores = []

        if isinstance(comment_ratio, (int, float)) and 0 <= comment_ratio <= 100:
            # Optimal comment ratio is around 10-30%
            if COMMENT_RATIO_OPTIMAL_MIN <= comment_ratio <= COMMENT_RATIO_OPTIMAL_MAX:
                scores.append(SCORE_EXCELLENT)
            elif COMMENT_RATIO_ACCEPTABLE_MIN <= comment_ratio <= COMMENT_RATIO_ACCEPTABLE_MAX:
                scores.append(SCORE_GOOD)
            elif comment_ratio <= COMMENT_RATIO_POOR_MAX:
                scores.append(SCORE_AVERAGE)
            else:
                scores.append(SCORE_POOR)

        if isinstance(avg_line_length, (int, float)) and avg_line_length > 0:
            # Optimal line length is around 80 characters
            if avg_line_length <= OPTIMAL_LINE_LENGTH:
                scores.append(SCORE_EXCELLENT)
            elif avg_line_length <= GOOD_LINE_LENGTH:
                scores.append(SCORE_GOOD)
            elif avg_line_length <= POOR_LINE_LENGTH:
                scores.append(SCORE_AVERAGE)
            else:
                scores.append(SCORE_POOR)

        if isinstance(naming_score, (int, float)) and 0 <= naming_score <= 10:
            scores.append(naming_score)

        return sum(scores) / len(scores) if scores else None

    @staticmethod
    def _score_reliability(metrics: Dict[str, Any]) -> Optional[float]:
        """Score reliability metrics.

        Args:
            metrics: Metrics dictionary

        Returns:
            Reliability score (0-10) or None
        """
        test_coverage = metrics.get("test_coverage")
        error_handling_ratio = metrics.get("error_handling_ratio")

        scores = []

        if isinstance(test_coverage, (int, float)) and 0 <= test_coverage <= 100:
            if test_coverage >= TEST_COVERAGE_EXCELLENT:
                scores.append(10.0)
            elif test_coverage >= TEST_COVERAGE_GOOD:
                scores.append(7.5)
            elif test_coverage >= TEST_COVERAGE_POOR:
                scores.append(5.0)
            else:
                scores.append(2.0)

        if isinstance(error_handling_ratio, (int, float)) and 0 <= error_handling_ratio <= 100:
            # Higher error handling ratio is better
            if error_handling_ratio >= 80:
                scores.append(10.0)
            elif error_handling_ratio >= 60:
                scores.append(7.5)
            elif error_handling_ratio >= 40:
                scores.append(5.0)
            else:
                scores.append(2.0)

        return sum(scores) / len(scores) if scores else None

    @staticmethod
    def _score_performance(metrics: Dict[str, Any]) -> Optional[float]:
        """Score performance-related metrics.

        Args:
            metrics: Metrics dictionary

        Returns:
            Performance score (0-10) or None
        """
        # Performance metrics are often context-dependent
        # For now, provide a neutral score if no specific metrics
        performance_issues = metrics.get("performance_issues", 0)

        if isinstance(performance_issues, int) and performance_issues >= 0:
            if performance_issues == 0:
                return 10.0
            elif performance_issues <= 2:
                return 7.5
            elif performance_issues <= 5:
                return 5.0
            else:
                return 2.0

        return None  # No performance data available

    @staticmethod
    def get_score_description(score: Union[int, float]) -> str:
        """Get human-readable description of quality score.

        Args:
            score: Quality score (0-10)

        Returns:
            Description string
        """
        if not isinstance(score, (int, float)):
            return "Invalid score"

        if score >= 9:
            return "Excellent"
        elif score >= 8:
            return "Very Good"
        elif score >= 7:
            return "Good"
        elif score >= 6:
            return "Above Average"
        elif score >= 5:
            return "Average"
        elif score >= 4:
            return "Below Average"
        elif score >= 3:
            return "Poor"
        elif score >= 2:
            return "Very Poor"
        else:
            return "Critical"
