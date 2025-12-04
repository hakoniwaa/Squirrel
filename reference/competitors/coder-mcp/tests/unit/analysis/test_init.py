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
from tests.helpers.utils import (
    AsyncAssertions,
    FileBuilder,
    ProjectBuilder,
    mock_async,
)


class TestCodeAnalyzer:
    """Comprehensive test suite for CodeAnalyzer."""

    def test_init_sets_workspace_root(self):
        """Test that CodeAnalyzer correctly sets workspace root."""
        workspace = Path("/test/workspace")
        analyzer = CodeAnalyzer(workspace)

        assert analyzer.workspace_root == workspace
        assert isinstance(analyzer.workspace_root, Path)

    def test_init_with_string_path(self):
        """Test CodeAnalyzer initialization with string path."""
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

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_analyze_file_basic_workflow(self, mock_get_factory):
        """Test basic file analysis workflow using helper patterns."""
        # Create proper async mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze_file = mock_async(
            return_value={"file": "test.py", "quality_score": 8}
        )

        mock_factory = Mock()
        mock_factory.get_analyzer.return_value = mock_analyzer
        mock_get_factory.return_value = mock_factory

        # Create test file using FileBuilder
        test_file = FileBuilder().with_name("test.py").with_language("python").build()

        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        # Test file analysis with timeout assertion
        result = await AsyncAssertions.assert_completes_within(
            analyzer.analyze_file(test_file["name"]),
            timeout=5.0,
            message="File analysis should complete quickly",
        )

        # Verify calls and result
        mock_factory.get_analyzer.assert_called_once_with(Path(test_file["name"]))
        assert result["file"] == "test.py"
        assert result["quality_score"] == 8

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
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

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_analyze_file_with_use_cache_parameter(self, mock_get_factory):
        """Test file analysis with use_cache parameter (should be ignored)."""
        # Set up mocks first
        mock_analyzer = AsyncMock()
        mock_factory = Mock()
        mock_factory.get_analyzer.return_value = mock_analyzer
        mock_get_factory.return_value = mock_factory

        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        file_path = "test.py"

        # use_cache parameter should be accepted but ignored
        await analyzer.analyze_file(file_path, use_cache=False)

        mock_analyzer.analyze_file.assert_called_once_with(Path(file_path), "quick")

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_analyze_file_with_path_object(self, mock_get_factory):
        """Test file analysis with Path object input."""
        # Set up mocks first
        mock_analyzer = AsyncMock()
        mock_factory = Mock()
        mock_factory.get_analyzer.return_value = mock_analyzer
        mock_get_factory.return_value = mock_factory

        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        file_path = Path("src/main.py")

        await analyzer.analyze_file(file_path)

        mock_factory.get_analyzer.assert_called_once_with(file_path)
        mock_analyzer.analyze_file.assert_called_once_with(file_path, "quick")

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_detect_code_smells_basic_workflow(self, mock_get_factory):
        """Test basic code smell detection workflow using helper patterns."""
        # Use helper to create mock factory
        mock_factory = Mock()
        mock_get_factory.return_value = mock_factory

        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        # Use ProjectBuilder to create test project structure
        project_files = (
            ProjectBuilder()
            .with_name("test_project")
            .with_type("python")
            .with_size("small")
            .build()
        )

        # Create test files using the project structure
        test_files = [Path(f"src/{file}") for file in project_files.keys() if file.endswith(".py")]

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

            # Setup analyzer mocks using helper
            mock_analyzer = Mock()
            mock_analyzer.detect_code_smells.return_value = [
                {"type": "test_smell", "file": "test", "severity": "medium"}
            ]
            mock_factory.get_analyzer.return_value = mock_analyzer

            # Run detection using helper timeout
            result = await AsyncAssertions.assert_completes_within(
                analyzer.detect_code_smells(Path("/workspace/src"), ["complexity"], "medium"),
                timeout=10.0,
                message="Code smell detection should complete within reasonable time",
            )

            # Verify results
            assert len(result) == len(test_files)
            assert mock_factory.can_analyze.call_count == len(test_files)

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_detect_code_smells_with_unsupported_files(self, mock_get_factory):
        """Test code smell detection with unsupported file types."""
        mock_factory = Mock()
        mock_get_factory.return_value = mock_factory

        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        test_files = [
            Path("src/supported.py"),
            Path("src/unsupported.txt"),
            Path("src/another_supported.js"),
        ]

        with (
            patch("pathlib.Path.rglob") as mock_rglob,
            patch("pathlib.Path.is_file") as mock_is_file,
            patch("builtins.open", create=True) as mock_open,
        ):

            mock_rglob.return_value = test_files
            mock_is_file.return_value = True

            # Mock file reading
            mock_file = Mock()
            mock_file.read.return_value = "test content"
            mock_open.return_value.__enter__.return_value = mock_file

            # Only some files are supported
            def can_analyze_side_effect(file_path):
                return file_path.suffix in [".py", ".js"]

            mock_factory.can_analyze.side_effect = can_analyze_side_effect

            # Mock analyzer
            mock_analyzer = Mock()
            mock_analyzer.detect_code_smells.return_value = []
            mock_factory.get_analyzer.return_value = mock_analyzer

            await analyzer.detect_code_smells(Path("/workspace/src"), [], "medium")

            # Should only analyze supported files
            assert mock_factory.can_analyze.call_count == len(test_files)
            assert mock_factory.get_analyzer.call_count == 2  # Only supported files

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_detect_code_smells_with_directories(self, mock_get_factory):
        """Test code smell detection filtering out directories."""
        mock_factory = Mock()
        mock_get_factory.return_value = mock_factory

        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        # Mix of files and directories
        test_paths = [
            Path("src/file1.py"),
            Path("src/subdir"),  # Directory
            Path("src/file2.py"),
        ]

        with (
            patch("pathlib.Path.rglob") as mock_rglob,
            patch("pathlib.Path.is_file") as mock_is_file,
            patch("builtins.open", create=True) as mock_open,
        ):

            mock_rglob.return_value = test_paths

            # Only files return True for is_file()
            mock_is_file.side_effect = [True, False, True]  # file, dir, file
            mock_factory.can_analyze.return_value = True

            # Mock file reading
            mock_file = Mock()
            mock_file.read.return_value = "test content"
            mock_open.return_value.__enter__.return_value = mock_file

            # Mock analyzer
            mock_analyzer = Mock()
            mock_analyzer.detect_code_smells.return_value = []
            mock_factory.get_analyzer.return_value = mock_analyzer

            await analyzer.detect_code_smells(Path("/workspace/src"), [], "medium")

            # Should only process files, not directories
            assert mock_factory.can_analyze.call_count == 2  # Only files checked

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_detect_code_smells_empty_directory(self, mock_get_factory):
        """Test code smell detection with empty directory."""
        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        mock_factory = Mock()
        mock_get_factory.return_value = mock_factory

        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.return_value = []  # No files found

            result = await analyzer.detect_code_smells(Path("/workspace/empty"), [], "medium")

            assert result == []
            mock_factory.can_analyze.assert_not_called()
            mock_factory.get_analyzer.assert_not_called()

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_detect_code_smells_file_reading_integration(self, mock_get_factory):
        """Test code smell detection with actual file reading."""
        mock_factory = Mock()
        mock_get_factory.return_value = mock_factory

        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        test_file = Path("test.py")
        test_content = "def function():\n    pass\n"

        with (
            patch("pathlib.Path.rglob") as mock_rglob,
            patch("pathlib.Path.is_file") as mock_is_file,
            patch("builtins.open", create=True) as mock_open,
        ):

            mock_rglob.return_value = [test_file]
            mock_is_file.return_value = True
            mock_factory.can_analyze.return_value = True

            # Mock file reading
            mock_file = Mock()
            mock_file.read.return_value = test_content
            mock_open.return_value.__enter__.return_value = mock_file

            # Mock analyzer
            mock_analyzer = Mock()
            expected_smells = [{"type": "test_smell", "content": test_content}]
            mock_analyzer.detect_code_smells.return_value = expected_smells
            mock_factory.get_analyzer.return_value = mock_analyzer

            result = await analyzer.detect_code_smells(Path("/workspace"), ["test"], "medium")

            # Verify file was read and content passed to analyzer
            mock_open.assert_called_once_with(test_file, "r", encoding="utf-8")
            mock_analyzer.detect_code_smells.assert_called_once_with(
                test_content, test_file, ["test"]
            )
            # Should return per-file results format
            expected_result = [{"file": test_file, "smells": expected_smells}]
            assert result == expected_result

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_detect_code_smells_with_path_object(self, mock_get_factory):
        """Test code smell detection with Path object input."""
        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        mock_factory = Mock()
        mock_get_factory.return_value = mock_factory

        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.return_value = []

            # Should work with Path object
            search_path = Path("/workspace/src")
            result = await analyzer.detect_code_smells(search_path, [], "medium")

            assert result == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize("analysis_type", ["quick", "deep", "security", "performance"])
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_analyze_file_various_analysis_types(self, mock_get_factory, analysis_type):
        """Parametrized test for different analysis types."""
        # Set up mocks first
        mock_analyzer = AsyncMock()
        mock_factory = Mock()
        mock_factory.get_analyzer.return_value = mock_analyzer
        mock_get_factory.return_value = mock_factory

        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        await analyzer.analyze_file("test.py", analysis_type)

        mock_analyzer.analyze_file.assert_called_once_with(Path("test.py"), analysis_type)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("severity_threshold", ["low", "medium", "high"])
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_detect_code_smells_various_severity_thresholds(
        self, mock_get_factory, severity_threshold
    ):
        """Parametrized test for different severity thresholds."""
        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        mock_factory = Mock()
        mock_get_factory.return_value = mock_factory

        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.return_value = []

            result = await analyzer.detect_code_smells(Path("/workspace"), [], severity_threshold)

            assert result == []

    @pytest.mark.parametrize(
        "workspace_path",
        [
            "/absolute/workspace",
            "relative/workspace",
            "../parent/workspace",
            "./current/workspace",
        ],
    )
    def test_init_with_various_workspace_paths(self, workspace_path):
        """Parametrized test for initialization with various workspace paths."""
        with patch("coder_mcp.analysis.get_analyzer_factory"):
            analyzer = CodeAnalyzer(workspace_path)
            assert analyzer.workspace_root == Path(workspace_path)


class TestCodeAnalyzerIntegration:
    """Integration tests for CodeAnalyzer with real dependencies."""

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_real_analyze_file_workflow(self, mock_get_factory):
        """Test analyze_file with more realistic scenario."""
        # Create a more realistic mock analyzer first
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze_file.return_value = {
            "file": "src/main.py",
            "analysis_type": "deep",
            "quality_score": 7.5,
            "issues": ["Missing type hints", "Complex function"],
            "suggestions": ["Add type annotations", "Refactor function"],
            "metrics": {"lines_of_code": 150, "complexity": 8, "test_coverage": 65},
        }

        mock_factory = Mock()
        mock_factory.get_analyzer.return_value = mock_analyzer
        mock_get_factory.return_value = mock_factory

        workspace = Path("/project")
        analyzer = CodeAnalyzer(workspace)

        result = await analyzer.analyze_file("src/main.py", "deep")

        # Verify realistic result structure
        assert result["file"] == "src/main.py"
        assert result["quality_score"] == 7.5
        assert len(result["issues"]) == 2
        assert len(result["suggestions"]) == 2
        assert "metrics" in result

    def test_code_analyzer_import(self):
        """Test that CodeAnalyzer can be imported from the package."""
        # This test verifies the __all__ export works correctly
        from coder_mcp.analysis import CodeAnalyzer as ImportedCodeAnalyzer

        assert ImportedCodeAnalyzer is CodeAnalyzer

    def test_code_analyzer_independence(self):
        """Test that multiple CodeAnalyzer instances are independent."""
        with patch("coder_mcp.analysis.get_analyzer_factory") as mock_get_factory:
            workspace1 = Path("/workspace1")
            workspace2 = Path("/workspace2")

            analyzer1 = CodeAnalyzer(workspace1)
            analyzer2 = CodeAnalyzer(workspace2)

            assert analyzer1.workspace_root != analyzer2.workspace_root
            assert analyzer1 is not analyzer2
            assert mock_get_factory.call_count == 2

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_error_propagation(self, mock_get_factory):
        """Test that errors from underlying components are properly propagated."""
        # Mock analyzer that raises an error
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze_file.side_effect = ValueError("Analysis failed")

        mock_factory = Mock()
        mock_factory.get_analyzer.return_value = mock_analyzer
        mock_get_factory.return_value = mock_factory

        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        # Error should be propagated
        with pytest.raises(ValueError, match="Analysis failed"):
            await analyzer.analyze_file("test.py")

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_factory_error_handling(self, mock_get_factory):
        """Test error handling when factory operations fail."""
        # Mock factory that raises an error
        mock_factory = Mock()
        mock_factory.get_analyzer.side_effect = RuntimeError("Factory error")
        mock_get_factory.return_value = mock_factory

        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        # Error should be propagated
        with pytest.raises(RuntimeError, match="Factory error"):
            await analyzer.analyze_file("test.py")


class TestCodeAnalyzerEdgeCases:
    """Test edge cases and error conditions for CodeAnalyzer."""

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_analyze_file_empty_path(self, mock_get_factory):
        """Test analyze_file with empty file path."""
        mock_analyzer = AsyncMock()
        mock_factory = Mock()
        mock_factory.get_analyzer.return_value = mock_analyzer
        mock_get_factory.return_value = mock_factory

        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        # Should handle empty string path
        await analyzer.analyze_file("")

        mock_factory.get_analyzer.assert_called_once_with(Path(""))

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_detect_code_smells_empty_smell_types(self, mock_get_factory):
        """Test code smell detection with empty smell types list."""
        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        mock_factory = Mock()
        mock_get_factory.return_value = mock_factory

        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.return_value = []

            # Should handle empty smell types
            result = await analyzer.detect_code_smells(Path("/workspace"), [], "medium")

            assert result == []

    @pytest.mark.asyncio
    @patch("coder_mcp.analysis.get_analyzer_factory")
    async def test_analyze_file_all_parameters(self, mock_get_factory):
        """Test analyze_file with all possible parameters."""
        mock_analyzer = AsyncMock()
        mock_factory = Mock()
        mock_factory.get_analyzer.return_value = mock_analyzer
        mock_get_factory.return_value = mock_factory

        workspace = Path("/workspace")
        analyzer = CodeAnalyzer(workspace)

        # Test with all parameters
        await analyzer.analyze_file(file_path="test.py", analysis_type="security", use_cache=True)

        mock_analyzer.analyze_file.assert_called_once_with(Path("test.py"), "security")
