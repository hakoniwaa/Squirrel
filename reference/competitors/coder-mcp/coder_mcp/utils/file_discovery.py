import fnmatch
import pathlib
from typing import List, Set


class FileDiscovery:
    def __init__(self, workspace_root: pathlib.Path):
        self.workspace_root = workspace_root
        self.ignore_patterns = self._load_ignore_patterns()

    def _load_ignore_patterns(self) -> Set[str]:
        """Load patterns from .mcpignore file"""
        ignore_file = self.workspace_root / ".mcpignore"
        patterns = set()

        if ignore_file.exists():
            with open(ignore_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.add(line)

        # Always ignore these regardless of .mcpignore
        default_ignores = {
            ".venv/",
            "venv/",
            ".env/",
            "env/",
            "__pycache__/",
            ".git/",
            ".pytest_cache/",
            "node_modules/",
            ".mypy_cache/",
            "htmlcov/",
            ".ruff_cache/",
            ".coverage",
            "*.pyc",
        }
        patterns.update(default_ignores)
        return patterns

    def should_ignore(self, path: pathlib.Path) -> bool:
        """Check if path should be ignored"""
        relative_path = path.relative_to(self.workspace_root)
        path_str = str(relative_path)

        for pattern in self.ignore_patterns:
            # Handle directory patterns
            if pattern.endswith("/"):
                if any(part == pattern[:-1] for part in relative_path.parts):
                    return True
            # Handle file patterns
            elif fnmatch.fnmatch(path_str, pattern):
                return True

        return False

    def get_project_files(self, pattern: str = "**/*") -> List[pathlib.Path]:
        """Get all project files respecting .mcpignore"""
        files = []
        for path in self.workspace_root.glob(pattern):
            if path.is_file() and not self.should_ignore(path):
                files.append(path)
        return files

    def count_files_by_type(self) -> dict[str, int]:
        """Count files by extension"""
        counts: dict[str, int] = {}
        for file in self.get_project_files():
            ext = file.suffix or "no_extension"
            counts[ext] = counts.get(ext, 0) + 1
        return counts
