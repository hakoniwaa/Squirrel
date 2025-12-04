"""
Code smell detection modules - refactored with improved architecture
"""

# Import base classes and utilities
from .base import (
    BaseDetector,
    BasePatternDetector,
    BaseRuleDetector,
    BaseStatisticalDetector,
    DetectionContext,
    DetectionStrategy,
    DetectionUtils,
    DetectorError,
    InvalidContextError,
    IssueDict,
    PatternDict,
    PatternNotFoundError,
    SecurityIssueDict,
)

# Import specialized detectors
from .code_smells import CodeSmellDetector

# Import centralized constants
from .constants import (
    AnalysisLimits,
    CodeQualityThresholds,
    ConfidenceLevels,
    DuplicateDetectionConfig,
    FileExtensions,
    PatternDetectionConfig,
    RegexPatterns,
    SecurityThresholds,
    SeverityLevels,
)
from .duplicates import DuplicateCodeDetector
from .patterns import PatternDetector
from .security import SecurityIssueDetector

__all__ = [
    # Base classes
    "BaseDetector",
    "BasePatternDetector",
    "BaseRuleDetector",
    "BaseStatisticalDetector",
    "DetectionContext",
    "DetectionStrategy",
    "DetectionUtils",
    "DetectorError",
    "PatternNotFoundError",
    "InvalidContextError",
    "IssueDict",
    "PatternDict",
    "SecurityIssueDict",
    # Constants
    "CodeQualityThresholds",
    "ConfidenceLevels",
    "SeverityLevels",
    "SecurityThresholds",
    "DuplicateDetectionConfig",
    "PatternDetectionConfig",
    "AnalysisLimits",
    "RegexPatterns",
    "FileExtensions",
    # Main detectors
    "CodeSmellDetector",
    "DuplicateCodeDetector",
    "PatternDetector",
    "SecurityIssueDetector",
]
