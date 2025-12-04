#!/usr/bin/env python3
"""
Core Template Engine
Handles template rendering, caching, and management for all generators
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import jinja2

from .utils.string_utils import (
    capitalize_first,
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    to_snake_case,
)

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Core template engine using Jinja2 for rendering"""

    def __init__(self, template_dirs: Optional[List[Path]] = None):
        """
        Initialize template engine

        Args:
            template_dirs: Directories to search for templates
        """
        self.template_dirs = template_dirs or []
        self._env: Optional[jinja2.Environment] = None
        self._template_cache: Dict[str, jinja2.Template] = {}
        self._setup_jinja_environment()

    def _setup_jinja_environment(self):
        """Setup Jinja2 environment with custom filters and globals"""
        # Create file system loader for template directories
        loaders = []
        for template_dir in self.template_dirs:
            if template_dir.exists():
                loaders.append(jinja2.FileSystemLoader(str(template_dir)))

        # Add a dictionary loader for inline templates
        loaders.append(jinja2.DictLoader({}))

        # Combine loaders
        loader = jinja2.ChoiceLoader(loaders) if loaders else jinja2.DictLoader({})

        self._env = jinja2.Environment(
            loader=loader,
            autoescape=jinja2.select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Add custom filters
        self._env.filters.update(
            {
                "snake_case": to_snake_case,
                "camel_case": to_camel_case,
                "pascal_case": to_pascal_case,
                "kebab_case": to_kebab_case,
                "capitalize_first": capitalize_first,
            }
        )

        # Add global functions
        self._env.globals.update(
            {
                "now": datetime.now,
                "utcnow": datetime.utcnow,
                "current_year": datetime.now().year,
            }
        )

    def render_template(self, template_name: str, variables: Dict[str, Any]) -> str:
        """
        Render a template with the given variables

        Args:
            template_name: Name of the template to render
            variables: Variables to pass to the template

        Returns:
            Rendered template content

        Raises:
            TemplateNotFound: If template doesn't exist
            TemplateError: If template rendering fails
        """
        if self._env is None:
            raise TemplateError("Jinja2 environment is not initialized.")
        try:
            template = self._env.get_template(template_name)
            return template.render(**variables)
        except jinja2.TemplateNotFound as e:
            logger.error(f"Template not found: {template_name}")
            raise TemplateNotFound(f"Template '{template_name}' not found") from e
        except jinja2.TemplateError as e:
            logger.error(f"Template rendering error in {template_name}: {e}")
            raise TemplateError(f"Error rendering template '{template_name}': {str(e)}") from e

    def render_string(self, template_string: str, variables: Dict[str, Any]) -> str:
        """
        Render a template string with the given variables

        Args:
            template_string: Template content as string
            variables: Variables to pass to the template

        Returns:
            Rendered template content
        """
        if self._env is None:
            raise TemplateError("Jinja2 environment is not initialized.")
        try:
            template = self._env.from_string(template_string)
            return template.render(**variables)
        except jinja2.TemplateError as e:
            logger.error(f"String template rendering error: {e}")
            raise TemplateError(f"Error rendering string template: {str(e)}") from e

    def add_template_dir(self, template_dir: Path):
        """Add a new template directory to the search path"""
        if template_dir not in self.template_dirs:
            self.template_dirs.append(template_dir)
            self._setup_jinja_environment()  # Recreate environment

    def register_inline_template(self, name: str, content: str):
        """Register an inline template for use"""
        if self._env is None:
            raise TemplateError("Jinja2 environment is not initialized.")
        dict_loader = None
        for loader in getattr(self._env.loader, "loaders", []):
            if isinstance(loader, jinja2.DictLoader):
                dict_loader = loader
                break

        if dict_loader:
            mapping = cast(dict, dict_loader.mapping)
            mapping[name] = content
        else:
            # Create new dict loader with the template
            new_dict_loader = jinja2.DictLoader({name: content})
            getattr(self._env.loader, "loaders", []).append(new_dict_loader)

    def list_templates(self) -> List[str]:
        """List all available templates"""
        if self._env is None:
            return []
        return self._env.list_templates()

    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists"""
        if self._env is None:
            return False
        try:
            self._env.get_template(template_name)
            return True
        except jinja2.TemplateNotFound:
            return False


class GeneratedCode:
    """Represents generated code with metadata"""

    def __init__(
        self, content: str, file_path: Optional[Path] = None, language: str = "", purpose: str = ""
    ):
        self.content = content
        self.file_path = file_path
        self.language = language
        self.purpose = purpose
        self.created_at = datetime.now(timezone.utc)

    def __str__(self) -> str:
        return self.content

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "content": self.content,
            "file_path": str(self.file_path) if self.file_path else None,
            "language": self.language,
            "purpose": self.purpose,
            "created_at": self.created_at.isoformat(),
        }


# Custom exceptions
class TemplateError(Exception):
    """Base exception for template-related errors"""


class TemplateNotFound(TemplateError):
    """Exception raised when a template is not found"""
