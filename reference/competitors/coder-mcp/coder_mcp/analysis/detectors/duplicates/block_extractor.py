"""
Code block extraction for duplicate detection
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..base import DetectionUtils
from ..constants import DuplicateDetectionConfig


@dataclass(frozen=True)
class DuplicateBlock:
    """Represents a duplicate code block"""

    file_path: str
    start_line: int
    end_line: int
    content: str
    hash_value: str
    similarity_score: float = 0.0


class CodeBlockExtractor:
    """Extract and validate code blocks for duplicate detection"""

    def __init__(self, config: Optional[DuplicateDetectionConfig] = None):
        """Initialize with configuration"""
        self.config = config or DuplicateDetectionConfig()
        self.min_lines = self.config.MIN_LINES
        self.min_block_size = self.config.MIN_BLOCK_SIZE
        self.min_characters = self.config.MIN_CHARACTERS
        self.sliding_window_step = self.config.SLIDING_WINDOW_STEP

    def extract_blocks(self, lines: List[str], file_path: Path) -> List[DuplicateBlock]:
        """Extract potential code blocks using sliding window approach"""
        if not self._has_sufficient_lines(lines):
            return []

        blocks = []

        for start_idx in range(len(lines) - self.min_lines + 1):
            for end_idx in range(
                start_idx + self.min_lines, len(lines) + 1, self.sliding_window_step
            ):
                block_lines = lines[start_idx:end_idx]

                if self._is_valid_code_block(block_lines):
                    block = self._create_duplicate_block(file_path, start_idx, end_idx, block_lines)
                    if block:
                        blocks.append(block)

        return blocks

    def _has_sufficient_lines(self, lines: List[str]) -> bool:
        """Check if there are enough lines for duplicate detection"""
        return len(lines) >= self.min_lines * 2  # Need at least 2 potential blocks

    def _is_valid_code_block(self, block_lines: List[str]) -> bool:
        """Check if a code block is valid for duplicate detection"""
        return (
            self._has_minimum_length(block_lines)
            and self._has_sufficient_content(block_lines)
            and self._has_meaningful_code(block_lines)
            and not self._is_mostly_comments_or_empty(block_lines)
        )

    def _has_minimum_length(self, block_lines: List[str]) -> bool:
        """Check if block meets minimum length requirements"""
        return len(block_lines) >= self.min_block_size

    def _has_sufficient_content(self, block_lines: List[str]) -> bool:
        """Check if block has sufficient content"""
        content = "\n".join(block_lines).strip()
        return len(content) >= self.min_characters

    def _has_meaningful_code(self, block_lines: List[str]) -> bool:
        """Check if block contains meaningful code"""
        non_empty_lines = [line for line in block_lines if line.strip()]
        return len(non_empty_lines) >= self.min_block_size

    def _is_mostly_comments_or_empty(self, block_lines: List[str]) -> bool:
        """Check if block is mostly comments or empty lines"""
        meaningful_lines = 0

        for line in block_lines:
            stripped = line.strip()
            if stripped and not DetectionUtils.is_comment_line(stripped):
                meaningful_lines += 1

        return meaningful_lines < self.min_block_size

    def _create_duplicate_block(
        self, file_path: Path, start_idx: int, end_idx: int, block_lines: List[str]
    ) -> Optional[DuplicateBlock]:
        """Create a DuplicateBlock from code lines"""
        try:
            content = "\n".join(block_lines)
            normalized_content = self._normalize_code(content)
            hash_value = self._calculate_hash(normalized_content)

            try:
                relative_path = str(file_path.relative_to(Path.cwd()))
            except ValueError:
                relative_path = str(file_path)

            return DuplicateBlock(
                file_path=relative_path,
                start_line=start_idx + 1,  # Convert to 1-based indexing
                end_line=end_idx,
                content=content,
                hash_value=hash_value,
            )

        except Exception:
            return None

    def _normalize_code(self, code: str) -> str:
        """Normalize code for better duplicate detection"""
        return DetectionUtils.normalize_code(code)

    def _calculate_hash(self, content: str) -> str:
        """Calculate hash for code content"""
        return hashlib.md5(content.encode("utf-8"), usedforsecurity=False).hexdigest()

    def get_block_statistics(self, blocks: List[DuplicateBlock]) -> dict:
        """Get statistics about extracted blocks"""
        if not blocks:
            return {"total_blocks": 0, "average_size": 0, "unique_hashes": 0, "files_processed": 0}

        total_lines = sum(block.end_line - block.start_line + 1 for block in blocks)
        unique_hashes = len(set(block.hash_value for block in blocks))
        unique_files = len(set(block.file_path for block in blocks))

        return {
            "total_blocks": len(blocks),
            "average_size": total_lines / len(blocks),
            "unique_hashes": unique_hashes,
            "files_processed": unique_files,
            "potential_duplicates": len(blocks) - unique_hashes,
        }
