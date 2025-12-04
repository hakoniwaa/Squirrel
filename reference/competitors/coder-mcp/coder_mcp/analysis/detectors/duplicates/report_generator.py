"""
Report generation for duplicate code detection
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..constants import DuplicateDetectionConfig, SeverityLevels
from .block_extractor import DuplicateBlock


class DuplicateReportGenerator:
    """Generate reports for detected duplicates"""

    def __init__(self, config: Optional[DuplicateDetectionConfig] = None):
        """Initialize with configuration"""
        self.config = config or DuplicateDetectionConfig()
        self.exact_match_threshold = self.config.EXACT_MATCH_THRESHOLD
        self.content_preview_lines = self.config.CONTENT_PREVIEW_LINES

    def create_duplicate_reports(
        self, blocks: List[DuplicateBlock], similarity_score: float
    ) -> List[Dict[str, Any]]:
        """Create duplicate reports from a group of duplicate blocks"""
        if not blocks:
            return []

        reports = []

        for block in blocks:
            report = self._create_single_duplicate_report(block, len(blocks), similarity_score)
            reports.append(report)

        return reports

    def create_cluster_reports(self, clusters: List[List[DuplicateBlock]]) -> List[Dict[str, Any]]:
        """Create reports for clusters of similar blocks"""
        reports = []

        for cluster_id, cluster in enumerate(clusters):
            if len(cluster) < 2:
                continue

            # Calculate average similarity within cluster
            avg_similarity = self._calculate_cluster_similarity(cluster)

            for block in cluster:
                report = self._create_cluster_report(
                    block, cluster_id, len(cluster), avg_similarity
                )
                reports.append(report)

        return reports

    def create_exact_match_reports(
        self, hash_groups: Dict[str, List[DuplicateBlock]]
    ) -> List[Dict[str, Any]]:
        """Create reports for exact matches grouped by hash"""
        reports = []

        for group in hash_groups.values():
            if len(group) > 1:
                exact_reports = self.create_duplicate_reports(group, similarity_score=1.0)
                reports.extend(exact_reports)

        return reports

    def create_summary_report(self, all_duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary report of all duplicate detection results"""
        if not all_duplicates:
            return self._create_empty_summary()

        # Group duplicates by type
        exact_matches = [
            d for d in all_duplicates if d.get("similarity_score", 0) >= self.exact_match_threshold
        ]
        similar_matches = [
            d for d in all_duplicates if d.get("similarity_score", 0) < self.exact_match_threshold
        ]

        # Calculate affected files
        affected_files = set(d.get("file", "") for d in all_duplicates)

        # Calculate potential lines saved
        lines_saved = self._calculate_lines_saved(all_duplicates)

        return {
            "total_duplicates": len(all_duplicates),
            "exact_matches": len(exact_matches),
            "similar_matches": len(similar_matches),
            "files_affected": len(affected_files),
            "potential_lines_saved": lines_saved,
            "severity_distribution": self._calculate_severity_distribution(all_duplicates),
            "top_duplicate_files": self._get_top_duplicate_files(all_duplicates),
            "duplicate_types": self._analyze_duplicate_types(all_duplicates),
            "recommendations": self._generate_recommendations(all_duplicates),
        }

    def _create_single_duplicate_report(
        self, block: DuplicateBlock, group_size: int, similarity_score: float
    ) -> Dict[str, Any]:
        """Create a single duplicate report for a block"""
        try:
            relative_path = str(Path(block.file_path).relative_to(Path.cwd()))
        except (ValueError, AttributeError):
            relative_path = block.file_path

        return {
            "type": "duplicate_code",
            "file": relative_path,
            "start_line": block.start_line,
            "end_line": block.end_line,
            "similarity_score": similarity_score,
            "hash": block.hash_value,
            "description": self._create_duplicate_description(group_size, similarity_score),
            "suggestion": self._get_duplicate_suggestion(similarity_score, group_size),
            "severity": self._get_duplicate_severity(similarity_score, group_size),
            "duplicate_group_size": group_size,
            "content_preview": self._get_content_preview(block.content),
            "lines_count": block.end_line - block.start_line + 1,
        }

    def _create_cluster_report(
        self, block: DuplicateBlock, cluster_id: int, cluster_size: int, avg_similarity: float
    ) -> Dict[str, Any]:
        """Create a report for a block in a similarity cluster"""
        report = self._create_single_duplicate_report(block, cluster_size, avg_similarity)
        report.update(
            {
                "cluster_id": cluster_id,
                "cluster_size": cluster_size,
                "average_cluster_similarity": avg_similarity,
            }
        )
        return report

    def _create_duplicate_description(self, group_size: int, similarity_score: float) -> str:
        """Create a description for the duplicate code"""
        if similarity_score >= self.exact_match_threshold:
            return f"Exact duplicate code found (appears {group_size} times)"
        else:
            return (
                f"Similar code found (similarity: {similarity_score:.2%}, "
                f"appears {group_size} times)"
            )

    def _get_duplicate_suggestion(self, similarity_score: float, group_size: int) -> str:
        """Get suggestion for handling duplicate code"""
        if similarity_score >= self.exact_match_threshold:
            if group_size > 3:
                return "Extract this exact duplicate code into a reusable function or class method"
            else:
                return "Extract this exact duplicate code into a reusable function"
        else:
            return "Consider refactoring similar code blocks to reduce duplication"

    def _get_duplicate_severity(self, similarity_score: float, group_size: int) -> str:
        """Determine severity based on similarity and group size"""
        if similarity_score >= self.exact_match_threshold:
            if group_size > 5:
                return SeverityLevels.HIGH
            elif group_size > 3:
                return SeverityLevels.MEDIUM
            else:
                return SeverityLevels.LOW
        else:
            if similarity_score >= 0.8:
                return SeverityLevels.MEDIUM
            else:
                return SeverityLevels.LOW

    def _get_content_preview(self, content: str, max_lines: Optional[int] = None) -> str:
        """Get a preview of the duplicate content"""
        if max_lines is None:
            max_lines = self.content_preview_lines

        lines = content.splitlines()
        preview_lines = lines[:max_lines]

        if len(lines) > max_lines:
            preview_lines.append("...")

        return "\n".join(preview_lines)

    def _calculate_cluster_similarity(self, cluster: List[DuplicateBlock]) -> float:
        """Calculate average similarity within a cluster"""
        if len(cluster) < 2:
            return 1.0

        # For simplicity, assume blocks in a cluster have high similarity
        # In practice, you might want to calculate pairwise similarities
        return 0.85  # Placeholder average

    def _create_empty_summary(self) -> Dict[str, Any]:
        """Create empty summary when no duplicates found"""
        return {
            "total_duplicates": 0,
            "exact_matches": 0,
            "similar_matches": 0,
            "files_affected": 0,
            "potential_lines_saved": 0,
            "severity_distribution": {},
            "top_duplicate_files": [],
            "duplicate_types": {},
            "recommendations": ["No duplicates found - good code quality!"],
        }

    def _calculate_lines_saved(self, duplicates: List[Dict[str, Any]]) -> int:
        """Calculate potential lines saved by eliminating duplicates"""
        lines_saved = 0

        # Group by hash to avoid double counting
        hash_groups: Dict[str, List[Dict[str, Any]]] = {}
        for duplicate in duplicates:
            hash_value = duplicate.get("hash", "")
            if hash_value not in hash_groups:
                hash_groups[hash_value] = []
            hash_groups[hash_value].append(duplicate)

        for group in hash_groups.values():
            if len(group) > 1:
                # Calculate lines for one instance
                sample = group[0]
                lines_in_block = sample.get(
                    "lines_count", sample.get("end_line", 0) - sample.get("start_line", 0) + 1
                )

                # Save lines for all but one occurrence
                lines_saved += lines_in_block * (len(group) - 1)

        return lines_saved

    def _calculate_severity_distribution(self, duplicates: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate distribution of duplicates by severity"""
        distribution: Dict[str, int] = {}

        for duplicate in duplicates:
            severity = duplicate.get("severity", SeverityLevels.LOW)
            distribution[severity] = distribution.get(severity, 0) + 1

        return distribution

    def _get_top_duplicate_files(
        self, duplicates: List[Dict[str, Any]], top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """Get files with the most duplicates"""
        file_counts: Dict[str, int] = {}

        for duplicate in duplicates:
            file_path = duplicate.get("file", "unknown")
            file_counts[file_path] = file_counts.get(file_path, 0) + 1

        # Sort by count and take top N
        sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)

        return [
            {"file": file_path, "duplicate_count": count}
            for file_path, count in sorted_files[:top_n]
        ]

    def _analyze_duplicate_types(self, duplicates: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze types of duplicates found"""
        types = {
            "exact_duplicates": 0,
            "high_similarity": 0,
            "medium_similarity": 0,
            "low_similarity": 0,
        }

        for duplicate in duplicates:
            similarity = duplicate.get("similarity_score", 0)

            if similarity >= self.exact_match_threshold:
                types["exact_duplicates"] += 1
            elif similarity >= 0.8:
                types["high_similarity"] += 1
            elif similarity >= 0.6:
                types["medium_similarity"] += 1
            else:
                types["low_similarity"] += 1

        return types

    def _generate_recommendations(self, duplicates: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations based on duplicate analysis"""
        if not duplicates:
            return ["No duplicates found - good code quality!"]

        recommendations = []

        # Analyze severity distribution
        severity_dist = self._calculate_severity_distribution(duplicates)
        high_severity = severity_dist.get(SeverityLevels.HIGH, 0)

        if high_severity > 0:
            recommendations.append(
                f"Priority: Address {high_severity} high-severity duplicates first"
            )

        # Analyze exact matches
        exact_matches = sum(
            1 for d in duplicates if d.get("similarity_score", 0) >= self.exact_match_threshold
        )

        if exact_matches > 10:
            recommendations.append(
                "Consider implementing a code review process to catch duplicates early"
            )

        # Analyze file distribution
        affected_files = len(set(d.get("file", "") for d in duplicates))

        if affected_files > 5:
            recommendations.append(
                "Duplicates span multiple files - consider architectural refactoring"
            )

        # General recommendations
        recommendations.extend(
            [
                "Extract common code into utility functions or base classes",
                "Use design patterns like Template Method or Strategy to reduce duplication",
                "Consider using code generation tools for repetitive patterns",
            ]
        )

        return recommendations
