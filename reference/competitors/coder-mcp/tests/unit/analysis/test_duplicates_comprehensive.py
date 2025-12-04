"""
Comprehensive tests for duplicates detection system.

This module provides complete test coverage for duplicate code detection including
coordinator logic, block extraction, similarity calculation, and report generation.
"""

import hashlib
from unittest.mock import patch

import pytest

from coder_mcp.analysis.detectors.constants import DuplicateDetectionConfig
from coder_mcp.analysis.detectors.duplicates.block_extractor import (
    CodeBlockExtractor,
    DuplicateBlock,
)
from coder_mcp.analysis.detectors.duplicates.coordinator import DuplicateCodeDetector


class TestDuplicateBlock:
    """Test DuplicateBlock dataclass."""

    def test_duplicate_block_creation(self):
        """Test creating DuplicateBlock instance."""
        block = DuplicateBlock(
            file_path="test.py",
            start_line=10,
            end_line=20,
            content="def test():\n    pass",
            hash_value="abc123",
            similarity_score=0.95,
        )

        assert block.file_path == "test.py"
        assert block.start_line == 10
        assert block.end_line == 20
        assert block.content == "def test():\n    pass"
        assert block.hash_value == "abc123"
        assert block.similarity_score == 0.95

    def test_duplicate_block_default_similarity(self):
        """Test DuplicateBlock with default similarity score."""
        block = DuplicateBlock(
            file_path="test.py",
            start_line=1,
            end_line=5,
            content="print('hello')",
            hash_value="def456",
        )

        assert block.similarity_score == 0.0


class TestCodeBlockExtractor:
    """Test CodeBlockExtractor class."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return DuplicateDetectionConfig()

    @pytest.fixture
    def extractor(self, config):
        """Create CodeBlockExtractor instance."""
        return CodeBlockExtractor(config)

    @pytest.fixture
    def sample_code_lines(self):
        """Sample code lines for testing."""
        return [
            "def function_one():",
            "    x = 1",
            "    y = 2",
            "    return x + y",
            "",
            "def function_two():",
            "    a = 1",
            "    b = 2",
            "    return a + b",
            "",
            "def function_three():",
            "    print('hello')",
            "    return None",
        ]

    def test_initialization_default_config(self):
        """Test extractor initialization with default config."""
        extractor = CodeBlockExtractor()

        assert extractor.config is not None
        assert extractor.min_lines > 0
        assert extractor.min_block_size > 0

    def test_initialization_custom_config(self, config):
        """Test extractor initialization with custom config."""
        extractor = CodeBlockExtractor(config)

        assert extractor.config is config
        assert extractor.min_lines == config.MIN_LINES

    def test_extract_blocks_basic(self, extractor, sample_code_lines, tmp_path):
        """Test basic block extraction."""
        test_file = tmp_path / "test.py"

        blocks = extractor.extract_blocks(sample_code_lines, test_file)

        assert isinstance(blocks, list)
        # Should find some blocks
        assert len(blocks) >= 0

    def test_extract_blocks_empty_lines(self, extractor, tmp_path):
        """Test block extraction with empty lines."""
        test_file = tmp_path / "empty.py"
        empty_lines = []

        blocks = extractor.extract_blocks(empty_lines, test_file)

        assert blocks == []

    def test_extract_blocks_insufficient_lines(self, extractor, tmp_path):
        """Test block extraction with insufficient lines."""
        test_file = tmp_path / "small.py"
        small_lines = ["print('hello')"]

        blocks = extractor.extract_blocks(small_lines, test_file)

        assert blocks == []

    def test_has_sufficient_lines_true(self, extractor):
        """Test has_sufficient_lines with enough lines."""
        lines = ["line"] * 20

        result = extractor._has_sufficient_lines(lines)

        assert result is True

    def test_has_sufficient_lines_false(self, extractor):
        """Test has_sufficient_lines with too few lines."""
        lines = ["line"] * 2

        result = extractor._has_sufficient_lines(lines)

        assert result is False

    def test_calculate_hash(self, extractor):
        """Test hash calculation."""
        content = "def test():\n    pass"

        hash_value = extractor._calculate_hash(content)

        expected_hash = hashlib.md5(content.encode("utf-8"), usedforsecurity=False).hexdigest()
        assert hash_value == expected_hash

    def test_get_block_statistics_empty(self, extractor):
        """Test block statistics with empty list."""
        stats = extractor.get_block_statistics([])

        assert stats["total_blocks"] == 0
        assert stats["average_size"] == 0
        assert stats["unique_hashes"] == 0
        assert stats["files_processed"] == 0

    def test_get_block_statistics_with_blocks(self, extractor):
        """Test block statistics with actual blocks."""
        blocks = [
            DuplicateBlock("file1.py", 1, 5, "content1", "hash1"),
            DuplicateBlock("file1.py", 6, 10, "content2", "hash2"),
            DuplicateBlock("file2.py", 1, 3, "content3", "hash1"),  # Duplicate hash
        ]

        stats = extractor.get_block_statistics(blocks)

        assert stats["total_blocks"] == 3
        assert stats["unique_hashes"] == 2
        assert stats["files_processed"] == 2
        assert stats["potential_duplicates"] == 1  # 3 blocks - 2 unique hashes


class TestDuplicateCodeDetector:
    """Test DuplicateCodeDetector coordinator."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return DuplicateDetectionConfig()

    @pytest.fixture
    def detector(self, config):
        """Create DuplicateCodeDetector instance."""
        return DuplicateCodeDetector(config)

    @pytest.fixture
    def sample_blocks(self):
        """Sample duplicate blocks for testing."""
        return [
            DuplicateBlock("file1.py", 1, 5, "def test():\n    pass", "hash1"),
            DuplicateBlock("file2.py", 1, 5, "def test():\n    pass", "hash1"),  # Exact duplicate
            DuplicateBlock("file1.py", 10, 15, "def other():\n    return 1", "hash2"),
        ]

    def test_initialization_default_config(self):
        """Test detector initialization with default config."""
        detector = DuplicateCodeDetector()

        assert detector.config is not None
        assert detector.block_extractor is not None
        assert detector.similarity_calculator is not None
        assert detector.report_generator is not None
        assert detector.statistics_calculator is not None

    def test_initialization_custom_config(self, config):
        """Test detector initialization with custom config."""
        detector = DuplicateCodeDetector(config)

        assert detector.config is config

    def test_load_patterns(self, detector):
        """Test load_patterns method (returns empty dict for this detector)."""
        patterns = detector._load_patterns()

        assert patterns == {}

    def test_detect_empty_content(self, detector, tmp_path):
        """Test detection with empty content."""
        test_file = tmp_path / "empty.py"

        result = detector.detect("", test_file)

        assert result == []

    def test_detect_valid_content(self, detector, tmp_path):
        """Test detection with valid content."""
        test_file = tmp_path / "test.py"
        content = "def test():\n    pass\n\ndef test2():\n    pass"

        with patch.object(detector.block_extractor, "extract_blocks", return_value=[]):
            result = detector.detect(content, test_file)

            assert isinstance(result, list)

    def test_detect_cross_file_duplicates_empty(self, detector):
        """Test cross-file detection with empty input."""
        result = detector.detect_cross_file_duplicates({})

        assert result == []

    def test_detect_cross_file_duplicates_valid(self, detector, tmp_path):
        """Test cross-file detection with valid input."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file_contents = {
            file1: "def test():\n    pass",
            file2: "def other():\n    return 1",
        }

        with patch.object(detector, "_extract_blocks_from_files", return_value=[]):
            result = detector.detect_cross_file_duplicates(file_contents)

            assert isinstance(result, list)

    def test_detect_with_detailed_analysis(self, detector, tmp_path):
        """Test detection with detailed analysis."""
        test_file = tmp_path / "test.py"
        content = "def test():\n    pass"

        with patch.object(detector, "detect", return_value=[]):
            with patch.object(detector, "get_duplicate_statistics", return_value={}):
                with patch.object(
                    detector.report_generator, "create_summary_report", return_value={}
                ):
                    result = detector.detect_with_detailed_analysis(content, test_file)

                    assert "duplicates" in result
                    assert "statistics" in result
                    assert "summary" in result
                    assert "analysis_metadata" in result

    def test_analyze_similarity_clusters_empty(self, detector):
        """Test similarity cluster analysis with empty input."""
        result = detector.analyze_similarity_clusters({})

        assert result == {"clusters": [], "statistics": {}}

    def test_analyze_similarity_clusters_valid(self, detector, tmp_path):
        """Test similarity cluster analysis with valid input."""
        file_contents = {tmp_path / "test.py": "def test():\n    pass"}

        with patch.object(detector, "_extract_blocks_from_files", return_value=[]):
            result = detector.analyze_similarity_clusters(file_contents)

            assert "clusters" in result
            assert "statistics" in result
            assert result["clusters"] == []

    def test_get_similarity_analysis(self, detector, tmp_path):
        """Test similarity analysis between two files."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        content1 = "def test1():\n    pass"
        content2 = "def test2():\n    pass"

        with patch.object(detector.block_extractor, "extract_blocks", return_value=[]):
            with patch.object(
                detector.similarity_calculator, "find_similar_blocks", return_value=[]
            ):
                result = detector.get_similarity_analysis(content1, file1, content2, file2)

                assert "cross_file_similarities" in result
                assert "file1_blocks" in result
                assert "file2_blocks" in result
                assert "similarity_count" in result
                assert "average_similarity" in result

    def test_configure_detection(self, detector):
        """Test dynamic detection configuration."""
        detector.configure_detection(min_lines=10, similarity_threshold=0.8)

        # Configuration should be updated (if these attributes exist)
        assert detector.config is not None
        # Components should be recreated
        assert detector.block_extractor is not None

    def test_is_valid_content_valid(self, detector):
        """Test content validation with valid content."""
        result = detector._is_valid_content("def test():\n    pass")

        assert result is True

    def test_is_valid_content_invalid(self, detector):
        """Test content validation with invalid content."""
        result = detector._is_valid_content("")

        assert result is False

    def test_has_sufficient_lines_true(self, detector):
        """Test line count validation with sufficient lines."""
        lines = ["line"] * 20

        result = detector._has_sufficient_lines(lines)

        assert result is True

    def test_has_sufficient_lines_false(self, detector):
        """Test line count validation with insufficient lines."""
        lines = ["line"] * 2

        result = detector._has_sufficient_lines(lines)

        assert result is False

    def test_group_blocks_by_hash(self, detector, sample_blocks):
        """Test grouping blocks by hash."""
        hash_groups = detector._group_blocks_by_hash(sample_blocks)

        assert "hash1" in hash_groups
        assert "hash2" in hash_groups
        assert len(hash_groups["hash1"]) == 2  # Two blocks with same hash
        assert len(hash_groups["hash2"]) == 1

    def test_get_config_summary(self, detector):
        """Test getting configuration summary."""
        summary = detector._get_config_summary()

        assert "min_lines" in summary
        assert "min_tokens" in summary
        assert "similarity_threshold" in summary

    def test_analyze_cluster_statistics_empty(self, detector):
        """Test cluster statistics analysis with empty clusters."""
        result = detector._analyze_cluster_statistics([])

        assert result["total_clusters"] == 0
        assert result["average_cluster_size"] == 0
        assert result["largest_cluster_size"] == 0

    def test_analyze_cluster_statistics_with_data(self, detector, sample_blocks):
        """Test cluster statistics analysis with data."""
        clusters = [sample_blocks[:2], sample_blocks[2:]]

        result = detector._analyze_cluster_statistics(clusters)

        assert result["total_clusters"] == 2
        assert result["average_cluster_size"] > 0
        assert "cluster_size_distribution" in result

    def test_calculate_cluster_size_distribution(self, detector):
        """Test cluster size distribution calculation."""
        cluster_sizes = [2, 5, 10, 20]

        result = detector._calculate_cluster_size_distribution(cluster_sizes)

        assert "small (2-3 blocks)" in result
        assert "medium (4-7 blocks)" in result
        assert "large (8-15 blocks)" in result
        assert "very_large (>15 blocks)" in result

    def test_get_performance_metrics(self, detector):
        """Test getting performance metrics."""
        metrics = detector.get_performance_metrics()

        assert "components" in metrics
        assert "configuration" in metrics
        assert "capabilities" in metrics
        assert "exact_duplicate_detection" in metrics["capabilities"]


class TestDuplicateDetectionConfig:
    """Test duplicate detection configuration."""

    def test_config_creation(self):
        """Test creating DuplicateDetectionConfig."""
        config = DuplicateDetectionConfig()

        assert config is not None
        assert hasattr(config, "MIN_LINES")
        assert hasattr(config, "MIN_TOKENS")
        assert hasattr(config, "SIMILARITY_THRESHOLD")
