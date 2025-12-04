"""
Unit tests for dependency analyzer pyproject.toml parsing functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from coder_mcp.analysis.dependency_analyzer import DependencyAnalyzer


class TestDependencyAnalyzerPyproject:
    """Test pyproject.toml parsing in DependencyAnalyzer."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_parse_poetry_dependencies(self, temp_workspace):
        """Test parsing Poetry format dependencies from pyproject.toml."""
        pyproject_content = """
[tool.poetry]
name = "test-project"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.8"
requests = "^2.28.0"
numpy = ">=1.20.0"
fastapi = {version = "^0.100.0", extras = ["all"]}
custom-pkg = {git = "https://github.com/user/repo.git"}

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
black = "^23.0.0"

[tool.poetry.group.test.dependencies]
coverage = "^7.0.0"
"""
        pyproject_file = temp_workspace / "pyproject.toml"
        pyproject_file.write_text(pyproject_content)

        analyzer = DependencyAnalyzer(temp_workspace)
        deps = analyzer._parse_pyproject_toml(pyproject_file)

        # Should include main dependencies (excluding python)
        assert "requests" in deps
        assert "numpy" in deps
        assert "fastapi" in deps
        assert "custom-pkg" in deps
        assert "python" not in deps  # Should be excluded

        # Should include dev dependencies with group names
        assert "pytest (dev)" in deps
        assert "black (dev)" in deps
        assert "coverage (test)" in deps

        # Check version parsing
        assert deps["requests"] == "^2.28.0"
        assert deps["numpy"] == ">=1.20.0"
        assert "git+" in deps["custom-pkg"]

    def test_parse_pep621_dependencies(self, temp_workspace):
        """Test parsing PEP 621 format dependencies from pyproject.toml."""
        pyproject_content = """
[project]
name = "test-project"
version = "0.1.0"
dependencies = [
    "requests>=2.28.0",
    "numpy>=1.20.0",
    "fastapi",
]
"""
        pyproject_file = temp_workspace / "pyproject.toml"
        pyproject_file.write_text(pyproject_content)

        analyzer = DependencyAnalyzer(temp_workspace)
        deps = analyzer._parse_pyproject_toml(pyproject_file)

        assert "requests" in deps
        assert "numpy" in deps
        assert "fastapi" in deps

        assert deps["requests"] == ">=2.28.0"
        assert deps["numpy"] == ">=1.20.0"
        assert deps["fastapi"] == "*"

    @pytest.mark.asyncio
    async def test_analyze_python_deps_with_pyproject(self, temp_workspace):
        """Test full analyze method with pyproject.toml file."""
        pyproject_content = """
[tool.poetry]
name = "test-project"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.8"
requests = "^2.28.0"
numpy = ">=1.20.0"
"""
        pyproject_file = temp_workspace / "pyproject.toml"
        pyproject_file.write_text(pyproject_content)

        analyzer = DependencyAnalyzer(temp_workspace)
        result = await analyzer.analyze(check_updates=False, security_scan=False)

        assert result["total_dependencies"] == 2  # requests + numpy (python excluded)
        assert "requests" in result["dependencies"]
        assert "numpy" in result["dependencies"]
        assert "python" not in result["dependencies"]

    def test_fallback_to_pyproject_when_no_requirements(self, temp_workspace):
        """Test that analyzer falls back to pyproject.toml when requirements.txt doesn't exist."""
        # Create only pyproject.toml, no requirements.txt
        pyproject_content = """
[tool.poetry.dependencies]
python = "^3.8"
requests = "^2.28.0"
"""
        pyproject_file = temp_workspace / "pyproject.toml"
        pyproject_file.write_text(pyproject_content)

        analyzer = DependencyAnalyzer(temp_workspace)
        deps = analyzer._parse_pyproject_toml(pyproject_file)

        assert len(deps) == 1  # Only requests, python excluded
        assert "requests" in deps

    @patch("coder_mcp.analysis.dependency_analyzer.toml", None)
    def test_graceful_handling_when_toml_not_available(self, temp_workspace):
        """Test graceful handling when toml library is not available."""
        pyproject_file = temp_workspace / "pyproject.toml"
        pyproject_file.write_text("[tool.poetry.dependencies]\nrequests = '^2.28.0'")

        analyzer = DependencyAnalyzer(temp_workspace)
        deps = analyzer._parse_pyproject_toml(pyproject_file)

        assert deps == {}  # Should return empty dict when toml not available

    def test_malformed_pyproject_toml(self, temp_workspace):
        """Test handling of malformed pyproject.toml files."""
        pyproject_file = temp_workspace / "pyproject.toml"
        pyproject_file.write_text("invalid toml content [[[")

        analyzer = DependencyAnalyzer(temp_workspace)
        deps = analyzer._parse_pyproject_toml(pyproject_file)

        assert deps == {}  # Should return empty dict on parse error
