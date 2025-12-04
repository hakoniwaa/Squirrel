#!/usr/bin/env python3
"""
Templates package for MCP server
Provides modular template generation with language-specific generators
"""

from .generators.base import BaseBuilder, BaseGenerator
from .generators.python import PythonGenerator, PythonTemplates
from .registry import TemplateRegistry
from .template_engine import GeneratedCode, TemplateEngine, TemplateError, TemplateNotFound

__all__ = [
    "TemplateEngine",
    "GeneratedCode",
    "TemplateError",
    "TemplateNotFound",
    "TemplateRegistry",
    "BaseGenerator",
    "BaseBuilder",
    "PythonGenerator",
    "PythonTemplates",
]
