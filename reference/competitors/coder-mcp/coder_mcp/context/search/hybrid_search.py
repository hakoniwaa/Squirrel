"""
Hybrid search operations combining semantic and text search
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...core import ConfigurationManager
from .semantic_search import SemanticSearch
from .text_search import TextSearch

logger = logging.getLogger(__name__)


class HybridSearch:
    """Combine semantic and text search for comprehensive results"""

    def __init__(self, workspace_root: Path, config_manager: ConfigurationManager):
        self.workspace_root = workspace_root
        self.config_manager = config_manager

        # Initialize search components
        self.semantic_search = SemanticSearch(config_manager)
        self.text_search = TextSearch(workspace_root, config_manager)

        # Hybrid search settings
        self.semantic_weight = 0.6  # Weight for semantic search results
        self.text_weight = 0.4  # Weight for text search results

    async def search(
        self,
        query: str,
        top_k: int = 10,
        search_strategy: str = "combined",
        semantic_ratio: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and text search

        Args:
            query: Search query
            top_k: Number of results to return
            search_strategy: "combined", "semantic_first", "text_first", or "parallel"
            semantic_ratio: Ratio of semantic to text results (0.0 to 1.0)
        """
        try:
            if search_strategy == "combined":
                return await self._combined_search(query, top_k, semantic_ratio)
            elif search_strategy == "semantic_first":
                return await self._semantic_first_search(query, top_k)
            elif search_strategy == "text_first":
                return await self._text_first_search(query, top_k)
            elif search_strategy == "parallel":
                return await self._parallel_search(query, top_k, semantic_ratio)
            else:
                logger.error(f"Unknown search strategy: {search_strategy}")
                return []

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    async def _combined_search(
        self, query: str, top_k: int, semantic_ratio: float
    ) -> List[Dict[str, Any]]:
        """Combine results from both search methods with weighted scoring"""
        # Get results from both search methods
        semantic_results = await self.semantic_search.search(query, top_k * 2)
        text_results = await self.text_search.search_files(query)

        # Combine and rank results
        combined_results = await self._merge_and_rank_results(
            semantic_results, text_results, semantic_ratio
        )

        return combined_results[:top_k]

    async def _semantic_first_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Try semantic search first, fall back to text search if insufficient results"""
        semantic_results = await self.semantic_search.search(query, top_k)

        if len(semantic_results) >= top_k * 0.7:  # If we have 70% of desired results
            return semantic_results[:top_k]

        # Supplement with text search
        text_results = await self.text_search.search_files(query)
        semantic_files = {r.get("metadata", {}).get("file_path", "") for r in semantic_results}

        # Add text results that aren't already in semantic results
        supplemental_results = []
        for result in text_results:
            if result["file"] not in semantic_files:
                # Convert text result format to match semantic format
                converted_result = await self._convert_text_result_to_semantic_format(result)
                supplemental_results.append(converted_result)

        combined = semantic_results + supplemental_results
        return combined[:top_k]

    async def _text_first_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Try text search first, supplement with semantic search"""
        text_results = await self.text_search.search_files(query)

        if len(text_results) >= top_k:
            # Convert text results to common format and return
            converted_results = []
            for result in text_results[:top_k]:
                converted_result = await self._convert_text_result_to_semantic_format(result)
                converted_results.append(converted_result)
            return converted_results

        # Supplement with semantic search
        semantic_results = await self.semantic_search.search(query, top_k)
        text_files = {r["file"] for r in text_results}

        # Add semantic results that aren't already in text results
        supplemental_results = []
        for result in semantic_results:
            file_path = result.get("metadata", {}).get("file_path", "")
            if file_path not in text_files:
                supplemental_results.append(result)

        # Convert text results and combine
        converted_text_results = []
        for result in text_results:
            converted_result = await self._convert_text_result_to_semantic_format(result)
            converted_text_results.append(converted_result)

        combined = converted_text_results + supplemental_results
        return combined[:top_k]

    async def _parallel_search(
        self, query: str, top_k: int, semantic_ratio: float
    ) -> List[Dict[str, Any]]:
        """Run both searches in parallel and merge results"""
        import asyncio

        # Run both searches concurrently
        semantic_task = asyncio.create_task(
            self.semantic_search.search(query, int(top_k * semantic_ratio * 2))
        )
        text_task = asyncio.create_task(self.text_search.search_files(query))

        semantic_results, text_results = await asyncio.gather(semantic_task, text_task)

        # Merge and rank results
        combined_results = await self._merge_and_rank_results(
            semantic_results, text_results, semantic_ratio
        )

        return combined_results[:top_k]

    async def _merge_and_rank_results(
        self,
        semantic_results: List[Dict[str, Any]],
        text_results: List[Dict[str, Any]],
        semantic_ratio: float,
    ) -> List[Dict[str, Any]]:
        """Merge and rank results from both search methods"""
        try:
            # Create a combined scoring system
            combined_results = {}

            # Process semantic results
            for result in semantic_results:
                file_path = result.get("metadata", {}).get("file_path", "")
                if file_path:
                    semantic_score = result.get("score", 0) * semantic_ratio
                    combined_results[file_path] = {
                        "result": result,
                        "semantic_score": semantic_score,
                        "text_score": 0,
                        "combined_score": semantic_score,
                        "source": "semantic",
                    }

            # Process text results and merge
            text_ratio = 1.0 - semantic_ratio
            for result in text_results[:20]:  # Limit text results to avoid overwhelming
                file_path = result["file"]

                # Calculate text score based on relevance
                text_score = self._calculate_text_relevance_score(result) * text_ratio

                if file_path in combined_results:
                    # Update existing entry
                    combined_results[file_path]["text_score"] = text_score
                    combined_results[file_path]["combined_score"] += text_score
                    combined_results[file_path]["source"] = "both"

                    # Enhance the result with text search context
                    combined_results[file_path]["result"]["text_context"] = {
                        "line_number": result["line_number"],
                        "matched_text": result.get("matched_text", ""),
                        "line": result["line"],
                    }
                else:
                    # Create new entry from text result
                    converted_result = await self._convert_text_result_to_semantic_format(result)
                    combined_results[file_path] = {
                        "result": converted_result,
                        "semantic_score": 0,
                        "text_score": text_score,
                        "combined_score": text_score,
                        "source": "text",
                    }

            # Sort by combined score and extract results
            sorted_items = sorted(
                combined_results.values(), key=lambda x: x["combined_score"], reverse=True
            )

            # Enhance results with hybrid metadata
            enhanced_results = []
            for item in sorted_items:
                result = item["result"].copy()
                result["hybrid_metadata"] = {
                    "semantic_score": item["semantic_score"],
                    "text_score": item["text_score"],
                    "combined_score": item["combined_score"],
                    "source": item["source"],
                }
                enhanced_results.append(result)

            return enhanced_results

        except Exception as e:
            logger.error(f"Failed to merge and rank results: {e}")
            return semantic_results + text_results

    def _calculate_text_relevance_score(self, text_result: Dict[str, Any]) -> float:
        """Calculate relevance score for text search results"""
        score = 0.5  # Base score

        # File type bonus
        file_type = text_result.get("file_type", "")
        if file_type in ["python", "javascript", "typescript"]:
            score += 0.3
        elif file_type in ["markdown", "text"]:
            score += 0.1

        # Match quality
        line = text_result["line"].lower()
        matched_text = text_result.get("matched_text", "").lower()

        # Exact match bonus
        if matched_text in line:
            score += 0.2

        # Context bonus (function/class definitions)
        if any(keyword in line for keyword in ["def ", "class ", "function "]):
            score += 0.2

        # Normalize to 0-1 range
        return min(1.0, score)

    async def _convert_text_result_to_semantic_format(
        self, text_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert text search result to semantic search result format"""
        return {
            "score": self._calculate_text_relevance_score(text_result),
            "metadata": {
                "file_path": text_result["file"],
                "file_type": text_result.get("file_type", "unknown"),
                "content_preview": text_result["line"][:1000],
                "lines_of_code": 1,  # We only have one line from text search
                "search_result_type": "text_search",
            },
            "text_context": {
                "line_number": text_result["line_number"],
                "matched_text": text_result.get("matched_text", ""),
                "line": text_result["line"],
                "match_start": text_result.get("match_start", 0),
                "match_end": text_result.get("match_end", 0),
            },
        }

    async def search_with_context(
        self, query: str, context_files: Optional[List[str]] = None, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Perform search with additional context from specific files"""
        try:
            # Enhance query with context if provided
            enhanced_query = query
            if context_files:
                context_content = await self._get_context_content(context_files or [])
                enhanced_query = f"Context: {context_content}\n\nQuery: {query}"

            # Perform hybrid search with enhanced query
            results = await self.search(enhanced_query, top_k)

            # Add context metadata to results
            for result in results:
                result["search_context"] = {
                    "original_query": query,
                    "context_files": context_files or [],
                    "enhanced_query": len(enhanced_query) > len(query),
                }

            return results

        except Exception as e:
            logger.error(f"Context search failed: {e}")
            return []

    async def contextual_search(
        self, query: str, context_files: Optional[List[str]] = None, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Perform search with additional context from specific files"""
        try:
            # Use semantic search for context-aware searching
            semantic_results = await self.semantic_search.search_with_context(
                query, context_files, top_k // 2
            )

            # Also do regular hybrid search
            hybrid_results = await self.search(query, top_k // 2, "parallel")

            # Combine results, prioritizing context-aware results
            all_results = []
            seen_files = set()

            # Add context-aware results first
            for result in semantic_results:
                file_path = result.get("metadata", {}).get("file_path", "")
                if file_path and file_path not in seen_files:
                    result["context_enhanced"] = True
                    all_results.append(result)
                    seen_files.add(file_path)

            # Add remaining hybrid results
            for result in hybrid_results:
                file_path = result.get("metadata", {}).get("file_path", "")
                if file_path and file_path not in seen_files:
                    result["context_enhanced"] = False
                    all_results.append(result)
                    seen_files.add(file_path)

            return all_results[:top_k]

        except Exception as e:
            logger.error(f"Contextual search failed: {e}")
            return []

    async def search_with_filters(
        self, query: str, filters: Dict[str, Any], top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Search with file type, size, or other filters"""
        try:
            # Apply filters to semantic search
            semantic_results = await self.semantic_search.search(query, top_k * 2, filters)

            # Apply filters to text search
            file_pattern = "*"
            if "file_types" in filters:
                file_types = filters["file_types"]
                if isinstance(file_types, list) and len(file_types) == 1:
                    ext = file_types[0]
                    if not ext.startswith("."):
                        ext = f".{ext}"
                    file_pattern = f"*{ext}"

            text_results = await self.text_search.search_files(query, file_pattern=file_pattern)

            # Merge results
            combined_results = await self._merge_and_rank_results(
                semantic_results, text_results, 0.6
            )

            # Apply additional filters
            filtered_results = await self._apply_additional_filters(combined_results, filters)

            return filtered_results[:top_k]

        except Exception as e:
            logger.error(f"Filtered search failed: {e}")
            return []

    async def _apply_additional_filters(
        self, results: List[Dict[str, Any]], filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply additional filters to search results"""
        filtered_results = []

        for result in results:
            metadata = result.get("metadata", {})

            # File size filter
            if "max_file_size" in filters:
                file_size = metadata.get("file_size", 0)
                if file_size > filters["max_file_size"]:
                    continue

            # Modified date filter
            if "modified_after" in filters:
                # Would need to implement date comparison
                pass

            # Content filters
            if "exclude_patterns" in filters:
                content_preview = metadata.get("content_preview", "")
                if any(pattern in content_preview for pattern in filters["exclude_patterns"]):
                    continue

            filtered_results.append(result)

        return filtered_results

    async def get_search_stats(self) -> Dict[str, Any]:
        """Get comprehensive search statistics"""
        try:
            semantic_stats = await self.semantic_search.get_search_stats()
            text_stats = await self.text_search.get_search_stats()

            return {
                "semantic_search": semantic_stats,
                "text_search": text_stats,
                "hybrid_settings": {
                    "semantic_weight": self.semantic_weight,
                    "text_weight": self.text_weight,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get search stats: {e}")
            return {"error": str(e)}

    async def _get_context_content(self, context_files: List[str]) -> str:
        """Fetch and concatenate content from context files for search enhancement."""
        # TODO: Implement actual file reading logic if needed
        return "\n".join([f"[Content from {f}]" for f in context_files])
