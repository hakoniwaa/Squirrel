"""
Security audit service for Memori database operations
Provides comprehensive security validation and monitoring
"""

import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .exceptions import SecurityError
from .input_validator import InputValidator


class SecurityLevel(str, Enum):
    """Security severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(str, Enum):
    """Types of security vulnerabilities"""

    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXPOSURE = "data_exposure"
    WEAK_VALIDATION = "weak_validation"


@dataclass
class SecurityFinding:
    """Represents a security finding"""

    vulnerability_type: VulnerabilityType
    severity: SecurityLevel
    description: str
    location: str
    recommendation: str
    evidence: str | None = None
    remediation_code: str | None = None


@dataclass
class SecurityAuditReport:
    """Security audit report"""

    findings: list[SecurityFinding]
    total_queries_audited: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    audit_timestamp: float
    overall_risk_score: float


class DatabaseSecurityAuditor:
    """Comprehensive security auditor for database operations"""

    # Advanced SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        # Union-based injection
        r"\bunion\s+select\b",
        r"\bunion\s+all\s+select\b",
        # Boolean-based injection
        r"\b(and|or)\s+\d+\s*=\s*\d+",
        r"\b(and|or)\s+.+\s*(like|=)\s*.+",
        # Time-based injection
        r"\bwaitfor\s+delay\b",
        r"\bsleep\s*\(",
        r"\bbenchmark\s*\(",
        r"\bpg_sleep\s*\(",
        # Comment-based injection
        r"--\s*[^\r\n]*",
        r"/\*.*?\*/",
        r"\#[^\r\n]*",
        # Stacked queries
        r";\s*(select|insert|update|delete|drop|create|alter)",
        # Information gathering
        r"\binformation_schema\b",
        r"\bsys\.|sysobjects|syscolumns",
        r"\bmysql\.user\b",
        r"\bpg_tables\b",
        # Dangerous functions
        r"\bxp_cmdshell\b",
        r"\bsp_executesql\b",
        r"\bexec\s*\(",
        r"\beval\s*\(",
        # File operations
        r"\binto\s+outfile\b",
        r"\binto\s+dumpfile\b",
        r"\bload_file\s*\(",
        r"\bcopy\s+.*\bfrom\b",
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>",
        r"<applet[^>]*>.*?</applet>",
        r"javascript\s*:",
        r"on\w+\s*=",
        r"expression\s*\(",
        r"url\s*\(",
        r"@import",
    ]

    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",
        r"\$\([^)]+\)",
        r"`[^`]+`",
        r"\|\s*(cat|ls|pwd|whoami|id|uname)",
        r"(^|\s)(wget|curl|nc|netcat|telnet|ssh)\s",
        r"\b(rm|mv|cp|chmod|chown|kill)\s",
    ]

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e\\",
        r"..%252f",
        r"..%255c",
    ]

    def __init__(self):
        self.findings = []
        self.queries_audited = 0
        self.blocked_operations = set()

    def audit_query(
        self,
        query: str,
        params: list[Any] | None = None,
        context: str | None = None,
    ) -> list[SecurityFinding]:
        """Audit a single database query for security vulnerabilities"""
        findings = []
        self.queries_audited += 1

        # Audit SQL injection
        sql_findings = self._audit_sql_injection(query, params, context)
        findings.extend(sql_findings)

        # Audit parameter validation
        param_findings = self._audit_parameter_validation(query, params, context)
        findings.extend(param_findings)

        # Audit privilege operations
        privilege_findings = self._audit_privilege_operations(query, context)
        findings.extend(privilege_findings)

        # Audit data exposure
        exposure_findings = self._audit_data_exposure(query, context)
        findings.extend(exposure_findings)

        return findings

    def _audit_sql_injection(
        self, query: str, params: list[Any] | None, context: str | None
    ) -> list[SecurityFinding]:
        """Audit for SQL injection vulnerabilities"""
        findings = []
        query_lower = query.lower()

        # Check for dangerous patterns
        for pattern in self.SQL_INJECTION_PATTERNS:
            matches = re.finditer(pattern, query_lower, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                findings.append(
                    SecurityFinding(
                        vulnerability_type=VulnerabilityType.SQL_INJECTION,
                        severity=SecurityLevel.CRITICAL,
                        description=f"Potential SQL injection pattern detected: {pattern}",
                        location=context or "unknown",
                        recommendation="Use parameterized queries and input validation",
                        evidence=f"Match: '{match.group()}' at position {match.start()}",
                        remediation_code="Use ? or %s placeholders with parameter binding",
                    )
                )

        # Check for string concatenation in queries
        if any(char in query for char in ["+", "||"]) and "VALUES" in query.upper():
            findings.append(
                SecurityFinding(
                    vulnerability_type=VulnerabilityType.SQL_INJECTION,
                    severity=SecurityLevel.HIGH,
                    description="String concatenation detected in SQL query",
                    location=context or "unknown",
                    recommendation="Use parameterized queries instead of string concatenation",
                    evidence="Query contains string concatenation operators",
                )
            )

        # Check if parameters are properly used
        if params is None and any(var in query_lower for var in ["%s", "?"]):
            findings.append(
                SecurityFinding(
                    vulnerability_type=VulnerabilityType.WEAK_VALIDATION,
                    severity=SecurityLevel.MEDIUM,
                    description="Query has parameter placeholders but no parameters provided",
                    location=context or "unknown",
                    recommendation="Ensure all parameter placeholders have corresponding values",
                )
            )

        return findings

    def _audit_parameter_validation(
        self, query: str, params: list[Any] | None, context: str | None
    ) -> list[SecurityFinding]:
        """Audit parameter validation"""
        findings = []

        if params:
            for i, param in enumerate(params):
                # Check for potential XSS in parameters
                if isinstance(param, str):
                    for pattern in self.XSS_PATTERNS:
                        if re.search(pattern, param, re.IGNORECASE):
                            findings.append(
                                SecurityFinding(
                                    vulnerability_type=VulnerabilityType.XSS,
                                    severity=SecurityLevel.HIGH,
                                    description=f"XSS pattern in parameter {i}",
                                    location=context or "unknown",
                                    recommendation="Sanitize and validate input parameters",
                                    evidence=f"Parameter value: {param[:100]}...",
                                )
                            )

                    # Check for command injection
                    for pattern in self.COMMAND_INJECTION_PATTERNS:
                        if re.search(pattern, param):
                            findings.append(
                                SecurityFinding(
                                    vulnerability_type=VulnerabilityType.COMMAND_INJECTION,
                                    severity=SecurityLevel.CRITICAL,
                                    description=f"Command injection pattern in parameter {i}",
                                    location=context or "unknown",
                                    recommendation="Validate and sanitize all user input",
                                    evidence=f"Parameter value: {param[:100]}...",
                                )
                            )

                    # Check for path traversal
                    for pattern in self.PATH_TRAVERSAL_PATTERNS:
                        if re.search(pattern, param):
                            findings.append(
                                SecurityFinding(
                                    vulnerability_type=VulnerabilityType.PATH_TRAVERSAL,
                                    severity=SecurityLevel.HIGH,
                                    description=f"Path traversal pattern in parameter {i}",
                                    location=context or "unknown",
                                    recommendation="Validate file paths and restrict access",
                                    evidence=f"Parameter value: {param[:100]}...",
                                )
                            )

                # Check parameter size
                if isinstance(param, str) and len(param) > 10000:
                    findings.append(
                        SecurityFinding(
                            vulnerability_type=VulnerabilityType.DATA_EXPOSURE,
                            severity=SecurityLevel.MEDIUM,
                            description=f"Unusually large parameter {i} ({len(param)} chars)",
                            location=context or "unknown",
                            recommendation="Implement input length limits",
                            evidence=f"Parameter length: {len(param)} characters",
                        )
                    )

        return findings

    def _audit_privilege_operations(
        self, query: str, context: str | None
    ) -> list[SecurityFinding]:
        """Audit for privilege escalation attempts"""
        findings = []
        query_upper = query.upper().strip()

        # Dangerous DDL operations
        dangerous_ddl = ["DROP", "CREATE USER", "ALTER USER", "GRANT", "REVOKE"]
        for operation in dangerous_ddl:
            if query_upper.startswith(operation):
                findings.append(
                    SecurityFinding(
                        vulnerability_type=VulnerabilityType.PRIVILEGE_ESCALATION,
                        severity=SecurityLevel.CRITICAL,
                        description=f"Dangerous DDL operation: {operation}",
                        location=context or "unknown",
                        recommendation="Restrict DDL operations to administrative contexts",
                        evidence=f"Query starts with: {operation}",
                    )
                )

        # System function calls
        system_functions = [
            "SYSTEM",
            "SHELL",
            "EXEC",
            "EXECUTE",
            "XP_CMDSHELL",
            "SP_EXECUTESQL",
            "OPENROWSET",
            "OPENDATASOURCE",
        ]

        for func in system_functions:
            if func in query_upper:
                findings.append(
                    SecurityFinding(
                        vulnerability_type=VulnerabilityType.PRIVILEGE_ESCALATION,
                        severity=SecurityLevel.CRITICAL,
                        description=f"System function call detected: {func}",
                        location=context or "unknown",
                        recommendation="Avoid system function calls in application queries",
                        evidence=f"Function: {func}",
                    )
                )

        return findings

    def _audit_data_exposure(
        self, query: str, context: str | None
    ) -> list[SecurityFinding]:
        """Audit for potential data exposure issues"""
        findings = []
        query_upper = query.upper()

        # SELECT * queries (potential over-exposure)
        if re.search(r"SELECT\s+\*", query_upper):
            findings.append(
                SecurityFinding(
                    vulnerability_type=VulnerabilityType.DATA_EXPOSURE,
                    severity=SecurityLevel.MEDIUM,
                    description="SELECT * query may expose unnecessary data",
                    location=context or "unknown",
                    recommendation="Specify exact columns needed instead of using *",
                    evidence="Query uses SELECT *",
                )
            )

        # Missing WHERE clauses in UPDATE/DELETE
        if query_upper.startswith(("UPDATE", "DELETE")) and "WHERE" not in query_upper:
            findings.append(
                SecurityFinding(
                    vulnerability_type=VulnerabilityType.DATA_EXPOSURE,
                    severity=SecurityLevel.CRITICAL,
                    description="UPDATE/DELETE without WHERE clause",
                    location=context or "unknown",
                    recommendation="Always include WHERE clause in UPDATE/DELETE operations",
                    evidence="Missing WHERE clause",
                )
            )

        # Potential sensitive data in queries
        sensitive_keywords = [
            "PASSWORD",
            "TOKEN",
            "SECRET",
            "KEY",
            "PRIVATE",
            "SSN",
            "SOCIAL_SECURITY",
            "CREDIT_CARD",
            "CVV",
        ]

        for keyword in sensitive_keywords:
            if keyword in query_upper:
                findings.append(
                    SecurityFinding(
                        vulnerability_type=VulnerabilityType.DATA_EXPOSURE,
                        severity=SecurityLevel.HIGH,
                        description=f"Query references potentially sensitive data: {keyword}",
                        location=context or "unknown",
                        recommendation="Ensure sensitive data is properly protected and encrypted",
                        evidence=f"Keyword: {keyword}",
                    )
                )

        return findings

    def validate_query_safety(
        self,
        query: str,
        params: list[Any] | None = None,
        context: str | None = None,
        strict_mode: bool = True,
    ) -> tuple[bool, list[SecurityFinding]]:
        """Validate if a query is safe to execute"""
        findings = self.audit_query(query, params, context)

        # Determine if query should be blocked
        has_critical = any(f.severity == SecurityLevel.CRITICAL for f in findings)
        has_high = any(f.severity == SecurityLevel.HIGH for f in findings)

        is_safe = True
        if strict_mode:
            is_safe = not (has_critical or has_high)
        else:
            is_safe = not has_critical

        return is_safe, findings

    def generate_audit_report(self) -> SecurityAuditReport:
        """Generate comprehensive security audit report"""
        critical_count = sum(
            1 for f in self.findings if f.severity == SecurityLevel.CRITICAL
        )
        high_count = sum(1 for f in self.findings if f.severity == SecurityLevel.HIGH)
        medium_count = sum(
            1 for f in self.findings if f.severity == SecurityLevel.MEDIUM
        )
        low_count = sum(1 for f in self.findings if f.severity == SecurityLevel.LOW)

        # Calculate risk score (0-100)
        risk_score = min(
            100,
            (critical_count * 25 + high_count * 10 + medium_count * 5 + low_count * 1),
        )

        return SecurityAuditReport(
            findings=self.findings.copy(),
            total_queries_audited=self.queries_audited,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            audit_timestamp=time.time(),
            overall_risk_score=risk_score,
        )

    def get_remediation_suggestions(self) -> dict[VulnerabilityType, list[str]]:
        """Get remediation suggestions grouped by vulnerability type"""
        suggestions = {
            VulnerabilityType.SQL_INJECTION: [
                "Use parameterized queries with ? or %s placeholders",
                "Validate and sanitize all user inputs",
                "Implement input length limits",
                "Use ORM frameworks when possible",
                "Escape special SQL characters",
                "Implement allowlist validation for dynamic queries",
            ],
            VulnerabilityType.XSS: [
                "HTML encode all user input before display",
                "Use Content Security Policy (CSP) headers",
                "Validate input against expected patterns",
                "Sanitize data before database storage",
                "Implement output encoding",
            ],
            VulnerabilityType.COMMAND_INJECTION: [
                "Never pass user input directly to system commands",
                "Use allowlist validation for system operations",
                "Implement proper input validation",
                "Use safe APIs instead of shell commands",
                "Run applications with minimal privileges",
            ],
            VulnerabilityType.PATH_TRAVERSAL: [
                "Validate and sanitize all file paths",
                "Use absolute paths with validation",
                "Implement chroot or similar containment",
                "Restrict file system access permissions",
                "Use safe file handling libraries",
            ],
            VulnerabilityType.PRIVILEGE_ESCALATION: [
                "Implement proper access controls",
                "Use principle of least privilege",
                "Validate user permissions before operations",
                "Audit administrative operations",
                "Separate administrative and user interfaces",
            ],
            VulnerabilityType.DATA_EXPOSURE: [
                "Use specific column names instead of SELECT *",
                "Implement data classification and handling policies",
                "Use encryption for sensitive data",
                "Implement proper access logging",
                "Regular security audits of data access patterns",
            ],
        }
        return suggestions


class SecureQueryBuilder:
    """Helper class for building secure queries"""

    def __init__(self, auditor: DatabaseSecurityAuditor):
        self.auditor = auditor

    def build_safe_select(
        self,
        table: str,
        columns: list[str],
        where_conditions: dict[str, Any],
        limit: int | None = None,
    ) -> tuple[str, list[Any]]:
        """Build a safe SELECT query"""
        # Validate inputs
        table = InputValidator.sanitize_sql_identifier(table)
        validated_columns = [
            InputValidator.sanitize_sql_identifier(col) for col in columns
        ]

        # Build query
        columns_str = ", ".join(validated_columns)
        query = f"SELECT {columns_str} FROM {table}"
        params = []

        if where_conditions:
            where_parts = []
            for column, value in where_conditions.items():
                safe_column = InputValidator.sanitize_sql_identifier(column)
                where_parts.append(f"{safe_column} = ?")
                params.append(value)
            query += f" WHERE {' AND '.join(where_parts)}"

        if limit:
            query += " LIMIT ?"
            params.append(int(limit))

        # Audit the query
        is_safe, findings = self.auditor.validate_query_safety(
            query, params, "build_safe_select"
        )
        if not is_safe:
            raise SecurityError(f"Generated query failed security audit: {findings}")

        return query, params

    def build_safe_insert(
        self, table: str, data: dict[str, Any]
    ) -> tuple[str, list[Any]]:
        """Build a safe INSERT query"""
        # Validate inputs
        table = InputValidator.sanitize_sql_identifier(table)
        validated_data = {}

        for column, value in data.items():
            safe_column = InputValidator.sanitize_sql_identifier(column)
            validated_data[safe_column] = value

        columns = list(validated_data.keys())
        values = list(validated_data.values())

        # Build query
        columns_str = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(values))
        query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

        # Audit the query
        is_safe, findings = self.auditor.validate_query_safety(
            query, values, "build_safe_insert"
        )
        if not is_safe:
            raise SecurityError(f"Generated query failed security audit: {findings}")

        return query, values


# Global security auditor instance
_global_auditor = DatabaseSecurityAuditor()


def get_security_auditor() -> DatabaseSecurityAuditor:
    """Get the global security auditor instance"""
    return _global_auditor


def audit_query(
    query: str, params: list[Any] | None = None, context: str | None = None
) -> list[SecurityFinding]:
    """Convenience function to audit a single query"""
    return _global_auditor.audit_query(query, params, context)


def validate_query_safety(
    query: str, params: list[Any] | None = None, context: str | None = None
) -> bool:
    """Convenience function to validate query safety"""
    is_safe, _ = _global_auditor.validate_query_safety(query, params, context)
    return is_safe
