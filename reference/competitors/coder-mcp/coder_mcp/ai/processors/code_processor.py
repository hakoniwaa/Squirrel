#!/usr/bin/env python3
"""
Code Processing Utilities
Handles code block extraction, syntax validation, and code analysis
"""

import ast
import logging
import re
from typing import List, Optional, Tuple

from .base import CodeBlock

logger = logging.getLogger(__name__)


class CodeExtractor:
    """Extract code blocks from text responses"""

    def __init__(self):
        self._language_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "java": "java",
            "cpp": "cpp",
            "c": "c",
            "go": "go",
            "rs": "rust",
            "rb": "ruby",
            "php": "php",
            "swift": "swift",
            "kt": "kotlin",
            "scala": "scala",
            "r": "r",
            "m": "matlab",
            "jl": "julia",
            "sh": "bash",
            "ps1": "powershell",
            "yaml": "yaml",
            "yml": "yaml",
            "json": "json",
            "xml": "xml",
            "md": "markdown",
            "sql": "sql",
            "dockerfile": "dockerfile",
        }

    def extract_code_blocks(self, text: str) -> List[CodeBlock]:
        """Extract all code blocks from text"""
        code_blocks = []

        # Pattern for fenced code blocks with optional language
        pattern = r"```(\w*)\n(.*?)```"
        matches = re.finditer(pattern, text, re.DOTALL)

        for match in matches:
            language = match.group(1) or "text"
            code = match.group(2).strip()

            # Try to extract description from line before code block
            pre_text = text[: match.start()].strip().split("\n")
            description = pre_text[-1] if pre_text else None

            # Normalize language name
            language = self._normalize_language(language)

            code_blocks.append(
                CodeBlock(
                    language=language,
                    code=code,
                    description=description,
                )
            )

        # Also look for inline code that might be file paths or commands
        inline_pattern = r"`([^`]+)`"
        inline_matches = re.finditer(inline_pattern, text)

        for match in inline_matches:
            code = match.group(1)
            # Only add if it looks like code (has special characters or multiple words)
            if any(char in code for char in ["(", ")", "{", "}", "[", "]", "=", "->", "=>"]):
                code_blocks.append(
                    CodeBlock(
                        language="inline",
                        code=code,
                    )
                )

        return code_blocks

    def _normalize_language(self, language: str) -> str:
        """Normalize language identifier"""
        language = language.lower().strip()
        normalized = self._language_map.get(language, language)
        return str(normalized)

    def _extract_code_from_text(self, text: str) -> Optional[str]:
        """Extract code from text that might contain code"""
        # Look for code patterns
        code_pattern = r"`([^`]+)`"
        match = re.search(code_pattern, text)
        if match:
            return match.group(1)

        # Look for code-like patterns (contains brackets, operators, etc.)
        if any(char in text for char in ["(", ")", "{", "}", "[", "]", "=", "->", "=>"]):
            return text.strip()

        return None


class SyntaxValidator:
    """Validate code syntax for various languages"""

    @staticmethod
    async def validate_syntax(code: str, language: str) -> Tuple[bool, List[str]]:
        """Validate code syntax"""
        errors = []

        try:
            if language == "python":
                ast.parse(code)
                return True, []
            elif language in ["javascript", "typescript"]:
                # Basic validation - check for common syntax errors
                # In production, you'd use a proper parser like Babel
                if SyntaxValidator._basic_js_validation(code):
                    return True, []
                else:
                    errors.append("Basic syntax validation failed")
            else:
                # For other languages, assume valid if it compiles basic structure
                return True, []
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return False, errors

    @staticmethod
    def _basic_js_validation(code: str) -> bool:
        """Basic JavaScript validation"""
        # Check for balanced brackets
        brackets = {"(": ")", "[": "]", "{": "}"}
        stack = []

        for char in code:
            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if not stack:
                    return False
                if brackets[stack.pop()] != char:
                    return False

        return len(stack) == 0
