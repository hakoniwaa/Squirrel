"""
Code quality metrics calculation

This module calculates various code quality metrics including:
- Maintainability Index
- Technical Debt Ratio
- Test Coverage Impact
- Code Duplication Analysis
- Overall Quality Scores
"""

import math
from enum import Enum
from typing import Any, Dict, List, Tuple


class QualityRating(Enum):
    """Quality rating levels"""

    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"
    VERY_POOR = "very_poor"
    DIFFICULT = "difficult"
    UNMAINTAINABLE = "unmaintainable"
    HIGH = "high"
    VERY_HIGH = "very_high"
    UNKNOWN = "unknown"


class QualityThresholds:
    """Thresholds for various quality metrics based on industry standards"""

    # Base scale units for metric calculations
    _BASE_SCALE = 10
    _PERCENTAGE_SCALE = 100

    # Maintainability Index thresholds (based on Microsoft's original research)
    # Microsoft's MI scale: 0-9 (unmaintainable), 10-19 (difficult), 20-49 (moderate),
    # 50-100 (maintainable)
    MAINTAINABILITY_EXCELLENT = 85  # Industry best practice threshold
    MAINTAINABILITY_GOOD = 70  # Good maintainability threshold
    MAINTAINABILITY_MODERATE = 50  # Acceptable maintainability
    MAINTAINABILITY_DIFFICULT = 25  # Requires attention
    MAINTAINABILITY_UNMAINTAINABLE = 0

    # Technical Debt Ratio thresholds (percentage based on SQALE methodology)
    # SQALE ratings: A=<=5%, B=6-10%, C=11-20%, D=21-50%, E=>50%
    TECH_DEBT_EXCELLENT = 5  # SQALE rating A
    TECH_DEBT_GOOD = 10  # SQALE rating B
    TECH_DEBT_MODERATE = 20  # SQALE rating C
    TECH_DEBT_HIGH = 50  # SQALE rating D

    # Test Coverage thresholds (based on industry research)
    # Google's recommendation: 90%+, Industry average: 70-80%
    COVERAGE_EXCELLENT = 90  # Google's internal standard
    COVERAGE_GOOD = 80  # Industry best practice
    COVERAGE_MODERATE = 70  # Acceptable minimum
    COVERAGE_POOR = 50  # Below industry average

    # Code Duplication thresholds (based on SonarQube standards)
    # SonarQube default rules: >3% is bad, >5% is very bad
    DUPLICATION_EXCELLENT = 3  # SonarQube acceptable threshold
    DUPLICATION_GOOD = 5  # SonarQube warning threshold
    DUPLICATION_MODERATE = 10  # Needs attention
    DUPLICATION_HIGH = 20  # Critical issue

    # Overall Quality Score thresholds (industry standard grading)
    OVERALL_EXCELLENT = 90  # A grade
    OVERALL_GOOD = 80  # B grade
    OVERALL_MODERATE = 70  # C grade
    OVERALL_POOR = 50  # D grade

    # Small file threshold (lines) - below this, different heuristics apply
    SMALL_FILE_LINES = 10


class TechnicalDebtEstimation:
    """Technical debt estimation based on industry research and empirical data"""

    # Time estimates based on "Clean Code" principles and industry studies
    # Source: "Technical Debt: From Metaphor to Theory and Practice" (Avgeriou et al.)

    # Issue remediation times (minutes) - derived from industry bug fix studies
    SIMPLE_ISSUE_MINUTES = 5  # Simple issues (missing docs, style)
    MODERATE_ISSUE_MINUTES = 15  # Moderate issues (refactoring, testing)
    COMPLEX_ISSUE_MINUTES = 45  # Complex issues (architectural changes)
    AVERAGE_ISSUE_MINUTES = 15  # Weighted average for mixed issue types

    # Complexity-based time estimates (minutes per complexity point)
    # Source: Software Engineering Institute complexity studies
    MINUTES_PER_COMPLEXITY_POINT = 2  # Time to understand/modify per complexity unit

    # Development velocity estimates (lines per minute)
    # Source: "Code Complete" by Steve McConnell - industry averages
    LINES_PER_MINUTE_DEVELOPMENT = 2.5  # Conservative estimate for quality code

    # Threshold for complexity-based debt calculation
    COMPLEXITY_DEBT_THRESHOLD = 10  # Above this, complexity significantly impacts debt


class MaintainabilityConstants:
    """Constants for Maintainability Index calculation"""

    # MI = 171 - 5.2 * ln(V) - 0.23 * C - 16.2 * ln(LOC)
    BASE_VALUE = float(171)  # Microsoft's original MI base value
    HALSTEAD_COEFFICIENT = 5.2  # Empirically derived coefficient
    COMPLEXITY_COEFFICIENT = 0.23  # Complexity weight in MI formula
    LOC_COEFFICIENT = 16.2  # Lines of code weight in MI formula

    # Defaults for missing metrics
    DEFAULT_HALSTEAD_VOLUME = float(QualityThresholds._BASE_SCALE * 5)  # 50.0
    DEFAULT_MIN_VALUE = 1  # To avoid log(0)

    # Small file adjustments
    SMALL_FILE_BASE_SCORE = float(QualityThresholds.MAINTAINABILITY_EXCELLENT)  # 85.0
    SMALL_FILE_COMPLEXITY_THRESHOLD = QualityThresholds._BASE_SCALE // 2  # 5
    SMALL_FILE_COMPLEXITY_PENALTY = QualityThresholds._BASE_SCALE  # 10

    # Score bounds
    MIN_SCORE = 0.0
    MAX_SCORE = float(QualityThresholds._PERCENTAGE_SCALE)  # 100.0
    FALLBACK_SCORE = float(QualityThresholds.MAINTAINABILITY_MODERATE)  # 50.0


class QualityWeights:
    """Weights for overall quality score calculation"""

    MAINTAINABILITY = 0.4
    TEST_COVERAGE = 0.3
    TECHNICAL_DEBT = 0.2
    DUPLICATION = 0.1


class RecommendationConstants:
    """Constants for quality recommendations"""

    # Threshold adjustments for recommendations
    OVERALL_FOCUS_THRESHOLD = 10  # Below (OVERALL_MODERATE - 10)

    # Recommendation messages
    MAINTAINABILITY_MSG = (
        "🔧 Improve maintainability by reducing complexity and breaking down large functions"
    )
    TECH_DEBT_MSG = "⚡ Address technical debt by fixing code smells and reducing complexity"
    OVERALL_FOCUS_MSG = (
        "🎯 Focus on the highest impact improvements: tests, complexity reduction, and code cleanup"
    )

    # Template messages
    TEST_COVERAGE_TEMPLATE = "🧪 Increase test coverage from {current:.1f}% to at least {target}%"
    DUPLICATION_TEMPLATE = (
        "📋 Reduce code duplication from {current:.1f}% by extracting common functionality"
    )


class QualityMetricsCalculator:
    """Calculate various code quality metrics"""

    def __init__(self) -> None:
        self.quality_rules = self._build_quality_rules()
        self.recommendation_checker = RecommendationChecker()

    def _build_quality_rules(self) -> Dict[str, Dict[str, Tuple[float, float]]]:
        """Build quality rating rules"""
        return {
            "maintainability_index": {
                QualityRating.EXCELLENT.value: (
                    QualityThresholds.MAINTAINABILITY_EXCELLENT,
                    MaintainabilityConstants.MAX_SCORE,
                ),
                QualityRating.GOOD.value: (
                    QualityThresholds.MAINTAINABILITY_GOOD,
                    QualityThresholds.MAINTAINABILITY_EXCELLENT - 1,
                ),
                QualityRating.MODERATE.value: (
                    QualityThresholds.MAINTAINABILITY_MODERATE,
                    QualityThresholds.MAINTAINABILITY_GOOD - 1,
                ),
                QualityRating.DIFFICULT.value: (
                    QualityThresholds.MAINTAINABILITY_DIFFICULT,
                    QualityThresholds.MAINTAINABILITY_MODERATE - 1,
                ),
                QualityRating.UNMAINTAINABLE.value: (
                    QualityThresholds.MAINTAINABILITY_UNMAINTAINABLE,
                    QualityThresholds.MAINTAINABILITY_DIFFICULT - 1,
                ),
            },
            "technical_debt_ratio": {
                QualityRating.EXCELLENT.value: (0, QualityThresholds.TECH_DEBT_EXCELLENT),
                QualityRating.GOOD.value: (
                    QualityThresholds.TECH_DEBT_EXCELLENT,
                    QualityThresholds.TECH_DEBT_GOOD,
                ),
                QualityRating.MODERATE.value: (
                    QualityThresholds.TECH_DEBT_GOOD,
                    QualityThresholds.TECH_DEBT_MODERATE,
                ),
                QualityRating.HIGH.value: (
                    QualityThresholds.TECH_DEBT_MODERATE,
                    QualityThresholds.TECH_DEBT_HIGH,
                ),
                QualityRating.VERY_HIGH.value: (QualityThresholds.TECH_DEBT_HIGH, float("inf")),
            },
        }

    def calculate_quality_score(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall quality score from various metrics

        Args:
            metrics: Dictionary containing code metrics

        Returns:
            Dictionary containing quality scores and ratings
        """
        scores: Dict[str, Any] = {}
        float_scores: Dict[str, float] = {}

        # Calculate maintainability index
        maintainability = float(self._calculate_maintainability_index(metrics))
        scores["maintainability_index"] = maintainability
        float_scores["maintainability_index"] = maintainability
        scores["maintainability_rating"] = self._get_quality_rating(
            maintainability, "maintainability_index"
        )

        # Calculate technical debt ratio
        tech_debt = float(self._calculate_technical_debt_ratio(metrics))
        scores["technical_debt_ratio"] = tech_debt
        float_scores["technical_debt_ratio"] = tech_debt
        scores["technical_debt_rating"] = self._get_quality_rating(
            tech_debt, "technical_debt_ratio"
        )

        # Calculate code coverage impact
        test_coverage = float(metrics.get("test_coverage", 0))
        scores["test_coverage"] = test_coverage
        float_scores["test_coverage"] = test_coverage
        scores["test_coverage_impact"] = self._calculate_coverage_impact(test_coverage)

        # Calculate duplication percentage
        duplication = float(self._calculate_duplication_percentage(metrics))
        scores["duplication_percentage"] = duplication
        float_scores["duplication_percentage"] = duplication
        scores["duplication_impact"] = self._calculate_duplication_impact(duplication)

        # Calculate overall quality score (weighted average)
        overall_score = float(self._calculate_overall_score(float_scores))
        scores["overall_quality_score"] = overall_score
        float_scores["overall_quality_score"] = overall_score
        scores["overall_quality_rating"] = self._get_overall_rating(overall_score)

        return scores

    def _calculate_maintainability_index(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate maintainability index using Halstead metrics and cyclomatic complexity

        Formula: MI = 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity)
        - 16.2 * ln(Lines of Code)

        Args:
            metrics: Code metrics dictionary

        Returns:
            Maintainability index value (0-100)
        """
        # Get required metrics with defaults to avoid log(0)
        lines_of_code = max(
            metrics.get("lines_of_code", MaintainabilityConstants.DEFAULT_MIN_VALUE),
            MaintainabilityConstants.DEFAULT_MIN_VALUE,
        )
        cyclomatic_complexity = max(
            metrics.get("cyclomatic_complexity", MaintainabilityConstants.DEFAULT_MIN_VALUE),
            MaintainabilityConstants.DEFAULT_MIN_VALUE,
        )
        halstead_volume = max(
            metrics.get("halstead_volume", MaintainabilityConstants.DEFAULT_HALSTEAD_VOLUME),
            MaintainabilityConstants.DEFAULT_MIN_VALUE,
        )

        # Special handling for very small files
        if lines_of_code < QualityThresholds.SMALL_FILE_LINES:
            return self._calculate_small_file_maintainability(cyclomatic_complexity)

        # Calculate maintainability index
        try:
            mi = (
                MaintainabilityConstants.BASE_VALUE
                - MaintainabilityConstants.HALSTEAD_COEFFICIENT * math.log(halstead_volume)
                - MaintainabilityConstants.COMPLEXITY_COEFFICIENT * cyclomatic_complexity
                - MaintainabilityConstants.LOC_COEFFICIENT * math.log(lines_of_code)
            )
            return float(
                max(MaintainabilityConstants.MIN_SCORE, min(MaintainabilityConstants.MAX_SCORE, mi))
            )
        except (ValueError, OverflowError):
            return float(MaintainabilityConstants.FALLBACK_SCORE)

    def _calculate_small_file_maintainability(self, cyclomatic_complexity: int) -> float:
        """Calculate maintainability for small files"""
        base_score = MaintainabilityConstants.SMALL_FILE_BASE_SCORE

        if cyclomatic_complexity > MaintainabilityConstants.SMALL_FILE_COMPLEXITY_THRESHOLD:
            complexity_penalty = (
                cyclomatic_complexity - MaintainabilityConstants.SMALL_FILE_COMPLEXITY_THRESHOLD
            ) * MaintainabilityConstants.SMALL_FILE_COMPLEXITY_PENALTY
            base_score -= complexity_penalty

        return float(
            max(
                MaintainabilityConstants.FALLBACK_SCORE,
                min(MaintainabilityConstants.MAX_SCORE, base_score),
            )
        )

    def _calculate_technical_debt_ratio(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate technical debt ratio as percentage using empirical estimation

        Args:
            metrics: Code metrics dictionary

        Returns:
            Technical debt ratio (0-100)
        """
        issues_count = len(metrics.get("issues", []))
        lines_of_code = max(metrics.get("lines_of_code", 1), 1)
        complexity = max(metrics.get("cyclomatic_complexity", 1), 1)

        # Handle edge case: if no lines of code, return 0 debt
        if lines_of_code <= 1 and issues_count == 0:
            return 0.0

        # Estimate remediation effort (in minutes) using empirical data
        issue_effort = issues_count * TechnicalDebtEstimation.AVERAGE_ISSUE_MINUTES

        # Add complexity-based effort only for high complexity code
        complexity_effort = 0
        if complexity > TechnicalDebtEstimation.COMPLEXITY_DEBT_THRESHOLD:
            excess_complexity = complexity - TechnicalDebtEstimation.COMPLEXITY_DEBT_THRESHOLD
            complexity_effort = (
                excess_complexity * TechnicalDebtEstimation.MINUTES_PER_COMPLEXITY_POINT
            )

        total_remediation_effort = issue_effort + complexity_effort

        # Development time estimate using empirical velocity
        development_time = lines_of_code / TechnicalDebtEstimation.LINES_PER_MINUTE_DEVELOPMENT

        # Technical debt ratio = remediation effort / development time * 100
        if development_time > 0:
            ratio = (total_remediation_effort / development_time) * 100
            return float(min(100, max(0, ratio)))  # Ensure it's between 0 and 100
        return 0.0

    def _calculate_coverage_impact(self, coverage: float) -> str:
        """Calculate the impact of test coverage on quality"""
        if coverage >= QualityThresholds.COVERAGE_EXCELLENT:
            return QualityRating.EXCELLENT.value
        elif coverage >= QualityThresholds.COVERAGE_GOOD:
            return QualityRating.GOOD.value
        elif coverage >= QualityThresholds.COVERAGE_MODERATE:
            return QualityRating.MODERATE.value
        elif coverage >= QualityThresholds.COVERAGE_POOR:
            return QualityRating.POOR.value
        else:
            return QualityRating.VERY_POOR.value

    def _calculate_duplication_percentage(self, metrics: Dict[str, Any]) -> float:
        """Calculate code duplication percentage"""
        duplicate_lines = float(metrics.get("duplicate_lines", 0))
        total_lines = float(max(metrics.get("lines_of_code", 1), 1))
        return (duplicate_lines / total_lines) * 100

    def _calculate_duplication_impact(self, duplication_pct: float) -> str:
        """Calculate the impact of code duplication"""
        if duplication_pct <= QualityThresholds.DUPLICATION_EXCELLENT:
            return QualityRating.EXCELLENT.value
        elif duplication_pct <= QualityThresholds.DUPLICATION_GOOD:
            return QualityRating.GOOD.value
        elif duplication_pct <= QualityThresholds.DUPLICATION_MODERATE:
            return QualityRating.MODERATE.value
        elif duplication_pct <= QualityThresholds.DUPLICATION_HIGH:
            return QualityRating.HIGH.value
        else:
            return QualityRating.VERY_HIGH.value

    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        weighted_sum = 0.0
        total_weight = 0.0

        maintainability: float = (
            scores["maintainability_index"]
            if "maintainability_index" in scores
            else float(MaintainabilityConstants.FALLBACK_SCORE)
        )
        weighted_sum += maintainability * QualityWeights.MAINTAINABILITY
        total_weight += QualityWeights.MAINTAINABILITY

        test_coverage: float = scores["test_coverage"] if "test_coverage" in scores else 0.0
        weighted_sum += test_coverage * QualityWeights.TEST_COVERAGE
        total_weight += QualityWeights.TEST_COVERAGE

        tech_debt: float = (
            scores["technical_debt_ratio"]
            if "technical_debt_ratio" in scores
            else float(QualityThresholds.TECH_DEBT_HIGH)
        )
        tech_debt_score = max(0, 100 - tech_debt)
        weighted_sum += tech_debt_score * QualityWeights.TECHNICAL_DEBT
        total_weight += QualityWeights.TECHNICAL_DEBT

        duplication: float = (
            scores["duplication_percentage"]
            if "duplication_percentage" in scores
            else float(QualityThresholds.DUPLICATION_MODERATE)
        )
        duplication_score = max(0, 100 - duplication)
        weighted_sum += duplication_score * QualityWeights.DUPLICATION
        total_weight += QualityWeights.DUPLICATION

        result = float(weighted_sum / total_weight) if total_weight > 0 else 0.0
        return result  # type: ignore[no-any-return]

    def _get_quality_rating(self, score: float, metric_type: str) -> str:
        """Get quality rating for a specific metric"""
        rules = self.quality_rules.get(metric_type, {})

        for rating, (min_val, max_val) in rules.items():
            if min_val <= score <= max_val:
                return rating

        return QualityRating.UNKNOWN.value

    def _get_overall_rating(self, score: float) -> str:
        """Get overall quality rating"""
        if score >= QualityThresholds.OVERALL_EXCELLENT:
            return QualityRating.EXCELLENT.value
        elif score >= QualityThresholds.OVERALL_GOOD:
            return QualityRating.GOOD.value
        elif score >= QualityThresholds.OVERALL_MODERATE:
            return QualityRating.MODERATE.value
        elif score >= QualityThresholds.OVERALL_POOR:
            return QualityRating.POOR.value
        else:
            return QualityRating.VERY_POOR.value

    def get_quality_recommendations(self, scores: Dict[str, Any]) -> List[str]:
        """
        Get recommendations based on quality scores

        Args:
            scores: Dictionary of quality scores

        Returns:
            List of improvement recommendations
        """
        return self.recommendation_checker.get_recommendations(scores)


class RecommendationChecker:
    """Handles quality recommendation logic"""

    def get_recommendations(self, scores: Dict[str, Any]) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations: list[str] = []

        # Check each quality aspect
        self._check_maintainability(scores, recommendations)
        self._check_test_coverage(scores, recommendations)
        self._check_technical_debt(scores, recommendations)
        self._check_duplication(scores, recommendations)
        self._check_overall_quality(scores, recommendations)

        return recommendations

    def _check_maintainability(self, scores: Dict[str, Any], recommendations: List[str]) -> None:
        """Check maintainability and add recommendations if needed"""
        maintainability = scores.get(
            "maintainability_index", MaintainabilityConstants.FALLBACK_SCORE
        )
        if maintainability < QualityThresholds.MAINTAINABILITY_MODERATE:
            recommendations.append(RecommendationConstants.MAINTAINABILITY_MSG)

    def _check_test_coverage(self, scores: Dict[str, Any], recommendations: List[str]) -> None:
        """Check test coverage and add recommendations if needed"""
        test_coverage = scores.get("test_coverage", 0)
        if test_coverage < QualityThresholds.COVERAGE_MODERATE:
            message = RecommendationConstants.TEST_COVERAGE_TEMPLATE.format(
                current=test_coverage, target=QualityThresholds.COVERAGE_MODERATE
            )
            recommendations.append(message)

    def _check_technical_debt(self, scores: Dict[str, Any], recommendations: List[str]) -> None:
        """Check technical debt and add recommendations if needed"""
        tech_debt = scores.get("technical_debt_ratio", 0)
        if tech_debt > QualityThresholds.TECH_DEBT_MODERATE:
            recommendations.append(RecommendationConstants.TECH_DEBT_MSG)

    def _check_duplication(self, scores: Dict[str, Any], recommendations: List[str]) -> None:
        """Check code duplication and add recommendations if needed"""
        duplication = scores.get("duplication_percentage", 0)
        if duplication > QualityThresholds.DUPLICATION_GOOD:
            message = RecommendationConstants.DUPLICATION_TEMPLATE.format(current=duplication)
            recommendations.append(message)

    def _check_overall_quality(self, scores: Dict[str, Any], recommendations: List[str]) -> None:
        """Check overall quality and add recommendations if needed"""
        overall = scores.get("overall_quality_score", QualityThresholds.OVERALL_POOR)
        threshold = (
            QualityThresholds.OVERALL_MODERATE - RecommendationConstants.OVERALL_FOCUS_THRESHOLD
        )

        if overall < threshold:
            recommendations.append(RecommendationConstants.OVERALL_FOCUS_MSG)
