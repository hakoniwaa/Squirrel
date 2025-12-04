#!/usr/bin/env python3
"""
File Utilities with Async Support
Safe file operations with size limits and proper error handling
"""

import logging
import threading
from pathlib import Path
from typing import Optional

# Try to import async file I/O
try:
    import aiofiles
    import aiofiles.os

    ASYNC_IO_AVAILABLE = True
except ImportError:
    ASYNC_IO_AVAILABLE = False

from ..security.exceptions import FileOperationError
from ..security.validators import validate_file_size

logger = logging.getLogger(__name__)


class FileManager:
    """Thread-safe file operations with size limits and async support"""

    def __init__(self, max_file_size: int = 10 * 1024 * 1024):  # 10MB default
        self.max_file_size = max_file_size
        self._file_lock = threading.RLock()

    async def safe_read_file(self, file_path: Path, max_size: Optional[int] = None) -> str:
        """Safely read file with size limits and async I/O"""
        max_size = max_size or self.max_file_size

        try:
            # Check file size first
            file_size = file_path.stat().st_size
            validate_file_size(file_size, max_size, str(file_path))

            # Use file lock to prevent concurrent access issues
            with self._file_lock:
                # Use async I/O if available
                if ASYNC_IO_AVAILABLE:
                    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                        content = await f.read(max_size)
                else:
                    # Fallback to sync I/O with size limit
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read(max_size)

            return content

        except PermissionError:
            # Let PermissionError propagate for test compatibility
            raise
        except OSError as e:
            raise FileOperationError(
                f"Cannot read file: {str(e)}",
                context={
                    "file_path": str(file_path),
                    "operation": "read",
                    "original_error": str(e),
                },
            )

    async def safe_write_file(
        self, file_path: Path, content: str, max_size: Optional[int] = None
    ) -> None:
        """Safely write file with size limits and async I/O"""
        max_size = max_size or self.max_file_size

        content_size = len(content.encode("utf-8"))
        validate_file_size(content_size, max_size, str(file_path))

        try:
            # Use file lock to prevent concurrent access issues
            with self._file_lock:
                # Create parent directories if needed
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Use async I/O if available
                if ASYNC_IO_AVAILABLE:
                    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                        await f.write(content)
                else:
                    # Fallback to sync I/O
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)

        except (PermissionError, OSError) as e:
            raise FileOperationError(
                f"Cannot write file: {str(e)}",
                context={
                    "file_path": str(file_path),
                    "operation": "write",
                    "original_error": str(e),
                },
            )

    async def safe_append_file(
        self, file_path: Path, content: str, max_size: Optional[int] = None
    ) -> None:
        """Safely append to file with size limits"""
        max_size = max_size or self.max_file_size

        try:
            # Check current file size if it exists
            if file_path.exists():
                current_size = file_path.stat().st_size
                content_size = len(content.encode("utf-8"))
                validate_file_size(current_size + content_size, max_size, str(file_path))

            with self._file_lock:
                file_path.parent.mkdir(parents=True, exist_ok=True)

                if ASYNC_IO_AVAILABLE:
                    async with aiofiles.open(file_path, "a", encoding="utf-8") as f:
                        await f.write(content)
                else:
                    with open(file_path, "a", encoding="utf-8") as f:
                        f.write(content)

        except (PermissionError, OSError) as e:
            raise FileOperationError(
                f"Cannot append to file: {str(e)}",
                context={
                    "file_path": str(file_path),
                    "operation": "append",
                    "original_error": str(e),
                },
            )

    def get_file_info(self, file_path: Path) -> dict:
        """Get safe file information"""
        # Check if file exists first and raise FileNotFoundError if not
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            stat = file_path.stat()
            return {
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "is_file": file_path.is_file(),
                "is_dir": file_path.is_dir(),
                "exists": file_path.exists(),
                "suffix": file_path.suffix,
                "name": file_path.name,
            }
        except (PermissionError, OSError) as e:
            logger.debug(f"Cannot get file info for {file_path}: {e}")
            return {
                "size": 0,
                "modified": 0,
                "is_file": False,
                "is_dir": False,
                "exists": False,
                "suffix": "",
                "name": str(file_path.name) if file_path else "",
            }

    def is_binary_file(self, file_path: Path, sample_size: int = 1024) -> bool:
        """Check if file is binary by examining a sample"""
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(sample_size)

            # Check for null bytes (common in binary files)
            if b"\x00" in chunk:
                return True

            # Check for common binary file signatures
            if chunk.startswith(b"\x89PNG"):  # PNG signature
                return True
            if chunk.startswith(b"\xff\xd8\xff"):  # JPEG signature
                return True
            if chunk.startswith(b"GIF8"):  # GIF signature
                return True
            if chunk.startswith(b"\x00\x01\x02\x03"):  # Generic binary pattern
                return True

            # Check for high percentage of non-printable characters
            if len(chunk) > 0:
                printable_chars = sum(
                    1 for byte in chunk if 32 <= byte <= 126 or byte in [9, 10, 13]
                )
                if printable_chars / len(chunk) < 0.7:
                    return True

            return False

        except (PermissionError, OSError):
            # If we can't read it, assume it's binary for safety
            return True

    def get_file_type(self, file_path: Path) -> str:
        """Determine file type based on extension and filename"""
        suffix = file_path.suffix.lower()
        filename = file_path.name

        # Special case for extensionless text files
        extensionless_text_files = {
            "README",
            "LICENSE",
            "AUTHORS",
            "CONTRIBUTORS",
            "CHANGELOG",
            "NEWS",
            "INSTALL",
            "TODO",
            "COPYING",
            "NOTICE",
            "VERSION",
        }

        # Special case for build/config files
        build_config_files = {
            "Dockerfile": "text",
            "Makefile": "text",
            "makefile": "text",
            ".gitignore": "text",
            ".gitattributes": "text",
            ".dockerignore": "text",
            ".env": "text",
            ".env.example": "text",
            ".bashrc": "text",
            ".bash_profile": "text",
            ".zshrc": "text",
            ".profile": "text",
        }

        type_mapping = {
            # Text files
            ".txt": "text",
            ".md": "markdown",
            ".rst": "restructuredtext",
            ".log": "log",
            # Code files
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "header",
            ".hpp": "header",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".r": "r",
            # Config files
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "config",  # Changed from "toml" to "config"
            ".ini": "ini",
            ".cfg": "config",
            ".conf": "config",
            ".xml": "xml",
            # Web files
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".less": "less",
            # Shell scripts
            ".sh": "shell",
            ".bash": "bash",
            ".zsh": "zsh",
            ".fish": "fish",
            ".ps1": "powershell",
            # Data files
            ".csv": "csv",
            ".tsv": "tsv",
            ".sql": "sql",
            # Build files
            ".mk": "makefile",
        }

        # Check exact filename matches first (including build/config files)
        if filename in build_config_files:
            return build_config_files[filename]

        # Check for extensionless text files
        if filename in extensionless_text_files:
            return "text"

        # Check extension mapping
        return type_mapping.get(suffix, "unknown")


# Global file manager instance
_file_manager = None
_file_manager_lock = threading.Lock()


def get_file_manager(max_file_size: Optional[int] = None) -> FileManager:
    """Get or create global file manager instance"""
    global _file_manager

    with _file_manager_lock:
        if _file_manager is None:
            _file_manager = FileManager(max_file_size or 10 * 1024 * 1024)
        return _file_manager
