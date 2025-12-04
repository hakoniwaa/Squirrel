#!/usr/bin/env python3
"""
AI Response Processors Package
Split into focused modules for better maintainability
"""

# Data models
from .base import CodeBlock, CodeChange, ProcessedResponse, TestCase
from .change_processor import ChangeExtractor, DiffProcessor
from .code_processor import CodeExtractor, SyntaxValidator
from .markdown_processor import MarkdownProcessor

# Main processors
from .response_builder import ResponseProcessor

__all__ = [
    # Data models
    "CodeBlock",
    "CodeChange",
    "TestCase",
    "ProcessedResponse",
    # Main processors
    "ResponseProcessor",
    "CodeExtractor",
    "SyntaxValidator",
    "ChangeExtractor",
    "DiffProcessor",
    "MarkdownProcessor",
]
