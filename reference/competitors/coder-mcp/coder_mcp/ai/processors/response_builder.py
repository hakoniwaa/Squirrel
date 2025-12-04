#!/usr/bin/env python3
"""
Main Response Builder
Orchestrates AI response processing using specialized processors
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from ...code_analyzer import CodeAnalyzer
from .base import ProcessedResponse
from .change_processor import ChangeExtractor
from .code_processor import CodeExtractor, SyntaxValidator
from .markdown_processor import MarkdownProcessor

logger = logging.getLogger(__name__)


class ResponseProcessor:
    """Process and enhance AI responses for better integration"""

    def __init__(
        self, code_analyzer: Optional[CodeAnalyzer] = None, workspace_root: Optional[Path] = None
    ):
        workspace_root = workspace_root or Path.cwd()
        self.code_analyzer = code_analyzer or CodeAnalyzer(workspace_root)

        # Initialize specialized processors
        self.code_extractor = CodeExtractor()
        self.syntax_validator = SyntaxValidator()
        self.change_extractor = ChangeExtractor()
        self.markdown_processor = MarkdownProcessor()

    async def process_response(
        self,
        response: str,
        response_type: str = "general",
        context: Optional[Dict[str, Any]] = None,
    ) -> ProcessedResponse:
        """
        Process AI response based on type

        Response types:
        - general: General text response
        - code_review: Code review with suggestions
        - code_generation: Generated code
        - analysis: Code analysis results
        - documentation: Generated documentation
        - debug: Debugging information
        """
        processor_map = {
            "general": self._process_general_response,
            "code_review": self._process_code_review_response,
            "code_generation": self._process_code_generation_response,
            "analysis": self._process_analysis_response,
            "documentation": self._process_documentation_response,
            "debug": self._process_debug_response,
        }

        processor = processor_map.get(response_type, self._process_general_response)

        try:
            return await processor(response, context or {})
        except Exception as e:
            logger.error(f"Error processing {response_type} response: {e}")
            return ProcessedResponse(
                content=response,
                warnings=[f"Failed to fully process response: {str(e)}"],
            )

    # ============================================================
    # Response Type Processors
    # ============================================================

    async def _process_general_response(
        self, response: str, context: Dict[str, Any]
    ) -> ProcessedResponse:
        """Process general text response"""
        code_blocks = self.code_extractor.extract_code_blocks(response)

        # Extract any JSON data
        structured_data = self._extract_json_data(response)

        # Extract action items (look for bullet points with action verbs)
        action_items = self._extract_action_items(response)

        return ProcessedResponse(
            content=response,
            code_blocks=code_blocks,
            structured_data=structured_data,
            action_items=action_items,
            metadata={"response_type": "general"},
        )

    async def _process_code_review_response(
        self, response: str, context: Dict[str, Any]
    ) -> ProcessedResponse:
        """Process code review response"""
        processed = await self._process_general_response(response, context)

        # Extract specific review sections
        issues = self._extract_review_issues(response)
        suggestions = self._extract_review_suggestions(response)

        # Parse severity levels
        critical_issues = [i for i in issues if i.get("severity") == "critical"]

        processed.structured_data = {
            "issues": issues,
            "suggestions": suggestions,
            "critical_count": len(critical_issues),
            "total_issues": len(issues),
        }

        # Convert to action items
        for issue in critical_issues:
            processed.action_items.append(
                {
                    "type": "fix_issue",
                    "priority": "high",
                    "description": issue.get("description"),
                    "location": issue.get("location"),
                }
            )

        processed.metadata["response_type"] = "code_review"
        return processed

    async def _process_code_generation_response(
        self, response: str, context: Dict[str, Any]
    ) -> ProcessedResponse:
        """Process code generation response"""
        code_blocks = self.code_extractor.extract_code_blocks(response)

        # Validate generated code
        validation_results = []
        for block in code_blocks:
            if block.language in ["python", "javascript", "typescript"]:
                is_valid, errors = await self.syntax_validator.validate_syntax(
                    block.code, block.language
                )
                validation_results.append(
                    {
                        "language": block.language,
                        "valid": is_valid,
                        "errors": errors,
                    }
                )

        # Extract implementation notes
        notes = self._extract_implementation_notes(response)

        # Extract test examples if present
        test_blocks = [b for b in code_blocks if "test" in b.code.lower()]

        return ProcessedResponse(
            content=response,
            code_blocks=code_blocks,
            structured_data={
                "validation_results": validation_results,
                "implementation_notes": notes,
                "has_tests": len(test_blocks) > 0,
                "test_count": len(test_blocks),
            },
            metadata={"response_type": "code_generation"},
        )

    async def _process_analysis_response(
        self, response: str, context: Dict[str, Any]
    ) -> ProcessedResponse:
        """Process code analysis response"""
        # Try to parse as JSON first
        try:
            # Look for JSON block
            json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group(1))
            else:
                # Try parsing the whole response as JSON
                analysis_data = json.loads(response)

            # Extract key metrics
            metrics = analysis_data.get("metrics", {})
            issues = analysis_data.get("issues", [])
            suggestions = analysis_data.get("suggestions", [])

            # Create action items from high-priority issues
            action_items = []
            for issue in issues:
                if issue.get("severity") in ["high", "critical"]:
                    action_items.append(
                        {
                            "type": "fix_issue",
                            "priority": issue.get("severity"),
                            "description": issue.get("description"),
                            "location": issue.get("location"),
                            "category": issue.get("type"),
                        }
                    )

            return ProcessedResponse(
                content=self._format_analysis_summary(analysis_data),
                structured_data=analysis_data,
                action_items=action_items,
                metadata={
                    "response_type": "analysis",
                    "metrics": metrics,
                    "issue_count": len(issues),
                    "suggestion_count": len(suggestions),
                },
            )

        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to text parsing
            logger.warning(f"Failed to parse analysis as JSON: {e}")
            return await self._process_general_response(response, context)

    async def _process_documentation_response(
        self, response: str, context: Dict[str, Any]
    ) -> ProcessedResponse:
        """Process documentation response"""
        # Extract sections using markdown processor
        sections = self.markdown_processor.extract_sections(response)

        # Extract code examples
        code_blocks = self.code_extractor.extract_code_blocks(response)
        examples = self.markdown_processor.extract_code_examples(response)

        # Extract API endpoints if present
        endpoints = self._extract_api_endpoints(response)

        return ProcessedResponse(
            content=response,
            code_blocks=code_blocks,
            structured_data={
                "sections": sections,
                "examples": len(examples),
                "endpoints": endpoints,
            },
            metadata={
                "response_type": "documentation",
                "has_examples": len(examples) > 0,
                "has_api_docs": len(endpoints) > 0,
            },
        )

    async def _process_debug_response(
        self, response: str, context: Dict[str, Any]
    ) -> ProcessedResponse:
        """Process debugging response"""
        processed = await self._process_general_response(response, context)

        # Extract debugging steps
        debug_steps = self._extract_debug_steps(response)

        # Extract root cause if identified
        root_cause = self._extract_root_cause(response)

        # Extract fix suggestions
        fixes = self._extract_fix_suggestions(response)

        processed.structured_data = {
            "debug_steps": debug_steps,
            "root_cause": root_cause,
            "fixes": fixes,
        }

        # Create action items for fixes
        for i, fix in enumerate(fixes):
            processed.action_items.append(
                {
                    "type": "apply_fix",
                    "priority": "high" if i == 0 else "medium",
                    "description": fix.get("description"),
                    "code": fix.get("code"),
                }
            )

        processed.metadata["response_type"] = "debug"
        return processed

    # ============================================================
    # Extraction Utilities
    # ============================================================

    def _extract_json_data(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON data from response"""
        # Look for JSON blocks
        json_pattern = r"```json\s*(.*?)\s*```"
        match = re.search(json_pattern, text, re.DOTALL)

        if match:
            try:
                return cast(Dict[str, Any], json.loads(match.group(1)))
            except json.JSONDecodeError:
                logger.warning("Found JSON block but failed to parse")
                return None

        # Try to find inline JSON
        try:
            # Look for JSON-like structures
            json_start = text.find("{")
            json_end = text.rfind("}")
            if json_start != -1 and json_end != -1 and json_end > json_start:
                potential_json = text[json_start : json_end + 1]
                return cast(Dict[str, Any], json.loads(potential_json))
        except json.JSONDecodeError:
            pass

        return None

    def _extract_action_items(self, text: str) -> List[Dict[str, Any]]:
        """Extract action items from text"""
        action_items = []

        # Action verbs that indicate tasks
        action_verbs = [
            "implement",
            "add",
            "create",
            "update",
            "fix",
            "remove",
            "refactor",
            "optimize",
            "test",
            "document",
            "review",
            "check",
            "validate",
            "ensure",
            "verify",
            "integrate",
            "configure",
            "deploy",
        ]

        # Look for bullet points with action verbs
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith(("-", "*", "•", "□", "☐", "1.", "2.", "3.")):
                # Remove bullet point
                content = re.sub(r"^[-*•□☐\d.]+\s*", "", line).strip()

                # Check if it contains action verb
                lower_content = content.lower()
                for verb in action_verbs:
                    if verb in lower_content:
                        action_items.append(
                            {
                                "type": "task",
                                "description": content,
                                "verb": verb,
                                "priority": self._determine_priority(content),
                            }
                        )
                        break

        return action_items

    def _extract_review_issues(self, text: str) -> List[Dict[str, Any]]:
        """Extract issues from code review"""
        issues = []

        # Patterns for issues
        severity_keywords = {
            "critical": ["critical", "severe", "must fix", "security risk", "vulnerability"],
            "high": ["high", "important", "should fix", "bug", "error"],
            "medium": ["medium", "consider", "could", "improve"],
            "low": ["low", "minor", "style", "convention", "nitpick"],
        }

        lines = text.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()

            # Check if this is an issue section
            if any(keyword in line.lower() for keyword in ["issue", "problem", "error", "bug"]):
                current_section = "issues"

            # Extract issues from bullet points
            if current_section == "issues" and line.startswith(("-", "*", "•")):
                content = re.sub(r"^[-*•]+\s*", "", line).strip()

                # Determine severity
                severity = "medium"  # default
                lower_content = content.lower()
                for sev, keywords in severity_keywords.items():
                    if any(keyword in lower_content for keyword in keywords):
                        severity = sev
                        break

                # Extract location if present
                location_match = re.search(r"(?:line|at)\s+(\d+)", content, re.IGNORECASE)
                location = location_match.group(1) if location_match else None

                issues.append(
                    {
                        "description": content,
                        "severity": severity,
                        "location": location,
                        "type": self._categorize_issue(content),
                    }
                )

        return issues

    def _extract_review_suggestions(self, text: str) -> List[Dict[str, Any]]:
        """Extract suggestions from code review"""
        suggestions = []

        lines = text.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()

            # Check if this is a suggestions section
            if any(keyword in line.lower() for keyword in ["suggest", "recommend", "consider"]):
                current_section = "suggestions"

            # Extract suggestions from bullet points
            if current_section == "suggestions" and line.startswith(("-", "*", "•")):
                content = re.sub(r"^[-*•]+\s*", "", line).strip()

                suggestions.append(
                    {
                        "description": content,
                        "category": self._categorize_suggestion(content),
                        "priority": self._determine_priority(content),
                    }
                )

        return suggestions

    def _extract_implementation_notes(self, text: str) -> List[str]:
        """Extract implementation notes from response"""
        notes = []

        # Look for notes, todos, or implementation details
        note_patterns = [
            r"(?:Note|TODO|FIXME|Implementation):\s*(.+)",
            r"(?:Remember|Important):\s*(.+)",
            r"(?:Warning|Caution):\s*(.+)",
        ]

        for pattern in note_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                notes.append(match.group(1).strip())

        return notes

    def _extract_api_endpoints(self, text: str) -> List[Dict[str, Any]]:
        """Extract API endpoints from documentation"""
        endpoints = []

        # Look for API endpoint patterns
        endpoint_pattern = r"(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s]+)"
        matches = re.finditer(endpoint_pattern, text, re.IGNORECASE)

        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)

            endpoints.append(
                {
                    "method": method,
                    "path": path,
                    "description": "",  # Could be enhanced to extract descriptions
                }
            )

        return endpoints

    def _extract_debug_steps(self, text: str) -> List[str]:
        """Extract debugging steps from response"""
        steps = []

        # Look for numbered steps or bullet points in debug context
        lines = text.split("\n")
        in_steps_section = False

        for line in lines:
            line = line.strip()

            # Check if we're in a steps section
            if any(keyword in line.lower() for keyword in ["step", "debug", "troubleshoot"]):
                in_steps_section = True

            # Extract steps
            if in_steps_section and re.match(r"^\d+\.|^[-*•]", line):
                step_content = re.sub(r"^\d+\.|-*•", "", line).strip()
                if step_content:
                    steps.append(step_content)

        return steps

    def _extract_root_cause(self, text: str) -> Optional[str]:
        """Extract root cause from debug response"""
        # Look for root cause indicators
        root_cause_patterns = [
            r"(?:root cause|caused by|due to):\s*(.+)",
            r"(?:the problem is|issue is):\s*(.+)",
            r"(?:main cause|primary cause):\s*(.+)",
        ]

        for pattern in root_cause_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_fix_suggestions(self, text: str) -> List[Dict[str, Any]]:
        """Extract fix suggestions from debug response"""
        fixes = []

        # Look for fix patterns
        fix_patterns = [
            r"(?:fix|solution|resolve):\s*(.+)",
            r"(?:try|attempt):\s*(.+)",
            r"(?:change|modify|update):\s*(.+)",
        ]

        for pattern in fix_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                description = match.group(1).strip()

                fixes.append(
                    {
                        "description": description,
                        "category": self._categorize_fix(description),
                        "code": self._extract_code_from_fix(description),
                    }
                )

        return fixes

    def _extract_code_from_fix(self, description: str) -> Optional[str]:
        """Extract code from fix description"""
        # Look for code in backticks
        code_match = re.search(r"`([^`]+)`", description)
        if code_match:
            return code_match.group(1)
        return None

    # ============================================================
    # Categorization and Utility Methods
    # ============================================================

    def _determine_priority(self, text: str) -> str:
        """Determine priority level from text"""
        lower_text = text.lower()

        if any(keyword in lower_text for keyword in ["critical", "urgent", "must", "security"]):
            return "high"
        elif any(keyword in lower_text for keyword in ["should", "important", "recommended"]):
            return "medium"
        else:
            return "low"

    def _categorize_suggestion(self, text: str) -> str:
        """Categorize suggestion type"""
        lower_text = text.lower()

        if any(keyword in lower_text for keyword in ["performance", "speed", "optimize"]):
            return "performance"
        elif any(keyword in lower_text for keyword in ["security", "auth", "validate"]):
            return "security"
        elif any(keyword in lower_text for keyword in ["test", "coverage"]):
            return "testing"
        elif any(keyword in lower_text for keyword in ["style", "format", "convention"]):
            return "style"
        else:
            return "general"

    def _categorize_fix(self, text: str) -> str:
        """Categorize fix type"""
        lower_text = text.lower()

        if any(keyword in lower_text for keyword in ["import", "module", "dependency"]):
            return "dependency"
        elif any(keyword in lower_text for keyword in ["syntax", "typo", "spelling"]):
            return "syntax"
        elif any(keyword in lower_text for keyword in ["logic", "algorithm", "condition"]):
            return "logic"
        elif any(keyword in lower_text for keyword in ["config", "setting", "parameter"]):
            return "configuration"
        else:
            return "general"

    def _categorize_issue(self, text: str) -> str:
        """Categorize issue type"""
        lower_text = text.lower()

        if any(keyword in lower_text for keyword in ["security", "vulnerability", "exploit"]):
            return "security"
        elif any(keyword in lower_text for keyword in ["performance", "slow", "memory"]):
            return "performance"
        elif any(keyword in lower_text for keyword in ["bug", "error", "exception"]):
            return "bug"
        elif any(keyword in lower_text for keyword in ["style", "format", "convention"]):
            return "style"
        else:
            return "general"

    def _format_analysis_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Format analysis data as readable summary"""
        summary_parts = []

        # Overall metrics
        metrics = analysis_data.get("metrics", {})
        if metrics:
            summary_parts.append("## Analysis Summary")
            for key, value in metrics.items():
                summary_parts.append(f"- **{key.title()}**: {value}")

        # Issues
        issues = analysis_data.get("issues", [])
        if issues:
            summary_parts.append(f"\n## Issues Found ({len(issues)})")
            for issue in issues[:5]:  # Show top 5
                summary_parts.append(f"- {issue.get('description', 'Unknown issue')}")

        # Suggestions
        suggestions = analysis_data.get("suggestions", [])
        if suggestions:
            summary_parts.append(f"\n## Suggestions ({len(suggestions)})")
            for suggestion in suggestions[:3]:  # Show top 3
                summary_parts.append(f"- {suggestion.get('description', 'Unknown suggestion')}")

        return "\n".join(summary_parts) if summary_parts else "Analysis completed successfully."
