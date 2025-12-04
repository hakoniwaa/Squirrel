#!/usr/bin/env python3
"""
Base Generator Class
Abstract base class for all language-specific generators
"""

import logging
import os
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..template_engine import GeneratedCode, TemplateEngine
from ..utils.string_utils import (
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    to_snake_case,
)

logger = logging.getLogger(__name__)


class BaseBuilder(ABC):
    """Base class for feature builders"""

    def __init__(self, template_engine: TemplateEngine):
        self.template_engine = template_engine

    @abstractmethod
    def build(self, name: str, options: Dict[str, Any]) -> GeneratedCode:
        """Build code for a specific feature"""

    def render_template(self, template_name: str, variables: Dict[str, Any]) -> str:
        """Render a template with variables"""
        return self.template_engine.render_template(template_name, variables)

    def render_string(self, template_string: str, variables: Dict[str, Any]) -> str:
        """Render a template string with variables"""
        return self.template_engine.render_string(template_string, variables)

    def get_common_variables(self, name: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Get common template variables used across builders"""
        return {
            "name": name,
            "name_snake": to_snake_case(name),
            "name_camel": to_camel_case(name),
            "name_pascal": to_pascal_case(name),
            "name_kebab": to_kebab_case(name),
            "name_lower": name.lower(),
            "name_upper": name.upper(),
            "current_year": datetime.now().year,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "options": options,
        }

    def to_snake_case(self, text: str) -> str:
        """Convert text to snake_case"""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def to_camel_case(self, text: str) -> str:
        """Convert text to camelCase"""
        components = text.replace("-", "_").split("_")
        return components[0].lower() + "".join(word.capitalize() for word in components[1:])

    def to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase"""
        components = text.replace("-", "_").split("_")
        return "".join(word.capitalize() for word in components)

    def to_kebab_case(self, text: str) -> str:
        """Convert text to kebab-case"""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", text)
        return re.sub("([a-z0-9])([A-Z])", r"\1-\2", s1).lower()


class BaseGenerator(ABC):
    """Base class for all language generators"""

    def __init__(self, template_engine: TemplateEngine, workspace_root: Path):
        self.template_engine = template_engine
        self.workspace_root = workspace_root
        self.builders = self._register_builders()
        self.logger = logger

    @abstractmethod
    def get_language_name(self) -> str:
        """Get the language name (e.g., 'python', 'javascript')"""

    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the primary file extension for this language"""

    @abstractmethod
    def _register_builders(self) -> Dict[str, BaseBuilder]:
        """Register feature builders for this language"""

    def generate(
        self, feature_type: str, name: str, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate code for a specific feature

        Args:
            feature_type: Type of feature to generate (e.g., 'class', 'function', 'test')
            name: Name of the feature
            options: Additional options for generation

        Returns:
            Dictionary with generation results
        """
        options = options or {}

        try:
            if feature_type not in self.builders:
                return {
                    "success": False,
                    "error": f"Unsupported feature type: {feature_type}. "
                    f"Supported types: {list(self.builders.keys())}",
                }

            builder = self.builders[feature_type]
            generated_code = builder.build(name, options)

            # Write file if path is specified
            files_created = []
            if generated_code.file_path:
                file_info = self.write_file(generated_code.file_path, generated_code.content)
                file_info["purpose"] = generated_code.purpose
                files_created.append(file_info)

            return {
                "success": True,
                "generated_code": generated_code.to_dict(),
                "files_created": files_created,
                "feature_type": feature_type,
                "language": self.get_language_name(),
            }

        except (IOError, ValueError) as e:
            self.logger.error("Error generating %s for %s: %s", feature_type, name, e)
            return {
                "success": False,
                "error": str(e),
                "feature_type": feature_type,
                "language": self.get_language_name(),
            }

    def get_supported_features(self) -> List[str]:
        """Get list of supported feature types"""
        return list(self.builders.keys())

    def write_file(self, file_path: Path, content: str) -> Dict[str, Any]:
        """
        Write content to a file with proper directory creation

        Args:
            file_path: Path to write the file
            content: Content to write

        Returns:
            File information dictionary
        """
        try:
            if not file_path.is_absolute():
                file_path = self.workspace_root / file_path

            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())

            try:
                relative_path = file_path.relative_to(self.workspace_root)
            except ValueError:
                relative_path = Path(file_path.name)

            file_size = file_path.stat().st_size

            return {
                "file_path": str(relative_path),
                "absolute_path": str(file_path),
                "size_bytes": file_size,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "language": self.get_language_name(),
            }

        except Exception as e:
            self.logger.error("Error writing file %s: %s", file_path, e)
            raise

    def get_source_directory(self) -> Path:
        """Get the source code directory for this language"""
        language = self.get_language_name()

        # Common source directory patterns
        common_patterns = {
            "python": ["src", "app", self.workspace_root.name],
            "javascript": ["src", "lib"],
            "typescript": ["src", "lib"],
            "java": ["src/main/java"],
            "go": ["."],
            "rust": ["src"],
        }

        patterns = common_patterns.get(language, ["src"])

        for pattern in patterns:
            source_dir = self.workspace_root / pattern
            if source_dir.exists() and source_dir.is_dir():
                return source_dir

        # Default to first pattern if none exist
        return self.workspace_root / patterns[0]

    def get_test_directory(self) -> Path:
        """Get the test directory for this language"""
        language = self.get_language_name()

        # Common test directory patterns
        common_patterns = {
            "python": ["tests", "test"],
            "javascript": ["tests", "test", "__tests__"],
            "typescript": ["tests", "test", "__tests__"],
            "java": ["src/test/java"],
            "go": ["."],  # Go tests are typically in same directory
            "rust": ["tests"],
        }

        patterns = common_patterns.get(language, ["tests"])

        for pattern in patterns:
            test_dir = self.workspace_root / pattern
            if test_dir.exists() and test_dir.is_dir():
                return test_dir

        # Default to first pattern
        return self.workspace_root / patterns[0]

    def generate_file_header(self, title: str, description: str = "") -> str:
        """
        Generate a standardized file header comment

        Args:
            title: Title of the file/module
            description: Description of the file's purpose

        Returns:
            Formatted header comment
        """
        language = self.get_language_name()

        # Language-specific comment styles
        comment_styles = {
            "python": ('"""', '"""'),
            "javascript": ("/**", " */"),
            "typescript": ("/**", " */"),
            "java": ("/**", " */"),
            "go": ("/*", " */"),
            "rust": ("/*", " */"),
        }

        start_comment, end_comment = comment_styles.get(language, ("/*", " */"))

        header_lines = [start_comment, title]

        if description:
            header_lines.extend(["", description])

        header_lines.extend(
            [
                f"Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
                end_comment,
                "",
                "",
            ]
        )

        return "\n".join(header_lines)

    def validate_name(self, name: str) -> bool:
        """
        Validate that a name is suitable for code generation

        Args:
            name: Name to validate

        Returns:
            True if valid, False otherwise
        """
        if not name or not isinstance(name, str):
            return False

        # Check for basic naming conventions
        # Should start with letter or underscore, contain only alphanumeric and underscores
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
            return False

        # Language-specific reserved words check could be added here
        return True

    def get_builder(self, feature_type: str) -> Optional[BaseBuilder]:
        """Get a specific builder by feature type"""
        return self.builders.get(feature_type)

    def add_builder(self, feature_type: str, builder: BaseBuilder):
        """Add a new builder for a feature type"""
        self.builders[feature_type] = builder

    def get_generator_info(self) -> Dict[str, Any]:
        """Get information about this generator"""
        return {
            "language": self.get_language_name(),
            "file_extension": self.get_file_extension(),
            "supported_features": self.get_supported_features(),
            "source_directory": str(self.get_source_directory()),
            "test_directory": str(self.get_test_directory()),
            "builder_count": len(self.builders),
        }
