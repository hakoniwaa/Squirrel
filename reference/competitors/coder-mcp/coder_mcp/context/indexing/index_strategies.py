"""
Different indexing strategies for content processing
"""

import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class IndexStrategy(ABC):
    """Abstract base class for indexing strategies"""

    @abstractmethod
    async def process_content(self, content: str, file_path: Path) -> str:
        """Process content before creating embeddings"""

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the name of the strategy"""


class BasicIndexStrategy(IndexStrategy):
    """Basic indexing strategy with minimal processing"""

    def get_strategy_name(self) -> str:
        return "basic"

    async def process_content(self, content: str, file_path: Path) -> str:
        """Basic content processing - just clean and truncate"""
        # Remove excessive whitespace
        content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

        # Truncate if too long (most embedding models have limits)
        max_length = 8000  # Conservative limit for most models
        if len(content) > max_length:
            content = content[:max_length] + "...[truncated]"

        return content


class SmartIndexStrategy(IndexStrategy):
    """Smart indexing strategy with language-aware processing"""

    def get_strategy_name(self) -> str:
        return "smart"

    async def process_content(self, content: str, file_path: Path) -> str:
        """Smart content processing based on file type"""
        file_ext = file_path.suffix.lower()

        if file_ext == ".py":
            return await self._process_python_content(content)
        elif file_ext in [".js", ".ts", ".jsx", ".tsx"]:
            return await self._process_javascript_content(content)
        elif file_ext == ".md":
            return await self._process_markdown_content(content)
        elif file_ext in [".json", ".yaml", ".yml"]:
            return await self._process_data_content(content)
        else:
            # Fall back to basic processing
            return await BasicIndexStrategy().process_content(content, file_path)

    async def _process_python_content(self, content: str) -> str:
        """Process Python files with emphasis on important parts"""
        lines = content.splitlines()
        processed_lines = []
        in_docstring = False

        for line in lines:
            stripped = line.strip()

            # Skip empty lines and comments (but keep docstrings)
            if not stripped or (stripped.startswith("#") and not in_docstring):
                continue

            # Track docstrings
            if '"""' in stripped or "'''" in stripped:
                in_docstring = not in_docstring

            # Emphasize important constructs
            if any(
                stripped.startswith(keyword)
                for keyword in ["class ", "def ", "async def ", "import ", "from "]
            ):
                processed_lines.append(f"IMPORTANT: {line}")
            elif in_docstring or stripped.startswith(('"""', "'''")):
                processed_lines.append(f"DOC: {line}")
            else:
                processed_lines.append(line)

        processed_content = "\n".join(processed_lines)

        # Truncate if needed
        if len(processed_content) > 8000:
            processed_content = processed_content[:8000] + "...[truncated]"

        return processed_content

    async def _process_javascript_content(self, content: str) -> str:
        """Process JavaScript/TypeScript files"""
        lines = content.splitlines()
        processed_lines = []
        in_comment_block = False

        for line in lines:
            stripped = line.strip()

            # Skip empty lines and single-line comments
            if not stripped or stripped.startswith("//"):
                continue

            # Handle block comments
            if "/*" in stripped:
                in_comment_block = True
            if "*/" in stripped:
                in_comment_block = False
                continue
            if in_comment_block:
                continue

            # Emphasize important constructs
            if any(
                keyword in stripped
                for keyword in [
                    "function ",
                    "class ",
                    "interface ",
                    "type ",
                    "import ",
                    "export ",
                    "const ",
                    "let ",
                    "var ",
                ]
            ):
                processed_lines.append(f"IMPORTANT: {line}")
            else:
                processed_lines.append(line)

        processed_content = "\n".join(processed_lines)

        # Truncate if needed
        if len(processed_content) > 8000:
            processed_content = processed_content[:8000] + "...[truncated]"

        return processed_content

    async def _process_markdown_content(self, content: str) -> str:
        """Process Markdown files with emphasis on structure"""
        lines = content.splitlines()
        processed_lines = []

        for line in lines:
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Emphasize headings and important elements
            if stripped.startswith("#"):
                processed_lines.append(f"HEADING: {line}")
            elif stripped.startswith("```"):
                processed_lines.append(f"CODE: {line}")
            elif stripped.startswith("-") or stripped.startswith("*") or stripped.startswith("+"):
                processed_lines.append(f"LIST: {line}")
            elif stripped.startswith("[") and "](" in stripped:
                processed_lines.append(f"LINK: {line}")
            else:
                processed_lines.append(line)

        processed_content = "\n".join(processed_lines)

        # Truncate if needed
        if len(processed_content) > 8000:
            processed_content = processed_content[:8000] + "...[truncated]"

        return processed_content

    async def _process_data_content(self, content: str) -> str:
        """Process data files (JSON, YAML) with structure emphasis"""
        # For data files, we want to preserve structure but reduce size
        lines = content.splitlines()

        # If it's a small file, keep it as-is
        if len(content) < 2000:
            return content

        # For larger files, extract structure
        processed_lines = []
        brace_level = 0

        for line in lines:
            stripped = line.strip()

            # Track nesting level
            brace_level += line.count("{") + line.count("[")
            brace_level -= line.count("}") + line.count("]")

            # Keep important lines (keys, structure)
            if any(char in stripped for char in [":", "{", "}", "[", "]"]) or brace_level <= 2:
                processed_lines.append(line)
            elif len(processed_lines) < 100:  # Limit number of lines
                processed_lines.append(line)

        processed_content = "\n".join(processed_lines)

        # Truncate if needed
        if len(processed_content) > 8000:
            processed_content = processed_content[:8000] + "...[truncated]"

        return processed_content


class SummaryIndexStrategy(IndexStrategy):
    """Strategy that creates summaries of content for indexing"""

    def get_strategy_name(self) -> str:
        return "summary"

    async def process_content(self, content: str, file_path: Path) -> str:
        """Create a summary of the content for indexing"""
        file_ext = file_path.suffix.lower()

        # Extract key information based on file type
        if file_ext == ".py":
            summary = await self._summarize_python_file(content, file_path)
        elif file_ext in [".js", ".ts", ".jsx", ".tsx"]:
            summary = await self._summarize_javascript_file(content, file_path)
        elif file_ext == ".md":
            summary = await self._summarize_markdown_file(content, file_path)
        else:
            summary = await self._summarize_generic_file(content, file_path)

        return summary

    async def _summarize_python_file(self, content: str, file_path: Path) -> str:
        """Create a summary of a Python file"""
        lines = content.splitlines()

        imports = self._extract_imports(lines)
        classes = self._extract_classes(lines)
        functions = self._extract_functions(lines)
        docstrings = self._extract_docstrings(lines)

        summary_parts = [f"Python file: {file_path.name}", f"Lines of code: {len(lines)}"]

        if imports:
            summary_parts.append(f"Imports: {', '.join(imports[:5])}")
        if classes:
            summary_parts.append(f"Classes: {', '.join(classes)}")
        if functions:
            summary_parts.append(f"Functions: {', '.join(functions[:10])}")
        if docstrings:
            summary_parts.append(f"Documentation: {' '.join(docstrings[:3])}")

        return "\n".join(summary_parts)

    @staticmethod
    def _extract_imports(lines):
        return [line.strip() for line in lines if line.strip().startswith(("import ", "from "))]

    @staticmethod
    def _extract_classes(lines):
        classes = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("class "):
                class_name = stripped.split("(")[0].replace("class ", "").strip()
                classes.append(class_name)
        return classes

    @staticmethod
    def _extract_functions(lines):
        functions = []
        current_class = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("class "):
                current_class = stripped.split("(")[0].replace("class ", "").strip()
            elif stripped.startswith(("def ", "async def ")):
                func_name = stripped.split("(")[0].replace("def ", "").replace("async ", "").strip()
                if current_class:
                    functions.append(f"{current_class}.{func_name}")
                else:
                    functions.append(func_name)
        return functions

    @staticmethod
    def _extract_docstrings(lines):
        docstrings = []
        in_docstring = False
        docstring_start = ""
        for line in lines:
            stripped = line.strip()
            if '"""' in stripped or "'''" in stripped:
                if not in_docstring:
                    in_docstring = True
                    docstring_start = stripped
                else:
                    in_docstring = False
                    if len(docstring_start) > 10:
                        docstrings.append(docstring_start[:100] + "...")
        return docstrings

    async def _summarize_javascript_file(self, content: str, file_path: Path) -> str:
        """Create a summary of a JavaScript/TypeScript file"""
        lines = content.splitlines()

        imports = self._extract_js_imports(lines)
        exports = self._extract_js_exports(lines)
        functions = self._extract_js_functions(lines)
        classes = self._extract_js_classes(lines)

        summary_parts = [
            f"JavaScript/TypeScript file: {file_path.name}",
            f"Lines of code: {len(lines)}",
        ]

        if imports:
            summary_parts.append(f"Imports: {len(imports)} modules")
        if exports:
            summary_parts.append(f"Exports: {len(exports)} items")
        if classes:
            summary_parts.append(f"Classes: {', '.join(classes)}")
        if functions:
            summary_parts.append(f"Functions: {', '.join(functions[:10])}")

        return "\n".join(summary_parts)

    @staticmethod
    def _extract_js_imports(lines):
        return [line.strip() for line in lines if line.strip().startswith("import ")]

    @staticmethod
    def _extract_js_exports(lines):
        return [line.strip() for line in lines if line.strip().startswith("export ")]

    @staticmethod
    def _extract_js_functions(lines):
        functions = []
        for line in lines:
            stripped = line.strip()
            if "function " in stripped:
                func_name = stripped.split("function ")[1].split("(")[0].strip()
                functions.append(func_name)
            elif "=>" in stripped:
                # Arrow function, no reliable name extraction, skip or add generic
                functions.append("arrow_function")
        return functions

    @staticmethod
    def _extract_js_classes(lines):
        classes = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("class "):
                class_name = stripped.split("class ")[1].split(" ")[0].strip()
                classes.append(class_name)
        return classes

    async def _summarize_markdown_file(self, content: str, file_path: Path) -> str:
        """Create a summary of a Markdown file"""
        lines = content.splitlines()

        headings = []
        links = []
        code_blocks = 0

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("#"):
                headings.append(stripped)
            elif "[" in stripped and "](" in stripped:
                links.append(stripped)
            elif stripped.startswith("```"):
                code_blocks += 1

        summary_parts = [f"Markdown file: {file_path.name}", f"Total lines: {len(lines)}"]

        if headings:
            summary_parts.append(f"Structure: {' > '.join(headings[:5])}")
        if links:
            summary_parts.append(f"Links: {len(links)} references")
        if code_blocks > 0:
            summary_parts.append(f"Code blocks: {code_blocks // 2}")

        return "\n".join(summary_parts)

    async def _summarize_generic_file(self, content: str, file_path: Path) -> str:
        """Create a summary of a generic file"""
        lines = content.splitlines()

        summary = [
            f"File: {file_path.name}",
            f"Type: {file_path.suffix or 'no extension'}",
            f"Lines: {len(lines)}",
            f"Size: {len(content)} characters",
        ]

        # Add first few lines as preview
        preview_lines = [line.strip() for line in lines[:3] if line.strip()]
        if preview_lines:
            summary.append(f"Preview: {' | '.join(preview_lines)}")

        return "\n".join(summary)
