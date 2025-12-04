"""
File metrics collector.

Classes:
    FileMetricsCollector: Single-method utility for file metrics
"""

from pathlib import Path
from typing import Any, Dict


class FileMetricsCollector:
    """Utility for collecting basic file metrics."""

    @staticmethod
    def collect_basic_metrics(content: str, file_path: Path) -> Dict[str, Any]:
        """Collect all basic file metrics in one method."""
        lines = content.splitlines()

        blank_count = 0
        comment_count = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_count += 1
            if stripped.startswith("#"):
                comment_count += 1

        return {
            "lines_of_code": len(lines),
            "blank_lines": blank_count,
            "comment_lines": comment_count,
            "file_size_bytes": len(content.encode("utf-8")),
        }
