#!/usr/bin/env python3
"""
Markdown Processing Utilities
Handles markdown formatting and enhancement
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


class MarkdownProcessor:
    """Process and enhance markdown content"""

    @staticmethod
    def enhance_markdown(content: str) -> str:
        """Enhance markdown content with better formatting"""
        # Add proper spacing around headers
        content = re.sub(r"(\n)(#+\s)", r"\1\n\2", content)
        content = re.sub(r"(#+\s.*?)(\n)([^\n#])", r"\1\2\n\3", content)

        # Enhance code blocks with proper spacing
        content = re.sub(r"(\n)(```)", r"\1\n\2", content)
        content = re.sub(r"(```\n)([^\n])", r"\1\n\2", content)

        # Add proper list formatting
        content = re.sub(r"(\n)([*-]\s)", r"\1\n\2", content)

        return content.strip()

    @staticmethod
    def to_mcp_format(content: str) -> str:
        """Convert content to MCP-compatible format"""
        # Ensure proper emoji formatting
        content = content.replace(":checkmark:", "✅")
        content = content.replace(":warning:", "⚠️")
        content = content.replace(":information_source:", "ℹ️")
        content = content.replace(":mag:", "🔍")
        content = content.replace(":robot:", "🤖")

        return content

    @staticmethod
    def extract_sections(content: str) -> Dict[str, str]:
        """Extract sections from markdown content"""
        sections = {}
        current_section = None
        current_content: List[str] = []

        lines = content.split("\n")

        for line in lines:
            # Check for headers
            header_match = re.match(r"^(#+)\s+(.+)", line)
            if header_match:
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()

                # Start new section
                current_section = header_match.group(2).strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save the last section
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    @staticmethod
    def extract_code_examples(content: str) -> List[Dict[str, str]]:
        """Extract code examples with their descriptions"""
        examples = []

        # Find code blocks with descriptions
        pattern = r"(?:(.*?)\n)?```(\w*)\n(.*?)```"
        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            description = match.group(1).strip() if match.group(1) else ""
            language = match.group(2) or "text"
            code = match.group(3).strip()

            if "example" in description.lower() or language:
                examples.append({"description": description, "language": language, "code": code})

        return examples

    @staticmethod
    def format_table(headers: List[str], rows: List[List[str]]) -> str:
        """Format data as a markdown table"""
        if not headers or not rows:
            return ""

        # Calculate column widths
        widths = [len(header) for header in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))

        # Build table
        table_lines = []

        # Header row
        header_row = (
            "| " + " | ".join(header.ljust(widths[i]) for i, header in enumerate(headers)) + " |"
        )
        table_lines.append(header_row)

        # Separator row
        separator = "| " + " | ".join("-" * width for width in widths) + " |"
        table_lines.append(separator)

        # Data rows
        for row in rows:
            data_row = (
                "| "
                + " | ".join(
                    str(cell).ljust(widths[i]) if i < len(widths) else str(cell)
                    for i, cell in enumerate(row)
                )
                + " |"
            )
            table_lines.append(data_row)

        return "\n".join(table_lines)
