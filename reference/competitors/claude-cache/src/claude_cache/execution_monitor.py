"""Monitor code execution signals to detect success patterns automatically"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ExecutionSignal:
    """Represents a signal from code execution"""
    signal_type: str  # 'test_pass', 'build_success', 'server_start', 'no_error'
    confidence: float  # 0.0 to 1.0
    context: Dict
    timestamp: datetime
    details: str


class ExecutionMonitor:
    """Detects success patterns from code execution output"""

    def __init__(self):
        # Test execution patterns
        self.test_patterns = {
            'pytest': {
                'pass': [
                    r'(\d+) passed',
                    r'PASSED',
                    r'All tests passed',
                    r'===.*passed.*===',
                    r'test session.*no failures'
                ],
                'fail': [
                    r'(\d+) failed',
                    r'FAILED',
                    r'AssertionError',
                    r'test.*failed'
                ]
            },
            'jest': {
                'pass': [
                    r'PASS',
                    r'✓.*passed',
                    r'Tests:.*\d+ passed',
                    r'All tests passed'
                ],
                'fail': [
                    r'FAIL',
                    r'✕.*failed',
                    r'Tests:.*\d+ failed'
                ]
            },
            'npm_test': {
                'pass': [
                    r'test.*passed',
                    r'✔.*success',
                    r'0 failing'
                ],
                'fail': [
                    r'test.*failed',
                    r'✖.*fail',
                    r'\d+ failing'
                ]
            }
        }

        # Build patterns
        self.build_patterns = {
            'success': [
                r'Build succeeded',
                r'Build complete',
                r'Successfully built',
                r'Compiled successfully',
                r'webpack.*compiled successfully',
                r'Build finished',
                r'✓.*Build',
                r'0 errors?,\s*0 warnings?'
            ],
            'failure': [
                r'Build failed',
                r'Compilation error',
                r'Build error',
                r'Failed to compile',
                r'webpack.*failed to compile'
            ]
        }

        # Server/app startup patterns
        self.server_patterns = {
            'success': [
                r'Server.*running',
                r'Server.*started',
                r'Listening on port',
                r'Ready on http',
                r'Server is ready',
                r'Development server.*running',
                r'Starting development server',
                r'webpack.*compiled',
                r'Watching for file changes'
            ],
            'failure': [
                r'Failed to start',
                r'Port.*already in use',
                r'Cannot start server',
                r'Server crashed',
                r'Error starting'
            ]
        }

        # Type checking patterns
        self.typecheck_patterns = {
            'success': [
                r'No type errors',
                r'0 errors?',
                r'Type check.*passed',
                r'Found 0 errors',
                r'tsc.*success'
            ],
            'failure': [
                r'Type error',
                r'Found \d+ errors?',
                r'TS\d+:',  # TypeScript errors
                r'type check.*failed'
            ]
        }

        # Linting patterns
        self.lint_patterns = {
            'success': [
                r'No lint errors',
                r'0 problems',
                r'✓.*All files pass',
                r'ESLint.*0 errors'
            ],
            'failure': [
                r'\d+ problems?',
                r'ESLint.*\d+ errors?',
                r'Lint errors found'
            ]
        }

        # Installation patterns
        self.install_patterns = {
            'success': [
                r'Successfully installed',
                r'added \d+ packages?',
                r'Packages.*installed',
                r'Installation complete',
                r'Dependencies installed'
            ],
            'failure': [
                r'Failed to install',
                r'npm ERR!',
                r'Installation failed',
                r'Could not resolve'
            ]
        }

    def analyze_output(self, output: str, command: str = "") -> List[ExecutionSignal]:
        """
        Analyze command output to detect execution signals

        Args:
            output: The output from a command execution
            command: The command that was run (helps with context)

        Returns:
            List of detected execution signals
        """
        signals = []
        output_lower = output.lower()

        # Detect test execution
        if 'test' in command.lower() or any(kw in output_lower for kw in ['test', 'spec', 'passed', 'failed']):
            signal = self._detect_test_signal(output)
            if signal:
                signals.append(signal)

        # Detect build execution
        if 'build' in command.lower() or 'compile' in output_lower:
            signal = self._detect_build_signal(output)
            if signal:
                signals.append(signal)

        # Detect server startup
        if any(kw in command.lower() for kw in ['start', 'serve', 'dev', 'run']) or 'server' in output_lower:
            signal = self._detect_server_signal(output)
            if signal:
                signals.append(signal)

        # Detect type checking
        if 'tsc' in command or 'typecheck' in command.lower() or 'type' in output_lower:
            signal = self._detect_typecheck_signal(output)
            if signal:
                signals.append(signal)

        # Detect linting
        if 'lint' in command.lower() or 'eslint' in output_lower:
            signal = self._detect_lint_signal(output)
            if signal:
                signals.append(signal)

        # Detect installation
        if 'install' in command.lower() or 'npm i' in command:
            signal = self._detect_install_signal(output)
            if signal:
                signals.append(signal)

        # Generic error detection (fallback)
        if not signals:
            signal = self._detect_generic_signal(output)
            if signal:
                signals.append(signal)

        return signals

    def _detect_test_signal(self, output: str) -> Optional[ExecutionSignal]:
        """Detect test execution signals"""
        for framework, patterns in self.test_patterns.items():
            # Check for pass patterns
            for pattern in patterns['pass']:
                if re.search(pattern, output, re.IGNORECASE):
                    # Extract test counts if possible
                    match = re.search(r'(\d+)\s+passed', output, re.IGNORECASE)
                    count = int(match.group(1)) if match else 0

                    return ExecutionSignal(
                        signal_type='test_pass',
                        confidence=0.95,
                        context={
                            'framework': framework,
                            'test_count': count
                        },
                        timestamp=datetime.now(),
                        details=f"Tests passed ({framework})"
                    )

            # Check for fail patterns
            for pattern in patterns['fail']:
                if re.search(pattern, output, re.IGNORECASE):
                    return ExecutionSignal(
                        signal_type='test_fail',
                        confidence=0.95,
                        context={'framework': framework},
                        timestamp=datetime.now(),
                        details=f"Tests failed ({framework})"
                    )

        return None

    def _detect_build_signal(self, output: str) -> Optional[ExecutionSignal]:
        """Detect build execution signals"""
        # Check success patterns
        for pattern in self.build_patterns['success']:
            if re.search(pattern, output, re.IGNORECASE):
                return ExecutionSignal(
                    signal_type='build_success',
                    confidence=0.9,
                    context={'pattern': pattern},
                    timestamp=datetime.now(),
                    details="Build succeeded"
                )

        # Check failure patterns
        for pattern in self.build_patterns['failure']:
            if re.search(pattern, output, re.IGNORECASE):
                return ExecutionSignal(
                    signal_type='build_fail',
                    confidence=0.9,
                    context={'pattern': pattern},
                    timestamp=datetime.now(),
                    details="Build failed"
                )

        return None

    def _detect_server_signal(self, output: str) -> Optional[ExecutionSignal]:
        """Detect server startup signals"""
        # Check success patterns
        for pattern in self.server_patterns['success']:
            if re.search(pattern, output, re.IGNORECASE):
                # Try to extract port
                port_match = re.search(r'port\s*[:=]?\s*(\d+)', output, re.IGNORECASE)
                port = int(port_match.group(1)) if port_match else None

                return ExecutionSignal(
                    signal_type='server_start',
                    confidence=0.85,
                    context={'port': port} if port else {},
                    timestamp=datetime.now(),
                    details="Server started successfully"
                )

        # Check failure patterns
        for pattern in self.server_patterns['failure']:
            if re.search(pattern, output, re.IGNORECASE):
                return ExecutionSignal(
                    signal_type='server_fail',
                    confidence=0.85,
                    context={},
                    timestamp=datetime.now(),
                    details="Server failed to start"
                )

        return None

    def _detect_typecheck_signal(self, output: str) -> Optional[ExecutionSignal]:
        """Detect type checking signals"""
        # Check success patterns
        for pattern in self.typecheck_patterns['success']:
            if re.search(pattern, output, re.IGNORECASE):
                return ExecutionSignal(
                    signal_type='typecheck_pass',
                    confidence=0.9,
                    context={},
                    timestamp=datetime.now(),
                    details="Type checking passed"
                )

        # Check failure patterns
        for pattern in self.typecheck_patterns['failure']:
            if re.search(pattern, output, re.IGNORECASE):
                # Try to extract error count
                error_match = re.search(r'(\d+)\s+errors?', output, re.IGNORECASE)
                error_count = int(error_match.group(1)) if error_match else 0

                return ExecutionSignal(
                    signal_type='typecheck_fail',
                    confidence=0.9,
                    context={'error_count': error_count},
                    timestamp=datetime.now(),
                    details=f"Type checking failed with {error_count} errors"
                )

        return None

    def _detect_lint_signal(self, output: str) -> Optional[ExecutionSignal]:
        """Detect linting signals"""
        # Check success patterns
        for pattern in self.lint_patterns['success']:
            if re.search(pattern, output, re.IGNORECASE):
                return ExecutionSignal(
                    signal_type='lint_pass',
                    confidence=0.85,
                    context={},
                    timestamp=datetime.now(),
                    details="Linting passed"
                )

        # Check failure patterns
        for pattern in self.lint_patterns['failure']:
            if re.search(pattern, output, re.IGNORECASE):
                return ExecutionSignal(
                    signal_type='lint_fail',
                    confidence=0.85,
                    context={},
                    timestamp=datetime.now(),
                    details="Linting failed"
                )

        return None

    def _detect_install_signal(self, output: str) -> Optional[ExecutionSignal]:
        """Detect package installation signals"""
        # Check success patterns
        for pattern in self.install_patterns['success']:
            if re.search(pattern, output, re.IGNORECASE):
                # Try to extract package count
                pkg_match = re.search(r'(\d+)\s+packages?', output, re.IGNORECASE)
                pkg_count = int(pkg_match.group(1)) if pkg_match else 0

                return ExecutionSignal(
                    signal_type='install_success',
                    confidence=0.8,
                    context={'package_count': pkg_count},
                    timestamp=datetime.now(),
                    details="Installation succeeded"
                )

        # Check failure patterns
        for pattern in self.install_patterns['failure']:
            if re.search(pattern, output, re.IGNORECASE):
                return ExecutionSignal(
                    signal_type='install_fail',
                    confidence=0.8,
                    context={},
                    timestamp=datetime.now(),
                    details="Installation failed"
                )

        return None

    def _detect_generic_signal(self, output: str) -> Optional[ExecutionSignal]:
        """Generic success/error detection as fallback"""
        output_lower = output.lower()

        # Strong error indicators
        error_keywords = ['error', 'exception', 'failed', 'failure', 'fatal', 'crash']
        error_count = sum(1 for kw in error_keywords if kw in output_lower)

        # Strong success indicators
        success_keywords = ['success', 'complete', 'done', 'ready', 'running', 'started']
        success_count = sum(1 for kw in success_keywords if kw in output_lower)

        if error_count > success_count and error_count > 0:
            return ExecutionSignal(
                signal_type='execution_error',
                confidence=min(0.5 + (error_count * 0.1), 0.8),
                context={'error_indicators': error_count},
                timestamp=datetime.now(),
                details="Execution errors detected"
            )
        elif success_count > error_count and success_count > 0:
            return ExecutionSignal(
                signal_type='execution_success',
                confidence=min(0.5 + (success_count * 0.1), 0.8),
                context={'success_indicators': success_count},
                timestamp=datetime.now(),
                details="Execution completed successfully"
            )

        # No clear signal
        return None

    def calculate_overall_success(self, signals: List[ExecutionSignal]) -> Tuple[bool, float]:
        """
        Calculate overall success from multiple signals

        Returns:
            Tuple of (is_success, confidence)
        """
        if not signals:
            return False, 0.0

        # Categorize signals
        positive_signals = [s for s in signals if 'pass' in s.signal_type or
                          'success' in s.signal_type or 'start' in s.signal_type]
        negative_signals = [s for s in signals if 'fail' in s.signal_type or
                          'error' in s.signal_type]

        # Weight by confidence
        positive_score = sum(s.confidence for s in positive_signals)
        negative_score = sum(s.confidence for s in negative_signals)

        if positive_score + negative_score == 0:
            return False, 0.0

        success_ratio = positive_score / (positive_score + negative_score)

        # Overall confidence is average of signal confidences
        avg_confidence = sum(s.confidence for s in signals) / len(signals)

        return success_ratio > 0.5, avg_confidence * success_ratio