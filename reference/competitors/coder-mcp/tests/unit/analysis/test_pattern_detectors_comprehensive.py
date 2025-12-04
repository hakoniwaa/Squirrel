"""Comprehensive tests for pattern detection functionality."""

from pathlib import Path
from unittest.mock import patch

from coder_mcp.analysis.detectors.constants import (
    ConfidenceLevels,
    PatternDetectionConfig,
    SeverityLevels,
)
from coder_mcp.analysis.detectors.patterns.coordinator import PatternDetector


class TestPatternDetectorLogic:
    """Test PatternDetector coordinator logic without abstract class dependencies."""

    def test_post_process_patterns_empty(self):
        """Test post-processing with empty patterns."""
        # Test the post-processing logic directly without instantiating the coordinator
        # Create a mock detector just for accessing the methods
        with (
            patch("coder_mcp.analysis.detectors.patterns.coordinator.DesignPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.AntiPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.ArchitecturalPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.StructuralPatternDetector"),
        ):

            detector = PatternDetector()
            result = detector._post_process_patterns([])

            assert result == []

    def test_deduplicate_patterns_no_duplicates(self):
        """Test deduplication with no duplicates."""
        with (
            patch("coder_mcp.analysis.detectors.patterns.coordinator.DesignPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.AntiPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.ArchitecturalPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.StructuralPatternDetector"),
        ):

            detector = PatternDetector()

            sample_patterns = [
                {
                    "file": "test.py",
                    "pattern_name": "Singleton",
                    "start_line": 10,
                    "description": "First pattern",
                },
                {
                    "file": "test.py",
                    "pattern_name": "Factory",
                    "start_line": 20,
                    "description": "Second pattern",
                },
            ]

            result = detector._deduplicate_patterns(sample_patterns)

            assert len(result) == len(sample_patterns)

    def test_deduplicate_patterns_with_duplicates(self):
        """Test deduplication with duplicates."""
        with (
            patch("coder_mcp.analysis.detectors.patterns.coordinator.DesignPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.AntiPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.ArchitecturalPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.StructuralPatternDetector"),
        ):

            detector = PatternDetector()

            patterns_with_duplicates = [
                {
                    "file": "test.py",
                    "pattern_name": "Singleton",
                    "start_line": 10,
                    "description": "First instance",
                },
                {
                    "file": "test.py",
                    "pattern_name": "Singleton",
                    "start_line": 10,
                    "description": "Duplicate instance",
                },
                {
                    "file": "test.py",
                    "pattern_name": "Singleton",
                    "start_line": 20,
                    "description": "Different line",
                },
            ]

            result = detector._deduplicate_patterns(patterns_with_duplicates)

            assert len(result) == 2  # One duplicate removed

    def test_sort_patterns_by_severity(self):
        """Test sorting patterns by severity."""
        with (
            patch("coder_mcp.analysis.detectors.patterns.coordinator.DesignPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.AntiPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.ArchitecturalPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.StructuralPatternDetector"),
        ):

            detector = PatternDetector()

            patterns = [
                {"severity": SeverityLevels.LOW, "confidence": 0.5},
                {"severity": SeverityLevels.HIGH, "confidence": 0.5},
                {"severity": SeverityLevels.MEDIUM, "confidence": 0.5},
            ]

            result = detector._sort_patterns(patterns)

            # Should be sorted by severity (high to low)
            assert result[0]["severity"] == SeverityLevels.HIGH
            assert result[1]["severity"] == SeverityLevels.MEDIUM
            assert result[2]["severity"] == SeverityLevels.LOW

    def test_get_pattern_statistics_empty(self):
        """Test statistics generation with empty patterns."""
        with (
            patch("coder_mcp.analysis.detectors.patterns.coordinator.DesignPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.AntiPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.ArchitecturalPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.StructuralPatternDetector"),
        ):

            detector = PatternDetector()
            result = detector.get_pattern_statistics([])

            assert result["total_patterns"] == 0
            assert result["by_type"] == {}
            assert result["by_confidence"] == {}
            assert result["by_severity"] == {}
            assert result["files_affected"] == 0
            assert result["average_confidence"] == 0.0

    def test_get_pattern_statistics_with_patterns(self):
        """Test statistics generation with sample patterns."""
        with (
            patch("coder_mcp.analysis.detectors.patterns.coordinator.DesignPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.AntiPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.ArchitecturalPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.StructuralPatternDetector"),
        ):

            detector = PatternDetector()

            sample_patterns = [
                {
                    "pattern_name": "Singleton",
                    "pattern_type": "design",
                    "file": "test.py",
                    "start_line": 10,
                    "severity": SeverityLevels.HIGH,
                    "confidence": ConfidenceLevels.HIGH,
                },
                {
                    "pattern_name": "God Object",
                    "pattern_type": "anti_pattern",
                    "file": "controller.py",
                    "start_line": 50,
                    "severity": SeverityLevels.MEDIUM,
                    "confidence": ConfidenceLevels.MEDIUM,
                },
            ]

            result = detector.get_pattern_statistics(sample_patterns)

            assert result["total_patterns"] == 2
            assert result["files_affected"] == 2  # test.py and controller.py
            assert "design" in result["by_type"]
            assert "anti_pattern" in result["by_type"]
            assert result["average_confidence"] > 0

    def test_detect_patterns_empty_content(self):
        """Test pattern detection with empty content."""
        with (
            patch("coder_mcp.analysis.detectors.patterns.coordinator.DesignPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.AntiPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.ArchitecturalPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.StructuralPatternDetector"),
        ):

            detector = PatternDetector()
            test_file = Path("/tmp/empty.py")

            patterns = detector.detect_patterns("", test_file)

            assert patterns == []

    def test_detect_patterns_whitespace_only(self):
        """Test pattern detection with whitespace-only content."""
        with (
            patch("coder_mcp.analysis.detectors.patterns.coordinator.DesignPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.AntiPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.ArchitecturalPatternDetector"),
            patch("coder_mcp.analysis.detectors.patterns.coordinator.StructuralPatternDetector"),
        ):

            detector = PatternDetector()
            test_file = Path("/tmp/whitespace.py")

            patterns = detector.detect_patterns("   \n\t  \n", test_file)

            assert patterns == []


class TestPatternDetectionConfig:
    """Test PatternDetectionConfig class."""

    def test_config_creation(self):
        """Test creating configuration object."""
        config = PatternDetectionConfig()
        assert config is not None


class TestSeverityLevels:
    """Test SeverityLevels constants."""

    def test_severity_constants_exist(self):
        """Test that severity constants are defined."""
        assert hasattr(SeverityLevels, "HIGH")
        assert hasattr(SeverityLevels, "MEDIUM")
        assert hasattr(SeverityLevels, "LOW")


class TestConfidenceLevels:
    """Test ConfidenceLevels constants."""

    def test_confidence_constants_exist(self):
        """Test that confidence constants are defined."""
        assert hasattr(ConfidenceLevels, "HIGH")
        assert hasattr(ConfidenceLevels, "MEDIUM")
        assert hasattr(ConfidenceLevels, "LOW")
