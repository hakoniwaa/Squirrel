"""
Statistics calculation for duplicate code detection
"""

from typing import Any, Dict, List, Optional

from ..constants import DuplicateDetectionConfig, SeverityLevels
from .block_extractor import DuplicateBlock


class DuplicateStatisticsCalculator:
    """Calculate comprehensive statistics for duplicate detection results"""

    def __init__(self, config: Optional[DuplicateDetectionConfig] = None):
        """Initialize with configuration"""
        self.config = config or DuplicateDetectionConfig()
        self.exact_match_threshold = self.config.EXACT_MATCH_THRESHOLD

    def calculate_statistics(self, duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive statistics about detected duplicates"""
        if not duplicates:
            return self._get_empty_statistics()

        basic_stats = self._calculate_basic_statistics(duplicates)
        similarity_stats = self._calculate_similarity_statistics(duplicates)
        severity_stats = self._calculate_severity_statistics(duplicates)
        file_stats = self._calculate_file_statistics(duplicates)
        efficiency_stats = self._calculate_efficiency_statistics(duplicates)

        return {
            **basic_stats,
            **similarity_stats,
            **severity_stats,
            **file_stats,
            **efficiency_stats,
        }

    def calculate_block_statistics(self, blocks: List[DuplicateBlock]) -> Dict[str, Any]:
        """Calculate statistics for extracted blocks before duplicate detection"""
        if not blocks:
            return {
                "total_blocks": 0,
                "average_block_size": 0,
                "size_distribution": {},
                "unique_hashes": 0,
                "hash_collision_rate": 0.0,
            }

        # Block size statistics
        block_sizes = [block.end_line - block.start_line + 1 for block in blocks]
        avg_size = sum(block_sizes) / len(block_sizes)

        # Size distribution
        size_distribution = self._calculate_size_distribution(block_sizes)

        # Hash statistics
        unique_hashes = len(set(block.hash_value for block in blocks))
        collision_rate = (len(blocks) - unique_hashes) / len(blocks) if blocks else 0.0

        return {
            "total_blocks": len(blocks),
            "average_block_size": avg_size,
            "min_block_size": min(block_sizes),
            "max_block_size": max(block_sizes),
            "size_distribution": size_distribution,
            "unique_hashes": unique_hashes,
            "hash_collision_rate": collision_rate,
            "potential_duplicates": len(blocks) - unique_hashes,
        }

    def calculate_similarity_distribution(self, similarities: List[float]) -> Dict[str, Any]:
        """Calculate distribution of similarity scores"""
        if not similarities:
            return {"count": 0, "average": 0.0, "distribution": {}}

        # Bucket similarities into ranges
        buckets = {
            "exact (1.0)": 0,
            "very_high (0.9-0.99)": 0,
            "high (0.8-0.89)": 0,
            "medium (0.6-0.79)": 0,
            "low (0.4-0.59)": 0,
            "very_low (<0.4)": 0,
        }

        for sim in similarities:
            if sim >= 1.0:
                buckets["exact (1.0)"] += 1
            elif sim >= 0.9:
                buckets["very_high (0.9-0.99)"] += 1
            elif sim >= 0.8:
                buckets["high (0.8-0.89)"] += 1
            elif sim >= 0.6:
                buckets["medium (0.6-0.79)"] += 1
            elif sim >= 0.4:
                buckets["low (0.4-0.59)"] += 1
            else:
                buckets["very_low (<0.4)"] += 1

        return {
            "count": len(similarities),
            "average": sum(similarities) / len(similarities),
            "min": min(similarities),
            "max": max(similarities),
            "distribution": buckets,
        }

    def calculate_duplication_impact(self, duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate the impact of code duplication on the codebase"""
        if not duplicates:
            return {
                "duplication_ratio": 0.0,
                "maintenance_burden": "low",
                "refactoring_priority": "none",
                "complexity_increase": 0,
            }

        # Calculate metrics
        total_duplicate_lines = sum(
            duplicate.get(
                "lines_count", duplicate.get("end_line", 0) - duplicate.get("start_line", 0) + 1
            )
            for duplicate in duplicates
        )

        # Estimate maintenance burden
        exact_matches = sum(
            1 for d in duplicates if d.get("similarity_score", 0) >= self.exact_match_threshold
        )

        maintenance_burden = self._assess_maintenance_burden(exact_matches)
        refactoring_priority = self._assess_refactoring_priority(duplicates)

        return {
            "total_duplicate_lines": total_duplicate_lines,
            "duplication_ratio": self._calculate_duplication_ratio(duplicates),
            "maintenance_burden": maintenance_burden,
            "refactoring_priority": refactoring_priority,
            "complexity_increase": self._estimate_complexity_increase(duplicates),
        }

    def _get_empty_statistics(self) -> Dict[str, Any]:
        """Return empty statistics when no duplicates found"""
        return {
            "total_duplicates": 0,
            "exact_matches": 0,
            "similar_matches": 0,
            "files_affected": 0,
            "average_similarity": 0.0,
            "largest_duplicate_group": 0,
            "duplicate_lines_saved": 0,
            "duplication_ratio": 0.0,
            "quality_score": 10.0,  # Perfect score
        }

    def _calculate_basic_statistics(self, duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate basic duplicate statistics"""
        exact_matches = sum(
            1 for d in duplicates if d.get("similarity_score", 0) >= self.exact_match_threshold
        )
        similar_matches = len(duplicates) - exact_matches

        affected_files = set(d.get("file", "") for d in duplicates)

        return {
            "total_duplicates": len(duplicates),
            "exact_matches": exact_matches,
            "similar_matches": similar_matches,
            "files_affected": len(affected_files),
        }

    def _calculate_similarity_statistics(self, duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate similarity-based statistics"""
        similarities = [d.get("similarity_score", 0) for d in duplicates if "similarity_score" in d]

        if not similarities:
            return {"average_similarity": 0.0, "similarity_distribution": {}}

        avg_similarity = sum(similarities) / len(similarities)
        distribution = self.calculate_similarity_distribution(similarities)

        return {
            "average_similarity": avg_similarity,
            "similarity_distribution": distribution["distribution"],
        }

    def _calculate_severity_statistics(self, duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate severity-based statistics"""
        severity_counts: dict[str, int] = {}

        for duplicate in duplicates:
            severity = duplicate.get("severity", SeverityLevels.LOW)
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Calculate quality score based on severity
        quality_score = self._calculate_quality_score(severity_counts, len(duplicates))

        return {"severity_distribution": severity_counts, "quality_score": quality_score}

    def _calculate_file_statistics(self, duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate file-based statistics"""
        file_counts: dict[str, int] = {}
        group_sizes = []

        for duplicate in duplicates:
            file_path = duplicate.get("file", "unknown")
            file_counts[file_path] = file_counts.get(file_path, 0) + 1

            group_size = duplicate.get("duplicate_group_size", 1)
            group_sizes.append(group_size)

        largest_group = max(group_sizes) if group_sizes else 0
        most_affected_file = (
            max(file_counts.items(), key=lambda x: x[1])[0] if file_counts else None
        )

        return {
            "largest_duplicate_group": largest_group,
            "most_affected_file": most_affected_file,
            "files_per_duplicate": len(file_counts) / len(duplicates) if duplicates else 0.0,
        }

    def _calculate_efficiency_statistics(self, duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate efficiency-related statistics"""
        lines_saved = self._estimate_lines_saved(duplicates)
        duplication_ratio = self._calculate_duplication_ratio(duplicates)

        return {
            "duplicate_lines_saved": lines_saved,
            "duplication_ratio": duplication_ratio,
            "potential_loc_reduction": self._calculate_loc_reduction(duplicates),
        }

    def _calculate_size_distribution(self, sizes: List[int]) -> Dict[str, int]:
        """Calculate distribution of block sizes"""
        distribution = {
            "small (5-10 lines)": 0,
            "medium (11-25 lines)": 0,
            "large (26-50 lines)": 0,
            "very_large (>50 lines)": 0,
        }

        for size in sizes:
            if size <= 10:
                distribution["small (5-10 lines)"] += 1
            elif size <= 25:
                distribution["medium (11-25 lines)"] += 1
            elif size <= 50:
                distribution["large (26-50 lines)"] += 1
            else:
                distribution["very_large (>50 lines)"] += 1

        return distribution

    def _estimate_lines_saved(self, duplicates: List[Dict[str, Any]]) -> int:
        """Estimate lines of code that could be saved by eliminating duplicates"""
        lines_saved = 0

        # Group by hash to avoid double counting
        hash_groups: dict[str, list[dict[str, Any]]] = {}
        for duplicate in duplicates:
            hash_value = duplicate.get("hash", f"temp_{id(duplicate)}")
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

    def _calculate_duplication_ratio(self, duplicates: List[Dict[str, Any]]) -> float:
        """Calculate the ratio of duplicated code to total code"""
        if not duplicates:
            return 0.0

        # This is a simplified calculation - in practice you'd need total LOC
        total_duplicate_lines = sum(
            duplicate.get(
                "lines_count", duplicate.get("end_line", 0) - duplicate.get("start_line", 0) + 1
            )
            for duplicate in duplicates
        )

        # Estimate based on affected files and average file size
        affected_files = len(set(d.get("file", "") for d in duplicates))
        estimated_total_lines = affected_files * 200  # Rough estimate

        return (
            min(total_duplicate_lines / estimated_total_lines, 1.0)
            if estimated_total_lines > 0
            else 0.0
        )

    def _calculate_loc_reduction(self, duplicates: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate potential lines of code reduction percentages"""
        lines_saved = self._estimate_lines_saved(duplicates)
        total_lines = sum(
            duplicate.get(
                "lines_count", duplicate.get("end_line", 0) - duplicate.get("start_line", 0) + 1
            )
            for duplicate in duplicates
        )

        if total_lines == 0:
            return {"percentage": 0.0, "lines": 0}

        reduction_percentage = (lines_saved / total_lines) * 100

        return {
            "percentage": reduction_percentage,
            "lines": lines_saved,
            "current_duplicate_lines": total_lines,
        }

    def _calculate_quality_score(
        self, severity_counts: Dict[str, int], total_duplicates: int
    ) -> float:
        """Calculate quality score based on duplicate severity distribution"""
        if total_duplicates == 0:
            return 10.0

        # Weight severities (lower scores for worse duplicates)
        severity_weights = {
            SeverityLevels.HIGH: 2.0,
            SeverityLevels.MEDIUM: 5.0,
            SeverityLevels.LOW: 8.0,
        }

        weighted_score = 0.0
        for severity, count in severity_counts.items():
            weight = severity_weights.get(severity, 5.0)
            weighted_score += (count / total_duplicates) * weight

        # Apply penalty for high duplicate count
        penalty = min(total_duplicates * 0.1, 3.0)  # Max 3 point penalty

        return max(0.0, weighted_score - penalty)

    def _assess_maintenance_burden(self, exact_matches: int) -> str:
        """Assess the maintenance burden level"""
        if exact_matches == 0:
            return "low"
        elif exact_matches < 5:
            return "medium"
        elif exact_matches < 15:
            return "high"
        else:
            return "critical"

    def _assess_refactoring_priority(self, duplicates: List[Dict[str, Any]]) -> str:
        """Assess refactoring priority based on duplicate characteristics"""
        high_severity = sum(1 for d in duplicates if d.get("severity") == SeverityLevels.HIGH)

        if high_severity == 0:
            return "low"
        elif high_severity < 5:
            return "medium"
        else:
            return "high"

    def _estimate_complexity_increase(self, duplicates: List[Dict[str, Any]]) -> int:
        """Estimate complexity increase due to duplicates"""
        # Simple heuristic: each duplicate group increases complexity
        unique_groups = set(d.get("hash", id(d)) for d in duplicates)
        return len(unique_groups)
