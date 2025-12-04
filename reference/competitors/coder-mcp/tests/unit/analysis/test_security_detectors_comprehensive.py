"""Comprehensive tests for security detection functionality."""

from unittest.mock import Mock, patch

import pytest

from coder_mcp.analysis.detectors.security.coordinator import SecurityIssueDetector


class TestSecurityIssueDetector:
    """Test SecurityIssueDetector coordinator class."""

    @pytest.fixture
    def detector(self):
        """Create SecurityIssueDetector instance."""
        return SecurityIssueDetector()

    @pytest.fixture
    def sample_security_issues(self):
        """Sample security issues for testing."""
        return [
            {
                "type": "sql_injection",
                "severity": "critical",
                "file": "test.py",
                "line": 10,
                "description": "SQL injection vulnerability",
                "suggestion": "Use parameterized queries",
                "cwe_id": "CWE-89",
                "owasp_category": "Injection",
                "code_snippet": "query = 'SELECT * FROM users WHERE id = ' + user_id",
            },
            {
                "type": "weak_crypto",
                "severity": "high",
                "file": "test.py",
                "line": 25,
                "description": "Weak cryptographic algorithm",
                "suggestion": "Use strong encryption algorithms",
                "cwe_id": "CWE-327",
                "owasp_category": "Cryptographic Failures",
                "code_snippet": "md5.new(data)",
            },
            {
                "type": "hardcoded_secret",
                "severity": "medium",
                "file": "config.py",
                "line": 5,
                "description": "Hardcoded API key",
                "suggestion": "Use environment variables",
                "cwe_id": "CWE-798",
                "owasp_category": "Sensitive Data Exposure",
                "code_snippet": "API_KEY = 'sk-1234567890abcdef'",
            },
        ]

    def test_initialization_default(self, detector):
        """Test default initialization."""
        assert detector.max_issues_per_type == SecurityIssueDetector.DEFAULT_MAX_ISSUES_PER_TYPE
        assert hasattr(detector, "injection_detector")
        assert hasattr(detector, "crypto_detector")
        assert hasattr(detector, "auth_detector")
        assert hasattr(detector, "input_detector")
        assert hasattr(detector, "function_detector")
        assert hasattr(detector, "secret_detector")
        assert hasattr(detector, "network_detector")

    def test_initialization_custom_max_issues(self):
        """Test initialization with custom max issues."""
        detector = SecurityIssueDetector(max_issues_per_type=50)
        assert detector.max_issues_per_type == 50

    def test_detect_security_issues_empty_content(self, detector, tmp_path):
        """Test detection with empty content."""
        test_file = tmp_path / "empty.py"

        issues = detector.detect_security_issues("", test_file)

        assert issues == []

    def test_detect_security_issues_whitespace_only(self, detector, tmp_path):
        """Test detection with whitespace-only content."""
        test_file = tmp_path / "whitespace.py"

        issues = detector.detect_security_issues("   \n\t  \n", test_file)

        assert issues == []

    @patch.object(SecurityIssueDetector, "_get_enabled_detectors")
    @patch.object(SecurityIssueDetector, "_sort_and_deduplicate_issues")
    def test_detect_security_issues_detector_execution(
        self, mock_sort, mock_enabled, detector, tmp_path
    ):
        """Test that detectors are executed properly."""
        test_file = tmp_path / "test.py"
        content = "print('test')"

        # Mock enabled detectors
        mock_detector = Mock()
        mock_detector.detect_vulnerabilities.return_value = []
        mock_enabled.return_value = {"test": mock_detector}
        mock_sort.return_value = []

        detector.detect_security_issues(content, test_file)

        # Verify detector was called
        mock_detector.detect_vulnerabilities.assert_called_once_with(
            content, content.splitlines(), test_file
        )
        mock_sort.assert_called_once()

    def test_get_enabled_detectors_all_enabled(self, detector):
        """Test getting all enabled detectors."""
        detector_map = {"detector1": Mock(), "detector2": Mock()}

        result = detector._get_enabled_detectors(detector_map, None)

        assert result == detector_map

    def test_get_enabled_detectors_selective(self, detector):
        """Test getting selectively enabled detectors."""
        detector_map = {"detector1": Mock(), "detector2": Mock(), "detector3": Mock()}

        result = detector._get_enabled_detectors(detector_map, ["detector1", "detector3"])

        assert len(result) == 2
        assert "detector1" in result
        assert "detector3" in result
        assert "detector2" not in result

    def test_sort_and_deduplicate_issues_empty(self, detector):
        """Test sorting and deduplication with empty list."""
        result = detector._sort_and_deduplicate_issues([])

        assert result == []

    def test_sort_and_deduplicate_issues_sorting(self, detector, sample_security_issues):
        """Test that issues are sorted by severity."""
        result = detector._sort_and_deduplicate_issues(sample_security_issues)

        # Should be sorted by severity: critical, high, medium, low
        assert result[0]["severity"] == "critical"
        assert result[1]["severity"] == "high"
        assert result[2]["severity"] == "medium"

    def test_sort_and_deduplicate_issues_deduplication(self, detector):
        """Test deduplication of similar issues."""
        duplicate_issues = [
            {"type": "test", "file": "test.py", "line": 1, "severity": "high"},
            {"type": "test", "file": "test.py", "line": 1, "severity": "high"},  # Duplicate
            {"type": "test", "file": "test.py", "line": 2, "severity": "medium"},  # Different line
        ]

        result = detector._sort_and_deduplicate_issues(duplicate_issues)

        assert len(result) == 2  # Duplicate removed

    def test_create_security_issue_basic(self, detector, tmp_path):
        """Test basic security issue creation."""
        test_file = tmp_path / "test.py"
        issue_config = {
            "issue_type": "test_issue",
            "severity": "high",
            "file_path": test_file,
            "line_number": 10,
            "description": "Test issue",
            "recommendation": "Fix the issue",
            "cwe_id": "CWE-123",
            "owasp_category": "Test Category",
            "code_snippet": "test code",
        }

        result = detector._create_security_issue(issue_config)

        assert result["type"] == "test_issue"
        assert result["severity"] == "high"
        assert result["line"] == 10
        assert result["description"] == "Test issue"
        assert result["suggestion"] == "Fix the issue"
        assert result["cwe_id"] == "CWE-123"
        assert result["owasp_category"] == "Test Category"
        assert result["code_snippet"] == "test code"

    def test_create_security_issue_defaults(self, detector):
        """Test security issue creation with defaults."""
        issue_config = {}

        result = detector._create_security_issue(issue_config)

        assert result["type"] == "unknown"
        assert result["severity"] == "medium"
        assert result["file"] == "unknown"
        assert result["line"] == 0
        assert result["description"] == "Security issue detected"
        assert result["suggestion"] == "Review code for security implications"

    def test_create_security_issue_path_conversion(self, detector, tmp_path):
        """Test file path conversion in issue creation."""
        test_file = tmp_path / "subdir" / "test.py"
        test_file.parent.mkdir(parents=True)

        issue_config = {"file_path": test_file}

        result = detector._create_security_issue(issue_config)

        assert isinstance(result["file"], str)

    def test_create_security_issue_exception_handling(self, detector):
        """Test exception handling in issue creation."""
        # Pass invalid data that could cause exceptions
        issue_config = {"file_path": None, "line_number": "invalid"}

        result = detector._create_security_issue(issue_config)

        # Should return basic issue with defaults (not fallback error)
        assert result["type"] == "unknown"
        assert result["severity"] == "medium"

    def test_get_security_statistics_empty(self, detector):
        """Test statistics generation with empty issues."""
        result = detector.get_security_statistics([])

        assert result["total_issues"] == 0
        assert result["critical_issues"] == 0
        assert result["high_issues"] == 0
        assert result["medium_issues"] == 0
        assert result["low_issues"] == 0
        assert result["most_common_cwe"] is None
        assert result["files_affected"] == 0
        assert result["owasp_categories"] == []
        assert result["type_distribution"] == {}
        assert result["security_score"] == 100

    def test_get_security_statistics_with_issues(self, detector, sample_security_issues):
        """Test statistics generation with sample issues."""
        result = detector.get_security_statistics(sample_security_issues)

        assert result["total_issues"] == 3
        assert result["critical_issues"] == 1
        assert result["high_issues"] == 1
        assert result["medium_issues"] == 1
        assert result["low_issues"] == 0
        assert result["files_affected"] == 2  # test.py and config.py
        assert len(result["owasp_categories"]) == 3
        assert "sql_injection" in result["type_distribution"]
        assert result["security_score"] < 100  # Should be lower with issues

    def test_count_by_severity(self, detector, sample_security_issues):
        """Test severity counting."""
        result = detector._count_by_severity(sample_security_issues)

        assert result["critical"] == 1
        assert result["high"] == 1
        assert result["medium"] == 1
        assert result["low"] == 0

    def test_find_most_common_cwe_no_cwe(self, detector):
        """Test most common CWE with no CWE IDs."""
        issues = [{"type": "test", "cwe_id": None}]

        result = detector._find_most_common_cwe(issues)

        assert result is None

    def test_find_most_common_cwe_with_cwe(self, detector):
        """Test most common CWE with CWE IDs."""
        issues = [{"cwe_id": "CWE-89"}, {"cwe_id": "CWE-89"}, {"cwe_id": "CWE-327"}]  # Most common

        result = detector._find_most_common_cwe(issues)

        assert result == "CWE-89"

    def test_get_unique_owasp_categories(self, detector, sample_security_issues):
        """Test getting unique OWASP categories."""
        result = detector._get_unique_owasp_categories(sample_security_issues)

        assert len(result) == 3
        assert "Injection" in result
        assert "Cryptographic Failures" in result
        assert "Sensitive Data Exposure" in result
        assert result == sorted(result)  # Should be sorted

    def test_get_type_distribution(self, detector, sample_security_issues):
        """Test getting type distribution."""
        result = detector._get_type_distribution(sample_security_issues)

        assert result["sql_injection"] == 1
        assert result["weak_crypto"] == 1
        assert result["hardcoded_secret"] == 1

    def test_calculate_security_score_no_issues(self, detector):
        """Test security score calculation with no issues."""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        score = detector._calculate_security_score(severity_counts, 0)

        assert score == 100.0

    def test_calculate_security_score_with_issues(self, detector):
        """Test security score calculation with various issues."""
        severity_counts = {"critical": 1, "high": 1, "medium": 1, "low": 1}

        score = detector._calculate_security_score(severity_counts, 4)

        assert 0 <= score <= 100
        assert score < 100  # Should be lower with issues

    def test_calculate_security_score_critical_heavy(self, detector):
        """Test security score with many critical issues."""
        severity_counts = {"critical": 5, "high": 0, "medium": 0, "low": 0}

        score = detector._calculate_security_score(severity_counts, 5)

        assert score == 0.0  # Should be 0 with all critical issues

    def test_severity_constants(self):
        """Test that severity constants are defined correctly."""
        assert SecurityIssueDetector.CRITICAL == "critical"
        assert SecurityIssueDetector.HIGH == "high"
        assert SecurityIssueDetector.MEDIUM == "medium"
        assert SecurityIssueDetector.LOW == "low"

    def test_default_constants(self):
        """Test default configuration constants."""
        assert SecurityIssueDetector.DEFAULT_MAX_ISSUES_PER_TYPE == 100
        assert SecurityIssueDetector.DEFAULT_ENABLE_ALL_DETECTORS is True
