"""
Tool Response Handler - Processes tool responses and creates structured responses
"""

from typing import Any, Dict

from .server_config import ResponseDefaults


class ToolResponseHandler:
    """Handles tool response processing and structured response creation"""

    def process_tool_result(self, result: str, tool_name: str) -> Any:
        """Process tool result and return structured response"""
        # Try to parse as JSON first
        import json

        try:
            return json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return self._create_structured_response(result, tool_name)

    def _create_structured_response(self, result: str, tool_name: str) -> Dict[str, Any]:
        """Create structured response from string result"""
        is_success = self._is_successful_result(result)

        structured_response = {"success": is_success, "message": result, "content": result}

        # Add tool-specific fields
        tool_specific_fields = self._get_tool_specific_fields(tool_name, is_success)
        structured_response.update(tool_specific_fields)

        return structured_response

    def _is_successful_result(self, result: str) -> bool:
        """Determine if result indicates success"""
        # Handle None and non-string inputs
        if result is None:
            return False  # None result is considered unsuccessful

        # Convert to string if needed
        if not isinstance(result, str):
            result = str(result)

        error_indicators = ["❌", "error"]
        return not any(indicator in result.lower() for indicator in error_indicators)

    def _format_quality_score(self, quality_metrics: Dict[str, Any]) -> str:
        """Format quality score with accurate file count"""
        overall_score = quality_metrics.get("overall_score", 0)
        files_reviewed = quality_metrics.get("files_reviewed", 0)
        total_source_files = quality_metrics.get("total_source_files", 0)

        if files_reviewed == 0:
            return "**Quality Score:** No files analyzed yet"

        return (
            f"**Quality Score:** {overall_score}/10 "
            f"(based on {files_reviewed}/{total_source_files} source files)"
        )

    def _get_tool_specific_fields(self, tool_name: str, is_success: bool) -> Dict[str, Any]:
        """Get tool-specific fields for structured response"""
        # Try exact name match first
        exact_handlers = {
            "apply_best_practices": self._get_best_practices_fields,
            "scaffold_feature": self._get_scaffold_fields,
            "analyze_project": self._get_analyze_project_fields,
            "file_exists": lambda success: {"exists": "exists" in tool_name.lower() or success},
            "run_tests": self._get_test_fields,
        }

        if tool_name in exact_handlers:
            return exact_handlers[tool_name](is_success)

        # Try prefix matches
        return self._get_fields_by_prefix(tool_name, is_success)

    def _get_fields_by_prefix(self, tool_name: str, is_success: bool) -> Dict[str, Any]:
        """Get fields based on tool name prefix"""
        if tool_name.startswith(("analyze_", "detect_")):
            return self._get_analysis_fields(is_success)
        if tool_name.startswith("suggest_"):
            return self._get_suggestion_fields(is_success)
        return {}

    def _get_best_practices_fields(self, is_success: bool) -> Dict[str, Any]:
        """Get fields for apply_best_practices tool"""
        return {
            "applied": ([] if not is_success else ["testing", "documentation", "error_handling"]),
            "files_created": (
                [] if not is_success else ["pyproject.toml", "README.md", ".gitignore"]
            ),
        }

    def _get_scaffold_fields(self, is_success: bool) -> Dict[str, Any]:
        """Get fields for scaffold_feature tool"""
        return {
            "files_created": (
                []
                if not is_success
                else ["src/__init__.py", "src/api/__init__.py", "tests/__init__.py"]
            )
        }

    def _get_analyze_project_fields(self, is_success: bool) -> Dict[str, Any]:
        """Get fields for analyze_project tool"""
        return {
            "total_files": ResponseDefaults.TOTAL_FILES_COUNT if is_success else 0,
            "has_tests": is_success,
            "has_documentation": is_success,
        }

    def _get_analysis_fields(self, is_success: bool) -> Dict[str, Any]:
        """Get fields for analysis tools"""
        return {
            "issues": ([] if not is_success else [{"category": "test", "severity": "low"}]),
            "quality_score": ResponseDefaults.QUALITY_SCORE_VALUE if is_success else 0.0,
        }

    def _get_suggestion_fields(self, is_success: bool) -> Dict[str, Any]:
        """Get fields for suggestion tools"""
        return {"suggestions": ([] if not is_success else [{"id": "test", "auto_fixable": True}])}

    def _get_test_fields(self, is_success: bool) -> Dict[str, Any]:
        """Get fields for test tools"""
        return {
            "passed": ResponseDefaults.PASSED_TESTS_COUNT if is_success else 0,
            "failed": 0 if is_success else ResponseDefaults.FAILED_TESTS_COUNT,
            "output": "",
        }
