"""
Analyzer factory for creating language-specific code analyzers.

This module provides a factory pattern for creating and managing code analyzers
with intelligent language detection, caching for performance, and robust fallback
mechanisms to ensure analysis always works.

Features:
    - Language-specific analyzer selection based on file extensions
    - Analyzer instance caching for improved performance
    - Support for multiple file types (.py, .js, .jsx, .ts, .tsx, .mjs, .cjs, etc.)
    - Graceful fallback to generic analyzer for unknown types
    - Emergency minimal analyzer as ultimate fallback
    - Comprehensive error handling and logging

Classes:
    MinimalAnalyzer: Emergency fallback analyzer for critical failures
    AnalyzerFactory: Main factory for creating and caching language-specific analyzers

Functions:
    get_analyzer_factory: Factory function to create AnalyzerFactory instances
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from .base_analyzer import BaseAnalyzer
from .languages.generic_analyzer import GenericAnalyzer  # noqa: E402

logger = logging.getLogger(__name__)


class MinimalAnalyzer(BaseAnalyzer):
    """Minimal analyzer implementation as emergency fallback."""

    def __init__(self, workspace_root: Path, validate_workspace: bool = True):
        """Initialize minimal analyzer."""
        super().__init__(workspace_root, validate_workspace)

    def get_file_extensions(self) -> List[str]:
        """Return all file extensions (supports any file)."""
        return ["*"]

    async def analyze_file(self, file_path: Path, analysis_type: str = "quick") -> Dict[str, Any]:
        """Perform minimal file analysis."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            lines = content.splitlines()
            return {
                "file": str(file_path.relative_to(self.workspace_root)),
                "analysis_type": analysis_type,
                "quality_score": 5.0,  # Neutral score
                "issues": [],
                "suggestions": [],
                "metrics": {
                    "total_lines": len(lines),
                    "non_empty_lines": len([line for line in lines if line.strip()]),
                    "file_size": len(content),
                },
                "analyzer": "MinimalAnalyzer",
            }
        except (OSError, UnicodeDecodeError) as e:
            return {
                "file": str(file_path),
                "analysis_type": analysis_type,
                "quality_score": 0.0,
                "issues": [f"Failed to analyze file: {e}"],
                "suggestions": [],
                "metrics": {},
                "analyzer": "MinimalAnalyzer",
            }

    def detect_code_smells(
        self, content: str, file_path: Path, smell_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Minimal code smell detection."""
        return []  # No smells detected in minimal analyzer


class AnalyzerFactory:
    """Factory for creating and caching language-specific analyzers."""

    def __init__(self, workspace_root: Path):
        """Initialize the analyzer factory.

        Args:
            workspace_root: Root directory of the workspace
        """
        self.workspace_root = Path(workspace_root)

        # Cache for analyzer instances to improve performance
        self._analyzer_cache: Dict[str, BaseAnalyzer] = {}

        # Extended file extension mapping with support for additional types
        self._extensions = {
            # Python files
            ".py": "python",
            ".pyw": "python",
            ".pyi": "python",
            # JavaScript files (including new types)
            ".js": "javascript",
            ".jsx": "javascript",
            ".mjs": "javascript",
            ".cjs": "javascript",
            # TypeScript files (including new types)
            ".ts": "typescript",
            ".tsx": "typescript",
        }

        logger.debug("Initialized AnalyzerFactory for workspace: %s", self.workspace_root)

    def get_analyzer(self, file_path: Path) -> BaseAnalyzer:
        """Get appropriate analyzer for the given file type.

        Uses caching to improve performance by reusing analyzer instances.
        Falls back to generic analyzer for unsupported file types.

        Args:
            file_path: Path to the file to be analyzed

        Returns:
            BaseAnalyzer: Appropriate analyzer instance for the file type
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        # Determine analyzer type
        analyzer_type = self._extensions.get(extension, "generic")

        # Check cache first for performance
        if analyzer_type in self._analyzer_cache:
            logger.debug("Using cached %s analyzer for %s", analyzer_type, file_path)
            return self._analyzer_cache[analyzer_type]

        # Create new analyzer instance
        analyzer = self._create_analyzer(analyzer_type, file_path)

        # Cache the analyzer for future use
        self._analyzer_cache[analyzer_type] = analyzer

        logger.debug("Created and cached %s analyzer for %s", analyzer_type, file_path)
        return analyzer

    def _create_analyzer(self, analyzer_type: str, file_path: Path) -> BaseAnalyzer:
        """Create a new analyzer instance of the specified type.

        Args:
            analyzer_type: Type of analyzer to create (
                'python', 'javascript', 'typescript', 'generic'
            )
            file_path: Path to the file (used for logging context)

        Returns:
            BaseAnalyzer: New analyzer instance

        Raises:
            ImportError: If analyzer module cannot be imported
            Exception: If analyzer instantiation fails
        """
        _ = file_path
        creators = {
            "python": self._create_python_analyzer,
            "javascript": self._create_javascript_analyzer,
            "typescript": self._create_typescript_analyzer,
        }
        try:
            if analyzer_type in creators:
                analyzer = creators[analyzer_type]()
                if analyzer:
                    return cast(BaseAnalyzer, analyzer)
            # Fallback to generic analyzer
            try:
                return GenericAnalyzer(self.workspace_root, validate_workspace=False)
            except (ImportError, AttributeError, TypeError):
                # If even GenericAnalyzer fails, use minimal analyzer
                logger.critical("All analyzer creation failed. Using minimal analyzer.")
                return MinimalAnalyzer(self.workspace_root, validate_workspace=False)
        except (ImportError, AttributeError, TypeError) as e:
            logger.warning(
                "Failed to create %s analyzer: %s. Using generic analyzer.", analyzer_type, e
            )
            try:
                return GenericAnalyzer(self.workspace_root, validate_workspace=False)
            except (ImportError, AttributeError, TypeError):
                # If even GenericAnalyzer fails, use minimal analyzer
                logger.critical("All analyzer creation failed. Using minimal analyzer.")
                return MinimalAnalyzer(self.workspace_root, validate_workspace=False)

    def _create_python_analyzer(self):
        try:
            from .languages.python_analyzer import PythonAnalyzer  # noqa: E402

            return PythonAnalyzer(self.workspace_root, validate_workspace=False)
        except (ImportError, AttributeError) as e:
            logger.warning("Failed to create Python analyzer: %s. Using generic analyzer.", e)
            return None

    def _create_javascript_analyzer(self):
        try:
            from .languages.javascript_analyzer import JavaScriptAnalyzer  # noqa: E402

            return JavaScriptAnalyzer(self.workspace_root, validate_workspace=False)
        except (ImportError, AttributeError) as e:
            logger.warning("Failed to create JavaScript analyzer: %s. Using generic analyzer.", e)
            return None

    def _create_typescript_analyzer(self):
        try:
            from .languages.typescript_analyzer import TypeScriptAnalyzer  # noqa: E402

            return TypeScriptAnalyzer(self.workspace_root, validate_workspace=False)
        except (ImportError, AttributeError) as e:
            logger.warning("Failed to create TypeScript analyzer: %s. Using generic analyzer.", e)
            return None

    def _create_minimal_analyzer(self, file_path: Optional[Path] = None) -> BaseAnalyzer:
        """Create a minimal analyzer as last resort fallback.

        Args:
            file_path: Unused, present for interface compatibility.
        Returns:
            BaseAnalyzer: Minimal analyzer instance that can handle basic operations
        """
        _ = file_path
        try:
            return GenericAnalyzer(self.workspace_root, validate_workspace=False)
        except Exception:
            # If even GenericAnalyzer fails, create a truly minimal implementation
            logger.critical("All analyzer creation failed. Creating emergency minimal analyzer.")
            return MinimalAnalyzer(self.workspace_root, validate_workspace=False)

    def can_analyze(self, file_path: Path) -> bool:
        """Check if file can be analyzed.

        Returns True for all files since we have generic analyzer as fallback.

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if file can be analyzed (always True due to generic fallback)
        """
        _ = file_path
        return True  # We can analyze any file type due to generic analyzer fallback

    def get_supported_extensions(self) -> Dict[str, str]:
        """Get mapping of supported file extensions to analyzer types.

        Returns:
            Dict[str, str]: Mapping of file extensions to analyzer types
        """
        return self._extensions.copy()

    def get_analyzer_type(self, file_path: Path) -> str:
        """Get the analyzer type for a given file path.

        Args:
            file_path: Path to the file

        Returns:
            str: Analyzer type ('python', 'javascript', 'typescript', or 'generic')
        """
        extension = Path(file_path).suffix.lower()
        return self._extensions.get(extension, "generic")

    def clear_cache(self) -> None:
        """Clear the analyzer cache.

        Useful for testing or when you want to force recreation of analyzers.
        """
        self._analyzer_cache.clear()
        logger.debug("Analyzer cache cleared")

    def get_cache_info(self) -> Dict[str, int]:
        """Get information about cached analyzers.

        Returns:
            Dict[str, int]: Information about cache size and contents
        """
        cache_info = {
            "total_cached": len(self._analyzer_cache),
            "cached_types": len(set(self._analyzer_cache.keys())),
        }

        # Count analyzers by type
        for analyzer_type in self._analyzer_cache:
            cache_info[f"{analyzer_type}_cached"] = 1

        return cache_info


def get_analyzer_factory(workspace_root: Path) -> AnalyzerFactory:
    """Get analyzer factory instance.

    Args:
        workspace_root: Root directory of the workspace

    Returns:
        AnalyzerFactory: Configured analyzer factory instance
    """
    return AnalyzerFactory(workspace_root)
