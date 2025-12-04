"""
Base analyzer for language-specific code analysis.

This module provides the foundational abstract base class for all language-specific
analyzers, establishing consistent interfaces and error handling patterns.

Classes:
    BaseAnalyzer: Abstract base class for language-specific analyzers
    AnalysisError: Custom exception for analysis errors
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .file_metrics import FileMetricsCollector

chardet: Any  # type: ignore
try:
    import chardet  # Optional dependency for encoding detection
except ImportError:
    chardet = None

# Constants
DEFAULT_ANALYSIS_TYPE = "quick"
SUPPORTED_ANALYSIS_TYPES = {"quick", "deep", "security", "performance"}

# Binary and non-text file extensions to skip
BINARY_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".so",
    ".dylib",
    ".dll",
    ".exe",
    ".bin",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".ico",
    ".svg",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".rar",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".wav",
    ".flac",
    ".db",
    ".sqlite",
    ".cache",
    ".dat",
    ".idx",
}

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """Custom exception for analysis errors."""

    def __init__(
        self, message: str, file_path: Optional[Path] = None, cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.file_path = file_path
        self.cause = cause


class BaseAnalyzer(ABC):
    """Abstract base class for language-specific analyzers.

    This class defines the essential interface that all language-specific analyzers
    must implement, providing consistent behavior and error handling patterns.

    Attributes:
        workspace_root: Path to the workspace root directory
        logger: Logger instance for this analyzer
    """

    def __init__(self, workspace_root: Union[str, Path], validate_workspace: bool = True) -> None:
        """Initialize analyzer with workspace root.

        Args:
            workspace_root: Path to the workspace root directory
            validate_workspace: Whether to validate workspace exists (set False for testing)

        Raises:
            AnalysisError: If workspace_root is invalid or inaccessible
        """
        try:
            self.workspace_root = Path(workspace_root).resolve()

            if validate_workspace:
                if not self.workspace_root.exists():
                    raise AnalysisError(f"Workspace root does not exist: {workspace_root}")
                if not self.workspace_root.is_dir():
                    raise AnalysisError(f"Workspace root is not a directory: {workspace_root}")
            else:
                # For testing: just warn if workspace doesn't exist
                if not self.workspace_root.exists():
                    logger.debug("Workspace root does not exist (test mode): %s", workspace_root)

        except (OSError, ValueError) as e:
            raise AnalysisError(f"Invalid workspace root: {workspace_root}", cause=e) from e

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def analyze_file(
        self, file_path: Path, analysis_type: str = DEFAULT_ANALYSIS_TYPE
    ) -> Dict[str, Any]:
        """Analyze a single file and return comprehensive results.

        Args:
            file_path: Path to the file to analyze
            analysis_type: Type of analysis ("quick", "deep", "security", "performance")

        Returns:
            Dictionary containing analysis results including metrics, issues, and score

        Raises:
            AnalysisError: If analysis fails
        """

    @abstractmethod
    def get_file_extensions(self) -> List[str]:
        """Return list of supported file extensions.

        Returns:
            List of file extensions this analyzer supports (e.g., [".py", ".pyi"])
        """

    @abstractmethod
    def detect_code_smells(
        self, content: str, file_path: Path, smell_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Detect code smells in the provided content.

        Args:
            content: File content to analyze
            file_path: Path to the file being analyzed
            smell_types: List of smell types to detect

        Returns:
            List of detected code smells with their details

        Raises:
            AnalysisError: If smell detection fails
        """

    @staticmethod
    def _try_chardet_detection(file_path: Path) -> Tuple[Optional[str], str]:
        """Try to detect encoding with chardet if available."""
        try:
            if chardet is None:
                logger.debug("chardet not available, using fallback encodings")
                return None, "detection failed"
            raw_data = file_path.read_bytes()
            if b"\x00" in raw_data[:1024]:
                return None, "binary file"
            detected = chardet.detect(raw_data)
            encoding = detected.get("encoding")
            confidence = detected.get("confidence", 0)
            if encoding and confidence > 0.7:
                try:
                    content = raw_data.decode(encoding)
                    return content, encoding
                except (UnicodeDecodeError, LookupError):
                    pass
        except OSError as e:
            logger.warning("Failed to read bytes for %s: %s", file_path, e)
        except Exception as exc:  # pylint: disable=broad-except
            # Catching all exceptions here to avoid breaking file
            logger.warning("Failed to detect encoding for %s: %s", file_path, exc)
        return None, "detection failed"

    @staticmethod
    def _try_fallback_encodings(file_path: Path) -> Tuple[Optional[str], str]:
        """Try common encodings as fallback."""
        fallback_encodings = ["latin-1", "cp1252", "iso-8859-1", "utf-16"]
        for encoding in fallback_encodings:
            try:
                content = file_path.read_text(encoding=encoding)
                return content, encoding
            except (UnicodeDecodeError, LookupError):
                continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            return content, "utf-8 (with replacements)"
        except Exception:
            pass
        return None, "unsupported encoding"

    @staticmethod
    def read_file_with_fallback(file_path: Path) -> Tuple[Optional[str], str]:
        """
        Read file content with automatic encoding detection.
        This method attempts to read files with various encodings, handling
        binary files and non-UTF-8 encodings gracefully.
        Args:
            file_path: Path to the file to read
        Returns:
            tuple: (content, encoding) or (None, error_message) if failed
        """
        # Skip known binary files
        if file_path.suffix.lower() in BINARY_EXTENSIONS:
            return None, "binary file extension"
        try:
            content = file_path.read_text(encoding="utf-8")
            return content, "utf-8"
        except UnicodeDecodeError:
            pass
        result_content, result_encoding = BaseAnalyzer._try_chardet_detection(file_path)
        if result_content is not None:
            return result_content, result_encoding
        return BaseAnalyzer._try_fallback_encodings(file_path)

    def validate_analysis_type(self, analysis_type: str) -> str:
        """Validate and normalize analysis type.

        Args:
            analysis_type: The analysis type to validate

        Returns:
            Validated analysis type

        Raises:
            AnalysisError: If analysis type is invalid
        """
        if not isinstance(analysis_type, str):
            raise AnalysisError(f"Analysis type must be a string, got {type(analysis_type)}")

        analysis_type = analysis_type.lower().strip()
        if analysis_type not in SUPPORTED_ANALYSIS_TYPES:
            self.logger.warning("Unknown analysis type '%s', using default", analysis_type)
            return DEFAULT_ANALYSIS_TYPE

        return analysis_type

    def validate_file_path(self, file_path: Path) -> Path:
        """Validate file path for analysis.

        Args:
            file_path: Path to validate

        Returns:
            Resolved file path

        Raises:
            FileNotFoundError: If file does not exist
            OSError: If path is invalid or not a file
            AnalysisError: If file path is invalid for other reasons
        """
        try:
            resolved_path = Path(file_path).resolve()

            if not resolved_path.exists():
                # Let FileNotFoundError propagate for test compatibility
                raise FileNotFoundError(f"File does not exist: {file_path}")
            if not resolved_path.is_file():
                # Let OSError propagate for test compatibility
                raise OSError(f"Path is not a file: {file_path}")

            # Check if file is within workspace
            try:
                resolved_path.relative_to(self.workspace_root)
            except ValueError:
                self.logger.warning("File %s is outside workspace root", file_path)

            return resolved_path

        except (FileNotFoundError, OSError):
            # Let file system errors propagate
            raise
        except (ValueError,) as e:
            raise AnalysisError(
                f"Invalid file path: {file_path}", file_path=file_path, cause=e
            ) from e

    def create_base_result(self, file_path: Path, analysis_type: str) -> Dict[str, Any]:
        """Create base analysis result structure with defaults.

        Args:
            file_path: Path to the analyzed file
            analysis_type: Type of analysis performed

        Returns:
            Base result dictionary with standard structure
        """
        try:
            relative_path = str(file_path.relative_to(self.workspace_root))
        except ValueError:
            relative_path = str(file_path)

        return {
            "file": relative_path,
            "analysis_type": analysis_type,
            "quality_score": 0,
            "issues": [],
            "suggestions": [],
            "metrics": {},
            "timestamp": datetime.now().isoformat(),
            "analyzer": self.__class__.__name__,
        }

    def get_basic_metrics(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Get basic file metrics safely.

        Args:
            content: File content
            file_path: Path to the file

        Returns:
            Dictionary of basic metrics

        Raises:
            AnalysisError: If metrics collection fails
        """
        try:
            return FileMetricsCollector.collect_basic_metrics(content, file_path)
        except Exception as exc:  # pylint: disable=broad-except
            raise AnalysisError(
                f"Failed to collect basic metrics for {file_path}", file_path=file_path, cause=exc
            ) from exc

    def supports_file(self, file_path: Path) -> bool:
        """Check if this analyzer supports the given file.

        Args:
            file_path: Path to check

        Returns:
            True if file is supported, False otherwise
        """
        # Skip binary files
        if file_path.suffix.lower() in BINARY_EXTENSIONS:
            return False

        extensions = self.get_file_extensions()
        if "*" in extensions:  # Generic analyzer
            return True

        return file_path.suffix.lower() in [ext.lower() for ext in extensions]

    def log_analysis_start(self, file_path: Path, analysis_type: str) -> None:
        """Log the start of analysis for debugging.

        Args:
            file_path: File being analyzed
            analysis_type: Type of analysis
        """
        self.logger.debug(f"Starting {analysis_type} analysis of {file_path}")

    def log_analysis_complete(self, file_path: Path, quality_score: float) -> None:
        """Log completion of analysis.

        Args:
            file_path: File that was analyzed
            quality_score: Resulting quality score
        """
        self.logger.debug(f"Completed analysis of {file_path}, score: {quality_score}")
