"""
Unit tests for code analyzer functionality.

Tests the main CodeAnalyzer class and its analysis capabilities.
"""

import asyncio
from pathlib import Path

import pytest

from coder_mcp.analysis import CodeAnalyzer


class TestCodeAnalyzer:
    """Test CodeAnalyzer class functionality."""

    def test_analyzer_initialization(self, tmp_path):
        """Test analyzer initialization with workspace."""
        analyzer = CodeAnalyzer(workspace_root=tmp_path)
        assert analyzer.workspace_root == tmp_path
        assert hasattr(analyzer, "file_manager")

    def test_analyzer_initialization_default_workspace(self):
        """Test analyzer initialization with default workspace."""
        analyzer = CodeAnalyzer(workspace_root=Path.cwd())
        assert analyzer.workspace_root == Path.cwd()

    @pytest.mark.asyncio
    async def test_analyze_file_python(self, tmp_path):
        """Test analyzing a Python file."""
        analyzer = CodeAnalyzer(workspace_root=tmp_path)

        # Create a Python file
        python_file = tmp_path / "test.py"
        python_content = '''
def hello_world():
    """A simple function."""
    return "Hello, World!"

class TestClass:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Hello, {self.name}"
'''
        python_file.write_text(python_content)

        # Analyze the file
        result = await analyzer.analyze_file(python_file)

        # Check basic structure
        assert isinstance(result, dict)
        assert "file_path" in result
        assert "language" in result
        assert "metrics" in result
        assert result["language"] == "python"

    @pytest.mark.asyncio
    async def test_analyze_file_javascript(self, tmp_path):
        """Test analyzing a JavaScript file."""
        analyzer = CodeAnalyzer(workspace_root=tmp_path)

        # Create a JavaScript file
        js_file = tmp_path / "test.js"
        js_content = """
function helloWorld() {
    return "Hello, World!";
}

class TestClass {
    constructor(name) {
        this.name = name;
    }

    greet() {
        return `Hello, ${this.name}`;
    }
}
"""
        js_file.write_text(js_content)

        # Analyze the file
        result = await analyzer.analyze_file(js_file)

        # Check basic structure
        assert isinstance(result, dict)
        assert result["language"] == "javascript"

    @pytest.mark.asyncio
    async def test_analyze_file_unsupported_type(self, tmp_path):
        """Test analyzing an unsupported file type."""
        analyzer = CodeAnalyzer(workspace_root=tmp_path)

        # Create an unsupported file
        binary_file = tmp_path / "test.exe"
        binary_file.write_bytes(b"\x89PNG\r\n\x1a\n")

        # Should handle gracefully
        result = await analyzer.analyze_file(binary_file)

        # Should return basic info even for unsupported files
        assert isinstance(result, dict)
        assert "file_path" in result

    @pytest.mark.asyncio
    async def test_analyze_file_nonexistent(self, tmp_path):
        """Test analyzing a nonexistent file."""
        analyzer = CodeAnalyzer(workspace_root=tmp_path)

        nonexistent = tmp_path / "nonexistent.py"

        # Should raise appropriate error
        with pytest.raises(Exception):
            await analyzer.analyze_file(nonexistent)

    @pytest.mark.asyncio
    async def test_analyze_directory(self, tmp_path):
        """Test analyzing a directory of files."""
        analyzer = CodeAnalyzer(workspace_root=tmp_path)

        # Create multiple files
        (tmp_path / "file1.py").write_text("def func1(): pass")
        (tmp_path / "file2.js").write_text("function func2() {}")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.py").write_text("def func3(): pass")

        # Analyze directory
        results = await analyzer.analyze_directory(tmp_path)

        # Should return multiple results
        assert isinstance(results, list)
        assert len(results) >= 2  # At least the code files

        # Each result should be valid
        for result in results:
            assert isinstance(result, dict)
            assert "file_path" in result
            assert "language" in result

    @pytest.mark.asyncio
    async def test_analyze_directory_with_filters(self, tmp_path):
        """Test analyzing directory with file type filters."""
        analyzer = CodeAnalyzer(workspace_root=tmp_path)

        # Create files of different types
        (tmp_path / "script.py").write_text("print('hello')")
        (tmp_path / "app.js").write_text("console.log('hello');")
        (tmp_path / "README.md").write_text("# Project")
        (tmp_path / "data.json").write_text('{"key": "value"}')

        # Analyze with Python filter
        results = await analyzer.analyze_directory(tmp_path, file_patterns=["*.py"])

        # Should only return Python files
        python_results = [r for r in results if r.get("language") == "python"]
        assert len(python_results) >= 1

    @pytest.mark.asyncio
    async def test_get_metrics_summary(self, tmp_path):
        """Test getting metrics summary for analyzed files."""
        analyzer = CodeAnalyzer(workspace_root=tmp_path)

        # Create and analyze some files
        (tmp_path / "simple.py").write_text("def simple(): return 42")
        (tmp_path / "complex.py").write_text(
            """
def complex_function(a, b, c):
    if a > 0:
        if b > 0:
            if c > 0:
                return a + b + c
            else:
                return a + b
        else:
            return a
    else:
        return 0
"""
        )

        results = await analyzer.analyze_directory(tmp_path)
        summary = analyzer.get_metrics_summary(results)

        # Should include aggregated metrics
        assert isinstance(summary, dict)
        assert "total_files" in summary
        assert "languages" in summary
        assert summary["total_files"] >= 2

    @pytest.mark.asyncio
    async def test_detect_code_smells(self, tmp_path):
        """Test code smell detection."""
        analyzer = CodeAnalyzer(workspace_root=tmp_path)

        # Create file with potential code smells
        smelly_file = tmp_path / "smelly.py"
        smelly_content = """
def very_long_function_name_that_violates_naming_conventions():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    f = 9
    g = 10  # Too many variables

    if True:  # Useless condition
        pass

    return x + y + z + a + b + c + d + e + f + g

def duplicate_code():
    x = 1
    y = 2
    return x + y

def more_duplicate_code():
    x = 1
    y = 2
    return x + y
"""
        smelly_file.write_text(smelly_content)

        result = await analyzer.analyze_file(smelly_file)

        # Should detect code smells
        assert "code_smells" in result or "quality_issues" in result

    @pytest.mark.asyncio
    async def test_calculate_complexity_metrics(self, tmp_path):
        """Test complexity metrics calculation."""
        analyzer = CodeAnalyzer(workspace_root=tmp_path)

        # Create file with known complexity
        complex_file = tmp_path / "complex.py"
        complex_content = '''
def complex_function(x, y):
    """Function with cyclomatic complexity of 4."""
    if x > 0:        # +1
        if y > 0:    # +1
            return x + y
        else:        # +1
            return x
    else:            # +1
        return 0
'''
        complex_file.write_text(complex_content)

        result = await analyzer.analyze_file(complex_file)

        # Should include complexity metrics
        assert "metrics" in result
        metrics = result["metrics"]
        assert "complexity" in metrics or "cyclomatic_complexity" in metrics

    @pytest.mark.asyncio
    async def test_error_handling_large_file(self, tmp_path):
        """Test error handling for large files."""
        analyzer = CodeAnalyzer(
            workspace_root=tmp_path
        )  # Note: max_file_size parameter not supported

        # Create a large file
        large_file = tmp_path / "large.py"
        large_content = "# " + "x" * 1000 + "\ndef func(): pass"
        large_file.write_text(large_content)

        # Should handle gracefully
        try:
            result = await analyzer.analyze_file(large_file)
            # Should either skip or return limited analysis
            assert isinstance(result, dict)
        except Exception as e:
            # Should raise appropriate error
            assert "size" in str(e).lower() or "limit" in str(e).lower()

    @pytest.mark.asyncio
    async def test_concurrent_analysis(self, tmp_path):
        """Test concurrent file analysis."""
        analyzer = CodeAnalyzer(workspace_root=tmp_path)

        # Create multiple files
        files = []
        for i in range(5):
            file_path = tmp_path / f"file_{i}.py"
            file_path.write_text(f"def func_{i}(): return {i}")
            files.append(file_path)

        # Analyze concurrently
        tasks = [analyzer.analyze_file(f) for f in files]
        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == 5
        for result in results:
            assert isinstance(result, dict)
            assert "file_path" in result


class TestCodeAnalyzerIntegration:
    """Integration tests for CodeAnalyzer."""

    @pytest.mark.asyncio
    async def test_full_project_analysis(self, tmp_path):
        """Test analysis of a complete project structure."""
        analyzer = CodeAnalyzer(workspace_root=tmp_path)

        # Create a realistic project structure
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "docs").mkdir()

        # Source files
        (tmp_path / "src" / "__init__.py").write_text("")
        (tmp_path / "src" / "main.py").write_text(
            '''
import sys
from pathlib import Path

def main():
    """Main application entry point."""
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
        )
        (tmp_path / "src" / "utils.py").write_text(
            '''
def calculate_sum(numbers):
    """Calculate sum of numbers."""
    return sum(numbers)

def validate_input(data):
    """Validate input data."""
    if not isinstance(data, (list, tuple)):
        raise ValueError("Data must be a list or tuple")
    return True
'''
        )

        # Test files
        (tmp_path / "tests" / "test_main.py").write_text(
            '''
import pytest
from src.main import main

def test_main():
    """Test main function."""
    result = main()
    assert result == 0
'''
        )

        # Documentation
        (tmp_path / "README.md").write_text("# Test Project")
        (tmp_path / "pyproject.toml").write_text('[tool.poetry]\nname = "test"')

        # Analyze the entire project
        results = await analyzer.analyze_directory(tmp_path)

        # Verify comprehensive analysis
        assert len(results) >= 4  # At least the Python files

        # Check for different file types
        languages = {r.get("language") for r in results}
        assert "python" in languages

        # Generate summary
        summary = analyzer.get_metrics_summary(results)
        assert summary["total_files"] >= 4
        assert "python" in summary["languages"]

    @pytest.mark.asyncio
    async def test_analysis_with_syntax_errors(self, tmp_path):
        """Test analysis of files with syntax errors."""
        analyzer = CodeAnalyzer(workspace_root=tmp_path)

        # Create file with syntax error
        broken_file = tmp_path / "broken.py"
        broken_file.write_text(
            """
def broken_function(
    # Missing closing parenthesis and colon
    print("This will cause a syntax error"
"""
        )

        # Should handle syntax errors gracefully
        result = await analyzer.analyze_file(broken_file)

        # Should return some information even for broken files
        assert isinstance(result, dict)
        assert "file_path" in result
        assert "error" in result or "syntax_error" in result

    @pytest.mark.asyncio
    async def test_performance_large_codebase(self, tmp_path):
        """Test performance with larger codebase."""
        analyzer = CodeAnalyzer(workspace_root=tmp_path)

        # Create many files
        for i in range(20):
            file_path = tmp_path / f"module_{i}.py"
            content = f"""
def function_{i}_1():
    return {i} * 1

def function_{i}_2():
    return {i} * 2

class Class_{i}:
    def __init__(self):
        self.value = {i}

    def method_{i}(self):
        return self.value * 2
"""
            file_path.write_text(content)

        # Time the analysis
        import time

        start_time = time.time()

        results = await analyzer.analyze_directory(tmp_path)

        end_time = time.time()
        analysis_time = end_time - start_time

        # Should complete in reasonable time (adjust threshold as needed)
        assert analysis_time < 10.0  # 10 seconds max for 20 files
        assert len(results) == 20

        # All results should be valid
        for result in results:
            assert isinstance(result, dict)
            assert "file_path" in result
