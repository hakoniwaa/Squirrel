#!/usr/bin/env python3
"""
Path Security and Validation
Enhanced path traversal prevention and workspace isolation
"""

import logging
import os
from pathlib import Path
from typing import Optional, Set

from .exceptions import ConfigurationError, SecurityError
from .validators import sanitize_path_input, validate_string_input

logger = logging.getLogger(__name__)


class PathSecurityManager:
    """Manages path security and workspace isolation"""

    # System directories that should never be accessed
    SYSTEM_DIRECTORIES = {
        "/",
        "/usr",
        "/etc",
        "/var",
        "/sys",
        "/proc",
        "/dev",
        "/System",
        "/Library",
        "/Applications",  # macOS
        "/Windows",
        "/Program Files",
        "/Program Files (x86)",  # Windows
        "/bin",
        "/sbin",
        "/boot",
        "/mnt",
        "/media",
        "/srv",
        "/opt",  # Linux
    }

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self._validate_workspace_root()

    def _validate_workspace_root(self) -> None:
        """Validate that the workspace root is reasonable and secure"""
        if not self.workspace_root:
            raise ConfigurationError("Workspace root not provided")

        # Check for exact match against system directories
        if str(self.workspace_root) in self.SYSTEM_DIRECTORIES:
            raise SecurityError(
                "Workspace root is a system directory",
                context={"workspace": str(self.workspace_root)},
            )

        # Ensure it's a directory that exists
        if not self.workspace_root.exists():
            raise ConfigurationError(
                "Workspace root does not exist", context={"workspace": str(self.workspace_root)}
            )

        if not self.workspace_root.is_dir():
            raise ConfigurationError(
                "Workspace root is not a directory", context={"workspace": str(self.workspace_root)}
            )

        # Ensure we have read permissions
        try:
            list(self.workspace_root.iterdir())
        except PermissionError as exc:
            raise SecurityError(
                "No permission to access workspace root",
                context={"workspace": str(self.workspace_root)},
            ) from exc

    def resolve_path(self, relative_path: str) -> Path:
        """Resolve path within workspace with enhanced security"""
        # Input validation
        relative_path = validate_string_input(relative_path, "path", max_length=4096)
        relative_path = sanitize_path_input(relative_path)

        path = Path(relative_path)

        # Enhanced path traversal prevention
        if ".." in path.parts:
            raise SecurityError("Path traversal not allowed", context={"path": str(path)})

        # Check for hidden directory access (except .mcp for our context)
        hidden_parts = [part for part in path.parts if part.startswith(".") and part != ".mcp"]
        if hidden_parts:
            raise SecurityError(
                "Hidden directory access not allowed",
                context={"path": str(path), "hidden_parts": hidden_parts},
            )

        if path.is_absolute():
            # If absolute, ensure it's within workspace
            try:
                resolved = path.resolve()
                workspace_resolved = self.workspace_root.resolve()
                resolved.relative_to(workspace_resolved)
                return resolved
            except (ValueError, OSError) as e:
                raise SecurityError(
                    "Absolute path must be within workspace",
                    context={
                        "path": str(path),
                        "workspace": str(self.workspace_root),
                        "original_error": str(e),
                    },
                ) from e

        # Resolve relative to workspace root
        resolved_path: Path | None = None
        try:
            resolved_path = (self.workspace_root / path).resolve()
            workspace_resolved = self.workspace_root.resolve()

            # Critical security check: ensure resolved path is within workspace
            resolved_path.relative_to(workspace_resolved)

            return resolved_path
        except (ValueError, OSError) as e:
            raise SecurityError(
                "Path must be within workspace",
                context={
                    "path": str(path),
                    "workspace": str(self.workspace_root),
                    "resolved_path": str(resolved_path) if resolved_path else None,
                    "original_error": str(e),
                },
            ) from e

    def is_safe_path(self, path: Path) -> bool:
        """Check if a path is safe to access"""
        try:
            if path.is_absolute():
                # For absolute paths, check if they're within the workspace
                try:
                    resolved = path.resolve()
                    workspace_resolved = self.workspace_root.resolve()
                    resolved.relative_to(workspace_resolved)
                    return True
                except ValueError:
                    return False
            else:
                # For relative paths, resolve through our security mechanism
                self.resolve_path(str(path))
                return True
        except (SecurityError, ValueError, OSError):
            return False

    def get_safe_file_iterator(self, pattern: str = "*", exclude_dirs: Optional[Set[str]] = None):
        """Get a safe file iterator that respects security boundaries"""
        if exclude_dirs is None:
            exclude_dirs = {
                "venv",
                "env",
                ".env",
                "virtualenv",  # Python virtual environments
                "node_modules",  # Node.js packages
                ".git",
                ".svn",
                ".hg",  # Version control
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",  # Python caches
                "dist",
                "build",
                "target",
                "out",  # Build outputs
                ".tox",
                ".nox",  # Test environments
                "coverage",
                "htmlcov",
                ".coverage",  # Coverage reports
                ".idea",
                ".vscode",
                ".vs",  # IDE directories
                "vendor",  # Vendor directories
                ".terraform",
                ".serverless",  # Infrastructure
                "tmp",
                "temp",
                ".tmp",  # Temporary directories
            }

        try:
            for path in self.workspace_root.rglob(pattern):
                if self._is_excluded_dir(path, exclude_dirs):
                    continue
                if self._is_hidden_path(path):
                    continue
                if self._is_symlink(path):
                    continue
                if self._is_accessible_file(path):
                    yield path
        except (PermissionError, OSError) as e:
            logger.debug("Permission denied accessing workspace: %s", e)
        except Exception as e:  # pylint: disable=broad-except
            # Defensive: catch all exceptions to ensure iteration does not break batch logic
            logger.error("Error iterating files in workspace: %s", e)

    def _is_excluded_dir(self, path: Path, exclude_dirs: Set[str]) -> bool:
        path_parts = set(path.parts)
        return any(excluded in path_parts for excluded in exclude_dirs)

    def _is_hidden_path(self, path: Path) -> bool:
        hidden_parts = [
            p
            for p in path.parts[len(self.workspace_root.parts) :]
            if p.startswith(".") and p != ".mcp"
        ]
        return bool(hidden_parts)

    def _is_symlink(self, path: Path) -> bool:
        try:
            return path.is_symlink()
        except (PermissionError, OSError):
            return True

    def _is_accessible_file(self, path: Path) -> bool:
        try:
            return path.is_file() and os.access(path, os.R_OK)
        except (PermissionError, OSError):
            return False


def detect_workspace_root() -> Optional[Path]:
    """Detect workspace root directory with validation"""
    current = Path.cwd()
    markers = [".git", "package.json", "pyproject.toml", "go.mod", "Cargo.toml", "requirements.txt"]

    # Check current directory first
    if any((current / marker).exists() for marker in markers):
        logger.info("Detected workspace root: %s", current)
        return current

    # Check parent directories up to a reasonable limit
    max_depth = 5  # Don't go more than 5 levels up
    for i, parent in enumerate(current.parents):
        if i >= max_depth:
            break

        if any((parent / marker).exists() for marker in markers):
            # Additional validation: make sure we're not at root or home
            if parent == Path("/") or parent == Path.home():
                continue
            return parent

    # If no markers found, use current directory
    return current
