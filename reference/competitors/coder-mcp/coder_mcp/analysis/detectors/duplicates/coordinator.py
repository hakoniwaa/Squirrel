"""
Duplicate code detection coordinator - orchestrates specialized components using composition
"""

from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import BaseDetector, DetectionContext
from ..constants import DuplicateDetectionConfig
from .block_extractor import CodeBlockExtractor, DuplicateBlock
from .report_generator import DuplicateReportGenerator
from .similarity_calculator import SimilarityCalculator
from .statistics_calculator import DuplicateStatisticsCalculator


class DuplicateCodeDetector(BaseDetector):
    """
    Main coordinator for duplicate code detection using composition and strategy pattern.

    This class delegates to specialized components instead of doing everything itself,
    following the Single Responsibility Principle and Composition over Inheritance.
    """

    def __init__(self, config: Optional[DuplicateDetectionConfig] = None):
        """
        Initialize duplicate detector with configurable components.

        Args:
            config: Configuration for duplicate detection parameters
        """
        super().__init__()
        self.config = config or DuplicateDetectionConfig()

        # Initialize specialized components using composition
        self.block_extractor = CodeBlockExtractor(self.config)
        self.similarity_calculator = SimilarityCalculator(self.config)
        self.report_generator = DuplicateReportGenerator(self.config)
        self.statistics_calculator = DuplicateStatisticsCalculator(self.config)

    def _load_patterns(self) -> Dict[str, Any]:
        """Load patterns - not used for this detector type"""
        return {}

    def detect(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Detect duplicate code blocks within a file"""
        try:
            context = self.create_context(content, file_path)

            if not self._is_valid_context(context):
                return []

            # Extract and analyze code blocks using specialized components
            # Guard against None context.lines
            if not context.lines:
                return []
            code_blocks = self.block_extractor.extract_blocks(context.lines, context.file_path)

            if not code_blocks:
                return []

            return self._find_all_duplicates(code_blocks)
        except Exception as e:
            self.logger.error(f"Duplicate detection failed for {file_path}: {e}")
            return []

    def detect_cross_file_duplicates(self, file_contents: Dict[Path, str]) -> List[Dict[str, Any]]:
        """Detect duplicate code blocks across multiple files"""
        if not file_contents:
            return []

        all_blocks = self._extract_blocks_from_files(file_contents)

        if not all_blocks:
            return []

        return self._find_all_duplicates(all_blocks)

    def detect_with_detailed_analysis(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Detect duplicates with comprehensive analysis and statistics"""
        duplicates = self.detect(content, file_path)

        # Generate comprehensive analysis
        statistics = self.get_duplicate_statistics(duplicates)
        summary_report = self.report_generator.create_summary_report(duplicates)

        return {
            "duplicates": duplicates,
            "statistics": statistics,
            "summary": summary_report,
            "analysis_metadata": {
                "file_analyzed": str(file_path),
                "detection_config": self._get_config_summary(),
                "blocks_extracted": len(self._get_blocks_for_file(content, file_path)),
            },
        }

    def analyze_similarity_clusters(
        self, file_contents: Dict[Path, str], similarity_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Analyze code for similarity clusters across files"""
        all_blocks = self._extract_blocks_from_files(file_contents)

        if not all_blocks:
            return {"clusters": [], "statistics": {}}

        # Find similarity clusters
        clusters = self.similarity_calculator.group_similar_blocks(all_blocks, similarity_threshold)

        # Generate cluster reports
        cluster_reports = self.report_generator.create_cluster_reports(clusters)

        return {
            "clusters": clusters,
            "cluster_reports": cluster_reports,
            "cluster_statistics": self._analyze_cluster_statistics(clusters),
            "total_blocks_analyzed": len(all_blocks),
        }

    def get_duplicate_statistics(self, duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive statistics about detected duplicates"""
        return self.statistics_calculator.calculate_statistics(duplicates)

    def get_similarity_analysis(
        self, content1: str, file1: Path, content2: str, file2: Path
    ) -> Dict[str, Any]:
        """Analyze similarity between two specific files"""
        blocks1 = self.block_extractor.extract_blocks(content1.splitlines(), file1)
        blocks2 = self.block_extractor.extract_blocks(content2.splitlines(), file2)

        all_blocks = blocks1 + blocks2
        similar_pairs = self.similarity_calculator.find_similar_blocks(all_blocks)

        # Filter pairs that cross between the two files
        cross_file_pairs = [
            (b1, b2, sim) for b1, b2, sim in similar_pairs if b1.file_path != b2.file_path
        ]

        return {
            "cross_file_similarities": cross_file_pairs,
            "file1_blocks": len(blocks1),
            "file2_blocks": len(blocks2),
            "similarity_count": len(cross_file_pairs),
            "average_similarity": (
                sum(sim for _, _, sim in cross_file_pairs) / len(cross_file_pairs)
                if cross_file_pairs
                else 0.0
            ),
        }

    def configure_detection(self, **kwargs) -> None:
        """Configure detection parameters dynamically"""
        # Update configuration
        for key, value in kwargs.items():
            if hasattr(self.config, key.upper()):
                setattr(self.config, key.upper(), value)

        # Recreate components with new configuration
        self.block_extractor = CodeBlockExtractor(self.config)
        self.similarity_calculator = SimilarityCalculator(self.config)
        self.report_generator = DuplicateReportGenerator(self.config)
        self.statistics_calculator = DuplicateStatisticsCalculator(self.config)

    def _is_valid_context(self, context: DetectionContext) -> bool:
        """Check if analysis context is valid"""
        return self._is_valid_content(context.content) and self._has_sufficient_lines(context.lines)

    def _is_valid_content(self, content: str) -> bool:
        """Check if content is valid for analysis"""
        return bool(content and content.strip())

    def _has_sufficient_lines(self, lines: Optional[List[str]]) -> bool:
        """Check if there are enough lines for duplicate detection"""
        return (
            lines is not None and len(lines) >= self.config.MIN_LINES * 2
        )  # Need at least 2 blocks

    def _extract_blocks_from_files(self, file_contents: Dict[Path, str]) -> List[DuplicateBlock]:
        """Extract code blocks from multiple files"""
        all_blocks = []

        for file_path, content in file_contents.items():
            try:
                context = self.create_context(content, file_path)

                if self._is_valid_context(context) and context.lines:
                    blocks = self.block_extractor.extract_blocks(context.lines, file_path)
                    all_blocks.extend(blocks)
            except Exception as e:
                self.logger.warning(f"Failed to extract blocks from {file_path}: {e}")
                continue

        return all_blocks

    def _find_all_duplicates(self, code_blocks: List[DuplicateBlock]) -> List[Dict[str, Any]]:
        """Find all types of duplicates in code blocks"""
        duplicates = []

        # Find exact matches using hash grouping
        exact_duplicates = self._find_exact_duplicates(code_blocks)
        duplicates.extend(exact_duplicates)

        # Find similar blocks (fuzzy matching)
        similar_duplicates = self._find_similar_duplicates(code_blocks)
        duplicates.extend(similar_duplicates)

        return duplicates

    def _find_exact_duplicates(self, blocks: List[DuplicateBlock]) -> List[Dict[str, Any]]:
        """Find exact duplicate blocks using hash matching"""
        duplicates = []
        hash_groups = self._group_blocks_by_hash(blocks)

        exact_reports = self.report_generator.create_exact_match_reports(hash_groups)
        duplicates.extend(exact_reports)

        return duplicates

    def _group_blocks_by_hash(
        self, blocks: List[DuplicateBlock]
    ) -> Dict[str, List[DuplicateBlock]]:
        """Group blocks by their hash values"""
        hash_groups = defaultdict(list)

        for block in blocks:
            hash_groups[block.hash_value].append(block)

        return dict(hash_groups)

    def _find_similar_duplicates(self, blocks: List[DuplicateBlock]) -> List[Dict[str, Any]]:
        """Find similar duplicate blocks using similarity analysis"""
        duplicates = []

        similar_pairs = self.similarity_calculator.find_similar_blocks(blocks)

        # Convert pairs to reports
        for block1, block2, similarity in similar_pairs:
            duplicate_pair = self.report_generator.create_duplicate_reports(
                [block1, block2], similarity_score=similarity
            )
            duplicates.extend(duplicate_pair)

        return duplicates

    def _get_blocks_for_file(self, content: str, file_path: Path) -> List[DuplicateBlock]:
        """Get blocks for a single file"""
        lines = content.splitlines()
        if not lines:
            return []
        return self.block_extractor.extract_blocks(lines, file_path)

    def _get_config_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration"""
        return {
            "min_lines": self.config.MIN_LINES,
            "min_tokens": self.config.MIN_TOKENS,
            "similarity_threshold": self.config.SIMILARITY_THRESHOLD,
            "exact_match_threshold": self.config.EXACT_MATCH_THRESHOLD,
            "jaccard_threshold": self.config.JACCARD_THRESHOLD,
        }

    def _analyze_cluster_statistics(self, clusters: List[List[DuplicateBlock]]) -> Dict[str, Any]:
        """Analyze statistics for similarity clusters"""
        if not clusters:
            return {
                "total_clusters": 0,
                "average_cluster_size": 0,
                "largest_cluster_size": 0,
                "total_clustered_blocks": 0,
            }

        cluster_sizes = [len(cluster) for cluster in clusters]
        total_blocks = sum(cluster_sizes)

        return {
            "total_clusters": len(clusters),
            "average_cluster_size": total_blocks / len(clusters),
            "largest_cluster_size": max(cluster_sizes),
            "smallest_cluster_size": min(cluster_sizes),
            "total_clustered_blocks": total_blocks,
            "cluster_size_distribution": self._calculate_cluster_size_distribution(cluster_sizes),
        }

    def _calculate_cluster_size_distribution(self, cluster_sizes: List[int]) -> Dict[str, int]:
        """Calculate distribution of cluster sizes"""
        distribution = {
            "small (2-3 blocks)": 0,
            "medium (4-7 blocks)": 0,
            "large (8-15 blocks)": 0,
            "very_large (>15 blocks)": 0,
        }

        for size in cluster_sizes:
            if size <= 3:
                distribution["small (2-3 blocks)"] += 1
            elif size <= 7:
                distribution["medium (4-7 blocks)"] += 1
            elif size <= 15:
                distribution["large (8-15 blocks)"] += 1
            else:
                distribution["very_large (>15 blocks)"] += 1

        return distribution

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance and efficiency metrics for the detector"""
        return {
            "components": {
                "block_extractor": "CodeBlockExtractor",
                "similarity_calculator": "SimilarityCalculator",
                "report_generator": "DuplicateReportGenerator",
                "statistics_calculator": "DuplicateStatisticsCalculator",
            },
            "configuration": self._get_config_summary(),
            "capabilities": [
                "exact_duplicate_detection",
                "similarity_based_detection",
                "cross_file_analysis",
                "cluster_analysis",
                "comprehensive_statistics",
                "configurable_thresholds",
            ],
        }
