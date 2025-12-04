"""
Pattern detection coordinator - orchestrates specialized pattern detectors
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..constants import ConfidenceLevels, PatternDetectionConfig, SeverityLevels
from .anti_patterns import AntiPatternDetector
from .architectural_patterns import ArchitecturalPatternDetector
from .design_patterns import DesignPatternDetector
from .structural_patterns import StructuralPatternDetector

logger = logging.getLogger(__name__)


class PatternDetector:
    """Main coordinator for pattern detection using composition"""

    def __init__(self, config: Optional[PatternDetectionConfig] = None):
        """Initialize coordinator with specialized detectors"""
        self.config = config or PatternDetectionConfig()

        # Initialize specialized pattern detectors
        self.design_detector = DesignPatternDetector(self.config)
        self.anti_pattern_detector = AntiPatternDetector(self.config)
        self.architectural_detector = ArchitecturalPatternDetector(self.config)
        self.structural_detector = StructuralPatternDetector(self.config)

    @property
    def design_patterns(self):
        """Access design patterns from the design detector"""
        return getattr(self.design_detector, "_patterns", {})

    @property
    def anti_patterns(self):
        """Access anti-patterns from the anti-pattern detector"""
        return getattr(self.anti_pattern_detector, "_patterns", {})

    @property
    def architectural_patterns(self):
        """Access architectural patterns from the architectural detector"""
        return getattr(self.architectural_detector, "_patterns", {})

    @property
    def structural_patterns(self):
        """Access structural patterns from the structural detector"""
        return getattr(self.structural_detector, "_patterns", {})

    def detect_patterns(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Detect code patterns using specialized detectors"""
        if not content or not content.strip():
            return []

        patterns = []
        lines = content.splitlines()

        # Delegate to specialized detectors
        try:
            patterns.extend(self.design_detector.detect_patterns(content, lines, file_path))
        except Exception as e:
            logger.error(f"Error in design pattern detection: {e}")

        try:
            patterns.extend(self.anti_pattern_detector.detect_patterns(content, lines, file_path))
        except Exception as e:
            logger.error(f"Error in anti-pattern detection: {e}")

        try:
            patterns.extend(self.architectural_detector.detect_patterns(content, lines, file_path))
        except Exception as e:
            logger.error(f"Error in architectural pattern detection: {e}")

        try:
            patterns.extend(self.structural_detector.detect_patterns(content, lines, file_path))
        except Exception as e:
            logger.error(f"Error in structural pattern detection: {e}")

        return self._post_process_patterns(patterns)

    def _post_process_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Post-process detected patterns"""
        if not patterns:
            return patterns

        # Remove duplicates
        deduplicated = self._deduplicate_patterns(patterns)

        # Sort by severity and confidence
        sorted_patterns = self._sort_patterns(deduplicated)

        return sorted_patterns

    def _deduplicate_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate patterns"""
        seen = set()
        deduplicated = []

        for pattern in patterns:
            key = (
                pattern.get("file", ""),
                pattern.get("pattern_name", ""),
                pattern.get("start_line", 0),
            )

            if key not in seen:
                seen.add(key)
                deduplicated.append(pattern)

        return deduplicated

    def _sort_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort patterns by severity and confidence"""
        severity_order = {
            SeverityLevels.HIGH: 3,
            SeverityLevels.MEDIUM: 2,
            SeverityLevels.LOW: 1,
            "info": 0,
        }

        return sorted(
            patterns,
            key=lambda x: (
                severity_order.get(x.get("severity", "info"), 0),
                x.get("confidence", 0.0),
            ),
            reverse=True,
        )

    def get_pattern_statistics(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics about detected patterns"""
        if not patterns:
            return {
                "total_patterns": 0,
                "by_type": {},
                "by_confidence": {},
                "by_severity": {},
                "files_affected": 0,
                "average_confidence": 0.0,
            }

        type_counts: Dict[str, int] = {}
        confidence_counts: Dict[str, int] = {}
        severity_counts: Dict[str, int] = {}
        affected_files = set()

        for pattern in patterns:
            # Count by type
            pattern_type = pattern.get("pattern_type", "unknown")
            type_counts[pattern_type] = type_counts.get(pattern_type, 0) + 1

            # Count by confidence
            confidence = pattern.get("confidence", 0.0)
            if confidence >= ConfidenceLevels.HIGH:
                conf_level = "high"
            elif confidence >= ConfidenceLevels.MEDIUM:
                conf_level = "medium"
            else:
                conf_level = "low"
            confidence_counts[conf_level] = confidence_counts.get(conf_level, 0) + 1

            # Count by severity
            severity = pattern.get("severity", "info")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # Track affected files
            affected_files.add(pattern.get("file", "unknown"))

        return {
            "total_patterns": len(patterns),
            "by_type": type_counts,
            "by_confidence": confidence_counts,
            "by_severity": severity_counts,
            "files_affected": len(affected_files),
            "average_confidence": sum(p.get("confidence", 0.0) for p in patterns) / len(patterns),
        }
