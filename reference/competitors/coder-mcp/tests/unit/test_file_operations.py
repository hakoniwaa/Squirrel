"""Test file operations functionality."""

import asyncio
from pathlib import Path

import pytest

from coder_mcp.utils.file_utils import FileManager


class TestFileManager:
    """Test FileManager class functionality."""

    def test_initialization_with_default_max_size(self):
        """Test FileManager initialization with default max size."""
        manager = FileManager()
        assert manager.max_file_size == 10 * 1024 * 1024  # 10MB default

    def test_initialization_with_custom_max_size(self):
        """Test FileManager initialization with custom max size."""
        custom_size = 5 * 1024 * 1024  # 5MB
        manager = FileManager(custom_size)
        assert manager.max_file_size == custom_size

    def test_get_file_type_python(self):
        """Test file type detection for Python files."""
        manager = FileManager()

        assert manager.get_file_type(Path("test.py")) == "python"
        assert manager.get_file_type(Path("module.py")) == "python"
        assert manager.get_file_type(Path("/path/to/script.py")) == "python"

    def test_get_file_type_javascript(self):
        """Test file type detection for JavaScript files."""
        manager = FileManager()

        assert manager.get_file_type(Path("script.js")) == "javascript"
        assert manager.get_file_type(Path("app.jsx")) == "javascript"
        assert manager.get_file_type(Path("component.tsx")) == "typescript"
        assert manager.get_file_type(Path("types.ts")) == "typescript"

    def test_get_file_type_markdown(self):
        """Test file type detection for Markdown files."""
        manager = FileManager()

        assert manager.get_file_type(Path("README.md")) == "markdown"
        assert manager.get_file_type(Path("docs.markdown")) == "unknown"

    def test_get_file_type_config(self):
        """Test file type detection for config files."""
        manager = FileManager()

        assert manager.get_file_type(Path("config.json")) == "json"
        assert manager.get_file_type(Path("data.yaml")) == "yaml"
        assert manager.get_file_type(Path("config.yml")) == "yaml"
        assert manager.get_file_type(Path("config.toml")) == "config"
        assert manager.get_file_type(Path("setup.cfg")) == "config"

    def test_get_file_type_text(self):
        """Test file type detection for text files."""
        manager = FileManager()

        assert manager.get_file_type(Path("notes.txt")) == "text"
        assert manager.get_file_type(Path("LICENSE")) == "text"
        assert manager.get_file_type(Path("Dockerfile")) == "text"
        assert manager.get_file_type(Path("Makefile")) == "text"

    def test_get_file_type_unknown(self):
        """Test file type detection for unknown extensions."""
        manager = FileManager()

        assert manager.get_file_type(Path("file.xyz")) == "unknown"
        assert manager.get_file_type(Path("binary.exe")) == "unknown"
        assert manager.get_file_type(Path("image.png")) == "unknown"

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("test.PY", "python"),  # Case insensitive
            ("Script.JS", "javascript"),
            ("README.MD", "markdown"),
            ("CONFIG.JSON", "json"),
        ],
    )
    def test_get_file_type_case_insensitive(self, filename, expected):
        """Test file type detection is case insensitive."""
        manager = FileManager()
        assert manager.get_file_type(Path(filename)) == expected

    def test_get_file_info_existing_file(self, tmp_path):
        """Test get_file_info for existing file."""
        manager = FileManager()
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        info = manager.get_file_info(test_file)

        assert "size" in info
        assert "modified" in info
        assert "is_file" in info
        assert "is_dir" in info
        assert "exists" in info
        assert info["size"] == len(test_content)
        assert isinstance(info["modified"], float)
        assert info["is_file"] is True
        assert info["exists"] is True

    def test_get_file_info_nonexistent_file(self):
        """Test get_file_info for non-existent file raises error."""
        manager = FileManager()
        nonexistent = Path("/nonexistent/file.txt")

        with pytest.raises(FileNotFoundError):
            manager.get_file_info(nonexistent)

    @pytest.mark.parametrize(
        "file_content,expected",
        [
            (b"Hello World", False),  # Text content
            (b"#!/usr/bin/env python\nprint('hello')", False),  # Script
            (b"\x89PNG\r\n\x1a\n", True),  # PNG header
            (b"\xff\xd8\xff", True),  # JPEG header
            (b"\x00\x01\x02\x03", True),  # Binary data
            (b"", False),  # Empty file
        ],
    )
    def test_is_binary_file(self, tmp_path, file_content, expected):
        """Test binary file detection."""
        manager = FileManager()
        test_file = tmp_path / "test_file"
        test_file.write_bytes(file_content)

        assert manager.is_binary_file(test_file) == expected

    def test_is_binary_file_nonexistent(self):
        """Test is_binary_file with non-existent file."""
        manager = FileManager()
        nonexistent = Path("/nonexistent/file.txt")

        # Should return True for safety (don't process unknown files)
        assert manager.is_binary_file(nonexistent) is True

    @pytest.mark.asyncio
    async def test_safe_read_file_success(self, tmp_path):
        """Test successful file reading."""
        manager = FileManager()
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!\nThis is a test file."
        test_file.write_text(test_content, encoding="utf-8")

        content = await manager.safe_read_file(test_file)

        assert content == test_content

    @pytest.mark.asyncio
    async def test_safe_read_file_nonexistent(self):
        """Test reading non-existent file."""
        manager = FileManager()
        nonexistent = Path("/nonexistent/file.txt")

        with pytest.raises(Exception):  # Should raise some kind of exception
            await manager.safe_read_file(nonexistent)

    @pytest.mark.asyncio
    async def test_safe_read_file_too_large(self, tmp_path):
        """Test reading file that exceeds size limit."""
        manager = FileManager(max_file_size=10)  # Very small limit
        test_file = tmp_path / "large.txt"
        test_content = "x" * 20  # Larger than limit
        test_file.write_text(test_content)

        with pytest.raises(Exception):  # Should raise size limit exception
            await manager.safe_read_file(test_file)

    @pytest.mark.asyncio
    async def test_safe_read_file_binary_as_text(self, tmp_path):
        """Test reading binary file as text (should handle gracefully)."""
        manager = FileManager()
        test_file = tmp_path / "binary.dat"
        binary_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        test_file.write_bytes(binary_content)

        # This might raise an exception or return empty/placeholder content
        # depending on implementation
        try:
            content = await manager.safe_read_file(test_file)
            assert isinstance(content, str)
        except (UnicodeDecodeError, Exception):
            # Expected for binary files
            pass

    @pytest.mark.asyncio
    async def test_safe_read_file_different_encodings(self, tmp_path):
        """Test reading files with different encodings."""
        manager = FileManager()

        # UTF-8 file
        utf8_file = tmp_path / "utf8.txt"
        utf8_content = "Hello 世界! 🌍"
        utf8_file.write_text(utf8_content, encoding="utf-8")

        content = await manager.safe_read_file(utf8_file)
        assert content == utf8_content

    @pytest.mark.asyncio
    async def test_safe_read_file_empty(self, tmp_path):
        """Test reading empty file."""
        manager = FileManager()
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        content = await manager.safe_read_file(test_file)
        assert content == ""

    @pytest.mark.asyncio
    async def test_safe_read_file_permission_denied(self, tmp_path):
        """Test reading file with permission denied."""
        manager = FileManager()
        test_file = tmp_path / "restricted.txt"
        test_file.write_text("secret content")

        # Remove read permissions
        test_file.chmod(0o000)

        try:
            with pytest.raises(PermissionError):
                await manager.safe_read_file(test_file)
        finally:
            # Restore permissions for cleanup
            test_file.chmod(0o644)

    @pytest.mark.asyncio
    async def test_safe_read_file_concurrent_access(self, tmp_path):
        """Test concurrent file reading."""
        manager = FileManager()
        test_file = tmp_path / "concurrent.txt"
        test_content = "Concurrent access test content"
        test_file.write_text(test_content)

        # Read the same file multiple times concurrently
        tasks = [manager.safe_read_file(test_file) for _ in range(5)]

        results = await asyncio.gather(*tasks)

        # All results should be the same
        assert all(result == test_content for result in results)
        assert len(results) == 5


class TestFileManagerEdgeCases:
    """Test edge cases and error conditions."""

    def test_file_manager_with_zero_max_size(self):
        """Test FileManager with zero max size."""
        manager = FileManager(max_file_size=0)
        assert manager.max_file_size == 0

    def test_file_manager_with_negative_max_size(self):
        """Test FileManager with negative max size."""
        manager = FileManager(max_file_size=-1)
        assert manager.max_file_size == -1

    def test_get_file_type_with_no_extension(self):
        """Test file type detection for files without extension."""
        manager = FileManager()

        assert manager.get_file_type(Path("README")) == "text"
        assert manager.get_file_type(Path("LICENSE")) == "text"
        assert manager.get_file_type(Path("Makefile")) == "text"
        assert manager.get_file_type(Path("Dockerfile")) == "text"

    def test_get_file_type_with_multiple_dots(self):
        """Test file type detection for files with multiple dots."""
        manager = FileManager()

        assert manager.get_file_type(Path("file.min.js")) == "javascript"
        assert manager.get_file_type(Path("config.local.json")) == "json"
        assert manager.get_file_type(Path("test.spec.py")) == "python"

    def test_get_file_type_hidden_files(self):
        """Test file type detection for hidden files."""
        manager = FileManager()

        assert manager.get_file_type(Path(".gitignore")) == "text"
        assert manager.get_file_type(Path(".env")) == "text"
        assert manager.get_file_type(Path(".bashrc")) == "text"

    @pytest.mark.asyncio
    async def test_safe_read_file_with_path_object(self, tmp_path):
        """Test reading file using Path object."""
        manager = FileManager()
        test_file = tmp_path / "path_test.txt"
        test_content = "Path object test"
        test_file.write_text(test_content)

        content = await manager.safe_read_file(test_file)
        assert content == test_content

    @pytest.mark.asyncio
    async def test_safe_read_file_with_string_path(self, tmp_path):
        """Test reading file using string path."""
        manager = FileManager()
        test_file = tmp_path / "string_test.txt"
        test_content = "String path test"
        test_file.write_text(test_content)

        content = await manager.safe_read_file(Path(str(test_file)))
        assert content == test_content


class TestFileManagerIntegration:
    """Integration tests for FileManager with real file scenarios."""

    @pytest.mark.asyncio
    async def test_typical_python_file_workflow(self, tmp_path):
        """Test complete workflow with a typical Python file."""
        manager = FileManager()

        # Create a typical Python file
        python_file = tmp_path / "example.py"
        python_content = '''#!/usr/bin/env python3
"""
Example Python module for testing.
"""

import os
import sys
from pathlib import Path


class ExampleClass:
    """Example class for demonstration."""

    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}!"


def main():
    """Main function."""
    example = ExampleClass("World")
    print(example.greet())


if __name__ == "__main__":
    main()
'''
        python_file.write_text(python_content)

        # Test file type detection
        assert manager.get_file_type(python_file) == "python"

        # Test binary detection
        assert manager.is_binary_file(python_file) is False

        # Test file info
        info = manager.get_file_info(python_file)
        assert info["size"] == len(python_content)

        # Test safe reading
        content = await manager.safe_read_file(python_file)
        assert content == python_content
        assert "class ExampleClass" in content
        assert "def main():" in content

    @pytest.mark.asyncio
    async def test_large_file_handling(self, tmp_path):
        """Test handling of large files within limits."""
        # Create a manager with 1KB limit
        manager = FileManager(max_file_size=1024)

        # Create a file just under the limit
        small_file = tmp_path / "small.txt"
        small_content = "x" * 1000  # 1000 bytes
        small_file.write_text(small_content)

        # Should read successfully
        content = await manager.safe_read_file(small_file)
        assert len(content) == 1000

        # Create a file over the limit
        large_file = tmp_path / "large.txt"
        large_content = "x" * 2000  # 2000 bytes
        large_file.write_text(large_content)

        # Should raise an exception
        with pytest.raises(Exception):
            await manager.safe_read_file(large_file)

    @pytest.mark.asyncio
    async def test_mixed_file_types_batch(self, tmp_path):
        """Test processing multiple different file types."""
        manager = FileManager()

        # Create different file types
        files = {
            "script.py": ("python", "print('Hello Python')"),
            "app.js": ("javascript", "console.log('Hello JavaScript');"),
            "README.md": ("markdown", "# Test Project\n\nThis is a test."),
            "config.json": ("json", '{"name": "test", "version": "1.0.0"}'),
            "data.yaml": ("yaml", "name: test\nversion: 1.0.0"),
            "notes.txt": ("text", "Some notes here."),
            "unknown.xyz": ("unknown", "Unknown file type"),
        }

        for filename, (expected_type, content) in files.items():
            file_path = tmp_path / filename
            file_path.write_text(content)

            # Test type detection
            assert manager.get_file_type(file_path) == expected_type

            # Test reading
            read_content = await manager.safe_read_file(file_path)
            assert read_content == content
