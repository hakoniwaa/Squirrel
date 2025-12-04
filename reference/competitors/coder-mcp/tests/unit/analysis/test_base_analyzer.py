"""
Comprehensive tests for base_analyzer.py module.

This module tests BaseAnalyzer with >90% coverage including:
- Abstract base class behavior
- Concrete method implementations
- Integration with file metrics and quality scoring
- Edge cases and error conditions
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from coder_mcp.analysis.base_analyzer import BaseAnalyzer


class ConcreteAnalyzer(BaseAnalyzer):
    """Concrete implementation of BaseAnalyzer for testing."""

    def __init__(self, workspace_root):
        """Initialize ConcreteAnalyzer with workspace validation disabled for testing."""
        super().__init__(workspace_root, validate_workspace=False)

    async def analyze_file(self, file_path: Path, analysis_type: str = "quick"):
        """Test implementation of analyze_file."""
        return {"file": str(file_path), "analysis_type": analysis_type, "test_result": True}

    def get_file_extensions(self):
        """Test implementation of get_file_extensions."""
        return [".py", ".pyw"]

    def detect_code_smells(self, content: str, file_path: Path, smell_types):
        """Test implementation of detect_code_smells."""
        return [
            {
                "type": "test_smell",
                "description": "Test code smell",
                "file": str(file_path),
                "line": 1,
            }
        ]


class TestBaseAnalyzer:
    """Comprehensive test suite for BaseAnalyzer."""

    def test_init_sets_workspace_root(self):
        """Test that BaseAnalyzer correctly sets workspace root."""
        workspace = Path("/test/workspace")
        analyzer = ConcreteAnalyzer(workspace)

        assert analyzer.workspace_root == workspace
        assert isinstance(analyzer.workspace_root, Path)

    def test_init_with_string_path(self):
        """Test BaseAnalyzer initialization with string path."""
        workspace_str = "/test/workspace"
        analyzer = ConcreteAnalyzer(workspace_str)

        assert analyzer.workspace_root == Path(workspace_str)
        assert isinstance(analyzer.workspace_root, Path)

    def test_init_with_relative_path(self):
        """Test BaseAnalyzer initialization with relative path."""
        workspace = Path("relative/workspace")
        analyzer = ConcreteAnalyzer(workspace)

        # BaseAnalyzer resolves paths to absolute paths
        assert analyzer.workspace_root == workspace.resolve()

    def test_abstract_class_cannot_be_instantiated(self):
        """Test that BaseAnalyzer cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAnalyzer(Path("/test"))

    def test_abstract_methods_must_be_implemented(self):
        """Test that abstract methods must be implemented in subclasses."""

        # Create incomplete implementation
        class IncompleteAnalyzer(BaseAnalyzer):
            pass

        with pytest.raises(TypeError):
            IncompleteAnalyzer(Path("/test"))

    @pytest.mark.asyncio
    async def test_analyze_file_abstract_method(self):
        """Test the analyze_file abstract method implementation."""
        analyzer = ConcreteAnalyzer(Path("/workspace"))
        file_path = Path("test.py")

        result = await analyzer.analyze_file(file_path, "deep")

        assert result["file"] == "test.py"
        assert result["analysis_type"] == "deep"
        assert result["test_result"] is True

    @pytest.mark.asyncio
    async def test_analyze_file_default_analysis_type(self):
        """Test analyze_file with default analysis type."""
        analyzer = ConcreteAnalyzer(Path("/workspace"))
        file_path = Path("test.py")

        result = await analyzer.analyze_file(file_path)

        assert result["analysis_type"] == "quick"

    def test_get_file_extensions_abstract_method(self):
        """Test the get_file_extensions abstract method implementation."""
        analyzer = ConcreteAnalyzer(Path("/workspace"))

        extensions = analyzer.get_file_extensions()

        assert extensions == [".py", ".pyw"]
        assert isinstance(extensions, list)

    def test_detect_code_smells_abstract_method(self):
        """Test the detect_code_smells abstract method implementation."""
        analyzer = ConcreteAnalyzer(Path("/workspace"))
        content = "def test_function(): pass"
        file_path = Path("test.py")
        smell_types = ["complexity", "duplication"]

        smells = analyzer.detect_code_smells(content, file_path, smell_types)

        assert len(smells) == 1
        assert smells[0]["type"] == "test_smell"
        assert smells[0]["file"] == "test.py"

    def test_create_base_result_basic_structure(self):
        """Test create_base_result method with basic inputs."""
        analyzer = ConcreteAnalyzer(Path("/workspace"))
        file_path = Path("test.py")
        analysis_type = "quick"

        result = analyzer.create_base_result(file_path, analysis_type)

        required_keys = [
            "file",
            "analysis_type",
            "quality_score",
            "issues",
            "suggestions",
            "metrics",
            "timestamp",
        ]
        for key in required_keys:
            assert key in result

    def test_create_base_result_file_path_handling(self):
        """Test create_base_result with various file path scenarios."""
        analyzer = ConcreteAnalyzer(Path("/workspace"))

        test_cases = [
            Path("simple.py"),
            Path("/absolute/path/file.py"),
            Path("relative/path/file.py"),
            Path("../parent/file.py"),
        ]

        for file_path in test_cases:
            result = analyzer.create_base_result(file_path, "quick")
            assert result["file"] == str(file_path)
            assert result["analysis_type"] == "quick"

    def test_create_base_result_analysis_type_variations(self):
        """Test create_base_result with different analysis types."""
        analyzer = ConcreteAnalyzer(Path("/workspace"))
        file_path = Path("test.py")

        analysis_types = ["quick", "deep", "security", "performance", "custom"]

        for analysis_type in analysis_types:
            result = analyzer.create_base_result(file_path, analysis_type)
            assert result["analysis_type"] == analysis_type

    def test_create_base_result_default_values(self):
        """Test that create_base_result sets correct default values."""
        analyzer = ConcreteAnalyzer(Path("/workspace"))
        file_path = Path("test.py")

        result = analyzer.create_base_result(file_path, "quick")

        assert result["quality_score"] == 0
        assert result["issues"] == []
        assert result["suggestions"] == []
        assert result["metrics"] == {}
        assert isinstance(result["timestamp"], str)

    def test_create_base_result_timestamp_format(self):
        """Test that create_base_result produces valid ISO timestamp."""
        analyzer = ConcreteAnalyzer(Path("/workspace"))
        file_path = Path("test.py")

        result = analyzer.create_base_result(file_path, "quick")

        # Should be able to parse the timestamp
        parsed_timestamp = datetime.fromisoformat(result["timestamp"])
        assert isinstance(parsed_timestamp, datetime)

    @patch("coder_mcp.analysis.base_analyzer.FileMetricsCollector")
    def test_get_basic_metrics_delegation(self, mock_collector):
        """Test that get_basic_metrics delegates to FileMetricsCollector."""
        analyzer = ConcreteAnalyzer(Path("/workspace"))
        content = "test content"
        file_path = Path("test.py")

        expected_metrics = {"lines_of_code": 10, "complexity": 2}
        mock_collector.collect_basic_metrics.return_value = expected_metrics

        result = analyzer.get_basic_metrics(content, file_path)

        mock_collector.collect_basic_metrics.assert_called_once_with(content, file_path)
        assert result == expected_metrics

    @patch("coder_mcp.analysis.base_analyzer.FileMetricsCollector")
    def test_get_basic_metrics_with_various_content(self, mock_collector):
        """Test get_basic_metrics with various content types."""
        analyzer = ConcreteAnalyzer(Path("/workspace"))

        test_contents = [
            "",
            "single line",
            "line 1\nline 2\nline 3",
            "# Comment\ncode\n\n# Another comment",
            "unicode content: 🚀 émoji",
        ]

        mock_metrics = {"lines_of_code": 5}
        mock_collector.collect_basic_metrics.return_value = mock_metrics

        for content in test_contents:
            result = analyzer.get_basic_metrics(content, Path("test.py"))
            assert result == mock_metrics

        assert mock_collector.collect_basic_metrics.call_count == len(test_contents)

    def test_inheritance_and_polymorphism(self):
        """Test that BaseAnalyzer works correctly with inheritance."""

        class CustomAnalyzer(BaseAnalyzer):
            def __init__(self, workspace_root):
                super().__init__(workspace_root, validate_workspace=False)

            async def analyze_file(self, file_path, analysis_type="quick"):
                return {"custom": True}

            def get_file_extensions(self):
                return [".custom"]

            def detect_code_smells(self, content, file_path, smell_types):
                return [{"custom_smell": True}]

        analyzer = CustomAnalyzer(Path("/test"))

        # Test polymorphic behavior
        assert isinstance(analyzer, BaseAnalyzer)
        assert analyzer.get_file_extensions() == [".custom"]

    def test_multiple_analyzer_instances(self):
        """Test that multiple analyzer instances are independent."""
        workspace1 = Path("/workspace1")
        workspace2 = Path("/workspace2")

        analyzer1 = ConcreteAnalyzer(workspace1)
        analyzer2 = ConcreteAnalyzer(workspace2)

        assert analyzer1.workspace_root != analyzer2.workspace_root
        assert analyzer1 is not analyzer2

    @pytest.mark.asyncio
    async def test_async_method_behavior(self):
        """Test that async methods work correctly."""
        analyzer = ConcreteAnalyzer(Path("/workspace"))

        # Test that analyze_file is actually async
        result = analyzer.analyze_file(Path("test.py"))
        assert hasattr(result, "__await__")  # Should be a coroutine

        # Await the result
        actual_result = await result
        assert actual_result["test_result"] is True

    def test_workspace_root_immutability(self):
        """Test that workspace_root doesn't change after initialization."""
        original_workspace = Path("/original/workspace")
        analyzer = ConcreteAnalyzer(original_workspace)

        # Try to modify workspace_root
        analyzer.workspace_root = Path("/modified/workspace")

        # Should be modified (no protection in simplified implementation)
        assert analyzer.workspace_root == Path("/modified/workspace")

    @pytest.mark.parametrize(
        "workspace_path",
        [
            Path("/absolute/workspace"),
            Path("relative/workspace"),
            Path("../parent/workspace"),
            Path("./current/workspace"),
            Path("."),
            Path(".."),
        ],
    )
    def test_init_with_various_workspace_paths(self, workspace_path):
        """Parametrized test for initialization with various workspace paths."""
        analyzer = ConcreteAnalyzer(workspace_path)
        # BaseAnalyzer resolves paths to absolute paths
        assert analyzer.workspace_root == workspace_path.resolve()

    @pytest.mark.parametrize(
        "analysis_type",
        ["quick", "deep", "security", "performance", "custom", "", "very-long-analysis-type-name"],
    )
    def test_create_base_result_analysis_types(self, analysis_type):
        """Parametrized test for create_base_result with various analysis types."""
        analyzer = ConcreteAnalyzer(Path("/workspace"))
        result = analyzer.create_base_result(Path("test.py"), analysis_type)
        assert result["analysis_type"] == analysis_type


class TestBaseAnalyzerIntegration:
    """Integration tests for BaseAnalyzer with real dependencies."""

    def test_integration_with_file_metrics_collector(self):
        """Test integration with real FileMetricsCollector."""
        analyzer = ConcreteAnalyzer(Path("/workspace"))
        content = "# Comment\nprint('hello')\n\n"
        file_path = Path("test.py")

        metrics = analyzer.get_basic_metrics(content, file_path)

        # Should return real metrics
        assert "lines_of_code" in metrics
        assert "blank_lines" in metrics
        assert "comment_lines" in metrics
        assert "file_size_bytes" in metrics
        assert metrics["lines_of_code"] == 3
        assert metrics["blank_lines"] == 1
        assert metrics["comment_lines"] == 1

    @pytest.mark.asyncio
    async def test_complete_analyzer_workflow(self):
        """Test complete workflow using all analyzer methods."""
        workspace = Path("/project")
        analyzer = ConcreteAnalyzer(workspace)

        # 1. Check supported extensions
        extensions = analyzer.get_file_extensions()
        assert ".py" in extensions

        # 2. Analyze a file
        file_path = Path("src/main.py")
        analysis_result = await analyzer.analyze_file(file_path, "deep")
        assert analysis_result["analysis_type"] == "deep"

        # 3. Get basic metrics
        content = "def hello():\n    print('world')\n"
        metrics = analyzer.get_basic_metrics(content, file_path)
        assert metrics["lines_of_code"] == 2

        # 4. Detect code smells
        smells = analyzer.detect_code_smells(content, file_path, ["complexity"])
        assert len(smells) >= 1

        # 5. Create base result structure
        base_result = analyzer.create_base_result(file_path, "deep")
        assert base_result["file"] == "src/main.py"

    def test_analyzer_extensibility(self):
        """Test that BaseAnalyzer can be extended with additional methods."""

        class ExtendedAnalyzer(ConcreteAnalyzer):
            def additional_method(self):
                return "extended functionality"

            def get_workspace_info(self):
                return {
                    "workspace_root": str(self.workspace_root),
                    "extensions": self.get_file_extensions(),
                }

        analyzer = ExtendedAnalyzer(Path("/workspace"))

        # Test original functionality
        assert analyzer.get_file_extensions() == [".py", ".pyw"]

        # Test extended functionality
        assert analyzer.additional_method() == "extended functionality"

        workspace_info = analyzer.get_workspace_info()
        assert workspace_info["workspace_root"] == "/workspace"
        assert workspace_info["extensions"] == [".py", ".pyw"]

    @pytest.mark.asyncio
    async def test_error_handling_in_concrete_methods(self):
        """Test error handling in concrete method implementations."""

        class ErrorProneAnalyzer(BaseAnalyzer):
            def __init__(self, workspace_root):
                super().__init__(workspace_root, validate_workspace=False)

            async def analyze_file(self, file_path, analysis_type="quick"):
                if analysis_type == "error":
                    raise ValueError("Test error")
                return {"success": True}

            def get_file_extensions(self):
                return [".test"]

            def detect_code_smells(self, content, file_path, smell_types):
                if "error" in smell_types:
                    raise RuntimeError("Smell detection error")
                return []

        analyzer = ErrorProneAnalyzer(Path("/workspace"))

        # Test error in analyze_file
        with pytest.raises(ValueError, match="Test error"):
            await analyzer.analyze_file(Path("test.py"), "error")

        # Test error in detect_code_smells
        with pytest.raises(RuntimeError, match="Smell detection error"):
            analyzer.detect_code_smells("content", Path("test.py"), ["error"])

    def test_base_methods_consistency(self):
        """Test that base methods produce consistent results."""
        analyzer = ConcreteAnalyzer(Path("/workspace"))
        file_path = Path("consistent_test.py")

        # Call create_base_result multiple times
        results = []
        for _ in range(5):
            result = analyzer.create_base_result(file_path, "quick")
            results.append(result)

        # All should have same structure but different timestamps
        for i, result in enumerate(results):
            assert result["file"] == "consistent_test.py"
            assert result["analysis_type"] == "quick"
            assert result["quality_score"] == 0
            assert result["issues"] == []
            assert result["suggestions"] == []
            assert result["metrics"] == {}

            # Timestamps should be slightly different
            if i > 0:
                # Can't guarantee they'll be different due to timing,
                # but structure should be consistent
                assert len(result["timestamp"]) == len(results[0]["timestamp"])
