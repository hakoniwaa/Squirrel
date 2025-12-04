#!/usr/bin/env python3
"""
Dependency AI Enhancement Module - Handles AI enhancement for dependency analysis and security
"""

import logging
from typing import Any, Dict, List, Optional

from .base_enhancer import AIServiceError, BaseEnhancer

logger = logging.getLogger(__name__)


class DependencyEnhancer(BaseEnhancer):
    """Handles AI enhancement for dependency analysis and security vulnerability detection"""

    async def get_enhancement_capabilities(self) -> List[str]:
        """Return list of enhancement capabilities this enhancer provides"""
        return [
            "dependency_analysis",
            "vulnerability_detection",
            "update_recommendations",
            "compatibility_assessment",
            "license_analysis",
            "security_audit",
        ]

    async def enhance_dependency_analysis(
        self, basic_deps: Dict[str, Any], project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance dependency analysis with AI insights"""
        if not self._ensure_ai_available():
            enhanced_result = self._fallback_enhancement(
                basic_deps, "AI dependency analysis unavailable"
            )
            if not isinstance(enhanced_result, dict):
                return {"error": "Fallback enhancement failed", "original_data": basic_deps}
            return enhanced_result

        try:
            with self._safe_ai_call("dependency_analysis"):
                if self.ai_service is None:
                    enhanced_result = self._fallback_enhancement(
                        basic_deps, "AI service not available"
                    )
                    if not isinstance(enhanced_result, dict):
                        return {"error": "Fallback enhancement failed", "original_data": basic_deps}
                    return enhanced_result

                ai_response = await self.ai_service.reason_about_code(
                    f"""Analyze these project dependencies and provide insights:

                    Dependencies: {basic_deps}
                    Project context: {project_context}

                    Provide analysis on:
                    1. Outdated packages and recommended updates
                    2. Security vulnerabilities in dependencies
                    3. License compatibility issues
                    4. Unused or redundant dependencies
                    5. Missing dependencies for common use cases
                    6. Version conflicts and compatibility issues
                    """,
                    code="",
                )

                enhanced_deps = basic_deps.copy()
                enhanced_deps["ai_analysis"] = {
                    "outdated_packages": self._extract_outdated_packages(ai_response.content),
                    "security_vulnerabilities": self._extract_security_vulnerabilities(
                        ai_response.content
                    ),
                    "license_issues": self._extract_license_issues(ai_response.content),
                    "unused_dependencies": self._extract_unused_dependencies(ai_response.content),
                    "recommended_additions": self._extract_recommended_additions(
                        ai_response.content
                    ),
                    "version_conflicts": self._extract_version_conflicts(ai_response.content),
                    "dependency_health_score": self._extract_score_from_response(
                        ai_response.content, 7.0
                    ),
                }

                logger.debug("Enhanced dependency analysis with AI insights")
                return enhanced_deps

        except AIServiceError:
            enhanced_result = self._fallback_enhancement(
                basic_deps, "AI dependency analysis unavailable"
            )
            if not isinstance(enhanced_result, dict):
                return {"error": "Fallback enhancement failed", "original_data": basic_deps}
            return enhanced_result
        except (ValueError, TypeError, KeyError) as e:
            logger.warning("AI enhancement failed for dependency analysis: %s", str(e))
            enhanced_result = self._fallback_enhancement(
                basic_deps, f"Dependency analysis error: {str(e)}"
            )
            if not isinstance(enhanced_result, dict):
                return {"error": "Fallback enhancement failed", "original_data": basic_deps}
            return enhanced_result

    async def analyze_security_vulnerabilities(
        self, dependencies: List[Dict[str, Any]], severity_threshold: str = "medium"
    ) -> Dict[str, Any]:
        """Analyze dependencies for security vulnerabilities"""
        if not self._ensure_ai_available():
            return {"vulnerabilities": [], "message": "AI security analysis unavailable"}

        try:
            with self._safe_ai_call("vulnerability_analysis"):
                if self.ai_service is None:
                    return {"vulnerabilities": [], "message": "AI service not available"}

                ai_response = await self.ai_service.reason_about_code(
                    f"""Analyze these dependencies for security vulnerabilities:

                    Dependencies: {dependencies}
                    Severity threshold: {severity_threshold}

                    Provide detailed security analysis including:
                    1. Known CVEs and security advisories
                    2. Vulnerability severity levels
                    3. Affected versions and fix versions
                    4. Exploitation likelihood and impact
                    5. Remediation recommendations
                    6. Alternative package suggestions if needed
                    """,
                    code="",
                )

                return {
                    "vulnerabilities": self._extract_detailed_vulnerabilities(ai_response.content),
                    "severity_summary": self._extract_severity_summary(ai_response.content),
                    "critical_issues": self._extract_critical_issues(ai_response.content),
                    "remediation_plan": self._extract_remediation_plan(ai_response.content),
                    "alternative_packages": self._extract_alternative_packages(ai_response.content),
                    "security_score": self._extract_score_from_response(ai_response.content, 5.0),
                    "risk_assessment": self._extract_risk_assessment(ai_response.content),
                }

        except AIServiceError:
            return {"vulnerabilities": [], "message": "AI vulnerability analysis unavailable"}
        except (ValueError, TypeError, KeyError) as e:
            logger.warning("Failed to analyze security vulnerabilities: %s", str(e))
            return {"vulnerabilities": [], "message": f"Vulnerability analysis error: {str(e)}"}

    async def recommend_dependency_updates(
        self, current_deps: Dict[str, str], project_type: str = "unknown"
    ) -> Dict[str, Any]:
        """Recommend dependency updates with AI analysis"""
        if not self._ensure_ai_available():
            return {"recommendations": [], "message": "AI update recommendations unavailable"}

        try:
            with self._safe_ai_call("update_recommendations"):
                if self.ai_service is None:
                    return {"recommendations": [], "message": "AI service not available"}

                ai_response = await self.ai_service.reason_about_code(
                    f"""Analyze these dependencies and recommend updates:

                    Current dependencies: {current_deps}
                    Project type: {project_type}

                    Provide update recommendations considering:
                    1. Security fixes and patches
                    2. Feature improvements and new capabilities
                    3. Breaking changes and migration effort
                    4. Performance improvements
                    5. Compatibility with other dependencies
                    6. Long-term support and maintenance status
                    """,
                    code="",
                )

                return {
                    "priority_updates": self._extract_priority_updates(ai_response.content),
                    "optional_updates": self._extract_optional_updates(ai_response.content),
                    "breaking_changes": self._extract_breaking_changes(ai_response.content),
                    "migration_effort": self._extract_migration_effort(ai_response.content),
                    "update_benefits": self._extract_update_benefits(ai_response.content),
                    "compatibility_warnings": self._extract_compatibility_warnings(
                        ai_response.content
                    ),
                    "recommended_order": self._extract_update_order(ai_response.content),
                }

        except AIServiceError:
            return {"recommendations": [], "message": "AI update recommendations unavailable"}
        except (ValueError, TypeError, KeyError) as e:
            logger.warning("Failed to recommend dependency updates: %s", str(e))
            return {"recommendations": [], "message": f"Update recommendation error: {str(e)}"}

    async def analyze_license_compatibility(
        self, dependencies: List[Dict[str, Any]], project_license: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze license compatibility of dependencies"""
        if not self._ensure_ai_available():
            return {"compatibility": "unknown", "message": "AI license analysis unavailable"}

        try:
            with self._safe_ai_call("license_analysis"):
                if self.ai_service is None:
                    return {"compatibility": "unknown", "message": "AI service not available"}

                ai_response = await self.ai_service.reason_about_code(
                    f"""Analyze license compatibility for these dependencies:

                    Dependencies: {dependencies}
                    Project license: {project_license or 'Not specified'}

                    Analyze:
                    1. License compatibility matrix
                    2. Potential conflicts and restrictions
                    3. Commercial use implications
                    4. Distribution requirements
                    5. Attribution requirements
                    6. Copyleft vs permissive licenses
                    """,
                    code="",
                )

                return {
                    "compatibility_score": self._extract_score_from_response(
                        ai_response.content, 8.0
                    ),
                    "license_conflicts": self._extract_license_conflicts(ai_response.content),
                    "commercial_restrictions": self._extract_commercial_restrictions(
                        ai_response.content
                    ),
                    "attribution_requirements": self._extract_attribution_requirements(
                        ai_response.content
                    ),
                    "distribution_requirements": self._extract_distribution_requirements(
                        ai_response.content
                    ),
                    "recommendations": self._extract_license_recommendations(ai_response.content),
                    "risk_level": self._extract_license_risk_level(ai_response.content),
                }

        except AIServiceError:
            return {"compatibility": "unknown", "message": "AI license analysis unavailable"}
        except (ValueError, TypeError, KeyError) as e:
            logger.warning("Failed to analyze license compatibility: %s", str(e))
            return {"compatibility": "error", "message": f"License analysis error: {str(e)}"}

    async def suggest_dependency_alternatives(
        self, problematic_deps: List[str], requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest alternative dependencies for problematic ones"""
        if not self._ensure_ai_available():
            return {"alternatives": {}, "message": "AI alternative suggestions unavailable"}

        try:
            with self._safe_ai_call("alternative_suggestions"):
                if self.ai_service is None:
                    return {"alternatives": {}, "message": "AI service not available"}

                ai_response = await self.ai_service.reason_about_code(
                    f"""Suggest alternatives for these problematic dependencies:

                    Problematic dependencies: {problematic_deps}
                    Requirements: {requirements}

                    For each dependency, suggest alternatives considering:
                    1. Similar functionality and features
                    2. Better security track record
                    3. Active maintenance and community
                    4. Performance characteristics
                    5. Compatibility with existing stack
                    6. Migration difficulty and effort
                    """,
                    code="",
                )

                alternatives = {}
                for dep in problematic_deps:
                    alternatives[dep] = self._extract_alternatives_for_dependency(
                        ai_response.content, dep
                    )

                return {
                    "alternatives": alternatives,
                    "selection_criteria": self._extract_selection_criteria(ai_response.content),
                    "migration_complexity": self._extract_migration_complexity(ai_response.content),
                    "recommended_priorities": self._extract_replacement_priorities(
                        ai_response.content
                    ),
                }

        except AIServiceError:
            return {"alternatives": {}, "message": "AI alternative suggestions unavailable"}
        except (ValueError, TypeError, KeyError) as e:
            logger.warning("Failed to suggest dependency alternatives: %s", str(e))
            return {"alternatives": {}, "message": f"Alternative suggestion error: {str(e)}"}

    # Helper methods for parsing AI responses
    def _extract_outdated_packages(self, ai_response: str) -> List[Dict[str, Any]]:
        """Extract outdated packages from AI response"""
        packages = []
        lines = ai_response.split("\n")

        for line in lines:
            if "outdated" in line.lower() or "old" in line.lower():
                package_info = {"name": line.strip(), "severity": "medium"}
                packages.append(package_info)

        return packages[:10]  # Limit to 10 packages

    def _extract_security_vulnerabilities(self, ai_response: str) -> List[Dict[str, Any]]:
        """Extract security vulnerabilities from AI response"""
        vulnerabilities = []
        lines = ai_response.split("\n")

        for line in lines:
            if any(word in line.lower() for word in ["vulnerability", "cve", "security"]):
                vuln_info = {
                    "description": line.strip(),
                    "severity": "medium",
                    "package": "unknown",
                }
                vulnerabilities.append(vuln_info)

        return vulnerabilities[:5]  # Limit to 5 vulnerabilities

    def _extract_license_issues(self, ai_response: str) -> List[str]:
        """Extract license issues from AI response"""
        return self._extract_list_from_response(
            ai_response, ["license", "legal", "copyright", "attribution"]
        )

    def _extract_unused_dependencies(self, ai_response: str) -> List[str]:
        """Extract unused dependencies from AI response"""
        return self._extract_list_from_response(
            ai_response, ["unused", "redundant", "unnecessary", "remove"]
        )

    def _extract_recommended_additions(self, ai_response: str) -> List[str]:
        """Extract recommended dependency additions from AI response"""
        return self._extract_list_from_response(
            ai_response, ["recommend", "add", "missing", "should include"]
        )

    def _extract_version_conflicts(self, ai_response: str) -> List[str]:
        """Extract version conflicts from AI response"""
        return self._extract_list_from_response(
            ai_response, ["conflict", "incompatible", "version", "mismatch"]
        )

    def _extract_detailed_vulnerabilities(self, ai_response: str) -> List[Dict[str, Any]]:
        """Extract detailed vulnerability information from AI response"""
        vulnerabilities = []
        lines = ai_response.split("\n")
        current_vuln: Dict[str, Any] = {}

        for line in lines:
            line = line.strip()
            if "cve" in line.lower() or "vulnerability" in line.lower():
                if current_vuln:
                    vulnerabilities.append(current_vuln)
                current_vuln = {
                    "id": line,
                    "severity": "medium",
                    "package": "unknown",
                    "description": line,
                }
            elif current_vuln and "severity" in line.lower():
                severity_words = ["critical", "high", "medium", "low"]
                for severity in severity_words:
                    if severity in line.lower():
                        current_vuln["severity"] = severity
                        break

        if current_vuln:
            vulnerabilities.append(current_vuln)

        return vulnerabilities

    def _extract_severity_summary(self, ai_response: str) -> Dict[str, int]:
        """Extract severity summary from AI response"""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for line in ai_response.split("\n"):
            line = line.lower()
            for severity in severity_counts:
                if severity in line and ("vulnerability" in line or "issue" in line):
                    severity_counts[severity] += 1

        return severity_counts

    def _extract_critical_issues(self, ai_response: str) -> List[str]:
        """Extract critical issues from AI response"""
        return self._extract_list_from_response(
            ai_response, ["critical", "urgent", "immediate", "severe"]
        )

    def _extract_remediation_plan(self, ai_response: str) -> List[str]:
        """Extract remediation plan from AI response"""
        return self._extract_list_from_response(
            ai_response, ["remediation", "fix", "patch", "update", "upgrade"]
        )

    def _extract_alternative_packages(self, ai_response: str) -> List[str]:
        """Extract alternative packages from AI response"""
        return self._extract_list_from_response(
            ai_response, ["alternative", "replace", "substitute", "instead"]
        )

    def _extract_risk_assessment(self, ai_response: str) -> str:
        """Extract risk assessment from AI response"""
        risk_levels = ["low", "medium", "high", "critical"]

        for line in ai_response.split("\n"):
            line = line.lower()
            if "risk" in line:
                for level in risk_levels:
                    if level in line:
                        return level.capitalize()

        return "Medium"

    def _extract_priority_updates(self, ai_response: str) -> List[Dict[str, Any]]:
        """Extract priority updates from AI response"""
        updates = []
        priorities = self._extract_list_from_response(
            ai_response, ["priority", "urgent", "critical", "security"]
        )

        for update in priorities:
            updates.append(
                {"package": update, "reason": "Security or critical update", "urgency": "high"}
            )

        return updates

    def _extract_optional_updates(self, ai_response: str) -> List[str]:
        """Extract optional updates from AI response"""
        return self._extract_list_from_response(
            ai_response, ["optional", "feature", "enhancement", "minor"]
        )

    def _extract_breaking_changes(self, ai_response: str) -> List[str]:
        """Extract breaking changes from AI response"""
        return self._extract_list_from_response(
            ai_response, ["breaking", "incompatible", "major", "migration"]
        )

    def _extract_migration_effort(self, ai_response: str) -> str:
        """Extract migration effort assessment from AI response"""
        effort_levels = ["minimal", "low", "moderate", "high", "extensive"]

        for line in ai_response.split("\n"):
            line = line.lower()
            if "effort" in line or "migration" in line:
                for level in effort_levels:
                    if level in line:
                        return level.capitalize()

        return "Moderate"

    def _extract_update_benefits(self, ai_response: str) -> List[str]:
        """Extract update benefits from AI response"""
        return self._extract_list_from_response(
            ai_response, ["benefit", "improvement", "feature", "performance"]
        )

    def _extract_compatibility_warnings(self, ai_response: str) -> List[str]:
        """Extract compatibility warnings from AI response"""
        return self._extract_list_from_response(
            ai_response, ["warning", "incompatible", "conflict", "issue"]
        )

    def _extract_update_order(self, ai_response: str) -> List[str]:
        """Extract recommended update order from AI response"""
        return self._extract_list_from_response(
            ai_response, ["first", "then", "finally", "order", "sequence"]
        )

    def _extract_license_conflicts(self, ai_response: str) -> List[str]:
        """Extract license conflicts from AI response"""
        return self._extract_list_from_response(
            ai_response, ["conflict", "incompatible", "violation", "restrict"]
        )

    def _extract_commercial_restrictions(self, ai_response: str) -> List[str]:
        """Extract commercial restrictions from AI response"""
        return self._extract_list_from_response(
            ai_response, ["commercial", "business", "restrict", "prohibit"]
        )

    def _extract_attribution_requirements(self, ai_response: str) -> List[str]:
        """Extract attribution requirements from AI response"""
        return self._extract_list_from_response(
            ai_response, ["attribution", "credit", "notice", "acknowledge"]
        )

    def _extract_distribution_requirements(self, ai_response: str) -> List[str]:
        """Extract distribution requirements from AI response"""
        return self._extract_list_from_response(
            ai_response, ["distribution", "distribute", "share", "source"]
        )

    def _extract_license_recommendations(self, ai_response: str) -> List[str]:
        """Extract license recommendations from AI response"""
        return self._extract_list_from_response(
            ai_response, ["recommend", "suggest", "consider", "license"]
        )

    def _extract_license_risk_level(self, ai_response: str) -> str:
        """Extract license risk level from AI response"""
        risk_levels = ["low", "medium", "high"]

        for line in ai_response.split("\n"):
            line = line.lower()
            if "risk" in line and "license" in line:
                for level in risk_levels:
                    if level in line:
                        return level.capitalize()

        return "Medium"

    def _extract_alternatives_for_dependency(
        self, ai_response: str, dependency: str
    ) -> List[Dict[str, Any]]:
        """Extract alternatives for a specific dependency"""
        alternatives = []
        lines = ai_response.split("\n")

        # Look for sections mentioning the dependency
        for i, line in enumerate(lines):
            if dependency.lower() in line.lower():
                # Look for alternatives in the next few lines
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if any(
                        word in next_line.lower() for word in ["alternative", "replace", "instead"]
                    ):
                        alternatives.append(
                            {"name": next_line, "reason": "AI recommended alternative"}
                        )

        return alternatives[:3]  # Limit to 3 alternatives per dependency

    def _extract_selection_criteria(self, ai_response: str) -> List[str]:
        """Extract selection criteria from AI response"""
        return self._extract_list_from_response(
            ai_response, ["criteria", "consider", "evaluate", "important"]
        )

    def _extract_migration_complexity(self, ai_response: str) -> str:
        """Extract migration complexity assessment from AI response"""
        complexity_levels = ["simple", "moderate", "complex", "difficult"]

        for line in ai_response.split("\n"):
            line = line.lower()
            if "migration" in line or "complexity" in line:
                for level in complexity_levels:
                    if level in line:
                        return level.capitalize()

        return "Moderate"

    def _extract_replacement_priorities(self, ai_response: str) -> List[str]:
        """Extract replacement priorities from AI response"""
        return self._extract_list_from_response(
            ai_response, ["priority", "first", "urgent", "important"]
        )
