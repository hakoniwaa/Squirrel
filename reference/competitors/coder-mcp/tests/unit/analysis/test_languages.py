"""Test language-specific analyzers."""

import pytest

from coder_mcp.analysis.languages.generic_analyzer import GenericAnalyzer
from coder_mcp.analysis.languages.javascript_analyzer import JavaScriptAnalyzer
from coder_mcp.analysis.languages.python_analyzer import PythonAnalyzer
from coder_mcp.analysis.languages.typescript_analyzer import TypeScriptAnalyzer


class TestPythonAnalyzer:
    """Test PythonAnalyzer class."""

    @pytest.fixture
    def analyzer(self, tmp_path):
        """Create PythonAnalyzer instance."""
        return PythonAnalyzer(tmp_path)

    def test_initialization(self, analyzer, tmp_path):
        """Test PythonAnalyzer initialization."""
        assert analyzer.workspace_root == tmp_path
        assert hasattr(analyzer, "logger")

    def test_get_file_extensions(self, analyzer):
        """Test supported file extensions."""
        extensions = analyzer.get_file_extensions()

        expected_extensions = [".py", ".pyw", ".pyi"]
        assert extensions == expected_extensions

    def test_supports_file(self, analyzer, tmp_path):
        """Test file support detection."""
        test_cases = [
            ("test.py", True),
            ("test.pyw", True),
            ("test.pyi", True),
            ("test.PY", True),  # Case insensitive
            ("test.js", False),
            ("test.txt", False),
        ]

        for filename, expected in test_cases:
            file_path = tmp_path / filename
            assert analyzer.supports_file(file_path) == expected

    @pytest.mark.asyncio
    async def test_analyze_file_simple_python(self, analyzer, tmp_path):
        """Test analyzing simple Python file."""
        test_file = tmp_path / "simple.py"
        test_content = '''
def hello_world():
    """Simple function."""
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello_world()
'''
        test_file.write_text(test_content)

        result = await analyzer.analyze_file(test_file)

        assert result["file"] == "simple.py"
        assert result["quality_score"] > 0
        assert "metrics" in result

        # Should have detected the function
        metrics = result["metrics"]
        assert "functions" in metrics
        assert metrics["functions"] >= 1

    @pytest.mark.asyncio
    async def test_analyze_file_syntax_error(self, analyzer, tmp_path):
        """Test analyzing Python file with syntax error."""
        test_file = tmp_path / "broken.py"
        test_content = "def broken_function(\n"  # Missing closing parenthesis
        test_file.write_text(test_content)

        result = await analyzer.analyze_file(test_file)

        assert result["file"] == "broken.py"
        assert result["quality_score"] >= 0  # Should handle gracefully
        assert "issues" in result or "metrics" in result

    def test_detect_code_smells_long_function(self, analyzer, tmp_path):
        """Test detecting long function code smell."""
        test_file = tmp_path / "long_func.py"
        long_function = "def long_function():\n" + "    pass\n" * 50  # 50 lines

        smells = analyzer.detect_code_smells(long_function, test_file, ["long_functions"])

        # Should detect long function
        assert len(smells) > 0
        assert any("long" in str(smell).lower() for smell in smells)

    def test_detect_code_smells_complexity(self, analyzer, tmp_path):
        """Test detecting complexity code smells."""
        test_file = tmp_path / "complex.py"
        complex_code = """
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                for i in range(10):
                    if i % 2 == 0:
                        if i > 5:
                            return True
    return False
"""

        smells = analyzer.detect_code_smells(complex_code, test_file, ["complex_conditionals"])

        # Should detect complexity issues
        assert isinstance(smells, list)


class TestJavaScriptAnalyzer:
    """Test JavaScriptAnalyzer class."""

    @pytest.fixture
    def analyzer(self, tmp_path):
        """Create JavaScriptAnalyzer instance."""
        return JavaScriptAnalyzer(tmp_path)

    def test_get_file_extensions(self, analyzer):
        """Test supported file extensions."""
        extensions = analyzer.get_file_extensions()

        expected_extensions = [".js", ".jsx", ".mjs", ".cjs"]
        assert extensions == expected_extensions

    def test_supports_file(self, analyzer, tmp_path):
        """Test file support detection."""
        test_cases = [
            ("test.js", True),
            ("test.jsx", True),
            ("test.mjs", True),
            ("test.cjs", True),
            ("test.JS", True),  # Case insensitive
            ("test.py", False),
            ("test.ts", False),
        ]

        for filename, expected in test_cases:
            file_path = tmp_path / filename
            assert analyzer.supports_file(file_path) == expected

    @pytest.mark.asyncio
    async def test_analyze_file_simple_javascript(self, analyzer, tmp_path):
        """Test analyzing simple JavaScript file."""
        test_file = tmp_path / "simple.js"
        test_content = """
function helloWorld() {
    console.log("Hello, World!");
    return true;
}

const arrow = () => {
    return "arrow function";
};

class MyClass {
    constructor() {
        this.value = 42;
    }
}

export { helloWorld, arrow, MyClass };
"""
        test_file.write_text(test_content)

        result = await analyzer.analyze_file(test_file)

        assert result["file"] == "simple.js"
        assert result["quality_score"] >= 0
        assert "metrics" in result

    @pytest.mark.asyncio
    async def test_analyze_file_react_jsx(self, analyzer, tmp_path):
        """Test analyzing React JSX file."""
        test_file = tmp_path / "component.jsx"
        test_content = """
import React from 'react';

const HelloComponent = ({ name }) => {
    return (
        <div className="hello">
            <h1>Hello, {name}!</h1>
        </div>
    );
};

export default HelloComponent;
"""
        test_file.write_text(test_content)

        result = await analyzer.analyze_file(test_file)

        assert result["file"] == "component.jsx"
        assert result["quality_score"] >= 0

    def test_detect_code_smells_long_function(self, analyzer, tmp_path):
        """Test detecting long function in JavaScript."""
        test_file = tmp_path / "long.js"
        long_function = "function longFunction() {\n" + "    console.log('line');\n" * 50 + "}"

        smells = analyzer.detect_code_smells(long_function, test_file, ["long_functions"])

        assert isinstance(smells, list)


class TestTypeScriptAnalyzer:
    """Test TypeScriptAnalyzer class."""

    @pytest.fixture
    def analyzer(self, tmp_path):
        """Create TypeScriptAnalyzer instance."""
        return TypeScriptAnalyzer(tmp_path)

    def test_get_file_extensions(self, analyzer):
        """Test supported file extensions."""
        extensions = analyzer.get_file_extensions()

        expected_extensions = [".ts", ".tsx"]
        assert extensions == expected_extensions

    def test_supports_file(self, analyzer, tmp_path):
        """Test file support detection."""
        test_cases = [
            ("test.ts", True),
            ("test.tsx", True),
            ("test.TS", True),  # Case insensitive
            ("test.js", False),
            ("test.py", False),
        ]

        for filename, expected in test_cases:
            file_path = tmp_path / filename
            assert analyzer.supports_file(file_path) == expected

    @pytest.mark.asyncio
    async def test_analyze_file_simple_typescript(self, analyzer, tmp_path):
        """Test analyzing simple TypeScript file."""
        test_file = tmp_path / "simple.ts"
        test_content = """
interface User {
    name: string;
    age: number;
}

function greetUser(user: User): string {
    return `Hello, ${user.name}! You are ${user.age} years old.`;
}

class UserManager {
    private users: User[] = [];

    addUser(user: User): void {
        this.users.push(user);
    }

    getUsers(): User[] {
        return this.users;
    }
}

export { User, greetUser, UserManager };
"""
        test_file.write_text(test_content)

        result = await analyzer.analyze_file(test_file)

        assert result["file"] == "simple.ts"
        assert result["quality_score"] >= 0
        assert "metrics" in result

    @pytest.mark.asyncio
    async def test_analyze_file_react_tsx(self, analyzer, tmp_path):
        """Test analyzing React TypeScript file."""
        test_file = tmp_path / "component.tsx"
        test_content = """
import React from 'react';

interface Props {
    name: string;
    age?: number;
}

const UserComponent: React.FC<Props> = ({ name, age = 0 }) => {
    return (
        <div>
            <h1>{name}</h1>
            {age > 0 && <p>Age: {age}</p>}
        </div>
    );
};

export default UserComponent;
"""
        test_file.write_text(test_content)

        result = await analyzer.analyze_file(test_file)

        assert result["file"] == "component.tsx"
        assert result["quality_score"] >= 0

    def test_detect_code_smells(self, analyzer, tmp_path):
        """Test code smell detection for TypeScript."""
        test_file = tmp_path / "test.ts"
        test_content = "const x = 1; const y = 2;"

        smells = analyzer.detect_code_smells(test_content, test_file, ["duplicate_code"])

        assert isinstance(smells, list)


class TestGenericAnalyzer:
    """Test GenericAnalyzer class."""

    @pytest.fixture
    def analyzer(self, tmp_path):
        """Create GenericAnalyzer instance."""
        return GenericAnalyzer(tmp_path)

    def test_get_file_extensions(self, analyzer):
        """Test supported file extensions."""
        extensions = analyzer.get_file_extensions()

        # GenericAnalyzer should support all files
        assert "*" in extensions or len(extensions) > 10

    def test_supports_file(self, analyzer, tmp_path):
        """Test file support detection."""
        # GenericAnalyzer should support all files
        test_files = [
            "test.py",
            "test.js",
            "test.ts",
            "test.java",
            "test.cpp",
            "test.go",
            "test.rs",
            "test.rb",
            "test.php",
            "test.txt",
            "README",
            "Makefile",
            "config.json",
        ]

        for filename in test_files:
            file_path = tmp_path / filename
            assert analyzer.supports_file(file_path) is True

    @pytest.mark.asyncio
    async def test_analyze_file_unknown_extension(self, analyzer, tmp_path):
        """Test analyzing file with unknown extension."""
        test_file = tmp_path / "config.conf"
        test_content = """
# Configuration file
server.host = localhost
server.port = 8080
debug.enabled = true

[database]
host = db.example.com
port = 5432
"""
        test_file.write_text(test_content)

        result = await analyzer.analyze_file(test_file)

        assert result["file"] == "config.conf"
        assert result["quality_score"] >= 0
        assert "metrics" in result

    @pytest.mark.asyncio
    async def test_analyze_file_text_file(self, analyzer, tmp_path):
        """Test analyzing plain text file."""
        test_file = tmp_path / "document.txt"
        test_content = """
This is a plain text document.
It contains multiple lines of text.
Some lines are longer than others.

There are also empty lines above.
"""
        test_file.write_text(test_content)

        result = await analyzer.analyze_file(test_file)

        assert result["file"] == "document.txt"
        assert result["quality_score"] >= 0

    @pytest.mark.asyncio
    async def test_analyze_file_empty_file(self, analyzer, tmp_path):
        """Test analyzing empty file."""
        test_file = tmp_path / "empty.dat"
        test_file.write_text("")

        result = await analyzer.analyze_file(test_file)

        assert result["file"] == "empty.dat"
        assert result["quality_score"] >= 0

    def test_detect_code_smells_generic(self, analyzer, tmp_path):
        """Test generic code smell detection."""
        test_file = tmp_path / "test.unknown"
        test_content = "Some generic content\nwith multiple lines\nfor testing"

        smells = analyzer.detect_code_smells(test_content, test_file, ["duplicate_code"])

        assert isinstance(smells, list)


class TestLanguageAnalyzerIntegration:
    """Integration tests for language analyzers."""

    @pytest.mark.asyncio
    async def test_all_analyzers_handle_empty_files(self, tmp_path):
        """Test all analyzers handle empty files gracefully."""
        analyzers = [
            PythonAnalyzer(tmp_path),
            JavaScriptAnalyzer(tmp_path),
            TypeScriptAnalyzer(tmp_path),
            GenericAnalyzer(tmp_path),
        ]

        extensions = [".py", ".js", ".ts", ".txt"]

        for analyzer, ext in zip(analyzers, extensions):
            empty_file = tmp_path / f"empty{ext}"
            empty_file.write_text("")

            result = await analyzer.analyze_file(empty_file)

            assert "file" in result
            assert "quality_score" in result
            assert result["quality_score"] >= 0

    @pytest.mark.asyncio
    async def test_all_analyzers_handle_binary_files(self, tmp_path):
        """Test all analyzers handle binary files gracefully."""
        analyzers = [
            PythonAnalyzer(tmp_path),
            JavaScriptAnalyzer(tmp_path),
            TypeScriptAnalyzer(tmp_path),
            GenericAnalyzer(tmp_path),
        ]

        extensions = [".py", ".js", ".ts", ".bin"]

        for analyzer, ext in zip(analyzers, extensions):
            binary_file = tmp_path / f"binary{ext}"
            binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")

            # Should handle binary content gracefully
            result = await analyzer.analyze_file(binary_file)

            assert "file" in result
            assert "quality_score" in result

    def test_all_analyzers_support_correct_extensions(self, tmp_path):
        """Test all analyzers support their declared extensions."""
        test_cases = [
            (PythonAnalyzer(tmp_path), [".py", ".pyw", ".pyi"]),
            (JavaScriptAnalyzer(tmp_path), [".js", ".jsx", ".mjs", ".cjs"]),
            (TypeScriptAnalyzer(tmp_path), [".ts", ".tsx"]),
        ]

        for analyzer, expected_extensions in test_cases:
            declared_extensions = analyzer.get_file_extensions()
            assert declared_extensions == expected_extensions

            # Test that analyzer supports its declared extensions
            for ext in expected_extensions:
                test_file = tmp_path / f"test{ext}"
                assert analyzer.supports_file(test_file) is True

    def test_analyzer_inheritance_and_interfaces(self, tmp_path):
        """Test that all analyzers properly inherit from BaseAnalyzer."""
        from coder_mcp.analysis.base_analyzer import BaseAnalyzer

        analyzers = [
            PythonAnalyzer(tmp_path),
            JavaScriptAnalyzer(tmp_path),
            TypeScriptAnalyzer(tmp_path),
            GenericAnalyzer(tmp_path),
        ]

        for analyzer in analyzers:
            # Should inherit from BaseAnalyzer
            assert isinstance(analyzer, BaseAnalyzer)

            # Should have required methods
            assert hasattr(analyzer, "analyze_file")
            assert hasattr(analyzer, "get_file_extensions")
            assert hasattr(analyzer, "detect_code_smells")
            assert hasattr(analyzer, "supports_file")

    @pytest.mark.asyncio
    async def test_error_handling_consistency(self, tmp_path):
        """Test that all analyzers handle errors consistently."""
        analyzers = [
            PythonAnalyzer(tmp_path),
            JavaScriptAnalyzer(tmp_path),
            TypeScriptAnalyzer(tmp_path),
            GenericAnalyzer(tmp_path),
        ]

        # Test non-existent file
        nonexistent = tmp_path / "nonexistent.file"

        for analyzer in analyzers:
            try:
                result = await analyzer.analyze_file(nonexistent)
                # If no exception, should return reasonable result
                assert isinstance(result, dict)
                assert "file" in result
            except Exception as e:
                # If exception, should be reasonable type
                assert isinstance(e, (FileNotFoundError, IOError, OSError))


class TestLanguageAnalyzerEdgeCases:
    """Test edge cases for language analyzers."""

    def test_very_large_files(self, tmp_path):
        """Test handling of very large files."""
        large_content = "# Large file\n" + "print('line')\n" * 10000
        large_file = tmp_path / "large.py"
        large_file.write_text(large_content)

        analyzer = PythonAnalyzer(tmp_path)

        # Should handle large files without crashing
        smells = analyzer.detect_code_smells(large_content, large_file, ["long_functions"])
        assert isinstance(smells, list)

    def test_unicode_content(self, tmp_path):
        """Test handling of Unicode content."""
        unicode_content = '''
# -*- coding: utf-8 -*-
def hello_мир():
    """Функция приветствия мира 🌍"""
    print("Привет, мир! 你好世界！ مرحبا بالعالم!")
    return "🎉"

класс = "тест"
'''
        unicode_file = tmp_path / "unicode.py"
        unicode_file.write_text(unicode_content, encoding="utf-8")

        analyzer = PythonAnalyzer(tmp_path)
        smells = analyzer.detect_code_smells(unicode_content, unicode_file, ["duplicate_code"])
        assert isinstance(smells, list)

    def test_mixed_line_endings(self, tmp_path):
        """Test handling of mixed line endings."""
        mixed_content = "line1\nline2\r\nline3\rline4\n"
        mixed_file = tmp_path / "mixed.js"
        mixed_file.write_text(mixed_content)

        analyzer = JavaScriptAnalyzer(tmp_path)
        smells = analyzer.detect_code_smells(mixed_content, mixed_file, ["duplicate_code"])
        assert isinstance(smells, list)
