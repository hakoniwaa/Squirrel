"""
Code smell detection coordinator - orchestrates specialized detectors using composition
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..base import DetectionContext, DetectionStrategy
from ..constants import SeverityLevels
from .complexity import ComplexitySmellDetector
from .quality import QualitySmellDetector
from .structural import StructuralSmellDetector

logger = logging.getLogger(__name__)


class CodeSmellDetector:
    """
    Main coordinator for code smell detection using composition and strategy pattern.

    This class delegates to specialized detectors instead of doing everything itself,
    following the Single Responsibility Principle and Composition over Inheritance.
    """

    def __init__(self, enabled_detectors: Optional[List[str]] = None):
        """
        Initialize code smell detector with configurable strategies.

        Args:
            enabled_detectors: List of detector names to enable. If None, all are enabled.
        """
        self.available_detectors = {
            "structural": StructuralSmellDetector(),
            "quality": QualitySmellDetector(),
            "complexity": ComplexitySmellDetector(),
        }

        self.enabled_detectors = self._validate_enabled_detectors(enabled_detectors)
        self.statistics = SmellStatisticsCalculator()

    def detect_code_smells(
        self, content: str, file_path: Path, enabled_smells: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect code smells using enabled detector strategies.

        Args:
            content: File content to analyze
            file_path: Path to the file being analyzed
            enabled_smells: Specific smell types to detect (optional filter)

        Returns:
            List of detected code smell dictionaries
        """
        if not self._is_valid_content(content):
            return []

        _ = DetectionContext(content=content, lines=content.splitlines(), file_path=file_path)

        all_smells = []

        # Use enabled detectors to find smells
        for detector_name in self.enabled_detectors:
            try:
                detector = self.available_detectors[detector_name]
                smells = detector.detect(content, file_path)

                # Filter by specific smell types if requested
                if enabled_smells:
                    smells = self._filter_smells_by_type(smells, enabled_smells)

                all_smells.extend(smells)

            except Exception as e:  # noqa: BLE001
                logger.warning("Error in %s detector: %s", detector_name, e)
                continue

        # Post-process and deduplicate results
        return self._post_process_smells(all_smells)

    def get_smell_statistics(self, smells: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive statistics about detected code smells"""
        return self.statistics.calculate_statistics(smells)

    def get_available_smell_types(self) -> Dict[str, List[str]]:
        """Get all available smell types organized by detector"""
        smell_types = {}

        for detector_name, detector in self.available_detectors.items():
            if hasattr(detector, "rules"):
                smell_types[detector_name] = list(detector.rules.keys())
            else:
                # Fallback for detectors without rules attribute
                smell_types[detector_name] = []

        return smell_types

    def configure_detector(self, detector_name: str, enabled: bool) -> None:
        """Enable or disable a specific detector"""
        if detector_name in self.available_detectors:
            if enabled and detector_name not in self.enabled_detectors:
                self.enabled_detectors.add(detector_name)
            elif not enabled and detector_name in self.enabled_detectors:
                self.enabled_detectors.discard(detector_name)

    def add_custom_detector(self, name: str, detector: DetectionStrategy) -> None:
        """Add a custom detector strategy"""
        if hasattr(detector, "detect"):
            self.available_detectors[name] = detector  # type: ignore[assignment]
            self.enabled_detectors.add(name)
        else:
            raise ValueError(f"Detector {name} does not implement required 'detect' method")

    def _validate_enabled_detectors(self, enabled_detectors: Optional[List[str]]) -> Set[str]:
        """Validate and return set of enabled detectors"""
        if enabled_detectors is None:
            return set(self.available_detectors.keys())

        valid_detectors = set()
        for detector in enabled_detectors:
            if detector in self.available_detectors:
                valid_detectors.add(detector)
            else:
                logger.warning(f"Unknown detector '{detector}' ignored")

        return valid_detectors if valid_detectors else set(self.available_detectors.keys())

    def _is_valid_content(self, content: str) -> bool:
        """Check if content is valid for analysis"""
        return bool(content and content.strip())

    def _filter_smells_by_type(
        self, smells: List[Dict[str, Any]], enabled_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Filter smells by specific types"""
        return [smell for smell in smells if smell.get("type") in enabled_types]

    def _post_process_smells(self, smells: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Post-process smells: deduplicate, sort, and validate"""
        # Remove duplicates based on file, line, and type
        seen = set()
        unique_smells = []

        for smell in smells:
            smell_key = (smell.get("file"), smell.get("line"), smell.get("type"))
            if smell_key not in seen:
                seen.add(smell_key)
                unique_smells.append(smell)

        # Sort by severity (high to low) then by file and line
        severity_order = {
            SeverityLevels.CRITICAL: 0,
            SeverityLevels.HIGH: 1,
            SeverityLevels.MEDIUM: 2,
            SeverityLevels.LOW: 3,
            SeverityLevels.INFO: 4,
        }

        unique_smells.sort(
            key=lambda x: (
                severity_order.get(x.get("severity", SeverityLevels.LOW), 3),
                x.get("file", ""),
                x.get("line", 0),
            )
        )

        return unique_smells


class SmellStatisticsCalculator:
    """Calculates comprehensive statistics for code smell detection results"""

    def calculate_statistics(self, smells: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive statistics about detected code smells"""
        if not smells:
            return self._get_empty_statistics()

        basic_stats = self._calculate_basic_statistics(smells)
        severity_stats = self._calculate_severity_statistics(smells)
        type_stats = self._calculate_type_statistics(smells)
        file_stats = self._calculate_file_statistics(smells)

        return {**basic_stats, **severity_stats, **type_stats, **file_stats}

    def _get_empty_statistics(self) -> Dict[str, Any]:
        """Return empty statistics when no smells found"""
        return {
            "total_smells": 0,
            "by_severity": {},
            "by_type": {},
            "files_affected": 0,
            "average_smells_per_file": 0.0,
            "most_common_smell": None,
            "severity_distribution": {},
            "quality_score": 10.0,  # Perfect score when no smells
        }

    def _calculate_basic_statistics(self, smells: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate basic smell statistics"""
        affected_files = set(smell.get("file", "unknown") for smell in smells)

        return {
            "total_smells": len(smells),
            "files_affected": len(affected_files),
            "average_smells_per_file": len(smells) / len(affected_files) if affected_files else 0.0,
        }

    def _calculate_severity_statistics(self, smells: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate severity-based statistics"""
        severity_counts: Dict[str, int] = {}

        for smell in smells:
            severity = smell.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Calculate quality score based on severity distribution
        quality_score = self._calculate_quality_score(severity_counts, len(smells))

        return {
            "by_severity": severity_counts,
            "severity_distribution": self._calculate_severity_percentages(
                severity_counts, len(smells)
            ),
            "quality_score": quality_score,
        }

    def _calculate_type_statistics(self, smells: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate type-based statistics"""
        type_counts: Dict[str, int] = {}

        for smell in smells:
            smell_type = smell.get("type", "unknown")
            type_counts[smell_type] = type_counts.get(smell_type, 0) + 1

        most_common = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None

        return {"by_type": type_counts, "most_common_smell": most_common}

    def _calculate_file_statistics(self, smells: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate file-based statistics"""
        file_counts: Dict[str, int] = {}

        for smell in smells:
            file_name = smell.get("file", "unknown")
            file_counts[file_name] = file_counts.get(file_name, 0) + 1

        most_problematic_file = (
            max(file_counts.items(), key=lambda x: x[1])[0] if file_counts else None
        )

        return {"smells_per_file": file_counts, "most_problematic_file": most_problematic_file}

    def _calculate_severity_percentages(
        self, severity_counts: Dict[str, int], total_smells: int
    ) -> Dict[str, float]:
        """Calculate percentage distribution of severities"""
        if total_smells == 0:
            return {}

        return {
            severity: (count / total_smells) * 100 for severity, count in severity_counts.items()
        }

    def _calculate_quality_score(self, severity_counts: Dict[str, int], total_smells: int) -> float:
        """
        Calculate quality score (0-10) based on smell severity distribution.
        Higher scores indicate better code quality.
        """
        if total_smells == 0:
            return 10.0

        # Weight severities (lower weights for more severe issues)
        severity_weights = {
            SeverityLevels.CRITICAL: 0.1,
            SeverityLevels.HIGH: 0.3,
            SeverityLevels.MEDIUM: 0.6,
            SeverityLevels.LOW: 0.8,
            SeverityLevels.INFO: 0.9,
        }

        weighted_score = 0.0
        for severity, count in severity_counts.items():
            weight = severity_weights.get(severity, 0.5)
            weighted_score += (count / total_smells) * weight

        # Scale to 0-10, with penalty for high smell density
        base_score = weighted_score * 10
        density_penalty = min(total_smells * 0.1, 3.0)  # Max 3 point penalty

        return max(0.0, base_score - density_penalty)
