"""
Centralized constants and thresholds for code analysis detectors
"""

from typing import Union


class CodeQualityThresholds:
    """Thresholds for code quality metrics"""

    # Structural metrics
    FUNCTION_LENGTH = 50
    CLASS_SIZE = 300
    NESTING_DEPTH = 4
    LINE_LENGTH = 120
    PARAMETER_COUNT = 5

    # Complexity metrics
    CYCLOMATIC_COMPLEXITY = 10
    COGNITIVE_COMPLEXITY = 15
    CONDITIONAL_COMPLEXITY = 5

    # Code smell detection
    DUPLICATE_LINES = 10
    MAGIC_NUMBER_DIGITS = 2
    PRIMITIVE_OBSESSION_COUNT = 3
    FEATURE_ENVY_CALLS = 5
    DATA_CLUMPS_COUNT = 4
    GLOBAL_VARIABLES_COUNT = 3

    # Quality metrics
    COMMENT_RATIO = 0.1
    COHESION_THRESHOLD = 0.3
    COUPLING_THRESHOLD = 5

    # Code metrics
    MINIMUM_BLOCK_SIZE = 3
    MINIMUM_TOKEN_LENGTH = 1
    MINIMUM_CHARACTERS = 50


class ConfidenceLevels:
    """Confidence thresholds for pattern detection"""

    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4
    MINIMUM = 0.3


class SeverityLevels:
    """Severity levels for issues"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecurityThresholds:
    """Thresholds for security issue detection"""

    # Secret detection
    MIN_SECRET_LENGTH = 8
    MIN_TOKEN_LENGTH = 20
    MIN_BASE64_LENGTH = 40
    MIN_ENTROPY_THRESHOLD = 4.5

    # Limits
    MAX_ISSUES_PER_TYPE = 100
    MAX_PATTERN_MATCHES = 50


class DuplicateDetectionConfig:
    """Configuration for duplicate code detection"""

    MIN_LINES = 5
    MIN_TOKENS = 10
    MIN_BLOCK_SIZE = 3
    MIN_CHARACTERS = 50

    # Similarity thresholds
    SIMILARITY_THRESHOLD = 0.8
    EXACT_MATCH_THRESHOLD = 0.95
    JACCARD_THRESHOLD = 0.7

    # Analysis parameters
    SLIDING_WINDOW_STEP = 1
    SIZE_RATIO_THRESHOLD = 0.5
    CONTENT_PREVIEW_LINES = 3


class PatternDetectionConfig:
    """Configuration for pattern detection"""

    # Pattern matching
    MIN_PATTERN_LINES = 3
    MAX_PATTERN_LINES = 100
    NAMING_CONVENTION_THRESHOLD = 5

    # Structural patterns
    DEEP_NESTING_THRESHOLD = 4
    LONG_METHOD_THRESHOLD = 50
    LARGE_CLASS_THRESHOLD = 300
    INDENT_SPACES = 4

    # Anti-pattern detection
    GOD_OBJECT_THRESHOLD = 300
    SPAGHETTI_CODE_THRESHOLD = 5
    MAGIC_NUMBER_MIN_DIGITS = 2


class AnalysisLimits:
    """Limits for analysis operations"""

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_LINES_PER_FILE = 10000
    MAX_ISSUES_PER_FILE = 1000
    MAX_ANALYSIS_TIME = 300  # 5 minutes

    # Processing limits
    MAX_CONCURRENT_FILES = 10
    MAX_MEMORY_USAGE = 512 * 1024 * 1024  # 512MB
    BATCH_SIZE = 100


class RegexPatterns:
    """Common regex patterns used across detectors"""

    # Language constructs
    FUNCTION_DEF = r"^\s*(def|function|async\s+def)\s+(\w+)"
    CLASS_DEF = r"^\s*class\s+(\w+)"
    METHOD_DEF = r"^\s*def\s+(\w+)\s*\("

    # Naming patterns
    SNAKE_CASE = r"\b[a-z]+_[a-z_]+\b"
    CAMEL_CASE = r"\b[a-z][a-zA-Z]*[A-Z][a-zA-Z]*\b"
    PASCAL_CASE = r"\b[A-Z][a-zA-Z]*\b"

    # Magic numbers
    MAGIC_NUMBER = r"\b(?<![\w.])\d+(?:\.\d+)?(?![\w.])"

    # Comments
    SINGLE_LINE_COMMENT = r"#.*$"
    MULTI_LINE_COMMENT = r'""".*?"""'

    # Security patterns
    PASSWORD_PATTERN = r'(?i)(password|pwd|pass)\s*[=:]\s*["\'][^"\']+["\']'
    API_KEY_PATTERN = r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\'][A-Za-z0-9]+["\']'
    SQL_INJECTION = r'\.execute\s*\(\s*["\'].*%.*["\']'


class FileExtensions:
    """File extensions for different languages"""

    PYTHON = {".py", ".pyx", ".pyi"}
    JAVASCRIPT = {".js", ".jsx", ".mjs"}
    TYPESCRIPT = {".ts", ".tsx"}
    JAVA = {".java"}
    CPP = {".cpp", ".cc", ".cxx", ".c++", ".hpp", ".h"}
    C = {".c", ".h"}
    CSHARP = {".cs"}
    GO = {".go"}
    RUST = {".rs"}
    PHP = {".php"}
    RUBY = {".rb"}

    ALL_SUPPORTED = (
        PYTHON | JAVASCRIPT | TYPESCRIPT | JAVA | CPP | C | CSHARP | GO | RUST | PHP | RUBY
    )


class ErrorMessages:
    """Standard error messages"""

    INVALID_FILE_PATH = "Invalid file path provided"
    FILE_TOO_LARGE = "File size exceeds maximum limit"
    EMPTY_CONTENT = "File content is empty"
    INVALID_ENCODING = "File encoding is not supported"
    ANALYSIS_TIMEOUT = "Analysis timeout exceeded"
    PATTERN_NOT_FOUND = "Pattern configuration not found"
    INSUFFICIENT_CONTEXT = "Insufficient context for analysis"


class WarningMessages:
    """Standard warning messages"""

    LARGE_FILE = "File is large and may take longer to analyze"
    MANY_ISSUES = "Many issues detected - consider reviewing file structure"
    LOW_CONFIDENCE = "Low confidence pattern match - manual review recommended"
    EXPERIMENTAL_FEATURE = "This feature is experimental"


def get_threshold_for_language(language: str, metric: str) -> Union[int, float]:
    """Get language-specific threshold for a metric"""

    language_overrides = {
        "python": {
            "function_length": CodeQualityThresholds.FUNCTION_LENGTH,
            "class_size": CodeQualityThresholds.CLASS_SIZE,
            "line_length": 88,  # Black formatter standard
        },
        "javascript": {
            "function_length": 30,  # JS functions tend to be shorter
            "line_length": 100,
        },
        "typescript": {
            "function_length": 35,
            "line_length": 100,
        },
        "java": {
            "class_size": 500,  # Java classes can be larger
            "line_length": 120,
        },
    }

    if language in language_overrides and metric in language_overrides[language]:
        return language_overrides[language][metric]

    # Default thresholds
    defaults = {
        "function_length": CodeQualityThresholds.FUNCTION_LENGTH,
        "class_size": CodeQualityThresholds.CLASS_SIZE,
        "line_length": CodeQualityThresholds.LINE_LENGTH,
        "nesting_depth": CodeQualityThresholds.NESTING_DEPTH,
        "parameter_count": CodeQualityThresholds.PARAMETER_COUNT,
    }

    return defaults.get(metric, 10)  # Safe default


def get_severity_for_confidence(confidence: float) -> str:
    """Map confidence level to severity"""
    if confidence >= ConfidenceLevels.HIGH:
        return SeverityLevels.HIGH
    elif confidence >= ConfidenceLevels.MEDIUM:
        return SeverityLevels.MEDIUM
    else:
        return SeverityLevels.LOW


def should_analyze_file(file_path: str, file_size: int) -> bool:
    """Determine if a file should be analyzed based on size and type"""
    # Check file size
    if file_size > AnalysisLimits.MAX_FILE_SIZE:
        return False

    # Check file extension
    extension = "." + file_path.split(".")[-1].lower() if "." in file_path else ""
    return extension in FileExtensions.ALL_SUPPORTED
