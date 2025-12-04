"""
Comprehensive tests for analyzer_factory.py module.

This module tests AnalyzerFactory with >90% coverage including:
- Factory creation and analyzer instantiation
- File extension handling and validation
- Integration with generic analyzer
- Edge cases and error conditions
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from coder_mcp.analysis.analyzer_factory import AnalyzerFactory, get_analyzer_factory


class TestAnalyzerFactory:
    """Comprehensive test suite for AnalyzerFactory."""

    def test_init_sets_workspace_root(self):
        """Test that AnalyzerFactory correctly sets workspace root."""
        workspace = Path("/test/workspace")
        factory = AnalyzerFactory(workspace)

        assert factory.workspace_root == workspace
        assert isinstance(factory.workspace_root, Path)

    def test_init_sets_supported_extensions(self):
        """Test that AnalyzerFactory correctly initializes supported extensions."""
        workspace = Path("/test/workspace")
        factory = AnalyzerFactory(workspace)

        # Updated to match actual implementation with enhanced file type support
        expected_extensions = {
            # Python files
            ".py": "python",
            ".pyw": "python",
            ".pyi": "python",
            # JavaScript files
            ".js": "javascript",
            ".jsx": "javascript",
            ".mjs": "javascript",
            ".cjs": "javascript",
            # TypeScript files
            ".ts": "typescript",
            ".tsx": "typescript",
        }
        assert factory._extensions == expected_extensions

    def test_init_with_string_path(self):
        """Test AnalyzerFactory initialization with string path."""
        workspace_str = "/test/workspace"
        factory = AnalyzerFactory(workspace_str)

        assert factory.workspace_root == Path(workspace_str)
        assert isinstance(factory.workspace_root, Path)

    def test_init_with_relative_path(self):
        """Test AnalyzerFactory initialization with relative path."""
        workspace = Path("relative/workspace")
        factory = AnalyzerFactory(workspace)

        assert factory.workspace_root == workspace

    def test_get_analyzer_returns_appropriate_analyzer(self):
        """Test that get_analyzer returns appropriate analyzer type based on caching and fallback
        strategy."""
        workspace = Path("/test/workspace")
        factory = AnalyzerFactory(workspace)

        # Test with different file types to ensure analyzer creation works
        file_types = [
            Path("test.py"),
            Path("app.js"),
            Path("component.ts"),
            Path("style.css"),  # Unsupported, should get generic
        ]

        for file_path in file_types:
            analyzer = factory.get_analyzer(file_path)
            # Should get some analyzer back (either specific or generic fallback)
            assert analyzer is not None
            assert hasattr(analyzer, "analyze_file")

    def test_get_analyzer_caching_behavior(self):
        """Test that get_analyzer properly caches analyzer instances."""
        workspace = Path("/test/workspace")
        factory = AnalyzerFactory(workspace)

        # Get analyzers for same type multiple times
        file1 = Path("test1.py")
        file2 = Path("test2.py")

        analyzer1 = factory.get_analyzer(file1)
        analyzer2 = factory.get_analyzer(file2)

        # Should be same instance due to caching
        assert analyzer1 is analyzer2

    def test_get_analyzer_with_different_file_types(self):
        """Test get_analyzer with various file types."""
        workspace = Path("/test/workspace")
        factory = AnalyzerFactory(workspace)

        file_types = [
            Path("script.py"),
            Path("app.js"),
            Path("component.ts"),
            Path("style.css"),
            Path("document.txt"),
            Path("config.json"),
        ]

        for file_path in file_types:
            analyzer = factory.get_analyzer(file_path)
            assert analyzer is not None
            assert hasattr(analyzer, "analyze_file")

    def test_can_analyze_returns_true_for_all_files(self):
        """Test can_analyze returns True for all files due to generic analyzer fallback."""
        workspace = Path("/test/workspace")
        factory = AnalyzerFactory(workspace)

        test_files = [
            Path("script.py"),
            Path("app.js"),
            Path("component.ts"),
            Path("style.css"),
            Path("document.txt"),
            Path("config.json"),
            Path("image.png"),
            Path("binary.exe"),
            Path("Script.PY"),  # Test case insensitivity
            Path("App.JS"),
            Path("Component.TS"),
        ]

        # All should return True due to generic analyzer fallback
        for file_path in test_files:
            assert factory.can_analyze(file_path) is True

    def test_can_analyze_no_extension(self):
        """Test can_analyze with files that have no extension."""
        workspace = Path("/test/workspace")
        factory = AnalyzerFactory(workspace)

        files_without_extension = [
            Path("Makefile"),
            Path("README"),
            Path("LICENSE"),
            Path("Dockerfile"),
        ]

        # All should return True due to generic analyzer fallback
        for file_path in files_without_extension:
            assert factory.can_analyze(file_path) is True

    def test_can_analyze_multiple_dots(self):
        """Test can_analyze with files that have multiple dots."""
        workspace = Path("/test/workspace")
        factory = AnalyzerFactory(workspace)

        multi_dot_files = [
            Path("test.spec.js"),
            Path("config.local.py"),
            Path("app.min.js"),
            Path("data.backup.txt"),
        ]

        # All should return True due to generic analyzer fallback
        for file_path in multi_dot_files:
            assert factory.can_analyze(file_path) is True

    def test_can_analyze_with_path_components(self):
        """Test can_analyze with complex path structures."""
        workspace = Path("/test/workspace")
        factory = AnalyzerFactory(workspace)

        complex_paths = [
            Path("/absolute/path/to/script.py"),
            Path("relative/path/to/app.js"),
            Path("../parent/component.ts"),
            Path("./current/style.css"),
            Path("deeply/nested/folder/structure/file.py"),
        ]

        # All should return True due to generic analyzer fallback
        for file_path in complex_paths:
            assert factory.can_analyze(file_path) is True

    def test_get_supported_extensions(self):
        """Test that get_supported_extensions returns correct mapping."""
        workspace = Path("/test/workspace")
        factory = AnalyzerFactory(workspace)

        supported = factory.get_supported_extensions()

        # Should contain all supported extensions
        expected_keys = {".py", ".pyw", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}
        assert set(supported.keys()) == expected_keys

        # Should be a copy (immutable)
        supported[".test"] = "test"
        assert ".test" not in factory.get_supported_extensions()

    def test_get_analyzer_type(self):
        """Test get_analyzer_type method."""
        workspace = Path("/test/workspace")
        factory = AnalyzerFactory(workspace)

        test_cases = [
            (Path("test.py"), "python"),
            (Path("test.js"), "javascript"),
            (Path("test.jsx"), "javascript"),
            (Path("test.ts"), "typescript"),
            (Path("test.tsx"), "typescript"),
            (Path("test.css"), "generic"),
            (Path("test"), "generic"),
        ]

        for file_path, expected_type in test_cases:
            assert factory.get_analyzer_type(file_path) == expected_type

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        workspace = Path("/test/workspace")
        factory = AnalyzerFactory(workspace)

        # Get an analyzer to populate cache
        factory.get_analyzer(Path("test.py"))

        # Verify cache has content
        cache_info = factory.get_cache_info()
        assert cache_info["total_cached"] > 0

        # Clear cache
        factory.clear_cache()

        # Verify cache is empty
        cache_info = factory.get_cache_info()
        assert cache_info["total_cached"] == 0

    def test_get_cache_info(self):
        """Test cache information reporting."""
        workspace = Path("/test/workspace")
        factory = AnalyzerFactory(workspace)

        # Initially empty
        cache_info = factory.get_cache_info()
        assert cache_info["total_cached"] == 0

        # Add some analyzers
        factory.get_analyzer(Path("test.py"))
        factory.get_analyzer(Path("test.js"))

        cache_info = factory.get_cache_info()
        assert cache_info["total_cached"] > 0

    def test_factory_independence(self):
        """Test that multiple factory instances are independent."""
        workspace1 = Path("/workspace1")
        workspace2 = Path("/workspace2")

        factory1 = AnalyzerFactory(workspace1)
        factory2 = AnalyzerFactory(workspace2)

        # Should have different workspace roots
        assert factory1.workspace_root != factory2.workspace_root

        # Should have same extensions (but different instances)
        assert factory1._extensions == factory2._extensions
        assert factory1._extensions is not factory2._extensions


class TestGetAnalyzerFactory:
    """Test suite for the get_analyzer_factory function."""

    def test_get_analyzer_factory_returns_analyzer_factory(self):
        """Test that get_analyzer_factory returns an AnalyzerFactory instance."""
        workspace = Path("/test/workspace")
        result = get_analyzer_factory(workspace)

        assert isinstance(result, AnalyzerFactory)
        assert result.workspace_root == workspace

    def test_get_analyzer_factory_with_string_path(self):
        """Test get_analyzer_factory with string workspace path."""
        workspace_str = "/test/workspace"
        result = get_analyzer_factory(workspace_str)

        assert isinstance(result, AnalyzerFactory)
        assert result.workspace_root == Path(workspace_str)

    def test_get_analyzer_factory_creates_new_instances(self):
        """Test that get_analyzer_factory creates new instances each time."""
        workspace = Path("/test/workspace")

        factory1 = get_analyzer_factory(workspace)
        factory2 = get_analyzer_factory(workspace)

        # Should be different instances (no caching in simplified version)
        assert factory1 is not factory2
        assert factory1.workspace_root == factory2.workspace_root

    def test_get_analyzer_factory_with_different_workspaces(self):
        """Test get_analyzer_factory with different workspace paths."""
        workspace1 = Path("/workspace1")
        workspace2 = Path("/workspace2")

        factory1 = get_analyzer_factory(workspace1)
        factory2 = get_analyzer_factory(workspace2)

        assert factory1.workspace_root == workspace1
        assert factory2.workspace_root == workspace2
        assert factory1 is not factory2

    @patch("coder_mcp.analysis.analyzer_factory.AnalyzerFactory")
    def test_get_analyzer_factory_delegates_to_constructor(self, mock_analyzer_factory):
        """Test that get_analyzer_factory delegates to AnalyzerFactory constructor."""
        workspace = Path("/test/workspace")
        mock_instance = Mock()
        mock_analyzer_factory.return_value = mock_instance

        result = get_analyzer_factory(workspace)

        mock_analyzer_factory.assert_called_once_with(workspace)
        assert result == mock_instance


class TestAnalyzerFactoryIntegration:
    """Integration tests for AnalyzerFactory."""

    def test_full_workflow_python_file(self):
        """Test complete workflow for analyzing a Python file."""
        workspace = Path("/project")
        factory = get_analyzer_factory(workspace)

        python_file = Path("src/main.py")

        # Check if file can be analyzed (should always be True)
        can_analyze = factory.can_analyze(python_file)
        assert can_analyze is True

        # Get analyzer
        analyzer = factory.get_analyzer(python_file)

        # Verify results
        assert analyzer is not None
        assert hasattr(analyzer, "analyze_file")

    def test_full_workflow_unsupported_file(self):
        """Test complete workflow for an unsupported file type."""
        workspace = Path("/project")
        factory = get_analyzer_factory(workspace)

        unsupported_file = Path("document.txt")

        # Check if file can be analyzed (should be True due to generic fallback)
        can_analyze = factory.can_analyze(unsupported_file)
        assert can_analyze is True

        # Get analyzer
        analyzer = factory.get_analyzer(unsupported_file)

        # Should return an analyzer (GenericAnalyzer can handle any file)
        assert analyzer is not None
        assert hasattr(analyzer, "analyze_file")

    def test_factory_consistency(self):
        """Test that factory behavior is consistent across multiple calls."""
        workspace = Path("/consistent/workspace")
        factory = AnalyzerFactory(workspace)

        test_files = [
            Path("test1.py"),
            Path("test2.js"),
            Path("test3.ts"),
            Path("test4.css"),
        ]

        # Test can_analyze consistency (all should be True)
        for _ in range(3):  # Call multiple times
            results = [factory.can_analyze(f) for f in test_files]
            assert results == [True, True, True, True]

    @pytest.mark.parametrize(
        "workspace_path",
        [
            Path("/absolute/workspace"),
            Path("relative/workspace"),
            Path("../parent/workspace"),
            Path("./current/workspace"),
        ],
    )
    def test_factory_with_various_workspace_paths(self, workspace_path):
        """Parametrized test for factory with various workspace path types."""
        factory = AnalyzerFactory(workspace_path)
        assert factory.workspace_root == workspace_path

    @pytest.mark.parametrize(
        "file_path,expected",
        [
            (Path("test.py"), True),
            (Path("test.js"), True),
            (Path("test.ts"), True),
            (Path("test.css"), True),  # Changed to True due to generic fallback
            (Path("test.html"), True),  # Changed to True due to generic fallback
            (Path("test"), True),  # Changed to True due to generic fallback
            (Path("test.PY"), True),
            (Path("test.JS"), True),
            (Path("test.TS"), True),
        ],
    )
    def test_can_analyze_parametrized(self, file_path, expected):
        """Parametrized test for can_analyze method."""
        workspace = Path("/test")
        factory = AnalyzerFactory(workspace)
        assert factory.can_analyze(file_path) is expected
