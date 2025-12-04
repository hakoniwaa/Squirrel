"""
Comprehensive tests for AnalyzerFactory module.

This module provides complete test coverage for the AnalyzerFactory class,
including edge cases, error handling, and all functionality.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from coder_mcp.analysis.analyzer_factory import (
    AnalyzerFactory,
    MinimalAnalyzer,
    get_analyzer_factory,
)
from coder_mcp.analysis.base_analyzer import BaseAnalyzer


class TestMinimalAnalyzer:
    """Test MinimalAnalyzer emergency fallback."""

    @pytest.fixture
    def minimal_analyzer(self, tmp_path):
        """Create MinimalAnalyzer instance."""
        return MinimalAnalyzer(tmp_path)

    def test_initialization(self, minimal_analyzer, tmp_path):
        """Test MinimalAnalyzer initialization."""
        assert minimal_analyzer.workspace_root == tmp_path
        assert isinstance(minimal_analyzer, BaseAnalyzer)

    def test_get_file_extensions(self, minimal_analyzer):
        """Test MinimalAnalyzer supports all file types."""
        extensions = minimal_analyzer.get_file_extensions()
        assert extensions == ["*"]

    @pytest.mark.asyncio
    async def test_analyze_file_success(self, minimal_analyzer, tmp_path):
        """Test successful file analysis."""
        # Create test file
        test_file = tmp_path / "test.py"
        test_content = "# Test comment\nprint('hello')\n\n"
        test_file.write_text(test_content)

        result = await minimal_analyzer.analyze_file(test_file)

        assert result["file"] == "test.py"
        assert result["analysis_type"] == "quick"
        assert result["quality_score"] == 5.0
        assert result["issues"] == []
        assert result["suggestions"] == []
        assert result["analyzer"] == "MinimalAnalyzer"

        # Check metrics
        metrics = result["metrics"]
        assert metrics["total_lines"] == 3
        assert metrics["non_empty_lines"] == 2
        assert metrics["file_size"] == len(test_content)

    @pytest.mark.asyncio
    async def test_analyze_file_custom_analysis_type(self, minimal_analyzer, tmp_path):
        """Test analysis with custom analysis type."""
        test_file = tmp_path / "test.js"
        test_file.write_text("console.log('test');")

        result = await minimal_analyzer.analyze_file(test_file, "deep")

        assert result["analysis_type"] == "deep"
        assert result["quality_score"] == 5.0

    @pytest.mark.asyncio
    async def test_analyze_file_empty_file(self, minimal_analyzer, tmp_path):
        """Test analyzing empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        result = await minimal_analyzer.analyze_file(test_file)

        assert result["metrics"]["total_lines"] == 0
        assert result["metrics"]["non_empty_lines"] == 0
        assert result["metrics"]["file_size"] == 0

    @pytest.mark.asyncio
    async def test_analyze_file_read_error(self, minimal_analyzer, tmp_path):
        """Test handling file read errors."""
        # Non-existent file
        test_file = tmp_path / "nonexistent.py"

        result = await minimal_analyzer.analyze_file(test_file)

        assert result["quality_score"] == 0.0
        assert len(result["issues"]) == 1
        assert "Failed to analyze file" in result["issues"][0]
        assert result["analyzer"] == "MinimalAnalyzer"

    @pytest.mark.asyncio
    async def test_analyze_file_binary_content(self, minimal_analyzer, tmp_path):
        """Test analyzing binary file content."""
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b"\x00\x01\x02\x03")

        result = await minimal_analyzer.analyze_file(test_file)

        # Should handle gracefully even with binary content
        assert "analyzer" in result
        assert result["analysis_type"] == "quick"

    def test_detect_code_smells(self, minimal_analyzer, tmp_path):
        """Test code smell detection (should return empty list)."""
        test_file = tmp_path / "test.py"
        content = "def bad_function():\n    pass"

        smells = minimal_analyzer.detect_code_smells(content, test_file, ["long_functions"])

        assert smells == []


class TestAnalyzerFactory:
    """Test AnalyzerFactory class."""

    @pytest.fixture
    def factory(self, tmp_path):
        """Create AnalyzerFactory instance."""
        return AnalyzerFactory(tmp_path)

    def test_initialization(self, factory, tmp_path):
        """Test AnalyzerFactory initialization."""
        assert factory.workspace_root == tmp_path
        assert factory._analyzer_cache == {}
        assert isinstance(factory._extensions, dict)

        # Check supported extensions
        expected_extensions = {
            ".py": "python",
            ".pyw": "python",
            ".pyi": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".mjs": "javascript",
            ".cjs": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
        }
        assert factory._extensions == expected_extensions

    def test_get_supported_extensions(self, factory):
        """Test getting supported extensions."""
        extensions = factory.get_supported_extensions()

        # Should return a copy
        assert extensions is not factory._extensions
        assert extensions == factory._extensions

        # Test all expected extensions
        assert ".py" in extensions
        assert ".jsx" in extensions
        assert ".tsx" in extensions
        assert ".mjs" in extensions

    def test_get_analyzer_type(self, factory):
        """Test analyzer type detection."""
        test_cases = [
            ("test.py", "python"),
            ("test.pyw", "python"),
            ("test.pyi", "python"),
            ("test.js", "javascript"),
            ("test.jsx", "javascript"),
            ("test.mjs", "javascript"),
            ("test.cjs", "javascript"),
            ("test.ts", "typescript"),
            ("test.tsx", "typescript"),
            ("test.txt", "generic"),
            ("test.java", "generic"),
            ("test", "generic"),  # No extension
        ]

        for filename, expected_type in test_cases:
            assert factory.get_analyzer_type(Path(filename)) == expected_type

    def test_can_analyze(self, factory):
        """Test can_analyze method."""
        # Should return True for all files due to fallback
        test_files = ["test.py", "test.js", "test.tsx", "test.unknown", "no_extension", "test.xyz"]

        for filename in test_files:
            assert factory.can_analyze(Path(filename)) is True

    @patch("coder_mcp.analysis.analyzer_factory.logger")
    def test_get_analyzer_caching(self, mock_logger, factory, tmp_path):
        """Test analyzer caching functionality."""
        test_file = tmp_path / "test.py"

        # First call should create and cache analyzer
        analyzer1 = factory.get_analyzer(test_file)
        assert "python" in factory._analyzer_cache

        # Second call should return cached analyzer
        analyzer2 = factory.get_analyzer(test_file)
        assert analyzer1 is analyzer2

        # Verify debug logging for cache usage
        mock_logger.debug.assert_called()

    def test_get_analyzer_fallback_to_minimal(self, factory, tmp_path):
        """Test fallback to minimal analyzer when all else fails."""
        test_file = tmp_path / "test.py"

        # Clear cache first to ensure fresh creation
        factory.clear_cache()

        # Mock all analyzer creation to fail
        with patch("coder_mcp.analysis.analyzer_factory.logger") as mock_logger:
            with patch.object(factory, "_create_python_analyzer", return_value=None):
                with patch(
                    "coder_mcp.analysis.analyzer_factory.GenericAnalyzer",
                    side_effect=ImportError("Generic analyzer failed"),
                ):
                    analyzer = factory.get_analyzer(test_file)

        assert isinstance(analyzer, MinimalAnalyzer)
        mock_logger.critical.assert_called()

    def test_get_analyzer_different_types(self, factory, tmp_path):
        """Test getting analyzers for different file types."""
        files = [
            (tmp_path / "test.py", "python"),
            (tmp_path / "test.js", "javascript"),
            (tmp_path / "test.ts", "typescript"),
            (tmp_path / "test.txt", "generic"),
        ]

        for file_path, expected_type in files:
            analyzer = factory.get_analyzer(file_path)
            # Should get proper analyzer instances
            assert hasattr(analyzer, "analyze_file")

    def test_clear_cache(self, factory, tmp_path):
        """Test cache clearing functionality."""
        # Add some analyzers to cache
        test_file = tmp_path / "test.py"
        factory.get_analyzer(test_file)

        assert len(factory._analyzer_cache) > 0

        # Clear cache
        with patch("coder_mcp.analysis.analyzer_factory.logger") as mock_logger:
            factory.clear_cache()

        assert factory._analyzer_cache == {}
        mock_logger.debug.assert_called_with("Analyzer cache cleared")

    def test_get_cache_info(self, factory, tmp_path):
        """Test cache information retrieval."""
        # Empty cache
        cache_info = factory.get_cache_info()
        assert cache_info["total_cached"] == 0
        assert cache_info["cached_types"] == 0

        # Add analyzers to cache
        files = [tmp_path / "test.py", tmp_path / "test.js", tmp_path / "test.ts"]

        for file_path in files:
            factory.get_analyzer(file_path)

        cache_info = factory.get_cache_info()
        assert cache_info["total_cached"] == 3  # 3 different types cached
        assert cache_info["cached_types"] == 3
        assert "python_cached" in cache_info
        assert "javascript_cached" in cache_info
        assert "typescript_cached" in cache_info

    def test_create_minimal_analyzer_fallback(self, factory):
        """Test minimal analyzer creation as ultimate fallback."""
        with patch(
            "coder_mcp.analysis.analyzer_factory.GenericAnalyzer",
            side_effect=Exception("Import failed"),
        ):
            analyzer = factory._create_minimal_analyzer()
            assert isinstance(analyzer, MinimalAnalyzer)

    def test_create_analyzer_import_errors(self, factory, tmp_path):
        """Test _create_analyzer with various import errors."""
        test_file = tmp_path / "test.py"

        with patch("coder_mcp.analysis.analyzer_factory.logger") as mock_logger:
            # Test with import error for specific analyzer and generic analyzer
            with patch.object(factory, "_create_python_analyzer", return_value=None):
                with patch(
                    "coder_mcp.analysis.analyzer_factory.GenericAnalyzer",
                    side_effect=ImportError("Module not found"),
                ):
                    analyzer = factory._create_analyzer("python", test_file)
                    assert isinstance(analyzer, MinimalAnalyzer)
                    mock_logger.critical.assert_called()

    def test_create_analyzer_generic_fallback(self, factory, tmp_path):
        """Test _create_analyzer with generic analyzer fallback."""
        test_file = tmp_path / "test.unknown"

        analyzer = factory._create_analyzer("generic", test_file)
        # Should get a valid analyzer instance
        assert hasattr(analyzer, "analyze_file")

    def test_workspace_root_validation(self, tmp_path):
        """Test workspace root validation during initialization."""
        # Valid directory
        factory = AnalyzerFactory(tmp_path)
        assert factory.workspace_root == tmp_path

        # Test with string path
        factory2 = AnalyzerFactory(str(tmp_path))
        assert factory2.workspace_root == tmp_path

    def test_pathlib_path_handling(self, factory, tmp_path):
        """Test proper Path object handling."""
        # Test with string path
        string_path = str(tmp_path / "test.py")
        analyzer_type = factory.get_analyzer_type(string_path)
        assert analyzer_type == "python"

        # Test with Path object
        path_obj = tmp_path / "test.js"
        analyzer_type = factory.get_analyzer_type(path_obj)
        assert analyzer_type == "javascript"

    def test_case_insensitive_extensions(self, factory):
        """Test case-insensitive extension handling."""
        test_cases = [
            ("test.PY", "python"),
            ("test.JS", "javascript"),
            ("test.TS", "typescript"),
            ("test.PyW", "python"),
        ]

        for filename, expected_type in test_cases:
            # Should handle case-insensitive extensions
            assert factory.get_analyzer_type(Path(filename)) == expected_type


class TestGetAnalyzerFactory:
    """Test the get_analyzer_factory function."""

    def test_get_analyzer_factory_function(self, tmp_path):
        """Test get_analyzer_factory function."""
        factory = get_analyzer_factory(tmp_path)

        assert isinstance(factory, AnalyzerFactory)
        assert factory.workspace_root == tmp_path

    def test_get_analyzer_factory_with_string_path(self, tmp_path):
        """Test get_analyzer_factory with string path."""
        factory = get_analyzer_factory(str(tmp_path))

        assert isinstance(factory, AnalyzerFactory)
        assert factory.workspace_root == tmp_path


class TestAnalyzerFactoryIntegration:
    """Integration tests for AnalyzerFactory."""

    @pytest.fixture
    def factory(self, tmp_path):
        """Create factory with test files."""
        factory = AnalyzerFactory(tmp_path)

        # Create test files
        test_files = {
            "python_file.py": "def hello():\n    print('Hello, World!')",
            "js_file.js": "function hello() { console.log('Hello'); }",
            "ts_file.ts": "function hello(): void { console.log('Hello'); }",
            "jsx_file.jsx": "const Hello = () => <div>Hello</div>;",
            "unknown_file.xyz": "Some unknown content",
        }

        for filename, content in test_files.items():
            (tmp_path / filename).write_text(content)

        return factory

    def test_multiple_file_analysis(self, factory, tmp_path):
        """Test analyzing multiple different file types."""
        files = ["python_file.py", "js_file.js", "ts_file.ts", "jsx_file.jsx", "unknown_file.xyz"]

        analyzers = {}
        for filename in files:
            file_path = tmp_path / filename
            analyzer = factory.get_analyzer(file_path)
            analyzers[filename] = analyzer

        # All should be valid analyzer instances
        for analyzer in analyzers.values():
            assert hasattr(analyzer, "analyze_file")

        # Cache should contain different analyzer types
        cache_info = factory.get_cache_info()
        assert cache_info["total_cached"] >= 3

    def test_error_resilience(self, factory, tmp_path):
        """Test factory resilience to various error conditions."""
        # Non-existent file
        analyzer1 = factory.get_analyzer(tmp_path / "nonexistent.py")
        assert analyzer1 is not None

        # File with no extension
        (tmp_path / "no_extension").write_text("content")
        analyzer2 = factory.get_analyzer(tmp_path / "no_extension")
        assert analyzer2 is not None

        # Empty file
        (tmp_path / "empty.py").write_text("")
        analyzer3 = factory.get_analyzer(tmp_path / "empty.py")
        assert analyzer3 is not None

    def test_logging_behavior(self, factory, tmp_path):
        """Test proper logging behavior."""
        with patch("coder_mcp.analysis.analyzer_factory.logger") as mock_logger:
            # Test analyzer creation logging
            test_file = tmp_path / "test.py"
            factory.get_analyzer(test_file)

            # Should log creation and caching
            debug_calls = [call.args[0] for call in mock_logger.debug.call_args_list]
            assert any("Created and cached" in call for call in debug_calls)

            # Test cache hit logging
            factory.get_analyzer(test_file)  # Second call
            debug_calls = [call.args[0] for call in mock_logger.debug.call_args_list]
            assert any("Using cached" in call for call in debug_calls)


class TestAnalyzerFactoryEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_filename(self, tmp_path):
        """Test handling empty filename."""
        factory = AnalyzerFactory(tmp_path)

        # Empty string filename
        analyzer_type = factory.get_analyzer_type(Path(""))
        assert analyzer_type == "generic"

    def test_multiple_dots_in_filename(self, tmp_path):
        """Test filename with multiple dots."""
        factory = AnalyzerFactory(tmp_path)

        test_cases = [
            ("file.test.py", "python"),
            ("file.min.js", "javascript"),
            ("file.d.ts", "typescript"),
            ("file.spec.jsx", "javascript"),
        ]

        for filename, expected_type in test_cases:
            assert factory.get_analyzer_type(Path(filename)) == expected_type

    def test_very_long_filename(self, tmp_path):
        """Test very long filename handling."""
        factory = AnalyzerFactory(tmp_path)

        long_name = "a" * 200 + ".py"
        analyzer_type = factory.get_analyzer_type(Path(long_name))
        assert analyzer_type == "python"

    def test_special_characters_in_filename(self, tmp_path):
        """Test filenames with special characters."""
        factory = AnalyzerFactory(tmp_path)

        test_cases = [
            ("file-name.py", "python"),
            ("file_name.js", "javascript"),
            ("file name.ts", "typescript"),  # Space in name
            ("file@name.jsx", "javascript"),
        ]

        for filename, expected_type in test_cases:
            assert factory.get_analyzer_type(Path(filename)) == expected_type

    def test_concurrent_access(self, tmp_path):
        """Test thread safety of analyzer factory."""
        import threading

        factory = AnalyzerFactory(tmp_path)
        results = []
        errors = []

        def get_analyzer_worker(file_ext):
            try:
                test_file = tmp_path / f"test{threading.current_thread().ident}.{file_ext}"
                analyzer = factory.get_analyzer(test_file)
                results.append((threading.current_thread().ident, analyzer))
            except Exception as e:
                errors.append(e)

        # Create multiple threads accessing factory concurrently
        threads = []
        for i, ext in enumerate(["py", "js", "ts"] * 3):
            thread = threading.Thread(target=get_analyzer_worker, args=(ext,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify no errors and all got analyzers
        assert len(errors) == 0
        assert len(results) == 9  # 3 extensions * 3 repetitions

        # All should be valid analyzer instances
        for thread_id, analyzer in results:
            assert hasattr(analyzer, "analyze_file")
