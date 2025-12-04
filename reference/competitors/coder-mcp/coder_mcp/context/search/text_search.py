"""
Full-text search operations for the context manager
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ...core import ConfigurationManager
from ...security.path_security import PathSecurityManager
from ...utils.cache import ThreadSafeMetrics
from ...utils.file_utils import FileManager

logger = logging.getLogger(__name__)


class TextSearch:
    """Handle full-text search operations"""

    def __init__(self, workspace_root: Path, config_manager: ConfigurationManager):
        self.workspace_root = workspace_root
        self.config_manager = config_manager

        # Initialize dependencies
        self.path_security = PathSecurityManager(workspace_root)

        # Get search limits with proper fallbacks
        self.max_results = self._get_max_results()
        self.max_file_size = self._get_max_file_size()
        self.max_search_depth = self._get_max_search_depth()

        # Handle both ServerConfig (test) and ConfigurationManager (production) types
        if hasattr(config_manager, "limits"):
            # ServerConfig type (used in tests)
            max_file_size = config_manager.limits.max_file_size
            max_files_to_index = config_manager.limits.max_files_to_index
        elif (
            hasattr(config_manager, "config")
            and hasattr(config_manager.config, "server")
            and hasattr(config_manager.config.server, "limits")
        ):
            # ConfigurationManager type with ServerConfig structure (used in production)
            max_file_size = config_manager.config.server.limits.max_file_size
            max_files_to_index = config_manager.config.server.limits.max_files_to_index
        elif hasattr(config_manager, "config") and hasattr(config_manager.config, "storage"):
            # Legacy ConfigurationManager type (used in production)
            max_file_size = config_manager.config.storage.max_file_size
            max_files_to_index = config_manager.config.storage.max_files_to_index
        else:
            # Fallback defaults
            max_file_size = 10 * 1024 * 1024  # 10MB
            max_files_to_index = 100

        self.file_manager = FileManager(max_file_size)

        # Initialize metrics
        self.metrics = ThreadSafeMetrics()

        # Search settings
        self.max_files = max_files_to_index

    def _get_max_results(self) -> int:
        """Get max results with proper fallbacks"""
        try:
            if hasattr(self.config_manager, "limits"):
                return getattr(self.config_manager.limits, "max_search_results", 100)
            elif hasattr(self.config_manager, "config") and hasattr(
                self.config_manager.config, "search"
            ):
                return getattr(self.config_manager.config.search, "max_results", 100)
        except (AttributeError, TypeError):
            pass
        return 100  # Default fallback

    def _get_max_file_size(self) -> int:
        """Get max file size with proper fallbacks"""
        try:
            if hasattr(self.config_manager, "limits"):
                return getattr(self.config_manager.limits, "max_file_size", 10 * 1024 * 1024)
            elif hasattr(self.config_manager, "config") and hasattr(
                self.config_manager.config, "server"
            ):
                return getattr(
                    self.config_manager.config.server.limits, "max_file_size", 10 * 1024 * 1024
                )
        except (AttributeError, TypeError):
            pass
        return 10 * 1024 * 1024  # 10MB fallback

    def _get_max_search_depth(self) -> int:
        """Get max search depth with proper fallbacks"""
        try:
            if hasattr(self.config_manager, "limits"):
                return getattr(self.config_manager.limits, "max_search_depth", 10)
            elif hasattr(self.config_manager, "config") and hasattr(
                self.config_manager.config, "search"
            ):
                return getattr(self.config_manager.config.search, "max_depth", 10)
        except (AttributeError, TypeError):
            pass
        return 10  # Default fallback

    def _compile_search_pattern(
        self, pattern: str, case_sensitive: bool = False, whole_words: bool = False
    ) -> Optional[re.Pattern]:
        """Compile regex pattern for searching"""
        regex_flags = re.MULTILINE
        if not case_sensitive:
            regex_flags |= re.IGNORECASE

        if whole_words:
            pattern = rf"\b{re.escape(pattern)}\b"

        try:
            return re.compile(pattern, regex_flags)
        except re.error as e:
            logger.error("Invalid regex pattern '%s': %s", pattern, e)
            return None

    async def _search_through_files(
        self, search_path: Path, file_pattern: str, regex_pattern: re.Pattern, original_pattern: str
    ) -> List[Dict[str, Any]]:
        """Search through files in the given path"""
        results: List[Dict[str, Any]] = []
        file_count = 0

        for file_path in search_path.rglob(file_pattern):
            if file_count >= self.max_files:
                logger.warning("Reached maximum file search limit (%d)", self.max_files)
                break

            try:
                if not self._should_search_file(file_path):
                    continue

                content = await self.file_manager.safe_read_file(file_path)
                file_results = await self._search_in_file(
                    file_path, content, regex_pattern, original_pattern
                )
                results.extend(file_results)
                file_count += 1

                if len(results) >= self.max_results:
                    logger.info("Reached maximum search results limit (%d)", self.max_results)
                    break

            except (IOError, OSError) as e:
                logger.debug("IO error searching file %s: %s", file_path, e)
                continue
            except (UnicodeDecodeError, ValueError) as e:
                logger.debug("Unexpected error searching file %s: %s", file_path, e)
                continue

        return results

    async def search_files(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: str = "*",
        case_sensitive: bool = False,
        whole_words: bool = False,
    ) -> List[Dict[str, Any]]:
        """Search for text patterns across multiple files"""
        try:
            search_path = self.workspace_root / path

            if not search_path.exists():
                logger.warning("Search path does not exist: %s", search_path)
                return []

            regex_pattern = self._compile_search_pattern(pattern, case_sensitive, whole_words)
            if not regex_pattern:
                return []

            results = await self._search_through_files(
                search_path, file_pattern, regex_pattern, pattern
            )
            results = await self._rank_search_results(results, pattern)

            self.metrics.increment("file_searches")
            logger.info("Text search completed: %d matches found for '%s'", len(results), pattern)

            return results

        except (IOError, OSError) as e:
            logger.error("IO error during file search for pattern '%s': %s", pattern, e)
            return []
        except (UnicodeDecodeError, ValueError, AttributeError) as e:
            logger.error("File search failed for pattern '%s': %s", pattern, e)
            return []

    async def search_in_file(
        self, file_path: str, pattern: str, case_sensitive: bool = False, whole_words: bool = False
    ) -> List[Dict[str, Any]]:
        """Search for a pattern within a specific file"""
        try:
            full_path = self.workspace_root / file_path

            if not self._should_search_file(full_path):
                return []

            regex_pattern = self._compile_search_pattern(pattern, case_sensitive, whole_words)
            if not regex_pattern:
                return []

            content = await self.file_manager.safe_read_file(full_path)
            return await self._search_in_file(full_path, content, regex_pattern, pattern)

        except (IOError, OSError) as e:
            logger.error("IO error searching in file %s: %s", file_path, e)
            return []
        except (UnicodeDecodeError, ValueError, AttributeError) as e:
            logger.error("Failed to search in file %s: %s", file_path, e)
            return []

    async def search_with_context(
        self, pattern: str, context_lines: int = 2, path: str = ".", file_pattern: str = "*"
    ) -> List[Dict[str, Any]]:
        """Search with additional context lines around matches"""
        try:
            results = await self.search_files(pattern, path, file_pattern)
            enhanced_results = []

            for result in results:
                enhanced_result = await self._add_context_to_result(result, context_lines)
                enhanced_results.append(enhanced_result)

            return enhanced_results

        except (UnicodeDecodeError, ValueError, AttributeError, TypeError) as e:
            logger.error("Context search failed: %s", e)
            return []

    async def multi_pattern_search(
        self, patterns: List[str], path: str = ".", file_pattern: str = "*", operator: str = "OR"
    ) -> List[Dict[str, Any]]:
        """Search for multiple patterns with AND/OR logic"""
        try:
            if operator.upper() == "OR":
                return await self._multi_pattern_or_search(patterns, path, file_pattern)
            elif operator.upper() == "AND":
                return await self._multi_pattern_and_search(patterns, path, file_pattern)
            else:
                logger.error("Invalid operator '%s'. Use 'AND' or 'OR'", operator)
                return []

        except (UnicodeDecodeError, ValueError, AttributeError, TypeError) as e:
            logger.error("Multi-pattern search failed: %s", e)
            return []

    async def _multi_pattern_or_search(
        self, patterns: List[str], path: str, file_pattern: str
    ) -> List[Dict[str, Any]]:
        """Perform OR search across multiple patterns"""
        all_results = []
        for pattern in patterns:
            results = await self.search_files(pattern, path, file_pattern)
            all_results.extend(results)

        # Remove duplicates based on file path and line number
        unique_results = []
        seen = set()
        for result in all_results:
            key = (result["file"], result["line_number"])
            if key not in seen:
                seen.add(key)
                unique_results.append(result)

        return unique_results

    async def _multi_pattern_and_search(
        self, patterns: List[str], path: str, file_pattern: str
    ) -> List[Dict[str, Any]]:
        """Perform AND search across multiple patterns"""
        if not patterns:
            return []

        results = await self.search_files(patterns[0], path, file_pattern)

        for pattern in patterns[1:]:
            pattern_results = await self.search_files(pattern, path, file_pattern)
            pattern_files = {r["file"] for r in pattern_results}
            results = [r for r in results if r["file"] in pattern_files]

        return results

    def _should_search_file(self, file_path: Path) -> bool:
        """Determine if a file should be searched"""
        try:
            if not self.path_security.is_safe_path(file_path):
                return False

            if self.file_manager.is_binary_file(file_path):
                return False

            file_info = self.file_manager.get_file_info(file_path)
            if file_info["size"] > self.max_file_size:
                return False

            return True

        except (IOError, OSError) as e:
            logger.debug("IO error checking file %s: %s", file_path, e)
            return False
        except (UnicodeDecodeError, ValueError, AttributeError, TypeError) as e:
            logger.debug("Error checking if file should be searched %s: %s", file_path, e)
            return False

    async def _search_in_file(
        self, file_path: Path, content: str, regex_pattern: re.Pattern, original_pattern: str
    ) -> List[Dict[str, Any]]:
        """Search for pattern matches within a file's content"""
        results = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            matches = list(regex_pattern.finditer(line))

            for match in matches:
                result = {
                    "file": str(file_path.relative_to(self.workspace_root)),
                    "line_number": line_num,
                    "line": line,
                    "match": original_pattern,
                    "match_start": match.start(),
                    "match_end": match.end(),
                    "matched_text": match.group(),
                    "file_type": self.file_manager.get_file_type(file_path),
                }

                results.append(result)

                if len(results) >= 20:  # Max 20 matches per file
                    break

            if len(results) >= 20:
                break

        return results

    def _calculate_relevance_score(self, result: Dict[str, Any], pattern: str) -> float:
        """Calculate relevance score for a search result"""
        score = 0.0

        # File name relevance
        file_name = Path(result["file"]).name.lower()
        if pattern.lower() in file_name:
            score += 10.0

        # File type relevance (prefer source code files)
        file_type = result.get("file_type", "")
        if file_type in ["python", "javascript", "typescript"]:
            score += 5.0
        elif file_type in ["markdown", "text"]:
            score += 2.0

        # Line content relevance
        line = result["line"].lower()
        pattern_lower = pattern.lower()

        # Exact match gets higher score
        if pattern_lower == result.get("matched_text", "").lower():
            score += 8.0

        # Word boundary matches
        if f" {pattern_lower} " in line:
            score += 5.0

        # Function/class definition context
        if any(keyword in line for keyword in ["def ", "class ", "function "]):
            score += 3.0

        # Comment context (slightly lower priority)
        if line.strip().startswith(("#", "//", "/*")):
            score += 1.0

        return score

    async def _rank_search_results(
        self, results: List[Dict[str, Any]], pattern: str
    ) -> List[Dict[str, Any]]:
        """Rank search results by relevance"""
        try:
            scored_results: List[Tuple[float, Dict[str, Any]]] = [
                (self._calculate_relevance_score(r, pattern), r) for r in results
            ]
            scored_results.sort(key=lambda x: x[0], reverse=True)
            return [result for _, result in scored_results]

        except (UnicodeDecodeError, ValueError, AttributeError, TypeError) as e:
            logger.error("Failed to rank search results: %s", e)
            return results

    async def _add_context_to_result(
        self, result: Dict[str, Any], context_lines: int
    ) -> Dict[str, Any]:
        """Add context lines around a search result"""
        try:
            file_path = self.workspace_root / result["file"]
            content = await self.file_manager.safe_read_file(file_path)
            lines = content.split("\n")

            line_num = result["line_number"] - 1  # Convert to 0-based index
            start_line = max(0, line_num - context_lines)
            end_line = min(len(lines), line_num + context_lines + 1)

            context = {
                "before": lines[start_line:line_num],
                "match": lines[line_num],
                "after": lines[line_num + 1 : end_line],
            }

            enhanced_result = result.copy()
            enhanced_result["context"] = context
            enhanced_result["context_start_line"] = start_line + 1
            enhanced_result["context_end_line"] = end_line

            return enhanced_result

        except (IOError, OSError) as e:
            logger.error("IO error adding context to result: %s", e)
            return result
        except (UnicodeDecodeError, ValueError, AttributeError, TypeError) as e:
            logger.error("Failed to add context to result: %s", e)
            return result

    async def get_search_stats(self) -> Dict[str, Any]:
        """Get statistics about search operations"""
        try:
            metrics_snapshot = self.metrics.get_snapshot()

            return {
                "total_searches": metrics_snapshot.get("file_searches", 0),
                "workspace_root": str(self.workspace_root),
                "max_results": self.max_results,
                "max_files": self.max_files,
                "searchable_files": await self._count_searchable_files(),
            }

        except (UnicodeDecodeError, ValueError, AttributeError, TypeError) as e:
            logger.error("Failed to get search stats: %s", e)
            return {"error": str(e)}

    async def _count_searchable_files(self) -> int:
        """Count the number of searchable files in the workspace"""
        try:
            count = 0
            for file_path in self.path_security.get_safe_file_iterator("*"):
                if self._should_search_file(file_path):
                    count += 1
                if count >= self.max_files:
                    break
            return count

        except (IOError, OSError) as e:
            logger.error("IO error counting searchable files: %s", e)
            return 0
        except (UnicodeDecodeError, ValueError, AttributeError, TypeError) as e:
            logger.error("Failed to count searchable files: %s", e)
            return 0
