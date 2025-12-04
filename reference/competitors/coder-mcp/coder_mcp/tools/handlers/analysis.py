#!/usr/bin/env python3
"""
Code analysis tool handler
Handles smart analysis, code smell detection, dependency analysis, and related file finding
"""

from typing import Any, Dict, List

from mcp.types import Tool

from ...code_analyzer import CodeAnalyzer
from ...security.exceptions import handle_exceptions
from ...security.validators import validate_dict_input, validate_string_input
from ..base_handler import BaseHandler


class AnalysisHandler(BaseHandler):
    """Code analysis operations"""

    def __init__(self, config_manager, context_manager):
        super().__init__(config_manager, context_manager)
        self.code_analyzer = CodeAnalyzer(self.workspace_root)

    @staticmethod
    def get_tools() -> List[Tool]:
        """Get analysis tools"""
        return [
            Tool(
                name="analyze_code",
                description="Analyze code for quality, security, and performance issues",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to analyze"},
                        "analysis_type": {
                            "type": "string",
                            "enum": ["quick", "deep", "security", "performance"],
                            "default": "quick",
                        },
                        "checks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific checks to perform",
                            "default": [],
                        },
                    },
                    "required": ["path"],
                },
            ),
            Tool(
                name="smart_analyze",
                description="Intelligently analyze code using cached context for faster results",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to analyze"},
                        "analysis_type": {
                            "type": "string",
                            "enum": ["quick", "deep", "security", "performance"],
                            "default": "quick",
                        },
                        "use_cache": {"type": "boolean", "default": True},
                    },
                    "required": ["path"],
                },
            ),
            Tool(
                name="detect_code_smells",
                description="Find potential code quality issues and anti-patterns",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "default": ".",
                            "description": "Path to analyze",
                        },
                        "smell_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "long_functions",
                                    "duplicate_code",
                                    "complex_conditionals",
                                    "large_classes",
                                    "dead_code",
                                ],
                            },
                            "default": ["long_functions", "duplicate_code", "complex_conditionals"],
                        },
                        "severity_threshold": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "default": "medium",
                        },
                    },
                },
            ),
            Tool(
                name="analyze_dependencies",
                description=(
                    "Analyze and visualize project dependencies, "
                    "find outdated packages, and suggest updates"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "check_updates": {
                            "type": "boolean",
                            "default": True,
                            "description": "Check for outdated dependencies",
                        },
                        "security_scan": {
                            "type": "boolean",
                            "default": False,
                            "description": "Scan for security vulnerabilities",
                        },
                        "visualize": {
                            "type": "boolean",
                            "default": False,
                            "description": "Create dependency graph visualization",
                        },
                    },
                },
            ),
            Tool(
                name="get_related_files",
                description="Find files related to the current file using vector search",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Current file path"},
                        "relationship_type": {
                            "type": "string",
                            "enum": ["imports", "similar_purpose", "tests", "documentation"],
                            "default": "similar_purpose",
                        },
                    },
                    "required": ["file_path"],
                },
            ),
        ]

    @handle_exceptions
    async def analyze_code(self, args: Dict[str, Any]) -> str:
        """Analyze code for quality, security, and performance issues"""
        validate_dict_input(args, "analyze_code arguments")

        path = validate_string_input(args.get("path", ""), "path")
        analysis_type = args.get("analysis_type", "quick")
        checks = args.get("checks", [])

        # If checks are specified, determine analysis type from them
        if checks:
            if any(check in ["security", "vulnerability"] for check in checks):
                analysis_type = "security"
            elif any(check in ["performance", "speed"] for check in checks):
                analysis_type = "performance"
            elif any(check in ["deep", "comprehensive"] for check in checks):
                analysis_type = "deep"

        try:
            file_path = self.safe_get_path(path)
            if not file_path.exists():
                return self.format_error("analyze_code", f"File not found: {path}")

            # Use the same logic as smart_analyze but with analyze_code branding
            analysis = await self.code_analyzer.analyze_file(
                file_path=file_path, analysis_type=analysis_type, use_cache=True
            )

            # Enhance with AI if enabled
            analysis = await self._enhance_analysis_with_ai(analysis, file_path)

            # Format results for analyze_code
            result = self._format_analyze_code_results(analysis, path, analysis_type, checks)
            await self.log_tool_usage("analyze_code", args, True)
            return result

        except (IOError, OSError, UnicodeDecodeError, AttributeError, ValueError) as e:
            await self.log_tool_usage("analyze_code", args, False)
            return self.format_error("analyze_code", str(e))

    def _format_analyze_code_results(self, analysis, path, analysis_type, checks) -> str:
        """Format analyze_code results for display"""
        result_parts = [
            f"🔍 **Code Analysis: {path}**",
            f"**Analysis Type:** {analysis_type}",
        ]

        if checks:
            result_parts.append(f"**Checks Performed:** {', '.join(checks)}")

        result_parts.extend(
            [
                self.format_ai_enhancement_status(),
                f"**Quality Score:** {analysis.get('quality_score', 'N/A')}/10",
            ]
        )

        self._add_issues_section(result_parts, analysis)
        self._add_suggestions_section(result_parts, analysis)
        self._add_metrics_section(result_parts, analysis)
        self._add_ai_insights_section(result_parts, analysis)

        return "\n".join(result_parts)

    @handle_exceptions
    async def smart_analyze(self, args: Dict[str, Any]) -> str:
        """Intelligently analyze code using cached context with AI enhancement"""
        validate_dict_input(args, "smart_analyze arguments")

        path = validate_string_input(args.get("path", ""), "path")
        analysis_type = args.get("analysis_type", "quick")
        use_cache = args.get("use_cache", True)

        try:
            file_path = self.safe_get_path(path)
            if not file_path.exists():
                return self.format_error("smart_analyze", f"File not found: {path}")

            # Step 1: Get basic analysis
            analysis = await self.code_analyzer.analyze_file(
                file_path=file_path, analysis_type=analysis_type, use_cache=use_cache
            )

            # Step 2: Enhance with AI if enabled
            analysis = await self._enhance_analysis_with_ai(analysis, file_path)

            # Step 3: Format and return results
            result = self._format_analysis_results(analysis, path, analysis_type)
            await self.log_tool_usage("smart_analyze", args, True)
            return result

        except (IOError, OSError, UnicodeDecodeError, AttributeError, ValueError) as e:
            await self.log_tool_usage("smart_analyze", args, False)
            return self.format_error("smart_analyze", str(e))

    async def _enhance_analysis_with_ai(self, analysis, file_path):
        """Enhance analysis with AI insights if available"""
        if not self.is_ai_enabled():
            return analysis

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            language = self._detect_language(file_path)
            return await self.ai_enhancer.enhance_analysis(
                analysis, content, language, str(file_path)
            )
        except (IOError, OSError, UnicodeDecodeError, AttributeError, ValueError):
            # AI fails gracefully - return basic result
            return analysis

    def _format_analysis_results(self, analysis, path, analysis_type) -> str:
        """Format analysis results for display"""
        result_parts = [
            f"🔍 **Code Analysis: {path}**",
            f"**Type:** {analysis_type}",
            self.format_ai_enhancement_status(),
            f"**Quality Score:** {analysis.get('quality_score', 'N/A')}/10",
        ]

        self._add_issues_section(result_parts, analysis)
        self._add_suggestions_section(result_parts, analysis)
        self._add_metrics_section(result_parts, analysis)
        self._add_ai_insights_section(result_parts, analysis)

        return "\n".join(result_parts)

    def _add_issues_section(self, result_parts, analysis):
        """Add issues section to results"""
        if analysis.get("issues"):
            result_parts.append(f"**Issues Found:** {len(analysis['issues'])}")
            for issue in analysis["issues"][:5]:
                result_parts.append(f"  • {issue}")

    def _add_suggestions_section(self, result_parts, analysis):
        """Add suggestions section to results"""
        if analysis.get("suggestions"):
            result_parts.append("**Suggestions:**")
            for suggestion in analysis["suggestions"][:3]:
                result_parts.append(f"  • {suggestion}")

    def _add_metrics_section(self, result_parts, analysis):
        """Add metrics section to results"""
        if not analysis.get("metrics"):
            return

        metrics = analysis["metrics"]
        result_parts.append("**Metrics:**")

        for key, label in [
            ("complexity", "Complexity"),
            ("lines_of_code", "Lines of Code"),
            ("test_coverage", "Test Coverage"),
            ("ai_quality_score", "AI Quality Score"),
            ("ai_security_score", "AI Security Score"),
        ]:
            if key in metrics:
                suffix = "%" if key == "test_coverage" else "/10" if "ai_" in key else ""
                result_parts.append(f"  • {label}: {metrics[key]}{suffix}")

    def _add_ai_insights_section(self, result_parts, analysis):
        """Add AI insights section to results"""
        if analysis.get("ai_insights"):
            ai_insights_formatted = self.format_ai_insights(analysis["ai_insights"])
            if ai_insights_formatted:
                result_parts.append(ai_insights_formatted)

    def _detect_language(self, file_path) -> str:
        """Detect programming language from file extension"""
        suffix = file_path.suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
        }
        return language_map.get(suffix, "text")

    @handle_exceptions
    async def detect_code_smells(self, args: Dict[str, Any]) -> str:
        """Find potential code issues with AI enhancement"""
        validate_dict_input(args, "detect_code_smells arguments")

        path = args.get("path", ".")
        smell_types = args.get(
            "smell_types", ["long_functions", "duplicate_code", "complex_conditionals"]
        )
        severity_threshold = args.get("severity_threshold", "medium")

        try:
            target_path = self.safe_get_path(path)

            # Step 1: Basic code smell detection
            smells = await self._process_basic_smells(target_path, smell_types, severity_threshold)

            # Step 2: AI enhancement (if enabled)
            enhanced_smells = await self._enhance_smells_with_ai(smells, target_path)

            # Step 3: Format and return output
            result = self._format_smells_output(enhanced_smells, path)

            await self.log_tool_usage("detect_code_smells", args, True)
            return result

        except (IOError, OSError, UnicodeDecodeError, AttributeError, ValueError) as e:
            await self.log_tool_usage("detect_code_smells", args, False)
            return self.format_error("detect_code_smells", str(e))

    async def _process_basic_smells(self, target_path, smell_types, severity_threshold):
        """Process basic code smell detection"""
        return await self.code_analyzer.detect_code_smells(
            path=target_path, smell_types=smell_types, severity_threshold=severity_threshold
        )

    async def _enhance_smells_with_ai(self, smells, target_path):
        """Enhance code smells with AI insights if available"""
        enhanced_smells = {"smells": smells}

        if self.is_ai_enabled() and target_path.is_file():
            try:
                content = target_path.read_text(encoding="utf-8", errors="ignore")
                language = self._detect_language(target_path)

                enhanced_smells = await self.ai_enhancer.enhance_code_smells(
                    smells, content, language, str(target_path)
                )
            except (IOError, OSError, UnicodeDecodeError, AttributeError, ValueError):
                # AI fails gracefully
                pass

        return enhanced_smells

    def _format_smells_output(self, enhanced_smells, path) -> str:
        """Format the complete code smells output"""
        basic_smells = enhanced_smells.get("smells", [])

        if not basic_smells and not enhanced_smells.get("ai_detected_issues"):
            return self.format_success("detect_code_smells", f"No code smells detected in {path}")

        result_parts = [
            f"🔍 **Code Smells Detected in {path}:**",
            self.format_ai_enhancement_status(),
            "",
        ]

        # Add basic smells section
        if basic_smells:
            result_parts.extend(self._format_basic_smells_section(basic_smells))

        # Add AI enhancement sections
        result_parts.extend(self._format_ai_enhancement_sections(enhanced_smells))

        return "\n".join(result_parts)

    def _format_basic_smells_section(self, basic_smells):
        """Format the basic smells analysis section"""
        result_parts = ["## 📊 Static Analysis Results"]

        # Group smells by severity
        severity_groups = self._group_smells_by_severity(basic_smells)

        # Display each severity level
        for severity in ["high", "medium", "low"]:
            if severity_groups[severity]:
                result_parts.extend(
                    self._format_severity_group(severity, severity_groups[severity])
                )

        return result_parts

    def _group_smells_by_severity(self, smells):
        """Group smells by severity level"""
        severity_groups = {"high": [], "medium": [], "low": []}

        for smell in smells:
            severity = smell.get("severity", "medium")
            if severity in severity_groups:
                severity_groups[severity].append(smell)

        return severity_groups

    def _format_severity_group(self, severity, smells):
        """Format a group of smells for a specific severity level"""
        result_parts = [f"**{severity.upper()} SEVERITY:**"]

        for smell in smells[:5]:  # Limit per severity
            file_path = smell.get("file", "Unknown")
            smell_type = smell.get("type", "Unknown")
            description = smell.get("description", "")
            line_number = smell.get("line_number", "")

            location = f":{line_number}" if line_number else ""
            result_parts.append(f"**{file_path}{location}** - {smell_type}\n" f"  {description}\n")

        if len(smells) > 5:
            result_parts.append(f"  ... and {len(smells) - 5} more {severity} issues\n")

        return result_parts

    def _format_ai_enhancement_sections(self, enhanced_smells):
        """Format all AI enhancement sections"""
        result_parts = []

        # AI-detected issues section
        if enhanced_smells.get("ai_detected_issues"):
            result_parts.append("\n## 🤖 AI-Detected Issues")
            for issue in enhanced_smells["ai_detected_issues"][:5]:
                result_parts.append(f"• {issue.get('description', 'AI-detected issue')}")

        # AI quality assessment section
        if enhanced_smells.get("ai_quality_assessment"):
            result_parts.extend(
                self._format_ai_quality_assessment(enhanced_smells["ai_quality_assessment"])
            )

        # AI refactoring suggestions section
        if enhanced_smells.get("refactoring_suggestions"):
            result_parts.extend(
                self._format_ai_refactoring_suggestions(enhanced_smells["refactoring_suggestions"])
            )

        return result_parts

    def _format_ai_quality_assessment(self, assessment):
        """Format AI quality assessment section"""
        result_parts = ["\n## 🤖 AI Quality Assessment"]
        result_parts.append(f"• Overall Score: {assessment.get('overall_score', 'N/A')}/10")
        result_parts.append(f"• Complexity Score: {assessment.get('complexity_score', 'N/A')}/10")
        result_parts.append(f"• Readability Score: {assessment.get('readability_score', 'N/A')}/10")
        return result_parts

    def _format_ai_refactoring_suggestions(self, suggestions):
        """Format AI refactoring suggestions section"""
        if not suggestions:
            return []

        result_parts = ["\n## 🔧 AI Refactoring Suggestions"]
        for suggestion in suggestions[:3]:
            result_parts.append(f"• {suggestion}")

        return result_parts

    @handle_exceptions
    async def analyze_dependencies(self, args: Dict[str, Any]) -> str:
        """Analyze project dependencies"""
        import logging
        import traceback

        logger = logging.getLogger(__name__)

        try:
            validate_dict_input(args, "analyze_dependencies arguments")

            check_updates = args.get("check_updates", True)
            security_scan = args.get("security_scan", False)
            visualize = args.get("visualize", False)

            logger.info(
                "analyze_dependencies: starting analysis with check_updates=%s, security_scan=%s",
                check_updates,
                security_scan,
            )

            analysis = await self.code_analyzer.analyze_dependencies(
                check_updates=check_updates,
                security_scan=security_scan,
            )

            logger.info("analyze_dependencies: analysis type=%s", type(analysis))
            if isinstance(analysis, dict):
                logger.info("analyze_dependencies: analysis keys=%s", list(analysis.keys()))
            else:
                logger.info("analyze_dependencies: analysis content=%s", str(analysis)[:200])

            # Convert string results to dictionary format to prevent AttributeError
            if isinstance(analysis, str):
                logger.info("analyze_dependencies: converting string to dict: %s", analysis[:100])
                analysis = {
                    "project_type": "unknown",
                    "total_dependencies": 0,
                    "dependencies": {},
                    "outdated": [],
                    "outdated_count": 0,
                    "vulnerabilities": [],
                    "vulnerability_count": 0,
                    "recommendations": [],
                    "analysis_timestamp": 0,
                    "error": analysis,
                    "errors": [analysis],
                }
                logger.info("analyze_dependencies: converted string to dict format")

            result = self._format_dependency_analysis(
                analysis, check_updates, security_scan, visualize
            )
            await self.log_tool_usage("analyze_dependencies", args, True)
            return result

        except Exception as e:
            logger.error("analyze_dependencies error: %s", e)
            logger.error("Full traceback: %s", traceback.format_exc())
            await self.log_tool_usage("analyze_dependencies", args, False)
            return self.format_error("analyze_dependencies", str(e))

    def _format_dependency_analysis(self, analysis, check_updates, security_scan, visualize) -> str:
        """Format dependency analysis results"""
        # Handle case where analysis is a string (from exception handling)
        if isinstance(analysis, str):
            return analysis

        # Handle case where analysis is None or not a dict
        if not isinstance(analysis, dict):
            error_msg = (
                f"❌ Error: Invalid analysis result format. "
                f"Got {type(analysis)}: {str(analysis)[:100]}"
            )
            return error_msg

        try:
            result_parts = [
                "📦 **Dependency Analysis**",
                f"**Project Type:** {analysis.get('project_type', 'unknown')}",
                f"**Total Dependencies:** {analysis.get('total_dependencies', 0)}",
            ]

            self._add_dependency_types_section(result_parts, analysis)
            self._add_outdated_packages_section(result_parts, analysis, check_updates)
            self._add_security_issues_section(result_parts, analysis, security_scan)
            self._add_recommendations_section(result_parts, analysis)
            self._add_visualization_section(result_parts, analysis, visualize)
            self._add_errors_section(result_parts, analysis)

            return "\n".join(result_parts)
        except Exception as e:
            return f"❌ Error formatting dependency analysis: {str(e)}"

    def _add_dependency_types_section(self, result_parts, analysis):
        """Add dependency types breakdown"""
        # Handle case where analysis is not a dict
        if not isinstance(analysis, dict):
            return

        dependencies = analysis.get("dependencies", {})
        if not dependencies:
            return

        # Handle both dict and list formats for dependencies
        if isinstance(dependencies, dict):
            # New format: dict of name -> version
            dep_types = {}
            for dep_name, version in dependencies.items():
                # Categorize by suffix in parentheses (e.g., "package (dev)")
                if " (" in dep_name and dep_name.endswith(")"):
                    dep_type = dep_name.split(" (")[-1][:-1]  # Extract text between ( and )
                else:
                    dep_type = "runtime"
                dep_types[dep_type] = dep_types.get(dep_type, 0) + 1

            for dep_type, count in dep_types.items():
                result_parts.append(f"**{dep_type.title()}:** {count}")
        else:
            # Legacy format: list of dicts
            dep_types = {}
            for dep in dependencies:
                dep_type = dep.get("type", "runtime")
                dep_types[dep_type] = dep_types.get(dep_type, 0) + 1

            for dep_type, count in dep_types.items():
                result_parts.append(f"**{dep_type.title()}:** {count}")

    def _add_outdated_packages_section(self, result_parts, analysis, check_updates):
        """Add outdated packages section"""
        # Handle case where analysis is not a dict
        if not isinstance(analysis, dict):
            return

        if not (check_updates and analysis.get("outdated")):
            return

        outdated = analysis["outdated"]
        result_parts.append(f"\n**Outdated Packages:** {len(outdated)}")

        for pkg in outdated[:5]:
            # Handle both old and new format
            if isinstance(pkg, dict):
                name = pkg.get("name", "unknown")
                current = pkg.get("current_version", "unknown")
                latest = pkg.get("latest_version", "unknown")
            else:
                # Legacy format
                name = str(pkg)
                current = "unknown"
                latest = "unknown"

            result_parts.append(f"  • {name}: {current} → {latest}")

        if len(outdated) > 5:
            result_parts.append(f"  ... and {len(outdated) - 5} more outdated packages")

    def _add_security_issues_section(self, result_parts, analysis, security_scan):
        """Add security vulnerabilities section"""
        # Handle case where analysis is not a dict
        if not isinstance(analysis, dict):
            return

        if not (security_scan and analysis.get("vulnerabilities")):
            return

        vulnerabilities = analysis["vulnerabilities"]
        result_parts.append(f"\n**Security Issues:** {len(vulnerabilities)}")

        for vuln in vulnerabilities[:3]:
            severity = vuln.get("severity", "unknown")
            package = vuln.get("package", "unknown")
            # Handle both 'description' and 'vulnerability' fields
            description = vuln.get("description") or vuln.get("vulnerability", "")
            result_parts.append(f"  ⚠️  {package} ({severity}): {description}")

        if len(vulnerabilities) > 3:
            result_parts.append(f"  ... and {len(vulnerabilities) - 3} more vulnerabilities")

    def _add_recommendations_section(self, result_parts, analysis):
        """Add recommendations section"""
        # Handle case where analysis is not a dict
        if not isinstance(analysis, dict):
            return

        recommendations = analysis.get("recommendations", [])
        if not recommendations:
            return

        result_parts.append("\n**Recommendations:**")
        for rec in recommendations:
            result_parts.append(f"  • {rec}")

    def _add_visualization_section(self, result_parts, analysis, visualize):
        """Add dependency graph visualization section"""
        # Handle case where analysis is not a dict
        if not isinstance(analysis, dict):
            return

        if visualize and analysis.get("graph_file"):
            result_parts.append(f"\n**Dependency Graph:** {analysis['graph_file']}")

    def _add_errors_section(self, result_parts, analysis):
        """Add errors section if any occurred"""
        # Handle case where analysis is not a dict
        if not isinstance(analysis, dict):
            return

        errors = analysis.get("errors", [])
        if not errors:
            return

        result_parts.append(f"\n**Errors ({len(errors)}):**")
        for error in errors:
            result_parts.append(f"  ⚠️  {error}")

    @handle_exceptions
    async def get_related_files(self, args: Dict[str, Any]) -> str:
        """Find files related to the current file with AI semantic understanding"""
        validate_dict_input(args, "get_related_files arguments")

        file_path = validate_string_input(args.get("file_path", ""), "file_path")
        relationship_type = args.get("relationship_type", "similar_purpose")

        try:
            # Step 1: Get basic relationships
            related = await self.context_manager.get_related_files(
                file_path=file_path, top_k=5, relationship_type=relationship_type
            )

            # Step 2: Enhance with AI if enabled
            enhanced_relationships = await self._enhance_file_relationships_with_ai(
                related, file_path, relationship_type
            )

            # Step 3: Format and return results
            result = self._format_related_files_results(related, enhanced_relationships, file_path)
            await self.log_tool_usage("get_related_files", args, True)
            return result

        except (IOError, OSError, UnicodeDecodeError, AttributeError, ValueError) as e:
            await self.log_tool_usage("get_related_files", args, False)
            return self.format_error("get_related_files", str(e))

    async def _enhance_file_relationships_with_ai(self, related, file_path, relationship_type):
        """Enhance file relationships with AI insights if available"""
        enhanced_relationships = {}

        if not self.is_ai_enabled():
            return enhanced_relationships

        try:
            target_path = self.safe_get_path(file_path)
            if target_path.exists():
                content = target_path.read_text(encoding="utf-8", errors="ignore")
                language = self._detect_language(target_path)

                basic_relationships = {
                    "files": related,
                    "relationship_type": relationship_type,
                }

                enhanced_relationships = await self.ai_enhancer.enhance_file_relationships(
                    basic_relationships, file_path, content, language
                )
        except (IOError, OSError, UnicodeDecodeError, AttributeError, ValueError):
            # AI fails gracefully
            pass

        return enhanced_relationships

    def _format_related_files_results(self, related, enhanced_relationships, file_path) -> str:
        """Format related files results for display"""
        if not related and not enhanced_relationships.get("ai_insights"):
            return self.format_info("get_related_files", f"No related files found for {file_path}")

        result_parts = [
            f"🔗 **Related Files for {file_path}:**",
            self.format_ai_enhancement_status(),
            "",
        ]

        self._add_vector_search_results(result_parts, related)
        self._add_ai_file_analysis(result_parts, enhanced_relationships)

        return "\n".join(result_parts)

    def _add_vector_search_results(self, result_parts, related):
        """Add vector search results section"""
        if not related:
            return

        result_parts.append("## 📊 Vector Search Results")
        for item in related:
            path = item.get("path", "Unknown")
            score = item.get("score", 0)
            reason = item.get("reason", "Similar content")
            result_parts.append(f"**{path}** (Score: {score:.2f})\n  {reason}\n")

    def _add_ai_file_analysis(self, result_parts, enhanced_relationships):
        """Add AI file analysis section"""
        ai_insights = enhanced_relationships.get("ai_insights")
        if not ai_insights:
            return

        if ai_insights.get("semantic_purpose"):
            result_parts.append("\n## 🤖 AI File Analysis")
            result_parts.append(f"**Purpose**: {ai_insights['semantic_purpose']}")

        for key, label in [
            ("design_patterns", "Design Patterns"),
            ("conceptual_dependencies", "Conceptual Dependencies"),
            ("likely_dependents", "Likely Dependents"),
        ]:
            items = ai_insights.get(key)
            if items:
                result_parts.append(f"**{label}**: {', '.join(items)}")
