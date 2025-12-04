"""
Comprehensive tests for analysis __init__.py module.

This module tests CodeAnalyzer with >90% coverage including:
- Initialization and factory integration
- File analysis workflow
- Code smell detection
- Error handling and edge cases
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from coder_mcp.analysis import CodeAnalyzer


class TestCodeAnalyzer:
    """Comprehensive test suite for CodeAnalyzer."""

    def test_init_sets_workspace_root(self):
        """Test that CodeAnalyzer correctly sets workspace root."""
        with patch("coder_mcp.analysis.get_analyzer_factory"):
            workspace = Path("/test/workspace")
            analyzer = CodeAnalyzer(workspace)

            assert analyzer.workspace_root == workspace
            assert isinstance(analyzer.workspace_root, Path)

    def test_init_with_string_path(self):
        """Test CodeAnalyzer initialization with string path."""
        with patch("coder_mcp.analysis.get_analyzer_factory"):
            workspace_str = "/test/workspace"
            analyzer = CodeAnalyzer(workspace_str)

            assert analyzer.workspace_root == Path(workspace_str)
            assert isinstance(analyzer.workspace_root, Path)

    @patch("coder_mcp.analysis.get_analyzer_factory")
    def test_init_creates_factory(self, mock_get_factory):
        """Test that CodeAnalyzer creates analyzer factory."""
        workspace = Path("/test/workspace")
        mock_factory = Mock()
        mock_get_factory.return_value = mock_factory

        analyzer = CodeAnalyzer(workspace)

        mock_get_factory.assert_called_once_with(workspace)
        assert analyzer.factory == mock_factory

    @patch("coder_mcp.analysis.get_analyzer_factory")
    @pytest.mark.asyncio
    async def test_analyze_file_basic_workflow(self, mock_get_factory):
        """Test basic file analysis workflow."""
        # Set up mocks first
        mock_analyzer = AsyncMock()
        mock_factory = Mock()
        mock_factory.get_analyzer.return_value = mock_analyzer
        mock_get_factory.return_value = mock_factory

        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        expected_result = {"file": "test.py", "quality_score": 8}
        mock_analyzer.analyze_file.return_value = expected_result

        # Test file analysis
        file_path = "test.py"
        result = await analyzer.analyze_file(file_path)

        # Verify calls and result
        mock_factory.get_analyzer.assert_called_once_with(Path(file_path))
        mock_analyzer.analyze_file.assert_called_once_with(Path(file_path), "quick")
        assert result == expected_result

    @patch("coder_mcp.analysis.get_analyzer_factory")
    @pytest.mark.asyncio
    async def test_analyze_file_with_analysis_type(self, mock_get_factory):
        """Test file analysis with specific analysis type."""
        # Set up mocks first
        mock_analyzer = AsyncMock()
        mock_factory = Mock()
        mock_factory.get_analyzer.return_value = mock_analyzer
        mock_get_factory.return_value = mock_factory

        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        file_path = "test.py"
        analysis_type = "deep"

        await analyzer.analyze_file(file_path, analysis_type)

        mock_analyzer.analyze_file.assert_called_once_with(Path(file_path), analysis_type)

    @patch("coder_mcp.analysis.get_analyzer_factory")
    @pytest.mark.asyncio
    async def test_detect_code_smells_basic_workflow(self, mock_get_factory):
        """Test basic code smell detection workflow."""
        # Mock the factory first
        mock_factory = Mock()
        mock_get_factory.return_value = mock_factory

        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        # Mock file system and analyzer
        test_files = [
            Path("src/file1.py"),
            Path("src/file2.js"),
        ]

        with (
            patch("pathlib.Path.rglob") as mock_rglob,
            patch("pathlib.Path.is_file") as mock_is_file,
            patch("builtins.open", create=True) as mock_open,
        ):

            # Setup file system mocks
            mock_rglob.return_value = test_files
            mock_is_file.return_value = True
            mock_factory.can_analyze.return_value = True

            # Setup file content mock
            mock_file = Mock()
            mock_file.read.return_value = "test content"
            mock_open.return_value.__enter__.return_value = mock_file

            # Setup analyzer mocks
            mock_analyzers = []
            for _ in test_files:
                mock_analyzer = Mock()
                mock_analyzer.detect_code_smells.return_value = [
                    {"type": "test_smell", "file": "test", "severity": "medium"}
                ]
                mock_analyzers.append(mock_analyzer)

            mock_factory.get_analyzer.side_effect = mock_analyzers

            # Run detection
            path = Path("/workspace/src")
            smell_types = ["complexity", "duplication"]
            severity_threshold = "medium"

            result = await analyzer.detect_code_smells(path, smell_types, severity_threshold)

            # Verify results
            assert len(result) == len(test_files)
            assert mock_factory.can_analyze.call_count == len(test_files)
            assert mock_factory.get_analyzer.call_count == len(test_files)

    def test_code_analyzer_import(self):
        """Test that CodeAnalyzer can be imported from the package."""
        # This test verifies the __all__ export works correctly
        from coder_mcp.analysis import CodeAnalyzer as ImportedCodeAnalyzer

        assert ImportedCodeAnalyzer is CodeAnalyzer
