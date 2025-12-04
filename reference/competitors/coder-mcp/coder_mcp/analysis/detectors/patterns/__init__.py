"""
Pattern detection package with specialized detectors
"""

from dataclasses import dataclass
from typing import Optional

from .anti_patterns import AntiPatternDetector
from .architectural_patterns import ArchitecturalPatternDetector
from .coordinator import PatternDetector
from .design_patterns import DesignPatternDetector
from .structural_patterns import StructuralPatternDetector


# Add backward compatibility classes
@dataclass
class PatternMatch:
    """Represents a detected pattern match"""

    pattern_name: str
    pattern_type: str
    file_path: str
    start_line: int
    end_line: Optional[int] = None
    confidence: float = 0.0
    description: str = ""
    suggestion: str = ""


__all__ = [
    "DesignPatternDetector",
    "AntiPatternDetector",
    "ArchitecturalPatternDetector",
    "StructuralPatternDetector",
    "PatternDetector",
    "PatternMatch",
]
