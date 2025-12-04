"""
Architectural pattern detection - identifies architectural design patterns
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import BasePatternDetector, DetectionContext, DetectionUtils, PatternConfig
from ..constants import PatternDetectionConfig
from . import utils

logger = logging.getLogger(__name__)


class ArchitecturalPatternDetector(BasePatternDetector):
    """Detect architectural patterns in code"""

    def __init__(self, config: Optional[PatternDetectionConfig] = None):
        """Initialize architectural pattern detector"""
        super().__init__()
        self.config = config or PatternDetectionConfig()

    def _load_patterns(self) -> Dict[str, Any]:
        """Load architectural pattern detection configurations"""
        return {
            "mvc": self._create_mvc_pattern(),
            "repository": self._create_repository_pattern(),
            "service_layer": self._create_service_layer_pattern(),
            "layered_architecture": self._create_layered_architecture_pattern(),
            "microservices": self._create_microservices_pattern(),
            "event_driven": self._create_event_driven_pattern(),
            "dependency_injection": self._create_dependency_injection_pattern(),
            "hexagonal": self._create_hexagonal_pattern(),
        }

    def _create_mvc_pattern(self) -> Dict[str, Any]:
        """Create MVC pattern configuration"""
        return {
            "indicators": [
                r"class\s+\w*Controller\w*",
                r"class\s+\w*View\w*",
                r"class\s+\w*Model\w*",
                r"def\s+render\(",
                r"def\s+update\(",
                r"def\s+handle_\w+\(",
            ],
            "description": "MVC architectural pattern detected",
            "suggestion": "Good separation of concerns with MVC pattern",
            "min_matches": 2,
        }

    def _create_repository_pattern(self) -> Dict[str, Any]:
        """Create repository pattern configuration"""
        return {
            "indicators": [
                r"class\s+\w*Repository\w*",
                r"def\s+find_by_\w+\(",
                r"def\s+save\(",
                r"def\s+delete\(",
                r"def\s+find_all\(",
                r"def\s+create\(",
            ],
            "description": "Repository pattern detected",
            "suggestion": "Good use of repository pattern for data access abstraction",
            "min_matches": 3,
        }

    def _create_service_layer_pattern(self) -> Dict[str, Any]:
        """Create service layer pattern configuration"""
        return {
            "indicators": [
                r"class\s+\w*Service\w*",
                r"def\s+process\(",
                r"def\s+handle\(",
                r"@service",
                r"def\s+execute\(",
                r"business_logic",
            ],
            "description": "Service layer pattern detected",
            "suggestion": "Good use of service layer for business logic separation",
            "min_matches": 2,
        }

    def _create_layered_architecture_pattern(self) -> Dict[str, Any]:
        """Create layered architecture pattern configuration"""
        return {
            "indicators": [
                r"presentation_layer",
                r"business_layer",
                r"data_layer",
                r"domain_layer",
                r"infrastructure_layer",
                r"application_layer",
            ],
            "description": "Layered architecture pattern detected",
            "suggestion": "Good separation of concerns with layered architecture",
            "min_matches": 2,
        }

    def _create_microservices_pattern(self) -> Dict[str, Any]:
        """Create microservices pattern configuration"""
        return {
            "indicators": [
                r"@app\.route\(",
                r"FastAPI\(",
                r"Flask\(",
                r"api_gateway",
                r"service_discovery",
                r"circuit_breaker",
            ],
            "description": "Microservices architecture pattern detected",
            "suggestion": "Consider service boundaries and communication patterns",
            "min_matches": 2,
        }

    def _create_event_driven_pattern(self) -> Dict[str, Any]:
        """Create event-driven pattern configuration"""
        return {
            "indicators": [
                r"def\s+emit_event\(",
                r"def\s+handle_event\(",
                r"event_bus",
                r"event_store",
                r"publish\(",
                r"subscribe\(",
            ],
            "description": "Event-driven architecture pattern detected",
            "suggestion": "Good use of event-driven architecture for loose coupling",
            "min_matches": 2,
        }

    def _create_dependency_injection_pattern(self) -> Dict[str, Any]:
        """Create dependency injection pattern configuration"""
        return {
            "indicators": [
                r"@inject",
                r"@dependency",
                r"container\.get\(",
                r"injector\.",
                r"def\s+__init__.*:.*=.*inject",
                r"DI_CONTAINER",
            ],
            "description": "Dependency injection pattern detected",
            "suggestion": "Good use of dependency injection for loose coupling",
            "min_matches": 2,
        }

    def _create_hexagonal_pattern(self) -> Dict[str, Any]:
        """Create hexagonal architecture pattern configuration"""
        return {
            "indicators": [
                r"class\s+\w*Port\w*",
                r"class\s+\w*Adapter\w*",
                r"primary_port",
                r"secondary_port",
                r"driven_adapter",
                r"driving_adapter",
            ],
            "description": "Hexagonal architecture pattern detected",
            "suggestion": "Good use of ports and adapters for testability",
            "min_matches": 2,
        }

    def detect_patterns(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Dict[str, Any]]:
        """Detect architectural patterns in code"""
        patterns: List[Dict[str, Any]] = []

        for pattern_name, pattern_config in self._patterns.items():
            context = DetectionContext(content=content, lines=lines, file_path=file_path)
            # Only process if pattern_config is a PatternConfig
            if isinstance(pattern_config, PatternConfig):
                matches = self._find_pattern_matches(context, pattern_name, pattern_config)
                patterns.extend(matches)

        return patterns

    def _find_pattern_matches(
        self, context: DetectionContext, pattern_name: str, pattern_config: PatternConfig
    ) -> List[Dict[str, Any]]:
        """Find matches for architectural patterns"""
        matches: List[Dict[str, Any]] = []
        for indicator in pattern_config.indicators:
            try:
                pattern_matches = self._search_pattern(context.content, indicator)
                for match in pattern_matches:
                    confidence = self._calculate_confidence(match, pattern_config)
                    if confidence >= pattern_config.confidence_threshold:
                        issue = utils.create_pattern_issue_from_match(
                            context,
                            pattern_name,
                            "architectural_pattern",
                            pattern_config,
                            match,
                            confidence,
                            DetectionUtils.get_line_number_from_match,
                            utils.get_code_snippet,
                        )
                        matches.append(issue)
            except re.error as e:
                self.logger.warning(f"Invalid regex pattern '{indicator}': {e}")
                continue
            except Exception as e:
                self.logger.warning(f"Error searching pattern '{indicator}': {e}")
                continue
        return matches

    def _collect_indicator_matches(self, content: str, indicators: List[str]) -> Dict[str, Any]:
        """Collect matches for all indicators"""
        indicator_matches = 0
        matched_lines = []

        for indicator in indicators:
            pattern_matches = list(re.finditer(indicator, content, re.MULTILINE))
            indicator_matches += len(pattern_matches)

            for match in pattern_matches:
                line_num = content[: match.start()].count("\n") + 1
                matched_lines.append(line_num)

        return {"indicator_matches": indicator_matches, "matched_lines": matched_lines}

    def _calculate_confidence(self, match: re.Match[Any], pattern_config: PatternConfig) -> float:
        """Calculate confidence score for pattern match"""
        # Custom confidence logic for architectural patterns: always medium
        return self._confidence_thresholds["medium"]

    def _create_pattern_result(
        self,
        context: DetectionContext,
        pattern_name: str,
        pattern_type: str,
        match_data: Dict[str, Any],
        pattern_config: PatternConfig,
        confidence: float,
    ) -> Dict[str, Any]:
        """Create pattern result from context and match data"""
        matched_lines = match_data["matched_lines"]
        start_line = min(matched_lines) if matched_lines else 1
        end_line = max(matched_lines) if matched_lines else len(context.lines or [])

        try:
            relative_path = str(context.file_path.relative_to(Path.cwd()))
        except ValueError:
            relative_path = str(context.file_path)

        return {
            "pattern_name": pattern_name,
            "pattern_type": pattern_type,
            "file": relative_path,
            "start_line": start_line,
            "end_line": end_line,
            "confidence": confidence,
            "description": pattern_config.description,
            "suggestion": pattern_config.suggestion,
            "severity": getattr(pattern_config, "severity", "info"),
            "matches_found": match_data["indicator_matches"],
        }

    def _create_issue_from_match(
        self,
        context: DetectionContext,
        pattern_name: str,
        pattern_config: PatternConfig,
        match: re.Match[Any],
        confidence: float,
    ) -> Dict[str, Any]:
        """Create issue dictionary from pattern match.

        Args:
            context: Detection context
            pattern_name: Name of the matched pattern
            pattern_config: Pattern configuration (PatternConfig)
            match: Regex match object
            confidence: Confidence score

        Returns:
            Issue dictionary compatible with the analysis system
        """
        description = pattern_config.description
        suggestion = pattern_config.suggestion
        severity = getattr(pattern_config, "severity", "info")
        # Calculate line number from match
        line_number = DetectionUtils.get_line_number_from_match(context.content, match)
        # Get code snippet around the match
        code_snippet = utils.get_code_snippet(
            context.lines if context.lines is not None else [], line_number, 2
        )
        return {
            "type": "architectural_pattern",
            "pattern_name": pattern_name,
            "severity": severity,
            "file": context.relative_path,
            "line": line_number,
            "description": description,
            "suggestion": suggestion,
            "confidence": confidence,
            "code_snippet": code_snippet,
            "match_text": match.group(0) if match.group(0) else "",
        }

    def _detect_mvc_pattern(
        self, tree: ast.AST, lines: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Detect MVC (Model-View-Controller) pattern"""
        patterns: List[Dict[str, Any]] = []

        # Handle None lines parameter
        if lines is None:
            return patterns

        # Check for MVC indicators
        has_model = False
        has_view = False
        has_controller = False

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name.lower()
                if "model" in class_name:
                    has_model = True
                elif "view" in class_name:
                    has_view = True
                elif "controller" in class_name:
                    has_controller = True

        if sum([has_model, has_view, has_controller]) >= 2:
            # Get code snippet safely
            snippet = utils.get_code_snippet(lines if lines is not None else [], 1, 5)

            patterns.append(
                {
                    "type": "mvc_pattern",
                    "confidence": 0.8,
                    "line": 1,
                    "details": {
                        "has_model": has_model,
                        "has_view": has_view,
                        "has_controller": has_controller,
                        "snippet": snippet,
                    },
                }
            )

        return patterns

    def _get_code_snippet(
        self, lines: Optional[List[str]], line_number: int, context_lines: int = 2
    ) -> str:
        # Method removed; use utils.get_code_snippet instead
        return ""
