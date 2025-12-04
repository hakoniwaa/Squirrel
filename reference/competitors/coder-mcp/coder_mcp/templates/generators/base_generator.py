#!/usr/bin/env python3
"""
Base Template Generator
Common functionality for all language-specific generators
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class BaseTemplateGenerator(ABC):
    """Base class for all template generators"""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.language = self.get_language_name()

    @abstractmethod
    def get_language_name(self) -> str:
        """Return the language name this generator handles"""

    @abstractmethod
    def get_file_extension(self) -> str:
        """Return the primary file extension for this language"""

    @abstractmethod
    def get_test_framework(self) -> str:
        """Return the default test framework for this language"""

    @abstractmethod
    def get_package_manager(self) -> str:
        """Return the package manager for this language"""

    def generate_file_header(self, title: str, description: str = "") -> str:
        """Generate a standard file header with timestamp"""
        timestamp = datetime.now().isoformat()
        comment_char = self.get_comment_char()

        header = f"{comment_char}\n"
        header += f"{comment_char} {title}\n"
        if description:
            header += f"{comment_char} {description}\n"
        header += f"{comment_char} Generated on {timestamp}\n"
        header += f"{comment_char}\n\n"

        return header

    def get_comment_char(self) -> str:
        """Get the comment character for this language"""
        if self.language in ["python"]:
            return '"""'
        elif self.language in ["javascript", "typescript"]:
            return "/**"
        else:
            return "#"

    def ensure_directory(self, file_path: Path) -> None:
        """Ensure the directory for a file exists"""
        file_path.parent.mkdir(parents=True, exist_ok=True)

    def write_file(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Write content to file and return file info"""
        self.ensure_directory(file_path)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "path": str(file_path.relative_to(self.workspace_root)),
            "purpose": f"Generated {self.language} file",
            "language": self.language,
            "size": len(content),
        }

    def detect_project_structure(self) -> Dict[str, Any]:
        """Detect the project structure and conventions"""
        structure = {
            "has_src_dir": (self.workspace_root / "src").exists(),
            "has_app_dir": (self.workspace_root / "app").exists(),
            "has_lib_dir": (self.workspace_root / "lib").exists(),
            "has_tests_dir": (self.workspace_root / "tests").exists(),
            "has_test_dir": (self.workspace_root / "test").exists(),
        }

        # Language-specific detection
        if self.language == "python":
            structure.update(
                {
                    "has_requirements": (self.workspace_root / "requirements.txt").exists(),
                    "has_pyproject": (self.workspace_root / "pyproject.toml").exists(),
                    "has_setup_py": (self.workspace_root / "setup.py").exists(),
                }
            )
        elif self.language in ["javascript", "typescript"]:
            structure.update(
                {
                    "has_package_json": (self.workspace_root / "package.json").exists(),
                    "has_node_modules": (self.workspace_root / "node_modules").exists(),
                }
            )

        return structure

    def get_source_directory(self) -> Path:
        """Get the main source directory for this project"""
        structure = self.detect_project_structure()

        if structure["has_src_dir"]:
            return self.workspace_root / "src"
        elif structure["has_app_dir"]:
            return self.workspace_root / "app"
        elif structure["has_lib_dir"]:
            return self.workspace_root / "lib"
        else:
            return self.workspace_root

    def get_test_directory(self) -> Path:
        """Get the test directory for this project"""
        structure = self.detect_project_structure()

        if structure["has_tests_dir"]:
            return self.workspace_root / "tests"
        elif structure["has_test_dir"]:
            return self.workspace_root / "test"
        else:
            # Create tests directory
            test_dir = self.workspace_root / "tests"
            test_dir.mkdir(exist_ok=True)
            return test_dir

    @abstractmethod
    async def generate_test_file(self, name: str, test_type: str = "unit") -> Dict[str, Any]:
        """Generate a test file for the given name"""

    @abstractmethod
    async def generate_service_class(self, name: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a service class"""

    @abstractmethod
    async def setup_testing_framework(self) -> List[str]:
        """Setup the testing framework for this language"""

    @abstractmethod
    async def setup_linting(self) -> List[str]:
        """Setup linting configuration for this language"""
