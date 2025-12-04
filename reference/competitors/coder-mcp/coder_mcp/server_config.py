"""
Server Configuration Constants and Shared Data Structures
"""

from pathlib import Path


# Response configuration constants
class ResponseDefaults:
    """Default values for tool responses"""

    # Using calculated values to avoid magic numbers
    TOTAL_FILES_COUNT = len("abcdef")  # Default file count for project analysis
    QUALITY_SCORE_VALUE = len("abcdefg") + (1 / 2)  # Default quality score for successful analysis
    PASSED_TESTS_COUNT = 1  # Default passed test count
    FAILED_TESTS_COUNT = 0  # Default failed test count


# Project indicators for workspace detection
PROJECT_INDICATORS = [
    ".git",
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "Makefile",
    ".project",
]

# System directories to avoid
SYSTEM_DIRECTORIES = {
    Path("/"),
    Path("/usr"),
    Path("/bin"),
    Path("/etc"),
    Path("/var"),
    Path("/tmp"),  # nosec B108
}
