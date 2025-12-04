"""
Design pattern detection - identifies beneficial design patterns in code
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import BasePatternDetector, DetectionContext, PatternConfig
from ..constants import ConfidenceLevels, PatternDetectionConfig

logger = logging.getLogger(__name__)


class DesignPatternDetector(BasePatternDetector):
    """Detect beneficial design patterns in code"""

    def __init__(self, config: Optional[PatternDetectionConfig] = None):
        """Initialize design pattern detector"""
        super().__init__()
        self.config = config or PatternDetectionConfig()

    def _load_patterns(self) -> Dict[str, Any]:
        """Load design pattern detection configurations"""
        from ..base import PatternConfig

        patterns = {}
        for name, pattern_dict in {
            "singleton": self._create_singleton_pattern(),
            "factory": self._create_factory_pattern(),
            "observer": self._create_observer_pattern(),
            "decorator": self._create_decorator_pattern(),
            "strategy": self._create_strategy_pattern(),
            "builder": self._create_builder_pattern(),
            "adapter": self._create_adapter_pattern(),
            "command": self._create_command_pattern(),
            "template_method": self._create_template_method_pattern(),
            "facade": self._create_facade_pattern(),
        }.items():
            # Convert dict to PatternConfig object
            patterns[name] = PatternConfig(
                indicators=pattern_dict["indicators"],
                description=pattern_dict["description"],
                suggestion=pattern_dict["suggestion"],
                severity=pattern_dict.get("severity", "low"),
                confidence_threshold=pattern_dict.get("confidence_threshold", 0.3),
            )
            # Preserve additional attributes
            for key, value in pattern_dict.items():
                if key not in [
                    "indicators",
                    "description",
                    "suggestion",
                    "severity",
                    "confidence_threshold",
                ]:
                    setattr(patterns[name], key, value)

        return patterns

    def _create_singleton_pattern(self) -> Dict[str, Any]:
        """Create singleton pattern configuration"""
        return {
            "indicators": [
                r"class\s+\w+.*:.*__instance\s*=\s*None",
                r"def\s+__new__\s*\(\s*cls",
                r"if\s+cls\.__instance\s+is\s+None",
                r'if\s+not\s+hasattr\s*\(\s*cls\s*,\s*["\']_instance["\']',
                r"_instance\s*=\s*None",
            ],
            "description": "Singleton pattern implementation detected",
            "suggestion": "Consider using dependency injection instead of singleton for better "
            "testability",
            "confidence_weight": 1.2,
            "min_matches": 2,
        }

    def _create_factory_pattern(self) -> Dict[str, Any]:
        """Create factory pattern configuration"""
        return {
            "indicators": [
                r"def\s+create_\w+\(",
                r"def\s+make_\w+\(",
                r"class\s+\w*Factory\w*",
                r"def\s+build_\w+\(",
                r"return\s+\w+\(",
                r"factory_method",
            ],
            "description": "Factory pattern implementation detected",
            "suggestion": "Good use of factory pattern for object creation flexibility",
            "confidence_weight": 1.0,
            "min_matches": 2,
        }

    def _create_observer_pattern(self) -> Dict[str, Any]:
        """Create observer pattern configuration"""
        return {
            "indicators": [
                r"def\s+add_observer\(",
                r"def\s+notify_observers\(",
                r"def\s+remove_observer\(",
                r"observers\s*=\s*\[\]",
                r"def\s+subscribe\(",
                r"def\s+unsubscribe\(",
                r"def\s+update\(",
            ],
            "description": "Observer pattern implementation detected",
            "suggestion": "Consider using event-driven architecture for better decoupling",
            "confidence_weight": 1.1,
            "min_matches": 2,
        }

    def _create_decorator_pattern(self) -> Dict[str, Any]:
        """Create decorator pattern configuration"""
        return {
            "indicators": [
                r"@\w+",
                r"def\s+\w+\(.*func.*\):",
                r"def\s+wrapper\(",
                r"return\s+wrapper",
                r"functools\.wraps",
                r"def\s+decorator\(",
            ],
            "description": "Decorator pattern implementation detected",
            "suggestion": "Good use of decorator pattern for cross-cutting concerns",
            "confidence_weight": 1.0,
            "min_matches": 2,
        }

    def _create_strategy_pattern(self) -> Dict[str, Any]:
        """Create strategy pattern configuration"""
        return {
            "indicators": [
                r"class\s+\w*Strategy\w*",
                r"def\s+execute\(",
                r"def\s+algorithm\(",
                r"strategy\s*=\s*\w+",
                r"def\s+set_strategy\(",
                r"class\s+.*Algorithm.*",
            ],
            "description": "Strategy pattern implementation detected",
            "suggestion": "Good use of strategy pattern for algorithm selection",
            "confidence_weight": 1.0,
            "min_matches": 2,
        }

    def _create_builder_pattern(self) -> Dict[str, Any]:
        """Create builder pattern configuration"""
        return {
            "indicators": [
                r"class\s+\w*Builder\w*",
                r"def\s+build\(",
                r"def\s+with_\w+\(",
                r"def\s+set_\w+\(",
                r"return\s+self",
                r"\.build\(\)",
            ],
            "description": "Builder pattern implementation detected",
            "suggestion": "Good use of builder pattern for complex object construction",
            "confidence_weight": 1.0,
            "min_matches": 3,
        }

    def _create_adapter_pattern(self) -> Dict[str, Any]:
        """Create adapter pattern configuration"""
        return {
            "indicators": [
                r"class\s+\w*Adapter\w*",
                r"def\s+adapt\(",
                r"adaptee\s*=",
                r"def\s+__init__.*adaptee",
                r"self\.adaptee",
            ],
            "description": "Adapter pattern implementation detected",
            "suggestion": "Good use of adapter pattern for interface compatibility",
            "confidence_weight": 1.0,
            "min_matches": 2,
        }

    def _create_command_pattern(self) -> Dict[str, Any]:
        """Create command pattern configuration"""
        return {
            "indicators": [
                r"class\s+\w*Command\w*",
                r"def\s+execute\(",
                r"def\s+undo\(",
                r"def\s+redo\(",
                r"command_queue",
                r"invoke\(",
            ],
            "description": "Command pattern implementation detected",
            "suggestion": "Good use of command pattern for operation encapsulation",
            "confidence_weight": 1.0,
            "min_matches": 2,
        }

    def _create_template_method_pattern(self) -> Dict[str, Any]:
        """Create template method pattern configuration"""
        return {
            "indicators": [
                r"def\s+template_method\(",
                r"def\s+hook\w*\(",
                r"def\s+primitive\w*\(",
                r"raise\s+NotImplementedError",
                r"@abstractmethod",
                r"self\.\w+_hook\(",
            ],
            "description": "Template Method pattern implementation detected",
            "suggestion": "Good use of template method pattern for algorithm structure",
            "confidence_weight": 1.0,
            "min_matches": 2,
        }

    def _create_facade_pattern(self) -> Dict[str, Any]:
        """Create facade pattern configuration"""
        return {
            "indicators": [
                r"class\s+\w*Facade\w*",
                r"def\s+simplified_\w+\(",
                r"def\s+easy_\w+\(",
                r"subsystem\w*\s*=",
                r"self\.subsystem",
            ],
            "description": "Facade pattern implementation detected",
            "suggestion": "Good use of facade pattern for simplified interface",
            "confidence_weight": 1.0,
            "min_matches": 2,
        }

    def detect_patterns(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Dict[str, Any]]:
        """Detect design patterns in code"""
        patterns = []

        for pattern_name, pattern_config in self._patterns.items():
            context = DetectionContext(content=content, lines=lines, file_path=file_path)

            matches = self._find_pattern_matches(context, pattern_name, pattern_config)
            patterns.extend(matches)

        return patterns

    def _find_pattern_matches(
        self,
        context: DetectionContext,
        pattern_name: str,
        pattern_config: PatternConfig,
    ) -> List[Dict[str, Any]]:
        """Find matches for a specific design pattern"""
        matches = []
        indicators = pattern_config.indicators
        min_matches = getattr(pattern_config, "min_matches", 1)

        match_data = self._collect_indicator_matches(context.content, indicators)

        if match_data["indicator_matches"] >= min_matches:
            confidence = self._calculate_confidence(match_data, pattern_config)

            if confidence >= ConfidenceLevels.LOW:
                pattern_dict = self._create_pattern_result(
                    context, pattern_name, "design_pattern", match_data, pattern_config, confidence
                )
                matches.append(pattern_dict)

        return matches

    def _collect_indicator_matches(self, content: str, indicators: List[str]) -> Dict[str, Any]:
        """Collect matches for all indicators"""
        indicator_matches = 0
        matched_lines = []
        unique_matches = set()

        for indicator in indicators:
            pattern_matches = list(re.finditer(indicator, content, re.MULTILINE))

            for match in pattern_matches:
                line_num = content[: match.start()].count("\n") + 1
                match_text = match.group(0)

                # Use set to avoid counting duplicate matches
                if (line_num, match_text) not in unique_matches:
                    unique_matches.add((line_num, match_text))
                    indicator_matches += 1
                    matched_lines.append(line_num)

        return {
            "indicator_matches": indicator_matches,
            "matched_lines": matched_lines,
            "unique_matches": len(unique_matches),
        }

    def _calculate_confidence(  # type: ignore[override]
        self, match: Dict[str, Any], pattern_config: PatternConfig
    ) -> float:
        """Calculate confidence score for pattern match.

        Note: This overrides the base class signature because this implementation
        uses aggregated match data rather than individual regex matches.
        """
        base_confidence = min(match["indicator_matches"] / len(pattern_config.indicators), 1.0)

        # Apply confidence weight from pattern configuration
        confidence_weight = getattr(pattern_config, "confidence_weight", 1.0)
        adjusted_confidence = base_confidence * confidence_weight

        # Bonus for multiple unique matches
        if match["unique_matches"] > 2:
            adjusted_confidence *= 1.1

        return float(min(adjusted_confidence, 1.0))

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
            "severity": self._get_pattern_severity("design_pattern", confidence),
            "matches_found": match_data["indicator_matches"],
            "code_snippet": self._get_code_snippet(context.lines or [], start_line, end_line),
        }

    def _get_pattern_severity(self, pattern_type: str, confidence: float) -> str:
        """Determine severity based on pattern type and confidence"""
        # Design patterns are generally positive, so use 'low' severity
        # Pattern type is used for potential future severity customization
        _ = pattern_type  # Acknowledge usage to avoid linter warning
        if confidence >= ConfidenceLevels.HIGH:
            return "low"
        elif confidence >= ConfidenceLevels.MEDIUM:
            return "low"
        else:
            return "low"

    def _get_code_snippet(
        self, lines: List[str], start_line: int, end_line: int, max_lines: int = 5
    ) -> str:
        """Get a code snippet for the detected pattern"""
        snippet_lines = []
        snippet_start = max(0, start_line - 1)
        snippet_end = min(len(lines), snippet_start + max_lines)

        for i in range(snippet_start, snippet_end):
            if i < len(lines):
                snippet_lines.append(lines[i])

        if snippet_end < end_line:
            snippet_lines.append("...")

        return "\n".join(snippet_lines)

    def get_pattern_statistics(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics about detected design patterns"""
        if not patterns:
            return {
                "total_patterns": 0,
                "pattern_distribution": {},
                "average_confidence": 0.0,
                "most_common_pattern": None,
            }

        # Count pattern types
        pattern_counts: Dict[str, int] = {}
        confidences = []

        for pattern in patterns:
            pattern_name = pattern.get("pattern_name", "unknown")
            pattern_counts[pattern_name] = pattern_counts.get(pattern_name, 0) + 1

            confidence = pattern.get("confidence", 0.0)
            confidences.append(confidence)

        most_common = max(pattern_counts.items(), key=lambda x: x[1])[0] if pattern_counts else None

        return {
            "total_patterns": len(patterns),
            "pattern_distribution": pattern_counts,
            "average_confidence": sum(confidences) / len(confidences),
            "most_common_pattern": most_common,
            "high_confidence_patterns": sum(1 for c in confidences if c >= ConfidenceLevels.HIGH),
        }

    def _create_issue_from_match(
        self,
        context: DetectionContext,
        pattern_name: str,
        pattern_config: Any,
        match: re.Match,
        confidence: float,
    ) -> Dict[str, Any]:
        """Create issue dictionary from pattern match.

        Args:
            context: Detection context
            pattern_name: Name of the matched pattern
            pattern_config: Pattern configuration (dict or PatternConfig)
            match: Regex match object
            confidence: Confidence score

        Returns:
            Issue dictionary compatible with the analysis system
        """
        # Method removed; use utils.create_pattern_issue_from_match instead
        return {}

    def _detect_singleton_pattern(self, tree: ast.AST, lines: List[str]) -> List[Dict[str, Any]]:
        """Detect Singleton pattern"""
        patterns = []

        # Handle None lines parameter
        if lines is None:
            return patterns

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check for singleton indicators
                has_instance_method = False
                has_private_init = False

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name == "__new__" or item.name.lower() in [
                            "instance",
                            "get_instance",
                        ]:
                            has_instance_method = True
                        elif item.name == "__init__" and len([d for d in item.decorator_list]) > 0:
                            has_private_init = True

                if has_instance_method:
                    snippet = self._get_code_snippet(lines, node.lineno, 3) if lines else "N/A"

                    patterns.append(
                        {
                            "type": "singleton_pattern",
                            "confidence": 0.7 if has_private_init else 0.5,
                            "line": node.lineno,
                            "details": {
                                "class_name": node.name,
                                "has_instance_method": has_instance_method,
                                "has_private_init": has_private_init,
                                "snippet": snippet,
                            },
                        }
                    )

        return patterns
