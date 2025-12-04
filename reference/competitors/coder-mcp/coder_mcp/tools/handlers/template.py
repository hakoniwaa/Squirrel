#!/usr/bin/env python3
"""
Template and scaffolding tool handler
Handles feature scaffolding, best practices application, and improvement roadmap generation
"""

import logging
from typing import Any, Dict, List, cast

from mcp.types import Tool

from ...security.exceptions import handle_exceptions
from ...security.validators import validate_dict_input, validate_string_input
from ...template_manager import TemplateManager
from ..base_handler import BaseHandler

logger = logging.getLogger(__name__)


class TemplateHandler(BaseHandler):
    """Template and scaffolding operations"""

    def __init__(self, config_manager, context_manager):
        super().__init__(config_manager, context_manager)
        self.template_manager = TemplateManager(self.workspace_root)

    @staticmethod
    def get_tools() -> List[Tool]:
        """Get template tools"""
        return [
            Tool(
                name="scaffold_feature",
                description="Generate boilerplate code for common features using templates",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "feature_type": {
                            "type": "string",
                            "enum": [
                                "api_endpoint",
                                "database_model",
                                "test_suite",
                                "cli_command",
                                "react_component",
                                "service_class",
                            ],
                            "description": "Type of feature to scaffold",
                        },
                        "name": {
                            "type": "string",
                            "description": (
                                "Name for the feature (e.g., 'UserAuth', 'PaymentService')"
                            ),
                        },
                        "options": {"type": "object", "description": "Feature-specific options"},
                    },
                    "required": ["feature_type", "name"],
                },
            ),
            Tool(
                name="apply_best_practices",
                description="Apply language-specific best practices and patterns to your project",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "enum": ["python", "javascript", "typescript", "auto"],
                            "default": "auto",
                            "description": ("Programming language (auto-detect if not specified)"),
                        },
                        "practices": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "testing",
                                    "documentation",
                                    "error_handling",
                                    "logging",
                                    "type_hints",
                                    "linting",
                                ],
                            },
                            "default": ["testing", "documentation", "error_handling"],
                        },
                        "create_files": {
                            "type": "boolean",
                            "default": True,
                            "description": "Create missing configuration files",
                        },
                    },
                },
            ),
            Tool(
                name="generate_improvement_roadmap",
                description=(
                    "Generate a personalized improvement roadmap " "based on context and history"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "focus_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": ["quality", "performance", "security", "maintainability"],
                        },
                        "time_frame": {
                            "type": "string",
                            "enum": ["immediate", "short_term", "long_term"],
                            "default": "short_term",
                        },
                    },
                },
            ),
        ]

    async def _perform_basic_scaffolding(
        self, feature_type: str, name: str, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform basic feature scaffolding"""
        try:
            logger.debug(
                f"_perform_basic_scaffolding called with: feature_type={feature_type}, "
                f"name={name}, options={options}"
            )
            logger.debug(
                f"Types: feature_type={type(feature_type)}, name={type(name)}, "
                f"options={type(options)}"
            )

            result = await self.template_manager.scaffold_feature(
                feature_type=feature_type,
                name=name,
                options=options,
            )

            logger.debug(f"template_manager.scaffold_feature returned: {result}")
            return cast(Dict[str, Any], result)
        except Exception as e:
            logger.error(f"Error in _perform_basic_scaffolding: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def _enhance_scaffold_with_ai(
        self, result: Dict[str, Any], feature_type: str, name: str
    ) -> Dict[str, Any]:
        """Enhance scaffolding result with AI if available"""
        if not self.is_ai_enabled() or not result.get("success") or not result.get("files_created"):
            return result

        try:
            context = await self.context_manager.load_context() if self.context_manager else {}

            scaffold_context = {
                "feature_type": feature_type,
                "name": name,
                "files_created": result["files_created"],
                "project_context": {
                    "structure": context.get("structure", {}),
                    "patterns": context.get("patterns", {}),
                    "dependencies": context.get("dependencies", {}),
                },
            }

            enhanced_output = await self.ai_enhancer.enhance_scaffold_output(
                result, scaffold_context
            )
            return cast(Dict[str, Any], enhanced_output)  # type: ignore[no-any-return]
        except (ConnectionError, TimeoutError) as e:
            logger.debug("AI enhancement failed (connection issue): %s", e)
            return result
        except (ValueError, TypeError, AttributeError, RuntimeError, OSError) as e:
            logger.debug("AI enhancement failed for scaffolding: %s", e)
            return result

    def _format_scaffold_result(
        self, enhanced_result: Dict[str, Any], feature_type: str, name: str
    ) -> str:
        """Format scaffolding result for display"""
        files_created = enhanced_result.get("files_created", [])
        message = self.format_success("scaffold_feature", f"Scaffolded {feature_type}: {name}")

        # Add AI enhancement status
        message += f"\n{self.format_ai_enhancement_status()}"

        if files_created:
            file_list = "\n".join(f"  📄 {file}" for file in files_created)
            message += f"\n**Files Created:**\n{file_list}"

        # Add AI-enhanced recommendations if available
        if enhanced_result.get("ai_recommendations"):
            recommendations = enhanced_result["ai_recommendations"]
            message += "\n\n## 🤖 AI Recommendations"

            if recommendations.get("next_steps"):
                message += "\n**Next Steps:**"
                for step in recommendations["next_steps"][:3]:
                    message += f"\n  • {step}"

            if recommendations.get("improvements"):
                message += "\n**Suggested Improvements:**"
                for improvement in recommendations["improvements"][:3]:
                    message += f"\n  • {improvement}"

            if recommendations.get("patterns_to_follow"):
                patterns = ", ".join(recommendations["patterns_to_follow"])
                message += f"\n**Consider Patterns**: {patterns}"

        return message

    async def _index_created_files(self, files_created) -> None:
        """Index newly created files in the context manager"""
        if self.context_manager and files_created:
            for item in files_created:
                # Handle both string paths and dict file info
                if isinstance(item, dict):
                    file_path = item.get("file_path", "")
                else:
                    file_path = item

                if file_path:
                    full_path = self.workspace_root / file_path
                    if full_path.exists():
                        await self.context_manager.index_file(full_path)

    @handle_exceptions
    async def scaffold_feature(self, args: Dict[str, Any]) -> str:
        """Generate boilerplate code for common features with AI enhancement"""
        validate_dict_input(args, "scaffold_feature arguments")

        feature_type = validate_string_input(args.get("feature_type", ""), "feature_type")
        name = validate_string_input(args.get("name", ""), "name")
        options = args.get("options", {})

        try:
            # Step 1: Basic scaffolding (always runs)
            result = await self._perform_basic_scaffolding(feature_type, name, options)

            # Step 2: AI enhancement (if enabled and successful)
            enhanced_result = await self._enhance_scaffold_with_ai(result, feature_type, name)

            await self.log_tool_usage(
                "scaffold_feature", args, enhanced_result.get("success", False)
            )

            if enhanced_result.get("success"):
                message = self._format_scaffold_result(enhanced_result, feature_type, name)

                # Update context with new files
                files_created = enhanced_result.get("files_created", [])
                await self._index_created_files(files_created)

                return message

            error_msg = enhanced_result.get("error", "Unknown error")
            return self.format_error(
                "scaffold_feature", f"Failed to scaffold {feature_type}: {error_msg}"
            )

        except (FileNotFoundError, PermissionError) as e:
            await self.log_tool_usage("scaffold_feature", args, False)
            return self.format_error("scaffold_feature", f"File operation error: {e}")
        except (ValueError, TypeError, AttributeError, RuntimeError, OSError) as e:
            await self.log_tool_usage("scaffold_feature", args, False)
            return self.format_error("scaffold_feature", str(e))

    @handle_exceptions
    async def apply_best_practices(self, args: Dict[str, Any]) -> str:
        """Apply language-specific best practices"""
        validate_dict_input(args, "apply_best_practices arguments")

        language = args.get("language", "auto")
        practices = args.get("practices", ["testing", "documentation", "error_handling"])
        create_files = args.get("create_files", True)

        try:
            result = await self.template_manager.apply_best_practices(
                language=language,
                practices=practices,
                create_files=create_files,
            )

            applied = result.get("applied", [])
            files_created = result.get("files_created", [])

            await self.log_tool_usage("apply_best_practices", args, len(applied) > 0)

            result_parts = [
                self.format_success(
                    "apply_best_practices", f"Applied best practices for {language}"
                )
            ]

            if applied:
                result_parts.append("**Practices Applied:**")
                result_parts.extend(f"  ✓ {practice}" for practice in applied)

            if files_created:
                result_parts.append("**Files Created:**")
                result_parts.extend(f"  📄 {file}" for file in files_created)

                # Update context with new files
                await self._index_created_files(files_created)

            if not applied and not files_created:
                result_parts.append(
                    "No changes were needed - project already follows the specified best practices!"
                )

            return "\n".join(result_parts)

        except (FileNotFoundError, PermissionError) as e:
            await self.log_tool_usage("apply_best_practices", args, False)
            return self.format_error("apply_best_practices", f"File operation error: {e}")
        except (ValueError, TypeError, AttributeError, RuntimeError, OSError) as e:
            await self.log_tool_usage("apply_best_practices", args, False)
            return self.format_error("apply_best_practices", str(e))

    async def _get_roadmap_ai_enhancement(
        self, roadmap: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI enhancement for roadmap if enabled"""
        if not self.is_ai_enabled():
            return roadmap

        try:
            codebase_summary = {
                "structure": context.get("structure", {}),
                "quality_metrics": context.get("quality_metrics", {}),
                "patterns": context.get("patterns", {}),
                "dependencies": context.get("dependencies", {}),
                "known_issues": context.get("known_issues", []),
            }

            enhanced_roadmap = await self.ai_enhancer.enhance_improvement_roadmap(
                roadmap, codebase_summary
            )
            return cast(Dict[str, Any], enhanced_roadmap)
        except (ConnectionError, TimeoutError) as e:
            logger.debug("AI enhancement failed (connection issue): %s", e)
            return roadmap
        except (ValueError, TypeError, AttributeError, RuntimeError, OSError) as e:
            logger.debug("AI enhancement failed for roadmap: %s", e)
            return roadmap

    def _format_roadmap_priorities(
        self, enhanced_roadmap: Dict[str, Any], result_parts: List[str]
    ) -> None:
        """Format roadmap priorities for display"""
        priority_order = ["high", "medium", "low"]

        for priority in priority_order:
            items = enhanced_roadmap.get(priority, [])
            if items:
                result_parts.append(f"**{priority.upper()} Priority:**")
                for item in items[:5]:  # Limit items per priority
                    result_parts.append(f"  • {item}")

                if len(items) > 5:
                    result_parts.append(f"  ... and {len(items) - 5} more items")

                result_parts.append("")  # Add spacing

    def _add_ai_strategic_insights(
        self, enhanced_roadmap: Dict[str, Any], result_parts: List[str]
    ) -> None:
        """Add AI strategic insights to roadmap"""
        if not enhanced_roadmap.get("ai_strategic_insights"):
            return

        ai_insights = enhanced_roadmap["ai_strategic_insights"]
        result_parts.append("## 🤖 AI Strategic Analysis")

        if ai_insights.get("priority_analysis"):
            result_parts.append(f"**Priority Analysis**: {ai_insights['priority_analysis']}")

        if ai_insights.get("risk_assessment"):
            result_parts.append(f"**Risk Assessment**: {ai_insights['risk_assessment']}")

        if ai_insights.get("effort_estimation"):
            result_parts.append(f"**Effort Estimation**: {ai_insights['effort_estimation']}")

        if ai_insights.get("recommended_order"):
            recommended = ai_insights["recommended_order"]
            if isinstance(recommended, list) and recommended:
                result_parts.append("**Recommended Implementation Order:**")
                for i, step in enumerate(recommended[:5], 1):
                    result_parts.append(f"  {i}. {step}")

    def _add_roadmap_summary(
        self, enhanced_roadmap: Dict[str, Any], result_parts: List[str]
    ) -> None:
        """Add summary and next steps to roadmap"""
        priority_order = ["high", "medium", "low"]
        total_items = sum(len(enhanced_roadmap.get(p, [])) for p in priority_order)

        if total_items > 0:
            result_parts.append(f"**Summary:** {total_items} improvement opportunities identified")
            result_parts.append("**Next Steps:** Start with HIGH priority items for maximum impact")
        else:
            result_parts.append(
                "**Summary:** Your project appears to be in excellent shape! "
                "No major improvements needed."
            )

    @handle_exceptions
    async def generate_improvement_roadmap(self, args: Dict[str, Any]) -> str:
        """Generate a personalized improvement roadmap with AI strategic insights"""
        validate_dict_input(args, "generate_improvement_roadmap arguments")

        focus_areas = args.get(
            "focus_areas", ["quality", "performance", "security", "maintainability"]
        )
        time_frame = args.get("time_frame", "short_term")

        try:
            # Get current context for analysis
            context = await self.context_manager.load_context()

            # Step 1: Basic roadmap generation (always runs)
            roadmap = await self.template_manager.generate_improvement_roadmap(
                context=context, focus_areas=focus_areas, time_frame=time_frame
            )

            # Step 2: AI enhancement (if enabled)
            enhanced_roadmap = await self._get_roadmap_ai_enhancement(roadmap, context)

            await self.log_tool_usage("generate_improvement_roadmap", args, True)

            result_parts = [
                f"🗺️  **Improvement Roadmap ({time_frame})**",
                f"**Focus Areas:** {', '.join(focus_areas)}",
                self.format_ai_enhancement_status(),
                "",
            ]

            # Format priorities
            self._format_roadmap_priorities(enhanced_roadmap, result_parts)

            # Add AI strategic insights
            self._add_ai_strategic_insights(enhanced_roadmap, result_parts)

            # Add summary and next steps
            self._add_roadmap_summary(enhanced_roadmap, result_parts)

            return "\n".join(result_parts)

        except (ConnectionError, TimeoutError) as e:
            await self.log_tool_usage("generate_improvement_roadmap", args, False)
            return self.format_error("generate_improvement_roadmap", f"Connection error: {e}")
        except (ValueError, TypeError, AttributeError, RuntimeError, OSError) as e:
            await self.log_tool_usage("generate_improvement_roadmap", args, False)
            return self.format_error("generate_improvement_roadmap", str(e))
