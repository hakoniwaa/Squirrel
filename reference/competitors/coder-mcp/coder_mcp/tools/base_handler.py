#!/usr/bin/env python3
"""
Base handler class for all tool handlers
Provides common functionality and interface
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from mcp.types import Tool

from ..ai.enhancers import EnhancerOrchestrator
from ..context.manager import ContextManager
from ..core import ConfigurationManager


class BaseHandler(ABC):
    """Base class for all tool handlers"""

    def __init__(self, config_manager: ConfigurationManager, context_manager: ContextManager):
        self.config_manager = config_manager
        self.context_manager = context_manager
        self.workspace_root = context_manager.workspace_root if context_manager else Path.cwd()

        # Use new modular AI enhancer orchestrator
        self.ai_enhancer = EnhancerOrchestrator(config_manager)

    @staticmethod
    @abstractmethod
    def get_tools() -> List[Tool]:
        """Get the tools provided by this handler"""

    def get_handler_name(self) -> str:
        """Get the name of this handler"""
        return self.__class__.__name__

    def get_tool_names(self) -> List[str]:
        """Get the names of all tools provided by this handler"""
        return [tool.name for tool in self.get_tools()]

    async def validate_context(self) -> bool:
        """Validate that the handler has required context"""
        if not self.context_manager:
            return False
        return True

    def format_error(self, operation: str, error: str) -> str:
        """Format error messages consistently"""
        return f"❌ Error in {operation}: {error}"

    def format_success(self, operation: str, details: str = "") -> str:
        """Format success messages consistently"""
        message = f"✅ {operation} completed successfully"
        if details:
            message += f": {details}"
        return message

    def format_info(self, title: str, content: str) -> str:
        """Format informational messages consistently"""
        return f"ℹ️  **{title}**\n{content}"

    def format_warning(self, message: str) -> str:
        """Format warning messages consistently"""
        return f"⚠️  {message}"

    def truncate_content(self, content: str, max_length: int = 2000) -> str:
        """Truncate content to a reasonable length for display"""
        if len(content) <= max_length:
            return content

        return content[:max_length] + f"\n... (truncated, {len(content)} total characters)"

    def safe_get_path(self, path_str: str) -> Path:
        """Safely resolve a path relative to workspace root"""
        if not path_str:
            return self.workspace_root

        path = Path(path_str)
        if path.is_absolute():
            # Ensure the absolute path is within workspace
            try:
                path.relative_to(self.workspace_root)
                return path
            except ValueError:
                # Path is outside workspace, use relative from workspace
                return self.workspace_root / path.name
        else:
            # Relative path, resolve from workspace root
            return self.workspace_root / path

    async def log_tool_usage(self, tool_name: str, args: Dict[str, Any], success: bool = True):
        """Log tool usage for analytics and debugging"""
        if self.context_manager:
            await self.context_manager.track_tool_usage(
                tool_name=tool_name, args=args, success=success, handler=self.get_handler_name()
            )

    def is_ai_enabled(self) -> bool:
        """Check if AI enhancement is enabled"""
        return self.ai_enhancer.is_enabled()

    def format_ai_insights(self, ai_insights: Dict[str, Any]) -> str:
        """Format AI insights for display"""
        if not ai_insights:
            return ""

        output = "\n## 🤖 AI Insights\n"

        # Security risks
        if "security_risks" in ai_insights and ai_insights["security_risks"]:
            output += f"- **Security Risks**: {len(ai_insights['security_risks'])} found\n"
            for risk in ai_insights["security_risks"][:3]:  # Show top 3
                output += f"  • {risk.get('description', 'Security concern')}\n"

        # Performance insights
        if "performance_insights" in ai_insights and ai_insights["performance_insights"]:
            output += (
                f"- **Performance Issues**: {len(ai_insights['performance_insights'])} found\n"
            )
            for insight in ai_insights["performance_insights"][:3]:  # Show top 3
                output += f"  • {insight.get('description', 'Performance concern')}\n"

        # Code quality score
        if "code_quality_score" in ai_insights:
            score = ai_insights["code_quality_score"]
            output += f"- **Code Quality Score**: {score}/10\n"

        # Architectural suggestions
        if "architectural_suggestions" in ai_insights and ai_insights["architectural_suggestions"]:
            output += (
                f"- **Architecture Suggestions**: "
                f"{len(ai_insights['architectural_suggestions'])} recommendations\n"
            )
            for suggestion in ai_insights["architectural_suggestions"][:2]:  # Show top 2
                output += f"  • {suggestion.get('description', 'Architectural improvement')}\n"

        return output

    def format_ai_search_suggestions(self, suggestions: List[str]) -> str:
        """Format AI search suggestions"""
        if not suggestions:
            return ""

        output = "\n💡 **AI suggests also searching for:**\n"
        for suggestion in suggestions:
            output += f"• {suggestion}\n"

        return output

    def format_ai_enhancement_status(self) -> str:
        """Format AI enhancement status for debugging"""
        if self.is_ai_enabled():
            return "🤖 AI Enhancement: **Enabled**"
        else:
            return "🤖 AI Enhancement: **Disabled**"
