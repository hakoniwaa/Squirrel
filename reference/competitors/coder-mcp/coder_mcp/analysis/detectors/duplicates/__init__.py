"""
Duplicate code detection package with specialized components
"""

from dataclasses import dataclass

from .block_extractor import CodeBlockExtractor
from .coordinator import DuplicateCodeDetector
from .report_generator import DuplicateReportGenerator
from .similarity_calculator import SimilarityCalculator
from .statistics_calculator import DuplicateStatisticsCalculator


# Add backward compatibility classes
@dataclass
class DuplicateBlock:
    """Represents a block of potentially duplicate code"""

    file_path: str
    start_line: int
    end_line: int
    content: str
    content_hash: str


__all__ = [
    "CodeBlockExtractor",
    "SimilarityCalculator",
    "DuplicateReportGenerator",
    "DuplicateStatisticsCalculator",
    "DuplicateCodeDetector",
    "DuplicateBlock",
]
