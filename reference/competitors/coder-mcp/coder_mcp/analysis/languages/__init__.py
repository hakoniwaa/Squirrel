"""
Language-specific analyzers for different programming languages.

This module provides specialized code analyzers for various programming languages,
each tailored to understand the syntax, patterns, and best practices specific to
that language. The analyzers work together to provide comprehensive code quality
assessment across different file types.

Available Analyzers:
    PythonAnalyzer: Comprehensive Python code analysis with AST parsing
    JavaScriptAnalyzer: JavaScript/ECMAScript analysis with modern patterns
    TypeScriptAnalyzer: TypeScript analysis with type safety checks
    GenericAnalyzer: Universal fallback analyzer for unsupported file types

Usage:
    from coder_mcp.analysis.languages import PythonAnalyzer, GenericAnalyzer

    analyzer = PythonAnalyzer(workspace_root)
    result = await analyzer.analyze_file(file_path, "deep")

Version: 2.0.0
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, TypedDict, Union, cast

from ..base_analyzer import BaseAnalyzer
from .generic_analyzer import GenericAnalyzer
from .javascript_analyzer import JavaScriptAnalyzer
from .python_analyzer import PythonAnalyzer
from .typescript_analyzer import TypeScriptAnalyzer

# Version information
__version__ = "2.0.0"
__author__ = "Coder MCP Team"

# Primary exports
__all__ = [
    # Core analyzers
    "PythonAnalyzer",
    "JavaScriptAnalyzer",
    "TypeScriptAnalyzer",
    "GenericAnalyzer",
    # Utility functions
    "get_analyzer_for_file",
    "get_supported_languages",
    "create_analyzer_registry",
    # Constants
    "SUPPORTED_LANGUAGES",
    "DEFAULT_ANALYZER",
]


# Language support mapping
class LanguageConfig(TypedDict):
    analyzer: Any
    extensions: List[str]
    description: str


SUPPORTED_LANGUAGES: Dict[str, LanguageConfig] = {
    "python": {
        "analyzer": PythonAnalyzer,
        "extensions": [".py", ".pyw", ".pyi"],
        "description": "Python programming language support with AST analysis",
    },
    "javascript": {
        "analyzer": JavaScriptAnalyzer,
        "extensions": [".js", ".mjs", ".jsx"],
        "description": "JavaScript/ECMAScript support with modern syntax",
    },
    "typescript": {
        "analyzer": TypeScriptAnalyzer,
        "extensions": [".ts", ".tsx", ".d.ts"],
        "description": "TypeScript support with type analysis",
    },
    "generic": {
        "analyzer": GenericAnalyzer,
        "extensions": ["*"],
        "description": "Universal text file analysis for unsupported languages",
    },
}

# Default analyzer for unknown file types
DEFAULT_ANALYZER = "generic"


def get_analyzer_for_file(file_path: Union[str, Path], workspace_root: Path) -> BaseAnalyzer:
    """Get the appropriate analyzer for a given file.

    This function determines the best analyzer to use based on the file extension
    and returns an initialized analyzer instance.

    Args:
        file_path: Path to the file to analyze
        workspace_root: Root directory of the workspace

    Returns:
        Initialized analyzer instance

    Raises:
        ValueError: If workspace_root is invalid

    Example:
        >>> analyzer = get_analyzer_for_file("script.py", Path("/workspace"))
        >>> isinstance(analyzer, PythonAnalyzer)
        True
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    file_extension = file_path.suffix.lower()

    # Find matching language analyzer
    for language, config in SUPPORTED_LANGUAGES.items():
        extensions = cast(List[str], config["extensions"])
        if extensions == ["*"] or file_extension in extensions:
            analyzer_class = config["analyzer"]
            if callable(analyzer_class):
                return cast(BaseAnalyzer, analyzer_class(workspace_root))
            else:
                raise TypeError(f"Analyzer class for {language} is not callable: {analyzer_class}")

    # Fallback to generic analyzer
    return GenericAnalyzer(workspace_root)


def get_supported_languages() -> Dict[str, Dict[str, Union[str, List[str]]]]:
    """Get information about all supported languages.

    Returns:
        Dictionary mapping language names to their configuration

    Example:
        >>> languages = get_supported_languages()
        >>> "python" in languages
        True
        >>> languages["python"]["extensions"]
        ['.py', '.pyw', '.pyi']
    """
    return {
        lang: {
            "extensions": config["extensions"].copy(),
            "description": config["description"],
        }
        for lang, config in SUPPORTED_LANGUAGES.items()
    }


def create_analyzer_registry(workspace_root: Path) -> Dict[str, BaseAnalyzer]:
    """Create a registry of all available analyzers.

    This function creates instances of all available analyzers, which can be
    useful for bulk operations or when you need to work with multiple analyzers.

    Args:
        workspace_root: Root directory of the workspace

    Returns:
        Dictionary mapping language names to analyzer instances

    Raises:
        ValueError: If workspace_root is invalid

    Example:
        >>> registry = create_analyzer_registry(Path("/workspace"))
        >>> "python" in registry
        True
        >>> isinstance(registry["python"], PythonAnalyzer)
        True
    """
    registry = {}
    for language, config in SUPPORTED_LANGUAGES.items():
        analyzer_class = config["analyzer"]
        try:
            registry[language] = cast(BaseAnalyzer, analyzer_class(workspace_root))
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning("Failed to create %s analyzer: %s", language, e)
    return registry


def get_file_language(file_path: Union[str, Path]) -> str:
    """Determine the language of a file based on its extension.

    Args:
        file_path: Path to the file

    Returns:
        Language name or "generic" if not recognized

    Example:
        >>> get_file_language("script.py")
        'python'
        >>> get_file_language("readme.txt")
        'generic'
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    file_extension = file_path.suffix.lower()

    for language, config in SUPPORTED_LANGUAGES.items():
        extensions = cast(List[str], config["extensions"])
        if extensions != ["*"] and file_extension in extensions:
            return language

    return DEFAULT_ANALYZER


def is_supported_file(file_path: Union[str, Path]) -> bool:
    """Check if a file is supported by any analyzer.

    Args:
        file_path: Path to check

    Returns:
        True if file is supported (always True since GenericAnalyzer handles all)

    Example:
        >>> is_supported_file("script.py")
        True
        >>> is_supported_file("binary.exe")
        True  # GenericAnalyzer can handle any file
    """
    # Since GenericAnalyzer handles all file types, everything is "supported"
    return True


# Module metadata
__doc_format__ = "google"
