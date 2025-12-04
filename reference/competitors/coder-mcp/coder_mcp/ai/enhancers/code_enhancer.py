#!/usr/bin/env python3
"""
Code AI Enhancement Module - Handles AI enhancement for code analysis and quality checks
"""

import logging
from typing import Any, Dict, List, Optional

from .base_enhancer import AIServiceError, BaseEnhancer

logger = logging.getLogger(__name__)


class CodeEnhancer(BaseEnhancer):
    """Handles AI enhancement for code analysis and quality checks"""

    async def get_enhancement_capabilities(self) -> List[str]:
        """Return list of enhancement capabilities this enhancer provides"""
        return [
            "code_analysis",
            "quality_assessment",
            "code_smell_detection",
            "refactoring_suggestions",
            "security_analysis",
            "performance_insights",
        ]

    async def enhance_analysis(
        self, basic_analysis: Dict[str, Any], code: str, language: str, file_path: str = ""
    ) -> Dict[str, Any]:
        """Enhance basic AST analysis with AI insights"""
        if not self._ensure_ai_available():
            fallback_result = self._fallback_enhancement(
                basic_analysis, "AI code analysis unavailable"
            )
            return fallback_result if isinstance(fallback_result, dict) else dict(basic_analysis)

        try:
            with self._safe_ai_call("code_analysis"):
                if self.ai_service is None:
                    fallback_result = self._fallback_enhancement(
                        basic_analysis, "AI service not available"
                    )
                    return (
                        fallback_result
                        if isinstance(fallback_result, dict)
                        else dict(basic_analysis)
                    )

                # Add AI insights to existing analysis
                ai_result = await self.ai_service.analyze_code(
                    code, language, analysis_type="comprehensive"
                )

                # Merge AI insights with AST analysis
                enhanced_analysis = basic_analysis.copy()
                enhanced_analysis["ai_insights"] = {
                    "security_risks": ai_result.security_concerns,
                    "performance_insights": ai_result.performance_insights,
                    "architectural_suggestions": ai_result.suggestions,
                    "code_quality_score": ai_result.metrics.get("maintainability", 0),
                    "summary": ai_result.summary,
                    "issues": ai_result.issues,
                }

                # Add AI-powered metrics
                if "metrics" not in enhanced_analysis:
                    enhanced_analysis["metrics"] = {}

                enhanced_analysis["metrics"]["ai_quality_score"] = ai_result.metrics.get(
                    "maintainability", 0
                )
                enhanced_analysis["metrics"]["ai_complexity_score"] = ai_result.metrics.get(
                    "complexity", 0
                )
                enhanced_analysis["metrics"]["ai_security_score"] = 10 - len(
                    ai_result.security_concerns
                )

                logger.debug("Enhanced analysis for %s with AI insights", file_path)
                return enhanced_analysis

        except AIServiceError:
            fallback_result = self._fallback_enhancement(basic_analysis, "AI service unavailable")
            return fallback_result if isinstance(fallback_result, dict) else dict(basic_analysis)
        except (UnicodeDecodeError, ValueError, AttributeError, TypeError) as e:
            logger.warning("AI enhancement failed for analysis: %s", e)
            fallback_result = self._fallback_enhancement(
                basic_analysis, f"AI enhancement error: {str(e)}"
            )
            return fallback_result if isinstance(fallback_result, dict) else dict(basic_analysis)
        except Exception as e:
            logger.warning("Unexpected error during AI enhancement: %s", e)
            fallback_result = self._fallback_enhancement(
                basic_analysis, f"Unexpected AI error: {str(e)}"
            )
            return fallback_result if isinstance(fallback_result, dict) else dict(basic_analysis)

    async def enhance_code_smells(
        self, basic_smells: List[Dict[str, Any]], code: str, language: str, file_path: str = ""
    ) -> Dict[str, Any]:
        """Enhance code smell detection with AI insights"""
        if not self._ensure_ai_available():
            return {"smells": basic_smells}

        try:
            with self._safe_ai_call("code_smell_detection"):
                if self.ai_service is None:
                    return {"smells": basic_smells, "ai_fallback": "AI service not available"}

                # Get AI analysis focused on code quality
                ai_result = await self.ai_service.analyze_code(
                    code, language, analysis_type="comprehensive"
                )

                # Merge AI insights with basic smell detection
                enhanced_smells = {
                    "basic_smells": basic_smells,
                    "ai_detected_issues": ai_result.issues,
                    "ai_suggestions": ai_result.suggestions,
                    "ai_quality_assessment": {
                        "overall_score": ai_result.metrics.get("maintainability", 0),
                        "complexity_score": ai_result.metrics.get("complexity", 0),
                        "readability_score": ai_result.metrics.get("readability", 0),
                    },
                    "ai_priority_issues": self._prioritize_issues(ai_result.issues),
                    "refactoring_suggestions": await self._get_refactoring_suggestions(
                        code, language
                    ),
                }

                logger.debug("Enhanced code smell detection for %s", file_path)
                return enhanced_smells

        except AIServiceError:
            return {"smells": basic_smells, "ai_fallback": "AI service unavailable"}
        except (UnicodeDecodeError, ValueError, AttributeError, TypeError) as e:
            logger.warning("AI enhancement failed for code smells: %s", e)
            return {"smells": basic_smells, "ai_fallback": f"AI enhancement error: {str(e)}"}

    async def enhance_security_analysis(
        self, basic_security: Dict[str, Any], code: str, language: str, file_path: str = ""
    ) -> Dict[str, Any]:
        """Enhance security analysis with AI-powered vulnerability detection"""
        if not self._ensure_ai_available():
            fallback_result = self._fallback_enhancement(
                basic_security, "AI security analysis unavailable"
            )
            return fallback_result if isinstance(fallback_result, dict) else basic_security

        try:
            with self._safe_ai_call("security_analysis"):
                if self.ai_service is None:
                    fallback_result = self._fallback_enhancement(
                        basic_security, "AI service not available"
                    )
                    return fallback_result if isinstance(fallback_result, dict) else basic_security

                ai_response = await self.ai_service.reason_about_code(
                    f"""Perform a comprehensive security analysis of this {language} code:

                    File: {file_path}

                    Focus on:
                    1. SQL injection vulnerabilities
                    2. XSS vulnerabilities
                    3. Authentication/authorization issues
                    4. Input validation problems
                    5. Cryptographic weaknesses
                    6. Information disclosure risks
                    7. Business logic flaws

                    Provide detailed findings with severity levels (high/medium/low)
                    and remediation suggestions.
                    """,
                    code,
                )

                enhanced_security = basic_security.copy()
                enhanced_security["ai_security_analysis"] = {
                    "vulnerabilities": self._extract_vulnerabilities(ai_response.content),
                    "severity_assessment": self._extract_severity_levels(ai_response.content),
                    "remediation_suggestions": self._extract_remediation_suggestions(
                        ai_response.content
                    ),
                    "security_score": self._extract_score_from_response(ai_response.content, 7.0),
                    "compliance_notes": self._extract_compliance_notes(ai_response.content),
                }

                logger.debug("Enhanced security analysis for %s", file_path)
                return enhanced_security

        except AIServiceError:
            fallback_result = self._fallback_enhancement(
                basic_security, "AI security analysis unavailable"
            )
            return fallback_result if isinstance(fallback_result, dict) else basic_security
        except (UnicodeDecodeError, ValueError, AttributeError, TypeError) as e:
            logger.warning("AI security enhancement failed: %s", e)
            fallback_result = self._fallback_enhancement(
                basic_security, f"AI security analysis error: {str(e)}"
            )
            return fallback_result if isinstance(fallback_result, dict) else basic_security

    async def enhance_performance_analysis(
        self, basic_performance: Dict[str, Any], code: str, language: str, file_path: str = ""
    ) -> Dict[str, Any]:
        """Enhance performance analysis with AI insights"""
        if not self._ensure_ai_available():
            fallback_result = self._fallback_enhancement(
                basic_performance, "AI performance analysis unavailable"
            )
            return fallback_result if isinstance(fallback_result, dict) else basic_performance

        try:
            with self._safe_ai_call("performance_analysis"):
                if self.ai_service is None:
                    fallback_result = self._fallback_enhancement(
                        basic_performance, "AI service not available"
                    )
                    return (
                        fallback_result if isinstance(fallback_result, dict) else basic_performance
                    )

                ai_response = await self.ai_service.reason_about_code(
                    f"""Analyze the performance characteristics of this {language} code:

                    File: {file_path}

                    Focus on:
                    1. Algorithmic complexity (Big O analysis)
                    2. Memory usage patterns
                    3. I/O operations efficiency
                    4. Database query optimization
                    5. Caching opportunities
                    6. Async/await usage patterns
                    7. Resource management

                    Provide specific optimization recommendations with expected impact.
                    """,
                    code,
                )

                enhanced_performance = basic_performance.copy()
                enhanced_performance["ai_performance_analysis"] = {
                    "complexity_analysis": self._extract_complexity_analysis(ai_response.content),
                    "optimization_opportunities": self._extract_optimization_opportunities(
                        ai_response.content
                    ),
                    "performance_score": self._extract_score_from_response(
                        ai_response.content, 6.0
                    ),
                    "bottleneck_detection": self._extract_bottlenecks(ai_response.content),
                    "optimization_priority": self._extract_optimization_priority(
                        ai_response.content
                    ),
                }

                logger.debug("Enhanced performance analysis for %s", file_path)
                return enhanced_performance

        except AIServiceError:
            fallback_result = self._fallback_enhancement(
                basic_performance, "AI performance analysis unavailable"
            )
            return fallback_result if isinstance(fallback_result, dict) else basic_performance
        except (UnicodeDecodeError, ValueError, AttributeError, TypeError) as e:
            logger.warning("AI performance enhancement failed: %s", e)
            fallback_result = self._fallback_enhancement(
                basic_performance, f"AI performance analysis error: {str(e)}"
            )
            return fallback_result if isinstance(fallback_result, dict) else basic_performance

    async def suggest_code_improvements(
        self, code: str, language: str, focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate AI-powered code improvement suggestions"""
        if not self._ensure_ai_available():
            return {"suggestions": [], "message": "AI suggestions unavailable"}

        focus_areas = focus_areas or ["maintainability", "readability", "performance"]

        try:
            with self._safe_ai_call("code_improvement_suggestions"):
                if self.ai_service is None:
                    return {"suggestions": [], "message": "AI service not available"}

                ai_response = await self.ai_service.reason_about_code(
                    f"""Provide improvement suggestions for this {language} code:

                    Code:
                    ```{language}
                    {code}
                    ```

                    Focus areas: {', '.join(focus_areas)}

                    Provide suggestions for:
                    1. Code structure and organization
                    2. Performance optimizations
                    3. Readability improvements
                    4. Maintainability enhancements
                    5. Security hardening
                    6. Best practices
                    """,
                    code,
                )

                return {
                    "suggestions": self._extract_suggestions(ai_response.content),
                    "focus_areas": focus_areas,
                    "priority_suggestions": self._extract_priority_suggestions(ai_response.content),
                    "implementation_complexity": self._extract_implementation_complexity(
                        ai_response.content
                    ),
                    "expected_impact": self._extract_expected_impact(ai_response.content),
                }

        except AIServiceError:
            return {"suggestions": [], "message": "AI service unavailable"}
        except (UnicodeDecodeError, ValueError, AttributeError, TypeError) as e:
            logger.warning("Failed to get code improvement suggestions: %s", e)
            return {"suggestions": [], "message": f"Error: {str(e)}"}

    # Helper methods for parsing AI responses
    def _prioritize_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize issues by severity and impact"""
        severity_weights = {"high": 3, "medium": 2, "low": 1}

        def priority_score(issue: Dict[str, Any]) -> float:
            severity = issue.get("severity", "medium")
            return severity_weights.get(severity, 2)

        return sorted(issues, key=priority_score, reverse=True)

    async def _get_refactoring_suggestions(self, code: str, language: str) -> List[str]:
        """Get AI-powered refactoring suggestions"""
        try:
            if self.ai_service is None:
                return []

            ai_response = await self.ai_service.reason_about_code(
                f"""Suggest refactoring improvements for this {language} code:

                Focus on:
                1. Maintainability improvements
                2. Readability enhancements
                3. Performance optimizations
                """,
                code,
            )
            return self._extract_suggestions(ai_response.content)
        except (UnicodeDecodeError, ValueError, AttributeError, TypeError) as e:
            logger.warning("Failed to get refactoring suggestions: %s", e)
            return []

    def _extract_suggestions(self, ai_response: str) -> List[str]:
        """Extract suggestions from AI response"""
        return self._extract_list_from_response(ai_response, ["suggest", "recommend", "improve"])

    def _extract_vulnerabilities(self, ai_response: str) -> List[Dict[str, Any]]:
        """Extract security vulnerabilities from AI response"""
        vulnerabilities = []
        lines = ai_response.split("\n")
        current_vuln: Dict[str, Any] = {}

        for line in lines:
            line = line.strip()
            if any(word in line.lower() for word in ["vulnerability", "security issue", "risk"]):
                if current_vuln:
                    vulnerabilities.append(current_vuln)
                current_vuln = {"description": line, "severity": "medium"}
            elif "severity" in line.lower() and current_vuln:
                if "high" in line.lower():
                    current_vuln["severity"] = "high"
                elif "low" in line.lower():
                    current_vuln["severity"] = "low"

        if current_vuln:
            vulnerabilities.append(current_vuln)

        return vulnerabilities[:5]  # Limit to 5 vulnerabilities

    def _extract_severity_levels(self, ai_response: str) -> Dict[str, int]:
        """Extract severity level counts from AI response"""
        severity_counts = {"high": 0, "medium": 0, "low": 0}

        for line in ai_response.split("\n"):
            line = line.lower()
            if "high" in line and "severity" in line:
                severity_counts["high"] += 1
            elif "medium" in line and "severity" in line:
                severity_counts["medium"] += 1
            elif "low" in line and "severity" in line:
                severity_counts["low"] += 1

        return severity_counts

    def _extract_remediation_suggestions(self, ai_response: str) -> List[str]:
        """Extract remediation suggestions from AI response"""
        return self._extract_list_from_response(
            ai_response, ["remediation", "fix", "solution", "mitigation"]
        )

    def _extract_compliance_notes(self, ai_response: str) -> List[str]:
        """Extract compliance-related notes from AI response"""
        return self._extract_list_from_response(
            ai_response, ["compliance", "standard", "regulation", "policy"]
        )

    def _extract_complexity_analysis(self, ai_response: str) -> Dict[str, Any]:
        """Extract complexity analysis from AI response"""
        return {
            "time_complexity": self._extract_key_value_from_response(
                ai_response, "time complexity"
            ),
            "space_complexity": self._extract_key_value_from_response(
                ai_response, "space complexity"
            ),
            "cyclomatic_complexity": self._extract_key_value_from_response(
                ai_response, "cyclomatic complexity"
            ),
        }

    def _extract_optimization_opportunities(self, ai_response: str) -> List[str]:
        """Extract optimization opportunities from AI response"""
        return self._extract_list_from_response(
            ai_response, ["optimization", "optimize", "performance", "faster"]
        )

    def _extract_bottlenecks(self, ai_response: str) -> List[str]:
        """Extract performance bottlenecks from AI response"""
        return self._extract_list_from_response(
            ai_response, ["bottleneck", "slow", "inefficient", "blocking"]
        )

    def _extract_optimization_priority(self, ai_response: str) -> List[str]:
        """Extract optimization priorities from AI response"""
        return self._extract_list_from_response(
            ai_response, ["priority", "critical", "important", "urgent"]
        )

    def _extract_priority_suggestions(self, ai_response: str) -> List[str]:
        """Extract priority suggestions from AI response"""
        return self._extract_list_from_response(
            ai_response, ["priority", "critical", "important", "must"]
        )

    def _extract_implementation_complexity(self, ai_response: str) -> str:
        """Extract implementation complexity assessment from AI response"""
        complexity_indicators = ["simple", "moderate", "complex", "difficult"]

        for line in ai_response.split("\n"):
            line = line.lower()
            if "complexity" in line or "difficult" in line or "simple" in line:
                for indicator in complexity_indicators:
                    if indicator in line:
                        return indicator.capitalize()

        return "Moderate"

    def _extract_expected_impact(self, ai_response: str) -> str:
        """Extract expected impact assessment from AI response"""
        impact_indicators = ["high", "medium", "low", "significant", "minimal"]

        for line in ai_response.split("\n"):
            line = line.lower()
            if "impact" in line:
                for indicator in impact_indicators:
                    if indicator in line:
                        return indicator.capitalize()

        return "Medium"
