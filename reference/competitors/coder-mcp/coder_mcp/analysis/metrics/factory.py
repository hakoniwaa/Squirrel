"""
Factory methods for creating appropriate metrics collectors

This module provides factory methods to create the right collector
based on file type and requirements.
"""

from pathlib import Path

from .collectors.base import FileConfiguration, MetricsCollector


class MetricsCollectorBuilder:
    """Builder pattern for configuring MetricsCollector instances"""

    def __init__(self):
        self._custom_quality_calculator = None
        self._custom_comment_processor = None
        self._custom_coverage_estimator = None

    def with_quality_calculator(self, calc):
        """Set a custom quality calculator"""
        self._custom_quality_calculator = calc
        return self

    def with_comment_processor(self, processor):
        """Set a custom comment processor"""
        self._custom_comment_processor = processor
        return self

    def with_coverage_estimator(self, estimator):
        """Set a custom coverage estimator"""
        self._custom_coverage_estimator = estimator
        return self

    def build(self) -> MetricsCollector:
        """Build the configured MetricsCollector"""
        collector = MetricsCollector()

        # Apply custom components if provided
        if self._custom_quality_calculator:
            collector.quality_calculator = self._custom_quality_calculator
        if self._custom_comment_processor:
            collector.comment_processor = self._custom_comment_processor
        if self._custom_coverage_estimator:
            collector.coverage_estimator = self._custom_coverage_estimator

        return collector


class MetricsCollectorFactory:
    """Factory for creating appropriate metrics collectors"""

    @staticmethod
    def create_for_file(file_path: Path) -> MetricsCollector:
        """
        Create appropriate collector based on file type

        Args:
            file_path: Path to the file to analyze

        Returns:
            MetricsCollector configured for the file type
        """
        # For now, we use the same MetricsCollector for all file types
        # but it internally handles different file types appropriately
        return MetricsCollector()

    @staticmethod
    def create_python_collector() -> MetricsCollector:
        """Create a collector optimized for Python files"""
        return MetricsCollector()

    @staticmethod
    def create_javascript_collector() -> MetricsCollector:
        """Create a collector optimized for JavaScript/TypeScript files"""
        return MetricsCollector()

    @staticmethod
    def create_generic_collector() -> MetricsCollector:
        """Create a collector for generic file types"""
        return MetricsCollector()

    @staticmethod
    def get_file_type(file_path: Path) -> str:
        """
        Determine file type based on extension

        Args:
            file_path: Path to analyze

        Returns:
            File type string ('python', 'javascript', 'generic')
        """
        suffix = file_path.suffix.lower()

        if suffix in FileConfiguration.PYTHON_EXTENSIONS:
            return "python"
        elif suffix in FileConfiguration.JS_EXTENSIONS:
            return "javascript"
        else:
            return "generic"

    @staticmethod
    def create_optimized_for_file(file_path: Path) -> MetricsCollector:
        """
        Create a collector optimized for the specific file type

        Args:
            file_path: Path to the file

        Returns:
            Optimized MetricsCollector
        """
        file_type = MetricsCollectorFactory.get_file_type(file_path)

        if file_type == "python":
            return MetricsCollectorFactory.create_python_collector()
        elif file_type == "javascript":
            return MetricsCollectorFactory.create_javascript_collector()
        else:
            return MetricsCollectorFactory.create_generic_collector()
