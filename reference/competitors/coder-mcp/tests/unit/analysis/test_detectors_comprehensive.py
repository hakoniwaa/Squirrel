"""Comprehensive tests for the detectors module."""

import pytest

from coder_mcp.analysis.detectors.code_smells.coordinator import (
    CodeSmellDetector,
    SmellStatisticsCalculator,
)


class TestCodeSmellDetector:
    """Test CodeSmellDetector coordinator class."""

    @pytest.fixture
    def detector(self):
        """Create CodeSmellDetector instance."""
        return CodeSmellDetector()

    def test_initialization_default(self, detector):
        """Test default initialization."""
        assert len(detector.available_detectors) == 3
        assert "structural" in detector.available_detectors
        assert "quality" in detector.available_detectors
        assert "complexity" in detector.available_detectors
        assert len(detector.enabled_detectors) == 3
        assert isinstance(detector.statistics, SmellStatisticsCalculator)

    def test_initialization_with_enabled_detectors(self):
        """Test initialization with specific enabled detectors."""
        detector = CodeSmellDetector(enabled_detectors=["structural", "quality"])

        assert len(detector.enabled_detectors) == 2
        assert "structural" in detector.enabled_detectors
        assert "quality" in detector.enabled_detectors
        assert "complexity" not in detector.enabled_detectors

    def test_detect_code_smells_empty_content(self, detector, tmp_path):
        """Test code smell detection with empty content."""
        test_file = tmp_path / "empty.py"

        smells = detector.detect_code_smells("", test_file)

        assert smells == []

    def test_get_smell_statistics(self, detector):
        """Test getting smell statistics."""
        sample_smells = [
            {"type": "long_function", "severity": "high", "file": "test.py", "line": 1},
            {"type": "too_many_params", "severity": "medium", "file": "test.py", "line": 1},
            {"type": "deep_nesting", "severity": "high", "file": "other.py", "line": 5},
        ]

        stats = detector.get_smell_statistics(sample_smells)

        assert isinstance(stats, dict)
        assert stats["total_smells"] == 3
        assert stats["files_affected"] == 2
        assert "by_severity" in stats
        assert "by_type" in stats

    def test_get_available_smell_types(self, detector):
        """Test getting available smell types."""
        smell_types = detector.get_available_smell_types()

        assert isinstance(smell_types, dict)
        assert "structural" in smell_types
        assert "quality" in smell_types
        assert "complexity" in smell_types


class TestSmellStatisticsCalculator:
    """Test SmellStatisticsCalculator class."""

    @pytest.fixture
    def calculator(self):
        """Create SmellStatisticsCalculator instance."""
        return SmellStatisticsCalculator()

    def test_calculate_statistics_empty_smells(self, calculator):
        """Test statistics calculation with empty smell list."""
        stats = calculator.calculate_statistics([])

        assert stats["total_smells"] == 0
        assert stats["files_affected"] == 0
        assert stats["average_smells_per_file"] == 0.0
        assert stats["quality_score"] == 10.0
        assert stats["most_common_smell"] is None

    def test_calculate_quality_score_no_smells(self, calculator):
        """Test quality score calculation with no smells."""
        score = calculator._calculate_quality_score({}, 0)

        assert score == 10.0
