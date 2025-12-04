"""
Similarity calculation for duplicate code detection
"""

import re
from typing import Dict, List, Optional, Set

from ..constants import DuplicateDetectionConfig
from .block_extractor import DuplicateBlock


class SimilarityCalculator:
    """Calculate similarity between code blocks using various algorithms"""

    def __init__(self, config: Optional[DuplicateDetectionConfig] = None):
        """Initialize with configuration"""
        self.config = config or DuplicateDetectionConfig()
        self.jaccard_threshold = self.config.JACCARD_THRESHOLD
        self.size_ratio_threshold = self.config.SIZE_RATIO_THRESHOLD
        self.token_min_length = 1  # Minimum token length to consider

    def calculate_jaccard_similarity(self, block1: DuplicateBlock, block2: DuplicateBlock) -> float:
        """Calculate Jaccard similarity between two code blocks"""
        tokens1 = set(self._tokenize_code(block1.content))
        tokens2 = set(self._tokenize_code(block2.content))

        if not tokens1 and not tokens2:
            return 1.0
        if not tokens1 or not tokens2:
            return 0.0

        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))

        return intersection / union if union > 0 else 0.0

    def calculate_levenshtein_similarity(
        self, block1: DuplicateBlock, block2: DuplicateBlock
    ) -> float:
        """Calculate normalized Levenshtein similarity between code blocks"""
        content1 = self._normalize_for_comparison(block1.content)
        content2 = self._normalize_for_comparison(block2.content)

        distance = self._levenshtein_distance(content1, content2)
        max_length = max(len(content1), len(content2))

        if max_length == 0:
            return 1.0

        return 1.0 - (distance / max_length)

    def calculate_line_similarity(self, block1: DuplicateBlock, block2: DuplicateBlock) -> float:
        """Calculate line-by-line similarity between code blocks"""
        lines1 = [line.strip() for line in block1.content.splitlines() if line.strip()]
        lines2 = [line.strip() for line in block2.content.splitlines() if line.strip()]

        if not lines1 and not lines2:
            return 1.0
        if not lines1 or not lines2:
            return 0.0

        common_lines = 0
        lines1_set = set(lines1)
        lines2_set = set(lines2)

        for line in lines1_set:
            if line in lines2_set:
                common_lines += 1

        total_unique_lines = len(lines1_set.union(lines2_set))
        return common_lines / total_unique_lines if total_unique_lines > 0 else 0.0

    def calculate_combined_similarity(
        self, block1: DuplicateBlock, block2: DuplicateBlock
    ) -> float:
        """Calculate combined similarity using multiple algorithms"""
        jaccard = self.calculate_jaccard_similarity(block1, block2)
        levenshtein = self.calculate_levenshtein_similarity(block1, block2)
        line_sim = self.calculate_line_similarity(block1, block2)

        # Weighted average: Jaccard (50%), Levenshtein (30%), Line similarity (20%)
        weights = [0.5, 0.3, 0.2]
        similarities = [jaccard, levenshtein, line_sim]

        return sum(w * s for w, s in zip(weights, similarities))

    def should_compare_blocks(self, block1: DuplicateBlock, block2: DuplicateBlock) -> bool:
        """Check if two blocks should be compared for similarity"""
        # Don't compare blocks from the same location
        if block1.file_path == block2.file_path and block1.start_line == block2.start_line:
            return False

        # Don't compare if one block is much smaller than the other
        lines1 = len(block1.content.splitlines())
        lines2 = len(block2.content.splitlines())

        if lines1 == 0 or lines2 == 0:
            return False

        size_ratio = min(lines1, lines2) / max(lines1, lines2)
        return size_ratio >= self.size_ratio_threshold

    def find_similar_blocks(
        self, blocks: List[DuplicateBlock], similarity_threshold: Optional[float] = None
    ) -> List[tuple]:
        """Find all pairs of similar blocks above the threshold"""
        if similarity_threshold is None:
            similarity_threshold = self.jaccard_threshold

        similar_pairs = []

        for i, block1 in enumerate(blocks):
            for block2 in blocks[i + 1 :]:
                if self.should_compare_blocks(block1, block2):
                    similarity = self.calculate_combined_similarity(block1, block2)

                    if similarity >= similarity_threshold:
                        similar_pairs.append((block1, block2, similarity))

        return similar_pairs

    def group_similar_blocks(
        self, blocks: List[DuplicateBlock], similarity_threshold: Optional[float] = None
    ) -> List[List[DuplicateBlock]]:
        """Group blocks into clusters of similar code"""
        if similarity_threshold is None:
            similarity_threshold = self.jaccard_threshold

        # Find all similar pairs
        similar_pairs = self.find_similar_blocks(blocks, similarity_threshold)

        # Build adjacency list for clustering
        adjacency: Dict[DuplicateBlock, Set[DuplicateBlock]] = {}
        for block1, block2, _ in similar_pairs:
            if block1 not in adjacency:
                adjacency[block1] = set()
            if block2 not in adjacency:
                adjacency[block2] = set()
            adjacency[block1].add(block2)
            adjacency[block2].add(block1)

        # Find connected components (clusters)
        visited: Set[DuplicateBlock] = set()
        clusters = []

        for block in blocks:
            if block not in visited:
                cluster = self._dfs_cluster(block, adjacency, visited)
                if len(cluster) > 1:  # Only clusters with multiple blocks
                    clusters.append(cluster)

        return clusters

    def _tokenize_code(self, code: str) -> List[str]:
        """Tokenize code for similarity analysis"""
        cleaned_code = self._remove_comments_and_strings(code)
        tokens = re.findall(r"\w+|[+\-*/=<>!&|^~%]", cleaned_code)
        meaningful_tokens = [token for token in tokens if len(token) > self.token_min_length]

        return meaningful_tokens

    def _remove_comments_and_strings(self, code: str) -> str:
        """Remove comments and string literals from code"""
        # Remove single-line comments
        code = re.sub(r"#.*$", "", code, flags=re.MULTILINE)
        code = re.sub(r"//.*$", "", code, flags=re.MULTILINE)

        # Remove multi-line comments (simplified)
        code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)

        # Remove string literals (simplified)
        code = re.sub(r'"[^"]*"', "", code)
        code = re.sub(r"'[^']*'", "", code)

        return code

    def _normalize_for_comparison(self, code: str) -> str:
        """Normalize code for character-level comparison"""
        # Remove whitespace and normalize
        normalized = re.sub(r"\s+", " ", code.strip())
        # Remove comments
        normalized = self._remove_comments_and_strings(normalized)
        return normalized.lower()

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _dfs_cluster(
        self, start_block: DuplicateBlock, adjacency: dict, visited: Set[DuplicateBlock]
    ) -> List[DuplicateBlock]:
        """Depth-first search to find connected component (cluster)"""
        cluster = []
        stack = [start_block]

        while stack:
            block = stack.pop()
            if block not in visited:
                visited.add(block)
                cluster.append(block)

                # Add adjacent blocks to stack
                for neighbor in adjacency.get(block, []):
                    if neighbor not in visited:
                        stack.append(neighbor)

        return cluster

    def get_similarity_statistics(self, similarities: List[float]) -> dict:
        """Calculate statistics for similarity scores"""
        if not similarities:
            return {"count": 0, "average": 0.0, "min": 0.0, "max": 0.0, "high_similarity_count": 0}

        return {
            "count": len(similarities),
            "average": sum(similarities) / len(similarities),
            "min": min(similarities),
            "max": max(similarities),
            "high_similarity_count": sum(1 for s in similarities if s >= 0.8),
        }
