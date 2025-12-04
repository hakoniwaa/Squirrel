"""
Security detection modules - refactored with improved architecture
"""

from .authentication import AuthenticationVulnerabilityDetector

# Import base classes and utilities
from .base import SecurityAnalysisUtils, SecurityContext, SecurityIssue, VulnerabilityPattern
from .coordinator import SecurityIssueDetector
from .cryptographic import CryptographicVulnerabilityDetector

# Import specialized detectors
from .injection import InjectionVulnerabilityDetector
from .input_validation import InputValidationVulnerabilityDetector
from .insecure_functions import InsecureFunctionDetector
from .network import NetworkSecurityDetector
from .secrets import SecretDetector

__all__ = [
    # Base classes and utilities
    "SecurityIssue",
    "VulnerabilityPattern",
    "SecurityContext",
    "SecurityAnalysisUtils",
    # Specialized detectors
    "InjectionVulnerabilityDetector",
    "CryptographicVulnerabilityDetector",
    "AuthenticationVulnerabilityDetector",
    "InputValidationVulnerabilityDetector",
    "InsecureFunctionDetector",
    "SecretDetector",
    "NetworkSecurityDetector",
    # Main coordinator
    "SecurityIssueDetector",
]
