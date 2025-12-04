#!/usr/bin/env python3
"""
Context management tool handler
Handles project context initialization, updates, and search operations
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from mcp.types import Tool

from ...security.exceptions import handle_exceptions
from ...security.validators import validate_dict_input, validate_string_input
from ..base_handler import BaseHandler

logger = logging.getLogger(__name__)


class ContextHandler(BaseHandler):
    """Context management operations"""

    def _format_quality_score(self, quality_metrics: Dict[str, Any]) -> str:
        """Format quality score display with helpful context"""
        overall_score = quality_metrics.get("overall_score")

        if overall_score is None:
            return "**Quality Score:** Calculating..."
        if quality_metrics.get("error"):
            return "**Quality Score:** Analysis failed"
        if overall_score == 0 and quality_metrics.get("files_reviewed", 0) == 0:
            return "**Quality Score:** No files analyzed"

        files_reviewed = quality_metrics.get("files_reviewed", 0)
        return f"**Quality Score:** {overall_score}/10 (based on {files_reviewed} files)"

    @staticmethod
    def get_tools() -> List[Tool]:
        """Get context management tools"""
        return [
            Tool(
                name="initialize_context",
                description=(
                    "Initialize or load project context. "
                    "ALWAYS RUN THIS FIRST to understand the project."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "force_refresh": {
                            "type": "boolean",
                            "default": False,
                            "description": "Force rebuild of context even if cached",
                        }
                    },
                },
            ),
            Tool(
                name="analyze_project",
                description=(
                    "Analyze the entire project structure and generate comprehensive report"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "generate_report": {
                            "type": "boolean",
                            "default": True,
                            "description": "Generate detailed analysis report",
                        },
                        "include_metrics": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include quality metrics in analysis",
                        },
                    },
                },
            ),
            Tool(
                name="update_context",
                description="Update project context with new information or improvements made",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "section": {
                            "type": "string",
                            "enum": [
                                "structure",
                                "dependencies",
                                "quality_metrics",
                                "patterns",
                                "improvements_made",
                                "known_issues",
                            ],
                            "description": "Section to update",
                        },
                        "updates": {
                            "type": "object",
                            "description": "Updates to apply to the section",
                        },
                    },
                    "required": ["section", "updates"],
                },
            ),
            Tool(
                name="add_note",
                description="Add a note or memory about the project for future reference",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "note_type": {
                            "type": "string",
                            "enum": [
                                "decision",
                                "todo",
                                "warning",
                                "insight",
                                "pattern",
                                "collaboration",
                            ],
                            "description": "Type of note",
                        },
                        "content": {"type": "string", "description": "Note content"},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for categorization",
                        },
                    },
                    "required": ["note_type", "content"],
                },
            ),
            Tool(
                name="search_context",
                description=("Search through project context and memories using vector search"),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "search_type": {
                            "type": "string",
                            "enum": ["context", "memories", "code", "all"],
                            "default": "all",
                        },
                    },
                    "required": ["query"],
                },
            ),
        ]

    def _perform_file_indexing(self, force_refresh: bool) -> tuple[List[str], Dict[str, Any]]:
        """Handle file indexing operations and return status messages and result"""
        del force_refresh  # Parameter kept for interface consistency but not used in placeholder
        indexing_status = ["🔄 **Indexing project files...**"]
        # This is a placeholder for the actual async indexing operation
        # The real implementation will be called from the main method
        return indexing_status, {}

    async def _index_and_analyze(self, force_refresh: bool) -> tuple[List[str], Dict[str, Any]]:

        indexing_status = ["🔄 **Indexing project files...**"]

        index_result = await self.context_manager.batch_index_files(force_reindex=force_refresh)

        # Update context with indexed files
        await self.context_manager.update_context(
            {
                "indexing": {
                    "indexed_count": index_result["indexed_count"],
                    "error_count": index_result["error_count"],
                    "max_files": index_result["max_files"],
                    "completed": index_result["completed"],
                    "last_indexed": datetime.now().isoformat(),
                }
            }
        )

        # Analyze project structure
        structure = await self.context_manager.analyze_project_structure()
        await self.context_manager.update_context({"structure": structure})

        # Calculate quality metrics
        indexing_status.append("🔄 **Calculating quality metrics...**")
        quality_metrics = await self.context_manager.calculate_quality_metrics()
        await self.context_manager.update_context({"quality_metrics": quality_metrics})

        # Log initialization context information
        total_files = structure.get("total_files", 0)
        filtered_files = index_result["indexed_count"]
        coverage = quality_metrics.get("test_coverage", 0)

        logger.info(f"Workspace root: {self.workspace_root}")
        logger.info(f"Total files found: {total_files}")
        logger.info(f"After filtering: {filtered_files}")
        logger.info(f"Test coverage: {coverage}%")

        files_analyzed = quality_metrics.get("files_reviewed", 0)
        indexing_status.append(f"📊 **Quality analysis complete: {files_analyzed} files analyzed**")

        indexing_status.append(f"✅ **Indexed {index_result['indexed_count']} files**")
        if index_result["error_count"] > 0:
            indexing_status.append(f"⚠️  **{index_result['error_count']} files had errors**")

        return indexing_status, index_result

    async def _get_ai_insights(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI insights for context if AI is enabled"""
        if not self.is_ai_enabled():
            return {}

        try:
            # Use the AI enhancer orchestrator to get context understanding
            context_enhancer = self.ai_enhancer.get_enhancer("context")
            if context_enhancer:
                ai_insights = await context_enhancer.enhance_context_understanding(
                    context, str(self.workspace_root)
                )
                return ai_insights
            else:
                logger.warning("Context enhancer not available")
                return {}
        except Exception as e:
            logger.warning(f"Failed to get AI insights: {e}")
            return {}

    def _get_fallback_ai_insights(self) -> Dict[str, Any]:
        """Provide fallback AI insights when enhancement fails"""
        return {
            "project_type": "AI analysis unavailable",
            "architecture_style": "AI analysis unavailable",
            "key_technologies": [],
            "health_assessment": {
                "score": 0,
                "strengths": [],
                "concerns": [],
                "overall_assessment": "Analysis unavailable",
            },
        }

    def _add_basic_project_info(
        self, summary_parts: List[str], context: Dict[str, Any], indexing_info: Dict[str, Any]
    ) -> None:
        """Add basic project information to summary"""
        structure_info = context.get("structure", {})

        summary_parts.extend(
            [
                "📁 **Project Context Initialized**",
                f"**Root:** {self.workspace_root}",
                f"**Files Indexed:** {indexing_info.get('indexed_count', 0)}",
                f"**Project Files:** {structure_info.get('total_files', 0)}",
                f"**Dependencies:** {len(context.get('dependencies', {}))}",
                self._format_quality_score(context.get("quality_metrics", {})),
                self.format_ai_enhancement_status(),
            ]
        )

        if context.get("patterns"):
            summary_parts.append(f"**Patterns Found:** {len(context['patterns'])}")

        if context.get("known_issues"):
            summary_parts.append(f"**Known Issues:** {len(context['known_issues'])}")

        if indexing_info.get("last_indexed"):
            summary_parts.append(f"**Last Indexed:** {indexing_info['last_indexed']}")

        # Add file type breakdown if available
        if structure_info.get("file_types"):
            file_types = structure_info["file_types"]
            top_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:3]
            type_summary = ", ".join([f"{ext}: {count}" for ext, count in top_types])
            summary_parts.append(f"**File Types:** {type_summary}")

    def _add_ai_insights_to_summary(
        self, summary_parts: List[str], ai_insights: Dict[str, Any]
    ) -> None:
        """Add AI insights to the summary"""
        if not ai_insights:
            return

        summary_parts.append("\n## 🤖 AI Project Analysis")

        # Extract and format AI insights dynamically
        project_type = ai_insights.get("project_type", "project type not available")
        architecture = ai_insights.get("architecture_style", "architecture not available")

        summary_parts.append(f"**Project Type**: {project_type}")
        summary_parts.append(f"**Architecture**: {architecture}")

        # Handle technologies
        technologies = ai_insights.get("key_technologies", [])
        if technologies:
            tech_str = ", ".join(technologies)
            summary_parts.append(f"**Technologies**: {tech_str}")

        # Handle health assessment
        health_assessment = ai_insights.get("health_assessment", {})
        if health_assessment:
            score = health_assessment.get("score", 0)
            summary_parts.append(f"**Health Score**: {score}/10")

            strengths = health_assessment.get("strengths", [])
            if strengths:
                strengths_str = ", ".join(strengths)
                summary_parts.append(f"**Strengths**: {strengths_str}")

            concerns = health_assessment.get("concerns", [])
            if concerns:
                concerns_str = ", ".join(concerns)
                summary_parts.append(f"**Areas for Improvement**: {concerns_str}")

    def _build_context_summary(
        self, context: Dict[str, Any], indexing_summary: str, ai_insights: Dict[str, Any]
    ) -> str:
        """Build comprehensive context summary"""
        indexing_info = context.get("indexing", {})
        summary_parts = [indexing_summary] if indexing_summary else []

        self._add_basic_project_info(summary_parts, context, indexing_info)

        # Add AI insights if available
        self._add_ai_insights_to_summary(summary_parts, ai_insights)

        return "\n".join(summary_parts)

    @handle_exceptions
    async def initialize_context(self, args: Dict[str, Any]) -> str:
        """Initialize or load project context with AI enhancement"""
        validate_dict_input(args, "initialize_context arguments")
        force_refresh = args.get("force_refresh", False)

        if not self.context_manager:
            return self.format_error("initialize_context", "Context manager not initialized")

        try:
            context = await self.context_manager.load_context(force_refresh=force_refresh)

            # Check if we need to index files
            current_indexed_count = context.get("indexing", {}).get("indexed_count", 0)
            should_index = force_refresh or current_indexed_count == 0

            if should_index:
                indexing_status, _ = await self._index_and_analyze(force_refresh)
                indexing_summary = "\n".join(indexing_status) + "\n"
                # Reload context to get updated data
                context = await self.context_manager.load_context()
            else:
                indexing_summary = ""

            # Build summary parts manually
            indexing_info = context.get("indexing", {})
            summary_parts = [indexing_summary] if indexing_summary else []

            # Add basic project info
            self._add_basic_project_info(summary_parts, context, indexing_info)

            # Get and add AI insights
            ai_insights = await self._get_ai_insights(context)
            self._add_ai_insights_to_summary(summary_parts, ai_insights)

            summary = "\n".join(summary_parts)

            await self.log_tool_usage("initialize_context", args, True)
            return summary

        except (ConnectionError, TimeoutError) as e:
            await self.log_tool_usage("initialize_context", args, False)
            return self.format_error("initialize_context", f"Connection error: {e}")
        except (ValueError, TypeError, AttributeError, RuntimeError, OSError) as e:
            await self.log_tool_usage("initialize_context", args, False)
            return self.format_error("initialize_context", str(e))

    def _ensure_meaningful_ai_insights(self, ai_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure AI insights have meaningful values instead of 'not available'"""
        if not ai_insights:
            return {}

        # Replace any "not available" values with more meaningful defaults
        enhanced_insights = ai_insights.copy()

        if enhanced_insights.get("project_type") in [None, "project type not available"]:
            enhanced_insights["project_type"] = "Analysis in progress..."

        if enhanced_insights.get("architecture_style") in [None, "architecture not available"]:
            enhanced_insights["architecture_style"] = "Architecture analysis pending..."

        return enhanced_insights

    @handle_exceptions
    async def analyze_project(self, args: Dict[str, Any]) -> str:
        """Analyze the entire project structure and generate comprehensive report"""
        validate_dict_input(args, "analyze_project arguments")

        generate_report = args.get("generate_report", True)
        include_metrics = args.get("include_metrics", True)

        try:
            # Get or initialize context
            context = await self._get_or_initialize_context()

            # Build structured result
            structured_result = self._build_analysis_result(context, include_metrics)

            await self.log_tool_usage("analyze_project", args, True)

            # Return appropriate format
            return self._format_analysis_response(structured_result, generate_report)

        except (IOError, OSError, UnicodeDecodeError, AttributeError, ValueError) as e:
            await self.log_tool_usage("analyze_project", args, False)
            return self.format_error("analyze_project", str(e))

    async def _get_or_initialize_context(self) -> Dict[str, Any]:
        context = await self.context_manager.load_context()
        # If context is empty, initialize it first
        if not context or not context.get("structure"):
            await self._index_and_analyze(force_refresh=False)
            context = await self.context_manager.load_context()

        return context

    def _build_analysis_result(
        self, context: Dict[str, Any], include_metrics: bool
    ) -> Dict[str, Any]:
        """Build structured analysis result from context"""
        structure_info = context.get("structure", {})
        quality_metrics = context.get("quality_metrics", {})
        # Indexing info is stored directly in context, not in structure
        indexing_info = context.get("indexing", {})

        # Use total_files from structure analysis, fallback to indexed_count if not available
        total_files = structure_info.get("total_files", indexing_info.get("indexed_count", 0))

        # Build result parts
        result_parts = [
            "📊 **Project Analysis Complete**",
            f"**Total Files:** {total_files}",
        ]

        if include_metrics:
            self._add_metrics_to_result(result_parts, quality_metrics)

        self._add_project_details_to_result(result_parts, context, structure_info)

        # Add AI enhancement status
        result_parts.append(self.format_ai_enhancement_status())

        return {
            "success": True,
            "total_files": total_files,
            "has_tests": self._has_test_files(context),
            "has_documentation": self._has_documentation_files(context),
            "quality_score": quality_metrics.get("overall_score", 0),
            "message": "\n".join(result_parts),
        }

    def _add_metrics_to_result(
        self, result_parts: List[str], quality_metrics: Dict[str, Any]
    ) -> None:
        """Add quality metrics to result parts"""
        result_parts.append(self._format_quality_score(quality_metrics))
        if quality_metrics.get("files_reviewed", 0) > 0:
            result_parts.append(f"**Issues Found:** {quality_metrics.get('issues_found', 0)}")

    def _add_project_details_to_result(
        self, result_parts: List[str], context: Dict[str, Any], structure_info: Dict[str, Any]
    ) -> None:
        """Add project details to result parts"""
        # Add file type breakdown
        search_stats = structure_info.get("search", {})
        if search_stats.get("file_types"):
            file_types = search_stats["file_types"]
            top_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:3]
            type_summary = ", ".join([f"{ext}: {count}" for ext, count in top_types])
            result_parts.append(f"**File Types:** {type_summary}")

        # Add dependencies, patterns, and issues
        dependencies = context.get("dependencies", {})
        if dependencies:
            result_parts.append(f"**Dependencies:** {len(dependencies)}")

        patterns = context.get("patterns", [])
        if patterns:
            result_parts.append(f"**Patterns Found:** {len(patterns)}")

        known_issues = context.get("known_issues", [])
        if known_issues:
            result_parts.append(f"**Known Issues:** {len(known_issues)}")

    def _format_analysis_response(
        self, structured_result: Dict[str, Any], generate_report: bool
    ) -> str:
        """Format the analysis response based on report preference"""
        if generate_report:
            # For report mode, return JSON with both message and structured data
            import json

            return json.dumps(structured_result)
        else:
            # For programmatic use, return just the key metrics as JSON
            import json

            summary_result = {
                "success": structured_result["success"],
                "total_files": structured_result["total_files"],
                "message": f"Analysis complete: {structured_result['total_files']} files analyzed",
            }
            return json.dumps(summary_result)

    def _has_test_files(self, context: Dict[str, Any]) -> bool:
        """Check if project has test files"""
        structure = context.get("structure", {})
        all_files = structure.get("all_files", [])
        for file_path in all_files:
            lower_path = file_path.lower()
            if "/test" in lower_path or "\\test" in lower_path or lower_path.startswith("test"):
                return True
        return False

    def _has_documentation_files(self, context: Dict[str, Any]) -> bool:
        """Check if project has documentation files"""
        structure = context.get("structure", {})
        search_stats = structure.get("search", {})

        # Gather all files from both 'all_files' and 'search.files'
        all_files = set(structure.get("all_files", []))
        files_from_search = set(search_stats.get("files", []))
        all_files_combined = all_files | files_from_search

        # Look for documentation patterns
        doc_patterns = [
            ".md",
            ".rst",
            ".txt",
            "readme",
            "changelog",
            "license",
            "docs/",
            "doc/",
            "documentation/",
            "api.md",
            "guide",
        ]

        # Check files and paths
        for file_path in all_files_combined:
            if any(pattern in file_path.lower() for pattern in doc_patterns):
                return True

        return False

    @handle_exceptions
    async def update_context(self, args: Dict[str, Any]) -> str:
        """Update project context with new information"""
        validate_dict_input(args, "update_context arguments")

        section = validate_string_input(args.get("section", ""), "section")
        updates = args.get("updates", {})
        validate_dict_input(updates, "updates")

        if not self.context_manager:
            return self.format_error("update_context", "Context manager not initialized")

        try:
            success = await self.context_manager.update_context({section: updates})
            await self.log_tool_usage("update_context", args, success)

            if success:
                return self.format_success(f"Updated {section} section")
            return self.format_error("update_context", f"Failed to update {section} section")
        except (ConnectionError, TimeoutError) as e:
            await self.log_tool_usage("update_context", args, False)
            return self.format_error("update_context", f"Connection error: {e}")
        except (ValueError, TypeError, AttributeError, RuntimeError, OSError) as e:
            await self.log_tool_usage("update_context", args, False)
            return self.format_error("update_context", str(e))

    @handle_exceptions
    async def add_note(self, args: Dict[str, Any]) -> str:
        """Add a note or memory about the project"""
        validate_dict_input(args, "add_note arguments")

        note_type = validate_string_input(args.get("note_type", ""), "note_type")
        content = validate_string_input(args.get("content", ""), "content")
        tags = args.get("tags", [])

        if not self.context_manager:
            return self.format_error("add_note", "Context manager not initialized")

        try:
            await self.context_manager.add_memory(memory_type=note_type, content=content, tags=tags)
            await self.log_tool_usage("add_note", args, True)
            return f"📝 Added {note_type} note: {content[:100]}..."
        except (ConnectionError, TimeoutError) as e:
            await self.log_tool_usage("add_note", args, False)
            return self.format_error("add_note", f"Connection error: {e}")
        except (ValueError, TypeError, AttributeError, RuntimeError, OSError) as e:
            await self.log_tool_usage("add_note", args, False)
            return self.format_error("add_note", str(e))

    async def _get_search_ai_insights(
        self, query: str, results: List[Dict[str, Any]], search_type: str
    ) -> Dict[str, Any]:
        """Get AI insights for search results"""
        if not self.is_ai_enabled() or not results:
            return {}

        try:
            search_context = {
                "query": query,
                "results": results[:5],  # Limit context size
                "search_type": search_type,
            }

            enhanced_results_list = await self.ai_enhancer.enhance_search_results(
                query, results, search_context
            )

            # Transform the list response into the expected dictionary format
            return {
                "enhanced_results": enhanced_results_list,
                "ai_insights": {
                    "query_intent": f"Search for {search_type} information about {query}",
                    "result_summary": f"Found {len(enhanced_results_list)} enhanced results",
                    "key_concepts": [query],  # Simplified
                },
                "related_searches": [f"Related to {query}"],  # Simplified
            }
        except (ConnectionError, TimeoutError) as e:
            logger.debug("AI enhancement failed (connection issue): %s", e)
            return {}
        except (ValueError, TypeError, AttributeError, RuntimeError, OSError) as e:
            logger.debug("AI enhancement failed for search: %s", e)
            return {}

    def _format_search_results(
        self, query: str, results: List[Dict[str, Any]], enhanced_results: Dict[str, Any]
    ) -> List[str]:
        """Format search results for display"""
        formatted_results = [
            f"🔍 **Search Results for:** {query}",
            self.format_ai_enhancement_status(),
            "",
        ]

        # Display basic results
        if results:
            formatted_results.append("## 📊 Semantic Search Results")
            for i, result in enumerate(results[:5], 1):
                file_path = result.get("file_path", "Unknown")
                score = result.get("score", 0)
                content_preview = result.get("content", "")[:200]

                formatted_results.append(
                    f"**{i}. {file_path}** (Score: {score:.2f})\n" f"   {content_preview}...\n"
                )

        # Add AI insights
        if enhanced_results.get("ai_insights"):
            ai_insights = enhanced_results["ai_insights"]

            if ai_insights.get("query_intent"):
                formatted_results.append("## 🤖 AI Search Analysis")
                formatted_results.append(f"**Query Intent**: {ai_insights['query_intent']}")

            if ai_insights.get("result_summary"):
                formatted_results.append(f"**Summary**: {ai_insights['result_summary']}")

            if ai_insights.get("key_concepts"):
                concepts = ", ".join(ai_insights["key_concepts"])
                formatted_results.append(f"**Key Concepts**: {concepts}")

        # Add AI search suggestions
        if enhanced_results.get("related_searches"):
            suggestions = enhanced_results["related_searches"]
            if suggestions:
                formatted_results.append("\n💡 **AI suggests also searching for:**")
                for suggestion in suggestions[:3]:
                    formatted_results.append(f"• {suggestion}")

        return formatted_results

    @handle_exceptions
    async def search_context(self, args: Dict[str, Any]) -> str:
        """Search through project context and memories with AI enhancement"""
        validate_dict_input(args, "search_context arguments")

        query = validate_string_input(args.get("query", ""), "query")
        search_type = args.get("search_type", "all")

        if not self.context_manager:
            return self.format_error("search_context", "Context manager not initialized")

        try:
            # Step 1: Basic search (always runs)
            results = await self.context_manager.semantic_search(query=query, top_k=10)

            # Step 2: AI enhancement (if enabled)
            enhanced_results: Dict[str, Any] = await self._get_search_ai_insights(
                query, results, search_type
            )

            await self.log_tool_usage("search_context", args, True)

            if not results and not enhanced_results.get("ai_insights"):
                return f"🔍 No results found for: {query}"

            # Step 3: Format output (adapts based on available data)
            formatted_results = self._format_search_results(query, results, enhanced_results)
            return "\n".join(formatted_results)

        except (ConnectionError, TimeoutError) as e:
            await self.log_tool_usage("search_context", args, False)
            return self.format_error("search_context", f"Connection error: {e}")
        except (ValueError, TypeError, AttributeError, RuntimeError, OSError) as e:
            await self.log_tool_usage("search_context", args, False)
            return self.format_error("search_context", str(e))
