"""
Test coverage estimation and analysis

This module handles test coverage estimation using both actual coverage data
and heuristic analysis when coverage data is not available.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from ..exceptions import CoverageDataError
from ..protocols import CoverageEstimatorProtocol


class CoverageCalculation:
    """Coverage calculation configuration based on empirical data"""

    # Base percentages derived from industry research and best practices
    PERFECT_COVERAGE_PERCENTAGE = 100.0
    HIGH_COVERAGE_PERCENTAGE = 85.0
    BASE_COVERAGE_PERCENTAGE = 30.0
    MAX_COVERAGE_NON_TEST = 95.0

    # Boost factors based on code quality indicators
    # These are derived from analysis of well-tested codebases
    TEST_FILE_BOOST_FACTOR = 40.0  # Having corresponding test files
    DOCUMENTATION_BOOST_FACTOR = 15.0  # Good documentation indicates thoughtful code
    DEFENSIVE_CODE_BOOST_FACTOR = 15.0  # Error handling and validation

    # Quality indicator patterns
    DEFENSIVE_PATTERNS = [
        "assert",
        "raise",
        "except",
        "try:",
        "if __name__",
        "TypeError",
        "ValueError",
        "isinstance",
    ]

    # Documentation patterns
    DOCUMENTATION_PATTERNS = ['"""', "'''"]

    # Test file indicators
    TEST_FILE_INDICATORS = ["test_", "_test", "tests", "spec_", "_spec"]

    # Project root indicators for finding coverage files
    PROJECT_ROOT_INDICATORS = [
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        ".git",
        "Pipfile",
        "poetry.lock",
        "tox.ini",
        "pytest.ini",
    ]


class FilePathMatcher:
    """Handles complex file path matching for coverage data"""

    def __init__(self, target_path: str, relative_path: str, file_key: str, file_path: Path):
        self.target_path = target_path
        self.relative_path = relative_path
        self.file_key = file_key
        self.file_path = file_path

    def matches(self) -> bool:
        """Check if file_key matches the target file using various strategies"""
        return self._check_path_endings() or self._check_name_match() or self._check_path_contains()

    def _check_path_endings(self) -> bool:
        """Check if paths end with the file key"""
        return self.target_path.endswith(self.file_key) or self.relative_path.endswith(
            self.file_key
        )

    def _check_name_match(self) -> bool:
        """Check if file key ends with the file name"""
        return self.file_key.endswith(str(self.file_path.name))

    def _check_path_contains(self) -> bool:
        """Check if paths contain each other (normalized)"""
        normalized_file_path = str(self.file_path).replace("\\", "/")
        normalized_file_key = self.file_key.replace("\\", "/")

        return (
            normalized_file_path in normalized_file_key
            or normalized_file_key in normalized_file_path
        )


class CoverageScorer:
    """Calculates coverage scores based on code quality indicators"""

    def __init__(self, lines: List[str], has_test_file: bool):
        self.lines = lines
        self.has_test_file = has_test_file
        self.total_lines = self._count_code_lines()

    def _count_code_lines(self) -> int:
        """Count actual code lines (exclude blank and comment lines)"""
        return len(
            [line for line in self.lines if line.strip() and not line.strip().startswith("#")]
        )

    def calculate_score(self) -> float:
        """Calculate the overall coverage score"""
        if self.total_lines == 0:
            return 0.0

        score = CoverageCalculation.BASE_COVERAGE_PERCENTAGE
        score += self._get_test_boost()
        score += self._get_defensive_boost()
        score += self._get_documentation_boost()

        return min(CoverageCalculation.MAX_COVERAGE_NON_TEST, score)

    def _get_test_boost(self) -> float:
        """Get boost for having test files"""
        return CoverageCalculation.TEST_FILE_BOOST_FACTOR if self.has_test_file else 0.0

    def _get_defensive_boost(self) -> float:
        """Get boost for defensive programming patterns"""
        defensive_count = self._count_pattern_occurrences(CoverageCalculation.DEFENSIVE_PATTERNS)

        if defensive_count == 0:
            return 0.0

        # Calculate ratio with reasonable scaling
        defensive_ratio = min(1.0, defensive_count / self.total_lines * 10)
        return defensive_ratio * CoverageCalculation.DEFENSIVE_CODE_BOOST_FACTOR

    def _get_documentation_boost(self) -> float:
        """Get boost for documentation patterns"""
        doc_count = self._count_pattern_occurrences(CoverageCalculation.DOCUMENTATION_PATTERNS)
        return CoverageCalculation.DOCUMENTATION_BOOST_FACTOR if doc_count > 0 else 0.0

    def _count_pattern_occurrences(self, patterns: List[str]) -> int:
        """Count occurrences of patterns in code"""
        return sum(1 for line in self.lines for pattern in patterns if pattern in line)


class CoverageFileLocator:
    """Locates and processes coverage data files"""

    def find_coverage_file(self, file_path: Path) -> Optional[Path]:
        """Find coverage.json file in project hierarchy"""
        project_root = self._find_project_root(file_path)

        coverage_paths = [
            project_root / "coverage.json",
            Path.cwd() / "coverage.json",
            file_path.parent / "coverage.json",
        ]

        for path in coverage_paths:
            if path.exists():
                return path

        return None

    def _find_project_root(self, file_path: Path) -> Path:
        """Find project root by looking for common project files"""
        current = file_path.parent if file_path.is_file() else file_path

        while current != current.parent:
            if any(
                (current / indicator).exists()
                for indicator in CoverageCalculation.PROJECT_ROOT_INDICATORS
            ):
                return current
            current = current.parent

        return Path.cwd()

    def load_coverage_data(self, coverage_file: Path) -> Dict:
        """Load and validate coverage data from file"""
        try:
            with open(coverage_file, "r") as f:
                coverage_data = json.load(f)

            if not isinstance(coverage_data, dict):
                raise CoverageDataError("Coverage data must be a dictionary", str(coverage_file))

            return coverage_data

        except json.JSONDecodeError as e:
            raise CoverageDataError(f"Invalid JSON in coverage file: {e}", str(coverage_file))
        except Exception as e:
            raise CoverageDataError(f"Error reading coverage file: {e}", str(coverage_file))


class TestFileDetector:
    """Detects test files and relationships"""

    def is_test_file(self, file_name: str) -> bool:
        """Check if file is a test file based on naming conventions"""
        file_name_lower = file_name.lower()
        return any(
            indicator in file_name_lower for indicator in CoverageCalculation.TEST_FILE_INDICATORS
        )

    def has_test_file(self, file_path: Path) -> bool:
        """Check if there's a corresponding test file"""
        try:
            test_patterns = self._generate_test_patterns(file_path)
            return any(test_file.exists() for test_file in test_patterns)
        except (OSError, AttributeError):
            return False

    def _generate_test_patterns(self, file_path: Path) -> List[Path]:
        """Generate possible test file paths"""
        return [
            file_path.parent / f"test_{file_path.stem}.py",
            file_path.parent / f"{file_path.stem}_test.py",
            file_path.parent / "tests" / f"test_{file_path.stem}.py",
            file_path.parent.parent / "tests" / f"test_{file_path.stem}.py",
            file_path.parent / "test" / f"test_{file_path.stem}.py",
        ]


class CoverageEstimator(CoverageEstimatorProtocol):
    """Main coverage estimation coordinator"""

    def __init__(self):
        self.file_locator = CoverageFileLocator()
        self.test_detector = TestFileDetector()

    def estimate_test_coverage(self, file_path: Path, content: str) -> float:
        """Get actual test coverage from coverage data, fallback to estimation"""
        # First, try to get actual coverage data
        actual_coverage = self._get_actual_coverage(file_path)
        if actual_coverage is not None:
            return actual_coverage

        # Fallback to heuristic estimation
        return self._estimate_coverage_heuristic(file_path, content)

    def _get_actual_coverage(self, file_path: Path) -> Optional[float]:
        """Get actual test coverage from coverage.json file"""
        try:
            coverage_file = self.file_locator.find_coverage_file(file_path)
            if not coverage_file:
                return None

            coverage_data = self.file_locator.load_coverage_data(coverage_file)
            return self._extract_file_coverage(file_path, coverage_data)

        except CoverageDataError:
            # Silently fail and fall back to heuristics
            return None

    def _extract_file_coverage(self, file_path: Path, coverage_data: Dict) -> Optional[float]:
        """Extract coverage percentage for specific file"""
        # Normalize file path for comparison
        target_path = str(file_path.resolve())
        relative_path = str(file_path)

        files_data = coverage_data.get("files", {})

        for file_key, file_info in files_data.items():
            if self._is_same_file(target_path, relative_path, file_key, file_path):
                summary = file_info.get("summary", {})
                coverage_percent = summary.get("percent_covered")

                if coverage_percent is not None:
                    return float(coverage_percent)

        return None

    def _is_same_file(
        self, target_path: str, relative_path: str, file_key: str, file_path: Path
    ) -> bool:
        """Check if file_key matches the target file"""
        matcher = FilePathMatcher(target_path, relative_path, file_key, file_path)
        return matcher.matches()

    def _estimate_coverage_heuristic(self, file_path: Path, content: str) -> float:
        """Fallback heuristic estimation of test coverage"""
        file_name = file_path.name.lower()

        # Check if this is a test file
        if self.test_detector.is_test_file(file_name):
            return CoverageCalculation.HIGH_COVERAGE_PERCENTAGE

        # Check for corresponding test file
        has_test_file = self.test_detector.has_test_file(file_path)

        # Analyze content for quality indicators
        lines = content.splitlines()
        scorer = CoverageScorer(lines, has_test_file)

        return scorer.calculate_score()
