#!/usr/bin/env python3
"""
File operation tool handler
Handles reading, writing, listing, and searching files
"""

import asyncio
import re
from pathlib import Path
from typing import Any, Dict, List

from mcp.types import Tool

from ...security.exceptions import handle_exceptions
from ...security.validators import validate_dict_input, validate_string_input
from ..base_handler import BaseHandler


class FileHandler(BaseHandler):
    """File operation tools"""

    # Performance limits to prevent timeouts
    MAX_FILES_TO_LIST = 1000
    MAX_PROCESSING_TIME = 55  # seconds (less than 60s MCP timeout)

    @staticmethod
    def get_tools() -> List[Tool]:
        """Get file operation tools"""
        return [
            Tool(
                name="read_file",
                description="Read file contents with context awareness",
                inputSchema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            ),
            Tool(
                name="write_file",
                description="Write file and update context",
                inputSchema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                    "required": ["path", "content"],
                },
            ),
            Tool(
                name="list_files",
                description="List files in a directory (limited to 1000 files for performance)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "default": ".", "description": "Directory path"},
                        "pattern": {
                            "type": "string",
                            "default": "*",
                            "description": "File pattern (e.g., *.py)",
                        },
                    },
                },
            ),
            Tool(
                name="search_files",
                description="Search for text across multiple files",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Search pattern (regex supported)",
                        },
                        "path": {
                            "type": "string",
                            "default": ".",
                            "description": "Directory to search in",
                        },
                        "file_pattern": {
                            "type": "string",
                            "default": "*",
                            "description": "File pattern to search",
                        },
                    },
                    "required": ["pattern"],
                },
            ),
        ]

    @handle_exceptions
    async def read_file(self, args: Dict[str, Any]) -> str:
        """Read file contents with context awareness"""
        validate_dict_input(args, "read_file arguments")

        path = validate_string_input(args.get("path", ""), "path")
        file_path = self.safe_get_path(path)

        try:
            if not file_path.exists():
                return self.format_error("read_file", f"File not found: {path}")

            # Use context manager's safe file reading
            content = await self.context_manager.file_manager.safe_read_file(file_path)

            # Update context with file access
            if self.context_manager:
                await self.context_manager.track_file_access(str(file_path))

            await self.log_tool_usage("read_file", args, True)

            # Truncate very large files for display
            truncated_content = self.truncate_content(content, 3000)
            return f"📄 **File:** {path}\n```\n{truncated_content}\n```"

        except (IOError, OSError, UnicodeDecodeError, PermissionError) as e:
            await self.log_tool_usage("read_file", args, False)
            return self.format_error("read_file", f"Error reading file {path}: {str(e)}")

    @handle_exceptions
    async def write_file(self, args: Dict[str, Any]) -> str:
        """Write file and update context"""
        validate_dict_input(args, "write_file arguments")

        path = validate_string_input(args.get("path", ""), "path")
        content = validate_string_input(args.get("content", ""), "content")
        file_path = self.safe_get_path(path)

        try:
            # Create parent directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Use context manager's safe file writing
            await self.context_manager.file_manager.safe_write_file(file_path, content)

            # Update context with file change
            if self.context_manager:
                await self.context_manager.index_file(file_path)

            await self.log_tool_usage("write_file", args, True)
            return self.format_success("write_file", f"Wrote {len(content)} characters to {path}")

        except (IOError, OSError, UnicodeDecodeError, PermissionError) as e:
            await self.log_tool_usage("write_file", args, False)
            return self.format_error("write_file", f"Error writing file {path}: {str(e)}")

    @handle_exceptions
    async def list_files(self, args: Dict[str, Any]) -> str:
        """List files in a directory with performance optimizations"""
        validate_dict_input(args, "list_files arguments")

        path = args.get("path", ".")
        pattern = args.get("pattern", "*")

        try:
            dir_path = self.safe_get_path(path)
            if not dir_path.exists():
                return self.format_error("list_files", f"Directory not found: {path}")

            if not dir_path.is_dir():
                return self.format_error("list_files", f"Path is not a directory: {path}")

            # Use optimized file listing with timeout protection
            files, directories, total_found, was_limited = await self._list_files_optimized(
                dir_path, pattern
            )

            # Combine directories first, then files
            all_items = directories + files

            if not all_items:
                return self.format_info("list_files", f"No items matching '{pattern}' in {path}")

            await self.log_tool_usage("list_files", args, True)

            # Build result with performance info
            result = f"📂 **Contents of {path}:**\n" + "\n".join(all_items)

            if was_limited:
                result += f"\n⚠️  **Limited to {self.MAX_FILES_TO_LIST} items for performance**"
                result += f"\n📊 **Total found: {total_found}** (showing first {len(all_items)})"
            elif total_found > len(all_items):
                result += f"\n📊 **Showing {len(all_items)} of {total_found} items**"

            return result

        except asyncio.TimeoutError:
            await self.log_tool_usage("list_files", args, False)
            return self.format_error(
                "list_files", f"Operation timed out - directory too large: {path}"
            )
        except (IOError, OSError, PermissionError) as e:
            await self.log_tool_usage("list_files", args, False)
            return self.format_error("list_files", str(e))

    async def _list_files_optimized(
        self, dir_path: Path, pattern: str
    ) -> tuple[List[str], List[str], int, bool]:
        """Optimized file listing with timeout and limits"""
        files: List[str] = []
        directories: List[str] = []
        total_found = 0
        was_limited = False

        try:
            # Apply timeout to the entire operation
            files, directories, total_found, was_limited = await asyncio.wait_for(
                self._scan_directory_safely(dir_path, pattern), timeout=self.MAX_PROCESSING_TIME
            )
        except asyncio.TimeoutError:
            was_limited = True

        # Sort for consistent output
        files.sort()
        directories.sort()
        return files, directories, total_found, was_limited

    async def _scan_directory_safely(
        self, dir_path: Path, pattern: str
    ) -> tuple[List[str], List[str], int, bool]:
        """Scan directory with safety limits"""
        files: List[str] = []
        directories: List[str] = []
        total_found = 0
        was_limited = False

        # For simple patterns, use iterdir for better performance
        items = dir_path.iterdir() if pattern == "*" else dir_path.glob(pattern)

        for item_path in items:
            if total_found >= self.MAX_FILES_TO_LIST:
                was_limited = True
                break

            total_found += 1

            # Yield control periodically for async operation
            if total_found % 100 == 0:
                await asyncio.sleep(0)

            self._add_directory_item(item_path, files, directories)

        return files, directories, total_found, was_limited

    def _add_directory_item(
        self, item_path: Path, files: List[str], directories: List[str]
    ) -> None:
        """Add a directory item to the appropriate list"""
        try:
            if item_path.is_file():
                stat = item_path.stat()
                size = stat.st_size
                files.append(f"📄 {item_path.name} ({size:,} bytes)")
            elif item_path.is_dir():
                directories.append(f"📁 {item_path.name}/")
        except (OSError, PermissionError):
            # Skip items that can't be accessed
            pass

    @handle_exceptions
    async def search_files(self, args: Dict[str, Any]) -> str:
        """Search for text across multiple files with AI enhancement"""
        validate_dict_input(args, "search_files arguments")

        pattern = validate_string_input(args.get("pattern", ""), "pattern")
        path = args.get("path", ".")
        file_pattern = args.get("file_pattern", "*")

        try:
            # Step 1: Get basic search results
            results = await self._get_search_results(pattern, path, file_pattern)

            # Step 2: Enhance with AI if enabled
            enhanced_results, ai_insights, search_suggestions = await self._enhance_search_with_ai(
                results, pattern, path, file_pattern
            )

            # Step 3: Format and return results
            result = self._format_search_results(
                enhanced_results, ai_insights, search_suggestions, pattern
            )
            await self.log_tool_usage("search_files", args, True)
            return result

        except (IOError, OSError, UnicodeDecodeError, PermissionError, AttributeError) as e:
            await self.log_tool_usage("search_files", args, False)
            return self.format_error("search_files", str(e))

    async def _get_search_results(self, pattern, path, file_pattern):
        """Get basic search results"""
        if hasattr(self.context_manager, "search_files"):
            return await self.context_manager.search_files(
                pattern=pattern, path=path, file_pattern=file_pattern
            )
        else:
            return await self._simple_file_search(pattern, path, file_pattern)

    async def _enhance_search_with_ai(self, results, pattern, path, file_pattern):
        """Enhance search results with AI insights if available"""
        enhanced_results = results
        ai_insights = None
        search_suggestions = []

        if self.is_ai_enabled() and results:
            try:
                search_context = f"Searching in {path} for files matching {file_pattern}"
                enhanced_results, ai_insights = await self.ai_enhancer.enhance_search(
                    pattern, results, search_context
                )
                search_suggestions = await self.ai_enhancer.suggest_related_searches(
                    pattern, search_context
                )
            except (IOError, OSError, UnicodeDecodeError, AttributeError, ValueError):
                # AI fails gracefully
                pass

        return enhanced_results, ai_insights, search_suggestions

    def _format_search_results(
        self, enhanced_results, ai_insights, search_suggestions, pattern
    ) -> str:
        """Format search results for display"""
        if not enhanced_results:
            base_message = f"🔍 No matches found for '{pattern}'"
            if search_suggestions:
                suggestion_text = self.format_ai_search_suggestions(search_suggestions)
                return f"{base_message}\n{suggestion_text}"
            return base_message

        formatted_results = [
            f"🔍 **Search Results for '{pattern}':**",
            self.format_ai_enhancement_status(),
            "",
        ]

        self._add_ai_insights_section(formatted_results, ai_insights)
        self._add_search_results_section(formatted_results, enhanced_results)
        self._add_search_suggestions_section(formatted_results, search_suggestions)

        return "\n".join(formatted_results)

    def _add_ai_insights_section(self, formatted_results, ai_insights):
        """Add AI insights section to results"""
        if not ai_insights:
            return

        if ai_insights.get("intent"):
            formatted_results.append(f"**AI detected intent**: {ai_insights['intent']}")
        if ai_insights.get("keywords"):
            keywords = ", ".join(ai_insights["keywords"][:5])
            formatted_results.append(f"**Related keywords**: {keywords}")
        formatted_results.append("")

    def _add_search_results_section(self, formatted_results, enhanced_results):
        """Add search results section"""
        formatted_results.append("## 📊 Search Results")

        for result in enhanced_results[:20]:
            if isinstance(result, dict):
                file_path = result.get("file", "Unknown")
                line_num = result.get("line_number", 0)
                line_content = result.get("line", "").strip()
            else:
                file_path = str(result)
                line_num = 0
                line_content = ""

            formatted_results.append(f"**{file_path}:{line_num}**\n  {line_content}\n")

        if len(enhanced_results) > 20:
            formatted_results.append(f"... and {len(enhanced_results) - 20} more matches")

    def _add_search_suggestions_section(self, formatted_results, search_suggestions):
        """Add search suggestions section"""
        if search_suggestions:
            suggestion_text = self.format_ai_search_suggestions(search_suggestions)
            formatted_results.append(suggestion_text)

    async def _simple_file_search(self, pattern: str, path: str, file_pattern: str) -> List[Dict]:
        """Simple fallback file search implementation"""
        results: List[Dict] = []
        search_path = self.safe_get_path(path)

        if not search_path.exists():
            return results

        regex = self._compile_search_regex(pattern)

        for file_path in search_path.rglob(file_pattern):
            if file_path.is_file():
                file_results = self._search_in_file(file_path, regex)
                results.extend(file_results)

        return results

    def _compile_search_regex(self, pattern: str):
        """Compile regex pattern with fallback to literal string"""
        try:
            return re.compile(pattern, re.IGNORECASE)
        except re.error:
            return re.compile(re.escape(pattern), re.IGNORECASE)

    def _search_in_file(self, file_path, regex) -> List[Dict]:
        """Search for pattern in a single file"""
        results: List[Dict] = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    if regex.search(line):
                        results.append(
                            {
                                "file": str(file_path.relative_to(self.workspace_root)),
                                "line_number": line_num,
                                "line": line.strip(),
                            }
                        )
                        # Limit matches per file
                        if len(results) >= 5:
                            break
        except (UnicodeDecodeError, PermissionError):
            # Skip files that can't be read
            pass

        return results
