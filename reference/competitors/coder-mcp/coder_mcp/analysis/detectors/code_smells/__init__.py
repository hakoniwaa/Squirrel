"""
Code smell detection package with specialized detectors
"""

from dataclasses import dataclass

from .complexity import ComplexitySmellDetector
from .coordinator import CodeSmellDetector
from .quality import QualitySmellDetector
from .structural import StructuralSmellDetector
from .utils import create_code_smell_issue


# Add backward compatibility classes
@dataclass
class CodeSmell:
    """Represents a detected code smell"""

    smell_type: str
    file_path: str
    line_number: int
    severity: str
    description: str
    suggestion: str


__all__ = [
    "StructuralSmellDetector",
    "QualitySmellDetector",
    "ComplexitySmellDetector",
    "CodeSmellDetector",
    "CodeSmell",
    "create_code_smell_issue",
]
